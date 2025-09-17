# Perfect21 认证API速查表

## 快速开始

**Base URL**: `http://localhost:8000/api/auth`

**认证方式**: `Authorization: Bearer <token>`

---

## 🔑 核心端点

### 1. 登录 `POST /login`

```json
// 请求
{
  "identifier": "user@example.com",  // 用户名或邮箱
  "password": "password123",         // 密码
  "remember_me": false              // 可选
}

// 成功响应 (200)
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "user": { "id": "123", "username": "user", ... }
}

// 失败响应 (401)
{
  "success": false,
  "message": "用户名或密码错误"
}
```

### 2. 刷新令牌 `POST /refresh`

```json
// 请求
{
  "refresh_token": "eyJ..."
}

// 成功响应 (200)
{
  "success": true,
  "access_token": "eyJ...",
  "expires_in": 3600,
  "user": { ... }
}
```

### 3. 登出 `POST /logout`

```bash
# 请求头
Authorization: Bearer eyJ...

# 响应 (200)
{
  "success": true,
  "message": "登出成功"
}
```

### 4. 获取用户信息 `GET /me`

```bash
# 请求头
Authorization: Bearer eyJ...

# 响应 (200)
{
  "id": "123",
  "username": "john_doe",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-15T10:30:00Z"
}
```

---

## 📊 状态码快查

| 状态码 | 含义 | 常见场景 |
|--------|------|----------|
| **200** | 成功 | 登录成功、获取信息成功 |
| **401** | 认证失败 | 密码错误、令牌过期 |
| **403** | 权限不足 | 账户被禁用、角色权限不够 |
| **422** | 参数错误 | 密码格式错误、必填字段缺失 |
| **429** | 请求过频 | 登录尝试过多、API调用超限 |
| **500** | 服务器错误 | 内部系统故障 |

---

## 🚨 错误码快查

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `invalid_credentials` | 登录凭据错误 | 检查用户名和密码 |
| `token_expired` | 令牌过期 | 使用refresh_token刷新 |
| `token_invalid` | 令牌无效 | 重新登录 |
| `account_locked` | 账户锁定 | 等待15分钟或联系管理员 |
| `rate_limit_exceeded` | 请求超限 | 等待后重试 |

---

## ⚡ cURL 命令示例

### 登录
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "password": "password123"
  }'
```

### 刷新令牌
```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

### 获取用户信息
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer your_access_token_here"
```

### 登出
```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer your_access_token_here"
```

---

## 🛡️ 安全规则

### 令牌管理
- **访问令牌**: 1小时有效期
- **刷新令牌**: 30天有效期，一次性使用
- **存储建议**: 访问令牌存内存，刷新令牌存安全存储

### 频率限制
- **登录**: 5次/IP/15分钟
- **刷新**: 10次/用户/小时
- **用户信息**: 100次/用户/小时

### 密码要求
- 最小长度: 8位
- 复杂度: 建议包含大小写字母、数字、特殊字符
- 历史检查: 不能重复最近3次密码

---

## 🔧 开发提示

### JavaScript/TypeScript
```javascript
// 使用fetch API
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    identifier: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
if (data.success) {
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}
```

### Python
```python
import requests

# 登录
response = requests.post('http://localhost:8000/api/auth/login', json={
    'identifier': 'user@example.com',
    'password': 'password123'
})

if response.status_code == 200:
    data = response.json()
    access_token = data['access_token']

    # 使用令牌访问受保护资源
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info = requests.get('http://localhost:8000/api/auth/me', headers=headers)
```

### 令牌自动刷新逻辑
```javascript
async function apiCall(url, options = {}) {
  let token = localStorage.getItem('access_token');

  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  });

  // 如果令牌过期，尝试刷新
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (refreshResponse.ok) {
      const data = await refreshResponse.json();
      localStorage.setItem('access_token', data.access_token);

      // 重试原请求
      return fetch(url, {
        ...options,
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          ...options.headers
        }
      });
    } else {
      // 刷新失败，需要重新登录
      window.location.href = '/login';
    }
  }

  return response;
}
```

---

## 📱 客户端集成

### React Hook 示例
```javascript
import { useState, useEffect } from 'react';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUserInfo(token);
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (identifier, password) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password })
    });

    const data = await response.json();
    if (data.success) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      setUser(data.user);
      return { success: true };
    }
    return { success: false, message: data.message };
  };

  const logout = async () => {
    const token = localStorage.getItem('access_token');
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return { user, login, logout, loading };
}
```

---

## 🔍 调试技巧

### 检查令牌有效性
```bash
# 解码JWT令牌内容（不验证签名）
echo "eyJ..." | base64 -d | jq .
```

### 测试API连通性
```bash
# 健康检查
curl http://localhost:8000/api/auth/health

# 验证令牌
curl -X GET "http://localhost:8000/api/auth/verify" \
  -H "Authorization: Bearer your_token_here"
```

### 常见问题排查
1. **401错误**: 检查令牌格式和有效期
2. **403错误**: 检查用户角色和权限
3. **429错误**: 检查请求频率，等待后重试
4. **422错误**: 检查请求参数格式和必填字段

---

> 💡 **提示**: 建议保存此文档到书签，方便开发时快速查阅API信息。