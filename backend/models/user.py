"""
用户模型
========

定义用户相关的数据模型:
- User: 主用户表
- UserProfile: 用户资料扩展表
- UserSetting: 用户设置表
"""

from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
import bcrypt

from .base import BaseModel, AuditMixin


class UserStatus(enum.Enum):
    """用户状态枚举"""

    ACTIVE = "active"  # 活跃
    INACTIVE = "inactive"  # 非活跃
    SUSPENDED = "suspended"  # 已暂停
    BANNED = "banned"  # 已封禁
    PENDING = "pending"  # 待激活


class UserRole(enum.Enum):
    """用户角色枚举"""

    ADMIN = "admin"  # 管理员
    MODERATOR = "moderator"  # 版主
    USER = "user"  # 普通用户
    GUEST = "guest"  # 访客


class User(BaseModel, AuditMixin):
    """
    用户主表
    ========

    存储用户的核心认证信息:
    - 用户名/邮箱/手机号
    - 密码哈希
    - 状态和角色
    - 登录相关信息
    """

    __tablename__ = "users"
    __table_args__ = (
        # 创建索引
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_phone", "phone_number"),
        Index("idx_users_status", "status"),
        Index("idx_users_last_login", "last_login_at"),
        # 添加约束
        CheckConstraint("char_length(username) >= 3", name="username_min_length"),
        CheckConstraint("char_length(username) <= 50", name="username_max_length"),
        # 表注释
        {"comment": "用户主表 - 存储用户核心认证信息"},
    )

    # 基本信息
    username = Column(
        String(50), unique=True, nullable=False, comment="用户名 (3-50字符，唯一)"
    )

    email = Column(String(255), unique=True, nullable=False, comment="邮箱地址 (唯一)")

    phone_number = Column(String(20), unique=True, nullable=True, comment="手机号码 (唯一)")

    # 认证信息
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")

    password_salt = Column(String(255), nullable=False, comment="密码盐值")

    # 状态和角色
    status = Column(
        Enum(UserStatus), default=UserStatus.PENDING, nullable=False, comment="用户状态"
    )

    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, comment="用户角色")

    # 验证状态
    email_verified = Column(Boolean, default=False, nullable=False, comment="邮箱是否已验证")

    phone_verified = Column(Boolean, default=False, nullable=False, comment="手机号是否已验证")

    # 登录信息
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")

    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP地址")  # IPv6支持

    login_count = Column(Integer, default=0, nullable=False, comment="登录次数")

    failed_login_count = Column(Integer, default=0, nullable=False, comment="连续失败登录次数")

    locked_until = Column(DateTime(timezone=True), nullable=True, comment="账户锁定截止时间")

    # 安全信息
    two_factor_enabled = Column(
        Boolean, default=False, nullable=False, comment="是否启用双因子认证"
    )

    two_factor_secret = Column(String(255), nullable=True, comment="双因子认证密钥")

    # 关联关系
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    settings = relationship(
        "UserSetting",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    # 密码相关方法
    def set_password(self, password: str) -> None:
        """
        设置密码 (自动生成盐值和哈希)

        Args:
            password: 明文密码
        """
        # 生成盐值
        salt = bcrypt.gensalt()
        # 生成哈希
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

        self.password_salt = salt.decode("utf-8")
        self.password_hash = password_hash.decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 要验证的明文密码

        Returns:
            密码是否正确
        """
        if not self.password_hash or not self.password_salt:
            return False

        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    # 账户状态方法
    @hybrid_property
    def is_active(self) -> bool:
        """检查用户是否活跃"""
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    @hybrid_property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        锁定账户

        Args:
            duration_minutes: 锁定时长 (分钟)
        """
        from datetime import timedelta

        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

    def unlock_account(self) -> None:
        """解锁账户"""
        self.locked_until = None
        self.failed_login_count = 0

    def record_login_attempt(self, success: bool, ip_address: str = None) -> None:
        """
        记录登录尝试

        Args:
            success: 登录是否成功
            ip_address: 登录IP地址
        """
        if success:
            self.last_login_at = datetime.utcnow()
            self.last_login_ip = ip_address
            self.login_count += 1
            self.failed_login_count = 0
        else:
            self.failed_login_count += 1
            # 连续失败5次锁定账户30分钟
            if self.failed_login_count >= 5:
                self.lock_account(30)

    # 验证方法
    @validates("username")
    def validate_username(self, key, username):
        """验证用户名格式"""
        if not username or len(username) < 3:
            raise ValueError("用户名至少需要3个字符")
        if len(username) > 50:
            raise ValueError("用户名不能超过50个字符")

        # 只允许字母数字和下划线
        import re

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("用户名只能包含字母、数字和下划线")

        return username

    @validates("email")
    def validate_email(self, key, email):
        """验证邮箱格式"""
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError("邮箱格式不正确")
        return email.lower()

    @validates("phone_number")
    def validate_phone(self, key, phone_number):
        """验证手机号格式"""
        if phone_number is None:
            return phone_number

        import re

        # 简单的手机号验证 (支持国际格式)
        phone_pattern = r"^\+?[1-9]\d{1,14}$"
        if not re.match(phone_pattern, phone_number):
            raise ValueError("手机号格式不正确")
        return phone_number


class UserProfile(BaseModel):
    """
    用户资料扩展表
    ===============

    存储用户的详细资料信息:
    - 个人信息 (姓名、生日、性别等)
    - 联系信息 (地址、社交账号等)
    - 个性化设置 (头像、简介等)
    """

    __tablename__ = "user_profiles"
    __table_args__ = (
        Index("idx_user_profiles_user_id", "user_id"),
        {"comment": "用户资料表 - 存储用户详细资料信息"},
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="关联用户ID",
    )

    # 个人信息
    first_name = Column(String(50), nullable=True, comment="名字")

    last_name = Column(String(50), nullable=True, comment="姓氏")

    display_name = Column(String(100), nullable=True, comment="显示名称")

    birth_date = Column(DateTime(timezone=True), nullable=True, comment="出生日期")

    gender = Column(String(10), nullable=True, comment="性别")

    # 联系信息
    address = Column(Text, nullable=True, comment="地址")

    city = Column(String(100), nullable=True, comment="城市")

    country = Column(String(100), nullable=True, comment="国家")

    postal_code = Column(String(20), nullable=True, comment="邮政编码")

    # 个性化信息
    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    bio = Column(Text, nullable=True, comment="个人简介")

    website = Column(String(500), nullable=True, comment="个人网站")

    # 社交账号 (JSON格式存储)
    social_links = Column(JSONB, nullable=True, comment="社交账号链接 (JSON格式)")

    # 扩展字段 (JSON格式存储自定义数据)
    extra_metadata = Column(JSONB, nullable=True, comment="扩展元数据 (JSON格式)")

    # 关联关系
    user = relationship("User", back_populates="profile")

    @hybrid_property
    def full_name(self) -> str:
        """获取全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        else:
            return self.user.username if self.user else "Unknown"


class UserSetting(BaseModel):
    """
    用户设置表
    ===========

    存储用户的个性化设置:
    - 界面设置 (主题、语言等)
    - 通知设置
    - 隐私设置
    - 安全设置
    """

    __tablename__ = "user_settings"
    __table_args__ = (
        Index("idx_user_settings_user_id", "user_id"),
        {"comment": "用户设置表 - 存储用户个性化设置"},
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="关联用户ID",
    )

    # 界面设置
    theme = Column(
        String(20), default="auto", nullable=False, comment="界面主题 (light/dark/auto)"
    )

    language = Column(String(10), default="zh-CN", nullable=False, comment="界面语言")

    timezone = Column(
        String(50), default="Asia/Shanghai", nullable=False, comment="时区设置"
    )

    # 通知设置
    email_notifications = Column(
        Boolean, default=True, nullable=False, comment="邮件通知开关"
    )

    sms_notifications = Column(Boolean, default=False, nullable=False, comment="短信通知开关")

    push_notifications = Column(Boolean, default=True, nullable=False, comment="推送通知开关")

    # 隐私设置
    profile_visibility = Column(
        String(20),
        default="public",
        nullable=False,
        comment="资料可见性 (public/friends/private)",
    )

    show_online_status = Column(Boolean, default=True, nullable=False, comment="显示在线状态")

    # 安全设置
    session_timeout = Column(
        Integer, default=3600, nullable=False, comment="会话超时时间 (秒)"  # 1小时
    )

    require_password_change = Column(
        Boolean, default=False, nullable=False, comment="要求更改密码"
    )

    # 扩展设置 (JSON格式)
    custom_settings = Column(JSONB, nullable=True, comment="自定义设置 (JSON格式)")

    # 关联关系
    user = relationship("User", back_populates="settings")


# 导出模型
__all__ = ["User", "UserProfile", "UserSetting", "UserStatus", "UserRole"]
