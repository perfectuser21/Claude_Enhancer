"""
认证系统完整测试用例
测试JWT认证、密码管理、RBAC权限、安全防护等功能
包含单元测试和集成测试
"""

import unittest
import time
import pytest
import hashlib
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.auth import AuthService, User
from src.auth.jwt import JWTTokenManager, TokenBlacklist
from src.auth.password import PasswordManager, PasswordPolicy
from src.auth.rbac import RBACManager, Permission, Role
from src.auth.security import BruteForceProtection, IPBlocklist, SecurityManager
from src.auth.middleware import require_auth, require_roles, require_permissions


class TestPasswordManager(unittest.TestCase):
    """密码管理器测试"""

    def setUp(self):
        self.password_manager = PasswordManager()

    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123!"
        hashed = self.password_manager.hash_password(password)

        self.assertIsInstance(hashed, str)
        self.assertNotEqual(password, hashed)
        self.assertTrue(len(hashed) > 50)  # bcrypt hash length

    def test_verify_password(self):
        """测试密码验证"""
        password = "TestPassword123!"
        hashed = self.password_manager.hash_password(password)

        # 正确密码
        self.assertTrue(self.password_manager.verify_password(password, hashed))

        # 错误密码
        self.assertFalse(
            self.password_manager.verify_password("wrong_password", hashed)
        )

    def test_password_strength_validation(self):
        """测试密码强度验证"""
        # 强密码
        strong_password = "StrongPass123!@#"
        result = self.password_manager.validate_password_strength(strong_password)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["strength"], "强")

        # 弱密码
        weak_password = "123"
        result = self.password_manager.validate_password_strength(weak_password)
        self.assertFalse(result["is_valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_generate_secure_password(self):
        """测试安全密码生成"""
        password = self.password_manager.generate_secure_password(16)

        self.assertEqual(len(password), 16)

        # 验证生成的密码强度
        result = self.password_manager.validate_password_strength(password)
        self.assertTrue(result["is_valid"])

    def test_password_history(self):
        """测试密码历史"""
        user_id = 1
        password1 = "Password123!"
        password2 = "NewPassword456!"

        # 第一次设置密码
        hash1 = self.password_manager.hash_password(password1)
        self.password_manager.add_password_to_history(user_id, hash1)

        # 检查历史
        self.assertTrue(
            self.password_manager.check_password_history(user_id, password2)
        )
        self.assertFalse(
            self.password_manager.check_password_history(user_id, password1)
        )


class TestJWTTokenManager(unittest.TestCase):
    """JWT令牌管理器测试"""

    def setUp(self):
        self.jwt_manager = JWTTokenManager(
            secret_key="test_secret",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )

    def test_generate_access_token(self):
        """测试访问令牌生成"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["user"],
        }

        token = self.jwt_manager.generate_access_token(user_data)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)

    def test_verify_token(self):
        """测试令牌验证"""
        user_data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["user"],
        }

        token = self.jwt_manager.generate_access_token(user_data)
        payload = self.jwt_manager.verify_token(token, "access")

        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], 1)
        self.assertEqual(payload["username"], "testuser")

    def test_refresh_token(self):
        """测试刷新令牌"""
        user_id = 1
        refresh_token = self.jwt_manager.generate_refresh_token(user_id)

        payload = self.jwt_manager.verify_token(refresh_token, "refresh")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], user_id)

    def test_token_blacklist(self):
        """测试令牌黑名单"""
        blacklist = TokenBlacklist()
        token = "test_token"

        # 添加到黑名单
        self.assertTrue(blacklist.add_token(token, "test"))
        self.assertTrue(blacklist.is_blacklisted(token))

        # 从黑名单移除
        self.assertTrue(blacklist.remove_token(token))
        self.assertFalse(blacklist.is_blacklisted(token))


class TestRBACManager(unittest.TestCase):
    """RBAC管理器测试"""

    def setUp(self):
        self.rbac = RBACManager()

    def test_create_permission(self):
        """测试创建权限"""
        perm = self.rbac.create_permission(
            "test.read", "test", "read", "Test read permission"
        )

        self.assertEqual(perm.name, "test.read")
        self.assertEqual(perm.resource, "test")
        self.assertEqual(perm.action, "read")

    def test_create_role(self):
        """测试创建角色"""
        # 先创建权限
        self.rbac.create_permission("test.read", "test", "read")
        self.rbac.create_permission("test.write", "test", "write")

        # 创建角色
        role = self.rbac.create_role(
            "test_role", "Test role", ["test.read", "test.write"]
        )

        self.assertEqual(role.name, "test_role")
        self.assertEqual(len(role.permissions), 2)

    def test_assign_role_to_user(self):
        """测试为用户分配角色"""
        user_id = 1

        # 分配默认角色
        self.assertTrue(self.rbac.assign_role_to_user(user_id, "user"))

        # 检查用户角色
        user_roles = self.rbac.get_user_roles(user_id)
        role_names = [role.name for role in user_roles]
        self.assertIn("user", role_names)

    def test_check_permission(self):
        """测试权限检查"""
        user_id = 1

        # 分配用户角色
        self.rbac.assign_role_to_user(user_id, "user")

        # 检查权限（用户角色应该有api.access权限）
        self.assertTrue(self.rbac.check_permission(user_id, "api", "access"))

        # 检查没有的权限
        self.assertFalse(self.rbac.check_permission(user_id, "system", "admin"))


class TestAuthService(unittest.TestCase):
    """认证服务测试"""

    def setUp(self):
        self.auth_service = AuthService()

    def test_user_registration(self):
        """测试用户注册"""
        result = self.auth_service.register(
            "testuser", "test@example.com", "TestPassword123!"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["user"]["username"], "testuser")
        self.assertEqual(result["user"]["email"], "test@example.com")

    def test_duplicate_registration(self):
        """测试重复注册"""
        # 第一次注册
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")

        # 重复注册用户名
        result = self.auth_service.register(
            "testuser", "test2@example.com", "TestPassword123!"
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "USERNAME_EXISTS")

        # 重复注册邮箱
        result = self.auth_service.register(
            "testuser2", "test@example.com", "TestPassword123!"
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "EMAIL_EXISTS")

    def test_user_login(self):
        """测试用户登录"""
        # 先注册用户
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")

        # 登录
        result = self.auth_service.login("test@example.com", "TestPassword123!")

        self.assertTrue(result["success"])
        self.assertIn("tokens", result)
        self.assertIn("access_token", result["tokens"])
        self.assertIn("refresh_token", result["tokens"])

    def test_invalid_login(self):
        """测试无效登录"""
        # 不存在的用户
        result = self.auth_service.login("nonexistent@example.com", "password")
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "USER_NOT_FOUND")

        # 注册用户但密码错误
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")
        result = self.auth_service.login("test@example.com", "wrong_password")
        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "INVALID_PASSWORD")

    def test_token_verification(self):
        """测试令牌验证"""
        # 注册并登录用户
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")
        login_result = self.auth_service.login("test@example.com", "TestPassword123!")

        token = login_result["tokens"]["access_token"]
        user_info = self.auth_service.verify_token(token)

        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "testuser")

    def test_logout(self):
        """测试登出"""
        # 注册并登录用户
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")
        login_result = self.auth_service.login("test@example.com", "TestPassword123!")

        access_token = login_result["tokens"]["access_token"]
        refresh_token = login_result["tokens"]["refresh_token"]

        # 登出
        logout_result = self.auth_service.logout(access_token, refresh_token)
        self.assertTrue(logout_result["success"])

        # 验证令牌已失效
        user_info = self.auth_service.verify_token(access_token)
        self.assertIsNone(user_info)

    def test_password_change(self):
        """测试密码修改"""
        # 注册用户
        self.auth_service.register("testuser", "test@example.com", "TestPassword123!")
        user_id = 1

        # 修改密码
        result = self.auth_service.change_password(
            user_id, "TestPassword123!", "NewPassword456!"
        )

        self.assertTrue(result["success"])

        # 验证新密码可以登录
        login_result = self.auth_service.login("test@example.com", "NewPassword456!")
        self.assertTrue(login_result["success"])

        # 验证旧密码不能登录
        login_result = self.auth_service.login("test@example.com", "TestPassword123!")
        self.assertFalse(login_result["success"])


class TestBruteForceProtection(unittest.TestCase):
    """暴力破解防护测试"""

    def setUp(self):
        self.protection = BruteForceProtection(
            max_attempts=3, window_minutes=15, lockout_minutes=30
        )

    def test_failed_attempts_tracking(self):
        """测试失败尝试跟踪"""
        identifier = "test@example.com"
        ip = "192.168.1.1"

        # 记录失败尝试
        for i in range(2):
            result = self.protection.record_failed_attempt(identifier, ip)
            self.assertFalse(result["locked"])

        # 第三次失败应该被锁定
        result = self.protection.record_failed_attempt(identifier, ip)
        self.assertTrue(result["locked"])

    def test_lockout_check(self):
        """测试锁定检查"""
        identifier = "test@example.com"
        ip = "192.168.1.1"

        # 达到锁定条件
        for i in range(3):
            self.protection.record_failed_attempt(identifier, ip)

        # 检查是否被锁定
        self.assertTrue(self.protection.is_locked(identifier))

    def test_successful_attempt_clears_failures(self):
        """测试成功尝试清除失败记录"""
        identifier = "test@example.com"
        ip = "192.168.1.1"

        # 记录失败尝试
        for i in range(2):
            self.protection.record_failed_attempt(identifier, ip)

        # 成功尝试
        self.protection.record_successful_attempt(identifier, ip)

        # 检查是否清除了失败记录
        self.assertFalse(self.protection.is_locked(identifier))
        self.assertEqual(self.protection.get_remaining_attempts(identifier), 3)


class TestIPBlocklist(unittest.TestCase):
    """IP黑名单测试"""

    def setUp(self):
        self.blocklist = IPBlocklist()

    def test_permanent_block(self):
        """测试永久封禁"""
        ip = "192.168.1.100"
        self.blocklist.add_permanent_block(ip, "Test block")

        self.assertTrue(self.blocklist.is_blocked(ip))

        # 移除封禁
        self.assertTrue(self.blocklist.remove_block(ip))
        self.assertFalse(self.blocklist.is_blocked(ip))

    def test_temporary_block(self):
        """测试临时封禁"""
        ip = "192.168.1.101"
        # 设置1秒的临时封禁用于测试
        self.blocklist.temporary_blocks[ip] = datetime.utcnow() + timedelta(seconds=1)

        self.assertTrue(self.blocklist.is_blocked(ip))

        # 等待封禁过期
        import time

        time.sleep(2)

        self.assertFalse(self.blocklist.is_blocked(ip))


class TestSecurityIntegration(unittest.TestCase):
    """安全集成测试"""

    def setUp(self):
        self.security_manager = SecurityManager()
        self.auth_service = AuthService()

    def test_login_with_security_checks(self):
        """测试带安全检查的登录流程"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        password = "TestPassword123!"

        # 注册用户
        self.auth_service.register("testuser", identifier, password)

        # 模拟多次失败登录
        for i in range(4):  # 超过最大尝试次数
            validation = self.security_manager.validate_login_attempt(identifier, ip)
            if validation["allowed"]:
                self.security_manager.handle_failed_login(identifier, ip)

        # 检查是否被锁定
        validation = self.security_manager.validate_login_attempt(identifier, ip)
        self.assertFalse(validation["allowed"])

    def test_successful_login_clears_protection(self):
        """测试成功登录清除防护"""
        identifier = "test@example.com"
        ip = "192.168.1.1"
        password = "TestPassword123!"

        # 注册用户
        self.auth_service.register("testuser", identifier, password)

        # 模拟失败登录
        for i in range(2):
            self.security_manager.handle_failed_login(identifier, ip)

        # 成功登录
        self.security_manager.handle_successful_login(identifier, ip, 1)

        # 检查防护是否被清除
        validation = self.security_manager.validate_login_attempt(identifier, ip)
        self.assertTrue(validation["allowed"])


class TestPasswordPolicy(unittest.TestCase):
    """密码策略测试"""

    def test_password_policies(self):
        """测试不同密码策略"""
        policy = PasswordPolicy()

        # 测试基础策略
        basic_manager = policy.apply_policy("basic")
        self.assertEqual(basic_manager.min_length, 8)
        self.assertFalse(basic_manager.require_uppercase)

        # 测试标准策略
        standard_manager = policy.apply_policy("standard")
        self.assertEqual(standard_manager.min_length, 12)
        self.assertTrue(standard_manager.require_symbols)

        # 测试严格策略
        strict_manager = policy.apply_policy("strict")
        self.assertEqual(strict_manager.min_length, 16)


# 保持向后兼容的测试函数
class TestAuthServiceLegacy:
    """认证服务遗留测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.auth_service = AuthService()

    def test_hash_password_consistency(self):
        """测试密码哈希一致性"""
        password = "test_password_123"
        # 使用新的密码管理器
        hash1 = self.auth_service.password_manager.hash_password(password)
        hash2 = self.auth_service.password_manager.hash_password(password)

        # bcrypt每次生成不同的哈希，但验证应该成功
        assert self.auth_service.password_manager.verify_password(password, hash1)
        assert self.auth_service.password_manager.verify_password(password, hash2)

    def test_register_user_success(self):
        """测试用户注册成功"""
        username = "testuser"
        email = "test@example.com"
        password = "SecurePassword123!"

        result = self.auth_service.register(username, email, password)

        assert result["success"] is True, "注册应该成功"
        assert result["user"]["username"] == username, "注册用户名应该匹配"
        assert result["user"]["email"] == email, "注册邮箱应该匹配"

    def test_login_success(self):
        """测试登录成功"""
        username = "testuser"
        email = "test@example.com"
        password = "SecurePassword123!"

        # 先注册
        self.auth_service.register(username, email, password)

        # 再登录
        result = self.auth_service.login(email, password)

        assert result["success"] is True, "登录应该成功"
        assert "tokens" in result, "应该返回令牌"


# 兼容性测试函数（保持向后兼容）
def test_password_hashing():
    """测试密码加密 - 向后兼容"""
    auth = AuthService()
    password = "test123"
    hash1 = auth.password_manager.hash_password(password)
    hash2 = auth.password_manager.hash_password(password)
    # bcrypt每次生成不同哈希，但都应该能验证成功
    assert auth.password_manager.verify_password(password, hash1)
    assert auth.password_manager.verify_password(password, hash2)
    print("✅ 密码加密测试通过")


def test_user_registration():
    """测试用户注册 - 向后兼容"""
    auth = AuthService()
    result = auth.register("testuser", "test@example.com", "Password123!")
    assert result["success"] == True
    assert result["user"]["username"] == "testuser"
    assert result["user"]["email"] == "test@example.com"
    print("✅ 用户注册测试通过")


def test_user_login():
    """测试用户登录 - 向后兼容"""
    auth = AuthService()
    # 先注册
    auth.register("testuser", "test@example.com", "Password123!")
    # 再登录
    result = auth.login("test@example.com", "Password123!")
    assert result["success"] == True
    assert "tokens" in result
    print("✅ 用户登录测试通过")


if __name__ == "__main__":
    # 运行简单测试
    test_password_hashing()
    test_user_registration()
    test_user_login()
    print("\n✅ 所有基础测试通过!")

    # 运行完整的unittest测试套件
    print("\n运行完整测试套件...")
    unittest.main(verbosity=2, exit=False)

    # 也可以运行pytest获得更详细的测试报告
    print("\n运行pytest测试...")
    pytest.main([__file__, "-v", "--tb=short"])
