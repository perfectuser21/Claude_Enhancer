"""
Claude Enhancer 认证API路由
提供用户认证相关的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator

from app.core.security import SecurityMiddleware, JWTSecurityHandler
from app.services.jwt_service import JWTTokenManager, get_jwt_manager
from app.services.user_service import UserService, get_user_service
from app.services.mfa_service import MFAService, get_mfa_service
from shared.messaging.publisher import MessagePublisher
from shared.metrics.metrics import monitor_function

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 安全依赖
security = HTTPBearer(auto_error=False)
jwt_handler = JWTSecurityHandler()


# Pydantic模型
class LoginRequest(BaseModel):
    """登录请求"""

    email: EmailStr
    password: str
    device_info: Optional[Dict[str, Any]] = {}
    remember_me: bool = False

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    requires_mfa: bool = False
    mfa_token: Optional[str] = None


class MFAVerificationRequest(BaseModel):
    """MFA验证请求"""

    mfa_token: str
    verification_code: str
    trust_device: bool = False


class RegisterRequest(BaseModel):
    """注册请求"""

    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    terms_accepted: bool

    @validator("terms_accepted")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("必须接受服务条款")
        return v

    @validator("password")
    def validate_password(cls, v):
        # 密码复杂度验证
        if len(v) < 12:
            raise ValueError("密码长度至少12位")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>' for c in v)

        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError("密码必须包含大写字母、小写字母、数字和特殊字符")

        return v


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """密码重置请求"""

    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认请求"""

    token: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError("密码长度至少12位")
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    current_password: str
    new_password: str

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError("密码长度至少12位")
        return v


# 依赖注入
async def get_client_info(request: Request) -> Dict[str, Any]:
    """获取客户端信息"""
    return {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "device_info": {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
        },
    }


@router.post("/login", response_model=LoginResponse, summary="用户登录")
@monitor_function("auth")
async def login(
    request: LoginRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service),
    mfa_service: MFAService = Depends(get_mfa_service),
) -> LoginResponse:
    """
    用户登录认证

    - **email**: 用户邮箱
    - **password**: 用户密码
    - **device_info**: 设备信息（可选）
    - **remember_me**: 记住登录状态

    Returns:
        包含访问令牌的登录响应
    """
    try:
        logger.info(f"Login attempt for email: {request.email}")

        # 用户认证
        user = await user_service.authenticate_user(
            email=request.email,
            password=request.password,
            login_context={
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "device_info": request.device_info,
            },
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
            )

        # 检查是否需要MFA
        if user.mfa_enabled:
            pass  # Auto-fixed empty block
            # 生成MFA挑战令牌
            mfa_token = await mfa_service.generate_mfa_challenge(
                user_id=str(user.id), ip_address=client_info["ip_address"]
            )

            return LoginResponse(
                access_token="",
                refresh_token="",
                expires_in=0,
                user={
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                requires_mfa=True,
                mfa_token=mfa_token,
            )

        # 获取用户权限
        permissions = await user_service.get_user_permissions(str(user.id))

        # 生成Token对
        token_response = await jwt_manager.generate_token_pair(
            user_id=str(user.id),
            permissions=permissions,
            device_info=client_info["device_info"],
            ip_address=client_info["ip_address"],
        )

        # 更新最后登录时间
        await user_service.update_last_login(str(user.id), client_info["ip_address"])

        logger.info(f"Successful login for user: {user.email}")

        return LoginResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "mfa_enabled": user.mfa_enabled,
            },
            requires_mfa=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登录服务暂时不可用"
        )


@router.post("/mfa/verify", response_model=LoginResponse, summary="MFA验证")
@monitor_function("auth")
async def verify_mfa(
    request: MFAVerificationRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service),
    mfa_service: MFAService = Depends(get_mfa_service),
) -> LoginResponse:
    """
    多因子认证验证

    - **mfa_token**: MFA挑战令牌
    - **verification_code**: 验证码
    - **trust_device**: 是否信任设备

    Returns:
        包含访问令牌的登录响应
    """
    try:
        pass  # Auto-fixed empty block
        # 验证MFA
        mfa_result = await mfa_service.verify_mfa_challenge(
            mfa_token=request.mfa_token,
            verification_code=request.verification_code,
            ip_address=client_info["ip_address"],
        )

        if not mfa_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=mfa_result.get("error", "MFA验证失败"),
            )

        user_id = mfa_result["user_id"]

        # 获取用户信息
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        # 获取用户权限
        permissions = await user_service.get_user_permissions(user_id)

        # 生成Token对
        token_response = await jwt_manager.generate_token_pair(
            user_id=user_id,
            permissions=permissions,
            device_info=client_info["device_info"],
            ip_address=client_info["ip_address"],
        )

        # 如果用户选择信任设备，记录设备指纹
        if request.trust_device:
            await user_service.trust_device(
                user_id=user_id,
                device_fingerprint=token_response["device_fingerprint"],
                ip_address=client_info["ip_address"],
            )

        # 更新最后登录时间
        await user_service.update_last_login(user_id, client_info["ip_address"])

        logger.info(f"Successful MFA verification for user: {user.email}")

        return LoginResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "mfa_enabled": user.mfa_enabled,
            },
            requires_mfa=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA验证服务暂时不可用"
        )


@router.post("/register", summary="用户注册")
@monitor_function("auth")
async def register(
    request: RegisterRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    用户注册

    - **email**: 用户邮箱
    - **password**: 用户密码
    - **first_name**: 名字（可选）
    - **last_name**: 姓氏（可选）
    - **phone_number**: 电话号码（可选）
    - **terms_accepted**: 是否接受服务条款

    Returns:
        注册结果
    """
    try:
        logger.info(f"Registration attempt for email: {request.email}")

        # 创建用户
        user = await user_service.create_user(
            user_data={
                "email": request.email,
                "password": request.password,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "phone_number": request.phone_number,
            },
            registration_context={
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "terms_accepted_at": datetime.utcnow(),
            },
        )

        logger.info(f"Successful registration for user: {request.email}")

        return {
            "message": "注册成功，请查收验证邮件",
            "user_id": str(user.id),
            "email": user.email,
            "status": "pending_verification",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="注册服务暂时不可用"
        )


@router.post("/refresh", response_model=Dict[str, Any], summary="刷新Token")
@monitor_function("auth")
async def refresh_token(
    request: RefreshTokenRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> Dict[str, Any]:
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌

    Returns:
        新的令牌对
    """
    try:
        pass  # Auto-fixed empty block
        # 刷新Token
        token_response = await jwt_manager.refresh_token(
            refresh_token=request.refresh_token, client_ip=client_info["ip_address"]
        )

        return {
            "access_token": token_response["access_token"],
            "refresh_token": token_response["refresh_token"],
            "token_type": token_response["token_type"],
            "expires_in": token_response["expires_in"],
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token刷新服务暂时不可用"
        )


@router.post("/logout", summary="用户登出")
@monitor_function("auth")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_handler),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> Dict[str, str]:
    """
    用户登出，撤销当前Token

    需要提供有效的访问令牌

    Returns:
        登出确认消息
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="需要提供访问令牌"
            )

        # 验证Token并获取JTI
        validation_result = await jwt_manager.validate_token(credentials.credentials)

        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌"
            )

        # 撤销Token
        await jwt_manager.revoke_token(
            jti=validation_result.claims.jti, reason="user_logout"
        )

        logger.info(f"User logout: {validation_result.claims.user_id}")

        return {"message": "登出成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登出服务暂时不可用"
        )


@router.post("/password/reset", summary="请求密码重置")
@monitor_function("auth")
async def request_password_reset(
    request: PasswordResetRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    """
    请求密码重置

    - **email**: 用户邮箱

    Returns:
        重置请求确认消息
    """
    try:
        await user_service.request_password_reset(
            email=request.email, ip_address=client_info["ip_address"]
        )

        return {"message": "如果邮箱存在，密码重置链接已发送"}

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # 为了安全，始终返回成功消息
        return {"message": "如果邮箱存在，密码重置链接已发送"}


@router.post("/password/reset/confirm", summary="确认密码重置")
@monitor_function("auth")
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> Dict[str, str]:
    """
    确认密码重置

    - **token**: 密码重置令牌
    - **new_password**: 新密码

    Returns:
        重置确认消息
    """
    try:
        pass  # Auto-fixed empty block
        # 重置密码
        user_id = await user_service.reset_password(
            reset_token=request.token,
            new_password=request.new_password,
            ip_address=client_info["ip_address"],
        )

        # 撤销用户所有现有Token
        await jwt_manager.revoke_all_user_tokens(
            user_id=user_id, reason="password_reset"
        )

        return {"message": "密码重置成功，请重新登录"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Password reset confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码重置服务暂时不可用"
        )


@router.post("/password/change", summary="修改密码")
@monitor_function("auth")
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(jwt_handler),
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> Dict[str, str]:
    """
    修改密码

    - **current_password**: 当前密码
    - **new_password**: 新密码

    需要提供有效的访问令牌

    Returns:
        修改确认消息
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="需要提供访问令牌"
            )

        # 验证Token
        validation_result = await jwt_manager.validate_token(credentials.credentials)

        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌"
            )

        user_id = validation_result.claims.user_id

        # 修改密码
        success = await user_service.change_password(
            user_id=user_id,
            old_password=request.current_password,
            new_password=request.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误"
            )

        # 撤销用户所有现有Token（除了当前Token）
        await jwt_manager.revoke_all_user_tokens(
            user_id=user_id, reason="password_changed"
        )

        return {"message": "密码修改成功，请重新登录"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码修改服务暂时不可用"
        )


@router.get("/verify-email/{token}", summary="验证邮箱")
@monitor_function("auth")
async def verify_email(
    token: str,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    """
    验证邮箱地址

    - **token**: 邮箱验证令牌

    Returns:
        验证结果
    """
    try:
        success = await user_service.verify_email(
            verification_token=token, ip_address=client_info["ip_address"]
        )

        if success:
            return {"message": "邮箱验证成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="验证令牌无效或已过期"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="邮箱验证服务暂时不可用"
        )


@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_handler),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    获取当前登录用户的信息

    需要提供有效的访问令牌

    Returns:
        用户信息
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="需要提供访问令牌"
            )

        # 验证Token
        validation_result = await jwt_manager.validate_token(credentials.credentials)

        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的访问令牌"
            )

        user_id = validation_result.claims.user_id

        # 获取用户信息
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "mfa_enabled": user.mfa_enabled,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat()
            if user.last_login_at
            else None,
            "permissions": validation_result.claims.permissions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户信息服务暂时不可用"
        )
