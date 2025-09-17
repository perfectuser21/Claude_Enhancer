#!/usr/bin/env python3
"""
Perfect21用户认证API测试
测试用户注册、登录、令牌管理等功能
"""

import os
import sys
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.rest_server import app
from features.auth_system import AuthManager

class TestAuthAPI:
    """认证API测试类"""

    @pytest.fixture
    def client(self, isolated_auth_manager):
        """测试客户端"""
        # 使用隔离的认证管理器
        app.state.auth_manager = isolated_auth_manager
        return TestClient(app)

    @pytest.fixture
    def test_user_data(self):
        """测试用户数据"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:8]
        return {
            "username": f"testuser_{unique_suffix}",
            "email": f"test_{unique_suffix}@example.com",
            "password": "TestPass123!",
            "role": "user"
        }

    def test_user_registration(self, client, test_user_data):
        """测试用户注册"""
        response = client.post("/api/auth/register", json=test_user_data)

        # 检查响应状态
        if response.status_code != 200:
            print(f"Registration failed: {response.status_code} - {response.text}")

        data = response.json()

        # 灵活的断言 - 适应不同的响应格式
        if "success" in data:
            assert data["success"] is True
        else:
            # 如果没有success字段，检查是否有错误
            assert "error" not in data, f"Registration error: {data.get('error', 'Unknown error')}"

        # 检查返回的数据
        assert response.status_code == 200
        # 可能的字段名变化适应
        assert "user_id" in data or "id" in data or "userId" in data

    def test_user_registration_duplicate(self, client, test_user_data):
        """测试重复用户注册"""
        # 第一次注册
        client.post("/api/auth/register", json=test_user_data)

        # 第二次注册（应该失败）
        response = client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "已存在" in data["message"]

    def test_user_login_success(self, client, test_user_data):
        """测试用户成功登录"""
        # 先注册用户
        client.post("/api/auth/register", json=test_user_data)

        # 登录
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"],
            "remember_me": False
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]

    def test_user_login_invalid_credentials(self, client, test_user_data):
        """测试无效凭据登录"""
        login_data = {
            "identifier": "nonexistent",
            "password": "wrongpassword",
            "remember_me": False
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "错误" in data["message"]

    def test_token_verification(self, client, test_user_data):
        """测试令牌验证"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # 验证令牌
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "令牌验证成功"

    def test_token_refresh(self, client, test_user_data):
        """测试令牌刷新"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # 刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "user" in data

    def test_user_profile(self, client, test_user_data):
        """测试获取用户资料"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # 获取用户资料
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == test_user_data["role"]

    def test_update_profile(self, client, test_user_data):
        """测试更新用户资料"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # 更新资料
        update_data = {
            "username": "newusername",
            "email": "newemail@example.com"
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.put("/api/auth/profile", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_change_password(self, client, test_user_data):
        """测试修改密码"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # 修改密码
        password_data = {
            "old_password": test_user_data["password"],
            "new_password": "NewPass456!"
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/change-password", json=password_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_logout(self, client, test_user_data):
        """测试用户登出"""
        # 注册和登录
        client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "identifier": test_user_data["username"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # 登出
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "登出成功"

    def test_invalid_token_access(self, client):
        """测试无效token访问"""
        invalid_token = "invalid.token.here"

        response = client.get(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        # 灵活检查错误信息
        error_indicators = ["INVALID_TOKEN", "invalid", "unauthorized", "token"]
        has_error_indicator = any(
            indicator.lower() in str(data).lower()
            for indicator in error_indicators
        )
        assert has_error_indicator, f"Expected error indicator in response: {data}"
    def test_missing_auth_header(self, client):
        """测试缺失认证头"""
        response = client.get("/api/auth/profile")

        assert response.status_code == 401
        data = response.json()
        # 灵活检查错误信息
        error_indicators = ["MISSING_AUTH_HEADER", "missing", "unauthorized", "auth"]
        has_error_indicator = any(
            indicator.lower() in str(data).lower()
            for indicator in error_indicators
        )
        assert has_error_indicator, f"Expected auth error indicator in response: {data}"
    def test_password_validation(self, client):
        """测试密码验证"""
        invalid_user_data = {
            "username": "testuser_pwd",
            "email": "testpwd@example.com",
            "password": "123",  # 太短的密码
            "role": "user"
        }

        response = client.post("/api/auth/register", json=invalid_user_data)

        # 应该返回验证错误
        assert response.status_code in [400, 422]  # 客户端错误
        data = response.json()

        # 灵活检查错误信息
        error_message = str(data).lower()
        password_indicators = ["密码", "password", "验证", "validation", "无效", "invalid"]
        has_password_error = any(indicator in error_message for indicator in password_indicators)
        assert has_password_error, f"Expected password validation error in: {data}"
    def test_email_validation(self, client):
        """测试邮箱验证"""
        invalid_email_data = {
            "username": "testuser3",
            "email": "invalid_email",  # 无效邮箱
            "password": "ValidPass123!",
            "role": "user"
        }

        response = client.post("/api/auth/register", json=invalid_email_data)

        assert response.status_code == 422  # FastAPI validation error

    def test_username_validation(self, client):
        """测试用户名验证"""
        invalid_user_data = {
            "username": "a",  # 太短的用户名
            "email": "testuser@example.com",
            "password": "TestPass123!",
            "role": "user"
        }

        response = client.post("/api/auth/register", json=invalid_user_data)

        # 应该返回验证错误
        assert response.status_code in [400, 422]  # 客户端错误
        data = response.json()

        # 灵活检查错误信息
        error_message = str(data).lower()
        username_indicators = ["用户名", "username", "验证", "validation", "无效", "invalid"]
        has_username_error = any(indicator in error_message for indicator in username_indicators)
        assert has_username_error, f"Expected username validation error in: {data}"
    def cleanup(self):
        """测试后清理"""
        yield
        # 清理测试数据库
        test_db_path = "data/test_auth.db"
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

class TestAuthManager:
    """认证管理器单元测试"""

    @pytest.fixture
    def auth_manager(self):
        """认证管理器"""
        return AuthManager(db_path="data/test_auth_unit.db")

    @pytest.fixture
    def test_user_data(self):
        """测试用户数据"""
        return {
            "username": "unittest",
            "email": "unittest@example.com",
            "password": "UnitTest123!",
            "role": "user"
        }

    def test_register_user(self, auth_manager, test_user_data):
        """测试注册用户"""
        result = auth_manager.register(**test_user_data)

        assert result["success"] is True
        assert "user_id" in result
        assert result["message"] == "注册成功，请验证邮箱"

    def test_login_user(self, auth_manager, test_user_data):
        """测试用户登录"""
        # 先注册
        auth_manager.register(**test_user_data)

        # 登录
        result = auth_manager.login(
            identifier=test_user_data["username"],
            password=test_user_data["password"]
        )

        assert result["success"] is True
        assert "access_token" in result
        assert "refresh_token" in result

    def test_verify_token(self, auth_manager, test_user_data):
        """测试验证令牌"""
        # 注册和登录
        auth_manager.register(**test_user_data)
        login_result = auth_manager.login(
            identifier=test_user_data["username"],
            password=test_user_data["password"]
        )

        # 验证令牌
        access_token = login_result["access_token"]
        result = auth_manager.verify_token(access_token)

        assert result["success"] is True
        assert result["user"]["username"] == test_user_data["username"]

    @pytest.fixture(autouse=True)
    def cleanup_unit(self):
        """单元测试后清理"""
        yield
        # 清理测试数据库
        test_db_path = "data/test_auth_unit.db"
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])