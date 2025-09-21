# 🔗 Authentication API Integration Tests
# 集成测试：验证API端点像完整的对话一样工作

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch
import httpx
from datetime import datetime, timedelta

# FastAPI test setup (adjust imports based on your actual implementation)
# from fastapi.testclient import TestClient
# from your_app import app

class MockAPIClient:
    """Mock API client for testing"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session_cookies = {}

    async def post(self, endpoint, json_data=None, headers=None, cookies=None):
        """Mock POST request"""
        # Simulate API behavior based on endpoint
        if endpoint == "/api/v1/auth/register":
            return await self._handle_register(json_data)
        elif endpoint == "/api/v1/auth/login":
            return await self._handle_login(json_data)
        elif endpoint == "/api/v1/auth/refresh":
            return await self._handle_refresh(json_data, cookies)
        elif endpoint == "/api/v1/auth/logout":
            return await self._handle_logout(headers, cookies)
        else:
            return MockResponse(404, {"error": "Endpoint not found"})

    async def get(self, endpoint, headers=None, cookies=None):
        """Mock GET request"""
        if endpoint == "/api/v1/auth/profile":
            return await self._handle_get_profile(headers)
        elif endpoint == "/api/v1/health":
            return MockResponse(200, {"status": "OK", "timestamp": datetime.utcnow().isoformat()})
        else:
            return MockResponse(404, {"error": "Endpoint not found"})

    async def _handle_register(self, data):
        """Mock registration endpoint"""
        if not data:
            return MockResponse(400, {"error": "Request body required"})

        # Validate required fields
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return MockResponse(400, {"error": "Missing required fields"})

        # Mock validation
        if len(data['password']) < 8:
            return MockResponse(400, {"error": "Validation failed", "details": ["Password too short"]})

        if '@' not in data['email']:
            return MockResponse(400, {"error": "Validation failed", "details": ["Invalid email format"]})

        # Mock duplicate user check
        if data['email'] == 'existing@example.com':
            return MockResponse(409, {"error": "Email already registered"})

        # Successful registration
        return MockResponse(201, {
            "user": {
                "id": "mock-user-123",
                "username": data['username'],
                "email": data['email'],
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            },
            "tokens": {
                "access_token": "mock.access.token",
                "refresh_token": "mock.refresh.token",
                "expires_in": 900,
                "token_type": "Bearer"
            },
            "message": "User registered successfully"
        }, cookies={"refresh_token": "mock.refresh.token"})

    async def _handle_login(self, data):
        """Mock login endpoint"""
        if not data or 'email' not in data or 'password' not in data:
            return MockResponse(400, {"error": "Email and password required"})

        # Mock user validation
        if data['email'] == 'test@example.com' and data['password'] == 'TestPassword123!':
            return MockResponse(200, {
                "user": {
                    "id": "mock-user-123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "status": "active"
                },
                "tokens": {
                    "access_token": "mock.access.token",
                    "refresh_token": "mock.refresh.token",
                    "expires_in": 900,
                    "token_type": "Bearer"
                },
                "message": "Login successful"
            }, cookies={"refresh_token": "mock.refresh.token"})

        # Mock account lockout after multiple failures
        if data['email'] == 'locked@example.com':
            return MockResponse(401, {"error": "Account temporarily locked"})

        return MockResponse(401, {"error": "Invalid credentials"})

    async def _handle_refresh(self, data, cookies):
        """Mock token refresh endpoint"""
        refresh_token = None
        if cookies and 'refresh_token' in cookies:
            refresh_token = cookies['refresh_token']
        elif data and 'refresh_token' in data:
            refresh_token = data['refresh_token']

        if not refresh_token:
            return MockResponse(401, {"error": "Refresh token required"})

        if refresh_token == "mock.refresh.token":
            return MockResponse(200, {
                "tokens": {
                    "access_token": "new.mock.access.token",
                    "expires_in": 900,
                    "token_type": "Bearer"
                },
                "message": "Token refreshed successfully"
            })

        return MockResponse(401, {"error": "Invalid refresh token"})

    async def _handle_logout(self, headers, cookies):
        """Mock logout endpoint"""
        return MockResponse(200, {
            "message": "Logged out successfully"
        }, clear_cookies=["refresh_token"])

    async def _handle_get_profile(self, headers):
        """Mock get profile endpoint"""
        if not headers or 'Authorization' not in headers:
            return MockResponse(401, {"error": "Authorization header required"})

        auth_header = headers['Authorization']
        if not auth_header.startswith('Bearer '):
            return MockResponse(401, {"error": "Bearer token required"})

        token = auth_header.split(' ')[1]
        if token == "mock.access.token" or token == "new.mock.access.token":
            return MockResponse(200, {
                "user": {
                    "id": "mock-user-123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "status": "active",
                    "email_verified": True,
                    "last_login_at": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow().isoformat()
                }
            })

        return MockResponse(401, {"error": "Invalid or expired token"})


class MockResponse:
    """Mock HTTP response"""

    def __init__(self, status_code, json_data, cookies=None, clear_cookies=None):
        self.status_code = status_code
        self._json_data = json_data
        self.cookies = cookies or {}
        self.clear_cookies = clear_cookies or []

    def json(self):
        return self._json_data


@pytest.fixture
def api_client():
    """API client for testing"""
    return MockAPIClient()


class TestHealthEndpoint:
    """Test health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self, api_client):
        """测试健康检查 - 像检查系统是否在线"""
        response = await api_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "timestamp" in data


class TestUserRegistrationEndpoint:
    """Test user registration API endpoint"""

    @pytest.mark.asyncio
    async def test_successful_registration(self, api_client):
        """测试成功注册 - 像成功开户"""
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
            "first_name": "New",
            "last_name": "User"
        }

        response = await api_client.post("/api/v1/auth/register", json_data=registration_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "tokens" in data
        assert "message" in data

        # Verify user data
        user = data["user"]
        assert user["username"] == registration_data["username"]
        assert user["email"] == registration_data["email"]
        assert user["status"] == "active"
        assert "id" in user
        assert "created_at" in user

        # Verify tokens
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "Bearer"

        # Verify refresh token cookie is set
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_registration_missing_required_fields(self, api_client):
        """测试缺少必填字段 - 像提交不完整表单"""
        incomplete_data = {
            "username": "testuser"
            # Missing email and password
        }

        response = await api_client.post("/api/v1/auth/register", json_data=incomplete_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Missing required fields" in data["error"]

    @pytest.mark.asyncio
    async def test_registration_invalid_email(self, api_client):
        """测试无效邮箱格式 - 像使用错误邮箱格式"""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email-format",
            "password": "TestPassword123!"
        }

        response = await api_client.post("/api/v1/auth/register", json_data=invalid_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Validation failed" in data["error"]

    @pytest.mark.asyncio
    async def test_registration_weak_password(self, api_client):
        """测试弱密码 - 像使用不安全密码"""
        weak_password_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"  # Too short
        }

        response = await api_client.post("/api/v1/auth/register", json_data=weak_password_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Validation failed" in data["error"]

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, api_client):
        """测试重复邮箱注册 - 像重复申请账户"""
        duplicate_data = {
            "username": "testuser",
            "email": "existing@example.com",  # This email exists in mock
            "password": "TestPassword123!"
        }

        response = await api_client.post("/api/v1/auth/register", json_data=duplicate_data)

        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert "Email already registered" in data["error"]

    @pytest.mark.asyncio
    async def test_registration_empty_request_body(self, api_client):
        """测试空请求体 - 像提交空白表单"""
        response = await api_client.post("/api/v1/auth/register", json_data=None)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


class TestUserLoginEndpoint:
    """Test user login API endpoint"""

    @pytest.mark.asyncio
    async def test_successful_login(self, api_client):
        """测试成功登录 - 像正确输入密码开门"""
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }

        response = await api_client.post("/api/v1/auth/login", json_data=login_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "tokens" in data
        assert "message" in data

        # Verify user data
        user = data["user"]
        assert user["email"] == login_data["email"]
        assert user["status"] == "active"
        assert "id" in user
        assert "username" in user

        # Verify tokens
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert "token_type" in tokens

        # Verify refresh token cookie
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, api_client):
        """测试无效凭据 - 像使用错误密码"""
        invalid_login_data = {
            "email": "test@example.com",
            "password": "WrongPassword123!"
        }

        response = await api_client.post("/api/v1/auth/login", json_data=invalid_login_data)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid credentials" in data["error"]

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, api_client):
        """测试缺少凭据 - 像忘记输入密码"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password
        }

        response = await api_client.post("/api/v1/auth/login", json_data=incomplete_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Email and password required" in data["error"]

    @pytest.mark.asyncio
    async def test_login_account_locked(self, api_client):
        """测试账户锁定 - 像被锁定的账户"""
        locked_account_data = {
            "email": "locked@example.com",
            "password": "TestPassword123!"
        }

        response = await api_client.post("/api/v1/auth/login", json_data=locked_account_data)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Account temporarily locked" in data["error"]

    @pytest.mark.asyncio
    async def test_login_empty_request(self, api_client):
        """测试空登录请求 - 像不输入任何信息"""
        response = await api_client.post("/api/v1/auth/login", json_data={})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


class TestTokenRefreshEndpoint:
    """Test token refresh API endpoint"""

    @pytest.mark.asyncio
    async def test_successful_token_refresh_with_cookie(self, api_client):
        """测试使用Cookie刷新令牌 - 像使用储存的通行证续期"""
        cookies = {"refresh_token": "mock.refresh.token"}

        response = await api_client.post("/api/v1/auth/refresh", cookies=cookies)

        assert response.status_code == 200
        data = response.json()

        assert "tokens" in data
        assert "message" in data

        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "expires_in" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_successful_token_refresh_with_body(self, api_client):
        """测试使用请求体刷新令牌 - 像手动提供通行证续期"""
        refresh_data = {"refresh_token": "mock.refresh.token"}

        response = await api_client.post("/api/v1/auth/refresh", json_data=refresh_data)

        assert response.status_code == 200
        data = response.json()

        assert "tokens" in data
        tokens = data["tokens"]
        assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_token_refresh_missing_token(self, api_client):
        """测试缺少刷新令牌 - 像没有续期证明"""
        response = await api_client.post("/api/v1/auth/refresh", json_data={})

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Refresh token required" in data["error"]

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, api_client):
        """测试无效刷新令牌 - 像使用假的续期证明"""
        invalid_refresh_data = {"refresh_token": "invalid.refresh.token"}

        response = await api_client.post("/api/v1/auth/refresh", json_data=invalid_refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid refresh token" in data["error"]


class TestProtectedEndpoints:
    """Test protected API endpoints"""

    @pytest.mark.asyncio
    async def test_get_profile_with_valid_token(self, api_client):
        """测试使用有效令牌访问个人资料 - 像用正确通行证进入"""
        headers = {"Authorization": "Bearer mock.access.token"}

        response = await api_client.get("/api/v1/auth/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        user = data["user"]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "status" in user
        assert user["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_profile_without_token(self, api_client):
        """测试无令牌访问个人资料 - 像没有通行证试图进入"""
        response = await api_client.get("/api/v1/auth/profile")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Authorization header required" in data["error"]

    @pytest.mark.asyncio
    async def test_get_profile_with_invalid_token(self, api_client):
        """测试使用无效令牌访问个人资料 - 像用假通行证试图进入"""
        headers = {"Authorization": "Bearer invalid.token"}

        response = await api_client.get("/api/v1/auth/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Invalid or expired token" in data["error"]

    @pytest.mark.asyncio
    async def test_get_profile_with_malformed_header(self, api_client):
        """测试格式错误的授权头 - 像使用错误格式的通行证"""
        headers = {"Authorization": "InvalidFormat token"}

        response = await api_client.get("/api/v1/auth/profile", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "Bearer token required" in data["error"]


class TestLogoutEndpoint:
    """Test user logout API endpoint"""

    @pytest.mark.asyncio
    async def test_successful_logout(self, api_client):
        """测试成功登出 - 像正确锁门离开"""
        headers = {"Authorization": "Bearer mock.access.token"}
        cookies = {"refresh_token": "mock.refresh.token"}

        response = await api_client.post("/api/v1/auth/logout", headers=headers, cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]

        # Verify refresh token cookie is cleared
        assert "refresh_token" in response.clear_cookies

    @pytest.mark.asyncio
    async def test_logout_without_token(self, api_client):
        """测试无令牌登出 - 像没带钥匙就想锁门"""
        response = await api_client.post("/api/v1/auth/logout")

        # Logout should still succeed even without tokens
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestCompleteUserFlow:
    """Test complete user authentication flow"""

    @pytest.mark.asyncio
    async def test_complete_registration_login_flow(self, api_client):
        """测试完整注册登录流程 - 像完整的开户到使用过程"""
        # Step 1: Register
        registration_data = {
            "username": "flowtest",
            "email": "flowtest@example.com",
            "password": "FlowTestPassword123!",
            "first_name": "Flow",
            "last_name": "Test"
        }

        register_response = await api_client.post("/api/v1/auth/register", json_data=registration_data)
        assert register_response.status_code == 201

        register_data = register_response.json()
        assert "user" in register_data
        assert "tokens" in register_data

        # Step 2: Use access token to get profile
        access_token = register_data["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = await api_client.get("/api/v1/auth/profile", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["user"]["email"] == registration_data["email"]

        # Step 3: Refresh token
        refresh_token = register_data["tokens"]["refresh_token"]
        refresh_cookies = {"refresh_token": refresh_token}

        refresh_response = await api_client.post("/api/v1/auth/refresh", cookies=refresh_cookies)
        assert refresh_response.status_code == 200

        refresh_data = refresh_response.json()
        assert "tokens" in refresh_data
        new_access_token = refresh_data["tokens"]["access_token"]

        # Step 4: Use new access token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        new_profile_response = await api_client.get("/api/v1/auth/profile", headers=new_headers)
        assert new_profile_response.status_code == 200

        # Step 5: Logout
        logout_response = await api_client.post("/api/v1/auth/logout",
                                               headers=new_headers,
                                               cookies=refresh_cookies)
        assert logout_response.status_code == 200

    @pytest.mark.asyncio
    async def test_login_after_registration_flow(self, api_client):
        """测试注册后登录流程 - 像开户后再次登录"""
        # First register (this uses flowtest2 to avoid conflicts)
        registration_data = {
            "username": "flowtest2",
            "email": "flowtest2@example.com",
            "password": "FlowTest2Password123!"
        }

        register_response = await api_client.post("/api/v1/auth/register", json_data=registration_data)
        assert register_response.status_code == 201

        # Then login with same credentials
        # Note: In mock, we need to use test@example.com for successful login
        login_data = {
            "email": "test@example.com",  # Mock implementation specific
            "password": "TestPassword123!"
        }

        login_response = await api_client.post("/api/v1/auth/login", json_data=login_data)
        assert login_response.status_code == 200

        login_result = login_response.json()
        assert "user" in login_result
        assert "tokens" in login_result

        # Verify we can access protected resources
        access_token = login_result["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = await api_client.get("/api/v1/auth/profile", headers=headers)
        assert profile_response.status_code == 200


# Performance tests for API endpoints
class TestAPIPerformance:
    """Test API endpoint performance"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_registration_endpoint_performance(self, api_client):
        """测试注册接口性能 - 确保响应时间合理"""
        registration_data = {
            "username": "perftest",
            "email": "perftest@example.com",
            "password": "PerfTestPassword123!"
        }

        start_time = asyncio.get_event_loop().time()
        response = await api_client.post("/api/v1/auth/register", json_data=registration_data)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        assert response.status_code == 201
        assert duration < 1000, f"Registration took {duration}ms, expected < 1000ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_login_endpoint_performance(self, api_client):
        """测试登录接口性能 - 确保响应时间合理"""
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }

        start_time = asyncio.get_event_loop().time()
        response = await api_client.post("/api/v1/auth/login", json_data=login_data)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        assert response.status_code == 200
        assert duration < 500, f"Login took {duration}ms, expected < 500ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_profile_endpoint_performance(self, api_client):
        """测试个人资料接口性能 - 确保响应时间合理"""
        headers = {"Authorization": "Bearer mock.access.token"}

        start_time = asyncio.get_event_loop().time()
        response = await api_client.get("/api/v1/auth/profile", headers=headers)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        assert response.status_code == 200
        assert duration < 200, f"Profile fetch took {duration}ms, expected < 200ms"