"""
Perfect21 认证API路由
提供完整的RESTful认证服务端点
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, List
import logging
from datetime import datetime

# 导入模型和依赖
from .models import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    MFAVerificationRequest,
    MFAEnableRequest,
    MFASetupResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    UserProfile,
    StandardResponse,
    ErrorResponse,
)
from .dependencies import (
    get_client_info,
    get_current_user,
    get_current_active_user,
    get_user_service,
    get_jwt_manager,
    get_mfa_service,
    require_permissions,
    rate_limit_check,
)

# 导入服务层
from backend.core.services import UserService, JWTTokenManager, MFAService
from backend.core.models import User
from backend.core.monitoring import monitor_endpoint, SecurityEvent

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户",
    responses={
        201: {"description": "注册成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        409: {"model": ErrorResponse, "description": "用户已存在"},
        429: {"model": ErrorResponse, "description": "请求频率过高"},
    },
)
@monitor_endpoint("auth_register")
async def register(
    request: RegisterRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(rate_limit_check),
) -> RegisterResponse:
    """
    ## 用户注册

    创建新的用户账户。注册成功后会发送邮箱验证邮件。

    ### 密码要求
    - 至少12位字符
    - 包含大写字母、小写字母、数字和特殊字符
    - 不能包含常见弱密码模式

    ### 安全特性
    - 自动检测重复注册
    - IP地址和设备信息记录
    - 邮箱验证机制
    """
    try:
        logger.info(f"注册请求: {request.email}, IP: {client_info['ip_address']}")

        # 记录安全事件
        SecurityEvent.log_auth_attempt(
            event_type="register_attempt",
            user_email=request.email,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        # 创建用户
        user = await user_service.create_user(
            user_data={
                "email": request.email,
                "password": request.password,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "phone_number": request.phone_number,
                "marketing_consent": request.marketing_consent,
            },
            registration_context={
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "device_info": client_info["device_info"],
                "terms_accepted_at": datetime.utcnow(),
                "request_id": client_info["request_id"],
            },
        )

        # 记录成功事件
        SecurityEvent.log_auth_success(
            event_type="register_success",
            user_id=str(user.id),
            user_email=request.email,
            ip_address=client_info["ip_address"],
        )

        logger.info(f"用户注册成功: {request.email}")

        return RegisterResponse(
            message="注册成功，请查收验证邮件",
            user_id=str(user.id),
            email=user.email,
            status=user.status,
            verification_required=True,
        )

    except ValueError as e:
        # 业务逻辑错误（如用户已存在）
        SecurityEvent.log_auth_failure(
            event_type="register_failure",
            user_email=request.email,
            ip_address=client_info["ip_address"],
            reason=str(e),
        )

        if "已存在" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"注册失败 {request.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="注册服务暂时不可用"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="用户身份认证登录",
    responses={
        200: {"description": "登录成功"},
        401: {"model": ErrorResponse, "description": "认证失败"},
        429: {"model": ErrorResponse, "description": "请求频率过高"},
    },
)
@monitor_endpoint("auth_login")
async def login(
    request: LoginRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service),
    mfa_service: MFAService = Depends(get_mfa_service),
    _: bool = Depends(rate_limit_check),
) -> LoginResponse:
    """
    ## 用户登录

    使用邮箱和密码进行身份认证。

    ### 安全特性
    - 防暴力破解保护
    - 设备指纹识别
    - 多因子认证支持
    - 异常登录检测

    ### MFA流程
    如果用户启用了MFA，返回的响应中：
    - `requires_mfa` 为 `true`
    - `mfa_token` 包含用于验证的临时令牌
    - 需要调用 `/auth/mfa/verify` 完成登录
    """
    try:
        logger.info(f"登录请求: {request.email}, IP: {client_info['ip_address']}")

        # 记录登录尝试
        SecurityEvent.log_auth_attempt(
            event_type="login_attempt",
            user_email=request.email,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        # 用户认证
        user = await user_service.authenticate_user(
            email=request.email,
            password=request.password,
            login_context={
                "ip_address": client_info["ip_address"],
                "user_agent": client_info["user_agent"],
                "device_info": request.device_info or client_info["device_info"],
                "remember_me": request.remember_me,
                "request_id": client_info["request_id"],
            },
        )

        if not user:
            # 记录认证失败
            SecurityEvent.log_auth_failure(
                event_type="login_failure",
                user_email=request.email,
                ip_address=client_info["ip_address"],
                reason="invalid_credentials",
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
            )

        # 检查账户状态
        if user.status != "active":
            SecurityEvent.log_auth_failure(
                event_type="login_failure",
                user_email=request.email,
                ip_address=client_info["ip_address"],
                reason=f"account_status_{user.status}",
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"账户状态异常: {user.status}",
            )

        # 检查是否需要MFA
        if user.mfa_enabled:
            logger.info(f"用户 {request.email} 需要MFA验证")

            # 生成MFA挑战令牌
            mfa_token = await mfa_service.generate_mfa_challenge(
                user_id=str(user.id),
                ip_address=client_info["ip_address"],
                device_info=request.device_info or client_info["device_info"],
            )

            return LoginResponse(
                access_token="",
                refresh_token="",
                token_type="Bearer",
                expires_in=0,
                user=UserProfile(
                    id=str(user.id),
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    mfa_enabled=user.mfa_enabled,
                    is_verified=user.is_verified,
                    status=user.status,
                    created_at=user.created_at,
                    permissions=[],
                ),
                requires_mfa=True,
                mfa_token=mfa_token,
            )

        # 获取用户权限
        permissions = await user_service.get_user_permissions(str(user.id))

        # 生成Token对
        token_response = await jwt_manager.generate_token_pair(
            user_id=str(user.id),
            permissions=permissions,
            device_info=request.device_info or client_info["device_info"],
            ip_address=client_info["ip_address"],
            remember_me=request.remember_me,
        )

        # 更新最后登录时间
        await user_service.update_last_login(
            str(user.id), client_info["ip_address"], client_info["user_agent"]
        )

        # 记录登录成功
        SecurityEvent.log_auth_success(
            event_type="login_success",
            user_id=str(user.id),
            user_email=request.email,
            ip_address=client_info["ip_address"],
        )

        logger.info(f"用户登录成功: {user.email}")

        return LoginResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type="Bearer",
            expires_in=token_response["expires_in"],
            user=UserProfile(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                mfa_enabled=user.mfa_enabled,
                is_verified=user.is_verified,
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                permissions=permissions,
            ),
            requires_mfa=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录异常 {request.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登录服务暂时不可用"
        )


@router.post(
    "/logout",
    response_model=StandardResponse,
    summary="用户登出",
    description="注销当前用户会话",
    responses={
        200: {"description": "登出成功"},
        401: {"model": ErrorResponse, "description": "未认证"},
    },
)
@monitor_endpoint("auth_logout")
async def logout(
    current_user: User = Depends(get_current_user),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    client_info: Dict[str, Any] = Depends(get_client_info),
) -> StandardResponse:
    """
    ## 用户登出

    安全地注销当前用户会话，撤销访问令牌。

    ### 安全特性
    - 立即撤销当前访问令牌
    - 可选择撤销所有设备的令牌
    - 记录登出事件
    """
    try:
        logger.info(f"用户登出: {current_user.email}, IP: {client_info['ip_address']}")

        # 撤销当前Token
        if hasattr(current_user, "_token_claims"):
            await jwt_manager.revoke_token(
                jti=current_user._token_claims.jti, reason="user_logout"
            )

        # 记录登出事件
        SecurityEvent.log_auth_success(
            event_type="logout_success",
            user_id=str(current_user.id),
            user_email=current_user.email,
            ip_address=client_info["ip_address"],
        )

        logger.info(f"用户登出成功: {current_user.email}")

        return StandardResponse(success=True, message="登出成功")

    except Exception as e:
        logger.error(f"登出异常 {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登出服务暂时不可用"
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌",
    responses={
        200: {"description": "刷新成功"},
        401: {"model": ErrorResponse, "description": "刷新令牌无效"},
        429: {"model": ErrorResponse, "description": "请求频率过高"},
    },
)
@monitor_endpoint("auth_refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    _: bool = Depends(rate_limit_check),
) -> RefreshTokenResponse:
    """
    ## 刷新访问令牌

    使用有效的刷新令牌获取新的访问令牌对。

    ### 安全特性
    - 刷新令牌轮换（返回新的刷新令牌）
    - 设备绑定验证
    - 异常活动检测
    """
    try:
        logger.info(f"Token刷新请求, IP: {client_info['ip_address']}")

        # 刷新Token
        token_response = await jwt_manager.refresh_token(
            refresh_token=request.refresh_token,
            client_ip=client_info["ip_address"],
            device_info=client_info["device_info"],
        )

        logger.info("Token刷新成功")

        return RefreshTokenResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type="Bearer",
            expires_in=token_response["expires_in"],
        )

    except ValueError as e:
        logger.warning(f"Token刷新失败: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Token刷新异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token刷新服务暂时不可用"
        )


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="获取用户资料",
    description="获取当前认证用户的详细资料",
    responses={
        200: {"description": "获取成功"},
        401: {"model": ErrorResponse, "description": "未认证"},
    },
)
@monitor_endpoint("auth_profile")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserProfile:
    """
    ## 获取用户资料

    返回当前认证用户的详细信息，包括：
    - 基本信息（姓名、邮箱等）
    - 安全设置（MFA状态）
    - 账户状态
    - 权限列表
    """
    try:
        # 获取最新的用户信息
        user = await user_service.get_user_by_id(str(current_user.id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        # 获取用户权限
        permissions = []
        if hasattr(current_user, "_token_claims"):
            permissions = current_user._token_claims.permissions

        # 获取MFA方法
        mfa_methods = await user_service.get_user_mfa_methods(str(user.id))

        return UserProfile(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            avatar_url=user.avatar_url,
            mfa_enabled=user.mfa_enabled,
            mfa_methods=mfa_methods,
            is_verified=user.is_verified,
            status=user.status,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            permissions=permissions,
            preferences=user.preferences or {},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户资料异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户资料服务暂时不可用"
        )


@router.post(
    "/mfa/enable",
    response_model=MFASetupResponse,
    summary="启用多因子认证",
    description="为用户账户启用MFA",
    responses={
        200: {"description": "MFA设置成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "未认证"},
    },
)
@monitor_endpoint("auth_mfa_enable")
async def enable_mfa(
    request: MFAEnableRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
    mfa_service: MFAService = Depends(get_mfa_service),
    client_info: Dict[str, Any] = Depends(get_client_info),
) -> MFASetupResponse:
    """
    ## 启用多因子认证

    为用户账户设置MFA。支持的方法：
    - **TOTP**: 基于时间的一次性密码（推荐）
    - **SMS**: 短信验证码
    - **EMAIL**: 邮件验证码

    ### TOTP设置流程
    1. 调用此接口获取密钥和二维码
    2. 使用认证器应用扫描二维码
    3. 调用 `/auth/mfa/verify` 验证设置

    ### 安全要求
    - 需要提供当前密码确认身份
    - 返回的密钥仅显示一次
    - 同时生成备用恢复码
    """
    try:
        logger.info(f"用户 {current_user.email} 尝试启用MFA: {request.method}")

        # 验证当前密码
        password_valid = await user_service.verify_password(
            str(current_user.id), request.current_password
        )

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码验证失败"
            )

        # 检查是否已启用该方法
        if current_user.mfa_enabled:
            existing_methods = await user_service.get_user_mfa_methods(
                str(current_user.id)
            )
            if request.method.value in existing_methods:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"MFA方法 {request.method.value} 已启用",
                )

        # 设置MFA
        setup_result = await mfa_service.setup_mfa(
            user_id=str(current_user.id),
            method=request.method.value,
            phone_number=request.phone_number,
            ip_address=client_info["ip_address"],
        )

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="mfa_setup_initiated",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={"method": request.method.value},
        )

        logger.info(f"用户 {current_user.email} MFA设置成功: {request.method}")

        return MFASetupResponse(
            message=f"MFA方法 {request.method.value} 设置成功",
            method=request.method,
            secret_key=setup_result.get("secret_key"),
            qr_code_url=setup_result.get("qr_code_url"),
            backup_codes=setup_result.get("backup_codes"),
            verification_required=setup_result.get("verification_required", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA启用异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA设置服务暂时不可用"
        )


@router.post(
    "/mfa/verify",
    response_model=LoginResponse,
    summary="验证多因子认证",
    description="完成MFA验证流程",
    responses={
        200: {"description": "MFA验证成功"},
        401: {"model": ErrorResponse, "description": "验证失败"},
        429: {"model": ErrorResponse, "description": "请求频率过高"},
    },
)
@monitor_endpoint("auth_mfa_verify")
async def verify_mfa(
    request: MFAVerificationRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    user_service: UserService = Depends(get_user_service),
    mfa_service: MFAService = Depends(get_mfa_service),
    _: bool = Depends(rate_limit_check),
) -> LoginResponse:
    """
    ## 验证多因子认证

    完成MFA验证并获取访问令牌。

    ### 验证流程
    1. 提供从 `/auth/login` 获得的 `mfa_token`
    2. 输入认证器生成的验证码
    3. 可选择信任当前设备

    ### 设备信任
    如果选择信任设备，在该设备上一定时间内可跳过MFA验证。
    """
    try:
        logger.info(f"MFA验证请求, IP: {client_info['ip_address']}")

        # 验证MFA
        mfa_result = await mfa_service.verify_mfa_challenge(
            mfa_token=request.mfa_token,
            verification_code=request.verification_code,
            ip_address=client_info["ip_address"],
            device_info=client_info["device_info"],
        )

        if not mfa_result["valid"]:
            # 记录MFA验证失败
            SecurityEvent.log_auth_failure(
                event_type="mfa_verification_failure",
                user_email=mfa_result.get("user_email", "unknown"),
                ip_address=client_info["ip_address"],
                reason=mfa_result.get("error", "invalid_code"),
            )

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
                device_fingerprint=token_response.get("device_fingerprint"),
                ip_address=client_info["ip_address"],
                trust_duration_days=30,  # 信任30天
            )

        # 更新最后登录时间
        await user_service.update_last_login(
            user_id, client_info["ip_address"], client_info["user_agent"]
        )

        # 记录MFA验证成功
        SecurityEvent.log_auth_success(
            event_type="mfa_verification_success",
            user_id=user_id,
            user_email=user.email,
            ip_address=client_info["ip_address"],
        )

        logger.info(f"用户 {user.email} MFA验证成功")

        return LoginResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            token_type="Bearer",
            expires_in=token_response["expires_in"],
            user=UserProfile(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                mfa_enabled=user.mfa_enabled,
                is_verified=user.is_verified,
                status=user.status,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                permissions=permissions,
            ),
            requires_mfa=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA验证异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="MFA验证服务暂时不可用"
        )


# 附加端点
@router.post(
    "/password/change",
    response_model=StandardResponse,
    summary="修改密码",
    description="修改当前用户密码",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
    client_info: Dict[str, Any] = Depends(get_client_info),
) -> StandardResponse:
    """修改用户密码"""
    try:
        # 验证当前密码
        password_valid = await user_service.verify_password(
            str(current_user.id), request.current_password
        )

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码验证失败"
            )

        # 修改密码
        await user_service.change_password(
            user_id=str(current_user.id),
            old_password=request.current_password,
            new_password=request.new_password,
        )

        # 撤销用户所有现有Token
        await jwt_manager.revoke_all_user_tokens(
            user_id=str(current_user.id), reason="password_changed"
        )

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="password_changed",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
        )

        return StandardResponse(success=True, message="密码修改成功，请重新登录")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码修改异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码修改服务暂时不可用"
        )


@router.post(
    "/password/reset",
    response_model=StandardResponse,
    summary="请求密码重置",
    description="发送密码重置邮件",
)
async def request_password_reset(
    request: PasswordResetRequest,
    client_info: Dict[str, Any] = Depends(get_client_info),
    user_service: UserService = Depends(get_user_service),
    _: bool = Depends(rate_limit_check),
) -> StandardResponse:
    """请求密码重置"""
    try:
        await user_service.request_password_reset(
            email=request.email,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )

        # 为了安全，始终返回成功消息
        return StandardResponse(success=True, message="如果邮箱存在，密码重置链接已发送")

    except Exception as e:
        logger.error(f"密码重置请求异常: {e}", exc_info=True)
        # 为了安全，始终返回成功消息
        return StandardResponse(success=True, message="如果邮箱存在，密码重置链接已发送")


@router.get(
    "/sessions",
    response_model=List[Dict[str, Any]],
    summary="获取活动会话",
    description="获取用户所有活动会话",
)
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> List[Dict[str, Any]]:
    """获取用户所有活动会话"""
    try:
        sessions = await jwt_manager.get_user_sessions(str(current_user.id))
        return sessions
    except Exception as e:
        logger.error(f"获取会话列表异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话列表服务暂时不可用"
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=StandardResponse,
    summary="撤销会话",
    description="撤销指定会话",
)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    jwt_manager: JWTTokenManager = Depends(get_jwt_manager),
) -> StandardResponse:
    """撤销指定会话"""
    try:
        await jwt_manager.revoke_user_session(
            user_id=str(current_user.id), session_id=session_id
        )

        return StandardResponse(success=True, message="会话已撤销")
    except Exception as e:
        logger.error(f"撤销会话异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="撤销会话服务暂时不可用"
        )
