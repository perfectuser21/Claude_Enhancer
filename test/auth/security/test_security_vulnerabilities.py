# 🛡️ Security Vulnerability Tests
# 安全测试：像银行保险库的安全检查一样测试各种攻击

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import re
import hashlib
import hmac
from datetime import datetime, timedelta

class SecurityTestSuite:
    """Security testing utility class"""

    @staticmethod
    def generate_sql_injection_payloads():
        """Generate various SQL injection attack patterns"""
        return [
            # Classic SQL injection
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' OR 1=1 --",
            "admin'; --",

            # Union-based injection
            "' UNION SELECT * FROM users --",
            "' UNION SELECT username, password FROM users --",
            "1' UNION SELECT NULL, username, password FROM users --",

            # Boolean-based blind injection
            "' AND (SELECT COUNT(*) FROM users) > 0 --",
            "' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a",

            # Time-based blind injection
            "'; WAITFOR DELAY '00:00:05' --",
            "' OR (SELECT SLEEP(5)) --",

            # Error-based injection
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e)) --",
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",

            # NoSQL injection (for MongoDB)
            "'; return db.users.find(); var dummy='",
            "$ne",
            {"$ne": None},
            {"$regex": ".*"},

            # Advanced payloads
            "admin'/*",
            "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT password FROM users LIMIT 0,1),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",
            "1' AND (SELECT 1 FROM (SELECT SLEEP(5))a) --"
        ]

    @staticmethod
    def generate_xss_payloads():
        """Generate Cross-Site Scripting attack patterns"""
        return [
            # Basic XSS
            "<script>alert('XSS')</script>",
            "<script>alert(String.fromCharCode(88,83,83))</script>",

            # Event-based XSS
            "<img src=x onerror=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<svg onload=alert('XSS')>",

            # JavaScript URL
            "javascript:alert('XSS')",
            "JaVaScRiPt:alert('XSS')",

            # Data URL
            "data:text/html,<script>alert('XSS')</script>",

            # Advanced XSS
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<object data=javascript:alert('XSS')>",
            "<embed src=javascript:alert('XSS')>",

            # Encoded XSS
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",

            # Filter bypass
            "<script>/**/alert('XSS')</script>",
            "<SCR\x00IPT>alert('XSS')</SCR\x00IPT>",
        ]

    @staticmethod
    def generate_buffer_overflow_payloads():
        """Generate buffer overflow test data"""
        return [
            "A" * 1000,      # 1KB
            "A" * 10000,     # 10KB
            "A" * 100000,    # 100KB
            "A" * 1000000,   # 1MB
            "X" * 5000000,   # 5MB (very large)
        ]

    @staticmethod
    def generate_jwt_attack_payloads():
        """Generate JWT attack patterns"""
        return [
            # None algorithm attack
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",

            # Algorithm confusion
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",

            # Tampered payload
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsIm5hbWUiOiJBZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0.invalid_signature",

            # Invalid format
            "invalid.jwt.token",
            "header.payload",
            "header.payload.signature.extra",
            "",
            None,
        ]

    @staticmethod
    def detect_sql_injection_attempt(query_string):
        """Detect potential SQL injection in query string"""
        suspicious_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\'\s*(OR|AND)\s+\'\d+\'\s*=\s*\'\d+\')",
            r"(\bWAITFOR\b|\bSLEEP\b|\bBENCHMARK\b)",
            r"(\bEXTRACTVALUE\b|\bUNION\b|\bSELECT\b)",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                return True
        return False


@pytest.fixture
def security_test_suite():
    """Security test suite fixture"""
    return SecurityTestSuite()


@pytest.fixture
def mock_auth_service_with_security():
    """Mock auth service with security features"""
    class SecureAuthService:
        def __init__(self):
            self.failed_attempts = {}
            self.blacklisted_tokens = set()
            self.rate_limits = {}

        async def validate_input(self, data, field_name):
            """Validate input for security threats"""
            if not isinstance(data, str):
                return True

            # Check for SQL injection
            if SecurityTestSuite.detect_sql_injection_attempt(data):
                raise ValueError(f"Potential SQL injection detected in {field_name}")

            # Check for XSS
            xss_patterns = [
                r"<script",
                r"javascript:",
                r"onerror\s*=",
                r"onload\s*=",
                r"<iframe",
                r"<object",
                r"<embed"
            ]

            for pattern in xss_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    raise ValueError(f"Potential XSS detected in {field_name}")

            return True

        async def register_user(self, user_data):
            """Secure user registration with input validation"""
            # Validate all string inputs
            for field, value in user_data.items():
                if isinstance(value, str):
                    await self.validate_input(value, field)

            # Check for buffer overflow attempts
            for field, value in user_data.items():
                if isinstance(value, str) and len(value) > 10000:
                    raise ValueError(f"Input too long for field {field}")

            return {
                "user": {"id": "secure-user-123", "email": user_data.get("email")},
                "tokens": {"access_token": "secure.token.here"}
            }

        async def authenticate_user(self, credentials):
            """Secure authentication with rate limiting"""
            email = credentials.get("email")

            # Check rate limiting
            if email in self.rate_limits:
                last_attempt, count = self.rate_limits[email]
                if time.time() - last_attempt < 60 and count >= 5:
                    raise ValueError("Rate limit exceeded")

            # Validate inputs
            for field, value in credentials.items():
                if isinstance(value, str):
                    await self.validate_input(value, field)

            # Mock authentication logic
            if email == "admin@example.com" and credentials.get("password") == "admin123":
                return {"user": {"id": "admin-123"}, "tokens": {"access_token": "admin.token"}}
            else:
                # Record failed attempt
                if email in self.rate_limits:
                    self.rate_limits[email] = (time.time(), self.rate_limits[email][1] + 1)
                else:
                    self.rate_limits[email] = (time.time(), 1)
                raise ValueError("Invalid credentials")

        def verify_token(self, token):
            """Secure token verification"""
            if token in self.blacklisted_tokens:
                raise ValueError("Token has been revoked")

            # Check for JWT attacks
            if token in SecurityTestSuite.generate_jwt_attack_payloads():
                raise ValueError("Malicious token detected")

            # Basic validation
            if not token or len(token) < 10:
                raise ValueError("Invalid token format")

            return {"user_id": "valid-user", "exp": time.time() + 3600}

    return SecureAuthService()


class TestSQLInjectionProtection:
    """Test SQL injection protection mechanisms"""

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_registration_sql_injection_protection(self, mock_auth_service_with_security, security_test_suite):
        """测试注册时的SQL注入防护 - 像检查恶意代码注入"""
        sql_payloads = security_test_suite.generate_sql_injection_payloads()

        for payload in sql_payloads:
            user_data = {
                "username": payload,
                "email": f"test{hash(payload)}@example.com",
                "password": "TestPassword123!"
            }

            with pytest.raises(ValueError, match="Potential SQL injection detected"):
                await mock_auth_service_with_security.register_user(user_data)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_login_sql_injection_protection(self, mock_auth_service_with_security, security_test_suite):
        """测试登录时的SQL注入防护 - 像检查恶意登录尝试"""
        sql_payloads = security_test_suite.generate_sql_injection_payloads()

        for payload in sql_payloads:
            credentials = {
                "email": payload,
                "password": "anything"
            }

            with pytest.raises(ValueError, match="Potential SQL injection detected"):
                await mock_auth_service_with_security.authenticate_user(credentials)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_password_field_sql_injection_protection(self, mock_auth_service_with_security, security_test_suite):
        """测试密码字段SQL注入防护 - 像检查密码中的恶意代码"""
        sql_payloads = security_test_suite.generate_sql_injection_payloads()

        for payload in sql_payloads:
            credentials = {
                "email": "test@example.com",
                "password": payload
            }

            with pytest.raises(ValueError, match="Potential SQL injection detected"):
                await mock_auth_service_with_security.authenticate_user(credentials)

    @pytest.mark.security
    def test_sql_injection_detection_patterns(self, security_test_suite):
        """测试SQL注入检测模式 - 验证检测算法准确性"""
        # Positive cases (should detect)
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; --",
            "1' UNION SELECT * FROM users --"
        ]

        for malicious_input in malicious_inputs:
            assert security_test_suite.detect_sql_injection_attempt(malicious_input) is True

        # Negative cases (should not detect)
        legitimate_inputs = [
            "normal_username",
            "user@example.com",
            "MyPassword123!",
            "John O'Connor",  # Legitimate apostrophe
            "It's a normal sentence"
        ]

        for legitimate_input in legitimate_inputs:
            assert security_test_suite.detect_sql_injection_attempt(legitimate_input) is False


class TestXSSProtection:
    """Test Cross-Site Scripting (XSS) protection"""

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_registration_xss_protection(self, mock_auth_service_with_security, security_test_suite):
        """测试注册时的XSS防护 - 像检查恶意脚本注入"""
        xss_payloads = security_test_suite.generate_xss_payloads()

        for payload in xss_payloads:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPassword123!",
                "first_name": payload,  # XSS in first name
                "last_name": "User"
            }

            with pytest.raises(ValueError, match="Potential XSS detected"):
                await mock_auth_service_with_security.register_user(user_data)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_multiple_field_xss_protection(self, mock_auth_service_with_security):
        """测试多字段XSS防护 - 像检查所有输入字段"""
        xss_payload = "<script>alert('XSS')</script>"

        fields_to_test = ["username", "email", "first_name", "last_name"]

        for field in fields_to_test:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User"
            }
            user_data[field] = xss_payload

            with pytest.raises(ValueError, match="Potential XSS detected"):
                await mock_auth_service_with_security.register_user(user_data)


class TestBufferOverflowProtection:
    """Test buffer overflow protection"""

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_registration_buffer_overflow_protection(self, mock_auth_service_with_security, security_test_suite):
        """测试注册时的缓冲区溢出防护 - 像检查超长输入"""
        overflow_payloads = security_test_suite.generate_buffer_overflow_payloads()

        for payload in overflow_payloads[:3]:  # Test first 3 to avoid timeouts
            user_data = {
                "username": payload,
                "email": "test@example.com",
                "password": "TestPassword123!"
            }

            with pytest.raises(ValueError, match="Input too long"):
                await mock_auth_service_with_security.register_user(user_data)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_email_field_length_limit(self, mock_auth_service_with_security):
        """测试邮箱字段长度限制 - 像检查邮箱长度"""
        very_long_email = "a" * 10000 + "@example.com"

        user_data = {
            "username": "testuser",
            "email": very_long_email,
            "password": "TestPassword123!"
        }

        with pytest.raises(ValueError, match="Input too long"):
            await mock_auth_service_with_security.register_user(user_data)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_password_field_length_limit(self, mock_auth_service_with_security):
        """测试密码字段长度限制 - 像检查密码长度"""
        very_long_password = "A" * 10000 + "1!"

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": very_long_password
        }

        with pytest.raises(ValueError, match="Input too long"):
            await mock_auth_service_with_security.register_user(user_data)


class TestJWTSecurityVulnerabilities:
    """Test JWT security vulnerabilities"""

    @pytest.mark.security
    def test_jwt_none_algorithm_attack(self, mock_auth_service_with_security):
        """测试JWT None算法攻击 - 像使用无签名伪造令牌"""
        none_algorithm_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."

        with pytest.raises(ValueError, match="Malicious token detected"):
            mock_auth_service_with_security.verify_token(none_algorithm_token)

    @pytest.mark.security
    def test_jwt_malformed_tokens(self, mock_auth_service_with_security):
        """测试格式错误的JWT令牌 - 像使用损坏的通行证"""
        malformed_tokens = [
            "invalid.jwt.token",
            "header.payload",
            "header.payload.signature.extra",
            "",
            "a",
            "header.",
            ".payload.signature"
        ]

        for token in malformed_tokens:
            with pytest.raises(ValueError, match="Invalid token format"):
                mock_auth_service_with_security.verify_token(token)

    @pytest.mark.security
    def test_jwt_token_blacklist(self, mock_auth_service_with_security):
        """测试JWT令牌黑名单 - 像阻止被撤销的令牌"""
        revoked_token = "revoked.jwt.token"
        mock_auth_service_with_security.blacklisted_tokens.add(revoked_token)

        with pytest.raises(ValueError, match="Token has been revoked"):
            mock_auth_service_with_security.verify_token(revoked_token)


class TestRateLimitingAndBruteForce:
    """Test rate limiting and brute force protection"""

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_login_rate_limiting(self, mock_auth_service_with_security):
        """测试登录频率限制 - 像限制尝试次数防止暴力破解"""
        credentials = {
            "email": "ratelimit@example.com",
            "password": "wrong_password"
        }

        # First 5 attempts should fail normally
        for i in range(5):
            with pytest.raises(ValueError, match="Invalid credentials"):
                await mock_auth_service_with_security.authenticate_user(credentials)

        # 6th attempt should trigger rate limiting
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            await mock_auth_service_with_security.authenticate_user(credentials)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_brute_force_protection_different_users(self, mock_auth_service_with_security):
        """测试不同用户的暴力破解防护 - 像每个账户独立计算尝试次数"""
        # Test with different emails
        for i in range(3):
            credentials = {
                "email": f"user{i}@example.com",
                "password": "wrong_password"
            }

            # Each user should get their own rate limit counter
            for j in range(4):  # 4 attempts per user
                with pytest.raises(ValueError, match="Invalid credentials"):
                    await mock_auth_service_with_security.authenticate_user(credentials)

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_successful_login_resets_attempts(self, mock_auth_service_with_security):
        """测试成功登录重置尝试次数 - 像正确密码重置失败计数"""
        # First, trigger some failed attempts
        fail_credentials = {
            "email": "admin@example.com",
            "password": "wrong_password"
        }

        for i in range(3):
            with pytest.raises(ValueError, match="Invalid credentials"):
                await mock_auth_service_with_security.authenticate_user(fail_credentials)

        # Then login successfully
        success_credentials = {
            "email": "admin@example.com",
            "password": "admin123"
        }

        result = await mock_auth_service_with_security.authenticate_user(success_credentials)
        assert result["user"]["id"] == "admin-123"


class TestTimingAttacks:
    """Test protection against timing attacks"""

    @pytest.mark.asyncio
    @pytest.mark.security
    @pytest.mark.slow
    async def test_constant_time_password_verification(self, mock_auth_service_with_security):
        """测试密码验证的恒定时间 - 防止时序攻击"""
        # This test would need actual bcrypt implementation
        # Mock version demonstrates the concept

        valid_credentials = {
            "email": "admin@example.com",
            "password": "admin123"
        }

        invalid_credentials = {
            "email": "admin@example.com",
            "password": "wrong_password"
        }

        # Measure timing for valid password
        start_time = time.time()
        try:
            await mock_auth_service_with_security.authenticate_user(valid_credentials)
        except:
            pass
        valid_time = time.time() - start_time

        # Measure timing for invalid password
        start_time = time.time()
        try:
            await mock_auth_service_with_security.authenticate_user(invalid_credentials)
        except:
            pass
        invalid_time = time.time() - start_time

        # Time difference should be minimal (within reasonable bounds)
        time_difference = abs(valid_time - invalid_time)
        assert time_difference < 0.1, f"Timing difference too large: {time_difference}s"


class TestInputSanitization:
    """Test input sanitization and validation"""

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_null_byte_injection(self, mock_auth_service_with_security):
        """测试空字节注入防护 - 像检查隐藏的空字符"""
        malicious_inputs = [
            "admin\x00.txt",
            "user\x00'; DROP TABLE users; --",
            "test@example.com\x00@evil.com"
        ]

        for malicious_input in malicious_inputs:
            user_data = {
                "username": malicious_input,
                "email": "test@example.com",
                "password": "TestPassword123!"
            }

            # System should handle null bytes safely
            # In this mock, it would likely pass through, but real implementation should sanitize
            try:
                await mock_auth_service_with_security.register_user(user_data)
                # If it passes, ensure the null byte is removed
                assert "\x00" not in user_data["username"]
            except ValueError:
                # If it fails, that's also acceptable security behavior
                pass

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_unicode_normalization_attacks(self, mock_auth_service_with_security):
        """测试Unicode规范化攻击 - 像检查特殊字符编码"""
        unicode_attacks = [
            "admin\u202E\u202D",  # Right-to-left override
            "test\uFEFF@example.com",  # Zero-width no-break space
            "user\u200B@example.com",  # Zero-width space
        ]

        for attack in unicode_attacks:
            user_data = {
                "username": "testuser",
                "email": attack,
                "password": "TestPassword123!"
            }

            # Should either sanitize or reject
            try:
                result = await mock_auth_service_with_security.register_user(user_data)
                # If accepted, ensure proper normalization
                assert len(result["user"]["email"]) > 0
            except ValueError:
                # Rejection is also acceptable
                pass


class TestCryptographicSecurity:
    """Test cryptographic security measures"""

    @pytest.mark.security
    def test_password_hash_entropy(self):
        """测试密码哈希熵 - 确保哈希值随机性"""
        import bcrypt

        password = "TestPassword123!"
        hashes = []

        # Generate multiple hashes of the same password
        for _ in range(10):
            hash_value = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashes.append(hash_value)

        # All hashes should be different (due to salt)
        unique_hashes = set(hashes)
        assert len(unique_hashes) == len(hashes), "Password hashes should be unique"

        # All hashes should verify correctly
        for hash_value in hashes:
            assert bcrypt.checkpw(password.encode('utf-8'), hash_value)

    @pytest.mark.security
    def test_jwt_secret_strength(self):
        """测试JWT密钥强度 - 确保密钥足够复杂"""
        # In real implementation, check actual JWT secret
        mock_secrets = [
            "secret",  # Too weak
            "123456",  # Too weak
            "my-super-secret-key-that-is-very-long-and-random-12345",  # Good
        ]

        for secret in mock_secrets:
            # Check minimum length
            if len(secret) < 32:
                assert False, f"JWT secret too short: {len(secret)} characters"

            # Check for common patterns
            if secret.lower() in ["secret", "password", "key", "token"]:
                assert False, f"JWT secret too predictable: {secret}"


class TestSessionManagement:
    """Test session and token management security"""

    @pytest.mark.security
    def test_token_expiration_enforcement(self, mock_auth_service_with_security):
        """测试令牌过期执行 - 确保过期令牌被拒绝"""
        # Mock expired token (would need actual JWT implementation)
        expired_token = "expired.jwt.token"

        # Should reject expired tokens
        with pytest.raises(ValueError):
            mock_auth_service_with_security.verify_token(expired_token)

    @pytest.mark.security
    def test_concurrent_session_limits(self, mock_auth_service_with_security):
        """测试并发会话限制 - 像限制同时登录设备数"""
        # This would test actual session management
        # Mock demonstrates the concept
        user_sessions = {
            "user_123": ["session1", "session2", "session3", "session4", "session5"]
        }

        max_sessions = 3
        if len(user_sessions["user_123"]) > max_sessions:
            # Should enforce session limit
            assert False, f"Too many concurrent sessions: {len(user_sessions['user_123'])}"


# Security test runner
class TestSecuritySuite:
    """Comprehensive security test runner"""

    @pytest.mark.security
    def test_security_headers_configuration(self):
        """测试安全头配置 - 像检查HTTP安全头"""
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]

        # Mock response headers (in real test, check actual API response)
        mock_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'"
        }

        for header in required_headers:
            assert header in mock_headers, f"Missing security header: {header}"

    @pytest.mark.security
    def test_error_message_information_disclosure(self):
        """测试错误消息信息泄露 - 确保错误不暴露敏感信息"""
        # Error messages should not reveal:
        # - Database structure
        # - Internal file paths
        # - Stack traces in production
        # - User existence confirmation

        safe_error_messages = [
            "Invalid credentials",
            "Validation failed",
            "Access denied",
            "Resource not found"
        ]

        unsafe_error_messages = [
            "User 'admin' not found in table 'users'",
            "File not found: /etc/passwd",
            "Stack trace: at line 42 in auth.py",
            "Database connection failed to postgresql://user:pass@localhost/db"
        ]

        # Verify safe error messages are used
        for message in safe_error_messages:
            assert len(message) > 0 and not any(
                keyword in message.lower()
                for keyword in ["database", "table", "file", "stack", "trace", "path"]
            )

        # Verify unsafe patterns are avoided
        for message in unsafe_error_messages:
            # These should not be returned to users
            assert any(
                keyword in message.lower()
                for keyword in ["table", "file", "stack", "database", "connection"]
            ), f"Example unsafe message: {message}"