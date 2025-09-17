#!/usr/bin/env python3
"""
密码管理器 - bcrypt rounds=12
负责密码哈希、验证、强度检查等安全功能
"""

import re
import secrets
import bcrypt
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class PasswordStrengthResult:
    """密码强度检查结果"""
    is_strong: bool
    score: int  # 0-100分
    issues: List[str]
    suggestions: List[str]

class PasswordManager:
    """密码安全管理器"""

    def __init__(self, bcrypt_rounds: int = 12):
        """
        初始化密码管理器
        Args:
            bcrypt_rounds: bcrypt加密轮数，默认12（推荐值）
        """
        self.bcrypt_rounds = bcrypt_rounds
        self.min_length = 8
        self.max_length = 128

        # 常见弱密码列表（实际应用中应从文件加载更完整的列表）
        self.common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            '1234567890', 'password1', '123123', 'qwerty123',
            'iloveyou', 'princess', 'rockyou', '12345678'
        }

        # 密码强度正则表达式
        self.patterns = {
            'lowercase': re.compile(r'[a-z]'),
            'uppercase': re.compile(r'[A-Z]'),
            'digit': re.compile(r'\d'),
            'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]'),
            'extended_special': re.compile(r'[^\w\s]'),
            'repeating': re.compile(r'(.)\1{2,}'),  # 3个或更多重复字符
            'sequential': re.compile(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', re.IGNORECASE),
            'keyboard_pattern': re.compile(r'(qwer|asdf|zxcv|1234|2345|3456|4567|5678|6789)', re.IGNORECASE)
        }

    def hash_password(self, password: str) -> str:
        """
        使用bcrypt哈希密码
        Args:
            password: 原始密码
        Returns:
            哈希后的密码
        """
        if not isinstance(password, str):
            raise ValueError("密码必须是字符串类型")

        if not password:
            raise ValueError("密码不能为空")

        # 将密码编码为字节
        password_bytes = password.encode('utf-8')

        # 生成盐并哈希
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码
        Args:
            password: 原始密码
            hashed: 哈希后的密码
        Returns:
            验证结果
        """
        if not isinstance(password, str) or not isinstance(hashed, str):
            return False

        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    def check_password_strength(self, password: str, username: str = "", email: str = "") -> PasswordStrengthResult:
        """
        检查密码强度
        Args:
            password: 待检查的密码
            username: 用户名（用于检查密码是否包含用户信息）
            email: 邮箱（用于检查密码是否包含邮箱信息）
        Returns:
            密码强度检查结果
        """
        issues = []
        suggestions = []
        score = 0

        if not password:
            return PasswordStrengthResult(
                is_strong=False,
                score=0,
                issues=["密码不能为空"],
                suggestions=["请输入密码"]
            )

        # 1. 长度检查
        length = len(password)
        if length < self.min_length:
            issues.append(f"密码长度不能少于{self.min_length}位")
            suggestions.append(f"请使用至少{self.min_length}个字符")
        elif length < 12:
            score += 10
            suggestions.append("建议使用12位或更长的密码")
        elif length < 16:
            score += 20
        else:
            score += 30

        if length > self.max_length:
            issues.append(f"密码长度不能超过{self.max_length}位")
            return PasswordStrengthResult(
                is_strong=False,
                score=0,
                issues=issues,
                suggestions=["请缩短密码长度"]
            )

        # 2. 字符类型多样性检查
        char_types = 0
        if self.patterns['lowercase'].search(password):
            char_types += 1
            score += 5
        else:
            issues.append("缺少小写字母")
            suggestions.append("添加小写字母 (a-z)")

        if self.patterns['uppercase'].search(password):
            char_types += 1
            score += 5
        else:
            issues.append("缺少大写字母")
            suggestions.append("添加大写字母 (A-Z)")

        if self.patterns['digit'].search(password):
            char_types += 1
            score += 5
        else:
            issues.append("缺少数字")
            suggestions.append("添加数字 (0-9)")

        if self.patterns['special'].search(password):
            char_types += 1
            score += 10
        else:
            issues.append("缺少特殊字符")
            suggestions.append("添加特殊字符 (!@#$%^&*等)")

        # 字符类型多样性加分
        if char_types >= 3:
            score += 10
        if char_types >= 4:
            score += 15

        # 3. 常见密码检查
        password_lower = password.lower()
        if password_lower in self.common_passwords:
            issues.append("使用了常见的弱密码")
            suggestions.append("避免使用常见密码如'password'、'123456'等")
            score -= 30

        # 4. 个人信息检查
        if username and len(username) >= 3:
            if username.lower() in password_lower:
                issues.append("密码包含用户名")
                suggestions.append("避免在密码中使用用户名")
                score -= 15

        if email and len(email) >= 3:
            email_parts = email.lower().split('@')
            if email_parts[0] in password_lower:
                issues.append("密码包含邮箱信息")
                suggestions.append("避免在密码中使用邮箱信息")
                score -= 15

        # 5. 模式检查
        if self.patterns['repeating'].search(password):
            issues.append("包含过多重复字符")
            suggestions.append("避免连续重复的字符")
            score -= 10

        if self.patterns['sequential'].search(password):
            issues.append("包含连续的字符或数字序列")
            suggestions.append("避免使用abc、123等连续序列")
            score -= 10

        if self.patterns['keyboard_pattern'].search(password):
            issues.append("包含键盘连续按键模式")
            suggestions.append("避免使用qwer、asdf等键盘模式")
            score -= 10

        # 6. 熵值计算加分
        entropy = self._calculate_entropy(password)
        if entropy > 60:
            score += 20
        elif entropy > 40:
            score += 10

        # 确保分数在0-100范围内
        score = max(0, min(100, score))

        # 判断是否为强密码
        is_strong = (
            len(issues) == 0 and
            score >= 70 and
            char_types >= 3 and
            length >= 12
        )

        return PasswordStrengthResult(
            is_strong=is_strong,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def _calculate_entropy(self, password: str) -> float:
        """计算密码熵值"""
        charset_size = 0

        # 计算字符集大小
        if self.patterns['lowercase'].search(password):
            charset_size += 26
        if self.patterns['uppercase'].search(password):
            charset_size += 26
        if self.patterns['digit'].search(password):
            charset_size += 10
        if self.patterns['extended_special'].search(password):
            charset_size += 32  # 估计的特殊字符数

        if charset_size == 0:
            return 0

        # 熵值 = log2(字符集大小) * 密码长度
        import math
        entropy = math.log2(charset_size) * len(password)
        return entropy

    def generate_secure_password(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """
        生成安全的随机密码
        Args:
            length: 密码长度
            include_uppercase: 包含大写字母
            include_lowercase: 包含小写字母
            include_digits: 包含数字
            include_special: 包含特殊字符
            exclude_ambiguous: 排除容易混淆的字符 (0oO1lI等)
        Returns:
            生成的安全密码
        """
        if length < 8:
            length = 8
        if length > 128:
            length = 128

        charset = ""

        if include_lowercase:
            charset += "abcdefghijklmnopqrstuvwxyz"
            if exclude_ambiguous:
                charset = charset.replace('l', '').replace('o', '')

        if include_uppercase:
            charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if exclude_ambiguous:
                charset = charset.replace('I', '').replace('O', '')

        if include_digits:
            charset += "0123456789"
            if exclude_ambiguous:
                charset = charset.replace('0', '').replace('1', '')

        if include_special:
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not charset:
            raise ValueError("至少需要选择一种字符类型")

        # 确保至少包含每种选择的字符类型
        password = []

        if include_lowercase:
            valid_chars = "abcdefghijkmnpqrstuvwxyz" if exclude_ambiguous else "abcdefghijklmnopqrstuvwxyz"
            password.append(secrets.choice(valid_chars))

        if include_uppercase:
            valid_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ" if exclude_ambiguous else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            password.append(secrets.choice(valid_chars))

        if include_digits:
            valid_chars = "23456789" if exclude_ambiguous else "0123456789"
            password.append(secrets.choice(valid_chars))

        if include_special:
            password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

        # 填充剩余长度
        remaining_length = length - len(password)
        for _ in range(remaining_length):
            password.append(secrets.choice(charset))

        # 打乱顺序
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    def is_password_expired(
        self,
        password_changed_at: datetime,
        max_age_days: int = 90
    ) -> bool:
        """
        检查密码是否过期
        Args:
            password_changed_at: 密码修改时间
            max_age_days: 最大有效天数
        Returns:
            是否过期
        """
        if not password_changed_at:
            return True

        expiry_date = password_changed_at + timedelta(days=max_age_days)
        return datetime.utcnow() > expiry_date

    def get_password_requirements(self) -> Dict[str, any]:
        """获取密码要求说明"""
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "required_character_types": [
                "小写字母 (a-z)",
                "大写字母 (A-Z)",
                "数字 (0-9)",
                "特殊字符 (!@#$%^&*等)"
            ],
            "forbidden": [
                "常见弱密码 (如 password, 123456)",
                "包含用户名或邮箱",
                "过多重复字符",
                "键盘连续模式",
                "简单数字或字母序列"
            ],
            "recommendations": [
                "使用12位或更长的密码",
                "包含多种字符类型",
                "避免个人信息",
                "定期更换密码",
                "使用密码管理器"
            ]
        }