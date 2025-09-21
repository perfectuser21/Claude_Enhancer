# 🧪 Authentication Service Unit Tests
# 单元测试：验证认证服务的每个功能像拼图一样完美工作

import pytest
import bcrypt
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

# Import your actual AuthService here
# from auth_system.auth_service import AuthService

class MockAuthService:
    """Mock AuthService for testing (replace with actual import)"""
    def __init__(self, db_pool=None, redis_client=None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.jwt_secret = 'test-secret'
        self.bcrypt_rounds = 4

    async def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=self.bcrypt_rounds)
        ).decode('utf-8')

    async def verify_password(self, password, hash_value):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hash_value.encode('utf-8'))

    def generate_tokens(self, user_id, user_data=None):
        """Generate JWT tokens"""
        now = datetime.utcnow()

        access_payload = {
            'sub': user_id,
            'type': 'access',
            'iat': now.timestamp(),
            'exp': (now + timedelta(minutes=15)).timestamp(),
            'aud': 'perfect21-app',
            'iss': 'perfect21-auth'
        }

        refresh_payload = {
            'sub': user_id,
            'type': 'refresh',
            'iat': now.timestamp(),
            'exp': (now + timedelta(days=7)).timestamp(),
            'aud': 'perfect21-app',
            'iss': 'perfect21-auth'
        }

        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900,  # 15 minutes
            'token_type': 'Bearer'
        }

    def verify_token(self, token, expected_type='access'):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                audience='perfect21-app',
                issuer='perfect21-auth'
            )

            if payload.get('type') != expected_type:
                raise ValueError(f"Expected token type '{expected_type}', got '{payload.get('type')}'")

            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def validate_registration_data(self, data):
        """Validate user registration data"""
        errors = []

        # Username validation
        username = data.get('username', '').strip()
        if not username or len(username) < 3 or len(username) > 50:
            errors.append('Username must be between 3 and 50 characters')

        # Email validation
        import re
        email = data.get('email', '').strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            errors.append('Valid email address is required')

        # Password validation
        password = data.get('password', '')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')

        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')

        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')

        return errors

    async def register_user(self, user_data):
        """Register a new user"""
        # Validate input data
        validation_errors = self.validate_registration_data(user_data)
        if validation_errors:
            raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")

        # Check if user already exists (mock implementation)
        existing_user = await self._check_existing_user(user_data['email'], user_data['username'])
        if existing_user:
            raise ValueError("User with this email or username already exists")

        # Hash password
        password_hash = await self.hash_password(user_data['password'])

        # Create user record (mock implementation)
        user_id = await self._create_user_record(user_data, password_hash)

        # Generate tokens
        tokens = self.generate_tokens(user_id)

        return {
            'user': {
                'id': user_id,
                'username': user_data['username'],
                'email': user_data['email'],
                'status': 'active'
            },
            'tokens': tokens
        }

    async def _check_existing_user(self, email, username):
        """Mock check for existing user"""
        # In real implementation, this would query the database
        return None

    async def _create_user_record(self, user_data, password_hash):
        """Mock user creation"""
        # In real implementation, this would insert into database
        return 'mock-user-id-123'


@pytest.fixture
def auth_service(mock_redis):
    """Create AuthService instance for testing"""
    return MockAuthService(db_pool=MagicMock(), redis_client=mock_redis)


class TestPasswordHandling:
    """Test password hashing and verification"""

    @pytest.mark.asyncio
    async def test_password_hashing_creates_valid_hash(self, auth_service):
        """测试密码哈希 - 像给密码加密码锁"""
        password = "TestPassword123!"

        hashed = await auth_service.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith('$2b$')  # bcrypt identifier
        assert hashed != password  # Should be different from original

    @pytest.mark.asyncio
    async def test_password_verification_success(self, auth_service):
        """测试正确密码验证 - 像用正确钥匙开锁"""
        password = "TestPassword123!"
        hashed = await auth_service.hash_password(password)

        is_valid = await auth_service.verify_password(password, hashed)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_password_verification_failure(self, auth_service):
        """测试错误密码验证 - 像用错误钥匙开锁"""
        correct_password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = await auth_service.hash_password(correct_password)

        is_valid = await auth_service.verify_password(wrong_password, hashed)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_password_hashing_is_deterministic_but_unique(self, auth_service):
        """测试密码哈希的唯一性 - 每次哈希都不同但都能验证"""
        password = "TestPassword123!"

        hash1 = await auth_service.hash_password(password)
        hash2 = await auth_service.hash_password(password)

        # Different hashes due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert await auth_service.verify_password(password, hash1) is True
        assert await auth_service.verify_password(password, hash2) is True


class TestJWTTokenHandling:
    """Test JWT token generation and verification"""

    def test_token_generation_creates_valid_tokens(self, auth_service):
        """测试令牌生成 - 像制作通行证"""
        user_id = "test-user-123"

        result = auth_service.generate_tokens(user_id)

        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'expires_in' in result
        assert 'token_type' in result
        assert result['token_type'] == 'Bearer'
        assert result['expires_in'] == 900  # 15 minutes

    def test_access_token_contains_correct_payload(self, auth_service):
        """测试访问令牌内容 - 像检查通行证信息"""
        user_id = "test-user-123"

        tokens = auth_service.generate_tokens(user_id)
        payload = auth_service.verify_token(tokens['access_token'], 'access')

        assert payload['sub'] == user_id
        assert payload['type'] == 'access'
        assert payload['aud'] == 'perfect21-app'
        assert payload['iss'] == 'perfect21-auth'
        assert 'iat' in payload
        assert 'exp' in payload

    def test_refresh_token_contains_correct_payload(self, auth_service):
        """测试刷新令牌内容 - 像检查续期证明"""
        user_id = "test-user-123"

        tokens = auth_service.generate_tokens(user_id)
        payload = auth_service.verify_token(tokens['refresh_token'], 'refresh')

        assert payload['sub'] == user_id
        assert payload['type'] == 'refresh'
        assert payload['aud'] == 'perfect21-app'
        assert payload['iss'] == 'perfect21-auth'

    def test_token_verification_rejects_wrong_type(self, auth_service):
        """测试令牌类型验证 - 像拒绝错误类型的通行证"""
        user_id = "test-user-123"

        tokens = auth_service.generate_tokens(user_id)

        # Try to verify refresh token as access token
        with pytest.raises(ValueError, match="Expected token type 'access'"):
            auth_service.verify_token(tokens['refresh_token'], 'access')

    def test_token_verification_rejects_invalid_token(self, auth_service):
        """测试无效令牌验证 - 像拒绝假通行证"""
        invalid_tokens = [
            "invalid.jwt.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            None
        ]

        for invalid_token in invalid_tokens:
            if invalid_token is None:
                continue
            with pytest.raises(ValueError, match="Invalid token"):
                auth_service.verify_token(invalid_token)

    def test_token_verification_rejects_expired_token(self, auth_service):
        """测试过期令牌验证 - 像拒绝过期通行证"""
        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        expired_payload = {
            'sub': 'test-user',
            'type': 'access',
            'iat': past_time.timestamp(),
            'exp': past_time.timestamp(),  # Already expired
            'aud': 'perfect21-app',
            'iss': 'perfect21-auth'
        }

        expired_token = jwt.encode(expired_payload, auth_service.jwt_secret, algorithm='HS256')

        with pytest.raises(ValueError, match="Token has expired"):
            auth_service.verify_token(expired_token)


class TestDataValidation:
    """Test input data validation"""

    def test_valid_registration_data_passes_validation(self, auth_service):
        """测试有效注册数据 - 像检查完整正确的申请表"""
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        errors = auth_service.validate_registration_data(valid_data)

        assert len(errors) == 0

    @pytest.mark.parametrize("username,expected_error", [
        ("ab", "Username must be between 3 and 50 characters"),  # Too short
        ("", "Username must be between 3 and 50 characters"),     # Empty
        ("a" * 51, "Username must be between 3 and 50 characters"), # Too long
    ])
    def test_username_validation_edge_cases(self, auth_service, username, expected_error):
        """测试用户名验证边界情况 - 像检查名字格式"""
        data = {
            'username': username,
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }

        errors = auth_service.validate_registration_data(data)

        assert any(expected_error in error for error in errors)

    @pytest.mark.parametrize("email", [
        "invalid-email",
        "@example.com",
        "test@",
        "test.example.com",
        "",
        "test@.com",
        "test@example.",
    ])
    def test_email_validation_rejects_invalid_formats(self, auth_service, email):
        """测试邮箱验证 - 像检查邮箱地址格式"""
        data = {
            'username': 'testuser',
            'email': email,
            'password': 'TestPassword123!'
        }

        errors = auth_service.validate_registration_data(data)

        assert any("Valid email address is required" in error for error in errors)

    @pytest.mark.parametrize("password,expected_errors", [
        ("123", ["Password must be at least 8 characters long"]),
        ("password", ["Password must contain at least one uppercase letter",
                     "Password must contain at least one number",
                     "Password must contain at least one special character"]),
        ("PASSWORD123", ["Password must contain at least one lowercase letter",
                        "Password must contain at least one special character"]),
        ("Password123", ["Password must contain at least one special character"]),
        ("Password!", ["Password must contain at least one number"]),
    ])
    def test_password_strength_validation(self, auth_service, password, expected_errors):
        """测试密码强度验证 - 像检查密码复杂度"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': password
        }

        errors = auth_service.validate_registration_data(data)

        for expected_error in expected_errors:
            assert any(expected_error in error for error in errors)

    def test_validation_accumulates_multiple_errors(self, auth_service):
        """测试多重验证错误 - 像检查多个错误的申请表"""
        invalid_data = {
            'username': 'x',  # Too short
            'email': 'invalid-email',  # Invalid format
            'password': '123'  # Too weak
        }

        errors = auth_service.validate_registration_data(invalid_data)

        assert len(errors) >= 3  # Should have multiple errors
        assert any("Username must be between" in error for error in errors)
        assert any("Valid email address is required" in error for error in errors)
        assert any("Password must be at least" in error for error in errors)


class TestUserRegistration:
    """Test user registration process"""

    @pytest.mark.asyncio
    async def test_successful_user_registration(self, auth_service):
        """测试成功用户注册 - 像成功申请账户"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewUserPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        result = await auth_service.register_user(user_data)

        assert 'user' in result
        assert 'tokens' in result
        assert result['user']['username'] == user_data['username']
        assert result['user']['email'] == user_data['email']
        assert result['user']['status'] == 'active'
        assert 'access_token' in result['tokens']
        assert 'refresh_token' in result['tokens']

    @pytest.mark.asyncio
    async def test_registration_fails_with_invalid_data(self, auth_service):
        """测试无效数据注册失败 - 像拒绝错误申请表"""
        invalid_data = {
            'username': 'x',  # Too short
            'email': 'invalid-email',
            'password': '123'  # Too weak
        }

        with pytest.raises(ValueError, match="Validation failed"):
            await auth_service.register_user(invalid_data)

    @pytest.mark.asyncio
    async def test_registration_fails_with_duplicate_user(self, auth_service):
        """测试重复用户注册失败 - 像拒绝重复申请"""
        user_data = {
            'username': 'existinguser',
            'email': 'existing@example.com',
            'password': 'ExistingPassword123!'
        }

        # Mock existing user check to return a user
        auth_service._check_existing_user = AsyncMock(return_value={'id': 'existing-user'})

        with pytest.raises(ValueError, match="User with this email or username already exists"):
            await auth_service.register_user(user_data)


# Performance tests for critical operations
class TestPerformance:
    """Test performance of critical operations"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_password_hashing_performance(self, auth_service):
        """测试密码哈希性能 - 确保加密速度合理"""
        password = "TestPassword123!"

        start_time = asyncio.get_event_loop().time()
        await auth_service.hash_password(password)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        # Password hashing should complete within 100ms for test environment
        assert duration < 100, f"Password hashing took {duration}ms, expected < 100ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_password_verification_performance(self, auth_service):
        """测试密码验证性能 - 确保验证速度合理"""
        password = "TestPassword123!"
        hashed = await auth_service.hash_password(password)

        start_time = asyncio.get_event_loop().time()
        await auth_service.verify_password(password, hashed)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        # Password verification should complete within 50ms
        assert duration < 50, f"Password verification took {duration}ms, expected < 50ms"

    @pytest.mark.performance
    def test_token_generation_performance(self, auth_service):
        """测试令牌生成性能 - 确保生成速度合理"""
        user_id = "test-user-123"

        start_time = asyncio.get_event_loop().time()
        auth_service.generate_tokens(user_id)
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        # Token generation should complete within 10ms
        assert duration < 10, f"Token generation took {duration}ms, expected < 10ms"

    @pytest.mark.performance
    def test_token_verification_performance(self, auth_service):
        """测试令牌验证性能 - 确保验证速度合理"""
        user_id = "test-user-123"
        tokens = auth_service.generate_tokens(user_id)

        start_time = asyncio.get_event_loop().time()
        auth_service.verify_token(tokens['access_token'])
        end_time = asyncio.get_event_loop().time()

        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        # Token verification should complete within 5ms
        assert duration < 5, f"Token verification took {duration}ms, expected < 5ms"