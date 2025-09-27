# API 文档模板

## 📋 API 基本信息

| 字段 | 值 |
|------|-----|
| **API名称** | [API项目名称] |
| **版本** | v1.0 |
| **基础URL** | https://api.example.com/v1 |
| **文档版本** | v1.0 |
| **最后更新** | [YYYY-MM-DD] |
| **维护团队** | [团队名称] |
| **联系方式** | [邮箱地址] |

---

## 🚀 快速开始

### 获取访问权限
1. **注册开发者账号**：访问 [开发者门户](https://developer.example.com)
2. **创建应用**：获取 API Key 和 Secret
3. **获取访问令牌**：通过认证接口获取 Token
4. **开始调用**：在请求头中携带认证信息

### 示例请求
```bash
curl -X GET "https://api.example.com/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 🔐 认证授权

### 认证方式
#### 1. API Key 认证 (简单接口)
```http
GET /api/v1/public/data
X-API-Key: your_api_key_here
```

#### 2. JWT Token 认证 (用户相关)
```http
GET /api/v1/users/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3. OAuth 2.0 (第三方集成)
```http
GET /api/v1/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID
```

### 获取访问令牌
```http
POST /auth/token
Content-Type: application/json

{
  "grant_type": "password",
  "username": "user@example.com",
  "password": "secure_password",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 📖 API 规范

### 请求格式
- **协议**：HTTPS
- **数据格式**：JSON
- **字符编码**：UTF-8
- **时间格式**：ISO 8601 (2024-01-01T12:00:00Z)

### 响应格式
#### 成功响应
```json
{
  "success": true,
  "data": {
    // 实际数据内容
  },
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

### HTTP 状态码
| 状态码 | 含义 | 说明 |
|--------|------|------|
| **200** | OK | 请求成功 |
| **201** | Created | 资源创建成功 |
| **204** | No Content | 请求成功，无返回内容 |
| **400** | Bad Request | 请求参数错误 |
| **401** | Unauthorized | 未授权，需要身份验证 |
| **403** | Forbidden | 权限不足 |
| **404** | Not Found | 资源不存在 |
| **409** | Conflict | 资源冲突 |
| **422** | Unprocessable Entity | 实体验证失败 |
| **429** | Too Many Requests | 请求频率过高 |
| **500** | Internal Server Error | 服务器内部错误 |

---

## 👥 用户管理 API

### 用户注册
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1001,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "注册成功"
}
```

### 用户登录
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

### 获取用户信息
```http
GET /users/me
Authorization: Bearer {access_token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "id": 1001,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://cdn.example.com/avatars/1001.jpg",
    "email_verified": true,
    "created_at": "2024-01-01T12:00:00Z",
    "last_login": "2024-01-01T18:30:00Z"
  }
}
```

### 更新用户信息
```http
PUT /users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "avatar_url": "https://cdn.example.com/avatars/new_avatar.jpg"
}
```

### 修改密码
```http
POST /users/me/change-password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

---

## 📦 资源管理 API

### 获取资源列表
```http
GET /resources?page=1&limit=20&sort=created_at&order=desc&category=tech
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| page | integer | 否 | 页码，默认1 | 1 |
| limit | integer | 否 | 每页数量，默认20，最大100 | 20 |
| sort | string | 否 | 排序字段 | created_at |
| order | string | 否 | 排序方向：asc/desc | desc |
| category | string | 否 | 分类筛选 | tech |
| search | string | 否 | 搜索关键词 | javascript |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 2001,
        "title": "JavaScript 高级教程",
        "description": "深入学习JavaScript高级特性",
        "category": "tech",
        "author": {
          "id": 1001,
          "username": "john_doe",
          "avatar_url": "https://cdn.example.com/avatars/1001.jpg"
        },
        "tags": ["javascript", "tutorial", "advanced"],
        "views": 1250,
        "likes": 89,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 获取单个资源
```http
GET /resources/{resource_id}
Authorization: Bearer {access_token}
```

### 创建资源
```http
POST /resources
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "React 性能优化指南",
  "description": "详细介绍React应用性能优化技巧",
  "content": "# React 性能优化\n\n...",
  "category": "tech",
  "tags": ["react", "performance", "optimization"],
  "is_public": true
}
```

### 更新资源
```http
PUT /resources/{resource_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "React 性能优化指南（更新版）",
  "description": "最新的React性能优化技巧和最佳实践",
  "tags": ["react", "performance", "optimization", "2024"]
}
```

### 删除资源
```http
DELETE /resources/{resource_id}
Authorization: Bearer {access_token}
```

---

## 💬 评论系统 API

### 获取评论列表
```http
GET /resources/{resource_id}/comments?page=1&limit=10
Authorization: Bearer {access_token}
```

### 发表评论
```http
POST /resources/{resource_id}/comments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "这个教程非常有用，谢谢分享！",
  "parent_id": null
}
```

### 回复评论
```http
POST /resources/{resource_id}/comments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "感谢您的反馈！",
  "parent_id": 3001
}
```

---

## 📤 文件上传 API

### 获取上传凭证
```http
POST /upload/token
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "file_type": "image",
  "file_size": 1024000,
  "file_name": "avatar.jpg"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "upload_url": "https://upload.example.com/upload",
    "upload_token": "upload_token_here",
    "expires_at": "2024-01-01T13:00:00Z",
    "max_file_size": 5242880
  }
}
```

### 直接上传文件
```http
POST /upload/file
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary file data]
type: "avatar"
```

---

## 🔔 通知系统 API

### 获取通知列表
```http
GET /notifications?unread_only=true&page=1&limit=20
Authorization: Bearer {access_token}
```

### 标记通知为已读
```http
POST /notifications/{notification_id}/read
Authorization: Bearer {access_token}
```

### 标记所有通知为已读
```http
POST /notifications/read-all
Authorization: Bearer {access_token}
```

---

## 🔍 搜索 API

### 全局搜索
```http
GET /search?q=javascript&type=all&page=1&limit=20
Authorization: Bearer {access_token}
```

**查询参数：**
| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| q | string | 是 | 搜索关键词 | javascript |
| type | string | 否 | 搜索类型：all/users/resources/comments | all |
| page | integer | 否 | 页码 | 1 |
| limit | integer | 否 | 每页数量 | 20 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "query": "javascript",
    "total": 45,
    "results": {
      "resources": [
        {
          "id": 2001,
          "title": "JavaScript 高级教程",
          "excerpt": "...JavaScript是一门强大的编程语言...",
          "relevance_score": 0.95
        }
      ],
      "users": [
        {
          "id": 1001,
          "username": "js_expert",
          "first_name": "Jane",
          "last_name": "Smith"
        }
      ]
    }
  }
}
```

---

## 📊 统计分析 API

### 获取用户统计
```http
GET /stats/user?period=30d
Authorization: Bearer {access_token}
```

### 获取资源统计
```http
GET /stats/resources/{resource_id}?period=7d
Authorization: Bearer {access_token}
```

---

## 🔄 Webhook

### 配置Webhook
```http
POST /webhooks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["resource.created", "comment.created"],
  "secret": "your_webhook_secret"
}
```

### Webhook事件格式
```json
{
  "event": "resource.created",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "resource": {
      "id": 2001,
      "title": "新资源标题",
      "author_id": 1001
    }
  },
  "signature": "sha256=hash_value"
}
```

---

## ⚡ 实时 API (WebSocket)

### 连接WebSocket
```javascript
const ws = new WebSocket('wss://api.example.com/ws');

// 认证
ws.onopen = function() {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_access_token'
  }));
};

// 接收消息
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};
```

### 订阅频道
```javascript
// 订阅用户通知
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'user.notifications'
}));

// 订阅资源评论
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'resource.2001.comments'
}));
```

---

## 🚦 限流规则

### 频率限制
| 接口类型 | 限制 | 时间窗口 | 超限响应 |
|----------|------|----------|----------|
| **认证接口** | 5次 | 1分钟 | 429 Too Many Requests |
| **读取接口** | 1000次 | 1小时 | 429 Too Many Requests |
| **写入接口** | 100次 | 1小时 | 429 Too Many Requests |
| **上传接口** | 10次 | 1分钟 | 429 Too Many Requests |

### 限流响应头
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 3600
```

---

## ❌ 错误代码

### 通用错误代码
| 代码 | 描述 | HTTP状态码 | 解决方案 |
|------|------|------------|----------|
| **INVALID_REQUEST** | 请求格式错误 | 400 | 检查请求格式和参数 |
| **UNAUTHORIZED** | 未授权访问 | 401 | 提供有效的认证信息 |
| **FORBIDDEN** | 权限不足 | 403 | 联系管理员获取权限 |
| **NOT_FOUND** | 资源不存在 | 404 | 检查资源ID是否正确 |
| **VALIDATION_ERROR** | 参数验证失败 | 422 | 按照API文档提供正确参数 |
| **RATE_LIMITED** | 请求频率过高 | 429 | 降低请求频率 |
| **INTERNAL_ERROR** | 服务器内部错误 | 500 | 稍后重试或联系技术支持 |

### 业务错误代码
| 代码 | 描述 | HTTP状态码 | 解决方案 |
|------|------|------------|----------|
| **USER_EXISTS** | 用户已存在 | 409 | 使用其他用户名或邮箱 |
| **INVALID_CREDENTIALS** | 认证信息错误 | 401 | 检查用户名和密码 |
| **EMAIL_NOT_VERIFIED** | 邮箱未验证 | 422 | 验证邮箱后重试 |
| **RESOURCE_LIMIT_EXCEEDED** | 资源数量超限 | 422 | 删除一些资源或升级账号 |

---

## 📚 SDK 和示例代码

### JavaScript SDK
```javascript
import { APIClient } from '@example/api-client';

const client = new APIClient({
  baseURL: 'https://api.example.com/v1',
  token: 'your_access_token'
});

// 获取用户信息
const user = await client.users.getMe();

// 创建资源
const resource = await client.resources.create({
  title: '新资源',
  content: '资源内容'
});
```

### Python SDK
```python
from example_api import APIClient

client = APIClient(
    base_url='https://api.example.com/v1',
    token='your_access_token'
)

# 获取用户信息
user = client.users.get_me()

# 创建资源
resource = client.resources.create(
    title='新资源',
    content='资源内容'
)
```

### cURL 示例
```bash
# 创建资源
curl -X POST "https://api.example.com/v1/resources" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新资源",
    "content": "资源内容"
  }'
```

---

## 🧪 测试环境

### 测试服务器
- **基础URL**：https://api-test.example.com/v1
- **测试账号**：test@example.com / TestPassword123!
- **API Key**：test_api_key_here

### 测试数据
```json
{
  "test_user": {
    "id": 9999,
    "username": "test_user",
    "email": "test@example.com"
  },
  "test_resource": {
    "id": 8888,
    "title": "测试资源"
  }
}
```

---

## 📈 版本历史

### v1.0 (当前版本)
- ✅ 用户认证和授权
- ✅ 资源CRUD操作
- ✅ 评论系统
- ✅ 文件上传
- ✅ 实时通知

### v0.9 (测试版本)
- ✅ 基础API功能
- ✅ 用户管理
- ✅ 搜索功能

### 即将发布 (v1.1)
- 🚧 高级搜索功能
- 🚧 批量操作API
- 🚧 GraphQL支持
- 🚧 更多数据导出格式

---

## 🛠️ 开发工具

### API测试工具
- **Postman Collection**：[下载链接](https://example.com/postman)
- **Insomnia Workspace**：[下载链接](https://example.com/insomnia)
- **OpenAPI规范**：[查看链接](https://api.example.com/docs)

### 调试工具
- **API调试面板**：https://api.example.com/debug
- **日志查看器**：https://logs.example.com
- **性能监控**：https://monitor.example.com

---

## 📞 技术支持

### 联系方式
- **技术支持邮箱**：api-support@example.com
- **开发者社区**：https://community.example.com
- **GitHub Issues**：https://github.com/example/api/issues
- **Discord频道**：https://discord.gg/example

### 支持时间
- **工作日**：9:00 - 18:00 (GMT+8)
- **响应时间**：4小时内回复
- **紧急问题**：24小时内处理

---

## 📋 FAQ

### Q: 如何获取API访问权限？
**A:** 访问开发者门户注册账号，创建应用即可获得API密钥。

### Q: API有访问频率限制吗？
**A:** 是的，不同接口有不同的频率限制，详见"限流规则"章节。

### Q: 如何处理Token过期？
**A:** 使用refresh_token刷新访问令牌，或重新登录获取新的Token。

### Q: 支持批量操作吗？
**A:** v1.0版本暂不支持，v1.1版本将提供批量操作API。

### Q: 如何报告API问题？
**A:** 通过GitHub Issues或技术支持邮箱报告问题。

---

*🔗 相关链接：*
*- [开发者门户](https://developer.example.com)*
*- [API状态页面](https://status.example.com)*
*- [更新日志](https://example.com/changelog)*
*- [服务条款](https://example.com/terms)*

*📝 使用说明：*
*1. 替换所有占位符和示例内容*
*2. 根据实际API功能调整章节*
*3. 保持示例代码的准确性*
*4. 定期更新文档内容*
*5. 提供清晰的错误处理指导*