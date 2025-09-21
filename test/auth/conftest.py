# 🔧 Pytest Configuration & Test Fixtures
# 测试配置：像搭建实验室环境一样准备测试所需的一切

import pytest
import asyncio
import asyncpg
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
from pathlib import Path

# Test database configuration
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', 'localhost'),
    'port': int(os.getenv('TEST_DB_PORT', 5432)),
    'database': os.getenv('TEST_DB_NAME', 'auth_test'),
    'user': os.getenv('TEST_DB_USER', 'test_user'),
    'password': os.getenv('TEST_DB_PASSWORD', 'test_password')
}

# Test configuration
TEST_CONFIG = {
    'jwt_secret': 'test-jwt-secret-key-for-testing-only',
    'bcrypt_rounds': 4,  # Lower for faster tests
    'rate_limit_window': 60,
    'rate_limit_max': 100,
    'password_min_length': 8
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_pool():
    """Create a test database connection pool."""
    pool = await asyncpg.create_pool(**TEST_DB_CONFIG, min_size=1, max_size=5)

    # Setup test schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE SCHEMA IF NOT EXISTS auth;

            CREATE TABLE IF NOT EXISTS auth.users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                email_verified BOOLEAN DEFAULT FALSE,
                email_verification_token TEXT,
                email_verification_expires_at TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                last_login_at TIMESTAMP,
                last_login_ip INET,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES auth.users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL,
                device_type VARCHAR(50),
                user_agent TEXT,
                ip_address INET,
                expires_at TIMESTAMP NOT NULL,
                revoked BOOLEAN DEFAULT FALSE,
                revoked_at TIMESTAMP,
                revoked_reason VARCHAR(100),
                last_used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
            CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON auth.refresh_tokens(token_hash);
        """)

    yield pool
    await pool.close()

@pytest.fixture
async def db_connection(test_db_pool):
    """Provide a database connection for tests."""
    async with test_db_pool.acquire() as conn:
        # Start transaction for test isolation
        tr = conn.transaction()
        await tr.start()

        yield conn

        # Rollback transaction to clean up
        await tr.rollback()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock(return_value=True)

    return redis_mock

@pytest.fixture
def test_user_data():
    """Standard test user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    }

@pytest.fixture
def test_user_variations():
    """Various test user data for edge cases."""
    return {
        'valid_users': [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': 'ValidPass123!',
                'first_name': 'User',
                'last_name': 'One'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'password': 'AnotherValid123!',
                'first_name': 'User',
                'last_name': 'Two'
            }
        ],
        'invalid_users': [
            {
                'username': 'x',  # Too short
                'email': 'invalid-email',
                'password': '123',  # Too weak
                'first_name': '',
                'last_name': ''
            },
            {
                'username': 'user_with_very_long_username_that_exceeds_limit',
                'email': 'test@example.com',
                'password': 'onlylowercase',  # Missing requirements
                'first_name': 'Test',
                'last_name': 'User'
            }
        ]
    }

@pytest.fixture
async def created_test_user(db_connection, test_user_data):
    """Create a test user in the database."""
    password_hash = bcrypt.hashpw(
        test_user_data['password'].encode('utf-8'),
        bcrypt.gensalt(rounds=TEST_CONFIG['bcrypt_rounds'])
    ).decode('utf-8')

    result = await db_connection.fetchrow("""
        INSERT INTO auth.users (username, email, password_hash, first_name, last_name)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, email, status, created_at
    """,
        test_user_data['username'],
        test_user_data['email'],
        password_hash,
        test_user_data['first_name'],
        test_user_data['last_name']
    )

    return dict(result)

@pytest.fixture
def jwt_tokens():
    """Generate test JWT tokens."""
    def _generate_tokens(user_id='test-user-123', token_type='access', **kwargs):
        now = datetime.utcnow()

        if token_type == 'access':
            payload = {
                'sub': user_id,
                'type': 'access',
                'iat': now.timestamp(),
                'exp': (now + timedelta(minutes=15)).timestamp(),
                'aud': 'perfect21-app',
                'iss': 'perfect21-auth',
                **kwargs
            }
        else:  # refresh
            payload = {
                'sub': user_id,
                'type': 'refresh',
                'iat': now.timestamp(),
                'exp': (now + timedelta(days=7)).timestamp(),
                'aud': 'perfect21-app',
                'iss': 'perfect21-auth',
                **kwargs
            }

        return jwt.encode(payload, TEST_CONFIG['jwt_secret'], algorithm='HS256')

    return _generate_tokens

@pytest.fixture
def malicious_payloads():
    """SQL injection and other malicious payloads for security testing."""
    return {
        'sql_injection': [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; DELETE FROM users WHERE '1'='1",
            "1'; INSERT INTO users (username, email) VALUES ('hacker', 'hack@evil.com'); --",
            "' UNION SELECT * FROM users --"
        ],
        'xss_payloads': [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        'buffer_overflow': [
            'A' * 10000,  # Very long string
            'x' * 1000000,  # Extremely long string
        ],
        'invalid_tokens': [
            "invalid.jwt.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid",
            "",
            None,
            123,
            [],
            {}
        ]
    }

@pytest.fixture
def performance_test_data():
    """Data for performance testing."""
    return {
        'concurrent_users': 50,
        'max_response_time': 500,  # milliseconds
        'max_registration_time': 1000,  # milliseconds
        'stress_test_users': 1000
    }

@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    email_mock = MagicMock()
    email_mock.send_verification_email = AsyncMock(return_value=True)
    email_mock.send_password_reset_email = AsyncMock(return_value=True)
    email_mock.send_security_alert = AsyncMock(return_value=True)

    return email_mock

@pytest.fixture
def security_test_scenarios():
    """Security testing scenarios."""
    return {
        'rate_limit_test': {
            'window_seconds': 60,
            'max_attempts': 10,
            'test_attempts': 15
        },
        'brute_force_test': {
            'max_failed_attempts': 5,
            'lockout_duration': 1800,  # 30 minutes
            'test_attempts': 10
        },
        'geo_location_test': {
            'suspicious_distance': 10000,  # km
            'time_threshold': 3600  # 1 hour
        }
    }

@pytest.fixture(autouse=True)
async def cleanup_test_data(db_connection):
    """Auto-cleanup test data after each test."""
    yield

    # Clean up test data (runs after each test)
    await db_connection.execute("DELETE FROM auth.refresh_tokens WHERE user_agent LIKE '%test%'")
    await db_connection.execute("DELETE FROM auth.users WHERE email LIKE '%test%' OR email LIKE '%example.com'")

@pytest.fixture
def test_app_client():
    """FastAPI test client for API testing."""
    # This would import your actual FastAPI app
    # from your_app import app
    # from fastapi.testclient import TestClient
    # return TestClient(app)
    pass

# Pytest configuration
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on file path
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "security/" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)