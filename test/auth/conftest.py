"""
🔧 Authentication Test Configuration
====================================

Shared test fixtures and configuration for authentication test suite
Provides common setup and teardown for all test modules

Author: Test Configuration Agent
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure test logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Test environment configuration
@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "test_environment": "isolated",
        "database_type": "memory",
        "logging_level": "INFO",
        "performance_monitoring": True,
        "security_testing": True,
        "cleanup_after_tests": True,
        "test_data_retention": False,
        "parallel_execution": False,
    }


# Async event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Temporary directory for test files
@pytest.fixture(scope="session")
def temp_test_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp(prefix="auth_tests_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# Test data generators
@pytest.fixture
def valid_user_data():
    """Generate valid user data for testing"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return {
        "email": f"testuser_{timestamp}@example.com",
        "password": "SecureTestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890",
        "country": "US",
        "terms_accepted": True,
    }


@pytest.fixture
def test_users_batch():
    """Generate batch of test users for load testing"""
    users = []
    for i in range(100):
        users.append(
            {
                "email": f"loadtest_{i}@example.com",
                "password": f"LoadTestPassword{i}123!",
                "first_name": f"LoadTest{i}",
                "last_name": "User",
                "phone": f"+123456{i:04d}",
                "country": "US",
                "terms_accepted": True,
            }
        )
    return users


@pytest.fixture
def mfa_test_data():
    """Generate MFA test data"""
    return {
        "valid_codes": ["123456", "789012", "345678"],
        "invalid_codes": ["000000", "111111", "999999", "abcdef"],
        "expired_codes": ["555555"],
        "backup_codes": ["recovery1", "recovery2", "recovery3"],
    }


@pytest.fixture
def invalid_user_data():
    """Generate invalid user data for testing"""
    return [
        {"email": "invalid-email", "password": "ValidPassword123!"},
        {"email": "valid@example.com", "password": "weak"},
        {"email": "", "password": "ValidPassword123!"},
        {"email": "valid@example.com", "password": ""},
        {"email": "a" * 300 + "@example.com", "password": "ValidPassword123!"},
        {"email": "valid@example.com", "password": "a" * 200},
    ]


# Security test data
@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection test payloads"""
    return [
        "admin' OR '1'='1",
        "admin'; DROP TABLE users; --",
        "admin' UNION SELECT * FROM passwords --",
        "admin' OR 1=1 #",
        "'; INSERT INTO admin VALUES('hacker', 'pass'); --",
        "user' OR 'x'='x",
        "admin' AND SLEEP(5) --",
        "'; EXEC xp_cmdshell('dir'); --",
    ]


@pytest.fixture
def xss_payloads():
    """Common XSS test payloads"""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(1)'></iframe>",
        "<svg onload=alert('XSS')>",
        "<object data='javascript:alert(1)'></object>",
        "<script src='http://evil.com/malware.js'></script>",
        "<body onload=alert('XSS')>",
    ]


# Performance test configuration
@pytest.fixture
def performance_config():
    """Performance test configuration"""
    return {
        "light_load_users": 10,
        "medium_load_users": 50,
        "heavy_load_users": 100,
        "stress_test_users": 200,
        "response_time_threshold_ms": 1000,
        "concurrent_request_timeout_s": 30,
        "memory_limit_mb": 512,
        "cpu_limit_percent": 80,
    }


# Test database fixtures
@pytest.fixture
async def test_database():
    """Create isolated test database"""

    # Mock database for testing
    class TestDatabase:
        def __init__(self):
            self.users = {}
            self.sessions = {}
            self.audit_logs = []

        async def create_user(self, user_data: Dict[str, Any]) -> bool:
            email = user_data.get("email")
            if email in self.users:
                return False
            self.users[email] = user_data
            return True

        async def get_user(self, email: str) -> Dict[str, Any]:
            return self.users.get(email)

        async def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
            if email in self.users:
                self.users[email].update(updates)
                return True
            return False

        async def delete_user(self, email: str) -> bool:
            if email in self.users:
                del self.users[email]
                return True
            return False

        async def create_session(self, session_data: Dict[str, Any]) -> str:
            import secrets

            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = session_data
            return session_id

        async def get_session(self, session_id: str) -> Dict[str, Any]:
            return self.sessions.get(session_id)

        async def delete_session(self, session_id: str) -> bool:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

        async def log_audit_event(self, event: Dict[str, Any]):
            self.audit_logs.append({**event, "timestamp": datetime.utcnow()})

        def cleanup(self):
            self.users.clear()
            self.sessions.clear()
            self.audit_logs.clear()

    db = TestDatabase()
    yield db
    db.cleanup()


# Enhanced fixtures for comprehensive testing
@pytest.fixture
def jwt_test_tokens():
    """Generate JWT test tokens for various scenarios"""
    import jwt
    import time
    from datetime import timedelta

    secret = "test_jwt_secret_key"
    now = datetime.utcnow()

    return {
        "valid_token": jwt.encode(
            {
                "user_id": "user123",
                "email": "test@example.com",
                "exp": now + timedelta(hours=1),
                "iat": now,
                "permissions": ["read", "write"],
            },
            secret,
            algorithm="HS256",
        ),
        "expired_token": jwt.encode(
            {
                "user_id": "user123",
                "email": "test@example.com",
                "exp": now - timedelta(hours=1),
                "iat": now - timedelta(hours=2),
            },
            secret,
            algorithm="HS256",
        ),
        "invalid_signature": jwt.encode(
            {
                "user_id": "user123",
                "email": "test@example.com",
                "exp": now + timedelta(hours=1),
                "iat": now,
            },
            "wrong_secret",
            algorithm="HS256",
        ),
        "malformed_token": "invalid.token.format",
    }


@pytest.fixture
def api_test_client():
    """Create test API client"""
    from fastapi.testclient import TestClient
    from backend.auth_service.main import app

    return TestClient(app)


# Authentication service fixtures
@pytest.fixture
async def auth_service(test_database):
    """Create authentication service for testing"""

    class TestAuthService:
        def __init__(self, database):
            self.db = database
            self.jwt_secret = "test_secret_key"
            self.password_pepper = "test_pepper"

        async def register_user(self, email: str, password: str) -> Dict[str, Any]:
            # Simulate user registration
            user_data = {
                "email": email,
                "password_hash": self._hash_password(password),
                "created_at": datetime.utcnow(),
                "is_active": True,
                "failed_login_attempts": 0,
            }

            success = await self.db.create_user(user_data)
            if success:
                await self.db.log_audit_event(
                    {"action": "user_registered", "email": email}
                )
                return {"success": True, "user_id": hash(email)}
            else:
                return {"success": False, "error": "User already exists"}

        async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
            user = await self.db.get_user(email)
            if not user:
                return {"success": False, "error": "Invalid credentials"}

            if self._verify_password(password, user["password_hash"]):
                pass  # Auto-fixed empty block
                # Create session
                session_id = await self.db.create_session(
                    {
                        "email": email,
                        "created_at": datetime.utcnow(),
                        "expires_at": datetime.utcnow(),
                    }
                )

                token = self._generate_token(email)

                await self.db.log_audit_event({"action": "user_login", "email": email})

                return {"success": True, "token": token, "session_id": session_id}
            else:
                await self.db.log_audit_event(
                    {"action": "login_failed", "email": email}
                )
                return {"success": False, "error": "Invalid credentials"}

        async def validate_token(self, token: str) -> Dict[str, Any]:
            # Simple token validation for testing
            if token.startswith("valid_token_"):
                email = token.replace("valid_token_", "")
                return {"success": True, "email": email}
            else:
                return {"success": False, "error": "Invalid token"}

        def _hash_password(self, password: str) -> str:
            import hashlib

            return hashlib.sha256(
                (password + self.password_pepper).encode()
            ).hexdigest()

        def _verify_password(self, password: str, password_hash: str) -> bool:
            return self._hash_password(password) == password_hash

        def _generate_token(self, email: str) -> str:
            return f"valid_token_{email}"

    service = TestAuthService(test_database)
    yield service


# Test monitoring fixtures
@pytest.fixture
def test_monitor():
    """Test execution monitoring"""

    class TestMonitor:
        def __init__(self):
            self.start_time = None
            self.metrics = {
                "tests_executed": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "total_duration": 0,
                "performance_metrics": [],
                "security_events": [],
                "errors": [],
            }

        def start_test(self, test_name: str):
            self.start_time = datetime.utcnow()
            logging.info(f"Starting test: {test_name}")

        def end_test(self, test_name: str, result: str):
            if self.start_time:
                duration = (datetime.utcnow() - self.start_time).total_seconds()
                self.metrics["total_duration"] += duration

            self.metrics["tests_executed"] += 1
            if result == "passed":
                self.metrics["tests_passed"] += 1
            else:
                self.metrics["tests_failed"] += 1

            logging.info(f"Completed test: {test_name} - {result}")

        def record_performance_metric(self, metric_name: str, value: float, unit: str):
            self.metrics["performance_metrics"].append(
                {
                    "name": metric_name,
                    "value": value,
                    "unit": unit,
                    "timestamp": datetime.utcnow(),
                }
            )

        def record_security_event(self, event_type: str, details: Dict[str, Any]):
            self.metrics["security_events"].append(
                {"type": event_type, "details": details, "timestamp": datetime.utcnow()}
            )

        def record_error(self, error_type: str, message: str):
            self.metrics["errors"].append(
                {"type": error_type, "message": message, "timestamp": datetime.utcnow()}
            )

        def get_summary(self) -> Dict[str, Any]:
            return {
                "total_tests": self.metrics["tests_executed"],
                "passed": self.metrics["tests_passed"],
                "failed": self.metrics["tests_failed"],
                "success_rate": (
                    self.metrics["tests_passed"]
                    / max(self.metrics["tests_executed"], 1)
                )
                * 100,
                "total_duration": self.metrics["total_duration"],
                "performance_metrics_count": len(self.metrics["performance_metrics"]),
                "security_events_count": len(self.metrics["security_events"]),
                "errors_count": len(self.metrics["errors"]),
            }

    monitor = TestMonitor()
    yield monitor

    # Print summary at end
    summary = monitor.get_summary()
    logging.info(f"Test execution summary: {summary}")


# Cleanup fixtures
@pytest.fixture(autouse=True)
def auto_cleanup(test_config):
    """Automatic cleanup after each test"""
    yield

    if test_config["cleanup_after_tests"]:
        pass  # Auto-fixed empty block
        # Perform any necessary cleanup
        import gc

        gc.collect()


# Test session reporting
@pytest.fixture(scope="session", autouse=True)
def test_session_setup(test_config):
    """Setup and teardown for entire test session"""
    # print(f"\n🚀 Starting Authentication Test Suite")
    # print(f"Environment: {test_config['test_environment']}")
    # print(f"Database: {test_config['database_type']}")
    # print(f"Security Testing: {test_config['security_testing']}")
    # print(f"Performance Monitoring: {test_config['performance_monitoring']}")
    # print("-" * 60)

    yield

    # print(f"\n✅ Authentication Test Suite Completed")
    # print("-" * 60)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "boundary: mark test as boundary test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        pass  # Auto-fixed empty block
        # Add markers based on test file names
        if "unit_test" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration_test" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "security_test" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "performance_test" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        elif "boundary_test" in item.nodeid:
            item.add_marker(pytest.mark.boundary)


def pytest_runtest_setup(item):
    """Setup before each test"""
    logging.info(f"Setting up test: {item.name}")


def pytest_runtest_teardown(item):
    """Teardown after each test"""
    logging.info(f"Tearing down test: {item.name}")


# Custom test result collection
def pytest_runtest_makereport(item, call):
    """Collect test results for reporting"""
    if call.when == "call":
        test_name = item.name
        outcome = "passed" if call.excinfo is None else "failed"

        # Store result for potential use by other fixtures
        if not hasattr(item.session, "test_results"):
            item.session.test_results = []

        item.session.test_results.append(
            {
                "name": test_name,
                "outcome": outcome,
                "duration": call.duration,
                "timestamp": datetime.utcnow(),
            }
        )


# Load testing fixtures
@pytest.fixture
def load_test_config():
    """Configuration for load testing"""
    return {
        "light_load": {"users": 10, "duration": 30},
        "medium_load": {"users": 50, "duration": 60},
        "heavy_load": {"users": 100, "duration": 90},
        "stress_test": {"users": 200, "duration": 120},
        "spike_test": {"users": 500, "duration": 10},
    }


@pytest.fixture
async def test_database_with_users(test_database, test_users_batch):
    """Database pre-populated with test users"""
    for user in test_users_batch:
        await test_database.create_user(user)
    yield test_database
    test_database.cleanup()


# Security testing fixtures
@pytest.fixture
def security_test_payloads():
    """Comprehensive security test payloads"""
    return {
        "sql_injection": [
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM passwords --",
            "admin' OR 1=1 #",
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'></iframe>",
        ],
        "command_injection": [
            "; ls -la",
            "&& cat /etc/passwd",
            "| whoami",
            "`id`",
            "$(uname -a)",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
    }


# Async test utilities
@pytest.fixture
def async_test_helper():
    """Helper utilities for async tests"""

    class AsyncTestHelper:
        @staticmethod
        async def wait_for_condition(
            condition_func, timeout_seconds=5, check_interval=0.1
        ):
            """Wait for a condition to become true"""
            import asyncio

            end_time = asyncio.get_event_loop().time() + timeout_seconds

            while asyncio.get_event_loop().time() < end_time:
                if (
                    await condition_func()
                    if asyncio.iscoroutinefunction(condition_func)
                    else condition_func()
                ):
                    return True
                await asyncio.sleep(check_interval)

            return False

        @staticmethod
        async def run_concurrent_tasks(tasks, max_concurrent=10):
            """Run tasks concurrently with limit"""
            import asyncio

            semaphore = asyncio.Semaphore(max_concurrent)

            async def run_with_semaphore(task):
                async with semaphore:
                    return await task

            return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

        @staticmethod
        async def measure_response_time(async_func, *args, **kwargs):
            """Measure async function response time"""
            start_time = time.time()
            result = await async_func(*args, **kwargs)
            end_time = time.time()
            return (
                result,
                (end_time - start_time) * 1000,
            )  # Return result and time in ms

        @staticmethod
        def generate_concurrent_users(
            count, base_email="testuser", password="TestPass123!"
        ):
            """Generate concurrent test users"""
            return [
                {
                    "email": f"{base_email}{i}@example.com",
                    "password": f"{password}{i}",
                    "first_name": f"Test{i}",
                    "last_name": "User",
                }
                for i in range(count)
            ]

    return AsyncTestHelper()
