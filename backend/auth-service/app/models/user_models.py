"""
Perfect21 用户数据模型
企业级用户相关数据模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Integer,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """用户主表"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # 基本信息
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)

    # 状态字段
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # MFA相关
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # TOTP密钥
    backup_codes = Column(JSON, nullable=True)  # 备用码

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # 登录相关
    last_login_ip = Column(String(45), nullable=True)  # 支持IPv6
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # 关联关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    roles = relationship("UserRole", back_populates="user")
    login_history = relationship("LoginHistory", back_populates="user")
    trusted_devices = relationship("TrustedDevice", back_populates="user")
    password_history = relationship("PasswordHistory", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def full_name(self) -> str:
        """获取全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    @property
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False


class UserProfile(Base):
    """用户资料表"""

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    # 个人信息
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)

    # 联系信息
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # 偏好设置
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="zh-CN", nullable=False)
    date_format = Column(String(20), default="YYYY-MM-DD", nullable=False)
    theme = Column(String(20), default="light", nullable=False)

    # 通知设置
    email_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)

    # 隐私设置
    profile_visibility = Column(
        String(20), default="private", nullable=False
    )  # public, friends, private
    show_email = Column(Boolean, default=False, nullable=False)
    show_phone = Column(Boolean, default=False, nullable=False)

    # 注册信息
    registration_ip = Column(String(45), nullable=True)
    registration_user_agent = Column(Text, nullable=True)
    registration_source = Column(String(50), nullable=True)  # web, mobile, api
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    privacy_policy_accepted_at = Column(DateTime(timezone=True), nullable=True)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # 关联关系
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id})>"


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 角色属性
    is_system = Column(Boolean, default=False, nullable=False)  # 系统内置角色
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 角色优先级

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # 关联关系
    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")

    def __repr__(self):
        return f"<Role(name={self.name})>"


class Permission(Base):
    """权限表"""

    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 权限分类
    resource = Column(String(100), nullable=False)  # 资源类型
    action = Column(String(50), nullable=False)  # 操作类型
    scope = Column(String(50), default="global", nullable=False)  # 权限范围

    # 权限属性
    is_system = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # 关联关系
    role_permissions = relationship("RolePermission", back_populates="permission")

    def __repr__(self):
        return f"<Permission(name={self.name})>"


class UserRole(Base):
    """用户角色关联表"""

    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    # 分配信息
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 角色过期时间

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)

    # 关联关系
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """角色权限关联表"""

    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(
        UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False
    )

    # 分配信息
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class LoginHistory(Base):
    """登录历史表"""

    __tablename__ = "login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 登录信息
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    location_info = Column(JSON, nullable=True)  # 地理位置信息

    # 登录结果
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100), nullable=True)

    # 安全信息
    mfa_used = Column(Boolean, default=False, nullable=False)
    trusted_device = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)  # 风险评分

    # 时间戳
    login_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    logout_at = Column(DateTime(timezone=True), nullable=True)
    session_duration = Column(Integer, nullable=True)  # 会话持续时间（秒）

    # 关联关系
    user = relationship("User", back_populates="login_history")

    def __repr__(self):
        return f"<LoginHistory(user_id={self.user_id}, success={self.success})>"


class TrustedDevice(Base):
    """受信任设备表"""

    __tablename__ = "trusted_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 设备信息
    device_fingerprint = Column(String(255), nullable=False, unique=True)
    device_name = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser_info = Column(JSON, nullable=True)
    os_info = Column(JSON, nullable=True)

    # 网络信息
    ip_address = Column(String(45), nullable=False)
    location_info = Column(JSON, nullable=True)

    # 信任状态
    is_active = Column(Boolean, default=True, nullable=False)
    trust_level = Column(
        String(20), default="medium", nullable=False
    )  # low, medium, high

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # 关联关系
    user = relationship("User", back_populates="trusted_devices")

    def __repr__(self):
        return f"<TrustedDevice(user_id={self.user_id}, fingerprint={self.device_fingerprint[:10]}...)>"


class PasswordHistory(Base):
    """密码历史表"""

    __tablename__ = "password_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 密码信息
    password_hash = Column(String(255), nullable=False)
    hash_algorithm = Column(String(50), default="bcrypt", nullable=False)

    # 变更信息
    changed_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # 谁修改的
    change_reason = Column(String(100), nullable=True)  # 修改原因
    change_method = Column(String(50), nullable=True)  # 修改方式：reset, change, admin

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    user = relationship("User", back_populates="password_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return (
            f"<PasswordHistory(user_id={self.user_id}, created_at={self.created_at})>"
        )


class AuditLog(Base):
    """审计日志表"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 操作信息
    action = Column(String(100), nullable=False)  # 操作类型
    resource = Column(String(100), nullable=True)  # 操作资源
    resource_id = Column(String(100), nullable=True)  # 资源ID

    # 请求信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)

    # 操作结果
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # 详细信息
    details = Column(JSON, nullable=True)  # 详细操作数据
    old_values = Column(JSON, nullable=True)  # 修改前的值
    new_values = Column(JSON, nullable=True)  # 修改后的值

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关联关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id})>"


class SecurityEvent(Base):
    """安全事件表"""

    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 事件信息
    event_type = Column(String(100), nullable=False)  # 事件类型
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    source = Column(String(100), nullable=False)  # 事件来源

    # 描述信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # 网络信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location_info = Column(JSON, nullable=True)

    # 事件数据
    event_data = Column(JSON, nullable=True)
    risk_score = Column(Integer, default=0, nullable=False)

    # 处理状态
    status = Column(
        String(20), default="open", nullable=False
    )  # open, investigating, resolved, false_positive
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # 关联关系
    user = relationship(
        "User", back_populates="security_events", foreign_keys=[user_id]
    )
    assigned_user = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<SecurityEvent(type={self.event_type}, severity={self.severity})>"


# 为User模型添加security_events关系
User.security_events = relationship(
    "SecurityEvent", back_populates="user", foreign_keys="SecurityEvent.user_id"
)

# 数据库索引优化
from sqlalchemy import Index

# 用户表索引
Index("idx_users_email_active", User.email, User.is_active)
Index("idx_users_last_login", User.last_login_at)

# 登录历史表索引
Index("idx_login_history_user_time", LoginHistory.user_id, LoginHistory.login_at)
Index("idx_login_history_ip", LoginHistory.ip_address)
Index("idx_login_history_success", LoginHistory.success, LoginHistory.login_at)

# 审计日志表索引
Index("idx_audit_logs_user_time", AuditLog.user_id, AuditLog.created_at)
Index("idx_audit_logs_action", AuditLog.action, AuditLog.created_at)
Index("idx_audit_logs_resource", AuditLog.resource, AuditLog.resource_id)

# 安全事件表索引
Index("idx_security_events_user_time", SecurityEvent.user_id, SecurityEvent.created_at)
Index(
    "idx_security_events_type_severity",
    SecurityEvent.event_type,
    SecurityEvent.severity,
)
Index("idx_security_events_status", SecurityEvent.status, SecurityEvent.created_at)

# 受信任设备表索引
Index("idx_trusted_devices_user", TrustedDevice.user_id, TrustedDevice.is_active)
Index("idx_trusted_devices_fingerprint", TrustedDevice.device_fingerprint)

# 角色权限相关索引
Index("idx_user_roles_user", UserRole.user_id, UserRole.is_active)
Index("idx_role_permissions_role", RolePermission.role_id)
