# Claude Enhancer 5.1 API 参考文档

## 📖 概述

Claude Enhancer 5.1 提供了完整的 REST API 接口，支持系统监控、性能分析、错误恢复和工作流管理。本文档详细描述了所有可用的API端点和使用方法。

### API基础信息
- **基础URL**: `http://localhost:8080/api/v1`
- **认证方式**: API Key (Header: `X-API-Key`)
- **数据格式**: JSON
- **版本**: v1.0 (Claude Enhancer 5.1)

### 新增功能
- 🆕 实时监控API
- 🆕 性能分析API
- 🆕 错误恢复API
- 🆕 自检优化API
- 🆕 资源管理API

## 🏥 系统监控 API

### 获取系统健康状态
获取系统整体健康状况和运行指标。

```http
GET /api/v1/health
```

#### 响应示例
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:30:00Z",
  "version": "5.1.0",
  "uptime": 3600000,
  "system": {
    "cpu": {
      "usage": 45.2,
      "cores": 8,
      "loadAverage": [1.2, 1.5, 1.8]
    },
    "memory": {
      "used": 134217728,
      "total": 8589934592,
      "percentage": 1.56,
      "available": 8455716864
    },
    "disk": {
      "used": 5368709120,
      "total": 107374182400,
      "percentage": 5.0
    }
  },
  "services": {
    "hookSystem": "running",
    "agentPool": "healthy",
    "workflowEngine": "active",
    "monitoring": "active"
  }
}
```

#### 状态码
- `200 OK` - 系统健康
- `503 Service Unavailable` - 系统异常

### 获取详细性能指标
获取详细的系统性能指标和历史数据。

```http
GET /api/v1/metrics
```

#### 查询参数
| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `timeframe` | string | 时间范围 (1h, 6h, 24h, 7d) | 1h |
| `resolution` | string | 数据分辨率 (1m, 5m, 1h) | 5m |
| `metrics` | string | 指标类型 (cpu,memory,disk,network) | all |

#### 响应示例
```json
{
  "timeframe": "1h",
  "resolution": "5m",
  "data": {
    "cpu": [
      {
        "timestamp": "2025-01-26T10:00:00Z",
        "usage": 42.1,
        "user": 35.2,
        "system": 6.9,
        "idle": 57.9
      }
    ],
    "memory": [
      {
        "timestamp": "2025-01-26T10:00:00Z",
        "used": 128974848,
        "cached": 2147483648,
        "buffers": 134217728,
        "available": 8321499136
      }
    ],
    "performance": {
      "responseTime": {
        "avg": 145,
        "p50": 120,
        "p95": 280,
        "p99": 450
      },
      "throughput": {
        "requests": 1247,
        "errors": 3,
        "errorRate": 0.24
      }
    }
  }
}
```

## 🤖 Agent管理 API

### 获取Agent状态
查看所有Agent的运行状态和性能指标。

```http
GET /api/v1/agents
```

#### 响应示例
```json
{
  "totalAgents": 56,
  "activeAgents": 8,
  "agents": {
    "backend-architect": {
      "status": "active",
      "tasks": 3,
      "avgResponseTime": 1200,
      "successRate": 98.5,
      "lastUsed": "2025-01-26T10:25:00Z"
    },
    "api-designer": {
      "status": "idle",
      "tasks": 0,
      "avgResponseTime": 950,
      "successRate": 99.2,
      "lastUsed": "2025-01-26T09:45:00Z"
    }
  },
  "strategies": {
    "simple": {
      "recommendedAgents": 4,
      "avgDuration": "5-10分钟",
      "usage": 245
    },
    "standard": {
      "recommendedAgents": 6,
      "avgDuration": "15-20分钟",
      "usage": 178
    },
    "complex": {
      "recommendedAgents": 8,
      "avgDuration": "25-30分钟",
      "usage": 89
    }
  }
}
```

### 智能Agent选择
基于任务描述智能推荐Agent组合。

```http
POST /api/v1/agents/recommend
Content-Type: application/json
```

#### 请求体
```json
{
  "task": "创建用户认证系统，包含JWT令牌和权限控制",
  "complexity": "auto",
  "preferences": {
    "prioritize": ["security", "performance"],
    "exclude": ["legacy-support"]
  }
}
```

#### 响应示例
```json
{
  "taskAnalysis": {
    "complexity": "standard",
    "score": 6,
    "keywords": ["authentication", "jwt", "security", "authorization"],
    "estimatedDuration": "15-20分钟"
  },
  "recommendation": {
    "strategy": "standard",
    "agentCount": 6,
    "agents": [
      {
        "name": "backend-architect",
        "role": "架构设计",
        "priority": 1,
        "reason": "JWT和认证架构设计"
      },
      {
        "name": "security-auditor",
        "role": "安全审计",
        "priority": 1,
        "reason": "认证系统安全检查"
      },
      {
        "name": "api-designer",
        "role": "API设计",
        "priority": 2,
        "reason": "认证接口设计"
      },
      {
        "name": "database-specialist",
        "role": "数据建模",
        "priority": 2,
        "reason": "用户和权限数据模型"
      },
      {
        "name": "test-engineer",
        "role": "测试工程",
        "priority": 3,
        "reason": "认证流程测试"
      },
      {
        "name": "technical-writer",
        "role": "文档编写",
        "priority": 3,
        "reason": "API文档和使用说明"
      }
    ]
  },
  "alternatives": [
    {
      "name": "简化版本",
      "agentCount": 4,
      "excludeAgents": ["database-specialist", "technical-writer"]
    }
  ]
}
```

## 🔧 工作流管理 API

### 获取当前工作流状态
查看当前项目的工作流阶段和进度。

```http
GET /api/v1/workflow/status
```

#### 响应示例
```json
{
  "currentPhase": "P3",
  "phaseName": "Implementation",
  "progress": 65.5,
  "startTime": "2025-01-26T09:00:00Z",
  "estimatedCompletion": "2025-01-26T10:45:00Z",
  "phases": {
    "P0": {
      "name": "Branch Creation",
      "status": "completed",
      "duration": 120,
      "completedAt": "2025-01-26T09:02:00Z"
    },
    "P1": {
      "name": "Requirements Analysis",
      "status": "completed",
      "duration": 300,
      "completedAt": "2025-01-26T09:07:00Z"
    },
    "P2": {
      "name": "Design Planning",
      "status": "completed",
      "duration": 600,
      "completedAt": "2025-01-26T09:17:00Z"
    },
    "P3": {
      "name": "Implementation",
      "status": "in_progress",
      "duration": 1800,
      "startedAt": "2025-01-26T09:17:00Z",
      "activeAgents": [
        "backend-architect",
        "api-designer",
        "database-specialist",
        "security-auditor"
      ]
    }
  }
}
```

### 手动推进工作流阶段
手动推进到下一个工作流阶段。

```http
POST /api/v1/workflow/advance
Content-Type: application/json
```

#### 请求体
```json
{
  "targetPhase": "P4",
  "force": false,
  "reason": "Implementation completed successfully"
}
```

#### 响应示例
```json
{
  "success": true,
  "previousPhase": "P3",
  "currentPhase": "P4",
  "message": "工作流已推进到P4阶段：Local Testing",
  "nextSteps": [
    "运行单元测试",
    "执行集成测试",
    "进行性能验证",
    "检查代码覆盖率"
  ]
}
```

## 🛠️ Hook系统 API

### 获取Hook执行状态
查看所有Hook的执行状态和性能信息。

```http
GET /api/v1/hooks/status
```

#### 响应示例
```json
{
  "totalHooks": 12,
  "activeHooks": 8,
  "avgExecutionTime": 145,
  "successRate": 99.2,
  "hooks": {
    "PreToolUse": [
      {
        "name": "system_health_check",
        "description": "系统健康检查",
        "status": "enabled",
        "executions": 1247,
        "avgTime": 85,
        "successRate": 100,
        "lastExecution": "2025-01-26T10:29:45Z"
      },
      {
        "name": "smart_agent_selector_v2",
        "description": "增强Agent选择策略",
        "status": "enabled",
        "executions": 89,
        "avgTime": 1200,
        "successRate": 98.9,
        "lastExecution": "2025-01-26T10:15:30Z"
      }
    ],
    "PostToolUse": [
      {
        "name": "performance_monitor",
        "description": "性能监控和优化",
        "status": "enabled",
        "executions": 2456,
        "avgTime": 45,
        "successRate": 99.8,
        "lastExecution": "2025-01-26T10:29:58Z"
      }
    ]
  }
}
```

### 手动执行Hook
手动触发特定Hook的执行。

```http
POST /api/v1/hooks/execute
Content-Type: application/json
```

#### 请求体
```json
{
  "hookName": "system_health_check",
  "parameters": {
    "detailed": true,
    "includeHistory": false
  }
}
```

#### 响应示例
```json
{
  "success": true,
  "hookName": "system_health_check",
  "executionTime": 87,
  "result": {
    "status": "healthy",
    "cpu": 42.1,
    "memory": 58.3,
    "disk": 12.7,
    "warnings": [],
    "recommendations": [
      "系统运行正常，无需优化"
    ]
  }
}
```

## 🚨 错误恢复 API

### 获取错误恢复状态
查看错误恢复系统的状态和历史记录。

```http
GET /api/v1/recovery/status
```

#### 响应示例
```json
{
  "system": {
    "status": "active",
    "totalRecoveries": 23,
    "successRate": 95.7,
    "lastRecovery": "2025-01-26T09:45:12Z"
  },
  "strategies": {
    "hook_failure": {
      "attempts": 8,
      "successes": 8,
      "avgRecoveryTime": 250
    },
    "memory_exhausted": {
      "attempts": 12,
      "successes": 11,
      "avgRecoveryTime": 500
    },
    "agent_communication_failed": {
      "attempts": 3,
      "successes": 3,
      "avgRecoveryTime": 1200
    }
  },
  "recentRecoveries": [
    {
      "timestamp": "2025-01-26T09:45:12Z",
      "errorType": "hook_failure",
      "hookName": "smart_agent_selector",
      "recoveryAction": "hook_restart",
      "success": true,
      "recoveryTime": 245
    }
  ]
}
```

### 手动触发错误恢复
手动触发特定类型的错误恢复。

```http
POST /api/v1/recovery/trigger
Content-Type: application/json
```

#### 请求体
```json
{
  "errorType": "memory_exhausted",
  "force": false,
  "parameters": {
    "aggressiveCleanup": true
  }
}
```

#### 响应示例
```json
{
  "success": true,
  "errorType": "memory_exhausted",
  "recoveryAction": "garbage_collection",
  "recoveryTime": 450,
  "result": {
    "memoryFreed": "64MB",
    "processingTime": 450,
    "recommendations": [
      "考虑增加系统内存",
      "优化内存使用模式"
    ]
  }
}
```

## 📊 性能分析 API

### 获取性能基准测试结果
运行性能基准测试并获取结果。

```http
POST /api/v1/performance/benchmark
Content-Type: application/json
```

#### 请求体
```json
{
  "testSuite": "comprehensive",
  "duration": 300,
  "concurrency": 10,
  "scenarios": [
    "hook_execution",
    "agent_selection",
    "workflow_progression",
    "error_recovery"
  ]
}
```

#### 响应示例
```json
{
  "testId": "bench_20250126_103000",
  "status": "completed",
  "duration": 300,
  "summary": {
    "totalTests": 4,
    "totalRequests": 12450,
    "successRate": 99.8,
    "avgResponseTime": 145,
    "throughput": 41.5
  },
  "scenarios": {
    "hook_execution": {
      "requests": 4500,
      "avgTime": 85,
      "p95Time": 150,
      "errorRate": 0.1,
      "score": 95.2
    },
    "agent_selection": {
      "requests": 450,
      "avgTime": 1200,
      "p95Time": 2100,
      "errorRate": 0.2,
      "score": 87.5
    },
    "workflow_progression": {
      "requests": 150,
      "avgTime": 2500,
      "p95Time": 4200,
      "errorRate": 0.0,
      "score": 92.1
    },
    "error_recovery": {
      "requests": 75,
      "avgTime": 680,
      "p95Time": 1200,
      "errorRate": 5.0,
      "score": 78.9
    }
  },
  "recommendations": [
    "Agent选择算法可以进一步优化",
    "错误恢复机制需要改进",
    "整体性能表现良好"
  ]
}
```

### 获取实时性能数据
获取实时的系统性能数据流。

```http
GET /api/v1/performance/realtime
```

**WebSocket连接**
```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/performance/realtime');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('实时性能数据:', data);
};
```

#### WebSocket消息格式
```json
{
  "timestamp": "2025-01-26T10:30:15Z",
  "cpu": 42.1,
  "memory": 58.3,
  "disk": 12.7,
  "network": {
    "bytesIn": 1024000,
    "bytesOut": 2048000
  },
  "hooks": {
    "activeCount": 3,
    "avgExecutionTime": 125
  },
  "agents": {
    "activeCount": 4,
    "queueLength": 2
  }
}
```

## 🔧 配置管理 API

### 获取系统配置
获取当前的系统配置信息。

```http
GET /api/v1/config
```

#### 响应示例
```json
{
  "version": "5.1.0",
  "project": "Claude Enhancer 5.1 - Self-Optimization System",
  "features": {
    "lazyLoading": true,
    "selfOptimization": true,
    "realTimeMonitoring": true,
    "errorRecovery": true
  },
  "thresholds": {
    "cpu": 80,
    "memory": 85,
    "disk": 90,
    "responseTime": 5000
  },
  "limits": {
    "maxConcurrentHooks": 12,
    "maxConcurrentAgents": 16,
    "hookTimeout": 5000,
    "agentTimeout": 30000
  }
}
```

### 更新系统配置
更新系统配置参数。

```http
PATCH /api/v1/config
Content-Type: application/json
```

#### 请求体
```json
{
  "thresholds": {
    "cpu": 85,
    "memory": 80
  },
  "limits": {
    "hookTimeout": 6000
  },
  "features": {
    "selfOptimization": true
  }
}
```

#### 响应示例
```json
{
  "success": true,
  "updated": [
    "thresholds.cpu",
    "thresholds.memory",
    "limits.hookTimeout",
    "features.selfOptimization"
  ],
  "restartRequired": false,
  "message": "配置更新成功"
}
```

## 📱 WebSocket API

### 实时事件流
连接到实时事件流，接收系统事件通知。

```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/events');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'hook_executed':
            console.log('Hook执行:', data.payload);
            break;
        case 'agent_selected':
            console.log('Agent选择:', data.payload);
            break;
        case 'workflow_advanced':
            console.log('工作流推进:', data.payload);
            break;
        case 'error_recovered':
            console.log('错误恢复:', data.payload);
            break;
    }
};
```

#### 事件类型

##### Hook执行事件
```json
{
  "type": "hook_executed",
  "timestamp": "2025-01-26T10:30:00Z",
  "payload": {
    "hookName": "system_health_check",
    "executionTime": 87,
    "success": true,
    "result": {...}
  }
}
```

##### Agent选择事件
```json
{
  "type": "agent_selected",
  "timestamp": "2025-01-26T10:30:00Z",
  "payload": {
    "task": "创建用户认证系统",
    "complexity": "standard",
    "selectedAgents": [
      "backend-architect",
      "security-auditor",
      "api-designer"
    ],
    "estimatedDuration": 1200
  }
}
```

##### 工作流推进事件
```json
{
  "type": "workflow_advanced",
  "timestamp": "2025-01-26T10:30:00Z",
  "payload": {
    "fromPhase": "P2",
    "toPhase": "P3",
    "phaseName": "Implementation",
    "progress": 37.5,
    "estimatedCompletion": "2025-01-26T11:15:00Z"
  }
}
```

## 🔐 认证和授权

### API密钥认证
所有API请求需要在请求头中包含有效的API密钥。

```http
X-API-Key: your-api-key-here
```

### 获取API密钥
```http
POST /api/v1/auth/apikey
Content-Type: application/json
```

#### 请求体
```json
{
  "name": "我的API密钥",
  "permissions": [
    "read:metrics",
    "read:status",
    "write:config",
    "execute:hooks"
  ],
  "expiresIn": "30d"
}
```

#### 响应示例
```json
{
  "apiKey": "ce51_abc123def456ghi789jkl012mno345",
  "name": "我的API密钥",
  "permissions": ["read:metrics", "read:status", "write:config", "execute:hooks"],
  "createdAt": "2025-01-26T10:30:00Z",
  "expiresAt": "2025-02-25T10:30:00Z"
}
```

### 权限说明
- `read:metrics` - 读取性能指标
- `read:status` - 读取系统状态
- `read:config` - 读取配置信息
- `write:config` - 修改配置
- `execute:hooks` - 执行Hook
- `manage:workflow` - 管理工作流
- `admin:*` - 管理员权限

## 🚀 SDK和客户端库

### Node.js SDK
```bash
npm install claude-enhancer-sdk
```

```javascript
const { ClaudeEnhancerClient } = require('claude-enhancer-sdk');

const client = new ClaudeEnhancerClient({
  baseUrl: 'http://localhost:8080',
  apiKey: 'your-api-key'
});

// 获取系统健康状态
const health = await client.getHealth();

// 获取性能指标
const metrics = await client.getMetrics({ timeframe: '1h' });

// 智能Agent选择
const recommendation = await client.recommendAgents({
  task: '创建用户认证系统'
});
```

### Python SDK
```bash
pip install claude-enhancer-python
```

```python
from claude_enhancer import ClaudeEnhancerClient

client = ClaudeEnhancerClient(
    base_url='http://localhost:8080',
    api_key='your-api-key'
)

# 获取系统健康状态
health = client.get_health()

# 获取性能指标
metrics = client.get_metrics(timeframe='1h')

# 智能Agent选择
recommendation = client.recommend_agents(
    task='创建用户认证系统'
)
```

## 📋 错误码参考

### 通用错误码
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - API密钥无效或缺失
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `429 Too Many Requests` - 请求频率超限
- `500 Internal Server Error` - 服务器内部错误
- `503 Service Unavailable` - 服务不可用

### 业务错误码
- `1001` - Hook执行失败
- `1002` - Agent选择失败
- `1003` - 工作流状态异常
- `1004` - 配置验证失败
- `1005` - 性能测试失败
- `1006` - 错误恢复失败

### 错误响应格式
```json
{
  "error": {
    "code": 1001,
    "message": "Hook执行失败",
    "details": "system_health_check hook timeout after 5000ms",
    "timestamp": "2025-01-26T10:30:00Z",
    "requestId": "req_abc123"
  }
}
```

## 📈 API使用限制

### 速率限制
- **一般API**: 每分钟100次请求
- **监控API**: 每分钟500次请求
- **WebSocket**: 每个连接最多100个订阅

### 数据限制
- **请求体大小**: 最大1MB
- **响应数据**: 最大10MB
- **历史数据**: 最多保留30天

## 🔄 版本兼容性

### API版本控制
- **当前版本**: v1.0
- **兼容版本**: v1.x
- **弃用策略**: 提前6个月通知

### 版本升级
```http
# 使用特定版本
GET /api/v1/health

# 使用最新版本
GET /api/latest/health
```

---

**Claude Enhancer 5.1 API 参考文档**
*版本: v1.0 | 更新时间: 2025-01-26*

如需更多信息，请访问：
- 📚 [完整文档](https://docs.claude-enhancer.com/api/)
- 🛠️ [SDK下载](https://github.com/claude-enhancer/sdks)
- 💬 [技术支持](https://support.claude-enhancer.com)