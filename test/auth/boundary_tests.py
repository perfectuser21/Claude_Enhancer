"""
🎯 Authentication Boundary Tests
================================

Edge case and boundary condition testing for authentication system
Tests what happens at the absolute limits - like testing a bridge's weight capacity

Author: Boundary Testing Agent
"""

import pytest
import asyncio
import time
import string
import random
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import secrets
import gc
import sys

# Boundary Test Configuration
class BoundaryConfig:
    """Configuration for boundary testing"""

    # Input Length Limits
    EMAIL_MIN_LENGTH = 5          # minimum@a.b
    EMAIL_MAX_LENGTH = 254        # RFC 5321 limit
    PASSWORD_MIN_LENGTH = 8       # Security minimum
    PASSWORD_MAX_LENGTH = 128     # Practical maximum

    # System Resource Limits
    MAX_CONCURRENT_SESSIONS = 10000    # Maximum sessions
    MAX_MEMORY_USAGE_MB = 1024         # 1GB memory limit
    MAX_CPU_USAGE_PERCENT = 90         # 90% CPU limit

    # Time-based Limits
    TOKEN_MIN_LIFETIME_SECONDS = 60    # 1 minute minimum
    TOKEN_MAX_LIFETIME_HOURS = 168     # 1 week maximum
    SESSION_TIMEOUT_MINUTES = 30       # Session timeout

    # Database Connection Limits
    MAX_DB_CONNECTIONS = 100
    CONNECTION_TIMEOUT_SECONDS = 30

class BoundaryTestService:
    """Enhanced service for boundary testing"""

    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.connections = []
        self.memory_usage = []
        self.lock = threading.Lock()
        self.jwt_secret = "boundary_test_secret"

    def monitor_memory_usage(self):
        """Monitor memory usage during tests"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        return memory_mb

    def simulate_db_connection(self) -> bool:
        """Simulate database connection with limits"""
        with self.lock:
            if len(self.connections) >= BoundaryConfig.MAX_DB_CONNECTIONS:
                return False

            connection_id = f"conn_{len(self.connections)}_{time.time()}"
            self.connections.append({
                "id": connection_id,
                "created_at": datetime.utcnow(),
                "active": True
            })
            return True

    def release_db_connection(self, connection_id: str):
        """Release database connection"""
        with self.lock:
            self.connections = [conn for conn in self.connections
                              if conn["id"] != connection_id]

    async def register_user_with_limits(self, email: str, password: str) -> Dict[str, Any]:
        """Register user with boundary checking"""
        try:
            # Check memory usage
            current_memory = self.monitor_memory_usage()
            if current_memory > BoundaryConfig.MAX_MEMORY_USAGE_MB:
                return {"success": False, "error": "System memory limit exceeded"}

            # Simulate database connection
            if not self.simulate_db_connection():
                return {"success": False, "error": "Database connection limit exceeded"}

            # Input length validation
            if len(email) < BoundaryConfig.EMAIL_MIN_LENGTH:
                return {"success": False, "error": "Email too short"}
            if len(email) > BoundaryConfig.EMAIL_MAX_LENGTH:
                return {"success": False, "error": "Email too long"}
            if len(password) < BoundaryConfig.PASSWORD_MIN_LENGTH:
                return {"success": False, "error": "Password too short"}
            if len(password) > BoundaryConfig.PASSWORD_MAX_LENGTH:
                return {"success": False, "error": "Password too long"}

            # Check if user exists
            with self.lock:
                if email in self.users:
                    return {"success": False, "error": "User already exists"}

                # Create user
                self.users[email] = {
                    "password_hash": f"hash_{password}",
                    "id": len(self.users) + 1,
                    "created_at": datetime.utcnow(),
                    "is_active": True
                }

                return {"success": True, "user_id": self.users[email]["id"]}

        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    async def create_session_with_limits(self, user_id: int, email: str) -> Dict[str, Any]:
        """Create session with boundary checking"""
        with self.lock:
            # Check session limits
            active_sessions = sum(1 for session in self.sessions.values()
                                if session.get("is_active", False))

            if active_sessions >= BoundaryConfig.MAX_CONCURRENT_SESSIONS:
                return {"success": False, "error": "Maximum sessions exceeded"}

            # Create session
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=BoundaryConfig.SESSION_TIMEOUT_MINUTES),
                "is_active": True,
                "last_activity": datetime.utcnow()
            }

            return {"success": True, "session_id": session_id}

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        with self.lock:
            expired_sessions = []
            for session_id, session in self.sessions.items():
                if session["expires_at"] < current_time:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]

            return len(expired_sessions)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        with self.lock:
            active_sessions = sum(1 for session in self.sessions.values()
                                if session.get("is_active", False))

            return {
                "total_users": len(self.users),
                "active_sessions": active_sessions,
                "db_connections": len(self.connections),
                "current_memory_mb": self.monitor_memory_usage(),
                "max_memory_mb": max(self.memory_usage) if self.memory_usage else 0
            }

# Test Fixtures
@pytest.fixture
async def boundary_service():
    """Provide boundary test service"""
    service = BoundaryTestService()
    yield service
    # Cleanup
    service.users.clear()
    service.sessions.clear()
    service.connections.clear()
    gc.collect()

@pytest.fixture
def boundary_config():
    """Provide boundary configuration"""
    return BoundaryConfig()

# ============================================================================
# BOUNDARY TESTS - INPUT LENGTH LIMITS
# ============================================================================

class TestInputLengthBoundaries:
    """Test input length boundaries and edge cases"""

    @pytest.mark.asyncio
    async def test_email_minimum_length_boundary(self, boundary_service):
        """📏 Test email minimum length boundary"""
        # Test emails at and around minimum length
        test_cases = [
            ("a@b.c", True),      # 5 chars - should pass
            ("ab@c.d", True),     # 6 chars - should pass
            ("a@b", False),       # 3 chars - should fail
            ("@b.c", False),      # 4 chars - should fail
            ("", False),          # 0 chars - should fail
        ]

        for email, should_succeed in test_cases:
            result = await boundary_service.register_user_with_limits(email, "ValidPassword123!")

            if should_succeed:
                assert result["success"] is True, f"Email '{email}' should have succeeded"
            else:
                assert result["success"] is False, f"Email '{email}' should have failed"
                assert "too short" in result["error"].lower() or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_email_maximum_length_boundary(self, boundary_service):
        """📏 Test email maximum length boundary"""
        # Create emails of various lengths around the boundary
        base_email = "test@example.com"  # 16 chars
        max_length = BoundaryConfig.EMAIL_MAX_LENGTH

        # Test at boundary
        long_prefix = "a" * (max_length - len("@example.com"))
        boundary_email = f"{long_prefix}@example.com"

        result = await boundary_service.register_user_with_limits(boundary_email, "ValidPassword123!")
        assert result["success"] is True, f"Email at max length ({len(boundary_email)}) should succeed"

        # Test over boundary
        over_boundary_email = boundary_email + "x"
        result = await boundary_service.register_user_with_limits(over_boundary_email, "ValidPassword123!")
        assert result["success"] is False
        assert "too long" in result["error"].lower()

        # Test extremely long email
        extremely_long_email = "a" * 1000 + "@example.com"
        result = await boundary_service.register_user_with_limits(extremely_long_email, "ValidPassword123!")
        assert result["success"] is False
        assert "too long" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_password_length_boundaries(self, boundary_service):
        """📏 Test password length boundaries"""
        email = "boundary@example.com"

        # Test minimum password length
        min_length = BoundaryConfig.PASSWORD_MIN_LENGTH

        # Just under minimum
        short_password = "a" * (min_length - 1)
        result = await boundary_service.register_user_with_limits(email, short_password)
        assert result["success"] is False
        assert "too short" in result["error"].lower()

        # At minimum length
        min_password = "A1b2c3d4"  # 8 chars with variety
        result = await boundary_service.register_user_with_limits(email + "1", min_password)
        assert result["success"] is True

        # At maximum length
        max_length = BoundaryConfig.PASSWORD_MAX_LENGTH
        max_password = "A1b2" + "x" * (max_length - 4)
        result = await boundary_service.register_user_with_limits(email + "2", max_password)
        assert result["success"] is True

        # Over maximum length
        over_max_password = max_password + "extra"
        result = await boundary_service.register_user_with_limits(email + "3", over_max_password)
        assert result["success"] is False
        assert "too long" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unicode_character_boundaries(self, boundary_service):
        """📏 Test Unicode character handling in boundaries"""
        # Test emails with Unicode characters
        unicode_emails = [
            "tëst@example.com",           # Accented characters
            "用户@example.com",            # Chinese characters
            "тест@example.com",           # Cyrillic characters
            "🚀user@example.com",         # Emoji (technically valid)
            "user@üñíçødé.com",          # Unicode domain
        ]

        for email in unicode_emails:
            result = await boundary_service.register_user_with_limits(email, "Password123!")

            # Unicode handling depends on implementation
            # At minimum, should not crash
            assert "error" in result or "success" in result

            if result["success"] is False:
                # Should have meaningful error message
                assert result["error"] != ""

    @pytest.mark.asyncio
    async def test_special_character_boundaries(self, boundary_service):
        """📏 Test special character handling at boundaries"""
        # Test passwords with various special characters
        special_passwords = [
            "Aa1!" + "x" * (BoundaryConfig.PASSWORD_MIN_LENGTH - 4),  # Minimum with specials
            "A" * 50 + "1!" + "b" * (BoundaryConfig.PASSWORD_MAX_LENGTH - 53),  # Maximum with specials
            "Password123!" + "🔐" * 10,  # Unicode special chars
            "Pass123!" + "™©®€¥£" + "word",  # Various symbols
        ]

        for i, password in enumerate(special_passwords):
            email = f"special{i}@example.com"
            result = await boundary_service.register_user_with_limits(email, password)

            if len(password) <= BoundaryConfig.PASSWORD_MAX_LENGTH:
                # Should handle special characters gracefully
                assert result["success"] is True or "format" in result["error"].lower()
            else:
                assert result["success"] is False
                assert "too long" in result["error"].lower()

# ============================================================================
# BOUNDARY TESTS - SYSTEM RESOURCE LIMITS
# ============================================================================

class TestSystemResourceBoundaries:
    """Test system resource boundaries and limits"""

    @pytest.mark.asyncio
    async def test_maximum_concurrent_sessions(self, boundary_service):
        """🚀 Test maximum concurrent session boundary"""
        # Create users and sessions up to the limit
        max_sessions = min(100, BoundaryConfig.MAX_CONCURRENT_SESSIONS)  # Use smaller number for testing

        created_sessions = 0
        for i in range(max_sessions + 10):  # Try to exceed limit
            email = f"session{i}@example.com"
            await boundary_service.register_user_with_limits(email, "Password123!")

            session_result = await boundary_service.create_session_with_limits(i + 1, email)

            if session_result["success"]:
                created_sessions += 1
            else:
                # Should hit limit before creating all sessions
                assert "Maximum sessions exceeded" in session_result["error"]
                break

        # Verify we created sessions up to (but not exceeding) the limit
        assert created_sessions <= max_sessions

        # Verify system stats
        stats = boundary_service.get_system_stats()
        assert stats["active_sessions"] <= max_sessions

    @pytest.mark.asyncio
    async def test_memory_usage_boundaries(self, boundary_service):
        """💾 Test memory usage boundaries"""
        initial_memory = boundary_service.monitor_memory_usage()

        # Create many users to increase memory usage
        users_created = 0
        memory_limit_hit = False

        for i in range(1000):  # Create many users
            email = f"memory{i}@example.com"
            # Create larger password to use more memory
            large_password = "Password123!" + "x" * 100

            result = await boundary_service.register_user_with_limits(email, large_password)

            if result["success"]:
                users_created += 1
            else:
                if "memory limit exceeded" in result["error"].lower():
                    memory_limit_hit = True
                    break

            # Check memory periodically
            if i % 100 == 0:
                current_memory = boundary_service.monitor_memory_usage()
    # print(f"Created {users_created} users, Memory: {current_memory:.1f}MB")

        final_memory = boundary_service.monitor_memory_usage()
        memory_increase = final_memory - initial_memory

    # print(f"Memory Test Results:")
    # print(f"  Users Created: {users_created}")
    # print(f"  Memory Increase: {memory_increase:.1f}MB")
    # print(f"  Memory Limit Hit: {memory_limit_hit}")

        # Verify memory was tracked
        assert len(boundary_service.memory_usage) > 0
        assert final_memory >= initial_memory  # Memory should have increased

    @pytest.mark.asyncio
    async def test_database_connection_limits(self, boundary_service):
        """🗄️ Test database connection boundaries"""
        max_connections = BoundaryConfig.MAX_DB_CONNECTIONS

        # Test creating connections up to limit
        successful_connections = 0
        for i in range(max_connections + 10):
            if boundary_service.simulate_db_connection():
                successful_connections += 1
            else:
                break

        assert successful_connections == max_connections

        # Try to create one more - should fail
        assert boundary_service.simulate_db_connection() is False

        # Release some connections
        connections_to_release = 10
        for i in range(connections_to_release):
            connection_id = f"conn_{i}_{time.time()}"
            boundary_service.release_db_connection(connection_id)

        # Should be able to create more connections now
        additional_connections = 0
        for i in range(5):
            if boundary_service.simulate_db_connection():
                additional_connections += 1

        assert additional_connections > 0

    @pytest.mark.asyncio
    async def test_session_cleanup_boundaries(self, boundary_service):
        """🧹 Test session cleanup at boundaries"""
        # Create sessions with different expiry times
        current_time = datetime.utcnow()

        sessions_created = 0
        for i in range(50):
            email = f"cleanup{i}@example.com"
            await boundary_service.register_user_with_limits(email, "Password123!")

            # Create session
            result = await boundary_service.create_session_with_limits(i + 1, email)
            if result["success"]:
                sessions_created += 1

                # Manually expire some sessions
                if i % 3 == 0:  # Every 3rd session
                    session_id = result["session_id"]
                    boundary_service.sessions[session_id]["expires_at"] = current_time - timedelta(minutes=1)

        # Run cleanup
        expired_count = boundary_service.cleanup_expired_sessions()

        # Verify cleanup worked
        assert expired_count > 0
        assert expired_count < sessions_created

        stats = boundary_service.get_system_stats()
        assert stats["active_sessions"] == sessions_created - expired_count

# ============================================================================
# BOUNDARY TESTS - TIME-BASED LIMITS
# ============================================================================

class TestTimeBasedBoundaries:
    """Test time-based boundaries and edge cases"""

    @pytest.mark.asyncio
    async def test_session_timeout_boundaries(self, boundary_service):
        """⏰ Test session timeout boundaries"""
        email = "timeout@example.com"
        await boundary_service.register_user_with_limits(email, "Password123!")

        # Create session
        session_result = await boundary_service.create_session_with_limits(1, email)
        assert session_result["success"] is True
        session_id = session_result["session_id"]

        # Verify session is active
        session = boundary_service.sessions[session_id]
        assert session["is_active"] is True

        # Manually expire the session
        session["expires_at"] = datetime.utcnow() - timedelta(seconds=1)

        # Run cleanup
        expired_count = boundary_service.cleanup_expired_sessions()
        assert expired_count == 1

        # Session should be gone
        assert session_id not in boundary_service.sessions

    @pytest.mark.asyncio
    async def test_rapid_session_creation_timing(self, boundary_service):
        """⚡ Test rapid session creation timing boundaries"""
        email = "rapid@example.com"
        await boundary_service.register_user_with_limits(email, "Password123!")

        # Create many sessions rapidly
        session_times = []
        sessions_created = 0

        for i in range(20):
            start_time = time.time()
            result = await boundary_service.create_session_with_limits(1, email)
            end_time = time.time()

            session_times.append(end_time - start_time)

            if result["success"]:
                sessions_created += 1

        # Analyze timing
        avg_time = sum(session_times) / len(session_times)
        max_time = max(session_times)

    # print(f"Session Creation Timing:")
    # print(f"  Sessions Created: {sessions_created}")
    # print(f"  Average Time: {avg_time:.3f}s")
    # print(f"  Maximum Time: {max_time:.3f}s")

        # Verify reasonable performance
        assert avg_time < 0.1  # Average under 100ms
        assert max_time < 0.5  # Maximum under 500ms

    @pytest.mark.asyncio
    async def test_clock_synchronization_boundaries(self, boundary_service):
        """🕐 Test system behavior with time edge cases"""
        email = "clock@example.com"
        await boundary_service.register_user_with_limits(email, "Password123!")

        # Test session creation at exact timeout boundary
        current_time = datetime.utcnow()

        # Create session
        result = await boundary_service.create_session_with_limits(1, email)
        session_id = result["session_id"]

        # Get the session
        session = boundary_service.sessions[session_id]
        expires_at = session["expires_at"]

        # Calculate time until expiry
        time_to_expiry = (expires_at - current_time).total_seconds()

        # Verify reasonable expiry time
        expected_expiry = BoundaryConfig.SESSION_TIMEOUT_MINUTES * 60
        assert abs(time_to_expiry - expected_expiry) < 10  # Within 10 seconds

# ============================================================================
# BOUNDARY TESTS - EDGE CASES AND CORNER CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and corner cases"""

    @pytest.mark.asyncio
    async def test_null_and_empty_input_handling(self, boundary_service):
        """🚫 Test handling of null and empty inputs"""
        edge_case_inputs = [
            ("", ""),                    # Both empty
            ("", "Password123!"),        # Empty email
            ("test@example.com", ""),    # Empty password
            (None, "Password123!"),      # None email
            ("test@example.com", None),  # None password
        ]

        for email, password in edge_case_inputs:
            try:
                # Handle None values
                email_param = email if email is not None else ""
                password_param = password if password is not None else ""

                result = await boundary_service.register_user_with_limits(email_param, password_param)

                assert result["success"] is False
                assert result["error"] != ""  # Should have meaningful error message

            except Exception as e:
                # Should handle exceptions gracefully
                assert "error" in str(e).lower() or len(str(e)) > 0

    @pytest.mark.asyncio
    async def test_whitespace_boundary_cases(self, boundary_service):
        """⬜ Test whitespace handling at boundaries"""
        whitespace_cases = [
            (" test@example.com", "Password123!"),         # Leading space in email
            ("test@example.com ", "Password123!"),         # Trailing space in email
            ("test@example.com", " Password123!"),         # Leading space in password
            ("test@example.com", "Password123! "),         # Trailing space in password
            ("  test@example.com  ", "  Password123!  "),  # Spaces in both
            ("test@exam ple.com", "Password123!"),         # Space in middle of email
            ("test@example.com", "Pass word123!"),         # Space in middle of password
        ]

        for email, password in whitespace_cases:
            result = await boundary_service.register_user_with_limits(email, password)

            # System should either accept (after trimming) or reject with clear error
            if result["success"] is False:
                assert "invalid" in result["error"].lower() or "format" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_extremely_large_requests(self, boundary_service):
        """🦣 Test handling of extremely large requests"""
        # Test with very large email
        huge_email = "a" * 10000 + "@example.com"
        result = await boundary_service.register_user_with_limits(huge_email, "Password123!")
        assert result["success"] is False
        assert "too long" in result["error"].lower()

        # Test with very large password
        huge_password = "Password123!" + "x" * 10000
        result = await boundary_service.register_user_with_limits("test@example.com", huge_password)
        assert result["success"] is False
        assert "too long" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_boundary_operations(self, boundary_service):
        """🔄 Test concurrent operations at boundaries"""
        async def create_user_and_session(user_index):
            email = f"concurrent{user_index}@example.com"
            password = f"Password{user_index}123!"

            # Register user
            reg_result = await boundary_service.register_user_with_limits(email, password)
            if reg_result["success"]:
                # Create session
                session_result = await boundary_service.create_session_with_limits(
                    reg_result["user_id"], email
                )
                return session_result["success"]
            return False

        # Run many concurrent operations
        num_concurrent = 50
        tasks = [create_user_and_session(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful operations
        successful_operations = sum(1 for result in results if result is True)

        # Verify reasonable success rate under concurrent load
        success_rate = successful_operations / num_concurrent
        assert success_rate > 0.5  # At least 50% success rate

    # print(f"Concurrent Operations Test:")
    # print(f"  Total Operations: {num_concurrent}")
    # print(f"  Successful: {successful_operations}")
    # print(f"  Success Rate: {success_rate:.1%}")

    @pytest.mark.asyncio
    async def test_system_recovery_boundaries(self, boundary_service):
        """🔄 Test system recovery from boundary conditions"""
        # Create users up to near memory limit
        users_created = 0
        for i in range(200):
            email = f"recovery{i}@example.com"
            result = await boundary_service.register_user_with_limits(email, "Password123!")

            if result["success"]:
                users_created += 1
            else:
                break

        initial_memory = boundary_service.monitor_memory_usage()

        # Force cleanup/garbage collection
        gc.collect()

        # Check if system recovered some memory
        post_cleanup_memory = boundary_service.monitor_memory_usage()

        # Try to create more users after cleanup
        additional_users = 0
        for i in range(10):
            email = f"postcleanup{i}@example.com"
            result = await boundary_service.register_user_with_limits(email, "Password123!")

            if result["success"]:
                additional_users += 1

    # print(f"System Recovery Test:")
    # print(f"  Initial Users Created: {users_created}")
    # print(f"  Memory Before Cleanup: {initial_memory:.1f}MB")
    # print(f"  Memory After Cleanup: {post_cleanup_memory:.1f}MB")
    # print(f"  Additional Users After Cleanup: {additional_users}")

        # Verify some level of recovery
        assert additional_users >= 0  # Should at least not crash

# ============================================================================
# BOUNDARY TEST REPORTING
# ============================================================================

class TestBoundaryReport:
    """Generate comprehensive boundary test report"""

    @pytest.mark.asyncio
    async def test_comprehensive_boundary_analysis(self, boundary_service):
        """📊 Comprehensive boundary test analysis"""
        boundary_results = {
            "input_length_tests": {"passed": 0, "failed": 0},
            "resource_limit_tests": {"passed": 0, "failed": 0},
            "time_boundary_tests": {"passed": 0, "failed": 0},
            "edge_case_tests": {"passed": 0, "failed": 0},
            "system_limits_reached": [],
            "performance_metrics": {}
        }

        # Test 1: Input Length Boundaries
        try:
            # Test minimum email length
            result = await boundary_service.register_user_with_limits("a@b.c", "Password123!")
            if result["success"]:
                boundary_results["input_length_tests"]["passed"] += 1
            else:
                boundary_results["input_length_tests"]["failed"] += 1

            # Test maximum password length
            max_password = "A1" + "x" * (BoundaryConfig.PASSWORD_MAX_LENGTH - 2)
            result = await boundary_service.register_user_with_limits("maxpass@test.com", max_password)
            if result["success"]:
                boundary_results["input_length_tests"]["passed"] += 1
            else:
                boundary_results["input_length_tests"]["failed"] += 1

        except Exception as e:
            boundary_results["input_length_tests"]["failed"] += 1

        # Test 2: Resource Limits
        try:
            # Test session creation
            initial_sessions = boundary_service.get_system_stats()["active_sessions"]

            for i in range(10):
                email = f"resource{i}@test.com"
                await boundary_service.register_user_with_limits(email, "Password123!")
                session_result = await boundary_service.create_session_with_limits(i + 100, email)

                if session_result["success"]:
                    boundary_results["resource_limit_tests"]["passed"] += 1
                else:
                    boundary_results["resource_limit_tests"]["failed"] += 1
                    if "exceeded" in session_result["error"].lower():
                        boundary_results["system_limits_reached"].append("session_limit")

        except Exception as e:
            boundary_results["resource_limit_tests"]["failed"] += 1

        # Test 3: Edge Cases
        try:
            # Test empty inputs
            result = await boundary_service.register_user_with_limits("", "")
            if result["success"] is False and result["error"]:
                boundary_results["edge_case_tests"]["passed"] += 1
            else:
                boundary_results["edge_case_tests"]["failed"] += 1

            # Test whitespace handling
            result = await boundary_service.register_user_with_limits(" test@example.com ", "Password123!")
            # Either success or meaningful error
            if result["success"] or "invalid" in result["error"].lower():
                boundary_results["edge_case_tests"]["passed"] += 1
            else:
                boundary_results["edge_case_tests"]["failed"] += 1

        except Exception as e:
            boundary_results["edge_case_tests"]["failed"] += 1

        # Collect performance metrics
        stats = boundary_service.get_system_stats()
        boundary_results["performance_metrics"] = {
            "total_users_created": stats["total_users"],
            "active_sessions": stats["active_sessions"],
            "memory_usage_mb": stats["current_memory_mb"],
            "max_memory_mb": stats["max_memory_mb"]
        }

        # Generate boundary test report
    # print(f"\n🎯 BOUNDARY TEST ANALYSIS REPORT")
    # print("=" * 50)
    # print(f"Test Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    # print()

    # print("INPUT LENGTH BOUNDARY TESTS:")
        input_tests = boundary_results["input_length_tests"]
        input_total = input_tests["passed"] + input_tests["failed"]
        input_success_rate = (input_tests["passed"] / input_total * 100) if input_total > 0 else 0
    # print(f"  Passed: {input_tests['passed']}")
    # print(f"  Failed: {input_tests['failed']}")
    # print(f"  Success Rate: {input_success_rate:.1f}%")
    # print()

    # print("RESOURCE LIMIT BOUNDARY TESTS:")
        resource_tests = boundary_results["resource_limit_tests"]
        resource_total = resource_tests["passed"] + resource_tests["failed"]
        resource_success_rate = (resource_tests["passed"] / resource_total * 100) if resource_total > 0 else 0
    # print(f"  Passed: {resource_tests['passed']}")
    # print(f"  Failed: {resource_tests['failed']}")
    # print(f"  Success Rate: {resource_success_rate:.1f}%")
    # print()

    # print("EDGE CASE BOUNDARY TESTS:")
        edge_tests = boundary_results["edge_case_tests"]
        edge_total = edge_tests["passed"] + edge_tests["failed"]
        edge_success_rate = (edge_tests["passed"] / edge_total * 100) if edge_total > 0 else 0
    # print(f"  Passed: {edge_tests['passed']}")
    # print(f"  Failed: {edge_tests['failed']}")
    # print(f"  Success Rate: {edge_success_rate:.1f}%")
    # print()

    # print("SYSTEM LIMITS ENCOUNTERED:")
        if boundary_results["system_limits_reached"]:
            for limit in boundary_results["system_limits_reached"]:
    # print(f"  ⚠️ {limit}")
        else:
    # print("  ✅ No system limits reached")
    # print()

    # print("PERFORMANCE METRICS:")
        metrics = boundary_results["performance_metrics"]
    # print(f"  Users Created: {metrics['total_users_created']}")
    # print(f"  Active Sessions: {metrics['active_sessions']}")
    # print(f"  Current Memory: {metrics['memory_usage_mb']:.1f}MB")
    # print(f"  Peak Memory: {metrics['max_memory_mb']:.1f}MB")
    # print()

        # Calculate overall boundary test score
        total_tests = input_total + resource_total + edge_total
        total_passed = input_tests["passed"] + resource_tests["passed"] + edge_tests["passed"]
        overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0

    # print("OVERALL BOUNDARY TEST SCORE:")
        if overall_score >= 90:
    # print(f"🟢 EXCELLENT - {overall_score:.1f}% ({total_passed}/{total_tests})")
        elif overall_score >= 75:
    # print(f"🟡 GOOD - {overall_score:.1f}% ({total_passed}/{total_tests})")
        elif overall_score >= 50:
    # print(f"🟠 FAIR - {overall_score:.1f}% ({total_passed}/{total_tests})")
        else:
    # print(f"🔴 POOR - {overall_score:.1f}% ({total_passed}/{total_tests})")

        # Assertions for test validation
        assert overall_score >= 70, f"Boundary test score too low: {overall_score:.1f}%"
        assert total_passed > 0, "No boundary tests passed"

# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    # print("🎯 Running Authentication Boundary Tests")
    # print("=" * 50)

    # Run boundary tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "--durations=5"
    ])