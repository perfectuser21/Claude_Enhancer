# Claude Enhancer 5.1 - API参考文档 v1.0

## 📋 概述

Claude Enhancer 5.1 提供了完整的RESTful API，支持用户认证、任务管理、项目管理、工作流控制等核心功能。API采用现代化设计，支持JWT认证、请求限流、错误处理等企业级特性。

### API特性
- **RESTful设计** - 遵循REST架构标准
- **JWT认证** - 安全的令牌认证机制
- **请求限流** - 防止滥用的速率限制
- **错误处理** - 统一的错误响应格式
- **版本控制** - API版本化管理
- **文档化** - OpenAPI 3.0规范

### 基础信息
```
Base URL: https://api.claude-enhancer.com/v1
Content-Type: application/json
Authentication: Bearer Token (JWT)
Rate Limit: 1000 requests/hour per user
```

---

## 🔐 认证系统 API

### 用户注册

#### `POST /auth/register`

注册新用户账户。

**请求参数：**
```json
{
  "username": "string (必填, 3-50字符)",
  "email": "string (必填, 有效邮箱格式)",
  "password": "string (必填, 8-128字符)",
  "roles": ["string"] (可选, 默认: ["user"]),
  "permissions": ["string"] (可选, 默认: [])
}
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "password": "SecurePassword123!",
    "roles": ["user", "developer"]
  }'
```

**成功响应 (201 Created)：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user": {
      "user_id": 12345,
      "username": "john_doe",
      "email": "john.doe@example.com",
      "roles": ["user", "developer"],
      "permissions": [],
      "created_at": "2025-09-27T10:30:00Z",
      "is_active": true
    }
  },
  "meta": {
    "timestamp": "2025-09-27T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**错误响应示例：**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "密码不符合安全要求",
    "details": [
      "密码必须包含大写字母",
      "密码必须包含特殊字符"
    ]
  },
  "meta": {
    "timestamp": "2025-09-27T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 用户登录

#### `POST /auth/login`

用户登录获取访问令牌。

**请求参数：**
```json
{
  "email_or_username": "string (必填, 邮箱或用户名)",
  "password": "string (必填)",
  "remember_me": "boolean (可选, 默认: false)"
}
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "john.doe@example.com",
    "password": "SecurePassword123!",
    "remember_me": true
  }'
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user": {
      "user_id": 12345,
      "username": "john_doe",
      "email": "john.doe@example.com",
      "roles": ["user", "developer"],
      "permissions": []
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 86400
    }
  },
  "meta": {
    "timestamp": "2025-09-27T10:30:00Z",
    "request_id": "req_def456"
  }
}
```

### 令牌刷新

#### `POST /auth/refresh`

使用刷新令牌获取新的访问令牌。

**请求参数：**
```json
{
  "refresh_token": "string (必填)"
}
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "令牌刷新成功",
  "data": {
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### 用户登出

#### `POST /auth/logout`

用户登出，撤销令牌。

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求参数：**
```json
{
  "refresh_token": "string (可选)"
}
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 修改密码

#### `PUT /auth/password`

修改用户密码。

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求参数：**
```json
{
  "old_password": "string (必填)",
  "new_password": "string (必填, 8-128字符)"
}
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

### 获取用户信息

#### `GET /auth/me`

获取当前登录用户的详细信息。

**请求头：**
```
Authorization: Bearer {access_token}
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": 12345,
      "username": "john_doe",
      "email": "john.doe@example.com",
      "roles": ["user", "developer"],
      "permissions": [],
      "is_active": true,
      "created_at": "2025-09-27T08:00:00Z",
      "last_login": "2025-09-27T10:30:00Z",
      "failed_login_attempts": 0,
      "locked_until": null
    }
  }
}
```

---

## 📋 任务管理 API

### 获取任务列表

#### `GET /tasks`

获取用户的任务列表，支持分页和筛选。

**请求头：**
```
Authorization: Bearer {access_token}
```

**查询参数：**
```
page: integer (可选, 默认: 1)
limit: integer (可选, 默认: 20, 最大: 100)
status: string (可选, 值: pending|in_progress|completed|cancelled)
priority: string (可选, 值: low|medium|high|urgent)
project_id: integer (可选, 筛选特定项目的任务)
search: string (可选, 搜索任务标题和描述)
sort_by: string (可选, 值: created_at|updated_at|due_date|priority)
sort_order: string (可选, 值: asc|desc, 默认: desc)
```

**请求示例：**
```bash
curl -X GET "https://api.claude-enhancer.com/v1/tasks?page=1&limit=10&status=in_progress&priority=high" \
  -H "Authorization: Bearer {access_token}"
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": 101,
        "title": "实现用户认证系统",
        "description": "开发JWT认证和用户管理功能",
        "status": "in_progress",
        "priority": "high",
        "project_id": 5,
        "assignee_id": 12345,
        "assignee": {
          "user_id": 12345,
          "username": "john_doe",
          "email": "john.doe@example.com"
        },
        "created_at": "2025-09-27T09:00:00Z",
        "updated_at": "2025-09-27T10:15:00Z",
        "due_date": "2025-09-30T18:00:00Z",
        "estimated_hours": 16,
        "actual_hours": 8,
        "tags": ["backend", "security", "api"],
        "progress": 60
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 25,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 创建任务

#### `POST /tasks`

创建新任务。

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求参数：**
```json
{
  "title": "string (必填, 最大200字符)",
  "description": "string (可选, 最大2000字符)",
  "status": "string (可选, 默认: pending)",
  "priority": "string (可选, 默认: medium)",
  "project_id": "integer (可选)",
  "assignee_id": "integer (可选, 默认: 当前用户)",
  "due_date": "string (可选, ISO 8601格式)",
  "estimated_hours": "number (可选)",
  "tags": ["string"] (可选)
}
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/tasks" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "设计数据库架构",
    "description": "为用户管理系统设计PostgreSQL数据库架构",
    "priority": "high",
    "project_id": 5,
    "due_date": "2025-09-28T18:00:00Z",
    "estimated_hours": 8,
    "tags": ["database", "design", "postgresql"]
  }'
```

**成功响应 (201 Created)：**
```json
{
  "success": true,
  "message": "任务创建成功",
  "data": {
    "task": {
      "id": 102,
      "title": "设计数据库架构",
      "description": "为用户管理系统设计PostgreSQL数据库架构",
      "status": "pending",
      "priority": "high",
      "project_id": 5,
      "assignee_id": 12345,
      "created_at": "2025-09-27T10:35:00Z",
      "updated_at": "2025-09-27T10:35:00Z",
      "due_date": "2025-09-28T18:00:00Z",
      "estimated_hours": 8,
      "actual_hours": 0,
      "tags": ["database", "design", "postgresql"],
      "progress": 0
    }
  }
}
```

### 获取单个任务

#### `GET /tasks/{task_id}`

获取特定任务的详细信息。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
task_id: integer (必填, 任务ID)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": 101,
      "title": "实现用户认证系统",
      "description": "开发JWT认证和用户管理功能",
      "status": "in_progress",
      "priority": "high",
      "project_id": 5,
      "assignee_id": 12345,
      "assignee": {
        "user_id": 12345,
        "username": "john_doe",
        "email": "john.doe@example.com"
      },
      "created_at": "2025-09-27T09:00:00Z",
      "updated_at": "2025-09-27T10:15:00Z",
      "due_date": "2025-09-30T18:00:00Z",
      "estimated_hours": 16,
      "actual_hours": 8,
      "tags": ["backend", "security", "api"],
      "progress": 60,
      "comments": [
        {
          "id": 1,
          "user_id": 12345,
          "username": "john_doe",
          "content": "已完成用户注册和登录功能",
          "created_at": "2025-09-27T10:15:00Z"
        }
      ],
      "attachments": [
        {
          "id": 1,
          "filename": "auth_design.pdf",
          "file_size": 1024576,
          "content_type": "application/pdf",
          "uploaded_at": "2025-09-27T09:30:00Z"
        }
      ]
    }
  }
}
```

### 更新任务

#### `PUT /tasks/{task_id}`

更新任务信息。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
task_id: integer (必填, 任务ID)
```

**请求参数：**
```json
{
  "title": "string (可选)",
  "description": "string (可选)",
  "status": "string (可选)",
  "priority": "string (可选)",
  "assignee_id": "integer (可选)",
  "due_date": "string (可选)",
  "estimated_hours": "number (可选)",
  "actual_hours": "number (可选)",
  "progress": "number (可选, 0-100)",
  "tags": ["string"] (可选)
}
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "任务更新成功",
  "data": {
    "task": {
      "id": 101,
      "title": "实现用户认证系统",
      "status": "completed",
      "progress": 100,
      "updated_at": "2025-09-27T11:00:00Z"
    }
  }
}
```

### 删除任务

#### `DELETE /tasks/{task_id}`

删除任务。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
task_id: integer (必填, 任务ID)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "任务删除成功"
}
```

---

## 📁 项目管理 API

### 获取项目列表

#### `GET /projects`

获取用户参与的项目列表。

**请求头：**
```
Authorization: Bearer {access_token}
```

**查询参数：**
```
page: integer (可选, 默认: 1)
limit: integer (可选, 默认: 20)
status: string (可选, 值: active|completed|archived)
search: string (可选, 搜索项目名称和描述)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": 5,
        "name": "Claude Enhancer 认证系统",
        "description": "为Claude Enhancer开发用户认证和授权系统",
        "status": "active",
        "owner_id": 12345,
        "owner": {
          "user_id": 12345,
          "username": "john_doe",
          "email": "john.doe@example.com"
        },
        "created_at": "2025-09-25T08:00:00Z",
        "updated_at": "2025-09-27T10:00:00Z",
        "start_date": "2025-09-25T00:00:00Z",
        "end_date": "2025-10-15T23:59:59Z",
        "progress": 75,
        "task_count": 15,
        "completed_task_count": 10,
        "member_count": 3,
        "tags": ["authentication", "security", "backend"]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 8,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### 创建项目

#### `POST /projects`

创建新项目。

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求参数：**
```json
{
  "name": "string (必填, 最大100字符)",
  "description": "string (可选, 最大1000字符)",
  "status": "string (可选, 默认: active)",
  "start_date": "string (可选, ISO 8601格式)",
  "end_date": "string (可选, ISO 8601格式)",
  "tags": ["string"] (可选)
}
```

**成功响应 (201 Created)：**
```json
{
  "success": true,
  "message": "项目创建成功",
  "data": {
    "project": {
      "id": 6,
      "name": "前端界面开发",
      "description": "开发Claude Enhancer的用户界面",
      "status": "active",
      "owner_id": 12345,
      "created_at": "2025-09-27T11:00:00Z",
      "updated_at": "2025-09-27T11:00:00Z",
      "start_date": "2025-09-28T00:00:00Z",
      "end_date": "2025-10-20T23:59:59Z",
      "progress": 0,
      "task_count": 0,
      "completed_task_count": 0,
      "member_count": 1,
      "tags": ["frontend", "ui", "react"]
    }
  }
}
```

---

## ⚡ 工作流管理 API

### 获取工作流状态

#### `GET /workflow/status`

获取当前工作流的状态信息。

**请求头：**
```
Authorization: Bearer {access_token}
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "workflow": {
      "current_phase": "P3",
      "phase_name": "Implementation",
      "progress": 65,
      "started_at": "2025-09-27T09:00:00Z",
      "estimated_completion": "2025-09-27T16:00:00Z",
      "active_agents": [
        {
          "name": "backend-architect",
          "status": "running",
          "progress": 80,
          "started_at": "2025-09-27T09:15:00Z"
        },
        {
          "name": "security-auditor",
          "status": "running",
          "progress": 60,
          "started_at": "2025-09-27T09:20:00Z"
        }
      ],
      "completed_phases": ["P1", "P2"],
      "remaining_phases": ["P4", "P5", "P6"]
    }
  }
}
```

### 启动工作流

#### `POST /workflow/start`

启动新的工作流任务。

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求参数：**
```json
{
  "task_description": "string (必填, 任务描述)",
  "complexity": "string (可选, 值: simple|standard|complex)",
  "agent_count": "integer (可选, 4-8个Agent)",
  "project_id": "integer (可选)",
  "priority": "string (可选, 默认: medium)"
}
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/workflow/start" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "创建一个用户认证系统，包含注册、登录、JWT令牌管理等功能",
    "complexity": "standard",
    "agent_count": 6,
    "project_id": 5,
    "priority": "high"
  }'
```

**成功响应 (201 Created)：**
```json
{
  "success": true,
  "message": "工作流启动成功",
  "data": {
    "workflow": {
      "id": "wf_abc123",
      "status": "running",
      "current_phase": "P1",
      "phase_name": "Plan",
      "selected_agents": [
        "backend-architect",
        "security-auditor",
        "api-designer",
        "database-specialist",
        "test-engineer",
        "technical-writer"
      ],
      "estimated_duration": "25-30 minutes",
      "started_at": "2025-09-27T11:30:00Z"
    }
  }
}
```

### 停止工作流

#### `POST /workflow/{workflow_id}/stop`

停止正在运行的工作流。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
workflow_id: string (必填, 工作流ID)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "message": "工作流已停止",
  "data": {
    "workflow": {
      "id": "wf_abc123",
      "status": "stopped",
      "stopped_at": "2025-09-27T11:45:00Z",
      "completed_phases": ["P1", "P2"],
      "partial_results": true
    }
  }
}
```

---

## 📊 监控和统计 API

### 获取系统健康状态

#### `GET /health`

获取系统健康状态，无需认证。

**成功响应 (200 OK)：**
```json
{
  "status": "healthy",
  "version": "5.1.0",
  "timestamp": "2025-09-27T12:00:00Z",
  "uptime": 86400,
  "services": {
    "database": {
      "status": "healthy",
      "response_time": 5
    },
    "redis": {
      "status": "healthy",
      "response_time": 2
    },
    "agents": {
      "status": "healthy",
      "active_count": 3,
      "available_count": 56
    }
  },
  "metrics": {
    "memory_usage": "45%",
    "cpu_usage": "25%",
    "disk_usage": "60%"
  }
}
```

### 获取用户统计

#### `GET /dashboard/stats`

获取用户的统计信息。

**请求头：**
```
Authorization: Bearer {access_token}
```

**查询参数：**
```
period: string (可选, 值: day|week|month|year, 默认: week)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "stats": {
      "period": "week",
      "tasks": {
        "total": 25,
        "completed": 18,
        "in_progress": 5,
        "pending": 2,
        "completion_rate": 72
      },
      "projects": {
        "total": 3,
        "active": 2,
        "completed": 1
      },
      "workflows": {
        "total_executions": 12,
        "successful": 11,
        "failed": 1,
        "average_duration": "22 minutes"
      },
      "productivity": {
        "tasks_per_day": 3.6,
        "hours_worked": 42,
        "efficiency_score": 85
      }
    }
  }
}
```

---

## 🔧 Agent管理 API

### 获取可用Agent列表

#### `GET /agents`

获取所有可用的专业Agent列表。

**请求头：**
```
Authorization: Bearer {access_token}
```

**查询参数：**
```
category: string (可选, 值: frontend|backend|database|testing|security|devops)
status: string (可选, 值: available|busy|offline)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "name": "backend-architect",
        "display_name": "后端架构师",
        "category": "backend",
        "description": "专业的后端系统架构设计和开发",
        "status": "available",
        "capabilities": [
          "API设计",
          "数据库架构",
          "微服务设计",
          "性能优化"
        ],
        "usage_count": 156,
        "success_rate": 95.5,
        "average_duration": "18 minutes"
      },
      {
        "name": "security-auditor",
        "display_name": "安全审计师",
        "category": "security",
        "description": "安全漏洞检测和防护措施实施",
        "status": "available",
        "capabilities": [
          "安全扫描",
          "漏洞评估",
          "加密实现",
          "访问控制"
        ],
        "usage_count": 89,
        "success_rate": 98.2,
        "average_duration": "12 minutes"
      }
    ],
    "categories": {
      "frontend": 12,
      "backend": 15,
      "database": 6,
      "testing": 8,
      "security": 6,
      "devops": 10
    },
    "total_agents": 57
  }
}
```

### 获取Agent详细信息

#### `GET /agents/{agent_name}`

获取特定Agent的详细信息和使用历史。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
agent_name: string (必填, Agent名称)
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "agent": {
      "name": "backend-architect",
      "display_name": "后端架构师",
      "category": "backend",
      "description": "专业的后端系统架构设计和开发",
      "status": "available",
      "version": "2.1.0",
      "capabilities": [
        "API设计",
        "数据库架构",
        "微服务设计",
        "性能优化",
        "缓存策略",
        "消息队列"
      ],
      "supported_languages": [
        "Python",
        "Node.js",
        "Java",
        "Go"
      ],
      "supported_frameworks": [
        "FastAPI",
        "Django",
        "Express.js",
        "Spring Boot"
      ],
      "usage_statistics": {
        "total_executions": 156,
        "successful_executions": 149,
        "failed_executions": 7,
        "success_rate": 95.5,
        "average_duration": "18 minutes",
        "last_used": "2025-09-27T10:30:00Z"
      },
      "recent_tasks": [
        {
          "task_id": 101,
          "title": "用户认证系统设计",
          "execution_time": "16 minutes",
          "status": "completed",
          "completed_at": "2025-09-27T10:30:00Z"
        }
      ]
    }
  }
}
```

---

## 📄 文件管理 API

### 上传文件

#### `POST /files/upload`

上传文件到系统。

**请求头：**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求参数：**
```
file: file (必填, 最大50MB)
task_id: integer (可选, 关联的任务ID)
project_id: integer (可选, 关联的项目ID)
description: string (可选, 文件描述)
```

**请求示例：**
```bash
curl -X POST "https://api.claude-enhancer.com/v1/files/upload" \
  -H "Authorization: Bearer {access_token}" \
  -F "file=@requirements.txt" \
  -F "task_id=101" \
  -F "description=项目依赖文件"
```

**成功响应 (201 Created)：**
```json
{
  "success": true,
  "message": "文件上传成功",
  "data": {
    "file": {
      "id": 201,
      "filename": "requirements.txt",
      "original_filename": "requirements.txt",
      "file_size": 2048,
      "content_type": "text/plain",
      "url": "https://files.claude-enhancer.com/uploads/user_12345/requirements_20250927.txt",
      "task_id": 101,
      "project_id": null,
      "description": "项目依赖文件",
      "uploaded_at": "2025-09-27T12:30:00Z",
      "uploaded_by": 12345
    }
  }
}
```

### 下载文件

#### `GET /files/{file_id}/download`

下载文件。

**请求头：**
```
Authorization: Bearer {access_token}
```

**路径参数：**
```
file_id: integer (必填, 文件ID)
```

**成功响应：**
- 返回文件内容，Content-Type根据文件类型设置
- Content-Disposition: attachment; filename="原始文件名"

---

## 🔍 搜索 API

### 全局搜索

#### `GET /search`

在任务、项目、文件中进行全局搜索。

**请求头：**
```
Authorization: Bearer {access_token}
```

**查询参数：**
```
q: string (必填, 搜索关键词)
type: string (可选, 值: all|tasks|projects|files, 默认: all)
page: integer (可选, 默认: 1)
limit: integer (可选, 默认: 20)
```

**请求示例：**
```bash
curl -X GET "https://api.claude-enhancer.com/v1/search?q=认证系统&type=all&page=1&limit=10" \
  -H "Authorization: Bearer {access_token}"
```

**成功响应 (200 OK)：**
```json
{
  "success": true,
  "data": {
    "results": {
      "tasks": [
        {
          "id": 101,
          "title": "实现用户认证系统",
          "description": "开发JWT认证和用户管理功能",
          "type": "task",
          "relevance_score": 0.95
        }
      ],
      "projects": [
        {
          "id": 5,
          "name": "Claude Enhancer 认证系统",
          "description": "为Claude Enhancer开发用户认证和授权系统",
          "type": "project",
          "relevance_score": 0.88
        }
      ],
      "files": [
        {
          "id": 201,
          "filename": "auth_design.pdf",
          "description": "认证系统设计文档",
          "type": "file",
          "relevance_score": 0.75
        }
      ]
    },
    "summary": {
      "total_results": 3,
      "tasks_count": 1,
      "projects_count": 1,
      "files_count": 1
    },
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 3,
      "total_pages": 1
    }
  }
}
```

---

## 📋 错误代码和处理

### HTTP状态码

| 状态码 | 说明 | 用途 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或令牌无效 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 请求格式正确但数据无效 |
| 429 | Too Many Requests | 请求频率超限 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务暂不可用 |

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": ["详细错误信息1", "详细错误信息2"]
  },
  "meta": {
    "timestamp": "2025-09-27T12:00:00Z",
    "request_id": "req_xyz789",
    "documentation_url": "https://docs.claude-enhancer.com/api/errors#ERROR_CODE"
  }
}
```

### 常见错误代码

#### 认证相关错误
```
INVALID_CREDENTIALS     - 用户名或密码错误
TOKEN_EXPIRED          - 访问令牌已过期
TOKEN_INVALID          - 令牌格式错误或无效
ACCOUNT_LOCKED         - 账户已被锁定
ACCOUNT_DISABLED       - 账户已被禁用
INSUFFICIENT_PERMISSIONS - 权限不足
```

#### 验证相关错误
```
VALIDATION_ERROR       - 请求参数验证失败
MISSING_REQUIRED_FIELD - 缺少必填字段
INVALID_FORMAT         - 字段格式错误
WEAK_PASSWORD          - 密码强度不足
EMAIL_EXISTS           - 邮箱已被注册
USERNAME_EXISTS        - 用户名已存在
```

#### 资源相关错误
```
RESOURCE_NOT_FOUND     - 资源不存在
RESOURCE_CONFLICT      - 资源冲突
RESOURCE_LIMIT_EXCEEDED - 资源数量超限
FILE_TOO_LARGE         - 文件大小超限
UNSUPPORTED_FILE_TYPE  - 不支持的文件类型
```

#### 系统相关错误
```
RATE_LIMIT_EXCEEDED    - 请求频率超限
SERVICE_UNAVAILABLE    - 服务暂时不可用
AGENT_BUSY             - Agent正忙
WORKFLOW_ERROR         - 工作流执行错误
DATABASE_ERROR         - 数据库错误
CACHE_ERROR            - 缓存错误
```

---

## 🔒 安全和最佳实践

### API安全

#### 1. 认证和授权
- 所有API端点（除/health外）都需要有效的JWT令牌
- 令牌在请求头中以Bearer格式传递
- 令牌有效期为1小时，可通过刷新令牌延长
- 支持基于角色的权限控制（RBAC）

#### 2. 输入验证
- 所有用户输入都经过严格验证和清理
- 防止SQL注入、XSS和其他代码注入攻击
- 文件上传类型和大小限制
- 请求参数长度和格式验证

#### 3. 速率限制
```
用户级别限制:
- 认证API: 10 requests/minute
- 普通API: 1000 requests/hour
- 文件上传: 50 requests/hour

IP级别限制:
- 全局: 5000 requests/hour
- 认证尝试: 50 requests/hour
```

#### 4. HTTPS和加密
- 所有生产环境强制使用HTTPS
- 敏感数据传输加密
- 密码使用bcrypt哈希存储
- 数据库连接加密

### 最佳实践

#### 1. 错误处理
```javascript
// 推荐的错误处理方式
try {
  const response = await fetch('/api/v1/tasks', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(taskData)
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.error.message);

    // 根据错误类型处理
    switch (error.error.code) {
      case 'TOKEN_EXPIRED':
        // 刷新令牌或重新登录
        break;
      case 'VALIDATION_ERROR':
        // 显示表单验证错误
        break;
      default:
        // 显示通用错误消息
    }
    return;
  }

  const data = await response.json();
  console.log('Success:', data);
} catch (error) {
  console.error('Network Error:', error);
}
```

#### 2. 令牌管理
```javascript
// 自动令牌刷新示例
class APIClient {
  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  async request(url, options = {}) {
    let response = await this.makeRequest(url, options);

    // 如果令牌过期，尝试刷新
    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        response = await this.makeRequest(url, options);
      }
    }

    return response;
  }

  async refreshAccessToken() {
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.accessToken = data.data.tokens.access_token;
        localStorage.setItem('access_token', this.accessToken);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    // 刷新失败，重定向到登录页
    window.location.href = '/login';
    return false;
  }
}
```

#### 3. 分页处理
```javascript
// 分页数据处理示例
async function loadTasks(page = 1, limit = 20) {
  const response = await apiClient.request(
    `/api/v1/tasks?page=${page}&limit=${limit}`
  );

  if (response.ok) {
    const data = await response.json();
    return {
      tasks: data.data.tasks,
      pagination: data.data.pagination,
      hasMore: data.data.pagination.has_next
    };
  }

  throw new Error('Failed to load tasks');
}

// 无限滚动实现
class TaskList {
  constructor() {
    this.tasks = [];
    this.currentPage = 1;
    this.loading = false;
  }

  async loadMore() {
    if (this.loading) return;

    this.loading = true;
    try {
      const result = await loadTasks(this.currentPage);
      this.tasks.push(...result.tasks);
      this.currentPage++;
      return result.hasMore;
    } finally {
      this.loading = false;
    }
  }
}
```

---

## 📊 API使用示例

### 完整工作流示例

以下是一个完整的用户认证和任务创建流程：

```javascript
// 1. 用户注册
async function registerUser() {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'developer',
      email: 'dev@example.com',
      password: 'SecurePass123!',
      roles: ['user', 'developer']
    })
  });

  return response.json();
}

// 2. 用户登录
async function loginUser() {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email_or_username: 'dev@example.com',
      password: 'SecurePass123!',
      remember_me: true
    })
  });

  const data = await response.json();
  if (data.success) {
    localStorage.setItem('access_token', data.data.tokens.access_token);
    localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
  }

  return data;
}

// 3. 创建项目
async function createProject() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/projects', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Web应用开发',
      description: '开发现代化的Web应用程序',
      start_date: '2025-09-28T00:00:00Z',
      end_date: '2025-12-31T23:59:59Z',
      tags: ['web', 'fullstack', 'react']
    })
  });

  return response.json();
}

// 4. 启动工作流
async function startWorkflow(projectId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/workflow/start', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      task_description: '创建用户认证系统，包含注册、登录、权限管理功能',
      complexity: 'standard',
      agent_count: 6,
      project_id: projectId,
      priority: 'high'
    })
  });

  return response.json();
}

// 5. 监控工作流进度
async function monitorWorkflow() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/workflow/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();
  if (data.success) {
    console.log(`当前阶段: ${data.data.workflow.phase_name}`);
    console.log(`进度: ${data.data.workflow.progress}%`);
    console.log(`活跃Agent: ${data.data.workflow.active_agents.length}个`);
  }

  return data;
}

// 执行完整流程
async function fullWorkflow() {
  try {
    // 注册用户
    console.log('1. 注册用户...');
    await registerUser();

    // 登录
    console.log('2. 用户登录...');
    await loginUser();

    // 创建项目
    console.log('3. 创建项目...');
    const project = await createProject();

    // 启动工作流
    console.log('4. 启动工作流...');
    await startWorkflow(project.data.project.id);

    // 监控进度
    console.log('5. 监控工作流进度...');
    const interval = setInterval(async () => {
      const status = await monitorWorkflow();
      if (status.data.workflow.current_phase === 'P6' &&
          status.data.workflow.progress === 100) {
        console.log('工作流完成！');
        clearInterval(interval);
      }
    }, 30000); // 每30秒检查一次

  } catch (error) {
    console.error('工作流执行失败:', error);
  }
}
```

---

## 📚 SDK和工具

### JavaScript/TypeScript SDK

```typescript
// Claude Enhancer API客户端
import { ClaudeEnhancerAPI } from '@claude-enhancer/api-client';

const api = new ClaudeEnhancerAPI({
  baseUrl: 'https://api.claude-enhancer.com/v1',
  apiKey: 'your-api-key', // 可选，用于服务端到服务端调用
  timeout: 30000
});

// 使用示例
async function example() {
  // 登录获取令牌
  const auth = await api.auth.login({
    email_or_username: 'user@example.com',
    password: 'password123'
  });

  // 设置访问令牌
  api.setAccessToken(auth.data.tokens.access_token);

  // 创建任务
  const task = await api.tasks.create({
    title: '开发新功能',
    description: '实现用户dashboard',
    priority: 'high',
    due_date: '2025-09-30T18:00:00Z'
  });

  // 启动工作流
  const workflow = await api.workflow.start({
    task_description: '创建React组件库',
    complexity: 'standard'
  });

  console.log('任务创建成功:', task.data.task.id);
  console.log('工作流启动:', workflow.data.workflow.id);
}
```

### Python SDK

```python
# Claude Enhancer Python客户端
from claude_enhancer import ClaudeEnhancerAPI

api = ClaudeEnhancerAPI(
    base_url='https://api.claude-enhancer.com/v1',
    timeout=30
)

# 使用示例
async def example():
    # 登录
    auth_result = await api.auth.login(
        email_or_username='user@example.com',
        password='password123'
    )

    # 设置访问令牌
    api.set_access_token(auth_result.data.tokens.access_token)

    # 获取任务列表
    tasks = await api.tasks.list(
        status='in_progress',
        limit=10
    )

    # 创建新任务
    new_task = await api.tasks.create({
        'title': '数据库优化',
        'description': '优化查询性能',
        'priority': 'medium'
    })

    print(f"找到 {len(tasks.data.tasks)} 个进行中的任务")
    print(f"创建了新任务: {new_task.data.task.id}")
```

### cURL命令工具

```bash
#!/bin/bash
# Claude Enhancer API 命令行工具

# 设置基础变量
BASE_URL="https://api.claude-enhancer.com/v1"
ACCESS_TOKEN=""

# 登录函数
function ce_login() {
    local email=$1
    local password=$2

    response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email_or_username\":\"$email\",\"password\":\"$password\"}")

    ACCESS_TOKEN=$(echo $response | jq -r '.data.tokens.access_token')
    echo "登录成功，令牌已保存"
}

# 获取任务列表
function ce_tasks() {
    curl -s -X GET "$BASE_URL/tasks" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
}

# 创建任务
function ce_create_task() {
    local title=$1
    local description=$2

    curl -s -X POST "$BASE_URL/tasks" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"title\":\"$title\",\"description\":\"$description\"}" | jq '.'
}

# 使用示例
# ce_login "user@example.com" "password123"
# ce_tasks
# ce_create_task "新任务" "任务描述"
```

---

## 📞 技术支持

### 获取帮助

#### 官方资源
- 📖 [完整API文档](https://docs.claude-enhancer.com/api)
- 🎓 [API使用教程](https://learn.claude-enhancer.com/api)
- 📊 [交互式API测试](https://api.claude-enhancer.com/docs)
- 🔧 [SDK下载](https://github.com/claude-enhancer/sdks)

#### 社区支持
- 💬 [开发者论坛](https://forum.claude-enhancer.com/api)
- 🐛 [问题反馈](https://github.com/claude-enhancer/api/issues)
- 💡 [功能建议](https://github.com/claude-enhancer/api/discussions)
- 📧 [邮件支持](mailto:api-support@claude-enhancer.com)

#### 企业支持
- 🏢 [企业API支持](mailto:enterprise-api@claude-enhancer.com)
- 📞 **API技术热线**: +1-800-API-HELP
- 💼 [专业集成服务](https://claude-enhancer.com/integration-services)
- 🎯 [SLA保障](https://claude-enhancer.com/api-sla)

### 版本和变更

#### API版本控制
- **当前版本**: v1.0
- **支持的版本**: v1.x
- **废弃通知**: 提前6个月通知
- **向后兼容**: 遵循语义化版本控制

#### 变更通知
- 📧 [API变更订阅](https://claude-enhancer.com/api-changelog-subscribe)
- 🔔 [Webhook通知](https://docs.claude-enhancer.com/api/webhooks)
- 📱 [移动App通知](https://app.claude-enhancer.com/notifications)

---

**Claude Enhancer 5.1 API** - 强大、安全、易用的AI驱动开发API
*Professional API for AI-driven development workflows*

🚀 **开始您的API集成之旅！查看我们的[快速开始指南](QUICK_START.md)获取更多信息。**