# Perfect21 后端API文档

> Perfect21智能开发平台后端API完整文档

## 概述

Perfect21后端提供了完整的用户认证、任务执行、Git工作流管理等功能的RESTful API接口。

### 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: `3.0.0`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 认证系统

### 用户注册

**POST** `/api/auth/register`

注册新用户账户。

**请求体:**
```json
{
  "username": "string (3-30字符)",
  "email": "string (有效邮箱)",
  "password": "string (8+字符，包含大小写字母、数字、特殊字符)",
  "role": "string (可选，默认为'user')"
}
```

**响应:**
```json
{
  "success": true,
  "user_id": "string",
  "verification_token": "string",
  "message": "注册成功，请验证邮箱"
}
```

**错误响应:**
```json
{
  "success": false,
  "message": "错误描述"
}
```

### 用户登录

**POST** `/api/auth/login`

用户登录获取访问令牌。

**请求体:**
```json
{
  "identifier": "string (用户名或邮箱)",
  "password": "string",
  "remember_me": "boolean (可选，默认false)"
}
```

**响应:**
```json
{
  "success": true,
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "string",
    "created_at": "string",
    "last_login": "string"
  },
  "expires_in": 3600,
  "message": "登录成功"
}
```

### 刷新令牌

**POST** `/api/auth/refresh`

使用刷新令牌获取新的访问令牌。

**请求体:**
```json
{
  "refresh_token": "string"
}
```

**响应:**
```json
{
  "success": true,
  "access_token": "string",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "string"
  },
  "expires_in": 3600,
  "message": "令牌刷新成功"
}
```

### 验证令牌

**GET** `/api/auth/verify`

验证访问令牌的有效性。

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "success": true,
  "message": "令牌验证成功"
}
```

### 用户登出

**POST** `/api/auth/logout`

撤销访问令牌，用户登出。

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 获取用户资料

**GET** `/api/auth/profile`

获取当前用户的详细资料。

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "role": "string",
  "created_at": "string",
  "last_login": "string"
}
```

### 更新用户资料

**PUT** `/api/auth/profile`

更新当前用户的资料信息。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "username": "string (可选)",
  "email": "string (可选)"
}
```

**响应:**
```json
{
  "success": true,
  "message": "用户资料更新成功"
}
```

### 修改密码

**POST** `/api/auth/change-password`

修改当前用户密码。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**响应:**
```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

## 开发任务执行

### 执行开发任务

**POST** `/task`

执行开发任务，调用Perfect21的Agent协作系统。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "description": "string (任务描述)",
  "timeout": "integer (可选，超时时间，默认300秒)",
  "verbose": "boolean (可选，是否详细输出)"
}
```

**响应:**
```json
{
  "success": true,
  "output": "string (任务执行输出)",
  "error": "string (错误信息，如果有)"
}
```

### 异步执行任务

**POST** `/task/async`

异步执行开发任务。

**请求体:** 同上

**响应:**
```json
{
  "success": true,
  "task_id": "string",
  "output": "任务已开始异步执行"
}
```

### 获取异步任务状态

**GET** `/task/{task_id}`

获取异步任务的执行状态。

**响应:**
```json
{
  "success": true,
  "task_id": "string",
  "output": "string (任务输出或状态)",
  "error": "string (错误信息，如果有)"
}
```

## Git工作流管理

### 执行Git工作流操作

**POST** `/workflow`

执行Git工作流相关操作。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "action": "string (操作类型)",
  "name": "string (可选，名称)",
  "version": "string (可选，版本)",
  "source": "string (可选，源分支)",
  "branch": "string (可选，目标分支)"
}
```

**支持的操作类型:**
- `create-feature`: 创建功能分支
- `create-release`: 创建发布分支
- `merge-to-main`: 合并到主分支
- `branch-info`: 获取分支信息
- `cleanup`: 清理旧分支

**响应:**
```json
{
  "success": true,
  "output": "string (操作结果)",
  "error": "string (错误信息，如果有)"
}
```

### Git钩子管理

**POST** `/hooks/install`

安装Git钩子。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "hook_group": "string (钩子组，默认'standard')",
  "force": "boolean (是否强制覆盖，默认false)"
}
```

**响应:**
```json
{
  "success": true,
  "output": "string (安装结果)",
  "error": "string (错误信息，如果有)"
}
```

## 系统状态

### 系统状态检查

**GET** `/status`

获取Perfect21系统状态。

**响应:**
```json
{
  "success": true,
  "output": "string (状态信息)",
  "error": "string (错误信息，如果有)"
}
```

### 健康检查

**GET** `/health`

系统健康检查端点。

**响应:**
```json
{
  "success": true,
  "perfect21_available": true,
  "output": "string (健康状态)"
}
```

### 认证服务健康检查

**GET** `/api/auth/health`

认证服务健康检查。

**响应:**
```json
{
  "status": "healthy",
  "service": "auth",
  "timestamp": "string"
}
```

## 性能监控接口

### 获取系统性能指标

**GET** `/api/metrics`

获取Perfect21系统性能指标。

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "success": true,
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "active_tasks": 3,
    "avg_response_time": 156.7,
    "error_rate": 0.02,
    "cache_hit_rate": 94.5
  },
  "timestamp": "2025-09-17T10:30:00Z"
}
```

### 获取质量门统计

**GET** `/api/quality/gates`

获取质量门检查统计信息。

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "success": true,
  "quality_gates": {
    "total_checks": 147,
    "passed_checks": 134,
    "failed_checks": 13,
    "pass_rate": 91.2,
    "average_score": 8.7
  },
  "recent_failures": [
    {
      "gate_name": "code_coverage",
      "timestamp": "2025-09-17T09:15:00Z",
      "reason": "Coverage 87% below threshold 90%"
    }
  ]
}
```

## 智能工作流接口

### 获取工作流模板

**GET** `/api/workflows/templates`

获取可用的工作流模板列表。

**响应:**
```json
{
  "success": true,
  "templates": [
    {
      "name": "premium_quality",
      "description": "质量优先工作流",
      "phases": 5,
      "estimated_time": "45-60分钟",
      "quality_gates": 3,
      "recommended_for": ["生产级功能", "核心架构", "安全相关"]
    },
    {
      "name": "rapid_development",
      "description": "快速开发工作流",
      "phases": 3,
      "estimated_time": "15-30分钟",
      "quality_gates": 1,
      "recommended_for": ["Bug修复", "原型开发", "简单功能"]
    }
  ]
}
```

### 执行智能工作流

**POST** `/api/workflows/execute`

执行智能工作流任务。

**请求头:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "template": "premium_quality",
  "description": "实现用户认证系统",
  "context": {
    "tech_stack": "Python FastAPI",
    "complexity": "medium",
    "security_level": "high"
  },
  "quality_requirements": {
    "code_coverage": 90,
    "performance_threshold": 200,
    "security_scan": true
  }
}
```

**响应:**
```json
{
  "success": true,
  "workflow_id": "wf-20250917-001",
  "execution_plan": {
    "phases": [
      {
        "name": "深度理解",
        "agents": ["@project-manager", "@business-analyst", "@technical-writer"],
        "parallel": true,
        "estimated_time": "10分钟"
      }
    ],
    "sync_points": 3,
    "quality_gates": 3,
    "estimated_total_time": "50分钟"
  },
  "monitoring_url": "/api/workflows/wf-20250917-001/status"
}
```

## 管理员接口

### 获取用户列表

**GET** `/api/auth/admin/users`

获取系统用户列表（需要管理员权限）。

**请求头:**
```
Authorization: Bearer <admin_access_token>
```

**响应:**
```json
{
  "success": true,
  "users": [],
  "total": 0,
  "message": "string"
}
```

### 获取安全统计

**GET** `/api/auth/admin/security/stats`

获取安全统计信息（需要管理员权限）。

**请求头:**
```
Authorization: Bearer <admin_access_token>
```

**响应:**
```json
{
  "success": true,
  "stats": {
    "total_events": "integer",
    "events_last_hour": "integer",
    "events_last_day": "integer",
    "locked_accounts": "integer",
    "password_policy": {}
  }
}
```

## WebSocket接口

### 实时任务流

**WebSocket** `/ws/task`

通过WebSocket实现实时任务执行流。

**发送消息:**
```json
{
  "description": "string (任务描述)",
  "timeout": "integer (可选)"
}
```

**接收消息:**
```json
{
  "type": "status|result|error",
  "message": "string",
  "success": "boolean (仅在type=result时)",
  "output": "string (仅在type=result时)",
  "error": "string (仅在type=error时)"
}
```

## 错误码说明

### HTTP状态码

- `200`: 请求成功
- `400`: 请求参数错误
- `401`: 未授权（需要登录）
- `403`: 禁止访问（权限不足）
- `404`: 资源不存在
- `422`: 请求数据验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误
- `503`: 服务不可用

### 业务错误码

#### 认证相关
- `USER_EXISTS`: 用户名或邮箱已存在
- `INVALID_CREDENTIALS`: 用户名或密码错误
- `ACCOUNT_INACTIVE`: 账户未激活或已禁用
- `TOO_MANY_ATTEMPTS`: 登录尝试次数过多
- `INVALID_TOKEN`: 访问令牌无效或已过期
- `INVALID_REFRESH_TOKEN`: 刷新令牌无效或已过期
- `USER_INACTIVE`: 用户不存在或已被禁用
- `INVALID_OLD_PASSWORD`: 原密码错误
- `USER_NOT_FOUND`: 用户不存在
- `NO_UPDATE_DATA`: 没有可更新的数据

#### 系统相关
- `RATE_LIMIT_EXCEEDED`: 请求频率限制
- `VALIDATION_ERROR`: 数据验证错误
- `INTERNAL_SERVER_ERROR`: 服务器内部错误

## 认证流程

### 标准认证流程

1. **注册**: POST `/api/auth/register`
2. **登录**: POST `/api/auth/login` → 获取 `access_token` 和 `refresh_token`
3. **API调用**: 在请求头中包含 `Authorization: Bearer <access_token>`
4. **令牌刷新**: 当访问令牌过期时，使用 `refresh_token` 调用 `/api/auth/refresh`
5. **登出**: POST `/api/auth/logout`

### 令牌生命周期

- **访问令牌**: 1小时（生产环境），24小时（开发环境）
- **刷新令牌**: 7天（生产环境），30天（开发环境）

## 速率限制

### 默认限制

- **标准接口**: 1000请求/小时
- **登录接口**: 10请求/10分钟
- **注册接口**: 5请求/小时

### 响应头

限流相关的响应头：
- `X-RateLimit-Limit`: 速率限制
- `X-RateLimit-Remaining`: 剩余请求数
- `X-RateLimit-Reset`: 重置时间
- `Retry-After`: 重试等待时间

## SDK示例

### Python示例

```python
import requests
import json

class Perfect21Client:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None

    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"identifier": username, "password": password}
        )
        data = response.json()
        if data["success"]:
            self.access_token = data["access_token"]
        return data

    def execute_task(self, description):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.post(
            f"{self.base_url}/task",
            json={"description": description},
            headers=headers
        )
        return response.json()

# 使用示例
client = Perfect21Client()
client.login("admin", "Admin123!")
result = client.execute_task("创建一个用户管理模块")
print(result["output"])
```

### JavaScript示例

```javascript
class Perfect21Client {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.accessToken = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/api/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({identifier: username, password: password})
        });
        const data = await response.json();
        if (data.success) {
            this.accessToken = data.access_token;
        }
        return data;
    }

    async executeTask(description) {
        const response = await fetch(`${this.baseURL}/task`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.accessToken}`
            },
            body: JSON.stringify({description: description})
        });
        return await response.json();
    }
}

// 使用示例
const client = new Perfect21Client();
await client.login('admin', 'Admin123!');
const result = await client.executeTask('实现数据分析功能');
console.log(result.output);
```

## 部署说明

### 开发环境

```bash
# 快速启动开发服务器
./start_dev_server.sh

# 或手动启动
python3 scripts/start_api.py --reload --debug
```

### 生产环境

```bash
# 使用Docker
docker-compose up -d

# 或手动启动
ENV=production python3 scripts/start_api.py --workers 4
```

### 环境变量

生产环境必需的环境变量：

```bash
export JWT_SECRET_KEY="your-secret-key"
export DATABASE_PASSWORD="your-db-password"
export ADMIN_PASSWORD="your-admin-password"
```

## 更新日志

### v3.0.0 (2025-09-17)
- ✨ 新增智能并行执行引擎
- ✨ 增强的质量门检查系统
- ✨ 实时性能监控与告警
- ✨ 多工作空间管理功能
- ✨ 高级安全防护机制
- ✨ 智能学习反馈循环
- ✨ 企业级部署优化
- ✨ 完整的故障排除工具

### v2.3.0 (2025-09-16)
- ✅ 完整的用户认证系统
- ✅ JWT令牌管理
- ✅ API限流和安全中间件
- ✅ 数据库和缓存支持
- ✅ WebSocket实时通信
- ✅ Docker化部署
- ✅ 完整的API文档

---

**注意**: 这是一个完整的生产级后端API系统，包含了企业级应用所需的所有核心功能。如需技术支持，请参考项目文档或联系开发团队。