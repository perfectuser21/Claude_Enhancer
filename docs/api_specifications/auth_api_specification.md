# Perfect21 认证API规范

## 概览

Perfect21认证API提供完整的用户认证和授权功能，支持JWT令牌认证、刷新令牌机制、用户管理等核心功能。

**基础URL**: `http://localhost:8000/api/auth`

**认证方式**: Bearer Token (JWT)

**内容类型**: `application/json`

---

## 核心端点

### 1. 用户登录

**端点**: `POST /api/auth/login`

**描述**: 用户使用邮箱/用户名和密码进行登录，获取访问令牌和刷新令牌

#### 请求

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "identifier": "user@example.com",  // 用户名或邮箱
  "password": "userpassword123",     // 密码
  "remember_me": false               // 可选，是否记住登录
}
```

**字段验证**:
- `identifier`: 必填，最小长度1
- `password`: 必填，最小长度1
- `remember_me`: 可选，布尔值，默认false

#### 响应

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IlJlZnJlc2gifQ...",
  "expires_in": 3600,
  "message": "登录成功",
  "user": {
    "id": "12345",
    "username": "john_doe",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2025-01-01T00:00:00Z",
    "last_login": "2025-01-15T10:30:00Z"
  }
}
```

**错误响应**:

**401 Unauthorized - 认证失败**:
```json
{
  "success": false,
  "access_token": null,
  "refresh_token": null,
  "user": null,
  "expires_in": null,
  "message": "用户名或密码错误"
}
```

**429 Too Many Requests - 请求过频**:
```json
{
  "success": false,
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 60
}
```

**422 Unprocessable Entity - 验证失败**:
```json
{
  "success": false,
  "message": "请求参数验证失败",
  "errors": [
    {
      "field": "password",
      "message": "密码不能为空"
    }
  ]
}
```

---

### 2. 刷新访问令牌

**端点**: `POST /api/auth/refresh`

**描述**: 使用有效的刷新令牌获取新的访问令牌

#### 请求

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IlJlZnJlc2gifQ..."
}
```

**字段验证**:
- `refresh_token`: 必填，最小长度1

#### 响应

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "message": "令牌刷新成功",
  "user": {
    "id": "12345",
    "username": "john_doe",
    "email": "user@example.com",
    "role": "user"
  }
}
```

**错误响应**:

**401 Unauthorized - 令牌无效**:
```json
{
  "success": false,
  "access_token": null,
  "user": null,
  "expires_in": null,
  "message": "刷新令牌已过期或无效"
}
```

**403 Forbidden - 令牌被吊销**:
```json
{
  "success": false,
  "message": "刷新令牌已被吊销"
}
```

---

### 3. 用户登出

**端点**: `POST /api/auth/logout`

**描述**: 登出当前用户，使当前的访问令牌失效

#### 请求

**请求头**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**请求体**: 无需请求体

#### 响应

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

**错误响应**:

**401 Unauthorized - 未认证**:
```json
{
  "success": false,
  "message": "需要认证",
  "error": "missing_token"
}
```

**401 Unauthorized - 令牌无效**:
```json
{
  "success": false,
  "message": "访问令牌无效或已过期",
  "error": "invalid_token"
}
```

---

### 4. 获取当前用户信息

**端点**: `GET /api/auth/me`

**描述**: 获取当前已认证用户的详细信息

#### 请求

**请求头**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**查询参数**: 无

#### 响应

**成功响应 (200 OK)**:
```json
{
  "id": "12345",
  "username": "john_doe",
  "email": "user@example.com",
  "role": "user",
  "created_at": "2025-01-01T00:00:00Z",
  "last_login": "2025-01-15T10:30:00Z"
}
```

**错误响应**:

**401 Unauthorized - 未认证**:
```json
{
  "detail": "需要认证",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

**403 Forbidden - 权限不足**:
```json
{
  "detail": "权限不足"
}
```

---

## 状态码说明

### 成功状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功处理请求（登录、刷新、登出、获取信息） |
| 201 | Created | 成功创建资源（注册用户） |

### 错误状态码

| 状态码 | 含义 | 使用场景 | 响应格式 |
|--------|------|----------|----------|
| 400 | Bad Request | 请求参数格式错误 | `{"detail": "请求格式错误"}` |
| 401 | Unauthorized | 认证失败或令牌无效 | `{"success": false, "message": "认证失败"}` |
| 403 | Forbidden | 权限不足或账户被禁用 | `{"detail": "权限不足"}` |
| 422 | Unprocessable Entity | 请求参数验证失败 | `{"detail": [{"field": "password", "message": "密码格式错误"}]}` |
| 429 | Too Many Requests | 请求频率超限 | `{"detail": "请求过于频繁", "retry_after": 60}` |
| 500 | Internal Server Error | 服务器内部错误 | `{"detail": "服务器内部错误"}` |

---

## 认证机制

### JWT访问令牌
- **格式**: Bearer Token
- **有效期**: 1小时 (3600秒)
- **使用方式**: 在请求头中添加 `Authorization: Bearer <token>`
- **包含信息**: 用户ID、角色、过期时间等

### 刷新令牌
- **有效期**: 30天
- **使用场景**: 当访问令牌过期时获取新的访问令牌
- **安全性**: 一次性使用，使用后会生成新的刷新令牌

### 令牌安全
- 支持令牌黑名单机制
- 登出时令牌立即失效
- 异常登录检测和自动吊销

---

## 速率限制

| 端点 | 限制规则 | 时间窗口 | 超限行为 |
|------|----------|----------|----------|
| `/login` | 5次/IP | 15分钟 | 返回429，等待15分钟 |
| `/refresh` | 10次/用户 | 1小时 | 返回429，等待1小时 |
| `/logout` | 无限制 | - | - |
| `/me` | 100次/用户 | 1小时 | 返回429，等待1小时 |

---

## 安全特性

### 密码安全
- 最小长度8位
- 支持特殊字符、大小写字母、数字
- bcrypt加密存储
- 密码历史检查

### 登录安全
- 失败次数限制（5次后锁定15分钟）
- IP地址跟踪
- 异常登录检测
- 设备指纹识别

### 令牌安全
- JWT签名验证
- 令牌过期检查
- 黑名单机制
- 自动轮换刷新令牌

---

## 示例请求

### 1. 用户登录示例

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "password": "securepassword123",
    "remember_me": true
  }'
```

### 2. 令牌刷新示例

```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IlJlZnJlc2gifQ..."
  }'
```

### 3. 获取用户信息示例

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. 用户登出示例

```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

---

## 错误处理

### 统一错误格式

所有API错误都遵循统一格式：

```json
{
  "success": false,
  "message": "错误描述",
  "error": "error_code",
  "details": {
    "field": "具体字段错误信息"
  }
}
```

### 常见错误代码

| 错误代码 | 含义 | 解决方案 |
|----------|------|----------|
| `invalid_credentials` | 用户名或密码错误 | 检查登录凭据 |
| `token_expired` | 令牌已过期 | 使用刷新令牌获取新的访问令牌 |
| `token_invalid` | 令牌格式无效 | 重新登录获取有效令牌 |
| `account_locked` | 账户被锁定 | 联系管理员或等待解锁 |
| `rate_limit_exceeded` | 请求频率超限 | 等待一段时间后重试 |
| `validation_failed` | 请求参数验证失败 | 检查请求参数格式和内容 |

---

## 版本信息

- **API版本**: v1.0
- **最后更新**: 2025-09-17
- **兼容性**: 向后兼容
- **弃用计划**: 无

---

## 联系信息

- **技术支持**: 通过GitHub Issues
- **文档更新**: 自动生成并同步
- **API变更通知**: 通过版本控制系统跟踪