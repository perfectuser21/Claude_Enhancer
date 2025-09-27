# Claude Enhancer 5.0 代码质量审查指南

## 🎯 概述
本指南作为Claude Enhancer 5.0项目的代码质量保障体系，确保代码的可维护性、安全性和性能表现符合最高标准。

---

## 📋 代码质量标准

### 1. **通用质量要求**

#### 1.1 代码可读性 (Score Weight: 25%)
```yaml
可读性标准:
  命名规范:
    - 函数名: 动词开头，驼峰命名 (例: validateConfig, processHook)
    - 变量名: 描述性强，避免缩写 (例: agent_count 而非 ac)
    - 常量名: 全大写+下划线 (例: MAX_AGENTS, DEFAULT_TIMEOUT)
    - 文件名: 小写+下划线 (例: quality_gate.sh, config_manager.py)

  注释要求:
    - 关键业务逻辑必须有注释
    - 复杂算法需要注释说明
    - 函数头部必须有功能描述
    - 配置参数需要说明用途

  代码结构:
    - 单个函数不超过50行
    - 文件不超过500行
    - 逻辑分层清晰
    - 避免深层嵌套(最多3层)
```

#### 1.2 性能要求 (Score Weight: 20%)
```yaml
性能标准:
  响应时间:
    - Hook脚本: < 100ms
    - Python配置加载: < 200ms
    - Agent选择算法: < 50ms
    - 并行任务启动: < 500ms

  内存使用:
    - Hook脚本: < 10MB
    - Python进程: < 100MB
    - 配置缓存: < 50MB
    - 日志文件单个: < 10MB

  并发处理:
    - 支持至少8个并行Agent
    - 文件锁机制防止竞态条件
    - 优雅的错误恢复
```

#### 1.3 安全要求 (Score Weight: 30%)
```yaml
安全标准:
  输入验证:
    - 所有外部输入必须验证
    - 防止命令注入攻击
    - 文件路径必须验证
    - JSON/YAML解析安全处理

  权限控制:
    - 最小权限原则
    - 文件权限正确设置
    - 敏感信息不记录到日志
    - 临时文件安全清理

  错误处理:
    - 不泄露系统内部信息
    - 敏感错误信息脱敏
    - 错误日志分级记录
```

#### 1.4 可维护性 (Score Weight: 25%)
```yaml
可维护性标准:
  模块化设计:
    - 单一职责原则
    - 低耦合高内聚
    - 接口定义清晰
    - 依赖关系简单

  配置管理:
    - 配置与代码分离
    - 环境特定配置
    - 配置验证机制
    - 热更新支持

  测试覆盖:
    - 单元测试覆盖率 > 80%
    - 集成测试覆盖关键流程
    - 性能测试验证
    - 错误场景测试
```

---

## 🔍 代码审查清单

### 2. **Hook脚本审查清单**

#### 2.1 Shell脚本标准
```bash
# ✅ 必须包含的标准模式
#!/bin/bash
set -e  # 错误时退出
set -u  # 未定义变量时退出
set -o pipefail  # 管道错误时退出

# ✅ 输入验证模式
validate_input() {
    local input="$1"

    # 检查输入是否为空
    if [ -z "$input" ]; then
        echo "错误: 输入为空" >&2
        return 1
    fi

    # 检查输入长度
    if [ ${#input} -gt 1000 ]; then
        echo "错误: 输入过长" >&2
        return 1
    fi

    # 检查危险字符
    if echo "$input" | grep -qE '[;&|`$()]'; then
        echo "错误: 输入包含危险字符" >&2
        return 1
    fi
}

# ✅ 安全的文件操作
safe_file_operation() {
    local file_path="$1"
    local lock_file="${file_path}.lock"

    # 创建文件锁
    exec 200>"$lock_file"
    if ! flock -x -w 10 200; then
        echo "错误: 无法获取文件锁" >&2
        return 1
    fi

    # 执行文件操作
    # ... 文件操作代码 ...

    # 释放锁
    flock -u 200
}

# ✅ 错误处理模式
error_handler() {
    local exit_code=$?
    local line_number=$1

    echo "错误发生在第 $line_number 行，退出码: $exit_code" >&2
    cleanup_temp_files
    exit $exit_code
}
trap 'error_handler $LINENO' ERR
```

#### 2.2 Hook脚本检查项
- [ ] **输入安全**: 验证所有外部输入
- [ ] **命令注入防护**: 使用引号保护变量
- [ ] **文件锁机制**: 并发访问保护
- [ ] **错误处理**: 完整的错误恢复机制
- [ ] **日志记录**: 关键操作记录
- [ ] **性能优化**: 避免不必要的外部命令调用
- [ ] **资源清理**: 临时文件和进程清理

### 3. **Python代码审查清单**

#### 3.1 Python代码标准
```python
#!/usr/bin/env python3
"""
模块文档字符串
描述模块的功能、作用和使用方法
"""

import logging
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# ✅ 日志配置模式
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """配置相关的自定义异常"""
    pass

class ConfigManager:
    """配置管理器 - 单一职责原则"""

    def __init__(self, config_path: Path):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径

        Raises:
            ConfigurationError: 配置路径不存在时
        """
        self.config_path = self._validate_path(config_path)
        self.cache: Dict[str, Any] = {}

    def _validate_path(self, path: Path) -> Path:
        """验证路径安全性"""
        if not isinstance(path, Path):
            raise TypeError("路径必须是Path对象")

        # 解析符号链接，防止路径遍历攻击
        resolved_path = path.resolve()

        # 检查路径是否在允许的目录内
        allowed_dirs = [Path.cwd(), Path.home() / '.claude']
        if not any(str(resolved_path).startswith(str(d)) for d in allowed_dirs):
            raise ConfigurationError(f"路径不在允许范围内: {resolved_path}")

        return resolved_path

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            force_reload: 是否强制重新加载

        Returns:
            配置字典

        Raises:
            ConfigurationError: 配置加载失败时
        """
        cache_key = str(self.config_path)

        if not force_reload and cache_key in self.cache:
            logger.debug(f"使用缓存配置: {cache_key}")
            return self.cache[cache_key]

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self._validate_config(config)
            self.cache[cache_key] = config

            logger.info(f"配置加载成功: {self.config_path}")
            return config

        except FileNotFoundError:
            raise ConfigurationError(f"配置文件不存在: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"配置文件格式错误: {e}")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise ConfigurationError(f"配置加载失败: {e}")

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置完整性"""
        required_keys = ['version', 'agents', 'hooks']

        for key in required_keys:
            if key not in config:
                raise ConfigurationError(f"缺少必需的配置项: {key}")

        # 验证版本号格式
        version = config.get('version')
        if not isinstance(version, str) or not version.count('.') == 2:
            raise ConfigurationError(f"版本号格式错误: {version}")
```

#### 3.2 Python代码检查项
- [ ] **类型提示**: 所有函数参数和返回值有类型注解
- [ ] **异常处理**: 具体的异常类型和错误信息
- [ ] **日志记录**: 分级日志记录关键操作
- [ ] **输入验证**: 验证所有外部输入和参数
- [ ] **资源管理**: 使用上下文管理器处理文件等资源
- [ ] **性能考虑**: 缓存机制和惰性加载
- [ ] **文档字符串**: 完整的函数和类文档

---

## 🚨 潜在代码陷阱识别

### 4. **常见安全陷阱**

#### 4.1 命令注入风险
```bash
# ❌ 危险: 未转义的用户输入
eval "echo $user_input"

# ❌ 危险: 动态命令构建
cmd="rm -rf $user_path"
$cmd

# ✅ 安全: 使用printf转义
printf '%q' "$user_input"

# ✅ 安全: 参数数组
rm_cmd=("rm" "-rf" "$user_path")
"${rm_cmd[@]}"
```

#### 4.2 路径遍历攻击
```python
# ❌ 危险: 未验证的路径
def load_file(filename):
    with open(f"/config/{filename}") as f:  # 可被 "../../../etc/passwd" 攻击
        return f.read()

# ✅ 安全: 路径验证
def load_file(filename):
    config_dir = Path("/config").resolve()
    file_path = (config_dir / filename).resolve()

    # 确保文件在允许的目录内
    if not str(file_path).startswith(str(config_dir)):
        raise SecurityError("路径不在允许范围内")

    with open(file_path) as f:
        return f.read()
```

#### 4.3 竞态条件
```bash
# ❌ 危险: 无锁文件操作
if [ ! -f "$lock_file" ]; then
    echo "$$" > "$lock_file"  # 竞态条件窗口
    # 关键操作
    rm "$lock_file"
fi

# ✅ 安全: 原子锁操作
{
    flock -x 200
    # 关键操作
} 200>"$lock_file"
```

### 5. **性能陷阱**

#### 5.1 内存泄漏
```python
# ❌ 危险: 无限增长的缓存
class ConfigCache:
    def __init__(self):
        self.cache = {}  # 永不清理

    def get(self, key):
        if key not in self.cache:
            self.cache[key] = expensive_operation(key)
        return self.cache[key]

# ✅ 安全: LRU缓存
from functools import lru_cache

class ConfigCache:
    @lru_cache(maxsize=128)
    def get(self, key):
        return expensive_operation(key)
```

#### 5.2 阻塞操作
```python
# ❌ 危险: 同步I/O阻塞
def process_configs():
    for config_file in config_files:
        with open(config_file) as f:  # 阻塞整个流程
            process(f.read())

# ✅ 优化: 异步处理
import asyncio
import aiofiles

async def process_configs():
    tasks = []
    for config_file in config_files:
        tasks.append(process_config_async(config_file))
    await asyncio.gather(*tasks)

async def process_config_async(config_file):
    async with aiofiles.open(config_file) as f:
        content = await f.read()
        await process_async(content)
```

---

## 💡 最佳实践建议

### 6. **Hook脚本最佳实践**

#### 6.1 标准化模板
```bash
#!/bin/bash
# Hook脚本标准模板
# 功能: [描述Hook的具体功能]
# 作者: [作者信息]
# 版本: [版本号]

set -euo pipefail  # 严格模式

# 全局变量
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
readonly LOG_FILE="/tmp/claude_${SCRIPT_NAME%.sh}.log"

# 日志函数
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# 清理函数
cleanup() {
    local exit_code=$?
    log_info "清理临时资源..."
    # 清理逻辑
    exit $exit_code
}
trap cleanup EXIT

# 主要逻辑
main() {
    log_info "开始执行 $SCRIPT_NAME"

    # 输入验证
    validate_input "$@"

    # 核心处理逻辑
    process_hook_logic "$@"

    log_info "$SCRIPT_NAME 执行完成"
}

# 输入验证函数
validate_input() {
    # 实现具体的输入验证逻辑
    :
}

# 核心处理函数
process_hook_logic() {
    # 实现具体的Hook逻辑
    :
}

# 程序入口
main "$@"
```

#### 6.2 错误恢复策略
```bash
# 错误恢复机制
retry_with_backoff() {
    local max_attempts=3
    local delay=1
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if "$@"; then
            return 0
        fi

        log_warn "尝试 $attempt/$max_attempts 失败，${delay}秒后重试"
        sleep $delay

        attempt=$((attempt + 1))
        delay=$((delay * 2))  # 指数退避
    done

    log_error "所有重试失败"
    return 1
}

# 使用示例
retry_with_backoff curl -f "$api_endpoint"
```

### 7. **配置管理最佳实践**

#### 7.1 分层配置策略
```yaml
# 配置优先级 (高到低):
# 1. 环境变量
# 2. 命令行参数
# 3. 环境特定配置文件
# 4. 主配置文件
# 5. 默认值

# 主配置文件 (main.yaml)
metadata:
  version: "5.1.0"
  schema_version: "1.0"

defaults:
  timeout: 30
  max_retries: 3
  log_level: "INFO"

# 环境特定配置 (production.yaml)
performance:
  timeout: 10
  max_retries: 5

logging:
  level: "WARN"
  format: "structured"
```

#### 7.2 配置验证Schema
```yaml
# config_schema.yaml
type: object
required:
  - metadata
  - agents
  - hooks

properties:
  metadata:
    type: object
    required: [version, schema_version]
    properties:
      version:
        type: string
        pattern: '^\d+\.\d+\.\d+$'
      schema_version:
        type: string
        pattern: '^\d+\.\d+$'

  agents:
    type: object
    properties:
      count_limits:
        type: object
        properties:
          min: { type: integer, minimum: 1, maximum: 3 }
          max: { type: integer, minimum: 5, maximum: 10 }

  hooks:
    type: object
    additionalProperties:
      type: object
      properties:
        enabled: { type: boolean }
        timeout: { type: integer, minimum: 1, maximum: 300 }
```

---

## 🔄 代码复用策略

### 8. **模块化设计原则**

#### 8.1 通用工具函数库
```bash
# 创建通用工具库
# .claude/lib/common.sh

# 安全的JSON解析
safe_json_parse() {
    local json_string="$1"
    local key_path="$2"

    echo "$json_string" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    keys = '$key_path'.split('.')
    result = data
    for key in keys:
        if key in result:
            result = result[key]
        else:
            sys.exit(1)
    print(result)
except:
    sys.exit(1)
"
}

# 安全的文件锁操作
with_file_lock() {
    local lock_file="$1"
    local timeout="${2:-10}"
    shift 2

    exec 200>"$lock_file"
    if flock -x -w "$timeout" 200; then
        "$@"
        local exit_code=$?
        flock -u 200
        return $exit_code
    else
        echo "获取文件锁失败: $lock_file" >&2
        return 1
    fi
}
```

#### 8.2 Python通用模块
```python
# .claude/lib/common.py

import logging
import functools
import time
from typing import Callable, Any, Optional
from pathlib import Path

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0,
                    backoff_factor: float = 2.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        sleep_time = delay * (backoff_factor ** attempt)
                        logging.warning(
                            f"尝试 {attempt + 1}/{max_attempts} 失败: {e}, "
                            f"{sleep_time:.1f}秒后重试"
                        )
                        time.sleep(sleep_time)

            raise last_exception
        return wrapper
    return decorator

def safe_file_operation(file_path: Path, mode: str = 'r',
                       encoding: str = 'utf-8', timeout: int = 10):
    """安全的文件操作上下文管理器"""
    import fcntl

    class SafeFileContext:
        def __init__(self, path, mode, encoding, timeout):
            self.path = path
            self.mode = mode
            self.encoding = encoding
            self.timeout = timeout
            self.file = None

        def __enter__(self):
            self.file = open(self.path, self.mode, encoding=self.encoding)

            # 设置文件锁
            try:
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                self.file.close()
                raise TimeoutError(f"无法获取文件锁: {self.path}")

            return self.file

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.file:
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
                self.file.close()

    return SafeFileContext(file_path, mode, encoding, timeout)

class ConfigValidator:
    """配置验证器基类"""

    @staticmethod
    def validate_version(version: str) -> bool:
        """验证版本号格式"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    @staticmethod
    def validate_timeout(timeout: Any) -> bool:
        """验证超时设置"""
        return isinstance(timeout, int) and 1 <= timeout <= 300

    @staticmethod
    def validate_path(path: Any, must_exist: bool = False) -> bool:
        """验证路径"""
        if not isinstance(path, (str, Path)):
            return False

        path_obj = Path(path)

        if must_exist and not path_obj.exists():
            return False

        # 检查路径遍历攻击
        try:
            path_obj.resolve().relative_to(Path.cwd())
            return True
        except ValueError:
            return False
```

### 9. **代码复用检查清单**

- [ ] **函数复用**: 识别重复代码片段，抽取为通用函数
- [ ] **配置复用**: 通用配置模式标准化
- [ ] **错误处理复用**: 统一的错误处理和恢复机制
- [ ] **日志复用**: 标准化日志记录模式
- [ ] **测试复用**: 通用测试工具和模式
- [ ] **文档复用**: 模板化文档结构

---

## 🎯 质量门禁流程

### 10. **自动化质量检查**

#### 10.1 Pre-commit检查
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 1. 代码格式检查
echo "🔍 检查代码格式..."
if command -v black >/dev/null 2>&1; then
    black --check .
fi

if command -v flake8 >/dev/null 2>&1; then
    flake8 .
fi

# 2. Shell脚本检查
echo "🔍 检查Shell脚本..."
find . -name "*.sh" -type f | while read -r file; do
    if command -v shellcheck >/dev/null 2>&1; then
        shellcheck "$file" || exit 1
    fi
done

# 3. 安全检查
echo "🔍 安全检查..."
if command -v bandit >/dev/null 2>&1; then
    bandit -r . -f json -o security_report.json
fi

# 4. 测试执行
echo "🧪 运行测试..."
if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
    pytest --cov=.claude --cov-report=term-missing
fi

echo "✅ 质量检查通过"
```

#### 10.2 持续集成检查
```yaml
# .github/workflows/quality_check.yml
name: Quality Check

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: 设置Python环境
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: 安装依赖
        run: |
          pip install -r requirements-dev.txt

      - name: 代码格式检查
        run: |
          black --check .
          flake8 .
          mypy .

      - name: 安全检查
        run: |
          bandit -r .claude
          safety check

      - name: 测试覆盖率
        run: |
          pytest --cov=.claude --cov-report=xml

      - name: 性能基准测试
        run: |
          python .claude/scripts/performance_benchmark.py

      - name: 上传测试报告
        uses: codecov/codecov-action@v1
        with:
          file: ./coverage.xml
```

---

## 📊 质量评分体系

### 11. **代码质量评分标准**

```yaml
质量评分算法:
  总分: 100分

  可读性 (25分):
    - 命名规范: 5分
    - 注释完整性: 5分
    - 代码结构: 5分
    - 函数复杂度: 5分
    - 文档字符串: 5分

  安全性 (30分):
    - 输入验证: 8分
    - 权限控制: 7分
    - 错误处理: 8分
    - 敏感信息保护: 7分

  性能 (20分):
    - 响应时间: 5分
    - 内存使用: 5分
    - 并发处理: 5分
    - 资源管理: 5分

  可维护性 (25分):
    - 模块化程度: 5分
    - 测试覆盖率: 5分
    - 配置管理: 5分
    - 依赖管理: 5分
    - 代码复用: 5分

评分等级:
  优秀: 90-100分
  良好: 80-89分
  及格: 70-79分
  需改进: < 70分
```

### 12. **质量报告模板**

```markdown
# 代码质量审查报告

## 📊 总体评分: {总分}/100

### 🎯 分项得分
- **可读性**: {可读性得分}/25
- **安全性**: {安全性得分}/30
- **性能**: {性能得分}/20
- **可维护性**: {可维护性得分}/25

### ✅ 优点
- [列出代码的优秀实践]

### ⚠️ 需要改进
- [列出需要改进的问题]

### 🚨 严重问题
- [列出安全或性能严重问题]

### 💡 建议
- [具体的改进建议]

### 📋 行动计划
- [ ] 高优先级修复项
- [ ] 中优先级改进项
- [ ] 低优先级优化项
```

---

## 🛠️ 工具配置

### 13. **开发工具集成**

#### 13.1 VS Code配置
```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,

  "shellcheck.enable": true,
  "shellformat.useEditorConfig": true,

  "files.associations": {
    "*.yaml": "yaml",
    "*.yml": "yaml",
    ".claude/**": "yaml"
  },

  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### 13.2 Pre-commit配置
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy

  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.8.0
    hooks:
      - id: shellcheck

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ['-c', '.bandit']

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.26.3
    hooks:
      - id: yamllint
```

---

## 📈 质量改进路线图

### 14. **阶段性改进计划**

#### Phase 1: 基础规范 (1-2周)
- [ ] 建立代码规范文档
- [ ] 配置自动化检查工具
- [ ] 培训开发团队规范

#### Phase 2: 安全加固 (2-3周)
- [ ] 安全漏洞扫描和修复
- [ ] 输入验证加强
- [ ] 权限控制优化

#### Phase 3: 性能优化 (3-4周)
- [ ] 性能基准测试建立
- [ ] 瓶颈识别和优化
- [ ] 监控系统完善

#### Phase 4: 持续改进 (持续)
- [ ] 质量指标监控
- [ ] 定期代码审查
- [ ] 最佳实践更新

---

## 🎓 培训资源

### 15. **代码质量培训**

#### 15.1 Shell脚本最佳实践
- [ShellCheck Wiki](https://github.com/koalaman/shellcheck/wiki)
- [Bash Style Guide](https://google.github.io/styleguide/shellguide.html)

#### 15.2 Python代码质量
- [PEP 8 Style Guide](https://pep8.org/)
- [Clean Code in Python](https://github.com/zedr/clean-code-python)

#### 15.3 安全编程
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)

---

**🏆 质量是成功的基石，让我们共同构建高质量的Claude Enhancer 5.0！**

---

*此文档版本: 1.0.0*
*最后更新: 2024年*
*维护者: Claude Code Review Team*