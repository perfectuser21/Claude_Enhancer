# Perfect21 Authentication API Implementation Guide

## 🔐 Overview

This guide provides implementation details for the Perfect21 Authentication API, designed with enterprise-grade security and scalability in mind.

## 🏗️ Architecture Design

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Rate Limiting│  │CORS Handler │  │   Logging   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Auth Service Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  JWT Handler│  │Password Hash│  │Session Mgmt │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Data Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ User Store  │  │Token Store  │  │ Audit Log   │        │
│  │(PostgreSQL) │  │  (Redis)    │  │(PostgreSQL) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔒 Security Implementation

### 1. Password Security

```python
# Password hashing with bcrypt
import bcrypt
from typing import str

class PasswordManager:
    COST_FACTOR = 12  # Recommended for 2025

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=PasswordManager.COST_FACTOR)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def validate_password_strength(password: str) -> list[str]:
        """Validate password meets security requirements"""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain at least one special character")

        return errors
```

### 2. JWT Token Management

```python
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

class TokenManager:
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=7)

    def generate_tokens(self, user_id: str, role: str) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        now = datetime.utcnow()
        jti_access = str(uuid.uuid4())
        jti_refresh = str(uuid.uuid4())

        # Access token payload
        access_payload = {
            'sub': user_id,
            'role': role,
            'type': 'access',
            'iat': now,
            'exp': now + self.access_token_expire,
            'jti': jti_access
        }

        # Refresh token payload
        refresh_payload = {
            'sub': user_id,
            'type': 'refresh',
            'iat': now,
            'exp': now + self.refresh_token_expire,
            'jti': jti_refresh
        }

        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_expire.total_seconds())
        }

    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get('type') != token_type:
                return None

            # Check if token is blacklisted (implement with Redis)
            if self.is_token_blacklisted(payload.get('jti')):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def blacklist_token(self, jti: str, exp: datetime):
        """Add token to blacklist"""
        # Implement with Redis
        # redis_client.setex(f"blacklist:{jti}", exp - datetime.utcnow(), "1")
        pass
```

### 3. Rate Limiting

```python
import redis
from typing import Tuple, Optional

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_rate_limit(self, key: str, limit: int, window: int) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit
        Returns: (is_allowed, rate_limit_info)
        """
        pipe = self.redis.pipeline()
        now = time.time()
        window_start = now - window

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(uuid.uuid4()): now})

        # Set expiration
        pipe.expire(key, window)

        results = pipe.execute()
        current_requests = results[1]

        if current_requests >= limit:
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset': int(now + window),
                'retry_after': window
            }

        return True, {
            'limit': limit,
            'remaining': limit - current_requests - 1,
            'reset': int(now + window)
        }

# Rate limit configurations
RATE_LIMITS = {
    'auth.register': {'limit': 5, 'window': 3600},  # 5 per hour
    'auth.login': {'limit': 10, 'window': 3600},    # 10 per hour
    'auth.refresh': {'limit': 20, 'window': 3600},  # 20 per hour
}
```

### 4. Account Security

```python
from datetime import datetime, timedelta
import redis

class AccountSecurity:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)

    def record_failed_login(self, email: str) -> dict:
        """Record failed login attempt"""
        key = f"failed_login:{email}"
        attempts = self.redis.incr(key)

        if attempts == 1:
            # Set expiration on first attempt
            self.redis.expire(key, int(self.lockout_duration.total_seconds()))

        if attempts >= self.max_failed_attempts:
            # Account is locked
            lock_key = f"account_locked:{email}"
            self.redis.setex(
                lock_key,
                int(self.lockout_duration.total_seconds()),
                str(datetime.utcnow().isoformat())
            )

            return {
                'locked': True,
                'attempts': attempts,
                'unlock_time': datetime.utcnow() + self.lockout_duration
            }

        return {
            'locked': False,
            'attempts': attempts,
            'remaining_attempts': self.max_failed_attempts - attempts
        }

    def is_account_locked(self, email: str) -> bool:
        """Check if account is locked"""
        return self.redis.exists(f"account_locked:{email}")

    def clear_failed_attempts(self, email: str):
        """Clear failed login attempts after successful login"""
        self.redis.delete(f"failed_login:{email}")
        self.redis.delete(f"account_locked:{email}")
```

## 📊 Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone_number VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'moderator')),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### User Sessions Table

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jti VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('access', 'refresh')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_jti ON user_sessions(jti);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
```

### Audit Log Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## 🔧 Implementation Examples

### 1. Registration Endpoint

```python
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr, validator
import re

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        errors = PasswordManager.validate_password_strength(v)
        if errors:
            raise ValueError(', '.join(errors))
        return v

    @validator('phone_number')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be in E.164 format')
        return v

@app.post("/api/auth/register")
async def register_user(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Rate limiting
    client_ip = req.client.host
    rate_key = f"register:{client_ip}"
    allowed, rate_info = rate_limiter.check_rate_limit(
        rate_key,
        RATE_LIMITS['auth.register']['limit'],
        RATE_LIMITS['auth.register']['window']
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "TOO_MANY_REQUESTS",
                    "message": "Rate limit exceeded",
                    "retry_after": rate_info['retry_after']
                }
            }
        )

    # Check if user exists
    existing_user = await db.execute(
        select(User).where(User.email == request.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "CONFLICT",
                    "message": "Email already exists"
                }
            }
        )

    # Create user
    password_hash = PasswordManager.hash_password(request.password)
    user = User(
        email=request.email,
        password_hash=password_hash,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    tokens = token_manager.generate_tokens(str(user.id), user.role)

    # Log audit event
    await log_audit_event(
        user_id=user.id,
        action="USER_REGISTERED",
        ip_address=client_ip,
        user_agent=req.headers.get('user-agent')
    )

    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "email_verified": user.email_verified
        },
        "tokens": tokens
    }
```

### 2. Login Endpoint

```python
@app.post("/api/auth/login")
async def login_user(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    client_ip = req.client.host

    # Check account lockout
    if account_security.is_account_locked(request.email):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "ACCOUNT_LOCKED",
                    "message": "Account temporarily locked"
                }
            }
        )

    # Rate limiting
    rate_key = f"login:{client_ip}"
    allowed, rate_info = rate_limiter.check_rate_limit(
        rate_key,
        RATE_LIMITS['auth.login']['limit'],
        RATE_LIMITS['auth.login']['window']
    )

    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not PasswordManager.verify_password(request.password, user.password_hash):
        # Record failed attempt
        account_security.record_failed_login(request.email)

        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password"
                }
            }
        )

    # Clear failed attempts
    account_security.clear_failed_attempts(request.email)

    # Update login info
    user.last_login = datetime.utcnow()
    user.login_count += 1
    await db.commit()

    # Generate tokens
    tokens = token_manager.generate_tokens(str(user.id), user.role)

    # Log audit event
    await log_audit_event(
        user_id=user.id,
        action="USER_LOGIN",
        ip_address=client_ip,
        user_agent=req.headers.get('user-agent')
    )

    return {
        "message": "Login successful",
        "user": user.to_dict(),
        "tokens": tokens
    }
```

### 3. JWT Middleware

```python
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract user from JWT token"""

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}
        )

    # Verify token
    payload = token_manager.verify_token(credentials.credentials, 'access')
    if not payload:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}}
        )

    # Get user
    user_id = payload.get('sub')
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "User not found"}}
        )

    return user
```

## 🛡️ Security Best Practices

### 1. Environment Configuration

```bash
# .env file
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
BCRYPT_ROUNDS=12
DATABASE_URL=postgresql://user:pass@localhost/perfect21
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 2. Security Headers

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### 3. Input Validation and Sanitization

```python
import bleach
from pydantic import validator

class UserInput(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator('first_name', 'last_name')
    def sanitize_name(cls, v):
        if v:
            # Remove any HTML tags and scripts
            return bleach.clean(v.strip(), tags=[], strip=True)
        return v
```

## 📈 Monitoring and Logging

### 1. Structured Logging

```python
import structlog
import json

logger = structlog.get_logger()

async def log_audit_event(
    user_id: Optional[str],
    action: str,
    resource: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log audit event"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Log to database
    db.add(audit_log)
    await db.commit()

    # Log to structured logger
    logger.info(
        "audit_event",
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        timestamp=datetime.utcnow().isoformat()
    )
```

### 2. Health Checks

```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    checks = {
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "timestamp": datetime.utcnow().isoformat()
    }

    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "checks": checks}
        )
```

## 🚀 Deployment Considerations

### 1. Environment Variables

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8000:8000"
```

### 2. Load Balancing

```nginx
# nginx.conf
upstream api_servers {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://api_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

This implementation guide provides a comprehensive foundation for building a secure, scalable authentication API that follows industry best practices for security, performance, and maintainability.