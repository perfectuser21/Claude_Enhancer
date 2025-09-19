# Perfect21 用户登录API - 接口文档与最佳实践

## 🎯 概述

Perfect21用户登录API是一个企业级身份认证系统，基于Perfect21架构设计，提供完整的用户认证、授权和会话管理功能。该API遵循RESTful设计原则，采用JWT令牌认证机制，具备完善的安全防护和审计功能。

## 🏗️ 架构设计

### 核心组件
```
┌─────────────────────────────────────────────────────────────┐
│                  Perfect21 Auth API                        │
├─────────────────────────────────────────────────────────────┤
│  🔐 Authentication Layer (身份认证层)                        │
│  ├── JWT Token Management (JWT令牌管理)                     │
│  ├── Password Hashing (密码哈希)                            │
│  ├── Account Security (账户安全)                            │
│  └── Session Management (会话管理)                          │
├─────────────────────────────────────────────────────────────┤
│  🛡️ Security Layer (安全防护层)                             │
│  ├── Rate Limiting (限流保护)                               │
│  ├── Account Lockout (账户锁定)                            │
│  ├── IP Filtering (IP过滤)                                 │
│  └── Audit Logging (审计日志)                              │
├─────────────────────────────────────────────────────────────┤
│  📊 Data Layer (数据存储层)                                 │
│  ├── PostgreSQL/MySQL (用户数据)                           │
│  ├── Redis Cache (会话缓存)                                │
│  └── Audit Database (审计数据)                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈
- **框架**: Flask (轻量级Web框架)
- **认证**: JWT (JSON Web Tokens)
- **密码**: bcrypt (密码哈希算法)
- **数据库**: SQLAlchemy ORM (支持PostgreSQL/MySQL/SQLite)
- **缓存**: Redis (会话存储和限流)
- **验证**: Pydantic (数据验证)
- **监控**: 集成Perfect21日志系统

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入Perfect21项目目录
cd /path/to/Perfect21

# 安装API依赖
pip install flask jwt bcrypt sqlalchemy redis pydantic flask-cors

# 或使用requirements.txt
pip install -r features/auth_api/requirements.txt
```

### 2. 配置环境

在 `modules/config.py` 中添加认证配置：

```python
# 认证配置
AUTH_CONFIG = {
    'jwt_secret_key': 'your-super-secret-jwt-key-here',
    'jwt_algorithm': 'HS256',
    'access_token_expires': 3600,  # 1小时
    'refresh_token_expires': 604800,  # 7天
    'max_login_attempts': 5,
    'lockout_duration': 900,  # 15分钟
    'require_captcha_after': 3,
    'password_salt_rounds': 12
}

# 数据库配置
DATABASE_CONFIG = {
    'url': 'postgresql://user:password@localhost/perfect21_auth',
    'echo': False
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None
}
```

### 3. 初始化数据库

```python
from features.auth_api.user_login_api import UserLoginAPI

# 创建API实例（自动创建表结构）
api = UserLoginAPI()
print("数据库初始化完成！")
```

### 4. 启动API服务器

```bash
# 直接启动
python3 features/auth_api/user_login_api.py

# 或通过Perfect21 CLI
python3 main/cli.py auth-api start --host 0.0.0.0 --port 8080
```

## 📡 API接口详解

### 1. 用户登录 `POST /api/v1/auth/login`

最核心的身份认证接口，支持用户名/密码登录。

#### 请求示例
```bash
curl -X POST https://api.perfect21.dev/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "User-Agent: Perfect21-Client/1.0" \
  -d '{
    "username": "john_doe",
    "password": "secure_password123",
    "remember_me": false,
    "device_fingerprint": "fp_1234567890abcdef"
  }'
```

#### 成功响应
```json
{
  "success": true,
  "message": "登录成功",
  "user_id": "usr_1234567890abcdef",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user_profile": {
    "user_id": "usr_1234567890abcdef",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "developer",
    "is_active": true,
    "last_login": "2024-01-01T12:00:00Z"
  },
  "permissions": [
    "user:read",
    "user:write",
    "project:*",
    "code:*"
  ],
  "session_id": "sess_abcdef1234567890"
}
```

#### 安全特性
- **密码保护**: bcrypt哈希算法，12轮加盐
- **账户锁定**: 5次失败后锁定15分钟
- **IP限流**: 5分钟内最多10次尝试
- **验证码**: 3次失败后需要验证码
- **审计日志**: 记录所有登录尝试

### 2. 令牌验证 `POST /api/v1/auth/validate`

验证JWT访问令牌的有效性，用于API网关和微服务间的认证。

#### 请求示例
```bash
curl -X POST https://api.perfect21.dev/v1/auth/validate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### 响应示例
```json
{
  "valid": true,
  "user_id": "usr_1234567890abcdef",
  "role": "developer",
  "expires_at": "2024-01-01T13:00:00Z",
  "permissions": [
    "user:read",
    "user:write",
    "project:*"
  ]
}
```

### 3. 令牌刷新 `POST /api/v1/auth/refresh`

使用刷新令牌获取新的访问令牌，实现无感知的令牌续期。

#### 请求示例
```bash
curl -X POST https://api.perfect21.dev/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### 安全机制
- **一次性使用**: 刷新令牌用后即废
- **令牌轮换**: 返回新的访问令牌和刷新令牌
- **会话绑定**: 验证令牌与会话的绑定关系

### 4. 用户登出 `POST /api/v1/auth/logout`

安全终止用户会话，清理服务端状态。

#### 请求示例
```bash
curl -X POST https://api.perfect21.dev/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 5. 用户档案 `GET /api/v1/auth/profile`

获取当前认证用户的详细档案信息。

#### 请求示例
```bash
curl -X GET https://api.perfect21.dev/v1/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 🔐 安全最佳实践

### 1. 密码安全

```python
# 强密码策略
PASSWORD_POLICY = {
    'min_length': 8,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_symbols': True,
    'prevent_common_passwords': True,
    'prevent_user_info': True
}

# 密码哈希
import bcrypt

def hash_password(password: str) -> str:
    """使用bcrypt哈希密码"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hash: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
```

### 2. JWT令牌安全

```python
import jwt
from datetime import datetime, timedelta

# JWT配置
JWT_CONFIG = {
    'secret_key': 'your-256-bit-secret-key',  # 至少256位
    'algorithm': 'HS256',
    'access_token_exp': 3600,   # 1小时
    'refresh_token_exp': 604800  # 7天
}

# 生成令牌
def generate_tokens(user_id: str, role: str) -> dict:
    """生成访问令牌和刷新令牌"""
    now = datetime.utcnow()

    # 访问令牌
    access_payload = {
        'user_id': user_id,
        'role': role,
        'type': 'access',
        'iat': now,
        'exp': now + timedelta(seconds=JWT_CONFIG['access_token_exp'])
    }

    # 刷新令牌
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'iat': now,
        'exp': now + timedelta(seconds=JWT_CONFIG['refresh_token_exp'])
    }

    return {
        'access_token': jwt.encode(access_payload, JWT_CONFIG['secret_key'], algorithm=JWT_CONFIG['algorithm']),
        'refresh_token': jwt.encode(refresh_payload, JWT_CONFIG['secret_key'], algorithm=JWT_CONFIG['algorithm'])
    }
```

### 3. 账户安全保护

```python
from datetime import datetime, timedelta

class AccountSecurity:
    """账户安全保护类"""

    def __init__(self, max_attempts=5, lockout_duration=900):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration

    def check_lockout(self, user) -> bool:
        """检查账户是否被锁定"""
        if not user.is_locked:
            return False

        if user.lock_until and datetime.utcnow() > user.lock_until:
            # 锁定时间已过，自动解锁
            user.is_locked = False
            user.lock_until = None
            user.login_attempts = 0
            return False

        return True

    def handle_failed_login(self, user):
        """处理登录失败"""
        user.login_attempts += 1

        if user.login_attempts >= self.max_attempts:
            user.is_locked = True
            user.lock_until = datetime.utcnow() + timedelta(seconds=self.lockout_duration)

    def handle_successful_login(self, user):
        """处理登录成功"""
        user.login_attempts = 0
        user.is_locked = False
        user.lock_until = None
        user.last_login = datetime.utcnow()
```

### 4. IP限流保护

```python
import redis
from typing import Optional

class RateLimiter:
    """IP限流保护类"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def is_allowed(self, ip_address: str, window_seconds: int = 300, max_requests: int = 10) -> bool:
        """检查IP是否允许请求"""
        if not self.redis:
            return True

        key = f"rate_limit:{ip_address}"

        try:
            current_requests = self.redis.incr(key)
            if current_requests == 1:
                self.redis.expire(key, window_seconds)

            return current_requests <= max_requests
        except Exception:
            # Redis故障时允许请求
            return True

    def get_remaining_attempts(self, ip_address: str, max_requests: int = 10) -> int:
        """获取剩余尝试次数"""
        if not self.redis:
            return max_requests

        key = f"rate_limit:{ip_address}"
        current_requests = self.redis.get(key) or 0
        return max(0, max_requests - int(current_requests))
```

## 📊 监控和审计

### 1. 审计日志

```python
import json
from datetime import datetime
from enum import Enum

class AuditEventType(Enum):
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILED = "login.failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token.refresh"
    ACCOUNT_LOCKED = "account.locked"
    PASSWORD_CHANGED = "password.changed"

class AuditLogger:
    """审计日志记录器"""

    def log_event(self, event_type: AuditEventType, user_id: str = None,
                  ip_address: str = None, details: dict = None):
        """记录审计事件"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type.value,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': details.get('user_agent') if details else None,
            'details': details or {}
        }

        # 记录到数据库
        self._save_to_database(audit_entry)

        # 记录到日志文件
        self._save_to_log_file(audit_entry)

        # 发送告警（如果需要）
        self._send_alert_if_needed(audit_entry)

    def _save_to_database(self, entry: dict):
        """保存到数据库"""
        # 实现数据库保存逻辑
        pass

    def _save_to_log_file(self, entry: dict):
        """保存到日志文件"""
        import logging
        logger = logging.getLogger('audit')
        logger.info(json.dumps(entry, ensure_ascii=False))

    def _send_alert_if_needed(self, entry: dict):
        """发送告警"""
        critical_events = [
            AuditEventType.ACCOUNT_LOCKED.value,
            AuditEventType.LOGIN_FAILED.value
        ]

        if entry['event_type'] in critical_events:
            # 发送告警通知
            self._send_security_alert(entry)
```

### 2. 性能监控

```python
import time
from functools import wraps
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控类"""

    def __init__(self):
        self.metrics = {}

    def time_function(self, func_name: str):
        """函数执行时间装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self._record_success(func_name, time.time() - start_time)
                    return result
                except Exception as e:
                    self._record_error(func_name, time.time() - start_time, str(e))
                    raise
            return wrapper
        return decorator

    def _record_success(self, func_name: str, duration: float):
        """记录成功执行"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                'total_calls': 0,
                'success_calls': 0,
                'error_calls': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'min_duration': float('inf')
            }

        metric = self.metrics[func_name]
        metric['total_calls'] += 1
        metric['success_calls'] += 1
        metric['total_duration'] += duration
        metric['avg_duration'] = metric['total_duration'] / metric['total_calls']
        metric['max_duration'] = max(metric['max_duration'], duration)
        metric['min_duration'] = min(metric['min_duration'], duration)

    def _record_error(self, func_name: str, duration: float, error: str):
        """记录错误执行"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                'total_calls': 0,
                'success_calls': 0,
                'error_calls': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'min_duration': float('inf'),
                'recent_errors': []
            }

        metric = self.metrics[func_name]
        metric['total_calls'] += 1
        metric['error_calls'] += 1
        metric['total_duration'] += duration
        metric['avg_duration'] = metric['total_duration'] / metric['total_calls']

        # 记录最近的错误
        if 'recent_errors' not in metric:
            metric['recent_errors'] = []
        metric['recent_errors'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'error': error,
            'duration': duration
        })
        # 只保留最近10个错误
        metric['recent_errors'] = metric['recent_errors'][-10:]

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
```

## 🔧 集成指南

### 1. 与Perfect21主系统集成

```python
# 在 features/auth_api/capability.py 中定义能力
from features.capability_discovery.capability import CapabilityDefinition

def register_auth_api_capability():
    """注册认证API能力"""
    return CapabilityDefinition(
        name="auth_api",
        description="企业级用户认证API",
        version="1.0.0",
        category="security",
        endpoints=[
            "/api/v1/auth/login",
            "/api/v1/auth/validate",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v1/auth/profile"
        ],
        dependencies=["flask", "jwt", "bcrypt", "sqlalchemy", "redis"],
        config_required=["jwt_secret_key", "database_url", "redis_config"],
        health_check_endpoint="/api/v1/auth/health"
    )
```

### 2. CLI命令集成

```python
# 在 main/cli.py 中添加auth-api命令
def handle_auth_api(args):
    """处理认证API命令"""
    if args.action == 'start':
        from features.auth_api.user_login_api import UserLoginAPI, create_flask_app

        api = UserLoginAPI()
        app = create_flask_app(api)

        host = args.host or '0.0.0.0'
        port = args.port or 8080

        print(f"🚀 Perfect21认证API启动: http://{host}:{port}")
        app.run(host=host, port=port, debug=args.debug)

    elif args.action == 'status':
        # 检查API服务状态
        print("📊 Perfect21认证API状态检查...")
        # 实现状态检查逻辑

    elif args.action == 'test':
        # 运行API测试
        from features.auth_api.test_suite import run_auth_api_tests
        run_auth_api_tests()

# 添加子命令解析器
auth_api_parser = subparsers.add_parser('auth-api', help='认证API管理')
auth_api_parser.add_argument('action', choices=['start', 'stop', 'status', 'test'])
auth_api_parser.add_argument('--host', help='服务器主机地址')
auth_api_parser.add_argument('--port', type=int, help='服务器端口')
auth_api_parser.add_argument('--debug', action='store_true', help='调试模式')
```

### 3. 前端集成示例

```javascript
// JavaScript客户端集成示例
class Perfect21AuthClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    async login(username, password, rememberMe = false) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                remember_me: rememberMe,
                device_fingerprint: this.getDeviceFingerprint()
            })
        });

        const data = await response.json();

        if (data.success) {
            this.accessToken = data.access_token;
            this.refreshToken = data.refresh_token;

            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', this.refreshToken);
            localStorage.setItem('user_profile', JSON.stringify(data.user_profile));

            return { success: true, user: data.user_profile };
        } else {
            return { success: false, message: data.message };
        }
    }

    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.accessToken) {
            throw new Error('未登录');
        }

        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // 令牌过期，尝试刷新
            const refreshSuccess = await this.refreshAccessToken();
            if (refreshSuccess) {
                // 重新发送请求
                return this.makeAuthenticatedRequest(url, options);
            } else {
                // 刷新失败，跳转到登录页
                this.logout();
                window.location.href = '/login';
                return null;
            }
        }

        return response;
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });

            const data = await response.json();

            if (data.success) {
                this.accessToken = data.access_token;
                this.refreshToken = data.refresh_token;

                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('refresh_token', this.refreshToken);

                return true;
            }
        } catch (error) {
            console.error('刷新令牌失败:', error);
        }

        return false;
    }

    async logout() {
        if (this.accessToken) {
            try {
                await fetch(`${this.baseURL}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`
                    }
                });
            } catch (error) {
                console.error('登出请求失败:', error);
            }
        }

        // 清理本地存储
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_profile');

        this.accessToken = null;
        this.refreshToken = null;
    }

    getDeviceFingerprint() {
        // 简单的设备指纹生成
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);

        return btoa(JSON.stringify({
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screen: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            canvas: canvas.toDataURL()
        }));
    }
}

// 使用示例
const authClient = new Perfect21AuthClient('https://api.perfect21.dev/v1');

// 登录
authClient.login('john_doe', 'password123').then(result => {
    if (result.success) {
        console.log('登录成功:', result.user);
    } else {
        console.error('登录失败:', result.message);
    }
});
```

## 🧪 测试指南

### 1. 单元测试

```python
# features/auth_api/tests/test_user_login_api.py
import unittest
from unittest.mock import patch, MagicMock
from features.auth_api.user_login_api import UserLoginAPI, LoginRequest

class TestUserLoginAPI(unittest.TestCase):

    def setUp(self):
        self.api = UserLoginAPI()

    @patch('features.auth_api.user_login_api.bcrypt.checkpw')
    def test_login_success(self, mock_checkpw):
        """测试登录成功"""
        mock_checkpw.return_value = True

        # 模拟数据库查询
        with patch.object(self.api, 'db_session_maker') as mock_session:
            mock_user = MagicMock()
            mock_user.id = 'test_user_id'
            mock_user.username = 'testuser'
            mock_user.email = 'test@example.com'
            mock_user.role = 'user'
            mock_user.is_active = True
            mock_user.is_locked = False
            mock_user.login_attempts = 0

            mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_user

            # 执行登录
            request = LoginRequest(username='testuser', password='password123')
            result = self.api.login(request)

            # 验证结果
            self.assertTrue(result.success)
            self.assertEqual(result.user_id, 'test_user_id')
            self.assertIsNotNone(result.access_token)

    def test_login_invalid_credentials(self):
        """测试无效凭据"""
        with patch.object(self.api, 'db_session_maker') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = None

            request = LoginRequest(username='nonexistent', password='password123')
            result = self.api.login(request)

            self.assertFalse(result.success)
            self.assertEqual(result.message, '用户名或密码错误')

    def test_account_lockout(self):
        """测试账户锁定"""
        with patch.object(self.api, 'db_session_maker') as mock_session:
            mock_user = MagicMock()
            mock_user.is_locked = True
            mock_user.lock_until = datetime.utcnow() + timedelta(minutes=10)

            mock_session.return_value.__enter__.return_value.query.return_value.filter_by.return_value.first.return_value = mock_user

            request = LoginRequest(username='lockeduser', password='password123')
            result = self.api.login(request)

            self.assertFalse(result.success)
            self.assertIn('锁定', result.message)

if __name__ == '__main__':
    unittest.main()
```

### 2. 集成测试

```python
# features/auth_api/tests/test_integration.py
import requests
import pytest
from datetime import datetime, timedelta

class TestAuthAPIIntegration:

    def setup_class(self):
        """测试类初始化"""
        self.base_url = 'http://localhost:8080/api/v1'
        self.test_user = {
            'username': 'testuser',
            'password': 'testpass123'
        }

    def test_complete_auth_flow(self):
        """测试完整认证流程"""
        # 1. 登录
        login_response = requests.post(f'{self.base_url}/auth/login', json={
            'username': self.test_user['username'],
            'password': self.test_user['password']
        })

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data['success'] == True

        access_token = login_data['access_token']
        refresh_token = login_data['refresh_token']

        # 2. 验证令牌
        validate_response = requests.post(f'{self.base_url}/auth/validate', json={
            'token': access_token
        })

        assert validate_response.status_code == 200
        validate_data = validate_response.json()
        assert validate_data['valid'] == True

        # 3. 获取用户档案
        profile_response = requests.get(f'{self.base_url}/auth/profile', headers={
            'Authorization': f'Bearer {access_token}'
        })

        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data['success'] == True

        # 4. 刷新令牌
        refresh_response = requests.post(f'{self.base_url}/auth/refresh', json={
            'refresh_token': refresh_token
        })

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert refresh_data['success'] == True

        # 5. 登出
        logout_response = requests.post(f'{self.base_url}/auth/logout', headers={
            'Authorization': f'Bearer {access_token}'
        })

        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert logout_data['success'] == True

    def test_rate_limiting(self):
        """测试限流功能"""
        # 快速发送多个请求
        failed_attempts = 0
        for i in range(15):  # 超过限制的10次
            response = requests.post(f'{self.base_url}/auth/login', json={
                'username': 'nonexistent',
                'password': 'wrongpassword'
            })

            if response.status_code == 429:
                failed_attempts += 1

        assert failed_attempts > 0  # 应该有请求被限流

if __name__ == '__main__':
    pytest.main([__file__])
```

### 3. 性能测试

```python
# features/auth_api/tests/test_performance.py
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestAuthAPIPerformance:

    def test_login_performance(self):
        """测试登录接口性能"""
        base_url = 'http://localhost:8080/api/v1'

        def single_login_test():
            start_time = time.time()
            response = requests.post(f'{base_url}/auth/login', json={
                'username': 'testuser',
                'password': 'testpass123'
            })
            duration = time.time() - start_time
            return {
                'status_code': response.status_code,
                'duration': duration,
                'success': response.json().get('success', False) if response.status_code == 200 else False
            }

        # 并发测试
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(single_login_test) for _ in range(100)]
            for future in as_completed(futures):
                results.append(future.result())

        # 分析结果
        successful_requests = [r for r in results if r['success']]
        durations = [r['duration'] for r in successful_requests]

        print(f"成功请求数: {len(successful_requests)}/100")
        print(f"平均响应时间: {sum(durations)/len(durations):.3f}s")
        print(f"最快响应: {min(durations):.3f}s")
        print(f"最慢响应: {max(durations):.3f}s")

        # 性能断言
        assert len(successful_requests) >= 95  # 95%成功率
        assert sum(durations)/len(durations) < 1.0  # 平均响应时间小于1秒
```

## 📈 生产部署

### 1. 环境配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  perfect21-auth-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=perfect21_auth
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - perfect21-auth-api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 2. Nginx配置

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream perfect21_auth_api {
        server perfect21-auth-api:8080;
    }

    # SSL配置
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    server {
        listen 443 ssl http2;
        server_name api.perfect21.dev;

        # 限流
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;

        location /api/v1/auth/ {
            proxy_pass http://perfect21_auth_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # CORS
            add_header Access-Control-Allow-Origin "https://app.perfect21.dev";
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type";
            add_header Access-Control-Max-Age 3600;
        }
    }

    server {
        listen 80;
        server_name api.perfect21.dev;
        return 301 https://$server_name$request_uri;
    }
}
```

### 3. 监控告警

```python
# features/auth_api/monitoring.py
import time
import psutil
import requests
from datetime import datetime
from typing import Dict, Any

class AuthAPIMonitor:
    """认证API监控器"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.alert_thresholds = {
            'response_time_ms': 1000,
            'error_rate_percent': 5,
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        start_time = time.time()

        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000  # 毫秒

            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': response_time,
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def system_metrics(self) -> Dict[str, Any]:
        """系统指标"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'connections': len(psutil.net_connections()),
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None,
            'timestamp': datetime.utcnow().isoformat()
        }

    def check_alerts(self) -> list:
        """检查告警条件"""
        alerts = []

        # 健康检查
        health = self.health_check()
        if health['status'] == 'unhealthy':
            alerts.append({
                'type': 'health_check_failed',
                'message': f"API健康检查失败: {health.get('error')}",
                'severity': 'critical'
            })
        elif health.get('response_time_ms', 0) > self.alert_thresholds['response_time_ms']:
            alerts.append({
                'type': 'high_response_time',
                'message': f"API响应时间过高: {health['response_time_ms']:.1f}ms",
                'severity': 'warning'
            })

        # 系统指标
        metrics = self.system_metrics()

        if metrics['cpu_percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'high_cpu_usage',
                'message': f"CPU使用率过高: {metrics['cpu_percent']:.1f}%",
                'severity': 'warning'
            })

        if metrics['memory_percent'] > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'message': f"内存使用率过高: {metrics['memory_percent']:.1f}%",
                'severity': 'warning'
            })

        if metrics['disk_percent'] > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'high_disk_usage',
                'message': f"磁盘使用率过高: {metrics['disk_percent']:.1f}%",
                'severity': 'critical'
            })

        return alerts
```

## 📚 总结

Perfect21用户登录API是一个功能完整、安全可靠的企业级身份认证系统。它提供了：

### ✅ 核心功能
- JWT令牌认证机制
- 密码安全存储
- 会话生命周期管理
- 基于角色的权限控制
- 完整的审计日志

### 🛡️ 安全特性
- bcrypt密码哈希
- 账户锁定保护
- IP地址限流
- 防暴力破解
- 验证码支持
- 设备指纹识别

### 📊 运维支持
- 性能监控
- 健康检查
- 告警通知
- 审计追踪
- 指标分析

### 🔧 开发友好
- OpenAPI规范
- 完整文档
- 测试用例
- 客户端SDK
- Docker部署

该API设计严格遵循RESTful原则和安全最佳实践，可以作为Perfect21平台的身份认证基础设施，为整个系统提供统一、安全、可扩展的用户认证服务。