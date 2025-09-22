"""
🎭 Authentication Test Fixtures
===============================

Advanced test data generators and mock services for comprehensive authentication testing
Provides realistic test scenarios and edge cases

Author: Test Data Engineering Agent
"""

import pytest
import asyncio
import secrets
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator
from dataclasses import dataclass
from enum import Enum
import random
import string


class UserRole(Enum):
    """User roles for testing"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class TestScenario(Enum):
    """Test scenario types"""
    HAPPY_PATH = "happy_path"
    ERROR_CASE = "error_case"
    EDGE_CASE = "edge_case"
    SECURITY_TEST = "security_test"
    PERFORMANCE_TEST = "performance_test"


@dataclass
class TestUser:
    """Test user data structure"""
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    mfa_enabled: bool = False
    terms_accepted: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "email": self.email,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "role": self.role.value,
            "is_active": self.is_active,
            "mfa_enabled": self.mfa_enabled,
            "terms_accepted": self.terms_accepted,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TestDataGenerator:
    """Advanced test data generator"""

    @staticmethod
    def generate_email(prefix: str = "test", domain: str = "example.com") -> str:
        """Generate unique test email"""
        timestamp = int(time.time() * 1000)
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"{prefix}_{timestamp}_{random_suffix}@{domain}"

    @staticmethod
    def generate_password(
        length: int = 12,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True
    ) -> str:
        """Generate test password with specified complexity"""
        chars = ""

        if include_lowercase:
            chars += string.ascii_lowercase
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_digits:
            chars += string.digits
        if include_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not chars:
            raise ValueError("At least one character type must be included")

        password = ''.join(random.choices(chars, k=length))

        # Ensure at least one character from each selected type
        requirements = []
        if include_lowercase:
            requirements.append(random.choice(string.ascii_lowercase))
        if include_uppercase:
            requirements.append(random.choice(string.ascii_uppercase))
        if include_digits:
            requirements.append(random.choice(string.digits))
        if include_special:
            requirements.append(random.choice("!@#$%^&*()_+-="))

        # Replace random positions with requirements
        password_list = list(password)
        for i, req_char in enumerate(requirements):
            if i < len(password_list):
                password_list[i] = req_char

        return ''.join(password_list)

    @staticmethod
    def generate_user(
        role: UserRole = UserRole.USER,
        scenario: TestScenario = TestScenario.HAPPY_PATH,
        **kwargs
    ) -> TestUser:
        """Generate test user based on scenario"""

        if scenario == TestScenario.HAPPY_PATH:
            return TestUser(
                email=TestDataGenerator.generate_email("valid"),
                password=TestDataGenerator.generate_password(),
                first_name=f"Test{random.randint(1, 1000)}",
                last_name="User",
                phone=f"+1{random.randint(1000000000, 9999999999)}",
                role=role,
                **kwargs
            )

        elif scenario == TestScenario.ERROR_CASE:
            return TestUser(
                email=TestDataGenerator.generate_email("error"),
                password="weak",  # Deliberately weak password
                first_name="",  # Empty name
                last_name="",
                role=role,
                is_active=False,  # Inactive user
                **kwargs
            )

        elif scenario == TestScenario.EDGE_CASE:
            return TestUser(
                email=TestDataGenerator.generate_email("edge"),
                password="A1!" + "a" * 125,  # Very long password
                first_name="A" * 50,  # Very long name
                last_name="B" * 50,
                phone="+1" + "9" * 15,  # Very long phone
                role=role,
                **kwargs
            )

        elif scenario == TestScenario.SECURITY_TEST:
            return TestUser(
                email="admin' OR '1'='1' --@evil.com",  # SQL injection attempt
                password="<script>alert('xss')</script>",  # XSS attempt
                first_name="'; DROP TABLE users; --",
                last_name="<img src=x onerror=alert('xss')>",
                role=role,
                **kwargs
            )

        else:
            return TestUser(
                email=TestDataGenerator.generate_email(),
                password=TestDataGenerator.generate_password(),
                first_name="Test",
                last_name="User",
                role=role,
                **kwargs
            )

    @staticmethod
    def generate_users_batch(
        count: int,
        role: UserRole = UserRole.USER,
        scenario: TestScenario = TestScenario.HAPPY_PATH
    ) -> List[TestUser]:
        """Generate batch of test users"""
        return [
            TestDataGenerator.generate_user(role, scenario)
            for _ in range(count)
        ]

    @staticmethod
    def generate_device_info(scenario: TestScenario = TestScenario.HAPPY_PATH) -> Dict[str, Any]:
        """Generate device information for testing"""

        if scenario == TestScenario.HAPPY_PATH:
            return {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "platform": "Win32",
                "screen_resolution": "1920x1080",
                "timezone": "America/New_York",
                "language": "en-US"
            }

        elif scenario == TestScenario.EDGE_CASE:
            return {
                "user_agent": "A" * 1000,  # Very long user agent
                "platform": "Unknown",
                "screen_resolution": "99999x99999",
                "timezone": "Invalid/Timezone",
                "language": "xx-XX"
            }

        elif scenario == TestScenario.SECURITY_TEST:
            return {
                "user_agent": "<script>alert('xss')</script>",
                "platform": "'; DROP TABLE devices; --",
                "screen_resolution": "../../../etc/passwd",
                "timezone": "$(whoami)",
                "language": "|cat /etc/shadow"
            }

        else:
            return {
                "user_agent": "TestAgent/1.0",
                "platform": "TestPlatform",
                "screen_resolution": "800x600",
                "timezone": "UTC",
                "language": "en"
            }


class MockJWTService:
    """Mock JWT service for testing"""

    def __init__(self):
        self.secret = "test_jwt_secret_key_12345"
        self.algorithm = "HS256"
        self.tokens = {}  # Track generated tokens
        self.blacklist = set()  # Blacklisted tokens

    def generate_token(
        self,
        user_id: str,
        email: str,
        permissions: List[str] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate JWT token"""
        import jwt

        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "email": email,
            "permissions": permissions or [],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
            "jti": secrets.token_urlsafe(16)
        }

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        self.tokens[payload["jti"]] = payload
        return token

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        import jwt

        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            jti = payload.get("jti")

            if jti in self.blacklist:
                return {"valid": False, "error": "Token blacklisted"}

            return {"valid": True, "payload": payload}

        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}

    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            jti = payload.get("jti")
            if jti:
                self.blacklist.add(jti)
                return True
        except:
            pass
        return False

    def get_token_stats(self) -> Dict[str, Any]:
        """Get token statistics"""
        return {
            "total_tokens": len(self.tokens),
            "blacklisted_tokens": len(self.blacklist),
            "active_tokens": len(self.tokens) - len(self.blacklist)
        }


class MockEmailService:
    """Mock email service for testing"""

    def __init__(self):
        self.sent_emails = []
        self.delivery_failures = set()  # Emails that should fail

    async def send_verification_email(self, email: str, token: str) -> bool:
        """Send verification email"""
        if email in self.delivery_failures:
            return False

        self.sent_emails.append({
            "type": "verification",
            "to": email,
            "token": token,
            "sent_at": datetime.utcnow(),
            "template": "email_verification"
        })
        return True

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email"""
        if email in self.delivery_failures:
            return False

        self.sent_emails.append({
            "type": "password_reset",
            "to": email,
            "token": token,
            "sent_at": datetime.utcnow(),
            "template": "password_reset"
        })
        return True

    async def send_security_alert(self, email: str, alert_type: str, details: Dict[str, Any]) -> bool:
        """Send security alert email"""
        if email in self.delivery_failures:
            return False

        self.sent_emails.append({
            "type": "security_alert",
            "to": email,
            "alert_type": alert_type,
            "details": details,
            "sent_at": datetime.utcnow(),
            "template": "security_alert"
        })
        return True

    def simulate_delivery_failure(self, email: str):
        """Simulate email delivery failure"""
        self.delivery_failures.add(email)

    def get_sent_emails(self, email: str = None, email_type: str = None) -> List[Dict[str, Any]]:
        """Get sent emails with optional filtering"""
        emails = self.sent_emails

        if email:
            emails = [e for e in emails if e["to"] == email]

        if email_type:
            emails = [e for e in emails if e["type"] == email_type]

        return emails

    def clear_sent_emails(self):
        """Clear sent emails history"""
        self.sent_emails.clear()


class MockSMSService:
    """Mock SMS service for MFA testing"""

    def __init__(self):
        self.sent_messages = []
        self.delivery_failures = set()
        self.verification_codes = {}

    async def send_verification_code(self, phone: str, code: str) -> bool:
        """Send SMS verification code"""
        if phone in self.delivery_failures:
            return False

        self.verification_codes[phone] = {
            "code": code,
            "sent_at": datetime.utcnow(),
            "attempts": 0
        }

        self.sent_messages.append({
            "to": phone,
            "code": code,
            "sent_at": datetime.utcnow(),
            "message": f"Your verification code is: {code}"
        })
        return True

    def verify_code(self, phone: str, code: str) -> Dict[str, Any]:
        """Verify SMS code"""
        if phone not in self.verification_codes:
            return {"valid": False, "error": "No code sent to this number"}

        stored_code = self.verification_codes[phone]
        stored_code["attempts"] += 1

        # Check expiration (5 minutes)
        if datetime.utcnow() - stored_code["sent_at"] > timedelta(minutes=5):
            return {"valid": False, "error": "Code expired"}

        # Check max attempts
        if stored_code["attempts"] > 3:
            return {"valid": False, "error": "Too many attempts"}

        # Check code
        if stored_code["code"] != code:
            return {"valid": False, "error": "Invalid code"}

        # Success - remove code
        del self.verification_codes[phone]
        return {"valid": True}

    def simulate_delivery_failure(self, phone: str):
        """Simulate SMS delivery failure"""
        self.delivery_failures.add(phone)

    def get_sent_messages(self, phone: str = None) -> List[Dict[str, Any]]:
        """Get sent messages"""
        if phone:
            return [msg for msg in self.sent_messages if msg["to"] == phone]
        return self.sent_messages.copy()


# Pytest fixtures using the above classes
@pytest.fixture
def test_data_generator():
    """Provide test data generator"""
    return TestDataGenerator()

@pytest.fixture
def mock_jwt_service():
    """Provide mock JWT service"""
    return MockJWTService()

@pytest.fixture
def mock_email_service():
    """Provide mock email service"""
    return MockEmailService()

@pytest.fixture
def mock_sms_service():
    """Provide mock SMS service"""
    return MockSMSService()

@pytest.fixture
def comprehensive_test_users(test_data_generator):
    """Generate comprehensive set of test users for various scenarios"""
    return {
        "valid_users": test_data_generator.generate_users_batch(10, UserRole.USER, TestScenario.HAPPY_PATH),
        "admin_users": test_data_generator.generate_users_batch(3, UserRole.ADMIN, TestScenario.HAPPY_PATH),
        "edge_case_users": test_data_generator.generate_users_batch(5, UserRole.USER, TestScenario.EDGE_CASE),
        "security_test_users": test_data_generator.generate_users_batch(5, UserRole.USER, TestScenario.SECURITY_TEST),
        "error_case_users": test_data_generator.generate_users_batch(5, UserRole.USER, TestScenario.ERROR_CASE)
    }

@pytest.fixture
def device_info_scenarios(test_data_generator):
    """Generate device info for various test scenarios"""
    return {
        "normal_device": test_data_generator.generate_device_info(TestScenario.HAPPY_PATH),
        "suspicious_device": test_data_generator.generate_device_info(TestScenario.SECURITY_TEST),
        "edge_case_device": test_data_generator.generate_device_info(TestScenario.EDGE_CASE)
    }

@pytest.fixture
async def integrated_test_environment(
    mock_jwt_service,
    mock_email_service,
    mock_sms_service,
    test_database
):
    """Provide integrated test environment with all services"""
    class IntegratedTestEnvironment:
        def __init__(self):
            self.jwt_service = mock_jwt_service
            self.email_service = mock_email_service
            self.sms_service = mock_sms_service
            self.database = test_database
            self.test_session_data = {}

        async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
            """Complete user registration flow"""
            # Create user in database
            success = await self.database.create_user(user_data)
            if not success:
                return {"success": False, "error": "User already exists"}

            # Send verification email
            verification_token = secrets.token_urlsafe(32)
            email_sent = await self.email_service.send_verification_email(
                user_data["email"],
                verification_token
            )

            return {
                "success": True,
                "user_id": hash(user_data["email"]),
                "verification_token": verification_token,
                "email_sent": email_sent
            }

        async def login_user(self, email: str, password: str, device_info: Dict[str, Any] = None) -> Dict[str, Any]:
            """Complete user login flow"""
            # Get user from database
            user = await self.database.get_user(email)
            if not user:
                return {"success": False, "error": "User not found"}

            # Simulate password verification (simplified)
            if user.get("password") != password:
                return {"success": False, "error": "Invalid password"}

            # Generate JWT token
            token = self.jwt_service.generate_token(
                user_id=str(hash(email)),
                email=email,
                permissions=["read", "write"]
            )

            # Create session
            session_id = await self.database.create_session({
                "user_email": email,
                "token": token,
                "device_info": device_info or {},
                "created_at": datetime.utcnow()
            })

            return {
                "success": True,
                "token": token,
                "session_id": session_id,
                "user": {
                    "email": email,
                    "id": str(hash(email))
                }
            }

        async def verify_token(self, token: str) -> Dict[str, Any]:
            """Verify JWT token"""
            return self.jwt_service.validate_token(token)

        def get_service_stats(self) -> Dict[str, Any]:
            """Get statistics from all services"""
            return {
                "jwt_service": self.jwt_service.get_token_stats(),
                "email_service": {
                    "total_sent": len(self.email_service.sent_emails),
                    "delivery_failures": len(self.email_service.delivery_failures)
                },
                "sms_service": {
                    "total_sent": len(self.sms_service.sent_messages),
                    "delivery_failures": len(self.sms_service.delivery_failures)
                }
            }

    env = IntegratedTestEnvironment()
    yield env

    # Cleanup
    env.database.cleanup()
    env.email_service.clear_sent_emails()