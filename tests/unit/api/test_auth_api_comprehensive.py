#!/usr/bin/env python3
"""
Comprehensive unit tests for api.auth_api
Target: High coverage for authentication API functionality
"""

import pytest
import jwt
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from api.auth_api import AuthAPI, UserManager, TokenManager, AuthError


class TestAuthAPI:
    """Test AuthAPI class functionality"""

    @pytest.fixture
    def auth_api(self, tmp_path):
        """Create AuthAPI instance for testing"""
        db_path = tmp_path / "test_auth.db"
        return AuthAPI(db_path=str(db_path), secret_key="test_secret_key")

    def test_auth_api_initialization(self, auth_api):
        """Test AuthAPI initialization"""
        assert auth_api.secret_key == "test_secret_key"
        assert auth_api.user_manager is not None
        assert auth_api.token_manager is not None
        assert auth_api.session_timeout == 3600  # Default 1 hour

    def test_user_registration_success(self, auth_api):
        """Test successful user registration"""
        result = auth_api.register_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )

        assert result['success'] is True
        assert result['user_id'] is not None
        assert 'password' not in result  # Password should not be returned

    def test_user_registration_duplicate_username(self, auth_api):
        """Test user registration with duplicate username"""
        # Register first user
        auth_api.register_user("testuser", "password123", "test1@example.com")

        # Try to register with same username
        with pytest.raises(AuthError) as exc_info:
            auth_api.register_user("testuser", "password456", "test2@example.com")

        assert "already exists" in str(exc_info.value)

    def test_user_registration_invalid_email(self, auth_api):
        """Test user registration with invalid email"""
        with pytest.raises(AuthError) as exc_info:
            auth_api.register_user("testuser", "password123", "invalid_email")

        assert "Invalid email" in str(exc_info.value)

    def test_user_authentication_success(self, auth_api):
        """Test successful user authentication"""
        # Register user first
        auth_api.register_user("testuser", "password123", "test@example.com")

        # Authenticate
        result = auth_api.authenticate("testuser", "password123")

        assert result['success'] is True
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['user_id'] is not None

    def test_user_authentication_invalid_credentials(self, auth_api):
        """Test authentication with invalid credentials"""
        # Register user first
        auth_api.register_user("testuser", "password123", "test@example.com")

        # Try with wrong password
        with pytest.raises(AuthError) as exc_info:
            auth_api.authenticate("testuser", "wrongpassword")

        assert "Invalid credentials" in str(exc_info.value)

    def test_user_authentication_nonexistent_user(self, auth_api):
        """Test authentication with nonexistent user"""
        with pytest.raises(AuthError) as exc_info:
            auth_api.authenticate("nonexistent", "password123")

        assert "User not found" in str(exc_info.value)

    def test_token_validation_valid(self, auth_api):
        """Test token validation with valid token"""
        # Register and authenticate user
        auth_api.register_user("testuser", "password123", "test@example.com")
        auth_result = auth_api.authenticate("testuser", "password123")

        # Validate token
        token_data = auth_api.validate_token(auth_result['access_token'])

        assert token_data['username'] == "testuser"
        assert 'user_id' in token_data
        assert 'exp' in token_data

    def test_token_validation_expired(self, auth_api):
        """Test token validation with expired token"""
        # Create expired token
        payload = {
            'username': 'testuser',
            'user_id': 1,
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(payload, auth_api.secret_key, algorithm='HS256')

        with pytest.raises(AuthError) as exc_info:
            auth_api.validate_token(expired_token)

        assert "Token expired" in str(exc_info.value)

    def test_token_validation_invalid(self, auth_api):
        """Test token validation with invalid token"""
        with pytest.raises(AuthError) as exc_info:
            auth_api.validate_token("invalid.token.here")

        assert "Invalid token" in str(exc_info.value)

    def test_token_refresh_success(self, auth_api):
        """Test successful token refresh"""
        # Register and authenticate user
        auth_api.register_user("testuser", "password123", "test@example.com")
        auth_result = auth_api.authenticate("testuser", "password123")

        # Refresh token
        refresh_result = auth_api.refresh_token(auth_result['refresh_token'])

        assert refresh_result['success'] is True
        assert 'access_token' in refresh_result
        assert refresh_result['access_token'] != auth_result['access_token']

    def test_token_refresh_invalid(self, auth_api):
        """Test token refresh with invalid refresh token"""
        with pytest.raises(AuthError) as exc_info:
            auth_api.refresh_token("invalid.refresh.token")

        assert "Invalid refresh token" in str(exc_info.value)

    def test_user_logout(self, auth_api):
        """Test user logout"""
        # Register and authenticate user
        auth_api.register_user("testuser", "password123", "test@example.com")
        auth_result = auth_api.authenticate("testuser", "password123")

        # Logout
        logout_result = auth_api.logout(auth_result['access_token'])

        assert logout_result['success'] is True

        # Token should now be invalid
        with pytest.raises(AuthError):
            auth_api.validate_token(auth_result['access_token'])

    def test_password_change_success(self, auth_api):
        """Test successful password change"""
        # Register user
        auth_api.register_user("testuser", "oldpassword", "test@example.com")

        # Change password
        result = auth_api.change_password("testuser", "oldpassword", "newpassword")

        assert result['success'] is True

        # Old password should not work
        with pytest.raises(AuthError):
            auth_api.authenticate("testuser", "oldpassword")

        # New password should work
        auth_result = auth_api.authenticate("testuser", "newpassword")
        assert auth_result['success'] is True

    def test_password_change_wrong_old_password(self, auth_api):
        """Test password change with wrong old password"""
        # Register user
        auth_api.register_user("testuser", "password123", "test@example.com")

        # Try to change with wrong old password
        with pytest.raises(AuthError) as exc_info:
            auth_api.change_password("testuser", "wrongpassword", "newpassword")

        assert "Current password is incorrect" in str(exc_info.value)

    def test_user_profile_retrieval(self, auth_api):
        """Test user profile retrieval"""
        # Register user
        register_result = auth_api.register_user(
            "testuser", "password123", "test@example.com"
        )
        user_id = register_result['user_id']

        # Get profile
        profile = auth_api.get_user_profile(user_id)

        assert profile['username'] == "testuser"
        assert profile['email'] == "test@example.com"
        assert 'password' not in profile
        assert 'created_at' in profile

    def test_user_profile_update(self, auth_api):
        """Test user profile update"""
        # Register user
        register_result = auth_api.register_user(
            "testuser", "password123", "test@example.com"
        )
        user_id = register_result['user_id']

        # Update profile
        update_data = {
            'email': 'newemail@example.com',
            'full_name': 'Test User',
            'bio': 'This is a test user'
        }
        result = auth_api.update_user_profile(user_id, update_data)

        assert result['success'] is True

        # Verify update
        profile = auth_api.get_user_profile(user_id)
        assert profile['email'] == 'newemail@example.com'
        assert profile['full_name'] == 'Test User'
        assert profile['bio'] == 'This is a test user'

    def test_role_based_access_control(self, auth_api):
        """Test role-based access control"""
        # Register users with different roles
        admin_result = auth_api.register_user(
            "admin", "password123", "admin@example.com", role="admin"
        )
        user_result = auth_api.register_user(
            "user", "password123", "user@example.com", role="user"
        )

        # Check role permissions
        assert auth_api.has_permission(admin_result['user_id'], "admin_action") is True
        assert auth_api.has_permission(user_result['user_id'], "admin_action") is False
        assert auth_api.has_permission(user_result['user_id'], "user_action") is True

    def test_session_management(self, auth_api):
        """Test session management"""
        # Register and authenticate user
        auth_api.register_user("testuser", "password123", "test@example.com")
        auth_result = auth_api.authenticate("testuser", "password123")

        # Check active sessions
        sessions = auth_api.get_active_sessions(auth_result['user_id'])
        assert len(sessions) == 1
        assert sessions[0]['token'] == auth_result['access_token']

        # Create another session
        auth_result2 = auth_api.authenticate("testuser", "password123")
        sessions = auth_api.get_active_sessions(auth_result['user_id'])
        assert len(sessions) == 2

        # Logout from one session
        auth_api.logout(auth_result['access_token'])
        sessions = auth_api.get_active_sessions(auth_result['user_id'])
        assert len(sessions) == 1

    def test_rate_limiting(self, auth_api):
        """Test rate limiting for authentication attempts"""
        auth_api.enable_rate_limiting(max_attempts=3, window_minutes=5)

        # Register user
        auth_api.register_user("testuser", "password123", "test@example.com")

        # Make multiple failed attempts
        for _ in range(3):
            with pytest.raises(AuthError):
                auth_api.authenticate("testuser", "wrongpassword")

        # Next attempt should be rate limited
        with pytest.raises(AuthError) as exc_info:
            auth_api.authenticate("testuser", "wrongpassword")

        assert "Rate limit exceeded" in str(exc_info.value)

    def test_password_strength_validation(self, auth_api):
        """Test password strength validation"""
        auth_api.enable_password_policy(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special=True
        )

        # Weak passwords should fail
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase, numbers, special chars
            "PASSWORD",  # No lowercase, numbers, special chars
            "Password",  # No numbers, special chars
            "Password1",  # No special chars
        ]

        for weak_password in weak_passwords:
            with pytest.raises(AuthError) as exc_info:
                auth_api.register_user("user", weak_password, "test@example.com")
            assert "Password does not meet requirements" in str(exc_info.value)

        # Strong password should succeed
        result = auth_api.register_user(
            "testuser", "StrongPass123!", "test@example.com"
        )
        assert result['success'] is True

    def test_account_lockout(self, auth_api):
        """Test account lockout after multiple failed attempts"""
        auth_api.enable_account_lockout(max_attempts=3, lockout_minutes=10)

        # Register user
        auth_api.register_user("testuser", "password123", "test@example.com")

        # Make multiple failed attempts
        for _ in range(3):
            with pytest.raises(AuthError):
                auth_api.authenticate("testuser", "wrongpassword")

        # Account should be locked
        with pytest.raises(AuthError) as exc_info:
            auth_api.authenticate("testuser", "password123")

        assert "Account locked" in str(exc_info.value)

    def test_two_factor_authentication(self, auth_api):
        """Test two-factor authentication"""
        # Enable 2FA for user
        register_result = auth_api.register_user(
            "testuser", "password123", "test@example.com"
        )
        user_id = register_result['user_id']

        auth_api.enable_2fa(user_id)

        # Authentication should now require 2FA
        auth_result = auth_api.authenticate("testuser", "password123")
        assert auth_result['requires_2fa'] is True
        assert 'temp_token' in auth_result

        # Complete 2FA
        with patch('api.auth_api.verify_totp_code', return_value=True):
            final_result = auth_api.complete_2fa(
                auth_result['temp_token'], "123456"
            )
            assert final_result['success'] is True
            assert 'access_token' in final_result


class TestUserManager:
    """Test UserManager class functionality"""

    @pytest.fixture
    def user_manager(self, tmp_path):
        """Create UserManager instance for testing"""
        db_path = tmp_path / "test_users.db"
        return UserManager(db_path=str(db_path))

    def test_user_creation(self, user_manager):
        """Test user creation"""
        user_id = user_manager.create_user(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com"
        )

        assert user_id is not None
        user = user_manager.get_user_by_id(user_id)
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_user_retrieval_by_username(self, user_manager):
        """Test user retrieval by username"""
        user_id = user_manager.create_user(
            "testuser", "hashed_password", "test@example.com"
        )

        user = user_manager.get_user_by_username("testuser")
        assert user['id'] == user_id
        assert user['username'] == "testuser"

    def test_user_retrieval_by_email(self, user_manager):
        """Test user retrieval by email"""
        user_id = user_manager.create_user(
            "testuser", "hashed_password", "test@example.com"
        )

        user = user_manager.get_user_by_email("test@example.com")
        assert user['id'] == user_id
        assert user['email'] == "test@example.com"

    def test_user_existence_checks(self, user_manager):
        """Test user existence checks"""
        user_manager.create_user(
            "testuser", "hashed_password", "test@example.com"
        )

        assert user_manager.user_exists("testuser") is True
        assert user_manager.email_exists("test@example.com") is True
        assert user_manager.user_exists("nonexistent") is False
        assert user_manager.email_exists("nonexistent@example.com") is False

    def test_password_update(self, user_manager):
        """Test password update"""
        user_id = user_manager.create_user(
            "testuser", "old_hash", "test@example.com"
        )

        result = user_manager.update_password(user_id, "new_hash")
        assert result is True

        user = user_manager.get_user_by_id(user_id)
        assert user['password_hash'] == "new_hash"

    def test_user_profile_update(self, user_manager):
        """Test user profile update"""
        user_id = user_manager.create_user(
            "testuser", "password_hash", "test@example.com"
        )

        update_data = {
            'email': 'newemail@example.com',
            'full_name': 'Test User',
            'last_login': datetime.utcnow()
        }

        result = user_manager.update_user(user_id, update_data)
        assert result is True

        user = user_manager.get_user_by_id(user_id)
        assert user['email'] == 'newemail@example.com'
        assert user['full_name'] == 'Test User'

    def test_user_deletion(self, user_manager):
        """Test user deletion"""
        user_id = user_manager.create_user(
            "testuser", "password_hash", "test@example.com"
        )

        result = user_manager.delete_user(user_id)
        assert result is True

        user = user_manager.get_user_by_id(user_id)
        assert user is None

    def test_user_list_pagination(self, user_manager):
        """Test user list with pagination"""
        # Create multiple users
        for i in range(25):
            user_manager.create_user(
                f"user{i}", "password_hash", f"user{i}@example.com"
            )

        # Test pagination
        page1 = user_manager.list_users(page=1, per_page=10)
        assert len(page1) == 10

        page2 = user_manager.list_users(page=2, per_page=10)
        assert len(page2) == 10

        page3 = user_manager.list_users(page=3, per_page=10)
        assert len(page3) == 5  # Remaining users

    def test_user_search(self, user_manager):
        """Test user search functionality"""
        # Create test users
        user_manager.create_user("john_doe", "hash", "john@example.com")
        user_manager.create_user("jane_doe", "hash", "jane@example.com")
        user_manager.create_user("bob_smith", "hash", "bob@example.com")

        # Search by username
        results = user_manager.search_users("doe")
        assert len(results) == 2

        # Search by email
        results = user_manager.search_users("john@")
        assert len(results) == 1
        assert results[0]['username'] == "john_doe"


class TestTokenManager:
    """Test TokenManager class functionality"""

    @pytest.fixture
    def token_manager(self):
        """Create TokenManager instance for testing"""
        return TokenManager(secret_key="test_secret_key")

    def test_token_generation(self, token_manager):
        """Test JWT token generation"""
        payload = {
            'user_id': 1,
            'username': 'testuser',
            'role': 'user'
        }

        token = token_manager.generate_token(payload, expires_in=3600)
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts

    def test_token_verification(self, token_manager):
        """Test JWT token verification"""
        payload = {
            'user_id': 1,
            'username': 'testuser'
        }

        token = token_manager.generate_token(payload)
        decoded = token_manager.verify_token(token)

        assert decoded['user_id'] == 1
        assert decoded['username'] == 'testuser'
        assert 'exp' in decoded

    def test_token_expiration(self, token_manager):
        """Test token expiration"""
        payload = {'user_id': 1}

        # Create token that expires in 1 second
        token = token_manager.generate_token(payload, expires_in=1)

        # Should be valid immediately
        decoded = token_manager.verify_token(token)
        assert decoded['user_id'] == 1

        # Wait for expiration and test
        import time
        time.sleep(2)

        with pytest.raises(jwt.ExpiredSignatureError):
            token_manager.verify_token(token)

    def test_refresh_token_generation(self, token_manager):
        """Test refresh token generation"""
        refresh_token = token_manager.generate_refresh_token(user_id=1)
        assert isinstance(refresh_token, str)

        # Verify refresh token
        payload = token_manager.verify_refresh_token(refresh_token)
        assert payload['user_id'] == 1
        assert payload['type'] == 'refresh'

    def test_token_blacklisting(self, token_manager):
        """Test token blacklisting"""
        payload = {'user_id': 1}
        token = token_manager.generate_token(payload)

        # Token should be valid
        decoded = token_manager.verify_token(token)
        assert decoded['user_id'] == 1

        # Blacklist token
        token_manager.blacklist_token(token)

        # Token should now be invalid
        with pytest.raises(AuthError):
            token_manager.verify_token(token)

    def test_token_claims_validation(self, token_manager):
        """Test token claims validation"""
        payload = {
            'user_id': 1,
            'username': 'testuser',
            'role': 'admin',
            'permissions': ['read', 'write', 'delete']
        }

        token = token_manager.generate_token(payload)
        decoded = token_manager.verify_token(token)

        assert token_manager.validate_claims(decoded, required_role='admin') is True
        assert token_manager.validate_claims(decoded, required_role='user') is True
        assert token_manager.validate_claims(decoded, required_role='superadmin') is False

        assert token_manager.validate_claims(
            decoded, required_permissions=['read', 'write']
        ) is True
        assert token_manager.validate_claims(
            decoded, required_permissions=['admin_only']
        ) is False


@pytest.mark.asyncio
class TestAuthAPIAsync:
    """Test async functionality of AuthAPI"""

    @pytest.fixture
    async def async_auth_api(self, tmp_path):
        """Create async AuthAPI instance for testing"""
        db_path = tmp_path / "test_auth_async.db"
        api = AuthAPI(db_path=str(db_path), secret_key="test_secret_key")
        await api.initialize_async()
        return api

    async def test_async_user_registration(self, async_auth_api):
        """Test async user registration"""
        result = await async_auth_api.register_user_async(
            username="asyncuser",
            password="password123",
            email="async@example.com"
        )

        assert result['success'] is True
        assert result['user_id'] is not None

    async def test_async_authentication(self, async_auth_api):
        """Test async authentication"""
        # Register user first
        await async_auth_api.register_user_async(
            "asyncuser", "password123", "async@example.com"
        )

        # Authenticate
        result = await async_auth_api.authenticate_async("asyncuser", "password123")

        assert result['success'] is True
        assert 'access_token' in result

    async def test_async_token_validation(self, async_auth_api):
        """Test async token validation"""
        # Register and authenticate
        await async_auth_api.register_user_async(
            "asyncuser", "password123", "async@example.com"
        )
        auth_result = await async_auth_api.authenticate_async(
            "asyncuser", "password123"
        )

        # Validate token
        token_data = await async_auth_api.validate_token_async(
            auth_result['access_token']
        )

        assert token_data['username'] == "asyncuser"

    async def test_concurrent_operations(self, async_auth_api):
        """Test concurrent auth operations"""
        tasks = []

        # Create multiple registration tasks
        for i in range(10):
            task = async_auth_api.register_user_async(
                f"user{i}", "password123", f"user{i}@example.com"
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        assert len(successful_results) == 10


@pytest.mark.integration
class TestAuthAPIIntegration:
    """Integration tests for AuthAPI"""

    def test_complete_auth_workflow(self, tmp_path):
        """Test complete authentication workflow"""
        db_path = tmp_path / "integration_auth.db"
        auth_api = AuthAPI(db_path=str(db_path), secret_key="integration_test_key")

        # 1. User registration
        register_result = auth_api.register_user(
            username="integrationuser",
            password="SecurePass123!",
            email="integration@example.com"
        )
        assert register_result['success'] is True
        user_id = register_result['user_id']

        # 2. User authentication
        auth_result = auth_api.authenticate("integrationuser", "SecurePass123!")
        assert auth_result['success'] is True
        access_token = auth_result['access_token']
        refresh_token = auth_result['refresh_token']

        # 3. Token validation
        token_data = auth_api.validate_token(access_token)
        assert token_data['username'] == "integrationuser"

        # 4. Profile retrieval and update
        profile = auth_api.get_user_profile(user_id)
        assert profile['email'] == "integration@example.com"

        update_result = auth_api.update_user_profile(user_id, {
            'full_name': 'Integration Test User',
            'bio': 'This is an integration test'
        })
        assert update_result['success'] is True

        # 5. Password change
        password_result = auth_api.change_password(
            "integrationuser", "SecurePass123!", "NewSecurePass456!"
        )
        assert password_result['success'] is True

        # 6. Token refresh
        refresh_result = auth_api.refresh_token(refresh_token)
        assert refresh_result['success'] is True

        # 7. Logout
        logout_result = auth_api.logout(refresh_result['access_token'])
        assert logout_result['success'] is True

        # 8. Verify token is now invalid
        with pytest.raises(AuthError):
            auth_api.validate_token(refresh_result['access_token'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])