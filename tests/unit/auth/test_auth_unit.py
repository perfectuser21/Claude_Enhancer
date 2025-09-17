#!/usr/bin/env python3
"""
Perfect21认证系统单元测试
测试密码加密、JWT生成验证等核心功能
"""

import pytest
import os
import sys
import secrets
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from features.auth_system.auth_manager import AuthManager
from features.auth_system.token_manager import TokenManager
from features.auth_system.security_service import SecurityService
from features.auth_system.user_service import UserService


class TestPasswordEncryption:
    """密码加密功能测试"""

    @pytest.fixture
    def user_service(self, mock_env):
        """创建用户服务实例"""
        return UserService("data/test_auth.db")

    def test_password_hashing(self, user_service):
        """测试密码哈希功能"""
        password = "TestPassword123!"

        # 测试密码哈希
        hashed = user_service._hash_password(password)

        # 验证哈希结果
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith('$2b$')  # bcrypt格式

    def test_password_verification(self, user_service):
        """测试密码验证功能"""
        password = "TestPassword123!"

        # 创建测试用户
        user_id = user_service.create_user(
            username="testuser",
            email="test@example.com",
            password=password
        )

        # 测试正确密码验证
        assert user_service.verify_password(user_id, password) == True

        # 测试错误密码验证
        assert user_service.verify_password(user_id, "wrongpassword") == False

    def test_password_hash_uniqueness(self, user_service):
        """测试相同密码的不同哈希值"""
        password = "TestPassword123!"

        # 生成多个哈希值
        hash1 = user_service._hash_password(password)
        hash2 = user_service._hash_password(password)

        # 验证哈希值不同（salt确保唯一性）
        assert hash1 != hash2

        # 但都能验证相同密码
        assert user_service._verify_password_hash(password, hash1) == True
        assert user_service._verify_password_hash(password, hash2) == True


class TestJWTTokens:
    """JWT令牌生成和验证测试"""

    @pytest.fixture
    def token_manager(self, mock_env):
        """创建令牌管理器实例"""
        return TokenManager(secret_key="test_secret_key_for_testing_only")

    def test_access_token_generation(self, token_manager):
        """测试访问令牌生成"""
        user_id = "test_user_123"

        # 生成访问令牌
        token = token_manager.generate_access_token(user_id)

        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT格式：header.payload.signature

    def test_access_token_verification(self, token_manager):
        """测试访问令牌验证"""
        user_id = "test_user_123"

        # 生成令牌
        token = token_manager.generate_access_token(user_id)

        # 验证令牌
        payload = token_manager.verify_access_token(token)

        # 检查载荷内容
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['type'] == 'access'
        assert 'exp' in payload
        assert 'iat' in payload
        assert 'jti' in payload

    def test_refresh_token_generation(self, token_manager):
        """测试刷新令牌生成"""
        user_id = "test_user_123"

        # 生成刷新令牌
        token = token_manager.generate_refresh_token(user_id)

        # 验证令牌
        payload = token_manager.verify_refresh_token(token)
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['type'] == 'refresh'

    def test_token_expiration(self, token_manager):
        """测试令牌过期"""
        user_id = "test_user_123"

        # 生成短期令牌（1秒过期）
        short_expires = timedelta(seconds=1)
        token = token_manager.generate_access_token(user_id, expires_delta=short_expires)

        # 立即验证应该成功
        payload = token_manager.verify_access_token(token)
        assert payload is not None

        # 等待令牌过期
        time.sleep(2)

        # 验证过期令牌应该失败
        payload = token_manager.verify_access_token(token)
        assert payload is None

    def test_invalid_token_verification(self, token_manager):
        """测试无效令牌验证"""
        # 测试空令牌
        assert token_manager.verify_access_token("") is None
        assert token_manager.verify_access_token(None) is None

        # 测试格式错误的令牌
        assert token_manager.verify_access_token("invalid.token") is None
        assert token_manager.verify_access_token("completely_invalid") is None

    def test_token_blacklist(self, token_manager):
        """测试令牌黑名单功能"""
        user_id = "test_user_123"

        # 生成令牌
        token = token_manager.generate_access_token(user_id)

        # 验证令牌有效
        assert token_manager.verify_access_token(token) is not None

        # 撤销令牌
        token_manager.revoke_token(token)

        # 验证令牌已被撤销
        assert token_manager.verify_access_token(token) is None

    def test_token_additional_claims(self, token_manager):
        """测试令牌额外声明"""
        user_id = "test_user_123"
        additional_claims = {
            'role': 'admin',
            'permissions': ['read', 'write']
        }

        # 生成带额外声明的令牌
        token = token_manager.generate_access_token(
            user_id,
            additional_claims=additional_claims
        )

        # 验证额外声明
        payload = token_manager.verify_access_token(token)
        assert payload is not None
        assert payload['role'] == 'admin'
        assert payload['permissions'] == ['read', 'write']


class TestSecurityService:
    """安全服务测试"""

    @pytest.fixture
    def security_service(self):
        """创建安全服务实例"""
        return SecurityService()

    def test_password_strength_validation(self, security_service):
        """测试密码强度验证"""
        # 测试强密码
        strong_password = "StrongPass123!"
        result = security_service.validate_password(strong_password)
        assert result['valid'] == True
        assert result['strength'] in ['strong', 'very_strong']

        # 测试弱密码
        weak_password = "123456"
        result = security_service.validate_password(weak_password)
        assert result['valid'] == False
        assert len(result['error']) > 0

    def test_password_requirements(self, security_service):
        """测试密码要求"""
        test_cases = [
            ("short", False, "长度"),
            ("nouppercase123!", False, "大写"),
            ("NOLOWERCASE123!", False, "小写"),
            ("NoDigits!", False, "数字"),
            ("NoSpecialChars123", False, "特殊"),
            ("password", False, "弱密码"),
            ("ValidPass123!", True, None)
        ]

        for password, should_pass, error_keyword in test_cases:
            result = security_service.validate_password(password)
            if should_pass:
                assert result['valid'] == True, f"Password '{password}' should be valid"
            else:
                assert result['valid'] == False, f"Password '{password}' should be invalid"
                if error_keyword:
                    assert error_keyword in result['error'], f"Error should contain '{error_keyword}'"

    def test_email_validation(self, security_service):
        """测试邮箱验证"""
        # 有效邮箱
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]

        for email in valid_emails:
            result = security_service.validate_email(email)
            assert result['valid'] == True, f"Email '{email}' should be valid"

        # 无效邮箱
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "test@",
            "test..test@example.com"
        ]

        for email in invalid_emails:
            result = security_service.validate_email(email)
            assert result['valid'] == False, f"Email '{email}' should be invalid"

    def test_username_validation(self, security_service):
        """测试用户名验证"""
        # 有效用户名
        valid_usernames = [
            "testuser",
            "test_user",
            "test-user",
            "testuser123"
        ]

        for username in valid_usernames:
            result = security_service.validate_username(username)
            assert result['valid'] == True, f"Username '{username}' should be valid"

        # 无效用户名
        invalid_usernames = [
            "ab",  # 太短
            "test user",  # 包含空格
            "_testuser",  # 以下划线开头
            "admin",  # 保留字
            "test@user"  # 包含特殊字符
        ]

        for username in invalid_usernames:
            result = security_service.validate_username(username)
            assert result['valid'] == False, f"Username '{username}' should be invalid"

    def test_login_attempt_limiting(self, security_service):
        """测试登录尝试限制"""
        identifier = "test@example.com"

        # 初始状态应该允许登录
        assert security_service.check_login_attempts(identifier) == True

        # 记录多次失败尝试
        for i in range(5):
            security_service.record_failed_attempt(identifier)

        # 超过限制后应该阻止登录
        assert security_service.check_login_attempts(identifier) == False

        # 清除失败记录后应该恢复
        security_service.clear_failed_attempts(identifier)
        assert security_service.check_login_attempts(identifier) == True

    def test_input_sanitization(self, security_service):
        """测试输入清理"""
        test_cases = [
            ("<script>alert('xss')</script>", "&lt;script&gt;alert('xss')&lt;/script&gt;"),
            ("normal text", "normal text"),
            ('test "quote"', "test &quot;quote&quot;"),
            ("test & ampersand", "test &amp; ampersand")
        ]

        for input_str, expected in test_cases:
            result = security_service.sanitize_input(input_str)
            assert result == expected


class TestUserService:
    """用户服务测试"""

    @pytest.fixture
    def user_service(self, mock_env):
        """创建用户服务实例"""
        return UserService("data/test_auth_user.db")

    def test_user_creation(self, user_service):
        """测试用户创建"""
        username = "testuser"
        email = "test@example.com"
        password = "TestPass123!"

        # 创建用户
        user_id = user_service.create_user(
            username=username,
            email=email,
            password=password
        )

        # 验证用户ID
        assert user_id is not None
        assert len(user_id) > 0

        # 验证用户存在
        assert user_service.user_exists(username, email) == True

    def test_user_retrieval(self, user_service):
        """测试用户检索"""
        username = "testuser2"
        email = "test2@example.com"
        password = "TestPass123!"

        # 创建用户
        user_id = user_service.create_user(
            username=username,
            email=email,
            password=password
        )

        # 通过ID获取用户
        user = user_service.get_user_by_id(user_id)
        assert user is not None
        assert user['username'] == username
        assert user['email'] == email

        # 通过用户名查找用户
        user = user_service.find_user(username)
        assert user is not None
        assert user['id'] == user_id

        # 通过邮箱查找用户
        user = user_service.find_user(email)
        assert user is not None
        assert user['id'] == user_id

    def test_duplicate_user_prevention(self, user_service):
        """测试重复用户防护"""
        username = "duplicateuser"
        email = "duplicate@example.com"
        password = "TestPass123!"

        # 创建第一个用户
        user_id1 = user_service.create_user(
            username=username,
            email=email,
            password=password
        )
        assert user_id1 is not None

        # 尝试创建重复用户名
        with pytest.raises(Exception):
            user_service.create_user(
                username=username,
                email="other@example.com",
                password=password
            )

        # 尝试创建重复邮箱
        with pytest.raises(Exception):
            user_service.create_user(
                username="otherusername",
                email=email,
                password=password
            )

    def test_password_update(self, user_service):
        """测试密码更新"""
        username = "passworduser"
        email = "password@example.com"
        old_password = "OldPass123!"
        new_password = "NewPass123!"

        # 创建用户
        user_id = user_service.create_user(
            username=username,
            email=email,
            password=old_password
        )

        # 验证旧密码
        assert user_service.verify_password(user_id, old_password) == True

        # 更新密码
        user_service.update_password(user_id, new_password)

        # 验证新密码
        assert user_service.verify_password(user_id, new_password) == True

        # 验证旧密码失效
        assert user_service.verify_password(user_id, old_password) == False

    def test_user_status_management(self, user_service):
        """测试用户状态管理"""
        username = "statususer"
        email = "status@example.com"
        password = "TestPass123!"

        # 创建用户
        user_id = user_service.create_user(
            username=username,
            email=email,
            password=password
        )

        # 验证初始状态
        user = user_service.get_user_by_id(user_id)
        assert user['status'] == 'active'

        # 更新用户状态
        user_service.update_user(user_id, status='inactive')

        # 验证状态更新
        user = user_service.get_user_by_id(user_id)
        assert user['status'] == 'inactive'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])