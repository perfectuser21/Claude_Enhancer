# 🌟 Claude Enhancer 最佳实践指南

> 开发、部署和运维的最佳实践，确保系统高质量和可维护性

## 📋 目录

- [开发最佳实践](#-开发最佳实践)
- [代码质量标准](#-代码质量标准)
- [Agent 设计模式](#-agent-设计模式)
- [Hook 开发规范](#-hook-开发规范)
- [性能优化实践](#-性能优化实践)
- [安全最佳实践](#-安全最佳实践)
- [部署最佳实践](#-部署最佳实践)
- [监控运维实践](#-监控运维实践)
- [团队协作规范](#-团队协作规范)

## 🚀 开发最佳实践

### 8-Phase 工作流最佳实践

#### Phase 策略选择
```yaml
# 任务复杂度判断标准
simple_tasks:
  criteria:
    - 代码变更 < 50 行
    - 影响文件 < 5 个
    - 风险等级: 低
  agents: 4
  duration: "5-10 分钟"
  examples:
    - 修复简单 bug
    - 更新文档
    - 调整配置

standard_tasks:
  criteria:
    - 代码变更 50-200 行
    - 影响文件 5-15 个
    - 风险等级: 中
  agents: 6
  duration: "15-20 分钟"
  examples:
    - 添加新功能
    - API 接口开发
    - 数据库表结构调整

complex_tasks:
  criteria:
    - 代码变更 > 200 行
    - 影响文件 > 15 个
    - 风险等级: 高
  agents: 8
  duration: "25-30 分钟"
  examples:
    - 系统架构重构
    - 微服务拆分
    - 大型功能模块
```

#### Agent 选择最佳实践
```bash
# 标准 Agent 组合模板

# 认证相关任务
auth_tasks_agents=(
    "security-auditor"      # 安全审查（必需）
    "backend-architect"     # 架构设计
    "api-designer"          # API 设计
    "database-specialist"   # 数据模型
    "test-engineer"         # 测试策略
    "technical-writer"      # 文档编写
)

# API 开发任务
api_development_agents=(
    "api-designer"          # API 设计（必需）
    "backend-engineer"      # 实现开发
    "test-engineer"         # 测试用例
    "security-auditor"      # 安全检查
    "performance-engineer"  # 性能优化
    "technical-writer"      # API 文档
)

# 数据库相关任务
database_tasks_agents=(
    "database-specialist"   # 数据设计（必需）
    "backend-architect"     # 架构影响
    "performance-engineer"  # 性能优化
    "security-auditor"      # 安全考虑
    "test-engineer"         # 数据测试
    "devops-engineer"       # 部署迁移
)
```

### 代码组织最佳实践

#### 项目结构模式
```
claude-enhancer/
├── .claude/                 # Claude Enhancer 配置
│   ├── core/               # L0: 核心引擎（5%）
│   │   ├── engine.py       # 8-Phase 工作流引擎
│   │   ├── orchestrator.py # Agent 协调器
│   │   └── config.yaml     # 核心配置
│   ├── framework/          # L1: 框架层（15%）
│   │   ├── workflow/       # 工作流实现
│   │   ├── strategies/     # Agent 策略
│   │   └── hooks/          # 基础 hooks
│   ├── services/           # L2: 服务层（20%）
│   │   ├── validation/     # 验证服务
│   │   ├── formatting/     # 格式化服务
│   │   └── analysis/       # 分析服务
│   └── features/           # L3: 特性层（60%+）
│       ├── basic/          # 简单特性
│       ├── standard/       # 标准特性
│       └── advanced/       # 高级特性
├── src/                    # 应用源码
├── tests/                  # 测试代码
├── docs/                   # 文档
└── deployment/             # 部署配置
```

#### 文件命名规范
```bash
# 通用文件命名
kebab-case.js              # JavaScript/TypeScript
snake_case.py              # Python
PascalCase.class           # Java/C#
camelCase.variable         # 变量命名

# Claude Enhancer 特定
agent-name.md              # Agent 定义文件
hook-name.sh               # Hook 脚本文件
feature-name/              # Feature 目录
config-name.yaml           # 配置文件
```

### Git 工作流最佳实践

#### 分支策略
```bash
# 分支命名规范
feature/CE-123-add-user-auth     # 功能分支
fix/CE-456-login-bug            # 修复分支
hotfix/CE-789-security-patch    # 热修复分支
release/v4.1.0                  # 发布分支

# 提交信息规范
feat(auth): add JWT authentication
fix(api): resolve login timeout issue
docs(readme): update installation guide
perf(hooks): optimize agent selection algorithm
```

#### Pre-commit 检查清单
```bash
# 必须通过的检查项
✅ 代码格式化（Prettier/Black）
✅ 代码检查（ESLint/flake8）
✅ 单元测试通过
✅ 测试覆盖率 ≥ 80%
✅ 安全扫描无高危问题
✅ 文档更新
✅ Commit message 规范
✅ 无调试代码残留
```

## 🏗️ 代码质量标准

### 代码风格规范

#### Python 代码标准
```python
# 文件: coding_standards.py

import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 使用 dataclass 定义数据结构
@dataclass
class AgentConfiguration:
    """Agent 配置数据类

    Attributes:
        name: Agent 名称
        capabilities: Agent 能力列表
        priority: 优先级（1-10）
        timeout: 超时时间（秒）
    """
    name: str
    capabilities: List[str]
    priority: int = 5
    timeout: int = 30

# 使用抽象基类定义接口
class AgentInterface(ABC):
    """Agent 接口定义"""

    @abstractmethod
    def execute(self, task: str) -> Dict[str, any]:
        """执行任务

        Args:
            task: 任务描述

        Returns:
            执行结果字典

        Raises:
            AgentExecutionError: 执行失败时抛出
        """
        pass

# 错误处理最佳实践
class AgentExecutionError(Exception):
    """Agent 执行错误"""

    def __init__(self, agent_name: str, error_message: str):
        self.agent_name = agent_name
        self.error_message = error_message
        super().__init__(f"Agent {agent_name} failed: {error_message}")

# 日志记录最佳实践
logger = logging.getLogger(__name__)

def execute_agent_with_retry(agent: AgentInterface, task: str, max_retries: int = 3) -> Dict[str, any]:
    """执行 Agent 任务，支持重试

    Args:
        agent: Agent 实例
        task: 任务描述
        max_retries: 最大重试次数

    Returns:
        执行结果

    Raises:
        AgentExecutionError: 重试失败后抛出
    """
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"执行任务：{task}，尝试次数：{attempt + 1}")
            result = agent.execute(task)
            logger.info(f"任务执行成功：{task}")
            return result
        except Exception as e:
            logger.warning(f"任务执行失败（尝试 {attempt + 1}/{max_retries + 1}）：{str(e)}")
            if attempt == max_retries:
                raise AgentExecutionError(agent.__class__.__name__, str(e))

    # 这行代码永远不会执行，但为了类型检查
    raise AgentExecutionError(agent.__class__.__name__, "未知错误")
```

#### Shell 脚本标准
```bash
#!/bin/bash
# 文件: shell_standards.sh
# 描述: Shell 脚本编写标准

# 严格模式
set -euo pipefail

# 全局变量使用大写
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_FILE="${SCRIPT_DIR}/../config/settings.json"
readonly LOG_FILE="/var/log/perfect21/script.log"

# 函数命名使用小写+下划线
log_info() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $message" | tee -a "$LOG_FILE"
}

log_error() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $message" | tee -a "$LOG_FILE" >&2
}

# 参数验证
validate_parameters() {
    local task_description="$1"

    if [[ -z "$task_description" ]]; then
        log_error "任务描述不能为空"
        return 1
    fi

    if [[ ${#task_description} -lt 10 ]]; then
        log_error "任务描述过短，至少需要10个字符"
        return 1
    fi

    return 0
}

# 错误处理
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "脚本异常退出，退出码：$exit_code"
    fi
    # 清理临时文件
    rm -f /tmp/perfect21_*
}

# 注册退出处理
trap cleanup_on_exit EXIT

# 主函数
main() {
    local task_description="${1:-}"

    log_info "开始执行脚本"

    if ! validate_parameters "$task_description"; then
        exit 1
    fi

    # 具体业务逻辑
    log_info "执行任务：$task_description"

    log_info "脚本执行完成"
}

# 只在直接执行时运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 测试标准

#### 单元测试最佳实践
```python
# 文件: test_agent_system.py

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.agent_system import AgentOrchestrator, AgentConfiguration

class TestAgentOrchestrator:
    """Agent 编排器测试类"""

    @pytest.fixture
    def orchestrator(self):
        """测试用编排器实例"""
        return AgentOrchestrator()

    @pytest.fixture
    def mock_agent_config(self):
        """模拟 Agent 配置"""
        return AgentConfiguration(
            name="test-agent",
            capabilities=["coding", "testing"],
            priority=5,
            timeout=30
        )

    def test_agent_selection_simple_task(self, orchestrator):
        """测试简单任务的 Agent 选择"""
        # Given
        task = "fix typo in documentation"

        # When
        selected_agents = orchestrator.select_agents(task)

        # Then
        assert len(selected_agents) == 4
        assert "technical-writer" in selected_agents

    def test_agent_selection_complex_task(self, orchestrator):
        """测试复杂任务的 Agent 选择"""
        # Given
        task = "refactor entire authentication system"

        # When
        selected_agents = orchestrator.select_agents(task)

        # Then
        assert len(selected_agents) == 8
        assert "security-auditor" in selected_agents
        assert "backend-architect" in selected_agents

    @pytest.mark.asyncio
    async def test_parallel_agent_execution(self, orchestrator, mock_agent_config):
        """测试并行 Agent 执行"""
        # Given
        agents = [mock_agent_config] * 4
        task = "implement user authentication"

        # Mock agent execution
        with patch.object(orchestrator, 'execute_agent', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"status": "success", "result": "task completed"}

            # When
            results = await orchestrator.execute_parallel(agents, task)

            # Then
            assert len(results) == 4
            assert all(result["status"] == "success" for result in results)
            assert mock_execute.call_count == 4

    def test_error_handling(self, orchestrator):
        """测试错误处理"""
        # Given
        invalid_task = ""

        # When & Then
        with pytest.raises(ValueError, match="任务描述不能为空"):
            orchestrator.select_agents(invalid_task)

    @pytest.mark.parametrize("task,expected_complexity", [
        ("fix bug", "simple"),
        ("add new feature", "standard"),
        ("architect new system", "complex"),
    ])
    def test_complexity_detection(self, orchestrator, task, expected_complexity):
        """参数化测试复杂度检测"""
        # When
        complexity = orchestrator.detect_complexity(task)

        # Then
        assert complexity == expected_complexity
```

#### 集成测试示例
```python
# 文件: test_integration.py

import pytest
import requests
import time
from testcontainers import DockerComposeContainer

class TestClaudeEnhancerIntegration:
    """Claude Enhancer 集成测试"""

    @pytest.fixture(scope="class")
    def docker_compose(self):
        """Docker Compose 测试环境"""
        with DockerComposeContainer("deployment/docker-compose.test.yml") as compose:
            # 等待服务启动
            time.sleep(30)
            yield compose

    def test_health_endpoint(self, docker_compose):
        """测试健康检查端点"""
        # Given
        base_url = "http://localhost:8080"

        # When
        response = requests.get(f"{base_url}/health")

        # Then
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_agent_selection_api(self, docker_compose):
        """测试 Agent 选择 API"""
        # Given
        base_url = "http://localhost:8080"
        payload = {
            "task": "implement user authentication",
            "complexity": "standard"
        }

        # When
        response = requests.post(f"{base_url}/api/agents/select", json=payload)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 6

    def test_workflow_execution(self, docker_compose):
        """测试完整工作流执行"""
        # Given
        base_url = "http://localhost:8080"
        workflow_data = {
            "phase": 3,
            "task": "add user profile feature",
            "agents": ["backend-engineer", "test-engineer", "api-designer"]
        }

        # When
        response = requests.post(f"{base_url}/api/workflow/execute", json=workflow_data)

        # Then
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        assert "execution_time" in result
```

## 🤖 Agent 设计模式

### Agent 定义模式

#### 标准 Agent 结构
```markdown
# agent-name: 角色简要描述

## 核心能力 (Core Capabilities)
- 主要技术技能
- 专业领域知识
- 工具和框架熟练度

## 职责范围 (Responsibilities)
- 具体任务类型
- 决策权限范围
- 输出物标准

## 协作模式 (Collaboration Patterns)
- 与其他 Agent 的协作方式
- 信息交换格式
- 冲突解决机制

## 质量标准 (Quality Standards)
- 代码质量要求
- 文档标准
- 测试覆盖率要求

## 使用场景 (Use Cases)
- 适用的任务类型
- 复杂度级别
- 时间估算

## 性能指标 (Performance Metrics)
- 执行效率要求
- 准确率标准
- 资源使用限制
```

#### Agent 专业化策略
```yaml
# 水平专业化：按技术栈划分
frontend_agents:
  - react-specialist
  - vue-specialist
  - angular-expert
  - typescript-pro

backend_agents:
  - python-pro
  - golang-pro
  - java-enterprise
  - rust-pro

# 垂直专业化：按职能划分
quality_agents:
  - test-engineer
  - security-auditor
  - performance-engineer
  - code-reviewer

process_agents:
  - technical-writer
  - devops-engineer
  - project-manager
  - cleanup-specialist

# 领域专业化：按业务领域划分
domain_agents:
  - fintech-specialist
  - healthcare-dev
  - ai-engineer
  - blockchain-dev
```

### Agent 通信协议

#### 输入输出标准化
```typescript
// Agent 输入接口
interface AgentInput {
  task: {
    description: string;
    complexity: 'simple' | 'standard' | 'complex';
    priority: number;
    deadline?: string;
  };
  context: {
    phase: number;
    previousResults?: AgentOutput[];
    constraints?: string[];
    requirements?: string[];
  };
  resources: {
    files: string[];
    documentation: string[];
    dependencies: string[];
  };
}

// Agent 输出接口
interface AgentOutput {
  agent: string;
  status: 'success' | 'partial' | 'failed';
  result: {
    code?: string[];
    documentation?: string[];
    tests?: string[];
    recommendations?: string[];
  };
  metadata: {
    executionTime: number;
    resourcesUsed: string[];
    confidence: number;
    warnings?: string[];
  };
  nextSteps?: string[];
}
```

## 🪝 Hook 开发规范

### Hook 接口标准

#### 输入处理模式
```bash
#!/bin/bash
# Hook 标准输入处理模式

# 1. 读取输入
INPUT=$(cat)

# 2. 解析 JSON（如果适用）
if command -v jq >/dev/null 2>&1; then
    TOOL=$(echo "$INPUT" | jq -r '.tool // empty')
    PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')
else
    # 备用解析方法
    TOOL=$(echo "$INPUT" | grep -o '"tool":[^,}]*' | cut -d'"' -f4)
    PROMPT=$(echo "$INPUT" | grep -o '"prompt":[^,}]*' | cut -d'"' -f4)
fi

# 3. 验证输入
if [[ -z "$PROMPT" ]]; then
    echo "警告: 未提供任务描述" >&2
fi

# 4. 处理逻辑
# ... 具体处理 ...

# 5. 输出结果（stderr 用于建议，stdout 用于原始输入）
echo "🎯 Agent 选择建议: 使用 6-agent 标准配置" >&2
echo "$INPUT"  # 传递原始输入

# 6. 退出状态
exit 0  # 0=非阻塞, 1=阻塞
```

#### 性能优化模式
```bash
#!/bin/bash
# 高性能 Hook 模式

# 超时保护
timeout 5 bash -c '
    # 核心逻辑
    echo "执行 Hook 逻辑"
' || {
    echo "Hook 执行超时，使用默认建议" >&2
    exit 0
}

# 缓存机制
CACHE_FILE="/tmp/perfect21_cache_$(echo "$INPUT" | md5sum | cut -d' ' -f1)"
CACHE_TTL=3600  # 1小时

if [[ -f "$CACHE_FILE" && $(($(date +%s) - $(stat -c %Y "$CACHE_FILE"))) -lt $CACHE_TTL ]]; then
    # 使用缓存结果
    cat "$CACHE_FILE" >&2
else
    # 计算新结果并缓存
    RESULT="计算的结果"
    echo "$RESULT" > "$CACHE_FILE"
    echo "$RESULT" >&2
fi

# 并行处理
{
    # 任务 1
    process_task_1 &
    PID1=$!

    # 任务 2
    process_task_2 &
    PID2=$!

    # 等待完成
    wait $PID1 $PID2
}
```

### Hook 安全规范

#### 输入验证
```bash
#!/bin/bash
# Hook 安全输入验证

validate_input() {
    local input="$1"

    # 检查输入长度
    if [[ ${#input} -gt 10000 ]]; then
        echo "错误: 输入过长" >&2
        return 1
    fi

    # 检查危险字符
    if echo "$input" | grep -qE '[\$`]|rm -rf|sudo|eval'; then
        echo "错误: 检测到危险字符" >&2
        return 1
    fi

    # 检查 JSON 格式（如果需要）
    if ! echo "$input" | jq . >/dev/null 2>&1; then
        echo "警告: 非标准 JSON 格式" >&2
    fi

    return 0
}

# 使用验证
INPUT=$(cat)
if ! validate_input "$INPUT"; then
    echo "$INPUT"  # 传递原始输入，但记录安全问题
    exit 0
fi
```

## ⚡ 性能优化实践

### 系统级优化

#### 并行处理模式
```python
# 文件: performance_optimization.py

import asyncio
import concurrent.futures
from typing import List, Callable, Any

class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    async def execute_parallel_async(self, tasks: List[Callable], *args) -> List[Any]:
        """异步并行执行任务"""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def bounded_task(task):
            async with semaphore:
                return await task(*args)

        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )

        return results

    def execute_parallel_threads(self, tasks: List[Callable], *args) -> List[Any]:
        """线程池并行执行任务"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(task, *args) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        return results

    def execute_parallel_processes(self, tasks: List[Callable], *args) -> List[Any]:
        """进程池并行执行任务（CPU 密集型任务）"""
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(task, *args) for task in tasks]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        return results

# 使用示例
async def optimize_agent_execution():
    """优化 Agent 执行性能"""
    optimizer = PerformanceOptimizer(max_workers=8)

    # 定义 Agent 任务
    agent_tasks = [
        execute_backend_architect,
        execute_api_designer,
        execute_security_auditor,
        execute_test_engineer,
    ]

    # 并行执行
    results = await optimizer.execute_parallel_async(agent_tasks, task_description="implement auth")

    return results
```

#### 缓存策略
```python
# 文件: caching_strategy.py

import functools
import time
import hashlib
import json
from typing import Any, Dict, Optional

class CacheManager:
    """缓存管理器"""

    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            cache_item = self.cache[key]
            if time.time() < cache_item['expires']:
                return cache_item['value']
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }

    def cached(self, ttl: Optional[int] = None):
        """缓存装饰器"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = self._generate_key(func.__name__, args, kwargs)

                # 尝试从缓存获取
                cached_result = self.get(key)
                if cached_result is not None:
                    return cached_result

                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result

            return wrapper
        return decorator

# 全局缓存实例
cache_manager = CacheManager()

# 使用示例
@cache_manager.cached(ttl=1800)  # 缓存30分钟
def analyze_task_complexity(task_description: str) -> str:
    """分析任务复杂度（可能耗时的操作）"""
    # 复杂的分析逻辑
    time.sleep(1)  # 模拟耗时操作

    if len(task_description) < 20:
        return "simple"
    elif len(task_description) < 100:
        return "standard"
    else:
        return "complex"
```

### 资源管理优化

#### 内存管理
```python
# 文件: memory_management.py

import gc
import psutil
import logging
from typing import Generator, Any

logger = logging.getLogger(__name__)

class MemoryManager:
    """内存管理器"""

    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent

    def check_memory_usage(self) -> float:
        """检查当前内存使用率"""
        memory = psutil.virtual_memory()
        return memory.percent

    def enforce_memory_limit(self) -> None:
        """强制执行内存限制"""
        current_usage = self.check_memory_usage()
        if current_usage > self.max_memory_percent:
            logger.warning(f"内存使用率过高: {current_usage:.1f}%")
            gc.collect()  # 强制垃圾回收

            # 再次检查
            new_usage = self.check_memory_usage()
            if new_usage > self.max_memory_percent:
                raise MemoryError(f"内存使用率仍然过高: {new_usage:.1f}%")

    def stream_process_large_data(self, data_source: Any) -> Generator[Any, None, None]:
        """流式处理大数据"""
        for item in data_source:
            # 定期检查内存使用
            self.enforce_memory_limit()
            yield self.process_item(item)

    def process_item(self, item: Any) -> Any:
        """处理单个数据项"""
        # 具体处理逻辑
        return item

# 使用示例
memory_manager = MemoryManager(max_memory_percent=75.0)

def process_large_file(file_path: str):
    """处理大文件"""
    try:
        with open(file_path, 'r') as file:
            for line in memory_manager.stream_process_large_data(file):
                # 处理每一行
                process_line(line)
    except MemoryError:
        logger.error("内存不足，无法处理文件")
        raise
```

## 🔒 安全最佳实践

### 输入验证和清理

#### 数据验证模式
```python
# 文件: security_validation.py

import re
import html
import json
from typing import Any, Dict, List, Union

class SecurityValidator:
    """安全验证器"""

    # 危险模式列表
    DANGEROUS_PATTERNS = [
        r'\$\([^)]*\)',          # 命令替换
        r'`[^`]*`',              # 反引号命令
        r'rm\s+-rf',             # 危险删除命令
        r'sudo\s+',              # sudo 命令
        r'eval\s*\(',            # eval 函数
        r'exec\s*\(',            # exec 函数
        r'<script[^>]*>',        # XSS 脚本标签
        r'javascript:',          # JavaScript 协议
        r'vbscript:',            # VBScript 协议
    ]

    @classmethod
    def sanitize_input(cls, input_data: str) -> str:
        """清理输入数据"""
        if not isinstance(input_data, str):
            raise TypeError("输入必须是字符串类型")

        # HTML 转义
        sanitized = html.escape(input_data)

        # 移除危险字符
        sanitized = re.sub(r'[<>"\';\\]', '', sanitized)

        return sanitized

    @classmethod
    def validate_input(cls, input_data: str, max_length: int = 1000) -> bool:
        """验证输入数据"""
        # 长度检查
        if len(input_data) > max_length:
            return False

        # 危险模式检查
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """验证 JSON 结构"""
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                return False

        # 检查字段类型
        field_types = {
            'task': str,
            'complexity': str,
            'agents': list,
            'phase': int
        }

        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False

        return True

# 使用示例
def secure_agent_selection(raw_input: str) -> Dict[str, Any]:
    """安全的 Agent 选择"""
    validator = SecurityValidator()

    # 验证输入
    if not validator.validate_input(raw_input, max_length=2000):
        raise ValueError("输入数据验证失败")

    # 清理输入
    clean_input = validator.sanitize_input(raw_input)

    # 解析 JSON
    try:
        data = json.loads(clean_input)
    except json.JSONDecodeError:
        raise ValueError("无效的 JSON 格式")

    # 验证结构
    required_fields = ['task', 'complexity']
    if not validator.validate_json_structure(data, required_fields):
        raise ValueError("JSON 结构验证失败")

    return data
```

### 权限控制

#### RBAC 权限模型
```python
# 文件: rbac_system.py

from enum import Enum
from typing import Dict, List, Set
from dataclasses import dataclass

class Permission(Enum):
    """权限枚举"""
    READ_AGENTS = "read_agents"
    WRITE_AGENTS = "write_agents"
    EXECUTE_WORKFLOW = "execute_workflow"
    ADMIN_SYSTEM = "admin_system"
    VIEW_LOGS = "view_logs"
    MODIFY_CONFIG = "modify_config"

class Role(Enum):
    """角色枚举"""
    VIEWER = "viewer"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class User:
    """用户数据类"""
    username: str
    roles: Set[Role]
    permissions: Set[Permission]

class RBACManager:
    """基于角色的访问控制管理器"""

    def __init__(self):
        # 角色权限映射
        self.role_permissions: Dict[Role, Set[Permission]] = {
            Role.VIEWER: {
                Permission.READ_AGENTS,
                Permission.VIEW_LOGS,
            },
            Role.DEVELOPER: {
                Permission.READ_AGENTS,
                Permission.WRITE_AGENTS,
                Permission.EXECUTE_WORKFLOW,
                Permission.VIEW_LOGS,
            },
            Role.ADMIN: {
                Permission.READ_AGENTS,
                Permission.WRITE_AGENTS,
                Permission.EXECUTE_WORKFLOW,
                Permission.VIEW_LOGS,
                Permission.MODIFY_CONFIG,
            },
            Role.SUPER_ADMIN: set(Permission),  # 所有权限
        }

    def get_user_permissions(self, user: User) -> Set[Permission]:
        """获取用户的所有权限"""
        permissions = set(user.permissions)

        for role in user.roles:
            permissions.update(self.role_permissions.get(role, set()))

        return permissions

    def check_permission(self, user: User, required_permission: Permission) -> bool:
        """检查用户是否具有指定权限"""
        user_permissions = self.get_user_permissions(user)
        return required_permission in user_permissions

    def require_permission(self, required_permission: Permission):
        """权限检查装饰器"""
        def decorator(func):
            def wrapper(user: User, *args, **kwargs):
                if not self.check_permission(user, required_permission):
                    raise PermissionError(f"用户 {user.username} 缺少权限: {required_permission.value}")
                return func(user, *args, **kwargs)
            return wrapper
        return decorator

# 使用示例
rbac = RBACManager()

@rbac.require_permission(Permission.EXECUTE_WORKFLOW)
def execute_agent_workflow(user: User, task: str) -> Dict[str, Any]:
    """执行 Agent 工作流（需要权限）"""
    return {"status": "success", "task": task}

# 创建用户
developer_user = User(
    username="john_doe",
    roles={Role.DEVELOPER},
    permissions=set()
)

# 检查权限
try:
    result = execute_agent_workflow(developer_user, "implement auth")
    print("工作流执行成功")
except PermissionError as e:
    print(f"权限不足: {e}")
```

## 🚀 部署最佳实践

### 容器化最佳实践

#### Dockerfile 优化
```dockerfile
# 多阶段构建 Dockerfile
FROM node:18-alpine AS node-builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./
COPY frontend/package*.json ./frontend/

# 安装依赖
RUN npm ci --only=production && \
    cd frontend && npm ci --only=production

# 复制源码并构建
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Python 构建阶段
FROM python:3.11-slim AS python-builder

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产阶段
FROM python:3.11-slim AS production

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从构建阶段复制文件
COPY --from=python-builder /root/.local /home/appuser/.local
COPY --from=node-builder /app/frontend/dist ./static/

# 复制应用代码
COPY src/ ./src/
COPY .claude/ ./.claude/
COPY deployment/docker-entrypoint.sh ./

# 设置权限
RUN chmod +x docker-entrypoint.sh && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 设置 PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "src.main"]
```

#### Docker Compose 配置
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  claude-enhancer:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/claude_enhancer
      - REDIS_URL=redis://redis:6379
      - CLAUDE_ENHANCER_MODE=enforcement
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - claude-enhancer-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=claude_enhancer
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./deployment/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - claude-enhancer-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - claude-enhancer-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/ssl:/etc/nginx/ssl
    depends_on:
      - claude-enhancer
    networks:
      - claude-enhancer-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  claude-enhancer-network:
    driver: bridge
```

### Kubernetes 部署策略

#### 滚动更新配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-enhancer
  namespace: claude-enhancer
  labels:
    app: claude-enhancer
    version: v4.1.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: claude-enhancer
  template:
    metadata:
      labels:
        app: claude-enhancer
        version: v4.1.0
    spec:
      serviceAccountName: claude-enhancer-sa
      containers:
      - name: claude-enhancer
        image: claude-enhancer:v4.1.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: claude-enhancer-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: claude-enhancer-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config-volume
          mountPath: /app/.claude/config
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: claude-enhancer-config
      terminationGracePeriodSeconds: 30
```

## 📊 监控运维实践

### 监控指标定义

#### 关键业务指标
```yaml
# monitoring/business_metrics.yml
business_metrics:
  agent_selection:
    - name: agent_selection_accuracy
      description: "Agent 选择准确率"
      target: "> 95%"
      alert_threshold: "< 90%"

    - name: task_completion_rate
      description: "任务完成率"
      target: "> 98%"
      alert_threshold: "< 95%"

  performance:
    - name: average_response_time
      description: "平均响应时间"
      target: "< 200ms"
      alert_threshold: "> 500ms"

    - name: concurrent_user_capacity
      description: "并发用户容量"
      target: "> 1000"
      alert_threshold: "< 500"

  reliability:
    - name: system_availability
      description: "系统可用性"
      target: "> 99.9%"
      alert_threshold: "< 99.5%"

    - name: error_rate
      description: "错误率"
      target: "< 0.1%"
      alert_threshold: "> 1%"
```

#### Prometheus 配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'claude-enhancer'
    static_configs:
      - targets: ['claude-enhancer:8080']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### 告警规则配置

#### 关键告警规则
```yaml
# monitoring/alert_rules.yml
groups:
- name: claude_enhancer_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Claude Enhancer 错误率过高"
      description: "错误率超过 1%，当前值: {{ $value }}"

  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "响应时间过慢"
      description: "95% 响应时间超过 500ms，当前值: {{ $value }}s"

  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "内存使用率过高"
      description: "内存使用率超过 90%，当前值: {{ $value | humanizePercentage }}"

  - alert: DatabaseConnectionFailure
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "数据库连接失败"
      description: "PostgreSQL 数据库连接失败"

  - alert: RedisConnectionFailure
    expr: up{job="redis"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Redis 连接失败"
      description: "Redis 缓存服务连接失败"
```

## 👥 团队协作规范

### 代码审查规范

#### Pull Request 模板
```markdown
## 📋 Pull Request 描述

### 🎯 变更类型
- [ ] 新功能 (feature)
- [ ] 修复 (fix)
- [ ] 性能优化 (performance)
- [ ] 重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 测试改进 (test)

### 📝 变更描述
简要描述本次变更的内容和目的。

### 🔧 技术细节
- **影响的组件**:
- **使用的 Agent**:
- **执行的 Phase**:
- **测试覆盖率**:

### ✅ 检查清单
- [ ] 代码已通过本地测试
- [ ] 测试覆盖率 ≥ 80%
- [ ] 文档已更新
- [ ] 遵循代码规范
- [ ] 无安全风险
- [ ] 性能影响评估完成

### 🧪 测试说明
描述如何测试本次变更。

### 📊 性能影响
如有性能影响，请说明预期的性能变化。

### 🔗 相关链接
- Issue: #
- 设计文档:
- 测试报告:
```

#### 代码审查标准
```yaml
code_review_standards:
  mandatory_checks:
    - code_style: "遵循项目代码规范"
    - test_coverage: "新代码测试覆盖率 ≥ 80%"
    - documentation: "公共 API 有完整文档"
    - security: "无明显安全风险"
    - performance: "无明显性能问题"

  recommended_checks:
    - error_handling: "适当的错误处理"
    - logging: "合理的日志记录"
    - maintainability: "代码可维护性"
    - reusability: "代码可复用性"

  review_process:
    - minimum_reviewers: 2
    - approval_required: true
    - auto_merge: false
    - dismiss_stale_reviews: true
```

### 知识分享机制

#### 技术分享模板
```markdown
# 🎓 技术分享：Claude Enhancer 最佳实践

## 📅 分享信息
- **主题**: [分享主题]
- **分享人**: [姓名]
- **时间**: [日期时间]
- **受众**: [目标受众]

## 🎯 分享目标
- 目标1：传授特定技术知识
- 目标2：分享最佳实践经验
- 目标3：解决团队痛点问题

## 📋 内容大纲
1. **背景介绍** (5分钟)
   - 问题背景
   - 解决方案概述

2. **技术深入** (20分钟)
   - 核心技术点
   - 实现细节
   - 代码示例

3. **最佳实践** (10分钟)
   - 经验总结
   - 避坑指南
   - 优化建议

4. **Q&A 讨论** (10分钟)
   - 问题解答
   - 经验交流

## 📚 参考资料
- 官方文档链接
- 相关代码仓库
- 学习资源推荐

## 💡 行动项
- [ ] 知识文档化
- [ ] 团队培训计划
- [ ] 工具或流程改进
```

---

**🎯 总结**:

这份最佳实践指南涵盖了 Claude Enhancer 开发、部署和运维的各个方面。通过遵循这些最佳实践，团队可以：

- 🚀 **提高开发效率**: 标准化的工作流和工具
- 🏗️ **保证代码质量**: 严格的质量标准和审查流程
- 🔒 **增强系统安全**: 全面的安全防护措施
- ⚡ **优化系统性能**: 系统级的性能优化策略
- 📊 **完善监控运维**: 全方位的监控和告警体系
- 👥 **促进团队协作**: 规范的协作流程和知识分享

**持续改进**: 最佳实践应该随着技术发展和团队经验积累不断完善和优化。