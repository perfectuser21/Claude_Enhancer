#!/usr/bin/env python3
"""
Perfect21认证系统集成测试
测试登录流程、令牌刷新等完整业务流程
"""

import pytest
import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from features.auth_system.auth_manager import AuthManager
from api.auth_api import auth_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestAuthManager:
    """认证管理器集成测试"""

    @pytest.fixture
    def auth_manager(self, mock_env):
        """创建认证管理器实例"""
        return AuthManager("data/test_auth_integration.db")

    def test_complete_registration_flow(self, auth_manager):
        """测试完整注册流程"""
        # 注册数据
        username = "testuser"
        email = "test@example.com"
        password = "TestPass123!"
        role = "user"

        # 执行注册
        result = auth_manager.register(
            username=username,
            email=email,
            password=password,
            role=role
        )

        # 验证注册结果
        assert result['success'] == True
        assert 'user_id' in result
        assert 'verification_token' in result
        assert result['message'] == '注册成功，请验证邮箱'

        # 验证用户已创建
        user_profile = auth_manager.get_user_profile(result['user_id'])
        assert user_profile['success'] == True
        assert user_profile['user']['username'] == username
        assert user_profile['user']['email'] == email
        assert user_profile['user']['role'] == role

    def test_complete_login_flow(self, auth_manager):
        """测试完整登录流程"""
        # 先注册用户
        username = "loginuser"
        email = "login@example.com"
        password = "LoginPass123!"

        registration_result = auth_manager.register(
            username=username,
            email=email,
            password=password
        )
        assert registration_result['success'] == True

        # 执行登录
        login_result = auth_manager.login(
            identifier=username,
            password=password,
            remember_me=False
        )

        # 验证登录结果
        assert login_result['success'] == True
        assert 'access_token' in login_result
        assert 'refresh_token' in login_result
        assert 'user' in login_result
        assert 'expires_in' in login_result
        assert login_result['user']['username'] == username
        assert login_result['user']['email'] == email

        # 验证令牌有效性
        access_token = login_result['access_token']
        verify_result = auth_manager.verify_token(access_token)
        assert verify_result['success'] == True
        assert verify_result['user']['username'] == username

    def test_login_with_email(self, auth_manager):
        """测试使用邮箱登录"""
        # 注册用户
        username = "emailuser"
        email = "emaillogin@example.com"
        password = "EmailPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        # 使用邮箱登录
        login_result = auth_manager.login(
            identifier=email,
            password=password
        )

        assert login_result['success'] == True
        assert login_result['user']['email'] == email

    def test_failed_login_attempts(self, auth_manager):
        """测试登录失败流程"""
        # 注册用户
        username = "failuser"
        email = "fail@example.com"
        password = "FailPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        # 测试错误密码
        wrong_password_result = auth_manager.login(
            identifier=username,
            password="wrongpassword"
        )
        assert wrong_password_result['success'] == False
        assert wrong_password_result['error'] == 'INVALID_CREDENTIALS'

        # 测试不存在的用户
        nonexistent_result = auth_manager.login(
            identifier="nonexistent",
            password=password
        )
        assert nonexistent_result['success'] == False
        assert nonexistent_result['error'] == 'INVALID_CREDENTIALS'

    def test_remember_me_functionality(self, auth_manager):
        """测试记住我功能"""
        # 注册用户
        username = "rememberuser"
        email = "remember@example.com"
        password = "RememberPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        # 使用记住我登录
        login_result = auth_manager.login(
            identifier=username,
            password=password,
            remember_me=True
        )

        assert login_result['success'] == True
        # 记住我应该有更长的过期时间
        assert login_result['expires_in'] > 86400  # 大于1天

    def test_token_refresh_flow(self, auth_manager):
        """测试令牌刷新流程"""
        # 注册并登录用户
        username = "refreshuser"
        email = "refresh@example.com"
        password = "RefreshPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        login_result = auth_manager.login(
            identifier=username,
            password=password
        )

        # 使用刷新令牌获取新的访问令牌
        refresh_token = login_result['refresh_token']
        refresh_result = auth_manager.refresh_token(refresh_token)

        assert refresh_result['success'] == True
        assert 'access_token' in refresh_result
        assert 'user' in refresh_result
        assert refresh_result['user']['username'] == username

        # 验证新的访问令牌
        new_access_token = refresh_result['access_token']
        verify_result = auth_manager.verify_token(new_access_token)
        assert verify_result['success'] == True

    def test_logout_flow(self, auth_manager):
        """测试登出流程"""
        # 注册并登录用户
        username = "logoutuser"
        email = "logout@example.com"
        password = "LogoutPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        login_result = auth_manager.login(
            identifier=username,
            password=password
        )

        access_token = login_result['access_token']

        # 验证令牌有效
        verify_result = auth_manager.verify_token(access_token)
        assert verify_result['success'] == True

        # 执行登出
        logout_result = auth_manager.logout(access_token)
        assert logout_result['success'] == True

        # 验证令牌已失效
        verify_result = auth_manager.verify_token(access_token)
        assert verify_result['success'] == False

    def test_password_change_flow(self, auth_manager):
        """测试密码修改流程"""
        # 注册用户
        username = "changeuser"
        email = "change@example.com"
        old_password = "OldPass123!"
        new_password = "NewPass123!"

        registration_result = auth_manager.register(
            username=username,
            email=email,
            password=old_password
        )
        user_id = registration_result['user_id']

        # 修改密码
        change_result = auth_manager.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password
        )
        assert change_result['success'] == True

        # 验证新密码可以登录
        login_result = auth_manager.login(
            identifier=username,
            password=new_password
        )
        assert login_result['success'] == True

        # 验证旧密码无法登录
        old_login_result = auth_manager.login(
            identifier=username,
            password=old_password
        )
        assert old_login_result['success'] == False

    def test_profile_management(self, auth_manager):
        """测试用户资料管理"""
        # 注册用户
        username = "profileuser"
        email = "profile@example.com"
        password = "ProfilePass123!"

        registration_result = auth_manager.register(
            username=username,
            email=email,
            password=password
        )
        user_id = registration_result['user_id']

        # 获取用户资料
        profile_result = auth_manager.get_user_profile(user_id)
        assert profile_result['success'] == True
        assert profile_result['user']['username'] == username

        # 更新用户资料
        new_username = "newprofileuser"
        new_email = "newprofile@example.com"

        update_result = auth_manager.update_user_profile(
            user_id=user_id,
            username=new_username,
            email=new_email
        )
        assert update_result['success'] == True

        # 验证更新生效
        updated_profile = auth_manager.get_user_profile(user_id)
        assert updated_profile['user']['username'] == new_username
        assert updated_profile['user']['email'] == new_email


class TestAuthAPI:
    """认证API集成测试"""

    @pytest.fixture
    def app(self, mock_env):
        """创建测试应用"""
        app = FastAPI()
        app.include_router(auth_router)
        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    def test_api_registration(self, client):
        """测试API注册端点"""
        registration_data = {
            "username": "apiuser",
            "email": "api@example.com",
            "password": "ApiPass123!",
            "role": "user"
        }

        response = client.post("/api/auth/register", json=registration_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'user_id' in data
        assert 'verification_token' in data

    def test_api_login(self, client):
        """测试API登录端点"""
        # 先注册用户
        registration_data = {
            "username": "apiloginuser",
            "email": "apilogin@example.com",
            "password": "ApiLoginPass123!"
        }
        client.post("/api/auth/register", json=registration_data)

        # 执行登录
        login_data = {
            "identifier": "apiloginuser",
            "password": "ApiLoginPass123!",
            "remember_me": False
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data

    def test_api_token_verification(self, client):
        """测试API令牌验证端点"""
        # 注册并登录获取令牌
        registration_data = {
            "username": "apiverifyuser",
            "email": "apiverify@example.com",
            "password": "ApiVerifyPass123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_data = {
            "identifier": "apiverifyuser",
            "password": "ApiVerifyPass123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()['access_token']

        # 验证令牌
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True

    def test_api_profile_access(self, client):
        """测试API用户资料访问"""
        # 注册并登录获取令牌
        registration_data = {
            "username": "apiprofileuser",
            "email": "apiprofile@example.com",
            "password": "ApiProfilePass123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_data = {
            "identifier": "apiprofileuser",
            "password": "ApiProfilePass123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()['access_token']

        # 获取用户资料
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data['username'] == "apiprofileuser"
        assert data['email'] == "apiprofile@example.com"

    def test_api_token_refresh(self, client):
        """测试API令牌刷新端点"""
        # 注册并登录获取令牌
        registration_data = {
            "username": "apirefreshuser",
            "email": "apirefresh@example.com",
            "password": "ApiRefreshPass123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_data = {
            "identifier": "apirefreshuser",
            "password": "ApiRefreshPass123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.json()['refresh_token']

        # 刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'access_token' in data

    def test_api_logout(self, client):
        """测试API登出端点"""
        # 注册并登录获取令牌
        registration_data = {
            "username": "apilogoutuser",
            "email": "apilogout@example.com",
            "password": "ApiLogoutPass123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_data = {
            "identifier": "apilogoutuser",
            "password": "ApiLogoutPass123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()['access_token']

        # 执行登出
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True

        # 验证令牌已失效
        response = client.get("/api/auth/verify", headers=headers)
        assert response.status_code == 401

    def test_api_authentication_required(self, client):
        """测试API认证要求"""
        # 尝试无认证访问受保护端点
        response = client.get("/api/auth/profile")
        assert response.status_code == 401

        response = client.post("/api/auth/logout")
        assert response.status_code == 401

        response = client.get("/api/auth/verify")
        assert response.status_code == 401

    def test_api_invalid_credentials(self, client):
        """测试API无效凭据处理"""
        # 尝试使用不存在的用户登录
        login_data = {
            "identifier": "nonexistent",
            "password": "password"
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == False
        assert data['message'] == '用户名或密码错误'

    def test_api_validation_errors(self, client):
        """测试API输入验证错误"""
        # 测试无效的注册数据
        invalid_registration = {
            "username": "ab",  # 太短
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 太短
        }

        response = client.post("/api/auth/register", json=invalid_registration)
        assert response.status_code == 422  # 验证错误


if __name__ == "__main__":
    pytest.main([__file__, "-v"])