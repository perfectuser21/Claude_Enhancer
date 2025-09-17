#!/usr/bin/env python3
"""
登录系统数据模型定义
包含用户、会话、权限等核心实体
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"

class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

# === SQLAlchemy模型 ===

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)
    status = Column(String(20), default=UserStatus.PENDING_VERIFICATION.value, nullable=False)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    # 安全信息
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(String, default='0', nullable=False)  # JSON存储
    locked_until = Column(DateTime, nullable=True)

    # 个人资料
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default='UTC')

    # 关系
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Token信息
    access_token_jti = Column(String(128), nullable=False, unique=True, index=True)
    refresh_token_jti = Column(String(128), nullable=False, unique=True, index=True)

    # 会话信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 客户端信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_id = Column(String(128), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # 事件信息
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, register, etc.
    event_description = Column(Text, nullable=True)

    # 时间和位置
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # 结果
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # 额外数据
    metadata = Column(Text, nullable=True)  # JSON格式

    # 关系
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, success={self.success})>"

# 索引优化
Index('idx_users_email_status', User.email, User.status)
Index('idx_users_username_status', User.username, User.status)
Index('idx_sessions_user_active', UserSession.user_id, UserSession.is_active)
Index('idx_audit_logs_user_time', AuditLog.user_id, AuditLog.created_at)

# === Pydantic模型 ===

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    timezone: str = Field("UTC", max_length=50)

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.USER

    @validator('password')
    def validate_password(cls, v: str) -> str:
        """密码强度验证"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')

        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('密码必须包含大写字母、小写字母、数字和特殊字符')

        return v

class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)

class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    created_at: datetime
    last_login_at: Optional[datetime]
    email_verified_at: Optional[datetime]

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """登录请求模型"""
    identifier: str = Field(..., min_length=1, description="用户名或邮箱")
    password: str = Field(..., min_length=1)
    remember_me: bool = False
    device_id: Optional[str] = None

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15分钟
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900

class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_new_password(cls, v: str) -> str:
        """新密码强度验证"""
        if len(v) < 8:
            raise ValueError('新密码长度至少8位')

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('新密码必须包含大写字母、小写字母、数字和特殊字符')

        return v

class SessionInfo(BaseModel):
    """会话信息模型"""
    id: str
    created_at: datetime
    last_accessed_at: datetime
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_id: Optional[str]
    is_current: bool = False

    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[List[str]] = None