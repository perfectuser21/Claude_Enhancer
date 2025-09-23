"""
Claude Enhancer JWT Token管理服务
企业级JWT Token生成、验证、管理
"""

import asyncio
import secrets
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function


class TokenClaims(BaseModel):
    """Token声明"""

    user_id: str
    permissions: List[str]
    roles: List[str]
    device_fingerprint: str
    ip_address: str
    issued_at: int
    expires_at: int
    jti: str
    token_type: str


class TokenValidationResult(BaseModel):
    """Token验证结果"""

    valid: bool
    claims: Optional[TokenClaims] = None
    error: Optional[str] = None
    warnings: List[str] = []
    risk_factors: List[str] = []


class JWTTokenManager:
    """JWT Token管理器"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.algorithm = settings.JWT_ALGORITHM
        self.issuer = settings.JWT_ISSUER
        self.audience = settings.JWT_AUDIENCE
        self.access_token_ttl = settings.JWT_ACCESS_TOKEN_TTL
        self.refresh_token_ttl = settings.JWT_REFRESH_TOKEN_TTL
        self.key_rotation_interval = settings.JWT_KEY_ROTATION_INTERVAL

        # 初始化组件
        self._initialize()

    def _initialize(self):
        """初始化Redis和消息发布者"""
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    async def set_message_publisher(self, publisher: MessagePublisher):
        """设置消息发布者"""
        self.message_publisher = publisher

    @monitor_function("token")
    async def generate_token_pair(
        self,
        user_id: str,
        permissions: List[str],
        device_info: Dict[str, Any],
        ip_address: str,
    ) -> Dict[str, Any]:
        """生成访问令牌和刷新令牌对"""

        current_time = datetime.utcnow()
        access_jti = secrets.token_urlsafe(32)
        refresh_jti = secrets.token_urlsafe(32)

        # 生成设备指纹
        device_fingerprint = self._generate_device_fingerprint(device_info)

        # 访问令牌负载
        access_payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": int(current_time.timestamp()),
            "exp": int(
                (current_time + timedelta(seconds=self.access_token_ttl)).timestamp()
            ),
            "jti": access_jti,
            "scope": permissions,
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "token_type": "access",
        }

        # 刷新令牌负载
        refresh_payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": int(current_time.timestamp()),
            "exp": int(
                (current_time + timedelta(seconds=self.refresh_token_ttl)).timestamp()
            ),
            "jti": refresh_jti,
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "token_type": "refresh",
        }

        # 获取当前私钥
        private_key = await self._get_current_private_key()

        # 添加密钥ID到头部
        headers = {"kid": await self._get_current_key_id()}

        # 生成Token
        access_token = jwt.encode(
            access_payload, private_key, algorithm=self.algorithm, headers=headers
        )

        refresh_token = jwt.encode(
            refresh_payload, private_key, algorithm=self.algorithm, headers=headers
        )

        # 存储Token元数据到Redis
        await self._store_token_metadata(
            access_jti,
            user_id,
            "access",
            self.access_token_ttl,
            {
                "device_fingerprint": device_fingerprint,
                "ip_address": ip_address,
                "permissions": permissions,
            },
        )

        await self._store_token_metadata(
            refresh_jti,
            user_id,
            "refresh",
            self.refresh_token_ttl,
            {
                "device_fingerprint": device_fingerprint,
                "ip_address": ip_address,
                "linked_access_jti": access_jti,
            },
        )

        # 记录Token生成事件
        if self.message_publisher:
            await self.message_publisher.publish_message(
                message_type=MessageType.USER_LOGIN,
                data={
                    "user_id": user_id,
                    "token_generated": True,
                    "access_jti": access_jti,
                    "refresh_jti": refresh_jti,
                    "ip_address": ip_address,
                    "device_fingerprint": device_fingerprint,
                },
                user_id=user_id,
            )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
            "scope": permissions,
            "issued_at": current_time.isoformat(),
            "device_fingerprint": device_fingerprint,
        }

    @monitor_function("token")
    async def validate_token(
        self, token: str, client_ip: str = None, user_agent: str = None
    ) -> TokenValidationResult:
        """验证Token有效性"""
        try:
            # 解码Token头部获取密钥ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                return TokenValidationResult(
                    valid=False, error="Missing key ID in token header"
                )

            # 获取对应公钥
            public_key = await self._get_public_key(kid)
            if not public_key:
                return TokenValidationResult(valid=False, error="Invalid key ID")

            # 验证Token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )

            jti = payload.get("jti")
            user_id = payload.get("sub")

            # 检查Token是否在黑名单
            if await self._is_token_blacklisted(jti):
                return TokenValidationResult(
                    valid=False, error="Token has been revoked"
                )

            # 检查Token元数据
            token_metadata = await self._get_token_metadata(jti)
            if not token_metadata or token_metadata.get("active") != "true":
                return TokenValidationResult(
                    valid=False, error="Token metadata invalid or inactive"
                )

            # 安全检查
            warnings = []
            risk_factors = []

            # IP地址检查
            token_ip = payload.get("ip_address")
            if client_ip and token_ip and client_ip != token_ip:
                warnings.append("IP address changed")
                risk_factors.append("ip_change")

            # 设备指纹检查
            if user_agent:
                current_fingerprint = self._generate_device_fingerprint(
                    {"user_agent": user_agent}
                )
                token_fingerprint = payload.get("device_fingerprint")
                if current_fingerprint != token_fingerprint:
                    warnings.append("Device fingerprint mismatch")
                    risk_factors.append("device_mismatch")

            # 创建Token声明对象
            claims = TokenClaims(
                user_id=user_id,
                permissions=payload.get("scope", []),
                roles=payload.get("roles", []),
                device_fingerprint=payload.get("device_fingerprint", ""),
                ip_address=payload.get("ip_address", ""),
                issued_at=payload.get("iat", 0),
                expires_at=payload.get("exp", 0),
                jti=jti,
                token_type=payload.get("token_type", "access"),
            )

            # 高风险检查
            if len(risk_factors) >= 2:
                # 自动撤销高风险Token
                await self.revoke_token(jti, "high_risk_detected")

                # 发送安全警告
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.SECURITY_ALERT,
                        data={
                            "user_id": user_id,
                            "alert_type": "suspicious_token_usage",
                            "severity": "high",
                            "description": "High-risk token usage detected",
                            "risk_factors": risk_factors,
                            "ip_address": client_ip,
                            "user_agent": user_agent,
                        },
                        user_id=user_id,
                        priority=7,
                    )

                return TokenValidationResult(
                    valid=False,
                    error="Token usage flagged as high risk",
                    risk_factors=risk_factors,
                )

            return TokenValidationResult(
                valid=True, claims=claims, warnings=warnings, risk_factors=risk_factors
            )

        except jwt.ExpiredSignatureError:
            await self._cleanup_expired_token(token)
            return TokenValidationResult(valid=False, error="Token has expired")
        except jwt.InvalidTokenError as e:
            return TokenValidationResult(valid=False, error=f"Invalid token: {str(e)}")
        except Exception as e:
            return TokenValidationResult(
                valid=False, error=f"Token validation error: {str(e)}"
            )

    @monitor_function("token")
    async def refresh_token(
        self, refresh_token: str, client_ip: str = None
    ) -> Dict[str, Any]:
        """刷新访问令牌"""

        # 验证refresh token
        validation_result = await self.validate_token(refresh_token, client_ip)

        if not validation_result.valid:
            raise ValueError(f"Invalid refresh token: {validation_result.error}")

        claims = validation_result.claims

        if claims.token_type != "refresh":
            raise ValueError("Token is not a refresh token")

        # 撤销旧的refresh token
        await self.revoke_token(claims.jti, "token_refreshed")

        # 撤销关联的access token
        metadata = await self._get_token_metadata(claims.jti)
        linked_access_jti = metadata.get("linked_access_jti")
        if linked_access_jti:
            await self.revoke_token(linked_access_jti, "token_refreshed")

        # 生成新的token对
        return await self.generate_token_pair(
            user_id=claims.user_id,
            permissions=claims.permissions,
            device_info={"user_agent": "refresh"},  # 简化设备信息
            ip_address=client_ip or claims.ip_address,
        )

    @monitor_function("token")
    async def revoke_token(self, jti: str, reason: str = "user_request"):
        """撤销Token"""
        try:
            # 添加到黑名单
            await self.redis_client.sadd("token_blacklist", jti)
            await self.redis_client.expire("token_blacklist", self.refresh_token_ttl)

            # 更新Token元数据
            metadata_key = f"token_metadata:{jti}"
            await self.redis_client.hset(
                metadata_key,
                mapping={
                    "active": "false",
                    "revoked_at": datetime.utcnow().isoformat(),
                    "revoke_reason": reason,
                },
            )

            # 记录撤销事件
            await self._log_token_event(
                "token_revoked",
                jti,
                {"reason": reason, "timestamp": datetime.utcnow().isoformat()},
            )

        except Exception as e:
            raise RuntimeError(f"Failed to revoke token: {e}")

    @monitor_function("token")
    async def revoke_all_user_tokens(
        self, user_id: str, reason: str = "security_measure"
    ):
        """撤销用户的所有Token"""
        try:
            # 获取用户所有Token
            user_tokens_key = f"user_tokens:{user_id}"
            token_jtis = await self.redis_client.smembers(user_tokens_key)

            revoked_count = 0
            for jti in token_jtis:
                await self.revoke_token(jti, reason)
                revoked_count += 1

            # 清除用户Token索引
            await self.redis_client.delete(user_tokens_key)

            # 记录批量撤销事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "bulk_token_revocation",
                        "severity": "medium",
                        "description": f"All user tokens revoked: {reason}",
                        "revoked_count": revoked_count,
                    },
                    user_id=user_id,
                )

            return revoked_count

        except Exception as e:
            raise RuntimeError(f"Failed to revoke user tokens: {e}")

    async def rotate_keys(self):
        """密钥轮换"""
        try:
            # 生成新的RSA密钥对
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )

            # 序列化私钥和公钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode()

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()

            # 生成密钥ID
            kid = f"key-{int(time.time())}"

            # 存储新密钥
            await self.redis_client.hset(
                "jwt_keys",
                mapping={
                    f"private:{kid}": private_pem,
                    f"public:{kid}": public_pem,
                    "current_kid": kid,
                },
            )

            # 设置旧密钥过期时间（24小时后）
            await self._schedule_key_cleanup(kid)

            # 记录密钥轮换事件
            await self._log_security_event("key_rotation", {"new_kid": kid})

            return kid

        except Exception as e:
            raise RuntimeError(f"Key rotation failed: {e}")

    async def ensure_keys_exist(self):
        """确保JWT密钥存在"""
        current_kid = await self.redis_client.hget("jwt_keys", "current_kid")

        if not current_kid:
            # 首次启动，生成初始密钥
            await self.rotate_keys()

    async def batch_validate_tokens(
        self, tokens: List[str]
    ) -> List[TokenValidationResult]:
        """批量验证Token"""
        results = []

        # 并发验证所有Token
        validation_tasks = [self.validate_token(token) for token in tokens]

        validation_results = await asyncio.gather(
            *validation_tasks, return_exceptions=True
        )

        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                results.append(
                    TokenValidationResult(
                        valid=False, error=f"Validation error: {str(result)}"
                    )
                )
            else:
                results.append(result)

        return results

    def _generate_device_fingerprint(self, device_info: Dict[str, Any]) -> str:
        """生成设备指纹"""
        import hashlib

        fingerprint_data = {
            "user_agent": device_info.get("user_agent", ""),
            "screen_resolution": device_info.get("screen_resolution", ""),
            "timezone": device_info.get("timezone", ""),
            "language": device_info.get("language", ""),
            "platform": device_info.get("platform", ""),
        }

        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    async def _store_token_metadata(
        self,
        jti: str,
        user_id: str,
        token_type: str,
        ttl: int,
        extra_data: Dict[str, Any],
    ):
        """存储Token元数据"""
        metadata = {
            "jti": jti,
            "user_id": user_id,
            "token_type": token_type,
            "active": "true",
            "created_at": datetime.utcnow().isoformat(),
            **extra_data,
        }

        metadata_key = f"token_metadata:{jti}"
        await self.redis_client.hset(metadata_key, mapping=metadata)
        await self.redis_client.expire(metadata_key, ttl)

        # 维护用户Token索引
        user_tokens_key = f"user_tokens:{user_id}"
        await self.redis_client.sadd(user_tokens_key, jti)
        await self.redis_client.expire(user_tokens_key, ttl)

    async def _get_token_metadata(self, jti: str) -> Optional[Dict[str, str]]:
        """获取Token元数据"""
        metadata_key = f"token_metadata:{jti}"
        metadata = await self.redis_client.hgetall(metadata_key)
        return metadata if metadata else None

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """检查Token是否在黑名单"""
        return await self.redis_client.sismember("token_blacklist", jti)

    async def _get_current_private_key(self) -> bytes:
        """获取当前私钥"""
        kid = await self._get_current_key_id()
        if not kid:
            await self.rotate_keys()
            kid = await self._get_current_key_id()

        private_key_pem = await self.redis_client.hget("jwt_keys", f"private:{kid}")
        if not private_key_pem:
            raise RuntimeError("Private key not found")

        return serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )

    async def _get_public_key(self, kid: str) -> Optional[bytes]:
        """获取公钥"""
        public_key_pem = await self.redis_client.hget("jwt_keys", f"public:{kid}")
        if not public_key_pem:
            return None

        return serialization.load_pem_public_key(
            public_key_pem.encode(), backend=default_backend()
        )

    async def _get_current_key_id(self) -> Optional[str]:
        """获取当前密钥ID"""
        return await self.redis_client.hget("jwt_keys", "current_kid")

    async def _schedule_key_cleanup(self, new_kid: str):
        """安排旧密钥清理"""
        # 这里可以使用Celery或其他任务队列来安排延迟清理
        # 简化实现：设置过期时间
        cleanup_time = 86400  # 24小时

        # 获取所有密钥
        all_keys = await self.redis_client.hkeys("jwt_keys")
        for key in all_keys:
            if key.startswith(("private:", "public:")) and not key.endswith(new_kid):
                await self.redis_client.expire(f"jwt_keys:{key}", cleanup_time)

    async def _cleanup_expired_token(self, token: str):
        """清理过期Token"""
        try:
            # 解码获取JTI（不验证过期时间）
            payload = jwt.decode(
                token, options={"verify_exp": False, "verify_signature": False}
            )
            jti = payload.get("jti")
            if jti:
                await self.redis_client.delete(f"token_metadata:{jti}")
        except:
            pass  # 忽略清理错误

    async def _log_token_event(
        self, event_type: str, jti: str, details: Dict[str, Any]
    ):
        """记录Token事件"""
        if self.message_publisher:
            await self.message_publisher.publish_message(
                message_type=MessageType.USER_LOGIN,  # 使用合适的消息类型
                data={
                    "event_type": event_type,
                    "jti": jti,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """记录安全事件"""
        if self.message_publisher:
            await self.message_publisher.publish_message(
                message_type=MessageType.SECURITY_ALERT,
                data={
                    "event_type": event_type,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局JWT管理器实例
jwt_manager = JWTTokenManager()


# 提供给其他模块使用的函数
async def get_jwt_manager() -> JWTTokenManager:
    """获取JWT管理器实例"""
    return jwt_manager
