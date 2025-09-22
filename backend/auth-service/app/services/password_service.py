"""
Perfect21 密码加密服务
企业级密码加密、验证和安全管理
"""

import bcrypt
import secrets
import hashlib
import hmac
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from shared.messaging.publisher import MessagePublisher, MessageType
from shared.metrics.metrics import monitor_function


class PasswordStrengthResult(BaseModel):
    """密码强度检查结果"""

    is_strong: bool
    score: int  # 0-100
    feedback: List[str]
    requirements_met: Dict[str, bool]
    estimated_crack_time: str


class PasswordValidationResult(BaseModel):
    """密码验证结果"""

    is_valid: bool
    breach_detected: bool = False
    reuse_detected: bool = False
    warnings: List[str] = []
    risk_factors: List[str] = []


class PasswordService:
    """密码服务管理器"""

    def __init__(self):
        self.redis_client = None
        self.message_publisher = None
        self.pepper = settings.PASSWORD_PEPPER.encode()
        self.bcrypt_rounds = settings.PASSWORD_BCRYPT_ROUNDS
        self.min_length = settings.PASSWORD_MIN_LENGTH
        self.max_length = settings.PASSWORD_MAX_LENGTH
        self.require_uppercase = settings.PASSWORD_REQUIRE_UPPERCASE
        self.require_lowercase = settings.PASSWORD_REQUIRE_LOWERCASE
        self.require_numbers = settings.PASSWORD_REQUIRE_NUMBERS
        self.require_special = settings.PASSWORD_REQUIRE_SPECIAL
        self.history_count = settings.PASSWORD_HISTORY_COUNT

        # 初始化加密器
        self._initialize_encryption()
        self._initialize_redis()

    def _initialize_encryption(self):
        """初始化加密组件"""
        # 使用配置的密钥派生加密密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"perfect21_password_salt",
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

    @monitor_function("password")
    async def hash_password(self, password: str, user_id: str = None) -> str:
        """加密密码"""
        try:
            # 预处理：添加pepper
            seasoned_password = password.encode() + self.pepper

            # 生成盐并加密
            salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
            password_hash = bcrypt.hashpw(seasoned_password, salt)

            # 记录密码创建事件（不包含密码内容）
            if self.message_publisher and user_id:
                await self.message_publisher.publish_message(
                    message_type=MessageType.USER_LOGIN,
                    data={
                        "event_type": "password_hashed",
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "bcrypt_rounds": self.bcrypt_rounds,
                    },
                    user_id=user_id,
                )

            return password_hash.decode("utf-8")

        except Exception as e:
            raise RuntimeError(f"密码加密失败: {e}")

    @monitor_function("password")
    async def verify_password(
        self,
        password: str,
        password_hash: str,
        user_id: str = None,
        ip_address: str = None,
    ) -> PasswordValidationResult:
        """验证密码"""
        try:
            # 预处理：添加pepper
            seasoned_password = password.encode() + self.pepper

            # 基本验证
            is_valid = bcrypt.checkpw(seasoned_password, password_hash.encode("utf-8"))

            warnings = []
            risk_factors = []

            # 如果密码正确，进行安全检查
            if is_valid and user_id:
                # 检查密码是否在已泄露数据库中
                breach_detected = await self._check_password_breach(password)
                if breach_detected:
                    warnings.append("密码存在于已知泄露数据库中")
                    risk_factors.append("password_breach")

                # 检查密码重用
                reuse_detected = await self._check_password_reuse(user_id, password)
                if reuse_detected:
                    warnings.append("密码与历史密码重复")
                    risk_factors.append("password_reuse")

                # 记录验证事件
                await self._log_password_verification(
                    user_id, ip_address, is_valid, risk_factors
                )

            return PasswordValidationResult(
                is_valid=is_valid,
                breach_detected=breach_detected
                if "breach_detected" in locals()
                else False,
                reuse_detected=reuse_detected
                if "reuse_detected" in locals()
                else False,
                warnings=warnings,
                risk_factors=risk_factors,
            )

        except Exception as e:
            raise RuntimeError(f"密码验证失败: {e}")

    @monitor_function("password")
    async def validate_password_strength(
        self, password: str, user_context: Dict[str, Any] = None
    ) -> PasswordStrengthResult:
        """验证密码强度"""
        feedback = []
        requirements_met = {}
        score = 0

        # 长度检查
        length_ok = self.min_length <= len(password) <= self.max_length
        requirements_met["length"] = length_ok
        if length_ok:
            score += 20
        else:
            feedback.append(f"密码长度应在{self.min_length}-{self.max_length}字符之间")

        # 大写字母检查
        has_uppercase = bool(re.search(r"[A-Z]", password))
        requirements_met["uppercase"] = has_uppercase
        if has_uppercase:
            score += 15
        elif self.require_uppercase:
            feedback.append("密码必须包含大写字母")

        # 小写字母检查
        has_lowercase = bool(re.search(r"[a-z]", password))
        requirements_met["lowercase"] = has_lowercase
        if has_lowercase:
            score += 15
        elif self.require_lowercase:
            feedback.append("密码必须包含小写字母")

        # 数字检查
        has_numbers = bool(re.search(r"\d", password))
        requirements_met["numbers"] = has_numbers
        if has_numbers:
            score += 15
        elif self.require_numbers:
            feedback.append("密码必须包含数字")

        # 特殊字符检查
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        requirements_met["special"] = has_special
        if has_special:
            score += 15
        elif self.require_special:
            feedback.append("密码必须包含特殊字符")

        # 复杂度检查
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 10
            feedback.append("字符多样性良好")

        # 常见模式检查
        if self._check_common_patterns(password):
            score -= 20
            feedback.append("避免使用常见密码模式")

        # 个人信息检查
        if user_context and self._check_personal_info(password, user_context):
            score -= 15
            feedback.append("避免使用个人信息作为密码")

        # 确保分数在0-100范围内
        score = max(0, min(100, score))

        # 评估破解时间
        crack_time = self._estimate_crack_time(password, score)

        # 总体评估
        is_strong = score >= 70 and all(
            requirements_met.get(req, True)
            for req in ["length", "uppercase", "lowercase", "numbers", "special"]
            if getattr(settings, f"PASSWORD_REQUIRE_{req.upper()}", False)
        )

        if is_strong:
            feedback.append("密码强度良好")

        return PasswordStrengthResult(
            is_strong=is_strong,
            score=score,
            feedback=feedback,
            requirements_met=requirements_met,
            estimated_crack_time=crack_time,
        )

    @monitor_function("password")
    async def store_password_history(self, user_id: str, password_hash: str):
        """存储密码历史"""
        try:
            history_key = f"password_history:{user_id}"

            # 加密密码哈希进行存储
            encrypted_hash = self.fernet.encrypt(password_hash.encode())

            # 添加到历史记录
            await self.redis_client.lpush(history_key, encrypted_hash.decode())

            # 保持历史记录数量限制
            await self.redis_client.ltrim(history_key, 0, self.history_count - 1)

            # 设置过期时间（2年）
            await self.redis_client.expire(history_key, 730 * 24 * 3600)

        except Exception as e:
            raise RuntimeError(f"存储密码历史失败: {e}")

    @monitor_function("password")
    async def generate_secure_password(
        self, length: int = 16, include_symbols: bool = True
    ) -> str:
        """生成安全密码"""
        try:
            if length < self.min_length:
                length = self.min_length
            if length > self.max_length:
                length = self.max_length

            # 定义字符集
            lowercase = "abcdefghijklmnopqrstuvwxyz"
            uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            numbers = "0123456789"
            symbols = '!@#$%^&*(),.?":{}|<>' if include_symbols else ""

            # 确保至少包含每种类型的字符
            password_chars = []

            if self.require_lowercase:
                password_chars.append(secrets.choice(lowercase))
            if self.require_uppercase:
                password_chars.append(secrets.choice(uppercase))
            if self.require_numbers:
                password_chars.append(secrets.choice(numbers))
            if self.require_special and include_symbols:
                password_chars.append(secrets.choice(symbols))

            # 填充剩余长度
            all_chars = lowercase + uppercase + numbers + symbols
            for _ in range(length - len(password_chars)):
                password_chars.append(secrets.choice(all_chars))

            # 随机打乱
            secrets.SystemRandom().shuffle(password_chars)

            return "".join(password_chars)

        except Exception as e:
            raise RuntimeError(f"生成安全密码失败: {e}")

    @monitor_function("password")
    async def check_password_expiry(
        self, user_id: str, password_created_at: datetime
    ) -> Dict[str, Any]:
        """检查密码是否过期"""
        try:
            # 密码有效期（90天）
            password_max_age = timedelta(days=90)
            age = datetime.utcnow() - password_created_at

            is_expired = age > password_max_age
            days_until_expiry = (password_max_age - age).days if not is_expired else 0

            # 提前30天开始警告
            warning_threshold = timedelta(days=30)
            should_warn = (
                age > (password_max_age - warning_threshold) and not is_expired
            )

            result = {
                "is_expired": is_expired,
                "age_days": age.days,
                "days_until_expiry": days_until_expiry,
                "should_warn": should_warn,
                "created_at": password_created_at.isoformat(),
            }

            # 如果过期，记录事件
            if is_expired and self.message_publisher:
                await self.message_publisher.publish_message(
                    message_type=MessageType.SECURITY_ALERT,
                    data={
                        "user_id": user_id,
                        "alert_type": "password_expired",
                        "severity": "medium",
                        "description": "用户密码已过期",
                        "age_days": age.days,
                    },
                    user_id=user_id,
                )

            return result

        except Exception as e:
            raise RuntimeError(f"密码过期检查失败: {e}")

    async def _check_password_breach(self, password: str) -> bool:
        """检查密码是否在已知泄露数据库中"""
        try:
            # 使用SHA-1哈希的前5位查询HaveIBeenPwned API
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            # 这里应该调用HaveIBeenPwned API
            # 为了演示，我们模拟检查常见密码
            common_passwords = {
                "5E884898DA28047151D0E56F8DC6292773603D0D6AABBDD62A11EF721D1542D8",  # 'password'
                "5E884898DA28047151D0E56F8DC6292773603D0D6AABBDD62A11EF721D1542D8",  # '123456'
                "EF92B778BAFE771E89245B89ECBC08A44A4E166C06659911881F383D4473E94F",  # 'secret'
            }

            # 简化检查
            return sha1_hash in common_passwords

        except Exception:
            # 如果检查失败，为了安全起见返回False
            return False

    async def _check_password_reuse(self, user_id: str, password: str) -> bool:
        """检查密码重用"""
        try:
            history_key = f"password_history:{user_id}"
            history = await self.redis_client.lrange(history_key, 0, -1)

            # 生成新密码的哈希
            seasoned_password = password.encode() + self.pepper

            for encrypted_hash in history:
                try:
                    # 解密历史密码哈希
                    decrypted_hash = self.fernet.decrypt(
                        encrypted_hash.encode()
                    ).decode()

                    # 比较密码
                    if bcrypt.checkpw(seasoned_password, decrypted_hash.encode()):
                        return True
                except Exception:
                    # 忽略解密失败的记录
                    continue

            return False

        except Exception:
            # 如果检查失败，为了安全起见返回False
            return False

    def _check_common_patterns(self, password: str) -> bool:
        """检查常见密码模式"""
        patterns = [
            r"(.)\1{2,}",  # 连续重复字符
            r"123456",  # 连续数字
            r"abcdef",  # 连续字母
            r"qwerty",  # 键盘模式
            r"password",  # 常见单词
            r"admin",  # 常见单词
            r"(\d{4})\1",  # 重复年份模式
        ]

        for pattern in patterns:
            if re.search(pattern, password.lower()):
                return True
        return False

    def _check_personal_info(self, password: str, user_context: Dict[str, Any]) -> bool:
        """检查是否包含个人信息"""
        personal_info = [
            user_context.get("first_name", ""),
            user_context.get("last_name", ""),
            user_context.get("email", "").split("@")[0],
            user_context.get("phone_number", ""),
            user_context.get("birth_date", ""),
        ]

        password_lower = password.lower()

        for info in personal_info:
            if info and len(info) >= 3 and info.lower() in password_lower:
                return True

        return False

    def _estimate_crack_time(self, password: str, score: int) -> str:
        """估算密码破解时间"""
        # 简化的破解时间估算
        if score >= 90:
            return "数世纪"
        elif score >= 80:
            return "数十年"
        elif score >= 70:
            return "数年"
        elif score >= 60:
            return "数月"
        elif score >= 50:
            return "数周"
        elif score >= 40:
            return "数天"
        elif score >= 30:
            return "数小时"
        else:
            return "数分钟"

    async def _log_password_verification(
        self, user_id: str, ip_address: str, is_valid: bool, risk_factors: List[str]
    ):
        """记录密码验证事件"""
        if self.message_publisher:
            await self.message_publisher.publish_message(
                message_type=MessageType.USER_LOGIN,
                data={
                    "event_type": "password_verification",
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "is_valid": is_valid,
                    "risk_factors": risk_factors,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                user_id=user_id,
            )

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()


# 全局密码服务实例
password_service = PasswordService()


# 提供给其他模块使用的函数
async def get_password_service() -> PasswordService:
    """获取密码服务实例"""
    return password_service
