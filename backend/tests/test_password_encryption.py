#!/usr/bin/env python3
"""
Password Encryption Unit Tests
=============================

测试密码加密和验证功能的核心组件：
- 密码哈希生成和验证
- 密码强度验证
- 盐值生成和管理
- 安全性测试
- 性能测试

作者: Claude Code AI Testing Team
版本: 1.0.0
创建时间: 2025-09-22
"""

import pytest
import bcrypt
import time
import hashlib
import secrets
from unittest.mock import Mock, patch
from typing import Tuple, List


# 基于之前看到的工具函数，创建密码验证器
class PasswordValidator:
    """密码强度验证器"""

    # 常见弱密码模式
    WEAK_PATTERNS = [
        "password",
        "pass123",
        "123456",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "root",
        "user",
        "guest",
    ]

    # 键盘模式
    KEYBOARD_PATTERNS = ["qwerty", "asdf", "zxcv", "1234", "abcd"]

    @classmethod
    def validate_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码强度

        Args:
            password: 待验证的密码

        Returns:
            (是否通过验证, 错误消息列表)
        """
        errors = []

        # 长度检查
        if len(password) < 12:
            errors.append("密码长度至少12位")
        elif len(password) > 128:
            errors.append("密码长度不能超过128位")

        # 字符类型检查
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>[]\\/-_+=~`' for c in password)

        if not has_upper:
            errors.append("密码必须包含大写字母")
        if not has_lower:
            errors.append("密码必须包含小写字母")
        if not has_digit:
            errors.append("密码必须包含数字")
        if not has_special:
            errors.append("密码必须包含特殊字符")

        # 重复字符检查
        if cls._has_repeated_chars(password):
            errors.append("密码不能包含过多重复字符")

        # 顺序字符检查
        if cls._has_sequential_chars(password):
            errors.append("密码不能包含连续的字符序列")

        # 弱密码模式检查
        password_lower = password.lower()
        for pattern in cls.WEAK_PATTERNS:
            if pattern in password_lower:
                errors.append(f"密码不能包含常见弱密码模式: {pattern}")

        # 键盘模式检查
        for pattern in cls.KEYBOARD_PATTERNS:
            if pattern in password_lower:
                errors.append(f"密码不能包含键盘模式: {pattern}")

        return len(errors) == 0, errors

    @staticmethod
    def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
        """检查是否有过多重复字符"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                count += 1
                if count > max_repeat:
                    return True
            else:
                count = 1
        return False

    @staticmethod
    def _has_sequential_chars(password: str, max_sequence: int = 3) -> bool:
        """检查是否有连续字符序列"""
        for i in range(len(password) - max_sequence + 1):
            # 检查递增序列
            is_ascending = True
            is_descending = True

            for j in range(1, max_sequence):
                if ord(password[i + j]) != ord(password[i + j - 1]) + 1:
                    is_ascending = False
                if ord(password[i + j]) != ord(password[i + j - 1]) - 1:
                    is_descending = False

            if is_ascending or is_descending:
                return True

        return False

    @classmethod
    def calculate_entropy(cls, password: str) -> float:
        """
        计算密码熵值

        Args:
            password: 密码

        Returns:
            密码熵值（bits）
        """
        charset_size = 0

        # 统计字符集大小
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in '!@#$%^&*(),.?":{}|<>[]\\/-_+=~`' for c in password):
            charset_size += 32

        # 计算熵值
        import math

        if charset_size > 0:
            entropy = len(password) * math.log2(charset_size)
        else:
            entropy = 0

        return entropy


class PasswordManager:
    """密码管理器 - 处理密码哈希和验证"""

    def __init__(self, rounds: int = 12):
        """初始化密码管理器

        Args:
            rounds: bcrypt轮数（默认12轮）
        """
        self.rounds = rounds
        self.validator = PasswordValidator()

    def hash_password(self, password: str) -> Tuple[str, str]:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            (密码哈希, 盐值)
        """
        # 生成盐值
        salt = bcrypt.gensalt(rounds=self.rounds)

        # 生成哈希
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

        return password_hash.decode("utf-8"), salt.decode("utf-8")

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 要验证的明文密码
            stored_hash: 存储的密码哈希

        Returns:
            密码是否正确
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码强度

        Args:
            password: 待验证的密码

        Returns:
            (是否通过验证, 错误消息列表)
        """
        return self.validator.validate_strength(password)

    def calculate_password_entropy(self, password: str) -> float:
        """
        计算密码熵值

        Args:
            password: 密码

        Returns:
            密码熵值（bits）
        """
        return self.validator.calculate_entropy(password)

    def is_password_compromised(self, password: str) -> bool:
        """
        检查密码是否在已泄露密码列表中（模拟实现）

        Args:
            password: 密码

        Returns:
            是否已被泄露
        """
        # 这里应该集成Have I Been Pwned API或类似服务
        # 为了测试，我们使用一个简单的黑名单
        compromised_passwords = {
            "password123",
            "123456789",
            "qwerty123",
            "admin123",
            "password1",
        }
        return password.lower() in compromised_passwords


class TestPasswordValidator:
    """密码验证器测试套件"""

    @pytest.fixture
    def validator(self):
        """创建密码验证器实例"""
        return PasswordValidator()

    def test_validate_strong_password(self, validator):
        """测试强密码验证"""
        strong_passwords = [
            "MySecureP@ssw0rd2023!",
            "Complex#Password123",
            "StrongP@ss1234567890",
            "UnbreakableP@ssw0rd!",
        ]

        for password in strong_passwords:
            is_valid, errors = validator.validate_strength(password)
            assert (
                is_valid
            ), f"Password {password} should be valid, but got errors: {errors}"
            assert len(errors) == 0

    def test_validate_weak_password_length(self, validator):
        """测试密码长度验证"""
        # 太短的密码
        short_passwords = ["Abc123!", "Short1!", "P@ss1"]

        for password in short_passwords:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any("至少12位" in error for error in errors)

        # 太长的密码
        long_password = "A" * 129 + "b1!"
        is_valid, errors = validator.validate_strength(long_password)
        assert not is_valid
        assert any("不能超过128位" in error for error in errors)

    def test_validate_missing_character_types(self, validator):
        """测试缺少字符类型的密码"""
        test_cases = [
            ("alllowercase123!", "大写字母"),
            ("ALLUPPERCASE123!", "小写字母"),
            ("NoDigitsHere!@#", "数字"),
            ("NoSpecialChars123", "特殊字符"),
        ]

        for password, missing_type in test_cases:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any(missing_type in error for error in errors)

    def test_validate_repeated_characters(self, validator):
        """测试重复字符检查"""
        passwords_with_repeats = [
            "Password1111!",  # 4个连续的1
            "Testtttpass1!",  # 4个连续的t
            "Mypasssssword1!",  # 4个连续的s
        ]

        for password in passwords_with_repeats:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any("重复字符" in error for error in errors)

    def test_validate_sequential_characters(self, validator):
        """测试连续字符检查"""
        passwords_with_sequences = [
            "MyPassword123!",  # 123是连续数字
            "TestPassword!abc",  # abc是连续字母
            "SecurePass!xyz1",  # xyz是连续字母
            "Password!4567",  # 4567是连续数字
        ]

        for password in passwords_with_sequences:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any("连续" in error for error in errors)

    def test_validate_weak_patterns(self, validator):
        """测试弱密码模式检查"""
        passwords_with_weak_patterns = [
            "MyPassword123!",  # 包含"password"
            "Admin123456!",  # 包含"admin"
            "UserQwerty123!",  # 包含"qwerty"
            "RootAccess123!",  # 包含"root"
        ]

        for password in passwords_with_weak_patterns:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any("弱密码模式" in error for error in errors)

    def test_validate_keyboard_patterns(self, validator):
        """测试键盘模式检查"""
        passwords_with_keyboard = [
            "MyQwertyPassword1!",  # 包含qwerty
            "Password1234!",  # 包含1234
            "SecureAsdfPass1!",  # 包含asdf
        ]

        for password in passwords_with_keyboard:
            is_valid, errors = validator.validate_strength(password)
            assert not is_valid
            assert any("键盘模式" in error for error in errors)

    def test_calculate_entropy_various_passwords(self, validator):
        """测试各种密码的熵值计算"""
        test_cases = [
            ("abc", 15.51),  # 只有小写字母
            ("ABC", 15.51),  # 只有大写字母
            ("123", 9.97),  # 只有数字
            ("Abc", 16.90),  # 大小写字母
            ("Abc1", 21.49),  # 大小写字母+数字
            ("Abc1!", 29.27),  # 大小写字母+数字+特殊字符
        ]

        for password, expected_entropy in test_cases:
            actual_entropy = validator.calculate_entropy(password)
            # 允许小的浮点数误差
            assert (
                abs(actual_entropy - expected_entropy) < 0.1
            ), f"Password {password}: expected {expected_entropy}, got {actual_entropy}"

    def test_calculate_entropy_empty_password(self, validator):
        """测试空密码的熵值"""
        entropy = validator.calculate_entropy("")
        assert entropy == 0

    def test_has_repeated_chars_edge_cases(self, validator):
        """测试重复字符检查的边界情况"""
        # 正好3个重复字符（应该通过）
        assert not validator._has_repeated_chars("aaa")
        assert not validator._has_repeated_chars("aaabbb")

        # 4个重复字符（应该失败）
        assert validator._has_repeated_chars("aaaa")
        assert validator._has_repeated_chars("aaaabbbb")

    def test_has_sequential_chars_edge_cases(self, validator):
        """测试连续字符检查的边界情况"""
        # 正好3个连续字符（应该失败）
        assert validator._has_sequential_chars("abc")
        assert validator._has_sequential_chars("123")
        assert validator._has_sequential_chars("xyz")

        # 反向连续
        assert validator._has_sequential_chars("cba")
        assert validator._has_sequential_chars("321")

        # 非连续字符（应该通过）
        assert not validator._has_sequential_chars("ace")
        assert not validator._has_sequential_chars("135")


class TestPasswordManager:
    """密码管理器测试套件"""

    @pytest.fixture
    def password_manager(self):
        """创建密码管理器实例"""
        return PasswordManager(rounds=4)  # 降低轮数以加快测试

    def test_hash_password_success(self, password_manager):
        """测试成功哈希密码"""
        password = "TestPassword123!"

        # 执行
        password_hash, salt = password_manager.hash_password(password)

        # 验证
        assert isinstance(password_hash, str)
        assert isinstance(salt, str)
        assert len(password_hash) > 50  # bcrypt哈希通常很长
        assert len(salt) > 20  # 盐值也有一定长度
        assert password_hash != password  # 哈希不应该等于原密码
        assert salt in password_hash  # bcrypt将盐值包含在哈希中

    def test_hash_password_different_salts(self, password_manager):
        """测试相同密码生成不同盐值"""
        password = "SamePassword123!"

        # 执行多次哈希
        results = []
        for _ in range(5):
            password_hash, salt = password_manager.hash_password(password)
            results.append((password_hash, salt))

        # 验证每次的结果都不同
        hashes = [result[0] for result in results]
        salts = [result[1] for result in results]

        assert len(set(hashes)) == 5  # 所有哈希都应该不同
        assert len(set(salts)) == 5  # 所有盐值都应该不同

    def test_verify_password_success(self, password_manager):
        """测试成功验证密码"""
        password = "CorrectPassword123!"

        # 先哈希密码
        password_hash, _ = password_manager.hash_password(password)

        # 验证正确密码
        assert password_manager.verify_password(password, password_hash) is True

    def test_verify_password_wrong_password(self, password_manager):
        """测试验证错误密码"""
        correct_password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"

        # 先哈希正确密码
        password_hash, _ = password_manager.hash_password(correct_password)

        # 验证错误密码
        assert password_manager.verify_password(wrong_password, password_hash) is False

    def test_verify_password_invalid_hash(self, password_manager):
        """测试验证无效哈希"""
        password = "TestPassword123!"
        invalid_hashes = ["invalid_hash", "", "$2b$12$invalid", None]

        for invalid_hash in invalid_hashes:
            if invalid_hash is None:
                with pytest.raises(AttributeError):
                    password_manager.verify_password(password, invalid_hash)
            else:
                assert password_manager.verify_password(password, invalid_hash) is False

    def test_validate_password_strength_integration(self, password_manager):
        """测试密码强度验证集成"""
        test_cases = [
            ("StrongPassword123!", True),
            ("weak", False),
            ("NoDigitsHere!", False),
            ("nouppercase123!", False),
        ]

        for password, should_be_valid in test_cases:
            is_valid, errors = password_manager.validate_password_strength(password)
            assert is_valid == should_be_valid
            if not should_be_valid:
                assert len(errors) > 0

    def test_calculate_password_entropy_integration(self, password_manager):
        """测试密码熵值计算集成"""
        password = "ComplexP@ssw0rd!"
        entropy = password_manager.calculate_password_entropy(password)

        # 复杂密码应该有高熵值
        assert entropy > 50  # 至少50 bits的熵值

    def test_is_password_compromised(self, password_manager):
        """测试密码泄露检查"""
        # 测试已知的泄露密码
        compromised_passwords = ["password123", "123456789", "qwerty123"]

        for password in compromised_passwords:
            assert password_manager.is_password_compromised(password) is True

        # 测试安全密码
        secure_password = "MyVeryUniqueP@ssw0rd2023!"
        assert password_manager.is_password_compromised(secure_password) is False

    def test_password_hashing_performance(self, password_manager):
        """测试密码哈希性能"""
        password = "PerformanceTestPassword123!"

        # 测试哈希时间
        start_time = time.time()
        password_hash, _ = password_manager.hash_password(password)
        hash_time = time.time() - start_time

        # bcrypt应该相对较快（但不会太快，以防止暴力攻击）
        assert hash_time < 1.0  # 应该在1秒内完成
        assert hash_time > 0.001  # 但不应该太快

        # 测试验证时间
        start_time = time.time()
        is_valid = password_manager.verify_password(password, password_hash)
        verify_time = time.time() - start_time

        assert is_valid is True
        assert verify_time < 1.0  # 验证也应该在1秒内完成

    def test_password_hashing_rounds_effect(self):
        """测试不同哈希轮数的效果"""
        password = "TestRoundsPassword123!"

        # 测试不同轮数
        rounds_to_test = [4, 8, 10]
        times = []

        for rounds in rounds_to_test:
            manager = PasswordManager(rounds=rounds)

            start_time = time.time()
            password_hash, _ = manager.hash_password(password)
            end_time = time.time()

            times.append(end_time - start_time)

            # 验证哈希仍然有效
            assert manager.verify_password(password, password_hash) is True

        # 更高的轮数应该花费更多时间
        assert times[1] > times[0]  # 8轮 > 4轮
        assert times[2] > times[1]  # 10轮 > 8轮

    def test_unicode_password_support(self, password_manager):
        """测试Unicode密码支持"""
        unicode_passwords = [
            "Пароль123!",  # 俄语
            "パスワード123!",  # 日语
            "密码123!",  # 中文
            "Contraseña123!",  # 西班牙语
            "🔐SecurePass123!",  # 包含emoji
        ]

        for password in unicode_passwords:
            # 哈希Unicode密码
            password_hash, salt = password_manager.hash_password(password)

            # 验证Unicode密码
            assert password_manager.verify_password(password, password_hash) is True
            assert (
                password_manager.verify_password(password + "wrong", password_hash)
                is False
            )

    def test_empty_and_edge_case_passwords(self, password_manager):
        """测试空密码和边界情况"""
        edge_cases = [
            "",  # 空字符串
            " ",  # 只有空格
            "\n",  # 换行符
            "\t",  # 制表符
        ]

        for password in edge_cases:
            # 这些应该能哈希但强度验证会失败
            password_hash, salt = password_manager.hash_password(password)
            assert isinstance(password_hash, str)
            assert isinstance(salt, str)

            # 验证哈希
            assert password_manager.verify_password(password, password_hash) is True

            # 强度验证应该失败
            is_valid, errors = password_manager.validate_password_strength(password)
            assert not is_valid
            assert len(errors) > 0


class TestPasswordSecurityFeatures:
    """密码安全特性测试"""

    @pytest.fixture
    def password_manager(self):
        return PasswordManager()

    def test_timing_attack_resistance(self, password_manager):
        """测试时序攻击抵抗性"""
        correct_password = "CorrectPassword123!"
        password_hash, _ = password_manager.hash_password(correct_password)

        # 测试不同长度的错误密码
        wrong_passwords = [
            "a",
            "ab",
            "wrong",
            "WrongPassword123!",
            "VeryLongWrongPasswordThatDoesNotMatch123!",
        ]

        times = []
        for wrong_password in wrong_passwords:
            start_time = time.time()
            result = password_manager.verify_password(wrong_password, password_hash)
            end_time = time.time()

            assert result is False
            times.append(end_time - start_time)

        # 验证时间差异不会太大（简单的时序攻击检测）
        if len(times) > 1:
            max_time = max(times)
            min_time = min(times)
            # bcrypt天然抵抗时序攻击，时间差异应该很小
            assert max_time / min_time < 3  # 允许一些正常的变化

    def test_salt_uniqueness_large_scale(self, password_manager):
        """测试大规模盐值唯一性"""
        password = "TestPassword123!"
        salts = set()

        # 生成100个哈希
        for _ in range(100):
            _, salt = password_manager.hash_password(password)
            salts.add(salt)

        # 所有盐值都应该唯一
        assert len(salts) == 100

    def test_hash_determinism_with_same_salt(self, password_manager):
        """测试相同盐值的哈希确定性"""
        password = "TestPassword123!"

        # 使用固定盐值
        fixed_salt = bcrypt.gensalt(rounds=4)

        # 多次使用相同盐值哈希
        hashes = []
        for _ in range(5):
            password_hash = bcrypt.hashpw(password.encode("utf-8"), fixed_salt)
            hashes.append(password_hash.decode("utf-8"))

        # 所有哈希应该相同
        assert len(set(hashes)) == 1

    def test_rainbow_table_resistance(self, password_manager):
        """测试彩虹表攻击抵抗性"""
        # 相同密码应该产生不同哈希（由于不同盐值）
        password = "CommonPassword123!"
        hashes = []

        for _ in range(10):
            password_hash, _ = password_manager.hash_password(password)
            hashes.append(password_hash)

        # 所有哈希都应该不同
        assert len(set(hashes)) == 10

        # 但都应该能验证原密码
        for password_hash in hashes:
            assert password_manager.verify_password(password, password_hash) is True


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])
