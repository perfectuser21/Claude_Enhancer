"""
Perfect21 多因子认证服务
TOTP、SMS、邮件验证码和备用码管理
"""

import secrets
import qrcode
import pyotp
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
import json
from pydantic import BaseModel
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function


class MFAMethod(BaseModel):
    """多因子认证方法"""

    method_type: str  # totp, sms, email, backup_code
    is_enabled: bool
    is_primary: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MFAChallenge(BaseModel):
    """多因子认证挑战"""

    challenge_id: str
    user_id: str
    method_type: str
    expires_at: datetime
    attempts_remaining: int
    ip_address: str
    metadata: Optional[Dict[str, Any]] = None


class MFAVerificationResult(BaseModel):
    """多因子认证验证结果"""

    valid: bool
    user_id: Optional[str] = None
    method_used: Optional[str] = None
    error: Optional[str] = None
    remaining_attempts: Optional[int] = None


class MFAService:
    """多因子认证服务管理器"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.totp_issuer = settings.MFA_TOTP_ISSUER
        self.totp_window = settings.MFA_TOTP_WINDOW
        self.backup_codes_count = settings.MFA_BACKUP_CODES_COUNT
        self.sms_valid_minutes = settings.MFA_SMS_VALID_MINUTES
        self.email_valid_minutes = settings.MFA_EMAIL_VALID_MINUTES

        # 初始化加密器
        self._initialize_encryption()
        self._initialize_redis()

    def _initialize_encryption(self):
        """初始化加密组件"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"perfect21_mfa_salt",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.DATA_ENCRYPTION_KEY.encode())
        )
        self.fernet = Fernet(key)

    def _initialize_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    async def set_message_publisher(self, publisher: MessagePublisher):
        """设置消息发布者"""
        self.message_publisher = publisher

    @monitor_function("mfa")
    async def setup_totp(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """设置TOTP多因子认证"""
        try:
            # 生成TOTP密钥
            secret = pyotp.random_base32()

            # 创建TOTP对象
            totp = pyotp.TOTP(secret)

            # 生成二维码URL
            provisioning_uri = totp.provisioning_uri(
                name=user_email, issuer_name=self.totp_issuer
            )

            # 生成二维码图片
            qr_code = self._generate_qr_code(provisioning_uri)

            # 加密并存储密钥（未验证状态）
            encrypted_secret = self.fernet.encrypt(secret.encode()).decode()

            setup_key = f"mfa_setup:{user_id}:totp"
            setup_data = {
                "secret": encrypted_secret,
                "created_at": datetime.utcnow().isoformat(),
                "verified": False,
            }

            await self.redis_client.setex(
                setup_key, 1800, json.dumps(setup_data)  # 30分钟过期
            )

            # 生成备用码
            backup_codes = self._generate_backup_codes()

            return {
                "secret": secret,
                "qr_code": qr_code,
                "provisioning_uri": provisioning_uri,
                "backup_codes": backup_codes,
            }

        except Exception as e:
            raise RuntimeError(f"TOTP设置失败: {e}")

    @monitor_function("mfa")
    async def verify_totp_setup(self, user_id: str, verification_code: str) -> bool:
        """验证TOTP设置"""
        try:
            setup_key = f"mfa_setup:{user_id}:totp"
            setup_data = await self.redis_client.get(setup_key)

            if not setup_data:
                return False

            setup_info = json.loads(setup_data)

            # 解密密钥
            encrypted_secret = setup_info["secret"]
            secret = self.fernet.decrypt(encrypted_secret.encode()).decode()

            # 验证验证码
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(verification_code, valid_window=self.totp_window)

            if is_valid:
                # 标记为已验证
                setup_info["verified"] = True
                setup_info["verified_at"] = datetime.utcnow().isoformat()

                await self.redis_client.setex(
                    setup_key, 3600, json.dumps(setup_info)  # 延長1小时等待激活
                )

                # 记录验证事件
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.USER_LOGIN,
                        data={
                            "event_type": "totp_setup_verified",
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        user_id=user_id,
                    )

            return is_valid

        except Exception as e:
            raise RuntimeError(f"TOTP验证失败: {e}")

    @monitor_function("mfa")
    async def enable_totp(self, user_id: str) -> bool:
        """启用TOTP多因子认证"""
        try:
            setup_key = f"mfa_setup:{user_id}:totp"
            setup_data = await self.redis_client.get(setup_key)

            if not setup_data:
                return False

            setup_info = json.loads(setup_data)

            if not setup_info.get("verified"):
                return False

            # 移动到正式存储
            mfa_key = f"mfa_methods:{user_id}:totp"
            mfa_data = {
                "secret": setup_info["secret"],
                "enabled": True,
                "is_primary": True,
                "created_at": setup_info["created_at"],
                "enabled_at": datetime.utcnow().isoformat(),
            }

            await self.redis_client.set(mfa_key, json.dumps(mfa_data))

            # 清理设置数据
            await self.redis_client.delete(setup_key)

            # 记录启用事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "mfa_enabled",
                        "severity": "low",
                        "description": "TOTP多因子认证已启用",
                        "method": "totp",
                    },
                    user_id=user_id,
                )

            return True

        except Exception as e:
            raise RuntimeError(f"TOTP启用失败: {e}")

    @monitor_function("mfa")
    async def generate_mfa_challenge(
        self, user_id: str, ip_address: str, preferred_method: str = None
    ) -> str:
        """生成多因子认证挑战"""
        try:
            # 获取用户的MFA方法
            available_methods = await self._get_user_mfa_methods(user_id)

            if not available_methods:
                raise ValueError("用户未启用多因子认证")

            # 选择认证方法
            method = (
                preferred_method
                if preferred_method in available_methods
                else available_methods[0]
            )

            # 生成挑战ID
            challenge_id = secrets.token_urlsafe(32)

            # 创建挑战
            challenge = MFAChallenge(
                challenge_id=challenge_id,
                user_id=user_id,
                method_type=method,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                attempts_remaining=3,
                ip_address=ip_address,
            )

            # 存储挑战
            challenge_key = f"mfa_challenge:{challenge_id}"
            await self.redis_client.setex(
                challenge_key, 600, challenge.json()  # 10分钟过期
            )

            # 根据方法发送验证码
            if method == "sms":
                await self._send_sms_code(user_id, challenge_id)
            elif method == "email":
                await self._send_email_code(user_id, challenge_id)

            return challenge_id

        except Exception as e:
            raise RuntimeError(f"生成MFA挑战失败: {e}")

    @monitor_function("mfa")
    async def verify_mfa_challenge(
        self, mfa_token: str, verification_code: str, ip_address: str
    ) -> Dict[str, Any]:
        """验证多因子认证挑战"""
        try:
            # 获取挑战信息
            challenge_key = f"mfa_challenge:{mfa_token}"
            challenge_data = await self.redis_client.get(challenge_key)

            if not challenge_data:
                return {"valid": False, "error": "MFA挑战不存在或已过期"}

            challenge = MFAChallenge.parse_raw(challenge_data)

            # 检查过期时间
            if datetime.utcnow() > challenge.expires_at:
                await self.redis_client.delete(challenge_key)
                return {"valid": False, "error": "MFA挑战已过期"}

            # 检查尝试次数
            if challenge.attempts_remaining <= 0:
                await self.redis_client.delete(challenge_key)
                return {"valid": False, "error": "MFA验证尝试次数已用尽"}

            # 验证验证码
            is_valid = False

            if challenge.method_type == "totp":
                is_valid = await self._verify_totp_code(
                    challenge.user_id, verification_code
                )
            elif challenge.method_type == "sms":
                is_valid = await self._verify_sms_code(mfa_token, verification_code)
            elif challenge.method_type == "email":
                is_valid = await self._verify_email_code(mfa_token, verification_code)
            elif challenge.method_type == "backup_code":
                is_valid = await self._verify_backup_code(
                    challenge.user_id, verification_code
                )

            if is_valid:
                # 清理成功的挑战
                await self.redis_client.delete(challenge_key)

                # 更新最后使用时间
                await self._update_method_last_used(
                    challenge.user_id, challenge.method_type
                )

                # 记录成功事件
                if self.message_publisher:
                    await self.message_publisher.publish_message(
                        message_type=MessageType.USER_LOGIN,
                        data={
                            "event_type": "mfa_verification_success",
                            "user_id": challenge.user_id,
                            "method": challenge.method_type,
                            "ip_address": ip_address,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        user_id=challenge.user_id,
                    )

                return {
                    "valid": True,
                    "user_id": challenge.user_id,
                    "method_used": challenge.method_type,
                }
            else:
                # 减少尝试次数
                challenge.attempts_remaining -= 1

                if challenge.attempts_remaining > 0:
                    # 更新挑战
                    await self.redis_client.setex(
                        challenge_key,
                        int((challenge.expires_at - datetime.utcnow()).total_seconds()),
                        challenge.json(),
                    )
                else:
                    # 删除已用尽的挑战
                    await self.redis_client.delete(challenge_key)

                return {
                    "valid": False,
                    "error": "验证码错误",
                    "remaining_attempts": challenge.attempts_remaining,
                }

        except Exception as e:
            raise RuntimeError(f"MFA验证失败: {e}")

    async def _get_user_mfa_methods(self, user_id: str) -> List[str]:
        """获取用户的MFA方法"""
        methods = []

        # 检查TOTP
        totp_key = f"mfa_methods:{user_id}:totp"
        totp_data = await self.redis_client.get(totp_key)
        if totp_data:
            totp_info = json.loads(totp_data)
            if totp_info.get("enabled"):
                methods.append("totp")

        # 检查备用码
        backup_key = f"mfa_backup_codes:{user_id}"
        backup_codes = await self.redis_client.get(backup_key)
        if backup_codes:
            codes = json.loads(backup_codes)
            if any(not code.get("used") for code in codes):
                methods.append("backup_code")

        return methods

    async def _verify_totp_code(self, user_id: str, code: str) -> bool:
        """验证TOTP验证码"""
        try:
            totp_key = f"mfa_methods:{user_id}:totp"
            totp_data = await self.redis_client.get(totp_key)

            if not totp_data:
                return False

            totp_info = json.loads(totp_data)
            if not totp_info.get("enabled"):
                return False

            # 解密密钥
            encrypted_secret = totp_info["secret"]
            secret = self.fernet.decrypt(encrypted_secret.encode()).decode()

            # 验证验证码
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=self.totp_window)

        except Exception:
            return False

    async def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """验证备用码"""
        try:
            backup_key = f"mfa_backup_codes:{user_id}"
            backup_data = await self.redis_client.get(backup_key)

            if not backup_data:
                return False

            backup_codes = json.loads(backup_data)

            # 查找匹配的未使用备用码
            for backup_code in backup_codes:
                if not backup_code.get("used") and backup_code["code"] == code:
                    # 标记为已使用
                    backup_code["used"] = True
                    backup_code["used_at"] = datetime.utcnow().isoformat()

                    # 更新存储
                    await self.redis_client.set(backup_key, json.dumps(backup_codes))

                    return True

            return False

        except Exception:
            return False

    async def _send_sms_code(self, user_id: str, challenge_id: str):
        """发送SMS验证码（简化实现）"""
        # 生成验证码
        code = secrets.randbelow(1000000)
        verification_code = f"{code:06d}"

        # 存储验证码
        code_key = f"mfa_sms_code:{challenge_id}"
        await self.redis_client.setex(
            code_key, self.sms_valid_minutes * 60, verification_code
        )

        # 这里应该集成SMS服务发送验证码
        # 为了演示，我们只记录日志

    # print(f"SMS验证码（仅用于演示）: {verification_code}")

    async def _send_email_code(self, user_id: str, challenge_id: str):
        """发送邮件验证码（简化实现）"""
        # 生成验证码
        code = secrets.randbelow(1000000)
        verification_code = f"{code:06d}"

        # 存储验证码
        code_key = f"mfa_email_code:{challenge_id}"
        await self.redis_client.setex(
            code_key, self.email_valid_minutes * 60, verification_code
        )

        # 这里应该集成邮件服务发送验证码
        # 为了演示，我们只记录日志

    # print(f"邮件验证码（仅用于演示）: {verification_code}")

    async def _verify_sms_code(self, challenge_id: str, code: str) -> bool:
        """验证SMS验证码"""
        code_key = f"mfa_sms_code:{challenge_id}"
        stored_code = await self.redis_client.get(code_key)

        if stored_code and stored_code == code:
            await self.redis_client.delete(code_key)
            return True

        return False

    async def _verify_email_code(self, challenge_id: str, code: str) -> bool:
        """验证邮件验证码"""
        code_key = f"mfa_email_code:{challenge_id}"
        stored_code = await self.redis_client.get(code_key)

        if stored_code and stored_code == code:
            await self.redis_client.delete(code_key)
            return True

        return False

    async def _update_method_last_used(self, user_id: str, method_type: str):
        """更新MFA方法最后使用时间"""
        if method_type == "totp":
            totp_key = f"mfa_methods:{user_id}:totp"
            totp_data = await self.redis_client.get(totp_key)
            if totp_data:
                totp_info = json.loads(totp_data)
                totp_info["last_used_at"] = datetime.utcnow().isoformat()
                await self.redis_client.set(totp_key, json.dumps(totp_info))

    def _generate_qr_code(self, provisioning_uri: str) -> str:
        """生成二维码图片"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为Base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def _generate_backup_codes(self) -> List[str]:
        """生成备用码"""
        codes = []
        for _ in range(self.backup_codes_count):
            # 生成 8 位数字备用码
            code = secrets.randbelow(100000000)
            codes.append(f"{code:08d}")
        return codes

    @monitor_function("mfa")
    async def store_backup_codes(self, user_id: str, codes: List[str]):
        """存储备用码"""
        try:
            backup_codes = []
            for code in codes:
                backup_codes.append(
                    {
                        "code": code,
                        "used": False,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )

            backup_key = f"mfa_backup_codes:{user_id}"
            await self.redis_client.set(backup_key, json.dumps(backup_codes))

        except Exception as e:
            raise RuntimeError(f"存储备用码失败: {e}")

    @monitor_function("mfa")
    async def disable_mfa(self, user_id: str) -> bool:
        """禁用多因子认证"""
        try:
            # 删除所有MFA方法
            totp_key = f"mfa_methods:{user_id}:totp"
            backup_key = f"mfa_backup_codes:{user_id}"

            await self.redis_client.delete(totp_key)
            await self.redis_client.delete(backup_key)

            # 记录禁用事件
            if self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "mfa_disabled",
                        "severity": "medium",
                        "description": "多因子认证已禁用",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    user_id=user_id,
                )

            return True

        except Exception as e:
            raise RuntimeError(f"禁用MFA失败: {e}")

    @monitor_function("mfa")
    async def get_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """获取MFA状态"""
        try:
            status = {"enabled": False, "methods": {}, "backup_codes_remaining": 0}

            # 检查TOTP
            totp_key = f"mfa_methods:{user_id}:totp"
            totp_data = await self.redis_client.get(totp_key)
            if totp_data:
                totp_info = json.loads(totp_data)
                if totp_info.get("enabled"):
                    status["enabled"] = True
                    status["methods"]["totp"] = {
                        "enabled": True,
                        "created_at": totp_info.get("created_at"),
                        "last_used_at": totp_info.get("last_used_at"),
                    }

            # 检查备用码
            backup_key = f"mfa_backup_codes:{user_id}"
            backup_data = await self.redis_client.get(backup_key)
            if backup_data:
                backup_codes = json.loads(backup_data)
                remaining = sum(1 for code in backup_codes if not code.get("used"))
                status["backup_codes_remaining"] = remaining

            return status

        except Exception as e:
            raise RuntimeError(f"获取MFA状态失败: {e}")

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局MFA服务实例
mfa_service = MFAService()


# 提供给其他模块使用的函数
async def get_mfa_service() -> MFAService:
    """获取MFA服务实例"""
    return mfa_service
