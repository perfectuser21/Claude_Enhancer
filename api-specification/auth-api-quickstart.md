# Claude Enhancer Authentication API Quick Start Guide

## 🚀 Quick Start

This guide helps you get started with the Claude Enhancer Authentication API in 5 minutes.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git

## 🔧 Setup

### 1. Clone and Install

```bash
git clone https://github.com/perfect21/auth-api.git
cd auth-api
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters
DATABASE_URL=postgresql://user:password@localhost:5432/perfect21
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 3. Database Setup

```bash
# Create database
createdb perfect21

# Run migrations
alembic upgrade head
```

### 4. Start the API

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🧪 Test the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "database": true,
    "redis": true,
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### 2. User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

Expected response:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "created_at": "2025-01-15T10:30:00Z",
    "email_verified": false
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### 3. User Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### 4. Access Protected Endpoint

```bash
# Replace TOKEN with your access token
curl -X GET http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer TOKEN"
```

### 5. Refresh Token

```bash
# Replace REFRESH_TOKEN with your refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "REFRESH_TOKEN"
  }'
```

### 6. Logout

```bash
# Replace TOKEN with your access token
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer TOKEN"
```

## 🐳 Docker Setup

### Quick Start with Docker

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/perfect21
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=your-docker-secret-key
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=perfect21
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 🌐 Frontend Integration Examples

### JavaScript/TypeScript

```typescript
// auth-client.ts
class AuthClient {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async register(userData: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
  }) {
    const response = await fetch(`${this.baseURL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error(`Registration failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.accessToken = data.tokens.access_token;

    // Store tokens securely
    localStorage.setItem('access_token', data.tokens.access_token);
    localStorage.setItem('refresh_token', data.tokens.refresh_token);

    return data;
  }

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.accessToken = data.tokens.access_token;

    localStorage.setItem('access_token', data.tokens.access_token);
    localStorage.setItem('refresh_token', data.tokens.refresh_token);

    return data;
  }

  async getProfile() {
    const token = this.accessToken || localStorage.getItem('access_token');

    if (!token) {
      throw new Error('No access token available');
    }

    const response = await fetch(`${this.baseURL}/api/auth/profile`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Try to refresh token
        await this.refreshToken();
        return this.getProfile();
      }
      throw new Error(`Failed to get profile: ${response.statusText}`);
    }

    return response.json();
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh failed, redirect to login
      this.logout();
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    localStorage.setItem('access_token', data.access_token);

    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }

    return data;
  }

  async logout() {
    const token = this.accessToken || localStorage.getItem('access_token');

    if (token) {
      try {
        await fetch(`${this.baseURL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout request failed:', error);
      }
    }

    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.accessToken = null;
  }
}

// Usage example
const authClient = new AuthClient();

// Register
try {
  const result = await authClient.register({
    email: 'user@example.com',
    password: 'SecurePass123!',
    first_name: 'John',
    last_name: 'Doe'
  });
  console.log('Registration successful:', result);
} catch (error) {
  console.error('Registration failed:', error);
}

// Login
try {
  const result = await authClient.login('user@example.com', 'SecurePass123!');
  console.log('Login successful:', result);
} catch (error) {
  console.error('Login failed:', error);
}
```

### React Hook Example

```tsx
// useAuth.ts
import { useState, useEffect, createContext, useContext } from 'react';
import { AuthClient } from './auth-client';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const authClient = new AuthClient();

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('access_token');
    if (token) {
      authClient.getProfile()
        .then(setUser)
        .catch(() => {
          // Token invalid, clear storage
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const result = await authClient.login(email, password);
    setUser(result.user);
  };

  const register = async (userData: any) => {
    const result = await authClient.register(userData);
    setUser(result.user);
  };

  const logout = () => {
    authClient.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (undefined === context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component Example
export const LoginForm: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
    } catch (error) {
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email:</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      {error && <div className="error">{error}</div>}
      <button type="submit">Login</button>
    </form>
  );
};
```

### Python Client Example

```python
# auth_client.py
import requests
from typing import Optional, Dict, Any

class AuthAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def register(self, email: str, password: str, **kwargs) -> Dict[str, Any]:
        """Register a new user"""
        data = {
            "email": email,
            "password": password,
            **kwargs
        }

        response = requests.post(f"{self.base_url}/api/auth/register", json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["tokens"]["access_token"]
        self.refresh_token = result["tokens"]["refresh_token"]

        return result

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        data = {"email": email, "password": password}

        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["tokens"]["access_token"]
        self.refresh_token = result["tokens"]["refresh_token"]

        return result

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        if not self.access_token:
            raise ValueError("No access token available")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/api/auth/profile", headers=headers)

        if response.status_code == 401:
            # Try to refresh token
            self.refresh_access_token()
            return self.get_profile()

        response.raise_for_status()
        return response.json()

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = {"refresh_token": self.refresh_token}
        response = requests.post(f"{self.base_url}/api/auth/refresh", json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result["access_token"]

        if "refresh_token" in result:
            self.refresh_token = result["refresh_token"]

        return result

    def logout(self) -> None:
        """Logout user"""
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            try:
                requests.post(f"{self.base_url}/api/auth/logout", headers=headers)
            except requests.RequestException:
                pass  # Ignore logout errors

        self.access_token = None
        self.refresh_token = None

# Usage example
if __name__ == "__main__":
    client = AuthAPIClient()

    # Register
    try:
        result = client.register(
            email="python@example.com",
            password="PythonPass123!",
            first_name="Python",
            last_name="Client"
        )
        print("Registration successful:", result["user"]["email"])
    except requests.HTTPError as e:
        print("Registration failed:", e.response.json())

    # Get profile
    try:
        profile = client.get_profile()
        print("Profile:", profile["email"])
    except Exception as e:
        print("Failed to get profile:", e)

    # Logout
    client.logout()
    print("Logged out successfully")
```

## 🔍 Common Issues and Solutions

### 1. Database Connection Errors

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
psql "postgresql://user:password@localhost:5432/perfect21"
```

### 2. Redis Connection Errors

```bash
# Check if Redis is running
redis-cli ping

# Check Redis configuration
redis-cli config get "*"
```

### 3. Token Validation Issues

- Ensure JWT_SECRET_KEY is set correctly
- Check token expiration times
- Verify token format (Bearer token)

### 4. CORS Issues

```python
# Update CORS settings in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 Next Steps

1. **Security Hardening**: Review security configuration
2. **Monitoring**: Set up logging and monitoring
3. **Testing**: Run the test suite
4. **Deployment**: Deploy to production environment
5. **Documentation**: Explore the full API documentation

## 🔗 Resources

- [OpenAPI Specification](./auth-api-openapi.yaml)
- [Implementation Guide](./auth-api-implementation-guide.md)
- [Testing Strategy](./auth-api-testing-strategy.md)
- [API Documentation](http://localhost:8000/docs) (when running)

---

🎉 **Congratulations!** You now have a fully functional authentication API running. Start building amazing applications with secure user authentication!