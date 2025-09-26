"""
Claude Enhancer 用户服务
企业级用户注册、登录、管理服务
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from email_validator import validate_email, EmailNotValidError

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user_models import User, UserProfile, LoginHistory, TrustedDevice
from app.services.password_service import PasswordService, get_password_service
from app.services.email_service import EmailService, get_email_service
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function


class UserRegistrationData(BaseModel):
    """用户注册数据"""

    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "zh-CN"


class AuthenticationResult(BaseModel):
    """认证结果"""

    success: bool
    user: Optional[User] = None
    failure_reason: Optional[str] = None
    account_locked: bool = False
    attempts_remaining: Optional[int] = None
    lockout_expires_at: Optional[datetime] = None


class UserService:
    """用户服务管理器"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.password_service = None
        self.email_service = None

        # 初始化Redis
        self._initialize_redis()

    def _initialize_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    async def set_dependencies(
        self,
        message_publisher: MessagePublisher,
        password_service: PasswordService,
        email_service: EmailService,
    ):
        """设置依赖服务"""
        self.message_publisher = message_publisher
        self.password_service = password_service
        self.email_service = email_service

    @monitor_function("user")
    async def create_user(
        self, user_data: Dict[str, Any], registration_context: Dict[str, Any]
    ) -> User:
        """创建新用户"""
        async with get_async_session() as session:
            try:
                # 验证邮箱格式
                try:
                    validated_email = validate_email(user_data["email"])
                    email = validated_email.email
                except EmailNotValidError as e:
                    raise ValueError(f"邮箱格式无效: {str(e)}")

                # 检查邮箱是否已存在
                existing_user = await self._get_user_by_email(session, email)
                if existing_user:
                    raise ValueError("邮箱已被注册")

                # 验证密码强度
                if not self.password_service:
                    self.password_service = await get_password_service()

                strength_result = (
                    await self.password_service.validate_password_strength(
                        password=user_data["password"],
                        user_context={
                            "first_name": user_data.get("first_name", ""),
                            "last_name": user_data.get("last_name", ""),
                            "email": email,
                        },
                    )
                )

                if not strength_result.is_strong:
                    raise ValueError(f"密码强度不足: {', '.join(strength_result.feedback)}")

                # 加密密码
                password_hash = await self.password_service.hash_password(
                    password=user_data["password"]
                )

                # 创建用户
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    username=email.split("@")[0],  # 默认用户名
                    password_hash=password_hash,
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    phone_number=user_data.get("phone_number"),
                    is_active=True,
                    is_verified=False,
                    mfa_enabled=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    password_changed_at=datetime.utcnow(),
                )

                session.add(user)
                await session.flush()  # 获取用户ID

                # 创建用户资料
                profile = UserProfile(
                    user_id=user.id,
                    timezone=user_data.get("timezone", "UTC"),
                    language=user_data.get("language", "zh-CN"),
                    registration_ip=registration_context.get("ip_address"),
                    registration_user_agent=registration_context.get("user_agent"),
                    terms_accepted_at=registration_context.get("terms_accepted_at"),
                )

                session.add(profile)

                # 存储密码历史
                await self.password_service.store_password_history(
                    user_id=str(user.id), password_hash=password_hash
                )

                # 生成邮箱验证令牌
                verification_token = await self._generate_verification_token(
                    str(user.id)
                )

                # 发送验证邮件
                if not self.email_service:
                    self.email_service = await get_email_service()

                await self.email_service.send_verification_email(
                    email=email,
                    first_name=user.first_name or "用户",
                    verification_token=verification_token,
                )

                await session.commit()

                # 发布用户注册事件
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.USER_REGISTERED,
                        data={
                            "user_id": str(user.id),
                            "email": email,
                            "registration_ip": registration_context.get("ip_address"),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        user_id=str(user.id),
                    )

                return user

            except Exception as e:
                await session.rollback()
                raise

    @monitor_function("user")
    async def authenticate_user(
        self, email: str, password: str, login_context: Dict[str, Any]
    ) -> Optional[User]:
        """用户认证"""
        async with get_async_session() as session:
            try:
                # 检查用户是否存在
                user = await self._get_user_by_email(session, email)
                if not user:
                    await self._log_failed_login(email, "user_not_found", login_context)
                    return None

                # 检查账户是否被锁定
                lockout_info = await self._check_account_lockout(str(user.id))
                if lockout_info["is_locked"]:
                    await self._log_failed_login(email, "account_locked", login_context)
                    return None

                # 检查账户是否激活
                if not user.is_active:
                    await self._log_failed_login(
                        email, "account_inactive", login_context
                    )
                    return None

                # 验证密码
                if not self.password_service:
                    self.password_service = await get_password_service()

                verification_result = await self.password_service.verify_password(
                    password=password,
                    password_hash=user.password_hash,
                    user_id=str(user.id),
                    ip_address=login_context.get("ip_address"),
                )

                if not verification_result.is_valid:
                    # 记录失败尝试
                    await self._record_failed_attempt(str(user.id), login_context)
                    await self._log_failed_login(
                        email, "invalid_password", login_context
                    )
                    return None

                # 检查密码风险因素
                if verification_result.risk_factors:
                    await self._handle_password_risk_factors(
                        user=user,
                        risk_factors=verification_result.risk_factors,
                        login_context=login_context,
                    )

                # 清除失败尝试计数
                await self._clear_failed_attempts(str(user.id))

                # 记录成功登录
                await self._record_successful_login(user, login_context)

                return user

            except Exception as e:
                raise RuntimeError(f"用户认证失败: {e}")

    @monitor_function("user")
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户"""
        async with get_async_session() as session:
            try:
                stmt = select(User).where(User.id == uuid.UUID(user_id))
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e:
                raise RuntimeError(f"获取用户信息失败: {e}")

    @monitor_function("user")
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        try:
            # 先从缓存获取
            cache_key = f"user_permissions:{user_id}"
            cached_permissions = await self.redis_client.get(cache_key)

            if cached_permissions:
                return cached_permissions.split(",")

            # 从数据库获取（这里简化为基础权限）
            permissions = ["read:profile", "update:profile"]

            # 缓存权限（5分钟）
            await self.redis_client.setex(
                cache_key, settings.CACHE_TTL_USER_PERMISSIONS, ",".join(permissions)
            )

            return permissions

        except Exception as e:
            raise RuntimeError(f"获取用户权限失败: {e}")

    @monitor_function("user")
    async def update_last_login(self, user_id: str, ip_address: str):
        """更新最后登录时间"""
        async with get_async_session() as session:
            try:
                stmt = (
                    update(User)
                    .where(User.id == uuid.UUID(user_id))
                    .values(
                        last_login_at=datetime.utcnow(),
                        last_login_ip=ip_address,
                        updated_at=datetime.utcnow(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"更新最后登录时间失败: {e}")

    @monitor_function("user")
    async def verify_email(self, verification_token: str, ip_address: str) -> bool:
        """验证邮箱"""
        try:
            # 验证令牌
            user_id = await self._verify_token(verification_token, "email_verification")
            if not user_id:
                return False

            async with get_async_session() as session:
                # 更新用户验证状态
                stmt = (
                    update(User)
                    .where(User.id == uuid.UUID(user_id))
                    .values(
                        is_verified=True,
                        email_verified_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

                # 删除验证令牌
                await self._delete_token(verification_token)

                # 发布邮箱验证事件
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.USER_LOGIN,
                        data={
                            "event_type": "email_verified",
                            "user_id": user_id,
                            "ip_address": ip_address,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        user_id=user_id,
                    )

                return True

        except Exception as e:
            raise RuntimeError(f"邮箱验证失败: {e}")

    @monitor_function("user")
    async def request_password_reset(self, email: str, ip_address: str):
        """请求密码重置"""
        async with get_async_session() as session:
            try:
                user = await self._get_user_by_email(session, email)
                if not user:
                    # 为了安全，不暴露用户是否存在
                    return

                # 生成重置令牌
                reset_token = await self._generate_reset_token(str(user.id))

                # 发送重置邮件
                if not self.email_service:
                    self.email_service = await get_email_service()

                await self.email_service.send_password_reset_email(
                    email=email,
                    first_name=user.first_name or "用户",
                    reset_token=reset_token,
                )

                # 记录重置请求
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.SECURITY_ALERT,
                        data={
                            "user_id": str(user.id),
                            "alert_type": "password_reset_requested",
                            "severity": "low",
                            "description": "用户请求密码重置",
                            "ip_address": ip_address,
                        },
                        user_id=str(user.id),
                    )

            except Exception as e:
                raise RuntimeError(f"密码重置请求失败: {e}")

    @monitor_function("user")
    async def reset_password(
        self, reset_token: str, new_password: str, ip_address: str
    ) -> str:
        """重置密码"""
        try:
            # 验证重置令牌
            user_id = await self._verify_token(reset_token, "password_reset")
            if not user_id:
                raise ValueError("无效或已过期的重置令牌")

            # 验证新密码强度
            if not self.password_service:
                self.password_service = await get_password_service()

            strength_result = await self.password_service.validate_password_strength(
                new_password
            )
            if not strength_result.is_strong:
                raise ValueError(f"密码强度不足: {', '.join(strength_result.feedback)}")

            # 检查密码重用
            verification_result = await self.password_service.verify_password(
                password=new_password, password_hash="", user_id=user_id  # 空哈希，只检查重用
            )

            if verification_result.reuse_detected:
                raise ValueError("新密码不能与历史密码相同")

            # 加密新密码
            new_password_hash = await self.password_service.hash_password(
                password=new_password, user_id=user_id
            )

            async with get_async_session() as session:
                # 更新密码
                stmt = (
                    update(User)
                    .where(User.id == uuid.UUID(user_id))
                    .values(
                        password_hash=new_password_hash,
                        password_changed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )
                await session.execute(stmt)
                await session.commit()

                # 存储新密码到历史
                await self.password_service.store_password_history(
                    user_id=user_id, password_hash=new_password_hash
                )

                # 删除重置令牌
                await self._delete_token(reset_token)

                # 发布密码重置事件
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.SECURITY_ALERT,
                        data={
                            "user_id": user_id,
                            "alert_type": "password_reset_completed",
                            "severity": "medium",
                            "description": "用户完成密码重置",
                            "ip_address": ip_address,
                        },
                        user_id=user_id,
                    )

                return user_id

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"密码重置失败: {e}")

    @monitor_function("user")
    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """修改密码"""
        async with get_async_session() as session:
            try:
                user = await session.get(User, uuid.UUID(user_id))
                if not user:
                    return False

                # 验证旧密码
                if not self.password_service:
                    self.password_service = await get_password_service()

                verification_result = await self.password_service.verify_password(
                    password=old_password,
                    password_hash=user.password_hash,
                    user_id=user_id,
                )

                if not verification_result.is_valid:
                    return False

                # 验证新密码强度
                strength_result = (
                    await self.password_service.validate_password_strength(new_password)
                )
                if not strength_result.is_strong:
                    raise ValueError(f"密码强度不足: {', '.join(strength_result.feedback)}")

                # 检查密码重用
                reuse_check = await self.password_service.verify_password(
                    password=new_password,
                    password_hash="",  # 空哈希，只检查重用
                    user_id=user_id,
                )

                if reuse_check.reuse_detected:
                    raise ValueError("新密码不能与历史密码相同")

                # 加密新密码
                new_password_hash = await self.password_service.hash_password(
                    password=new_password, user_id=user_id
                )

                # 更新密码
                user.password_hash = new_password_hash
                user.password_changed_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()

                await session.commit()

                # 存储新密码到历史
                await self.password_service.store_password_history(
                    user_id=user_id, password_hash=new_password_hash
                )

                return True

            except Exception as e:
                await session.rollback()
                if isinstance(e, ValueError):
                    raise
                raise RuntimeError(f"密码修改失败: {e}")

    @monitor_function("user")
    async def trust_device(
        self, user_id: str, device_fingerprint: str, ip_address: str
    ):
        """信任设备"""
        async with get_async_session() as session:
            try:
                trusted_device = TrustedDevice(
                    user_id=uuid.UUID(user_id),
                    device_fingerprint=device_fingerprint,
                    ip_address=ip_address,
                    created_at=datetime.utcnow(),
                    last_used_at=datetime.utcnow(),
                )

                session.add(trusted_device)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"设备信任失败: {e}")

    async def _get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_account_lockout(self, user_id: str) -> Dict[str, Any]:
        """检查账户锁定状态"""
        if not settings.ACCOUNT_LOCKOUT_ENABLED:
            return {"is_locked": False}

        lockout_key = f"account_lockout:{user_id}"
        lockout_data = await self.redis_client.get(lockout_key)

        if lockout_data:
            lockout_info = json.loads(lockout_data)  # 使用安全的JSON解析
            return {
                "is_locked": True,
                "locked_until": datetime.fromisoformat(lockout_info["locked_until"]),
                "attempt_count": lockout_info["attempt_count"],
            }

        return {"is_locked": False}

    async def _record_failed_attempt(self, user_id: str, login_context: Dict[str, Any]):
        """记录失败尝试"""
        if not settings.ACCOUNT_LOCKOUT_ENABLED:
            return

        attempts_key = f"login_attempts:{user_id}"
        attempt_count = await self.redis_client.incr(attempts_key)
        await self.redis_client.expire(attempts_key, 3600)  # 1小时过期

        if attempt_count >= settings.ACCOUNT_LOCKOUT_ATTEMPTS:
            # 锁定账户
            lockout_duration = settings.ACCOUNT_LOCKOUT_DURATION
            locked_until = datetime.utcnow() + timedelta(seconds=lockout_duration)

            lockout_data = {
                "locked_until": locked_until.isoformat(),
                "attempt_count": attempt_count,
                "ip_address": login_context.get("ip_address"),
            }

            lockout_key = f"account_lockout:{user_id}"
            await self.redis_client.setex(
                lockout_key, lockout_duration, str(lockout_data)
            )

            # 发布账户锁定事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "account_locked",
                        "severity": "high",
                        "description": f"账户因{attempt_count}次失败尝试被锁定",
                        "locked_until": locked_until.isoformat(),
                        "ip_address": login_context.get("ip_address"),
                    },
                    user_id=user_id,
                )

    async def _clear_failed_attempts(self, user_id: str):
        """清除失败尝试计数"""
        attempts_key = f"login_attempts:{user_id}"
        lockout_key = f"account_lockout:{user_id}"

        await self.redis_client.delete(attempts_key)
        await self.redis_client.delete(lockout_key)

    async def _record_successful_login(self, user: User, login_context: Dict[str, Any]):
        """记录成功登录"""
        async with get_async_session() as session:
            login_history = LoginHistory(
                user_id=user.id,
                ip_address=login_context.get("ip_address"),
                user_agent=login_context.get("user_agent"),
                device_info=login_context.get("device_info", {}),
                login_at=datetime.utcnow(),
                success=True,
            )

            session.add(login_history)
            await session.commit()

    async def _log_failed_login(
        self, email: str, reason: str, login_context: Dict[str, Any]
    ):
        """记录失败登录"""
        if self.message_publisher:
            await self.message_publisher.publish_message(
                message_type=MessageType.SECURITY_ALERT,
                data={
                    "event_type": "login_failed",
                    "email": email,
                    "reason": reason,
                    "ip_address": login_context.get("ip_address"),
                    "user_agent": login_context.get("user_agent"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def _handle_password_risk_factors(
        self, user: User, risk_factors: List[str], login_context: Dict[str, Any]
    ):
        """处理密码风险因素"""
        if "password_breach" in risk_factors:
            # 强制用户重置密码
            reset_token = await self._generate_reset_token(str(user.id))

            if not self.email_service:
                self.email_service = await get_email_service()

            await self.email_service.send_security_alert_email(
                email=user.email,
                first_name=user.first_name or "用户",
                alert_type="password_breach",
                details={
                    "message": "您的密码存在于已知泄露数据库中，请立即重置密码",
                    "reset_token": reset_token,
                },
            )

    async def _generate_verification_token(self, user_id: str) -> str:
        """生成邮箱验证令牌"""
        token = secrets.token_urlsafe(32)
        token_key = f"email_verification:{token}"

        await self.redis_client.setex(
            token_key, settings.EMAIL_VERIFICATION_TTL, user_id
        )

        return token

    async def _generate_reset_token(self, user_id: str) -> str:
        """生成密码重置令牌"""
        token = secrets.token_urlsafe(32)
        token_key = f"password_reset:{token}"

        await self.redis_client.setex(
            token_key, settings.EMAIL_RESET_PASSWORD_TTL, user_id
        )

        return token

    async def _verify_token(self, token: str, token_type: str) -> Optional[str]:
        """验证令牌"""
        token_key = f"{token_type}:{token}"
        user_id = await self.redis_client.get(token_key)
        return user_id

    async def _delete_token(self, token: str):
        """删除令牌"""
        # 删除所有可能的令牌类型
        for token_type in ["email_verification", "password_reset"]:
            token_key = f"{token_type}:{token}"
            await self.redis_client.delete(token_key)

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局用户服务实例
user_service = UserService()


# 提供给其他模块使用的函数
async def get_user_service() -> UserService:
    """获取用户服务实例"""
    return user_service
