# Perfect21 Authentication System

## Overview

The Perfect21 Authentication System is a comprehensive, enterprise-grade authentication solution built with FastAPI and React. It provides secure user authentication, authorization, multi-factor authentication (MFA), and session management with industry-standard security practices.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Redis 6.0+
- PostgreSQL 13+
- RabbitMQ (optional, for event messaging)

### Backend Setup

```bash
# Install dependencies
pip install -r backend/auth-service/requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://user:password@localhost/auth_db"
export REDIS_URL="redis://localhost:6379/0"

# Run database migrations
alembic upgrade head

# Start the auth service
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Frontend Setup

```bash
# Install dependencies
cd frontend/auth
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:8080/api" > .env

# Start the development server
npm start
```

### Docker Setup

```bash
# Start all services with Docker Compose
docker-compose up -d

# The auth service will be available at:
# - Backend API: http://localhost:8080
# - Frontend: http://localhost:3000
```

## 🏗️ Architecture

### System Components

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Auth UI]
        API[Auth API Client]
    end

    subgraph "Backend Layer"
        AUTH[Auth Service]
        JWT[JWT Manager]
        MFA[MFA Service]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis Cache)]
        QUEUE[RabbitMQ]
    end

    UI --> API
    API --> AUTH
    AUTH --> JWT
    AUTH --> MFA
    AUTH --> DB
    JWT --> REDIS
    MFA --> REDIS
    AUTH --> QUEUE
```

### Key Features

- **🔐 JWT-based Authentication**: RS256 signed tokens with automatic key rotation
- **👥 User Management**: Registration, email verification, profile management
- **🛡️ Multi-Factor Authentication**: TOTP, SMS, and email-based MFA
- **🚨 Security Features**: Rate limiting, account lockout, audit logging
- **📱 Device Trust**: Device fingerprinting and trusted device management
- **🔄 Session Management**: Active session monitoring and revocation
- **📊 Monitoring**: Comprehensive metrics and health checks

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Application
SECRET_KEY=your-super-secret-key
DEBUG=false
HOST=0.0.0.0
PORT=8080

# Database
DATABASE_URL=postgresql://user:password@localhost/auth_db
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_TTL=900       # 15 minutes
JWT_REFRESH_TOKEN_TTL=604800   # 7 days
JWT_ISSUER=perfect21-auth
JWT_AUDIENCE=perfect21-api

# Security
PASSWORD_MIN_LENGTH=12
ACCOUNT_LOCKOUT_ATTEMPTS=5
RATE_LIMIT_LOGIN_REQUESTS=5

# Email (optional)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# MFA (optional)
MFA_TOTP_ISSUER=Perfect21
SMS_PROVIDER=twilio
SMS_API_KEY=your-twilio-key
```

## 📚 API Endpoints

### Authentication

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh access token

### User Management

- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/verify-email/{token}` - Verify email
- `POST /api/v1/auth/password/reset` - Request password reset
- `POST /api/v1/auth/password/change` - Change password

### Multi-Factor Authentication

- `POST /api/v1/auth/mfa/setup` - Setup MFA
- `POST /api/v1/auth/mfa/verify` - Verify MFA code
- `POST /api/v1/auth/mfa/disable` - Disable MFA

## 🔍 Usage Examples

### Basic Login

```python
import requests

# Login request
response = requests.post('http://localhost:8080/api/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'securepassword123'
})

tokens = response.json()
access_token = tokens['access_token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {access_token}'}
user_info = requests.get('http://localhost:8080/api/v1/auth/me', headers=headers)
```

### Frontend Integration

```javascript
import { authAPI } from './services/authAPI';

// Login
const loginUser = async (email, password) => {
  try {
    const response = await authAPI.login({
      email,
      password,
      rememberMe: true
    });

    // Tokens are automatically stored
    console.log('Login successful');
  } catch (error) {
    console.error('Login failed:', error.message);
  }
};
```

## 🛡️ Security Features

### Password Requirements

- Minimum 12 characters
- Must contain uppercase, lowercase, number, and special character
- Password history tracking (prevents reuse of last 5 passwords)
- Bcrypt hashing with salt rounds

### Account Protection

- **Rate Limiting**: 5 login attempts per 5 minutes
- **Account Lockout**: Automatic lockout after 5 failed attempts
- **IP Tracking**: Monitor and log IP addresses
- **Device Fingerprinting**: Track device characteristics

### Token Security

- **Short-lived Access Tokens**: 15-minute expiration
- **Secure Refresh Tokens**: 7-day expiration with rotation
- **Automatic Key Rotation**: RSA keys rotated every 24 hours
- **Token Revocation**: Immediate token invalidation

## 🔧 Development

### Running Tests

```bash
# Backend tests
cd backend/auth-service
pytest tests/ -v

# Frontend tests
cd frontend/auth
npm test
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Monitoring

The authentication service provides several monitoring endpoints:

- `/health` - Service health check
- `/metrics` - Prometheus metrics
- `/api/v1/auth/status` - Authentication service status

## 📖 Additional Documentation

- [API Guide](./API_GUIDE.md) - Detailed API documentation
- [Integration Guide](./INTEGRATION_GUIDE.md) - How to integrate with your application
- [Security Guide](./SECURITY_GUIDE.md) - Security best practices
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:

- Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
- Review [API Documentation](./API_GUIDE.md)
- Open an issue on GitHub
- Contact the development team

---

**Version**: 2.0.0
**Last Updated**: 2025-01-24
**Maintainer**: Perfect21 Development Team