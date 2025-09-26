"""
会话模型
========

定义用户会话相关的数据模型:
- Session: 用户会话表
- RefreshToken: 刷新令牌表
- LoginHistory: 登录历史表
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import enum
import secrets
import hashlib

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Enum,
    Index,
    event,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class SessionStatus(enum.Enum):
    """会话状态枚举"""

    ACTIVE = "active"  # 活跃
    EXPIRED = "expired"  # 已过期
    REVOKED = "revoked"  # 已撤销
    INVALID = "invalid"  # 无效


class DeviceType(enum.Enum):
    """设备类型枚举"""

    WEB = "web"  # 网页浏览器
    MOBILE = "mobile"  # 移动应用
    DESKTOP = "desktop"  # 桌面应用
    API = "api"  # API客户端
    UNKNOWN = "unknown"  # 未知


class Session(BaseModel):
    """
    用户会话表
    ===========

    管理用户的登录会话:
    - 会话令牌和状态
    - 设备和位置信息
    - 安全相关字段
    - 会话生命周期管理
    """

    __tablename__ = "sessions"
    __table_args__ = (
        # 创建索引
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_token_hash", "token_hash"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_expires_at", "expires_at"),
        Index("idx_sessions_last_activity", "last_activity_at"),
        # 表注释
        {"comment": "用户会话表 - 管理用户登录会话信息"},
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联用户ID",
    )

    # 会话标识
    session_id = Column(
        String(255), unique=True, nullable=False, comment="会话ID (对外暴露的标识符)"
    )

    token_hash = Column(
        String(255), unique=True, nullable=False, comment="令牌哈希值 (用于验证)"
    )

    # 会话状态
    status = Column(
        Enum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False,
        comment="会话状态",
    )

    # 时间管理
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")

    last_activity_at = Column(DateTime(timezone=True), nullable=False, comment="最后活动时间")

    # 设备信息
    device_type = Column(
        Enum(DeviceType), default=DeviceType.UNKNOWN, nullable=False, comment="设备类型"
    )

    device_id = Column(String(255), nullable=True, comment="设备唯一标识")

    device_name = Column(String(255), nullable=True, comment="设备名称")

    user_agent = Column(Text, nullable=True, comment="用户代理字符串")

    # 网络信息
    ip_address = Column(INET, nullable=True, comment="IP地址")

    ip_location = Column(JSONB, nullable=True, comment="IP地理位置信息 (JSON)")

    # 安全字段
    csrf_token = Column(String(255), nullable=True, comment="CSRF令牌")

    is_trusted_device = Column(
        Boolean, default=False, nullable=False, comment="是否为受信任设备"
    )

    risk_score = Column(Integer, default=0, nullable=False, comment="风险评分 (0-100)")

    # 扩展信息
    metadata = Column(JSONB, nullable=True, comment="扩展元数据 (JSON)")

    # 关联关系
    user = relationship("User", back_populates="sessions")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="session", cascade="all, delete-orphan"
    )

    @classmethod
    def generate_session_id(cls) -> str:
        """生成会话ID"""
        return secrets.token_urlsafe(32)

    @classmethod
    def generate_token_hash(cls, token: str) -> str:
        """生成令牌哈希"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_session(
        cls,
        user_id: str,
        token: str,
        expires_in_seconds: int = 3600,
        device_type: DeviceType = DeviceType.UNKNOWN,
        ip_address: str = None,
        user_agent: str = None,
        **kwargs,
    ) -> "Session":
        """
        创建新会话

        Args:
            user_id: 用户ID
            token: 会话令牌
            expires_in_seconds: 过期时间 (秒)
            device_type: 设备类型
            ip_address: IP地址
            user_agent: 用户代理
            **kwargs: 其他参数

        Returns:
            新创建的会话对象
        """
        now = datetime.utcnow()

        session = cls(
            user_id=user_id,
            session_id=cls.generate_session_id(),
            token_hash=cls.generate_token_hash(token),
            status=SessionStatus.ACTIVE,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            last_activity_at=now,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )

        return session

    def verify_token(self, token: str) -> bool:
        """
        验证令牌

        Args:
            token: 要验证的令牌

        Returns:
            令牌是否有效
        """
        return self.token_hash == self.generate_token_hash(token)

    @hybrid_property
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at

    @hybrid_property
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return (
            self.status == SessionStatus.ACTIVE
            and not self.is_expired
            and not self.is_deleted
        )

    def extend_session(self, seconds: int = 3600) -> None:
        """
        延长会话有效期

        Args:
            seconds: 延长的秒数
        """
        if self.is_active:
            self.expires_at = datetime.utcnow() + timedelta(seconds=seconds)
            self.last_activity_at = datetime.utcnow()

    def revoke(self, reason: str = None) -> None:
        """
        撤销会话

        Args:
            reason: 撤销原因
        """
        self.status = SessionStatus.REVOKED
        if reason and self.metadata:
            self.metadata["revocation_reason"] = reason
        elif reason:
            self.metadata = {"revocation_reason": reason}

    def update_activity(self, ip_address: str = None) -> None:
        """
        更新活动时间

        Args:
            ip_address: 新的IP地址
        """
        self.last_activity_at = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address


class RefreshToken(BaseModel):
    """
    刷新令牌表
    ===========

    管理JWT刷新令牌:
    - 令牌标识和哈希
    - 过期时间管理
    - 使用计数和限制
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_session_id", "session_id"),
        Index("idx_refresh_tokens_token_hash", "token_hash"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
        {"comment": "刷新令牌表 - 管理JWT刷新令牌"},
    )

    # 关联会话
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联会话ID",
    )

    # 令牌信息
    token_hash = Column(String(255), unique=True, nullable=False, comment="刷新令牌哈希")

    token_family = Column(String(255), nullable=False, comment="令牌族标识 (用于检测令牌重放)")

    # 时间管理
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")

    # 使用信息
    used_count = Column(Integer, default=0, nullable=False, comment="使用次数")

    max_uses = Column(Integer, default=1, nullable=False, comment="最大使用次数")

    last_used_at = Column(DateTime(timezone=True), nullable=True, comment="最后使用时间")

    # 状态
    is_revoked = Column(Boolean, default=False, nullable=False, comment="是否已撤销")

    # 关联关系
    session = relationship("Session", back_populates="refresh_tokens")

    @classmethod
    def create_refresh_token(
        cls, session_id: str, token: str, expires_in_days: int = 30, max_uses: int = 1
    ) -> "RefreshToken":
        """
        创建刷新令牌

        Args:
            session_id: 会话ID
            token: 令牌值
            expires_in_days: 过期天数
            max_uses: 最大使用次数

        Returns:
            新创建的刷新令牌
        """
        return cls(
            session_id=session_id,
            token_hash=Session.generate_token_hash(token),
            token_family=secrets.token_urlsafe(16),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            max_uses=max_uses,
        )

    def verify_token(self, token: str) -> bool:
        """验证刷新令牌"""
        return self.token_hash == Session.generate_token_hash(token)

    @hybrid_property
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return (
            not self.is_revoked
            and not self.is_deleted
            and datetime.utcnow() < self.expires_at
            and self.used_count < self.max_uses
        )

    def use_token(self) -> bool:
        """
        使用令牌

        Returns:
            是否使用成功
        """
        if not self.is_valid:
            return False

        self.used_count += 1
        self.last_used_at = datetime.utcnow()

        # 如果达到最大使用次数，标记为已撤销
        if self.used_count >= self.max_uses:
            self.is_revoked = True

        return True


class LoginHistory(BaseModel):
    """
    登录历史表
    ===========

    记录用户的登录历史:
    - 登录成功/失败记录
    - 设备和位置信息
    - 安全事件记录
    """

    __tablename__ = "login_history"
    __table_args__ = (
        Index("idx_login_history_user_id", "user_id"),
        Index("idx_login_history_login_at", "login_at"),
        Index("idx_login_history_success", "success"),
        Index("idx_login_history_ip_address", "ip_address"),
        {"comment": "登录历史表 - 记录用户登录历史"},
    )

    # 关联用户
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联用户ID",
    )

    # 登录信息
    login_at = Column(DateTime(timezone=True), nullable=False, comment="登录时间")

    success = Column(Boolean, nullable=False, comment="登录是否成功")

    failure_reason = Column(String(255), nullable=True, comment="失败原因")

    # 设备信息
    device_type = Column(
        Enum(DeviceType), default=DeviceType.UNKNOWN, nullable=False, comment="设备类型"
    )

    device_fingerprint = Column(String(255), nullable=True, comment="设备指纹")

    user_agent = Column(Text, nullable=True, comment="用户代理")

    # 网络信息
    ip_address = Column(INET, nullable=True, comment="IP地址")

    ip_location = Column(JSONB, nullable=True, comment="IP地理位置")

    # 安全信息
    risk_score = Column(Integer, default=0, nullable=False, comment="风险评分")

    security_flags = Column(JSONB, nullable=True, comment="安全标记 (JSON)")

    # 会话关联 (如果登录成功)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联会话ID",
    )

    # 关联关系
    user = relationship("User")
    session = relationship("Session")


# 事件监听器 - 自动更新会话状态
@event.listens_for(Session, "before_update")
def update_session_status(mapper, connection, target):
    """自动更新过期会话的状态"""
    if target.is_expired and target.status == SessionStatus.ACTIVE:
        target.status = SessionStatus.EXPIRED


# 导出模型
__all__ = ["Session", "RefreshToken", "LoginHistory", "SessionStatus", "DeviceType"]
