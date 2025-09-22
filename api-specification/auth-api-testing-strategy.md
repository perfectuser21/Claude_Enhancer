# Authentication API Testing Strategy

## 🎯 Testing Overview

Comprehensive testing strategy for the Perfect21 Authentication API covering security, functionality, performance, and integration testing.

## 📋 Test Categories

### 1. Unit Tests

#### Password Management Tests

```python
import pytest
from auth.password_manager import PasswordManager

class TestPasswordManager:
    def test_password_hashing(self):
        """Test password hashing functionality"""
        password = "SecurePass123!"
        hashed = PasswordManager.hash_password(password)

        assert hashed != password
        assert PasswordManager.verify_password(password, hashed)
        assert not PasswordManager.verify_password("WrongPass", hashed)

    def test_password_strength_validation(self):
        """Test password strength validation"""
        # Valid password
        errors = PasswordManager.validate_password_strength("ValidPass123!")
        assert len(errors) == 0

        # Too short
        errors = PasswordManager.validate_password_strength("Short1!")
        assert "at least 8 characters" in str(errors)

        # Missing uppercase
        errors = PasswordManager.validate_password_strength("lowercase123!")
        assert "uppercase letter" in str(errors)

        # Missing special character
        errors = PasswordManager.validate_password_strength("NoSpecial123")
        assert "special character" in str(errors)
```

#### JWT Token Tests

```python
class TestTokenManager:
    def setup_method(self):
        self.token_manager = TokenManager("test-secret-key")

    def test_token_generation(self):
        """Test JWT token generation"""
        user_id = "test-user-123"
        role = "user"

        tokens = self.token_manager.generate_tokens(user_id, role)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"
        assert tokens["expires_in"] == 3600

    def test_token_verification(self):
        """Test JWT token verification"""
        user_id = "test-user-123"
        role = "user"

        tokens = self.token_manager.generate_tokens(user_id, role)

        # Verify access token
        payload = self.token_manager.verify_token(tokens["access_token"], "access")
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_invalid_token_verification(self):
        """Test invalid token verification"""
        invalid_token = "invalid.jwt.token"
        payload = self.token_manager.verify_token(invalid_token, "access")
        assert payload is None
```

### 2. Integration Tests

#### API Endpoint Tests

```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestAuthenticationEndpoints:

    def test_user_registration_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == user_data["email"]

    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        }

        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201

        # Duplicate registration
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 409
        data = response2.json()
        assert data["error"]["code"] == "CONFLICT"

    def test_user_login_success(self, client):
        """Test successful user login"""
        # Register user first
        register_data = {
            "email": "login@example.com",
            "password": "SecurePass123!"
        }
        client.post("/api/auth/register", json=register_data)

        # Login
        login_data = {
            "email": "login@example.com",
            "password": "SecurePass123!"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "tokens" in data

    def test_user_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_protected_endpoint_access(self, client):
        """Test accessing protected endpoint with valid token"""
        # Register and get token
        user_data = {
            "email": "protected@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        tokens = response.json()["tokens"]

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/api/auth/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]

    def test_protected_endpoint_unauthorized(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/profile")
        assert response.status_code == 401

    def test_token_refresh(self, client):
        """Test token refresh functionality"""
        # Register and get tokens
        user_data = {
            "email": "refresh@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        tokens = response.json()["tokens"]

        # Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_user_logout(self, client):
        """Test user logout"""
        # Register and get token
        user_data = {
            "email": "logout@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        tokens = response.json()["tokens"]

        # Logout
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"
```

### 3. Security Tests

#### Input Validation Tests

```python
class TestInputValidation:

    def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        malicious_data = {
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "Password123!"
        }

        response = client.post("/api/auth/register", json=malicious_data)
        # Should either reject with validation error or safely handle
        assert response.status_code in [400, 422]

    def test_xss_protection(self, client):
        """Test XSS protection in input fields"""
        xss_data = {
            "email": "test@example.com",
            "password": "Password123!",
            "first_name": "<script>alert('xss')</script>",
            "last_name": "<img src=x onerror=alert('xss')>"
        }

        response = client.post("/api/auth/register", json=xss_data)

        if response.status_code == 201:
            # Check that script tags are sanitized
            user_data = response.json()["user"]
            assert "<script>" not in user_data["first_name"]
            assert "<img" not in user_data["last_name"]

    def test_password_requirements(self, client):
        """Test password security requirements"""
        weak_passwords = [
            "123456",           # Too short, no complexity
            "password",         # No numbers, no special chars
            "PASSWORD123",      # No lowercase
            "password123",      # No uppercase
            "Password123"       # No special characters
        ]

        for weak_password in weak_passwords:
            user_data = {
                "email": f"test{weak_password}@example.com",
                "password": weak_password
            }

            response = client.post("/api/auth/register", json=user_data)
            assert response.status_code in [400, 422]
```

#### Authentication Security Tests

```python
class TestAuthenticationSecurity:

    def test_brute_force_protection(self, client):
        """Test brute force attack protection"""
        # Register a user
        user_data = {
            "email": "bruteforce@example.com",
            "password": "CorrectPass123!"
        }
        client.post("/api/auth/register", json=user_data)

        # Attempt multiple failed logins
        for i in range(6):  # Exceed the limit
            login_data = {
                "email": "bruteforce@example.com",
                "password": f"WrongPass{i}"
            }
            response = client.post("/api/auth/login", json=login_data)

            if i < 5:
                assert response.status_code == 401
            else:
                # Account should be locked after 5 attempts
                assert response.status_code == 401
                data = response.json()
                assert data["error"]["code"] == "ACCOUNT_LOCKED"

    def test_jwt_token_expiration(self, client):
        """Test JWT token expiration handling"""
        # This would require mocking time or using expired tokens
        # Implementation depends on your testing framework
        pass

    def test_token_blacklisting(self, client):
        """Test token blacklisting after logout"""
        # Register and get token
        user_data = {
            "email": "blacklist@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        tokens = response.json()["tokens"]

        # Use token successfully
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/api/auth/profile", headers=headers)
        assert response.status_code == 200

        # Logout (should blacklist token)
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200

        # Try to use same token (should fail)
        response = client.get("/api/auth/profile", headers=headers)
        assert response.status_code == 401
```

### 4. Performance Tests

#### Load Testing with Locust

```python
from locust import HttpUser, task, between

class AuthenticationLoadTest(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup for each user"""
        self.user_counter = 0

    @task(3)
    def register_user(self):
        """Test user registration under load"""
        self.user_counter += 1
        user_data = {
            "email": f"loadtest{self.user_counter}@example.com",
            "password": "LoadTest123!",
            "first_name": "Load",
            "last_name": "Test"
        }

        with self.client.post("/api/auth/register", json=user_data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                # Store token for other tests
                self.token = response.json()["tokens"]["access_token"]
            else:
                response.failure(f"Registration failed: {response.status_code}")

    @task(5)
    def login_user(self):
        """Test user login under load"""
        login_data = {
            "email": "existing@example.com",
            "password": "ExistingPass123!"
        }

        with self.client.post("/api/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    @task(2)
    def get_profile(self):
        """Test profile access under load"""
        if hasattr(self, 'token'):
            headers = {"Authorization": f"Bearer {self.token}"}
            with self.client.get("/api/auth/profile", headers=headers, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Profile access failed: {response.status_code}")
```

#### Rate Limiting Tests

```python
class TestRateLimiting:

    def test_registration_rate_limit(self, client):
        """Test registration rate limiting"""
        # Attempt to register many users quickly
        for i in range(10):  # Exceed the limit of 5 per hour
            user_data = {
                "email": f"ratelimit{i}@example.com",
                "password": "RateLimit123!"
            }
            response = client.post("/api/auth/register", json=user_data)

            if i < 5:
                assert response.status_code == 201
            else:
                assert response.status_code == 429
                data = response.json()
                assert data["error"]["code"] == "TOO_MANY_REQUESTS"

    def test_login_rate_limit(self, client):
        """Test login rate limiting"""
        login_data = {
            "email": "existing@example.com",
            "password": "WrongPassword"
        }

        # Attempt multiple logins quickly
        for i in range(15):  # Exceed the limit of 10 per hour
            response = client.post("/api/auth/login", json=login_data)

            if i < 10:
                assert response.status_code == 401  # Invalid credentials
            else:
                assert response.status_code == 429  # Rate limited
```

### 5. API Contract Tests

#### OpenAPI Specification Validation

```python
import yaml
from openapi_spec_validator import validate_spec

def test_openapi_specification():
    """Test that OpenAPI specification is valid"""
    with open('api-specification/auth-api-openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)

    # Validate against OpenAPI 3.1 specification
    validate_spec(spec)

def test_response_schemas(client):
    """Test that API responses match OpenAPI schemas"""
    # Register user
    user_data = {
        "email": "schema@example.com",
        "password": "SchemaTest123!"
    }
    response = client.post("/api/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()

    # Validate response structure
    required_fields = ["message", "user", "tokens"]
    for field in required_fields:
        assert field in data

    # Validate user object structure
    user_fields = ["id", "email", "role", "created_at", "email_verified"]
    for field in user_fields:
        assert field in data["user"]

    # Validate tokens object structure
    token_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
    for field in token_fields:
        assert field in data["tokens"]
```

## 🧪 Test Execution Strategy

### 1. Test Pyramid

```
    ┌─────────────────┐
    │   E2E Tests     │  ← Few, high-level user journeys
    │   (Expensive)   │
    ├─────────────────┤
    │ Integration     │  ← API endpoints, database interactions
    │ Tests (Medium)  │
    ├─────────────────┤
    │  Unit Tests     │  ← Many, fast, isolated components
    │ (Cheap & Fast)  │
    └─────────────────┘
```

### 2. Test Environment Setup

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  api-test:
    build: .
    environment:
      - DATABASE_URL=postgresql://test:test@postgres-test:5432/perfect21_test
      - REDIS_URL=redis://redis-test:6379
      - JWT_SECRET_KEY=test-secret-key-for-testing-only
    depends_on:
      - postgres-test
      - redis-test

  postgres-test:
    image: postgres:15
    environment:
      - POSTGRES_DB=perfect21_test
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=test

  redis-test:
    image: redis:7-alpine
```

### 3. Continuous Integration Pipeline

```yaml
# .github/workflows/test.yml
name: Test Authentication API

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: perfect21_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio httpx

    - name: Run unit tests
      run: pytest tests/unit/ -v

    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/perfect21_test
        REDIS_URL: redis://localhost:6379

    - name: Run security tests
      run: pytest tests/security/ -v

    - name: Run load tests
      run: locust -f tests/load/auth_load_test.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000
```

### 4. Test Data Management

```python
# conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/perfect21_test")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
def override_get_db(db_session):
    """Override database dependency"""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
```

## 📊 Test Reporting

### 1. Coverage Reports

```bash
# Generate coverage report
pytest --cov=auth --cov-report=html --cov-report=term-missing

# Coverage configuration in .coveragerc
[run]
source = auth
omit =
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### 2. Performance Metrics

```python
# Performance test reporting
class PerformanceReporter:
    def __init__(self):
        self.metrics = []

    def record_response_time(self, endpoint: str, response_time: float):
        self.metrics.append({
            'endpoint': endpoint,
            'response_time': response_time,
            'timestamp': datetime.utcnow()
        })

    def generate_report(self):
        """Generate performance report"""
        df = pd.DataFrame(self.metrics)
        report = {
            'avg_response_time': df['response_time'].mean(),
            'p95_response_time': df['response_time'].quantile(0.95),
            'p99_response_time': df['response_time'].quantile(0.99),
            'slowest_endpoints': df.groupby('endpoint')['response_time'].mean().sort_values(ascending=False)
        }
        return report
```

This comprehensive testing strategy ensures the authentication API is secure, reliable, and performant under various conditions.