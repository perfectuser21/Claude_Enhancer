# Perfect21 认证系统 API 接口列表

## 📋 API 接口概览

### 🔍 系统状态接口

| 接口 | 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|------|
| 健康检查 | GET | `/health` | 检查API服务状态 | ❌ |

### 🔐 认证接口

| 接口 | 方法 | 路径 | 描述 | 认证 | 限制 |
|------|------|------|------|------|------|
| 用户注册 | POST | `/auth/register` | 创建新用户账户 | ❌ | 5次/小时/IP |
| 用户登录 | POST | `/auth/login` | 用户身份验证 | ❌ | 10次/分钟/IP |
| 用户登出 | POST | `/auth/logout` | 使令牌失效 | ✅ | - |
| 刷新令牌 | POST | `/auth/refresh` | 获取新访问令牌 | ❌ | - |
| 忘记密码 | POST | `/auth/forgot-password` | 发起密码重置 | ❌ | 3次/小时/邮箱 |
| 重置密码 | POST | `/auth/reset-password` | 设置新密码 | ❌ | - |
| 修改密码 | POST | `/auth/change-password` | 已认证用户修改密码 | ✅ | - |

### 👤 用户管理接口

| 接口 | 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|------|
| 获取个人资料 | GET | `/users/profile` | 获取当前用户信息 | ✅ | user |
| 更新个人资料 | PUT | `/users/profile` | 更新用户信息 | ✅ | user |
| 上传头像 | POST | `/users/avatar` | 上传用户头像 | ✅ | user |
| 验证邮箱 | POST | `/users/verify-email` | 邮箱验证 | ✅ | user |
| 重发验证邮件 | POST | `/users/resend-verification` | 重新发送验证邮件 | ✅ | user |

### 🛡️ 管理员接口

| 接口 | 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|------|
| 获取用户列表 | GET | `/admin/users` | 分页获取用户列表 | ✅ | admin |
| 获取用户详情 | GET | `/admin/users/{userId}` | 获取指定用户信息 | ✅ | admin |
| 更新用户信息 | PUT | `/admin/users/{userId}` | 管理员更新用户 | ✅ | admin |
| 删除用户 | DELETE | `/admin/users/{userId}` | 删除用户账户 | ✅ | admin |

## 📤 请求响应示例

### 1. 用户注册

**请求示例**:
```bash
curl -X POST https://api.perfect21.dev/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "firstName": "John",
    "lastName": "Doe"
  }'
```

**成功响应** (201 Created):
```json
{
  "success": true,
  "message": "用户注册成功",
  "data": {
    "user": {
      "id": "usr_1234567890",
      "username": "johndoe",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "role": "user",
      "emailVerified": false,
      "createdAt": "2024-01-20T10:30:00Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600
    }
  }
}
```

**错误响应** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确",
        "code": "INVALID_FORMAT"
      }
    ],
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

### 2. 用户登录

**请求示例**:
```bash
curl -X POST https://api.perfect21.dev/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user": {
      "id": "usr_1234567890",
      "username": "johndoe",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "role": "user",
      "emailVerified": true,
      "lastLoginAt": "2024-01-20T10:30:00Z"
    },
    "tokens": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600
    }
  }
}
```

### 3. 获取用户资料

**请求示例**:
```bash
curl -X GET https://api.perfect21.dev/v1/users/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "usr_1234567890",
    "username": "johndoe",
    "email": "john@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1234567890",
    "organization": "Acme Corp",
    "role": "user",
    "emailVerified": true,
    "phoneVerified": false,
    "avatar": "https://api.perfect21.dev/avatars/usr_1234567890.jpg",
    "preferences": {
      "language": "zh-CN",
      "timezone": "Asia/Shanghai",
      "notifications": true,
      "theme": "auto"
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-20T10:30:00Z",
    "lastLoginAt": "2024-01-20T10:30:00Z"
  }
}
```

### 4. 管理员获取用户列表

**请求示例**:
```bash
curl -X GET "https://api.perfect21.dev/v1/admin/users?page=1&limit=20&search=john&role=user" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "usr_1234567890",
        "username": "johndoe",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "role": "user",
        "status": "active",
        "emailVerified": true,
        "createdAt": "2024-01-15T10:30:00Z",
        "lastLoginAt": "2024-01-20T10:30:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalUsers": 100,
      "limit": 20,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

### 5. 刷新访问令牌

**请求示例**:
```bash
curl -X POST https://api.perfect21.dev/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "message": "令牌刷新成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

## 🚫 常见错误示例

### 1. 认证失败
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "认证失败或令牌已过期",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

### 2. 权限不足
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "权限不足，无法执行此操作",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

### 3. 资源冲突
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "用户名或邮箱已存在",
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

### 4. 频率限制
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超过限制，请稍后重试",
    "retryAfter": 300,
    "timestamp": "2024-01-20T10:30:00Z",
    "requestId": "req_abc123xyz789"
  }
}
```

## 📊 API 使用统计

### 预期QPS (每秒查询数)
- 登录接口: 50-100 QPS
- 用户资料: 200-500 QPS
- 注册接口: 5-20 QPS
- 管理接口: 1-10 QPS

### 响应时间目标
- 认证接口: < 200ms
- 查询接口: < 100ms
- 更新接口: < 300ms
- 文件上传: < 2s

### 可用性目标
- SLA: 99.9% 可用性
- 响应时间: P95 < 500ms
- 错误率: < 0.1%

## 🔒 安全特性

### 认证安全
- JWT令牌签名验证
- 访问令牌1小时过期
- 刷新令牌30天过期
- 令牌黑名单机制

### 数据安全
- 密码bcrypt加密 (12轮)
- 敏感字段脱敏显示
- HTTPS强制传输
- 请求参数验证

### 访问控制
- 基于角色的权限控制
- API接口权限验证
- 资源级别权限检查
- 操作审计日志

## 📈 监控指标

### 业务指标
- 注册转化率
- 登录成功率
- 活跃用户数
- API调用量

### 技术指标
- 接口响应时间
- 错误率分布
- 并发连接数
- 系统资源使用率

### 安全指标
- 异常登录检测
- 暴力破解防护
- 恶意请求识别
- 数据泄露监控