"""
Perfect21 认证API数据模型
定义所有认证相关的请求和响应模型
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class TokenType(str, Enum):
    """Token类型枚举"""
    BEARER = "Bearer"
    REFRESH = "Refresh"


class MFAMethod(str, Enum):
    """MFA方法枚举"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# Request Models
class LoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr = Field(..., description="用户邮箱地址")
    password: str = Field(..., min_length=8, description="用户密码")
    device_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="设备信息")
    remember_me: bool = Field(default=False, description="是否记住登录状态")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "device_info": {
                    "device_type": "web",
                    "browser": "Chrome",
                    "os": "Windows 10"
                },
                "remember_me": False
            }
        }


class RegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr = Field(..., description="用户邮箱地址")
    password: str = Field(..., min_length=12, description="用户密码")
    confirm_password: str = Field(..., description="确认密码")
    first_name: Optional[str] = Field(None, max_length=50, description="名字")
    last_name: Optional[str] = Field(None, max_length=50, description="姓氏")
    phone_number: Optional[str] = Field(None, description="电话号码")
    terms_accepted: bool = Field(..., description="是否接受服务条款")
    marketing_consent: bool = Field(default=False, description="是否同意营销信息")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码和确认密码不匹配')
        return v

    @validator('terms_accepted')
    def validate_terms(cls, v):
        if not v:
            raise ValueError('必须接受服务条款')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        """密码强度验证"""
        if len(v) < 12:
            raise ValueError('密码长度至少12位')

        checks = {
            'uppercase': any(c.isupper() for c in v),
            'lowercase': any(c.islower() for c in v),
            'digit': any(c.isdigit() for c in v),
            'special': any(c in "!@#$%^&*(),.?\":{}|<>[]" for c in v)
        }

        if not all(checks.values()):
            missing = [k for k, v in checks.items() if not v]
            raise ValueError(f'密码必须包含: {", ".join(missing)}')

        # 检查常见弱密码模式
        weak_patterns = ['123456', 'password', 'qwerty', 'abc123']
        if any(pattern in v.lower() for pattern in weak_patterns):
            raise ValueError('密码不能包含常见弱密码模式')

        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "terms_accepted": True,
                "marketing_consent": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."
            }
        }


class MFAVerificationRequest(BaseModel):
    """MFA验证请求"""
    mfa_token: str = Field(..., description="MFA挑战令牌")
    verification_code: str = Field(..., min_length=6, max_length=8, description="验证码")
    trust_device: bool = Field(default=False, description="是否信任当前设备")

    @validator('verification_code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('验证码必须是数字')
        return v

    class Config:
        schema_extra = {
            "example": {
                "mfa_token": "mfa_challenge_token_123",
                "verification_code": "123456",
                "trust_device": False
            }
        }


class MFAEnableRequest(BaseModel):
    """启用MFA请求"""
    method: MFAMethod = Field(..., description="MFA方法")
    phone_number: Optional[str] = Field(None, description="电话号码（SMS方法需要）")
    current_password: str = Field(..., description="当前密码确认")

    @validator('phone_number')
    def validate_phone_for_sms(cls, v, values):
        if values.get('method') == MFAMethod.SMS and not v:
            raise ValueError('SMS方法需要提供电话号码')
        return v

    class Config:
        schema_extra = {
            "example": {
                "method": "totp",
                "current_password": "CurrentPassword123!"
            }
        }


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=12, description="新密码")
    confirm_new_password: str = Field(..., description="确认新密码")

    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v

    @validator('new_password')
    def validate_new_password(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('新密码不能与当前密码相同')
        return v


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: EmailStr = Field(..., description="用户邮箱地址")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


# Response Models
class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: TokenType = Field(default=TokenType.BEARER, description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    user: "UserProfile" = Field(..., description="用户信息")
    requires_mfa: bool = Field(default=False, description="是否需要MFA验证")
    mfa_token: Optional[str] = Field(None, description="MFA挑战令牌")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "id": "user_123",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "requires_mfa": False
            }
        }


class RegisterResponse(BaseModel):
    """注册响应"""
    message: str = Field(..., description="注册结果消息")
    user_id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    status: UserStatus = Field(..., description="用户状态")
    verification_required: bool = Field(default=True, description="是否需要邮箱验证")

    class Config:
        schema_extra = {
            "example": {
                "message": "注册成功，请查收验证邮件",
                "user_id": "user_123",
                "email": "newuser@example.com",
                "status": "pending_verification",
                "verification_required": True
            }
        }


class RefreshTokenResponse(BaseModel):
    """刷新Token响应"""
    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: TokenType = Field(default=TokenType.BEARER, description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class UserProfile(BaseModel):
    """用户档案信息"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="邮箱地址")
    username: Optional[str] = Field(None, description="用户名")
    first_name: Optional[str] = Field(None, description="名字")
    last_name: Optional[str] = Field(None, description="姓氏")
    phone_number: Optional[str] = Field(None, description="电话号码")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    mfa_enabled: bool = Field(default=False, description="是否启用MFA")
    mfa_methods: List[MFAMethod] = Field(default_factory=list, description="已启用的MFA方法")
    is_verified: bool = Field(default=False, description="是否已验证邮箱")
    status: UserStatus = Field(..., description="用户状态")
    created_at: datetime = Field(..., description="创建时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    permissions: List[str] = Field(default_factory=list, description="用户权限")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好设置")

    class Config:
        schema_extra = {
            "example": {
                "id": "user_123",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "avatar_url": "https://example.com/avatar.jpg",
                "mfa_enabled": True,
                "mfa_methods": ["totp", "backup_codes"],
                "is_verified": True,
                "status": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "last_login_at": "2023-12-01T12:00:00Z",
                "permissions": ["read:profile", "write:profile"],
                "preferences": {
                    "language": "en",
                    "timezone": "UTC",
                    "notifications": True
                }
            }
        }


class MFASetupResponse(BaseModel):
    """MFA设置响应"""
    message: str = Field(..., description="设置结果消息")
    method: MFAMethod = Field(..., description="MFA方法")
    secret_key: Optional[str] = Field(None, description="TOTP密钥（仅用于设置）")
    qr_code_url: Optional[str] = Field(None, description="TOTP二维码URL")
    backup_codes: Optional[List[str]] = Field(None, description="备用恢复码")
    verification_required: bool = Field(default=True, description="是否需要验证设置")

    class Config:
        schema_extra = {
            "example": {
                "message": "MFA设置成功，请使用验证器扫描二维码",
                "method": "totp",
                "secret_key": "JBSWY3DPEHPK3PXP",
                "qr_code_url": "otpauth://totp/Perfect21:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Perfect21",
                "backup_codes": ["12345678", "87654321", "11111111"],
                "verification_required": True
            }
        }


class StandardResponse(BaseModel):
    """标准API响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "timestamp": "2023-12-01T12:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="操作是否成功")
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间")
    request_id: Optional[str] = Field(None, description="请求ID")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": {
                    "field": "password",
                    "constraint": "minimum_length"
                },
                "timestamp": "2023-12-01T12:00:00Z",
                "request_id": "req_123"
            }
        }


# Update forward references
LoginResponse.model_rebuild()