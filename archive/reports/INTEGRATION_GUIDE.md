# Perfect21 编程集成指南

## 🎯 概述

Perfect21提供多种方式让您在编程其他程序时调用Perfect21进行开发任务。本指南介绍所有集成方式和最佳实践。

## 🚀 集成方式一览

### 1. Python SDK (推荐)
- **适用场景**: Python项目、脚本自动化
- **优势**: 原生集成、类型安全、异步支持
- **文件**: `api/perfect21_sdk.py`

### 2. REST API
- **适用场景**: 跨语言调用、微服务架构
- **优势**: 语言无关、HTTP标准、可扩展
- **文件**: `api/rest_server.py`

### 3. 命令行接口
- **适用场景**: 脚本集成、CI/CD流水线
- **优势**: 简单直接、Shell友好
- **文件**: `main/cli.py`

## 📋 快速开始

### Python SDK 基本用法

```python
from api.perfect21_sdk import Perfect21SDK

# 1. 创建SDK实例
sdk = Perfect21SDK()

# 2. 执行开发任务
result = sdk.task("创建用户登录API接口")
print(f"任务执行结果: {result['success']}")

# 3. Git工作流操作
sdk.git_workflow('create-feature', name='user-auth')

# 4. 安装Git钩子
sdk.install_hooks('standard')
```

### REST API 调用

```bash
# 启动API服务器
python3 api/rest_server.py --host 0.0.0.0 --port 8000

# 调用API
curl -X POST "http://localhost:8000/task" \
     -H "Content-Type: application/json" \
     -d '{"description": "创建用户模型", "timeout": 300}'
```

### 命令行集成

```bash
# 直接调用
python3 main/cli.py status
python3 main/cli.py workflow create-feature --name user-auth

# 在脚本中使用
result=$(python3 main/cli.py hooks install standard)
if [ $? -eq 0 ]; then
    echo "钩子安装成功"
fi
```

## 🔧 详细API参考

### Python SDK API

#### 基本方法

```python
# 任务执行
result = sdk.task(
    description="任务描述",
    timeout=300,        # 超时秒数
    verbose=False       # 详细输出
)

# 异步任务
def on_complete(task_id, result):
    print(f"任务 {task_id} 完成")

task_id = sdk.async_task(
    description="异步任务描述",
    callback=on_complete
)

# 系统状态
status = sdk.status()

# Git工作流
result = sdk.git_workflow(
    action='create-feature',    # 操作类型
    name='feature-name',        # 功能名称
    version='1.0.0',           # 版本号
    source='develop'           # 源分支
)

# 钩子管理
result = sdk.install_hooks(
    hook_group='standard',     # 钩子组
    force=False               # 强制覆盖
)
```

#### 便捷函数

```python
from api.perfect21_sdk import quick_task, quick_status, Perfect21Context

# 快速任务
result = quick_task("创建配置文件")

# 快速状态
status = quick_status()

# 上下文管理器
with Perfect21Context() as p21:
    result = p21.task("开发任务")
```

### REST API 端点

#### 任务执行

```http
POST /task
Content-Type: application/json

{
    "description": "任务描述",
    "timeout": 300,
    "verbose": false
}
```

#### 异步任务

```http
POST /task/async
# 启动异步任务

GET /task/{task_id}
# 查询任务状态
```

#### 工作流操作

```http
POST /workflow
Content-Type: application/json

{
    "action": "create-feature",
    "name": "feature-name",
    "source": "develop"
}
```

#### 系统管理

```http
GET /health          # 健康检查
GET /status          # 系统状态
POST /hooks/install  # 安装钩子
```

## 🎨 集成模式

### 1. 同步集成模式

```python
# 适用于简单脚本
def deploy_application():
    sdk = Perfect21SDK()

    # 代码检查
    check_result = sdk.task("执行代码质量检查")
    if not check_result['success']:
        return False

    # 运行测试
    test_result = sdk.task("运行完整测试套件")
    if not test_result['success']:
        return False

    # 部署准备
    deploy_result = sdk.task("准备生产部署")
    return deploy_result['success']
```

### 2. 异步集成模式

```python
# 适用于高并发场景
import asyncio

async def parallel_development():
    sdk = Perfect21SDK()

    tasks = [
        "创建用户模型",
        "设计API接口",
        "编写测试用例"
    ]

    # 并行执行多个任务
    results = []
    for task in tasks:
        task_id = sdk.async_task(task)
        results.append(task_id)

    # 等待所有任务完成
    await asyncio.sleep(30)  # 实际应用中使用适当的等待机制

    return results
```

### 3. 事件驱动模式

```python
# 适用于响应式系统
class DevelopmentWorkflow:
    def __init__(self):
        self.sdk = Perfect21SDK()

    def on_code_commit(self, commit_hash):
        """代码提交事件处理"""
        result = self.sdk.task(f"分析提交 {commit_hash} 的代码质量")
        if not result['success']:
            self.notify_team("代码质量检查失败")

    def on_feature_request(self, feature_spec):
        """功能请求事件处理"""
        # 创建功能分支
        self.sdk.git_workflow('create-feature', name=feature_spec['name'])

        # 生成初始代码
        self.sdk.task(f"根据规格创建功能: {feature_spec['description']}")
```

### 4. 微服务集成模式

```python
# 适用于微服务架构
import requests

class Perfect21Client:
    def __init__(self, api_base="http://perfect21-api:8000"):
        self.api_base = api_base

    def develop_service(self, service_spec):
        """开发微服务"""
        response = requests.post(f"{self.api_base}/task", json={
            "description": f"创建微服务: {service_spec}",
            "timeout": 600
        })

        return response.json()

    def validate_service(self, service_name):
        """验证服务"""
        response = requests.post(f"{self.api_base}/task", json={
            "description": f"验证微服务 {service_name} 的完整性"
        })

        return response.json()
```

## 📊 性能优化

### 任务超时设置

```python
# 根据任务复杂度设置超时
simple_task = sdk.task("简单函数", timeout=60)      # 1分钟
normal_task = sdk.task("API开发", timeout=300)      # 5分钟
complex_task = sdk.task("系统架构", timeout=1800)   # 30分钟
```

### 并发控制

```python
import threading
from concurrent.futures import ThreadPoolExecutor

def batch_development(tasks):
    """批量开发任务"""
    sdk = Perfect21SDK()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []

        for task in tasks:
            future = executor.submit(sdk.task, task)
            futures.append(future)

        results = [f.result() for f in futures]
        return results
```

### 错误处理

```python
def robust_task_execution(description, max_retries=3):
    """健壮的任务执行"""
    sdk = Perfect21SDK()

    for attempt in range(max_retries):
        try:
            result = sdk.task(description, timeout=300)
            if result['success']:
                return result
            else:
                print(f"尝试 {attempt + 1} 失败: {result.get('error')}")
        except Exception as e:
            print(f"尝试 {attempt + 1} 异常: {e}")

        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # 指数退避

    return {'success': False, 'error': '达到最大重试次数'}
```

## 🔒 安全考虑

### API认证 (可选扩展)

```python
# 扩展SDK支持认证
class SecurePerfect21SDK(Perfect21SDK):
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key

    def _make_request(self, endpoint, data):
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        # 发送请求...
```

### 任务权限控制

```python
# 限制可执行的任务类型
ALLOWED_TASK_PATTERNS = [
    r'创建.*',
    r'生成.*测试',
    r'优化.*性能'
]

def validate_task(description):
    import re
    return any(re.match(pattern, description) for pattern in ALLOWED_TASK_PATTERNS)
```

## 🚀 最佳实践

### 1. 任务描述规范

```python
# ✅ 好的任务描述
"创建用户认证API，包括登录、注册、密码重置功能"
"优化数据库查询性能，重点关注用户表的索引"
"生成完整的单元测试，覆盖率达到90%以上"

# ❌ 不好的任务描述
"做个API"
"优化一下"
"测试"
```

### 2. 错误处理策略

```python
def handle_task_result(result):
    """标准结果处理"""
    if result['success']:
        print("✅ 任务执行成功")
        return True
    else:
        error_msg = result.get('stderr') or result.get('error', '未知错误')
        print(f"❌ 任务执行失败: {error_msg}")

        # 记录详细错误日志
        logging.error(f"Perfect21任务失败: {error_msg}")
        return False
```

### 3. 资源管理

```python
# 使用上下文管理器确保资源清理
with Perfect21Context() as p21:
    try:
        result = p21.task("复杂开发任务")
        process_result(result)
    except Exception as e:
        handle_error(e)
    finally:
        cleanup_resources()
```

## 🔧 故障排除

### 常见问题

1. **Perfect21初始化失败**
   ```python
   # 检查项目结构
   if not os.path.exists('vp.py'):
       print("错误: 不在Perfect21项目根目录")
   ```

2. **任务执行超时**
   ```python
   # 增加超时时间或使用异步模式
   result = sdk.task(description, timeout=1800)  # 30分钟
   ```

3. **REST API连接失败**
   ```bash
   # 检查服务器状态
   curl http://localhost:8000/health
   ```

### 调试模式

```python
# 启用详细日志
sdk = Perfect21SDK()
result = sdk.task("任务描述", verbose=True)
print(result['stdout'])  # 查看详细输出
```

## 📚 完整示例

查看 `examples/integration_examples.py` 获取完整的集成示例，包括：

- 基本SDK使用
- 异步任务处理
- REST API调用
- CI/CD集成
- 错误处理
- 性能优化

## 🎉 总结

Perfect21提供了灵活的编程集成方式：

1. **Python SDK**: 最佳的Python项目集成方案
2. **REST API**: 跨语言和微服务的理想选择
3. **命令行**: 脚本和CI/CD的简单集成

选择适合您项目的集成方式，开始使用Perfect21提升开发效率！

---

*更新时间: 2025-09-15*
*版本: Perfect21 v2.0.0*