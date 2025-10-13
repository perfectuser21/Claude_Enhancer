"""
🔄 Authentication Integration Tests
===================================

End-to-end testing of complete authentication workflows
Tests how all components work together - like testing the entire security system

Author: Integration Test Engineering Agent
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
import tempfile
import os


# Mock Database Layer
class MockDatabase:
    """Mock database for integration testing"""

    def __init__(self):
        # Create in-memory SQLite database for testing
        self.db_path = ":memory:"
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.setup_tables()

    def setup_tables(self):
        """Create necessary tables for authentication"""
        cursor = self.connection.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_locked BOOLEAN DEFAULT FALSE,
                failed_login_attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                last_activity TIMESTAMP
            )
        """
        )

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                device_info TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        # Password reset tokens table
        cursor.execute(
            """
            CREATE TABLE password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        self.connection.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results as list of dictionaries"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)

        if query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            self.connection.commit()
            return []

    def close(self):
        """Close database connection"""
        self.connection.close()


# Mock API Server
class MockAPIServer:
    """Mock API server for integration testing"""

    def __init__(self):
        self.database = MockDatabase()
        self.jwt_secret = "test_integration_secret"
        self.session_timeout_hours = 24
        self.max_failed_attempts = 5

    async def register_user(
        self, email: str, password: str, device_info: str = None
    ) -> Dict[str, Any]:
        """Register new user endpoint simulation"""
        try:
            pass  # Auto-fixed empty block
            # Validate email format
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email format"}

            # Validate password strength
            if not self._validate_password(password):
                return {
                    "success": False,
                    "error": "Password does not meet requirements",
                }

            # Check if user already exists
            existing_users = self.database.execute_query(
                "SELECT id FROM users WHERE email = ?", (email,)
            )
            if existing_users:
                return {"success": False, "error": "Email already registered"}

            # Hash password (simplified for testing)
            password_hash = self._hash_password(password)

            # Insert new user
            self.database.execute_query(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )

            # Get created user
            users = self.database.execute_query(
                "SELECT id, email, created_at FROM users WHERE email = ?", (email,)
            )
            user = users[0] if users else None

            if user:
                return {
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "created_at": user["created_at"],
                    },
                }
            else:
                return {"success": False, "error": "Failed to create user"}

        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    async def login_user(
        self, email: str, password: str, device_info: str = None, ip_address: str = None
    ) -> Dict[str, Any]:
        """User login endpoint simulation"""
        try:
            pass  # Auto-fixed empty block
            # Get user from database
            users = self.database.execute_query(
                "SELECT * FROM users WHERE email = ?", (email,)
            )

            if not users:
                return {"success": False, "error": "Invalid credentials"}

            user = users[0]

            # Check if account is locked
            if user["is_locked"]:
                return {
                    "success": False,
                    "error": "Account is locked due to too many failed attempts",
                }

            # Check if account is active
            if not user["is_active"]:
                return {"success": False, "error": "Account is inactive"}

            # Verify password
            if not self._verify_password(password, user["password_hash"]):
                pass  # Auto-fixed empty block
                # Increment failed attempts
                new_attempts = user["failed_login_attempts"] + 1
                is_locked = new_attempts >= self.max_failed_attempts

                self.database.execute_query(
                    "UPDATE users SET failed_login_attempts = ?, is_locked = ? WHERE id = ?",
                    (new_attempts, is_locked, user["id"]),
                )

                if is_locked:
                    return {
                        "success": False,
                        "error": "Account locked due to too many failed attempts",
                    }
                else:
                    return {"success": False, "error": "Invalid credentials"}

            # Successful login - reset failed attempts and update last login
            self.database.execute_query(
                "UPDATE users SET failed_login_attempts = 0, last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],),
            )

            # Generate JWT token
            token = self._generate_jwt_token(user["id"], user["email"])

            # Create session record
            token_hash = self._hash_token(token)
            expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)

            self.database.execute_query(
                """INSERT INTO user_sessions (user_id, token_hash, device_info, ip_address, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    user["id"],
                    token_hash,
                    device_info,
                    ip_address,
                    expires_at.isoformat(),
                ),
            )

            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "last_login": user["last_login"],
                },
                "expires_at": expires_at.isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Token validation endpoint simulation"""
        try:
            pass  # Auto-fixed empty block
            # Decode JWT token
            payload = self._decode_jwt_token(token)
            if not payload:
                return {"success": False, "error": "Invalid or expired token"}

            # Check if session exists and is active
            token_hash = self._hash_token(token)
            sessions = self.database.execute_query(
                """SELECT s.*, u.email, u.is_active
                   FROM user_sessions s
                   JOIN users u ON s.user_id = u.id
                   WHERE s.token_hash = ? AND s.is_active = TRUE AND s.expires_at > CURRENT_TIMESTAMP""",
                (token_hash,),
            )

            if not sessions:
                return {"success": False, "error": "Session not found or expired"}

            session = sessions[0]

            # Check if user is still active
            if not session["is_active"]:
                return {"success": False, "error": "User account is inactive"}

            # Update last activity
            self.database.execute_query(
                "UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
                (session["id"],),
            )

            return {
                "success": True,
                "user": {"id": session["user_id"], "email": session["email"]},
                "session": {
                    "created_at": session["created_at"],
                    "expires_at": session["expires_at"],
                },
            }

        except Exception as e:
            return {"success": False, "error": f"Token validation failed: {str(e)}"}

    async def logout_user(self, token: str) -> Dict[str, Any]:
        """User logout endpoint simulation"""
        try:
            token_hash = self._hash_token(token)

            # Deactivate session
            result = self.database.execute_query(
                "UPDATE user_sessions SET is_active = FALSE WHERE token_hash = ?",
                (token_hash,),
            )

            return {"success": True, "message": "Successfully logged out"}

        except Exception as e:
            return {"success": False, "error": f"Logout failed: {str(e)}"}

    async def protected_endpoint(self, token: str) -> Dict[str, Any]:
        """Protected endpoint simulation requiring authentication"""
        validation_result = await self.validate_token(token)

        if not validation_result["success"]:
            return {"success": False, "error": "Authentication required"}

        return {
            "success": True,
            "data": {
                "message": "Access granted to protected resource",
                "user": validation_result["user"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    # Helper methods
    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> bool:
        """Basic password validation"""
        if len(password) < 8 or len(password) > 128:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

    def _hash_password(self, password: str) -> str:
        """Simplified password hashing for testing"""
        import hashlib

        return hashlib.sha256(f"salt_{password}".encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash

    def _generate_jwt_token(self, user_id: int, email: str) -> str:
        """Generate JWT token"""
        import jwt

        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=self.session_timeout_hours),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def _decode_jwt_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        import jwt

        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except:
            return None

    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()


# Test Fixtures
@pytest.fixture
async def api_server():
    """Provide clean API server for each test"""
    server = MockAPIServer()
    yield server
    server.database.close()


@pytest.fixture
async def test_user_data():
    """Provide test user data"""
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "device_info": "Test Device",
        "ip_address": "127.0.0.1",
    }


# ============================================================================
# INTEGRATION TESTS - COMPLETE AUTHENTICATION FLOWS
# ============================================================================


class TestCompleteAuthenticationFlows:
    """Test complete authentication workflows - like testing entire security processes"""

    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, api_server, test_user_data):
        """✅ Test complete user registration from API to database"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register user
        result = await api_server.register_user(email, password)

        assert result["success"] is True
        assert "user" in result
        assert result["user"]["email"] == email
        assert "id" in result["user"]

        # Step 2: Verify user exists in database
        users = api_server.database.execute_query(
            "SELECT * FROM users WHERE email = ?", (email,)
        )
        assert len(users) == 1
        user = users[0]
        assert user["email"] == email
        assert user["is_active"] is True
        assert user["is_locked"] is False
        assert user["failed_login_attempts"] == 0

    @pytest.mark.asyncio
    async def test_complete_login_flow(self, api_server, test_user_data):
        """✅ Test complete login flow with token generation"""
        email = test_user_data["email"]
        password = test_user_data["password"]
        device_info = test_user_data["device_info"]
        ip_address = test_user_data["ip_address"]

        # Step 1: Register user first
        await api_server.register_user(email, password)

        # Step 2: Login user
        login_result = await api_server.login_user(
            email, password, device_info, ip_address
        )

        assert login_result["success"] is True
        assert "token" in login_result
        assert "user" in login_result
        assert login_result["user"]["email"] == email
        assert "expires_at" in login_result

        # Step 3: Verify session created in database
        sessions = api_server.database.execute_query(
            "SELECT * FROM user_sessions WHERE user_id = ? AND is_active = TRUE",
            (login_result["user"]["id"],),
        )
        assert len(sessions) == 1
        session = sessions[0]
        assert session["device_info"] == device_info
        assert session["ip_address"] == ip_address
        assert session["is_active"] is True

    @pytest.mark.asyncio
    async def test_protected_route_access_with_token(self, api_server, test_user_data):
        """✅ Test accessing protected API endpoints with valid token"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register and login to get token
        await api_server.register_user(email, password)
        login_result = await api_server.login_user(email, password)
        token = login_result["token"]

        # Step 2: Access protected endpoint
        protected_result = await api_server.protected_endpoint(token)

        assert protected_result["success"] is True
        assert "data" in protected_result
        assert (
            protected_result["data"]["message"]
            == "Access granted to protected resource"
        )
        assert protected_result["data"]["user"]["email"] == email

    @pytest.mark.asyncio
    async def test_protected_route_access_without_token(self, api_server):
        """❌ Test protected API endpoint rejection without token"""
        # Access protected endpoint without token
        protected_result = await api_server.protected_endpoint("")

        assert protected_result["success"] is False
        assert "Authentication required" in protected_result["error"]

    @pytest.mark.asyncio
    async def test_token_validation_flow(self, api_server, test_user_data):
        """✅ Test token validation mechanism"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register and login to get token
        await api_server.register_user(email, password)
        login_result = await api_server.login_user(email, password)
        token = login_result["token"]

        # Step 2: Validate token
        validation_result = await api_server.validate_token(token)

        assert validation_result["success"] is True
        assert "user" in validation_result
        assert validation_result["user"]["email"] == email
        assert "session" in validation_result

    @pytest.mark.asyncio
    async def test_logout_token_invalidation(self, api_server, test_user_data):
        """✅ Test token invalidation on logout"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register and login to get token
        await api_server.register_user(email, password)
        login_result = await api_server.login_user(email, password)
        token = login_result["token"]

        # Step 2: Verify token is valid
        validation_result = await api_server.validate_token(token)
        assert validation_result["success"] is True

        # Step 3: Logout user
        logout_result = await api_server.logout_user(token)
        assert logout_result["success"] is True

        # Step 4: Try to use token after logout - should fail
        validation_result = await api_server.validate_token(token)
        assert validation_result["success"] is False
        assert "Session not found or expired" in validation_result["error"]

    @pytest.mark.asyncio
    async def test_multiple_device_login(self, api_server, test_user_data):
        """✅ Test user login from multiple devices"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register user
        await api_server.register_user(email, password)

        # Step 2: Login from first device
        login1 = await api_server.login_user(email, password, "Device 1", "192.168.1.1")
        assert login1["success"] is True
        token1 = login1["token"]

        # Step 3: Login from second device
        login2 = await api_server.login_user(email, password, "Device 2", "192.168.1.2")
        assert login2["success"] is True
        token2 = login2["token"]

        # Step 4: Both tokens should be valid
        validation1 = await api_server.validate_token(token1)
        validation2 = await api_server.validate_token(token2)

        assert validation1["success"] is True
        assert validation2["success"] is True

        # Step 5: Verify multiple sessions in database
        user_id = login1["user"]["id"]
        sessions = api_server.database.execute_query(
            "SELECT * FROM user_sessions WHERE user_id = ? AND is_active = TRUE",
            (user_id,),
        )
        assert len(sessions) == 2


# ============================================================================
# INTEGRATION TESTS - ERROR SCENARIOS
# ============================================================================


class TestErrorScenarios:
    """Test error handling in integration scenarios"""

    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(
        self, api_server, test_user_data
    ):
        """🔒 Test account lockout mechanism"""
        email = test_user_data["email"]
        password = test_user_data["password"]
        wrong_password = "WrongPassword123!"

        # Step 1: Register user
        await api_server.register_user(email, password)

        # Step 2: Make multiple failed login attempts
        for i in range(5):  # API server configured for 5 max attempts
            result = await api_server.login_user(email, wrong_password)
            assert result["success"] is False

        # Step 3: Account should now be locked
        # Try with correct password - should still fail
        result = await api_server.login_user(email, password)
        assert result["success"] is False
        assert (
            "Account locked" in result["error"]
            or "Account is locked" in result["error"]
        )

        # Step 4: Verify lockout status in database
        users = api_server.database.execute_query(
            "SELECT is_locked, failed_login_attempts FROM users WHERE email = ?",
            (email,),
        )
        user = users[0]
        assert user["is_locked"] is True
        assert user["failed_login_attempts"] >= 5

    @pytest.mark.asyncio
    async def test_duplicate_registration_prevention(self, api_server, test_user_data):
        """❌ Test prevention of duplicate user registration"""
        email = test_user_data["email"]
        password = test_user_data["password"]

        # Step 1: Register user first time
        result1 = await api_server.register_user(email, password)
        assert result1["success"] is True

        # Step 2: Try to register same email again
        result2 = await api_server.register_user(email, password)
        assert result2["success"] is False
        assert "already registered" in result2["error"]

        # Step 3: Verify only one user exists in database
        users = api_server.database.execute_query(
            "SELECT COUNT(*) as count FROM users WHERE email = ?", (email,)
        )
        assert users[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_invalid_token_handling(self, api_server):
        """❌ Test handling of invalid/malformed tokens"""
        invalid_tokens = [
            "invalid.token.format",
            "expired_token_simulation",
            "",
            None,
            "malformed-jwt-token",
        ]

        for token in invalid_tokens:
            if token is None:
                continue

            # Test token validation
            validation_result = await api_server.validate_token(token)
            assert validation_result["success"] is False

            # Test protected endpoint access
            protected_result = await api_server.protected_endpoint(token)
            assert protected_result["success"] is False


# ============================================================================
# INTEGRATION TESTS - PERFORMANCE SCENARIOS
# ============================================================================


class TestPerformanceIntegration:
    """Test authentication performance in integrated environment"""

    @pytest.mark.asyncio
    async def test_concurrent_user_registrations(self, api_server):
        """⏱️ Test system performance with concurrent registrations"""
        import asyncio

        async def register_user(user_index):
            email = f"user{user_index}@example.com"
            password = f"Password{user_index}123!"
            return await api_server.register_user(email, password)

        # Test with 50 concurrent registrations
        start_time = time.time()

        tasks = [register_user(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Verify all registrations successful
        successful_registrations = sum(
            1
            for result in results
            if isinstance(result, dict) and result.get("success")
        )

        assert successful_registrations == 50
        assert duration_ms < 10000  # Should complete within 10 seconds

        # Verify all users in database
        users = api_server.database.execute_query("SELECT COUNT(*) as count FROM users")
        assert users[0]["count"] == 50

    @pytest.mark.asyncio
    async def test_concurrent_logins(self, api_server):
        """⏱️ Test system performance with concurrent logins"""
        import asyncio

        # Setup: Create 20 test users
        users_data = []
        for i in range(20):
            email = f"loginuser{i}@example.com"
            password = f"LoginPassword{i}123!"
            await api_server.register_user(email, password)
            users_data.append((email, password))

        async def login_user(email, password):
            return await api_server.login_user(email, password)

        # Test concurrent logins
        start_time = time.time()

        tasks = [login_user(email, password) for email, password in users_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Verify all logins successful
        successful_logins = sum(
            1
            for result in results
            if isinstance(result, dict) and result.get("success")
        )

        assert successful_logins == 20
        assert duration_ms < 5000  # Should complete within 5 seconds

        # Verify all sessions created
        sessions = api_server.database.execute_query(
            "SELECT COUNT(*) as count FROM user_sessions WHERE is_active = TRUE"
        )
        assert sessions[0]["count"] == 20


# ============================================================================
# TEST EXECUTION AND REPORTING
# ============================================================================

if __name__ == "__main__":
    # print("🔄 Running Authentication Integration Tests")
    # print("=" * 50)

    # Run all tests with pytest
    pytest.main(
        [
            __file__,
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--asyncio-mode=auto",  # Enable asyncio support
            "--durations=10",  # Show 10 slowest tests
        ]
    )
