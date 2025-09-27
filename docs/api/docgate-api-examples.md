# DocGate Agent API 使用示例

这个文档提供了DocGate Agent API的完整使用示例，包括Python SDK、cURL命令和JavaScript客户端代码。

## 目录
1. [认证设置](#认证设置)
2. [基础质量检查](#基础质量检查)
3. [批量文档检查](#批量文档检查)
4. [获取检查结果](#获取检查结果)
5. [下载报告](#下载报告)
6. [配置管理](#配置管理)
7. [Webhook设置](#webhook设置)
8. [系统监控](#系统监控)
9. [错误处理](#错误处理)

## 认证设置

### 获取访问令牌
```bash
# 登录获取访问令牌
curl -X POST "https://api.claude-enhancer.com/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

### 使用访问令牌
```bash
# 在后续请求中使用令牌
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     "https://api.claude-enhancer.com/v1/docgate/health"
```

## 基础质量检查

### 1. 提交单个文档检查

#### Python SDK
```python
from docgate_sdk import DocGateClient

# 初始化客户端
client = DocGateClient(
    access_token="your_access_token",
    base_url="https://api.claude-enhancer.com/v1"
)

# 提交质量检查
check_request = {
    "document_source": {
        "type": "file",
        "path": "/project/docs/readme.md",
        "encoding": "utf-8"
    },
    "check_config": {
        "profile": "standard",
        "rules": {
            "grammar": True,
            "spelling": True,
            "style": True,
            "structure": True,
            "links": True,
            "images": False
        },
        "language": "zh-CN"
    },
    "options": {
        "async_mode": True,
        "priority": "normal",
        "timeout": 300,
        "include_suggestions": True
    }
}

response = client.submit_check(check_request)
check_id = response.data.check_id
print(f"检查任务已提交: {check_id}")
```

#### cURL
```bash
curl -X POST "https://api.claude-enhancer.com/v1/docgate/checks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_source": {
      "type": "file",
      "path": "/project/docs/readme.md"
    },
    "check_config": {
      "profile": "standard"
    },
    "options": {
      "async_mode": true,
      "priority": "normal"
    }
  }'
```

#### JavaScript
```javascript
const docgateApi = {
  baseUrl: 'https://api.claude-enhancer.com/v1',
  accessToken: 'YOUR_ACCESS_TOKEN',

  async submitCheck(request) {
    const response = await fetch(`${this.baseUrl}/docgate/checks`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }
};

// 使用示例
const checkRequest = {
  document_source: {
    type: "file",
    path: "/project/docs/readme.md"
  },
  check_config: {
    profile: "standard"
  },
  options: {
    async_mode: true
  }
};

docgateApi.submitCheck(checkRequest)
  .then(response => {
    console.log('检查已提交:', response.data.check_id);
  })
  .catch(error => {
    console.error('提交失败:', error);
  });
```

### 2. Git仓库文档检查

```python
# 检查Git仓库中的文档
git_check_request = {
    "document_source": {
        "type": "git",
        "path": "docs/api.md",
        "git_info": {
            "repository": "https://github.com/user/repo",
            "branch": "main",
            "commit": "abc123def456"
        }
    },
    "check_config": {
        "profile": "strict",
        "custom_rules": [
            {
                "name": "company_terminology",
                "enabled": True,
                "severity": "warning",
                "pattern": r"\b(AI|ML)\b",
                "message": "请使用中文术语: {suggestion}",
                "options": {
                    "replacements": {
                        "AI": "人工智能",
                        "ML": "机器学习"
                    }
                }
            }
        ]
    }
}

response = client.submit_check(git_check_request)
```

## 批量文档检查

### Python SDK
```python
# 批量检查多个文档
batch_request = {
    "documents": [
        {
            "id": "readme",
            "source": {
                "type": "file",
                "path": "/docs/readme.md"
            }
        },
        {
            "id": "api_docs",
            "source": {
                "type": "file",
                "path": "/docs/api.md"
            },
            "config_override": {
                "profile": "strict"
            }
        },
        {
            "id": "changelog",
            "source": {
                "type": "git",
                "path": "CHANGELOG.md",
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
        "async_mode": True,
        "webhook_url": "https://your-app.com/webhooks/docgate"
    },
    "batch_options": {
        "max_concurrent": 3,
        "stop_on_error": False
    }
}

batch_response = client.submit_batch_check(batch_request)
batch_id = batch_response.data.batch_id
print(f"批量检查已提交: {batch_id}")
```

### cURL
```bash
curl -X POST "https://api.claude-enhancer.com/v1/docgate/checks/batch" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "readme",
        "source": {
          "type": "file",
          "path": "/docs/readme.md"
        }
      },
      {
        "id": "api_docs",
        "source": {
          "type": "file",
          "path": "/docs/api.md"
        }
      }
    ],
    "check_config": {
      "profile": "standard"
    },
    "batch_options": {
      "max_concurrent": 2
    }
  }'
```

## 获取检查结果

### 1. 查询检查状态

```python
# 轮询检查状态
import time

def wait_for_completion(check_id, timeout=300):
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = client.get_check_status(check_id)

        print(f"状态: {status.data.status}")
        if status.data.progress:
            print(f"进度: {status.data.progress.percentage}%")

        if status.data.status in ["completed", "failed", "cancelled"]:
            return status.data

        time.sleep(5)  # 等待5秒后重试

    raise TimeoutError("检查超时")

# 使用示例
final_status = wait_for_completion(check_id)
print(f"最终状态: {final_status.status}")

if final_status.summary:
    print(f"质量评分: {final_status.summary.score}")
    print(f"发现问题: {final_status.summary.total_issues}个")
```

### 2. 获取检查列表

```python
# 获取最近的检查任务
checks = client.list_checks(
    page=1,
    page_size=20,
    status="completed",
    sort="created_at:desc"
)

for check in checks.data.items:
    print(f"ID: {check.check_id}")
    print(f"状态: {check.status}")
    if check.summary:
        print(f"评分: {check.summary.score}")
    print("---")
```

## 下载报告

### 1. 获取JSON格式报告

```python
# 获取详细报告
report = client.get_report(check_id)

print(f"文档: {report.data.document_info.name}")
print(f"总评分: {report.data.summary.score}")
print(f"问题总数: {report.data.summary.total_issues}")

# 遍历问题
for issue in report.data.issues:
    print(f"- [{issue.severity}] {issue.message}")
    print(f"  位置: 第{issue.location.line}行")
    if issue.suggestions:
        print(f"  建议: {issue.suggestions[0].text}")
```

### 2. 下载PDF报告

```python
# 下载PDF格式报告
pdf_content = client.download_report(check_id, format="pdf")

with open(f"quality_report_{check_id}.pdf", "wb") as f:
    f.write(pdf_content)

print("PDF报告已下载")
```

### 3. 下载HTML报告

```bash
# 使用cURL下载HTML报告
curl -X GET "https://api.claude-enhancer.com/v1/docgate/checks/check_123456/report/download?format=html" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o "quality_report.html"
```

## 配置管理

### 1. 创建自定义配置

```python
# 创建自定义检查配置
config_request = {
    "name": "严格文档检查",
    "description": "适用于正式发布文档的严格质量检查",
    "based_on": "standard",
    "rules": {
        "grammar": True,
        "spelling": True,
        "style": True,
        "structure": True,
        "links": True,
        "images": True,
        "accessibility": True,
        "seo": True
    },
    "custom_rules": [
        {
            "name": "brand_consistency",
            "enabled": True,
            "severity": "error",
            "pattern": r"\b(我们的产品|our product)\b",
            "message": "请使用统一的产品名称: Claude Enhancer",
            "options": {
                "replacements": {
                    "我们的产品": "Claude Enhancer",
                    "our product": "Claude Enhancer"
                }
            }
        },
        {
            "name": "version_format",
            "enabled": True,
            "severity": "warning",
            "pattern": r"v\d+\.\d+",
            "message": "版本号格式应为 'v1.0.0'（包含修订号）"
        }
    ],
    "is_public": False
}

config = client.create_config(config_request)
print(f"配置已创建: {config.data.id}")
```

### 2. 获取配置列表

```python
# 获取所有可用配置
configs = client.list_configs()

for config in configs.data:
    print(f"- {config.name}")
    print(f"  ID: {config.id}")
    print(f"  描述: {config.description}")
    print(f"  使用次数: {config.usage_count}")
    print()
```

## Webhook设置

### 1. 创建Webhook

```python
# 创建Webhook配置
webhook_request = {
    "name": "质量检查通知",
    "url": "https://your-app.com/webhooks/docgate",
    "events": [
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
        "secret": "your_webhook_secret"
    },
    "headers": {
        "X-Source": "DocGate",
        "X-Environment": "production"
    },
    "active": True
}

webhook = client.create_webhook(webhook_request)
print(f"Webhook已创建: {webhook.data.id}")
```

### 2. 处理Webhook事件

```python
# Flask应用示例
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhooks/docgate', methods=['POST'])
def handle_docgate_webhook():
    # 验证签名
    signature = request.headers.get('X-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    # 处理事件
    event_data = request.json
    event_type = event_data['event']

    if event_type == 'check.completed':
        handle_check_completed(event_data)
    elif event_type == 'check.failed':
        handle_check_failed(event_data)
    elif event_type == 'report.generated':
        handle_report_generated(event_data)

    return jsonify({'status': 'received'}), 200

def verify_signature(payload, signature):
    """验证Webhook签名"""
    secret = 'your_webhook_secret'
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected}', signature)

def handle_check_completed(event_data):
    """处理检查完成事件"""
    check_id = event_data['data']['check_id']
    score = event_data['data']['summary']['score']

    print(f"质量检查完成: {check_id}, 评分: {score}")

    # 发送通知、更新状态等
    if score < 80:
        send_alert(f"文档质量较低: {score}")

def handle_check_failed(event_data):
    """处理检查失败事件"""
    check_id = event_data['data']['check_id']
    print(f"质量检查失败: {check_id}")

    # 记录错误、重试等

def handle_report_generated(event_data):
    """处理报告生成事件"""
    report_url = event_data['data']['report_url']
    print(f"报告已生成: {report_url}")

    # 下载报告、发送邮件等
```

### 3. 测试Webhook

```python
# 测试Webhook配置
test_result = client.test_webhook(webhook.data.id)

if test_result.data:
    print("Webhook测试成功")
else:
    print("Webhook测试失败，请检查URL和配置")
```

## 系统监控

### 1. 获取系统状态

```python
# 检查系统健康状态
health = client.get_system_health()

print(f"系统状态: {health.data.status}")
print(f"版本: {health.data.version}")
print(f"运行时间: {health.data.uptime}秒")

print("\n服务状态:")
for service, status in health.data.services.items():
    print(f"- {service}: {status}")

print("\n系统指标:")
for metric, value in health.data.metrics.items():
    print(f"- {metric}: {value}")
```

### 2. 获取使用统计

```python
from datetime import datetime, timedelta

# 获取最近一周的统计
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=7)

stats = client.get_usage_stats(
    period="day",
    from_date=start_date,
    to_date=end_date
)

print(f"统计周期: {stats.data.period}")
print(f"总检查数: {stats.data.total_checks}")
print(f"成功率: {stats.data.completed_checks / stats.data.total_checks * 100:.1f}%")
print(f"平均处理时间: {stats.data.avg_processing_time}秒")

print("\n最常见问题:")
for issue in stats.data.most_common_issues:
    print(f"- {issue['type']}: {issue['count']}次")

print("\n文档类型分布:")
for doc_type, count in stats.data.document_types.items():
    print(f"- {doc_type}: {count}个")
```

## 错误处理

### 1. 处理API错误

```python
from docgate_sdk.exceptions import (
    DocGateException,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServiceError
)

try:
    # 提交检查
    response = client.submit_check(invalid_request)

except ValidationError as e:
    print(f"验证错误: {e.message}")
    print(f"错误码: {e.error_code}")
    if e.details:
        print(f"字段: {e.details.get('field')}")
        print(f"约束: {e.details.get('constraint')}")

except NotFoundError as e:
    print(f"资源不存在: {e.message}")
    print(f"资源类型: {e.details.get('resource_type')}")

except RateLimitError as e:
    print(f"请求频率过高: {e.message}")
    print(f"剩余次数: {e.details.get('remaining')}")
    print(f"重置时间: {e.details.get('reset_time')}")

    # 等待后重试
    import time
    time.sleep(60)  # 等待1分钟

except ServiceError as e:
    print(f"服务错误: {e.message}")
    print(f"服务名称: {e.details.get('service_name')}")

    # 重试逻辑
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            response = client.submit_check(request)
            break
        except ServiceError:
            retry_count += 1
            time.sleep(2 ** retry_count)  # 指数退避

except DocGateException as e:
    print(f"DocGate错误: {e.message}")
    print(f"错误码: {e.error_code}")
    print(f"状态码: {e.status_code}")
```

### 2. 处理HTTP错误

```javascript
// JavaScript错误处理示例
async function submitCheck(request) {
  try {
    const response = await fetch('/api/v1/docgate/checks', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new DocGateError(errorData.error, response.status);
    }

    return await response.json();

  } catch (error) {
    if (error instanceof DocGateError) {
      switch (error.code) {
        case 'DOC_VAL_001':
          console.error('文档路径无效:', error.message);
          break;
        case 'DOC_RAT_001':
          console.error('请求频率过高:', error.message);
          // 显示重试时间
          const retryAfter = error.details.reset_time;
          console.log(`请在 ${retryAfter} 秒后重试`);
          break;
        case 'DOC_SER_002':
          console.error('服务暂时不可用:', error.message);
          // 显示重试按钮
          break;
        default:
          console.error('未知错误:', error.message);
      }
    } else {
      console.error('网络错误:', error.message);
    }

    throw error;
  }
}

class DocGateError extends Error {
  constructor(errorData, statusCode) {
    super(errorData.message);
    this.code = errorData.code;
    this.type = errorData.type;
    this.details = errorData.details;
    this.statusCode = statusCode;
  }
}
```

## 最佳实践

### 1. 性能优化

```python
# 使用连接池优化HTTP请求
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedDocGateClient:
    def __init__(self, access_token, base_url):
        self.access_token = access_token
        self.base_url = base_url

        # 创建会话
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # 配置适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置默认头部
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })

    def submit_check(self, request):
        response = self.session.post(
            f'{self.base_url}/docgate/checks',
            json=request,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

### 2. 批量处理优化

```python
import asyncio
import aiohttp

async def process_documents_batch(documents, batch_size=10):
    """异步批量处理文档"""

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(batch_size)

        async def process_single_document(doc):
            async with semaphore:
                return await submit_check_async(session, doc)

        # 并发处理所有文档
        tasks = [process_single_document(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({'document': documents[i], 'error': result})
            else:
                successful.append(result)

        return successful, failed

async def submit_check_async(session, document):
    """异步提交单个检查"""
    async with session.post(
        'https://api.claude-enhancer.com/v1/docgate/checks',
        json=document,
        headers={'Authorization': f'Bearer {access_token}'}
    ) as response:
        response.raise_for_status()
        return await response.json()
```

### 3. 缓存策略

```python
import redis
import json
from datetime import timedelta

class CachedDocGateClient:
    def __init__(self, access_token, base_url):
        self.client = DocGateClient(access_token, base_url)
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1小时

    def get_report(self, check_id):
        # 尝试从缓存获取
        cache_key = f"docgate:report:{check_id}"
        cached_data = self.redis.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # 从API获取
        report = self.client.get_report(check_id)

        # 缓存结果
        self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(report.dict(), default=str)
        )

        return report

    def get_configs(self):
        # 配置变化不频繁，可以缓存更长时间
        cache_key = "docgate:configs"
        cached_data = self.redis.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        configs = self.client.list_configs()

        # 缓存30分钟
        self.redis.setex(
            cache_key,
            1800,
            json.dumps([config.dict() for config in configs.data], default=str)
        )

        return configs
```

---

## 总结

这个API设计提供了完整的文档质量管理功能，包括：

- **完整的RESTful API**: 遵循标准设计原则
- **强大的功能集**: 支持各种文档类型和检查方式
- **灵活的配置**: 可自定义检查规则和配置
- **实时通知**: Webhook事件推送
- **详细的监控**: 系统状态和使用统计
- **优秀的错误处理**: 标准化错误码和详细错误信息
- **高性能设计**: 支持异步处理和批量操作

通过这些示例，开发者可以快速集成DocGate Agent到自己的应用中，实现自动化的文档质量管理。