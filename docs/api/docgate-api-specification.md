# DocGate Agent 文档质量管理系统 API 设计规范

## 1. 系统概述

DocGate Agent是Claude Enhancer 5.0的文档质量管理系统，提供自动化的文档质量检查、报告生成和配置管理功能。

### 1.1 API特性
- **RESTful设计原则** - 统一的资源定位和操作方式
- **版本控制策略** - 支持API版本演进
- **统一认证授权** - 与Claude Enhancer认证系统集成
- **完整错误处理** - 标准化错误码和消息
- **实时通知机制** - Webhook事件推送
- **高性能设计** - 支持批量操作和异步处理

### 1.2 技术栈
- **框架**: FastAPI
- **认证**: JWT + 权限系统
- **版本控制**: URL路径版本控制
- **文档**: OpenAPI 3.0 + Swagger UI
- **监控**: 请求链路追踪

## 2. API版本控制

### 2.1 版本策略
```
Base URL: https://api.claude-enhancer.com/v1
Current Version: v1.0.0
Supported Versions: v1.x.x
```

### 2.2 版本Header
```http
API-Version: v1
Accept: application/json
Content-Type: application/json
```

### 2.3 版本演进规则
- **Major (v2)**: 破坏性变更
- **Minor (v1.1)**: 新增功能，向后兼容
- **Patch (v1.0.1)**: Bug修复，向后兼容

## 3. 认证和授权

### 3.1 认证机制
```http
Authorization: Bearer <access_token>
```

### 3.2 权限系统
```yaml
权限级别:
  - docgate:read         # 查看文档质量报告
  - docgate:write        # 执行质量检查
  - docgate:config       # 管理配置
  - docgate:admin        # 完全管理权限
  - docgate:webhook      # 管理Webhook配置
```

### 3.3 API密钥（可选）
```http
X-API-Key: <api_key>  # 用于系统间调用
```

## 4. 标准响应格式

### 4.1 成功响应
```json
{
  "success": true,
  "data": {
    // 具体数据
  },
  "message": "操作成功",
  "timestamp": "2023-12-01T12:00:00Z",
  "request_id": "req_123456"
}
```

### 4.2 错误响应
```json
{
  "success": false,
  "error": {
    "code": "DOC_001",
    "type": "VALIDATION_ERROR",
    "message": "文档路径无效",
    "details": {
      "field": "document_path",
      "constraint": "must_exist"
    }
  },
  "timestamp": "2023-12-01T12:00:00Z",
  "request_id": "req_123456"
}
```

### 4.3 分页响应
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_previous": false
    }
  }
}
```

## 5. 错误码体系

### 5.1 错误码结构
```
格式: [系统][类别][序号]
示例: DOC_VAL_001
```

### 5.2 系统代码
- **DOC**: DocGate系统
- **AUT**: 认证系统
- **SYS**: 系统级错误

### 5.3 类别代码
- **VAL**: 验证错误 (400)
- **AUT**: 认证错误 (401)
- **FOR**: 权限错误 (403)
- **NOT**: 资源不存在 (404)
- **CON**: 冲突错误 (409)
- **RAT**: 频率限制 (429)
- **SER**: 服务器错误 (500)

### 5.4 常用错误码
```yaml
# 验证错误 (400)
DOC_VAL_001: "文档路径无效"
DOC_VAL_002: "配置参数格式错误"
DOC_VAL_003: "文档类型不支持"
DOC_VAL_004: "批量操作超出限制"

# 认证错误 (401)
AUT_AUT_001: "访问令牌无效"
AUT_AUT_002: "访问令牌已过期"

# 权限错误 (403)
DOC_FOR_001: "缺少文档读取权限"
DOC_FOR_002: "缺少配置管理权限"
DOC_FOR_003: "缺少Webhook管理权限"

# 资源不存在 (404)
DOC_NOT_001: "文档不存在"
DOC_NOT_002: "检查任务不存在"
DOC_NOT_003: "配置不存在"
DOC_NOT_004: "Webhook不存在"

# 冲突错误 (409)
DOC_CON_001: "检查任务正在进行中"
DOC_CON_002: "配置名称已存在"

# 频率限制 (429)
DOC_RAT_001: "质量检查请求过于频繁"
DOC_RAT_002: "Webhook调用频率超限"

# 服务器错误 (500)
DOC_SER_001: "文档解析失败"
DOC_SER_002: "质量检查服务异常"
DOC_SER_003: "报告生成失败"
```

## 6. DocGate Agent API端点

### 6.1 质量检查接口

#### 6.1.1 提交文档质量检查
```http
POST /v1/docgate/checks
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "document_source": {
    "type": "file|git|url",
    "path": "/path/to/document.md",
    "git_info": {
      "repository": "https://github.com/user/repo",
      "branch": "main",
      "commit": "abc123"
    }
  },
  "check_config": {
    "profile": "standard|strict|custom",
    "rules": {
      "grammar": true,
      "spelling": true,
      "style": true,
      "structure": true,
      "links": true,
      "images": true
    },
    "custom_rules": [
      {
        "name": "custom_rule_1",
        "enabled": true,
        "severity": "error|warning|info"
      }
    ]
  },
  "options": {
    "async": true,
    "webhook_url": "https://example.com/webhook",
    "priority": "high|normal|low",
    "timeout": 300
  }
}
```

**响应 (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "check_id": "check_123456",
    "status": "queued|running|completed|failed",
    "estimated_completion": "2023-12-01T12:05:00Z",
    "webhook_configured": true
  },
  "message": "文档质量检查已提交"
}
```

#### 6.1.2 批量文档质量检查
```http
POST /v1/docgate/checks/batch
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "documents": [
    {
      "id": "doc1",
      "source": {
        "type": "file",
        "path": "/docs/readme.md"
      }
    },
    {
      "id": "doc2",
      "source": {
        "type": "git",
        "path": "docs/api.md",
        "git_info": {
          "repository": "https://github.com/user/repo",
          "branch": "main"
        }
      }
    }
  ],
  "check_config": {
    "profile": "standard"
  },
  "options": {
    "max_concurrent": 5,
    "webhook_url": "https://example.com/webhook"
  }
}
```

#### 6.1.3 获取检查状态
```http
GET /v1/docgate/checks/{check_id}
Authorization: Bearer <token>
```

**响应:**
```json
{
  "success": true,
  "data": {
    "check_id": "check_123456",
    "status": "completed",
    "document_info": {
      "name": "readme.md",
      "size": 15234,
      "type": "markdown",
      "encoding": "utf-8"
    },
    "progress": {
      "completed_steps": 5,
      "total_steps": 5,
      "current_step": "generating_report",
      "percentage": 100
    },
    "timestamps": {
      "created_at": "2023-12-01T12:00:00Z",
      "started_at": "2023-12-01T12:00:30Z",
      "completed_at": "2023-12-01T12:03:45Z"
    },
    "summary": {
      "total_issues": 12,
      "errors": 2,
      "warnings": 8,
      "info": 2,
      "score": 85.5
    }
  }
}
```

#### 6.1.4 获取检查列表
```http
GET /v1/docgate/checks?page=1&page_size=20&status=completed&sort=created_at:desc
Authorization: Bearer <token>
```

**查询参数:**
- `page` (int): 页码，默认1
- `page_size` (int): 每页大小，默认20，最大100
- `status` (string): 过滤状态 `queued|running|completed|failed`
- `document_type` (string): 文档类型过滤
- `created_from` (datetime): 创建时间起始
- `created_to` (datetime): 创建时间结束
- `sort` (string): 排序方式 `created_at:desc|asc`

#### 6.1.5 取消检查任务
```http
DELETE /v1/docgate/checks/{check_id}
Authorization: Bearer <token>
```

### 6.2 质量报告接口

#### 6.2.1 获取详细报告
```http
GET /v1/docgate/checks/{check_id}/report
Authorization: Bearer <token>
Accept: application/json|text/html|application/pdf
```

**响应 (JSON格式):**
```json
{
  "success": true,
  "data": {
    "report_id": "report_123456",
    "check_id": "check_123456",
    "document_info": {
      "name": "readme.md",
      "path": "/project/readme.md",
      "size": 15234,
      "lines": 456,
      "words": 2340,
      "characters": 15234
    },
    "summary": {
      "overall_score": 85.5,
      "grade": "B+",
      "total_issues": 12,
      "issues_by_severity": {
        "error": 2,
        "warning": 8,
        "info": 2
      },
      "issues_by_category": {
        "grammar": 3,
        "spelling": 2,
        "style": 4,
        "structure": 2,
        "links": 1
      }
    },
    "issues": [
      {
        "id": "issue_001",
        "severity": "error",
        "category": "grammar",
        "rule": "subject_verb_agreement",
        "message": "主谓不一致",
        "description": "动词形式应与主语数量保持一致",
        "location": {
          "line": 15,
          "column": 23,
          "start_offset": 456,
          "end_offset": 468
        },
        "context": {
          "before": "The development team",
          "text": "are working",
          "after": "on the new features"
        },
        "suggestions": [
          {
            "type": "replace",
            "text": "is working",
            "confidence": 0.95
          }
        ]
      }
    ],
    "metrics": {
      "readability": {
        "flesch_reading_ease": 65.2,
        "flesch_kincaid_grade": 8.5,
        "automated_readability_index": 9.1
      },
      "structure": {
        "heading_levels": [1, 2, 3],
        "sections": 8,
        "lists": 5,
        "code_blocks": 12
      },
      "links": {
        "total": 15,
        "internal": 8,
        "external": 7,
        "broken": 1
      }
    },
    "generated_at": "2023-12-01T12:05:00Z"
  }
}
```

#### 6.2.2 下载报告文件
```http
GET /v1/docgate/checks/{check_id}/report/download?format=pdf|html|json
Authorization: Bearer <token>
```

**响应:**
- Content-Type根据格式设置
- Content-Disposition: attachment; filename="report_123456.pdf"

#### 6.2.3 获取报告历史
```http
GET /v1/docgate/reports?document_path=/project/readme.md&page=1&page_size=10
Authorization: Bearer <token>
```

### 6.3 配置管理接口

#### 6.3.1 获取检查配置列表
```http
GET /v1/docgate/configs
Authorization: Bearer <token>
```

**响应:**
```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "id": "config_001",
        "name": "standard",
        "description": "标准质量检查配置",
        "is_default": true,
        "is_system": true,
        "rules": {
          "grammar": {
            "enabled": true,
            "severity": "error",
            "options": {
              "check_passive_voice": true,
              "check_complex_sentences": true
            }
          },
          "spelling": {
            "enabled": true,
            "severity": "error",
            "custom_dictionary": []
          }
        },
        "created_at": "2023-11-01T00:00:00Z",
        "updated_at": "2023-11-15T10:30:00Z"
      }
    ]
  }
}
```

#### 6.3.2 创建检查配置
```http
POST /v1/docgate/configs
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "name": "my-custom-config",
  "description": "我的自定义配置",
  "based_on": "standard",
  "rules": {
    "grammar": {
      "enabled": true,
      "severity": "warning",
      "options": {
        "check_passive_voice": false
      }
    },
    "custom_rules": [
      {
        "name": "company_terms",
        "type": "terminology",
        "enabled": true,
        "severity": "info",
        "terms": {
          "AI": "人工智能",
          "ML": "机器学习"
        }
      }
    ]
  }
}
```

#### 6.3.3 更新检查配置
```http
PUT /v1/docgate/configs/{config_id}
Authorization: Bearer <token>
```

#### 6.3.4 删除检查配置
```http
DELETE /v1/docgate/configs/{config_id}
Authorization: Bearer <token>
```

### 6.4 Webhook通知接口

#### 6.4.1 创建Webhook配置
```http
POST /v1/docgate/webhooks
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "name": "quality-check-notifications",
  "url": "https://example.com/webhooks/docgate",
  "events": [
    "check.started",
    "check.completed",
    "check.failed",
    "report.generated"
  ],
  "filters": {
    "document_patterns": ["*.md", "docs/**"],
    "severity_threshold": "warning"
  },
  "options": {
    "retry_attempts": 3,
    "timeout": 30,
    "secret": "webhook_secret_123"
  },
  "headers": {
    "X-Custom-Header": "value"
  }
}
```

#### 6.4.2 获取Webhook列表
```http
GET /v1/docgate/webhooks
Authorization: Bearer <token>
```

#### 6.4.3 测试Webhook
```http
POST /v1/docgate/webhooks/{webhook_id}/test
Authorization: Bearer <token>
```

**Webhook事件格式:**
```json
{
  "event": "check.completed",
  "timestamp": "2023-12-01T12:05:00Z",
  "webhook_id": "webhook_123",
  "data": {
    "check_id": "check_123456",
    "document_path": "/project/readme.md",
    "status": "completed",
    "summary": {
      "total_issues": 12,
      "score": 85.5
    },
    "report_url": "https://api.claude-enhancer.com/v1/docgate/checks/check_123456/report"
  },
  "signature": "sha256=abc123..." // HMAC签名验证
}
```

### 6.5 系统管理接口

#### 6.5.1 获取系统状态
```http
GET /v1/docgate/health
Authorization: Bearer <token>
```

**响应:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "services": {
      "document_parser": "healthy",
      "quality_checker": "healthy",
      "report_generator": "healthy",
      "webhook_service": "healthy"
    },
    "metrics": {
      "checks_today": 1250,
      "avg_processing_time": 45.2,
      "success_rate": 98.5,
      "queue_length": 12
    }
  }
}
```

#### 6.5.2 获取使用统计
```http
GET /v1/docgate/stats?period=day|week|month&from=2023-11-01&to=2023-12-01
Authorization: Bearer <token>
```

## 7. 限流策略

### 7.1 限流规则
```yaml
API限流配置:
  质量检查提交:
    - 限制: 100次/小时/用户
    - 突发: 10次/分钟

  批量检查:
    - 限制: 10次/小时/用户
    - 最大文档数: 50个/批次

  报告下载:
    - 限制: 1000次/小时/用户

  Webhook调用:
    - 限制: 10000次/小时/webhook
```

### 7.2 限流响应头
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1701432000
Retry-After: 3600
```

## 8. 安全考虑

### 8.1 输入验证
- 文档路径白名单验证
- 文件大小限制 (最大50MB)
- 文件类型验证
- SQL注入防护

### 8.2 输出过滤
- 敏感信息脱敏
- XSS防护
- 路径遍历防护

### 8.3 访问控制
- 基于角色的权限控制
- 资源级别的访问控制
- 操作审计日志

## 9. 监控和日志

### 9.1 请求链路追踪
```http
X-Trace-ID: trace_123456
X-Span-ID: span_789
```

### 9.2 监控指标
- API响应时间
- 错误率统计
- 限流触发次数
- 资源使用情况

### 9.3 审计日志
```json
{
  "timestamp": "2023-12-01T12:00:00Z",
  "trace_id": "trace_123456",
  "user_id": "user_123",
  "action": "quality_check_submitted",
  "resource": "document:/project/readme.md",
  "result": "success",
  "ip_address": "192.168.1.100",
  "user_agent": "DocGate Client/1.0"
}
```

## 10. SDK和客户端

### 10.1 官方SDK
- Python SDK
- JavaScript/TypeScript SDK
- CLI工具

### 10.2 示例代码
```python
from docgate_sdk import DocGateClient

client = DocGateClient(
    api_key="your-api-key",
    base_url="https://api.claude-enhancer.com/v1"
)

# 提交质量检查
check = client.submit_check(
    document_path="/project/readme.md",
    config="standard",
    async_mode=True
)

# 获取结果
report = client.get_report(check.id)
print(f"质量评分: {report.summary.score}")
```

## 11. 部署和运维

### 11.1 环境要求
- Python 3.9+
- Redis (缓存和队列)
- PostgreSQL (数据存储)
- FastAPI + Uvicorn

### 11.2 配置管理
```yaml
# config.yaml
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4

docgate:
  max_document_size: 52428800  # 50MB
  supported_formats: ["md", "txt", "rst", "html"]
  default_timeout: 300

quality_check:
  max_concurrent_checks: 10
  report_retention_days: 90
```

### 11.3 健康检查
```http
GET /health
GET /metrics
GET /ready
```

---

**文档版本**: v1.0.0
**最后更新**: 2023-12-01
**维护者**: Claude Enhancer团队

本API设计规范基于Claude Enhancer 5.0的现有架构，提供完整的文档质量管理功能。所有接口遵循RESTful设计原则，提供统一的认证授权机制和错误处理体系。