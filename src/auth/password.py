"""
密码安全处理模块
实现bcrypt密码哈希、验证、强度检查等功能
包含密码策略和安全措施
"""

import bcrypt
import re
import secrets
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class PasswordManager:
    """密码管理器"""

    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_numbers: bool = True,
        require_symbols: bool = True,
        bcrypt_rounds: int = 12,
    ):
        """
        初始化密码管理器

        Args:
            min_length: 最小密码长度
            max_length: 最大密码长度
            require_uppercase: 是否需要大写字母
            require_lowercase: 是否需要小写字母
            require_numbers: 是否需要数字
            require_symbols: 是否需要特殊符号
            bcrypt_rounds: bcrypt加密轮数（越高越安全但越慢）
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_symbols = require_symbols
        self.bcrypt_rounds = bcrypt_rounds

        # 常见弱密码列表（实际使用时应从文件加载更完整的列表）
        self.common_passwords = {
            "password",
            "123456",
            "123456789",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "root",
            "user",
            "guest",
            "12345678",
            "111111",
            "1234567890",
            "welcome",
            "login",
            "passw0rd",
            "1qaz2wsx",
            "letmein",
        }

        # 密码历史存储（生产环境应使用数据库）
        self.password_history = {}

    def hash_password(self, password: str) -> str:
        """
        使用bcrypt加密密码

        Args:
            password: 明文密码

        Returns:
            str: 加密后的密码哈希
        """
        # 将密码编码为字节
        password_bytes = password.encode("utf-8")

        # 生成盐并加密
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        # 返回字符串格式
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 存储的密码哈希

        Returns:
            bool: 密码正确返回True
        """
        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

    def validate_password_strength(
        self, password: str, username: str = None
    ) -> Dict[str, any]:
        """
        验证密码强度

        Args:
            password: 待验证的密码
            username: 用户名（用于检查密码是否包含用户名）

        Returns:
            Dict: 验证结果，包含is_valid和错误信息
        """
        errors = []
        warnings = []
        score = 0
        max_score = 100

        # 检查长度
        if len(password) < self.min_length:
            errors.append(f"密码长度至少需要{self.min_length}个字符")
        elif len(password) >= self.min_length:
            score += 10

        if len(password) > self.max_length:
            errors.append(f"密码长度不能超过{self.max_length}个字符")

        # 检查字符类型
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_symbol = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password))

        if self.require_uppercase and not has_upper:
            errors.append("密码必须包含至少一个大写字母")
        elif has_upper:
            score += 15

        if self.require_lowercase and not has_lower:
            errors.append("密码必须包含至少一个小写字母")
        elif has_lower:
            score += 15

        if self.require_numbers and not has_digit:
            errors.append("密码必须包含至少一个数字")
        elif has_digit:
            score += 15

        if self.require_symbols and not has_symbol:
            errors.append("密码必须包含至少一个特殊字符")
        elif has_symbol:
            score += 20

        # 检查常见弱密码
        if password.lower() in self.common_passwords:
            errors.append("这是一个常见的弱密码，请选择更安全的密码")

        # 检查重复字符
        if len(set(password)) < len(password) * 0.6:
            warnings.append("密码包含过多重复字符")
        else:
            score += 10

        # 检查连续字符
        consecutive_count = self._count_consecutive_chars(password)
        if consecutive_count > 3:
            warnings.append("密码包含连续字符序列")
        else:
            score += 10

        # 检查是否包含用户名
        if username and username.lower() in password.lower():
            errors.append("密码不能包含用户名")

        # 检查键盘模式
        if self._has_keyboard_pattern(password):
            warnings.append("密码包含键盘模式")
        else:
            score += 5

        # 计算强度等级
        if score >= 80:
            strength = "强"
        elif score >= 60:
            strength = "中等"
        elif score >= 40:
            strength = "弱"
        else:
            strength = "很弱"

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": score,
            "max_score": max_score,
            "strength": strength,
            "has_uppercase": has_upper,
            "has_lowercase": has_lower,
            "has_numbers": has_digit,
            "has_symbols": has_symbol,
            "length": len(password),
        }

    def _count_consecutive_chars(self, password: str) -> int:
        """计算最长连续字符序列长度"""
        max_consecutive = 0
        current_consecutive = 1

        for i in range(1, len(password)):
            if ord(password[i]) == ord(password[i - 1]) + 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1

        return max_consecutive

    def _has_keyboard_pattern(self, password: str) -> bool:
        """检查是否包含键盘模式"""
        keyboard_patterns = [
            "qwerty",
            "asdf",
            "zxcv",
            "1234",
            "abcd",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm",
        ]

        password_lower = password.lower()
        for pattern in keyboard_patterns:
            if pattern in password_lower or pattern[::-1] in password_lower:
                return True

        return False

    def generate_secure_password(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True,
    ) -> str:
        """
        生成安全密码

        Args:
            length: 密码长度
            include_uppercase: 包含大写字母
            include_lowercase: 包含小写字母
            include_numbers: 包含数字
            include_symbols: 包含特殊字符
            exclude_ambiguous: 排除易混淆字符 (0OIl1)

        Returns:
            str: 生成的安全密码
        """
        characters = ""

        if include_lowercase:
            chars = string.ascii_lowercase
            if exclude_ambiguous:
                chars = chars.replace("l", "").replace("o", "")
            characters += chars

        if include_uppercase:
            chars = string.ascii_uppercase
            if exclude_ambiguous:
                chars = chars.replace("I", "").replace("O", "")
            characters += chars

        if include_numbers:
            chars = string.digits
            if exclude_ambiguous:
                chars = chars.replace("0", "").replace("1", "")
            characters += chars

        if include_symbols:
            chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            characters += chars

        if not characters:
            raise ValueError("至少需要选择一种字符类型")

        # 确保密码包含每种选择的字符类型
        password = []

        if include_lowercase:
            password.append(
                secrets.choice(
                    string.ascii_lowercase.replace("l", "").replace("o", "")
                    if exclude_ambiguous
                    else string.ascii_lowercase
                )
            )

        if include_uppercase:
            password.append(
                secrets.choice(
                    string.ascii_uppercase.replace("I", "").replace("O", "")
                    if exclude_ambiguous
                    else string.ascii_uppercase
                )
            )

        if include_numbers:
            password.append(
                secrets.choice(
                    string.digits.replace("0", "").replace("1", "")
                    if exclude_ambiguous
                    else string.digits
                )
            )

        if include_symbols:
            password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

        # 填充剩余长度
        for _ in range(length - len(password)):
            password.append(secrets.choice(characters))

        # 打乱顺序
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    def check_password_history(
        self, user_id: int, new_password: str, history_limit: int = 5
    ) -> bool:
        """
        检查密码历史，防止重复使用

        Args:
            user_id: 用户ID
            new_password: 新密码
            history_limit: 历史密码保存数量

        Returns:
            bool: 如果密码未在历史中使用过返回True
        """
        if user_id not in self.password_history:
            return True

        history = self.password_history[user_id]

        # 检查新密码是否与历史密码相同
        for old_hash in history:
            if self.verify_password(new_password, old_hash):
                return False

        return True

    def add_password_to_history(
        self, user_id: int, password_hash: str, history_limit: int = 5
    ):
        """
        将密码添加到历史记录

        Args:
            user_id: 用户ID
            password_hash: 密码哈希
            history_limit: 历史密码保存数量
        """
        if user_id not in self.password_history:
            self.password_history[user_id] = []

        history = self.password_history[user_id]
        history.append(password_hash)

        # 保持历史记录数量限制
        if len(history) > history_limit:
            history.pop(0)

    def create_password_reset_token(
        self, user_id: int, expires_in_hours: int = 1
    ) -> str:
        """
        创建密码重置令牌

        Args:
            user_id: 用户ID
            expires_in_hours: 令牌有效时间（小时）

        Returns:
            str: 重置令牌
        """
        # 生成随机令牌
        token = secrets.token_urlsafe(32)

        # 存储令牌信息（生产环境应使用数据库）
        if not hasattr(self, "reset_tokens"):
            self.reset_tokens = {}

        self.reset_tokens[token] = {
            "user_id": user_id,
            "expires_at": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "used": False,
        }

        return token

    def verify_reset_token(self, token: str) -> Optional[int]:
        """
        验证密码重置令牌

        Args:
            token: 重置令牌

        Returns:
            int: 用户ID，令牌无效返回None
        """
        if not hasattr(self, "reset_tokens") or token not in self.reset_tokens:
            return None

        token_info = self.reset_tokens[token]

        # 检查是否已使用
        if token_info["used"]:
            return None

        # 检查是否过期
        if datetime.utcnow() > token_info["expires_at"]:
            del self.reset_tokens[token]
            return None

        return token_info["user_id"]

    def use_reset_token(self, token: str) -> bool:
        """
        使用密码重置令牌

        Args:
            token: 重置令牌

        Returns:
            bool: 使用成功返回True
        """
        if not hasattr(self, "reset_tokens") or token not in self.reset_tokens:
            return False

        self.reset_tokens[token]["used"] = True
        return True

    def cleanup_expired_tokens(self) -> int:
        """
        清理过期的重置令牌

        Returns:
            int: 清理的令牌数量
        """
        if not hasattr(self, "reset_tokens"):
            return 0

        expired_tokens = []
        now = datetime.utcnow()

        for token, info in self.reset_tokens.items():
            if now > info["expires_at"] or info["used"]:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.reset_tokens[token]

        return len(expired_tokens)


# 全局密码管理器实例
password_manager = PasswordManager()


class PasswordPolicy:
    """密码策略管理"""

    def __init__(self):
        self.policies = {
            "basic": {
                "min_length": 8,
                "require_uppercase": False,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": False,
                "description": "基础策略：8位数字字母组合",
            },
            "standard": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True,
                "description": "标准策略：12位大小写字母数字符号组合",
            },
            "strict": {
                "min_length": 16,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True,
                "description": "严格策略：16位大小写字母数字符号组合",
            },
        }

    def get_policy(self, policy_name: str) -> Dict[str, any]:
        """获取密码策略"""
        return self.policies.get(policy_name, self.policies["standard"])

    def apply_policy(self, policy_name: str) -> PasswordManager:
        """应用密码策略并返回配置的密码管理器"""
        policy = self.get_policy(policy_name)
        return PasswordManager(
            min_length=policy["min_length"],
            require_uppercase=policy["require_uppercase"],
            require_lowercase=policy["require_lowercase"],
            require_numbers=policy["require_numbers"],
            require_symbols=policy["require_symbols"],
        )


# 全局密码策略实例
password_policy = PasswordPolicy()
