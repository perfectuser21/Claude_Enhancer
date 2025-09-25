# Claude Enhancer 命名规范

## 📋 总体原则

1. **清晰优于简短**：`validate_user_input` > `val_usr`
2. **一致性至上**：同类型使用相同模式
3. **自解释性**：看名字就知道用途
4. **避免缩写**：除非是通用缩写（如 `config`, `utils`）

## 🗂️ 文件命名

### Python文件
```python
# 功能描述_动作.py
code_validator.py      # 代码验证器
agent_selector.py      # Agent选择器
format_checker.py      # 格式检查器

# 避免
validate.py           # 太宽泛
cv.py                # 缩写不清
CodeValidator.py     # 不用大写开头
```

### Shell脚本
```bash
# 动作_对象.sh
install_hooks.sh      # 安装hooks
cleanup_cache.sh      # 清理缓存
protect_architecture.sh # 保护架构

# Phase相关
phase0_branch.sh      # Phase脚本带数字
phase1_analysis.sh
```

### 配置文件
```yaml
# 用途.yaml 或 用途_环境.yaml
config.yaml           # 主配置
config_dev.yaml       # 开发配置
agent_468.yaml        # 特定策略配置
```

### Markdown文档
```markdown
# 全大写用于重要文档
README.md
ARCHITECTURE.md
GROWTH-STRATEGY.md

# 普通文档可混合
api-guide.md
deployment-notes.md
```

## 📁 目录命名

### 层级目录（L0-L3）
```
core/         # 单数，小写
framework/    # 单数，小写
services/     # 复数，表示多个服务
features/     # 复数，表示多个特性
```

### Feature分类
```
features/
├── basic/      # 形容词，表示级别
├── standard/   # 形容词，表示级别
└── advanced/   # 形容词，表示级别
```

### 功能目录
```
validation/     # 名词，表示功能类型
formatting/     # 动名词，表示动作类型
agents/         # 复数名词，表示集合
utils/          # 通用缩写，工具集
```

## 🐍 Python命名

### 类名
```python
# PascalCase（大驼峰）
class WorkflowEngine:
class AgentOrchestrator:
class CodeValidator:

# 避免
class workflow_engine:  # 应该用大驼峰
class WFEngine:        # 避免缩写
```

### 函数和方法
```python
# snake_case（蛇形）
def execute_phase():
def validate_input():
def get_agent_list():

# 私有方法
def _internal_process():
def _check_validity():
```

### 变量
```python
# snake_case（蛇形）
phase_count = 8
agent_list = []
is_valid = True

# 常量
MAX_AGENTS = 8
DEFAULT_TIMEOUT = 30
PHASE_NAMES = ["branch", "analysis", ...]
```

### 模块级私有
```python
# 单下划线前缀
_internal_cache = {}
_config_loaded = False

def _private_helper():
    pass
```

## 🔧 Shell命名

### 变量
```bash
# 大写下划线
PROJECT_ROOT="/home/xx/dev/Claude Enhancer"
AGENT_COUNT=6
IS_VERBOSE=false

# 局部变量可小写
local file_path="$1"
local result=""
```

### 函数
```bash
# 小写下划线
function check_requirements() {
    # ...
}

function validate_agent() {
    # ...
}
```

## 📦 Feature命名

### Basic Features
```
# 动作_对象.py 或 功能.py
quick_fix.py
auto_format.py
git_helper.py
```

### Standard Features
```
features/standard/
├── code_review/      # 功能名，下划线连接
├── test_runner/      # 动作_对象
└── doc_generator/    # 对象_生成器
```

### Advanced Features
```
features/advanced/
├── ai_workflow/           # 技术_功能
├── deployment_platform/   # 用途_类型
└── testing_framework/     # 功能_框架类型
```

## 🏷️ Git相关

### 分支名
```bash
feature/add-code-validator
fix/phase3-agent-selection
refactor/cleanup-architecture
docs/update-growth-strategy
```

### 提交信息
```bash
feat: 添加代码验证器
fix: 修复Phase3 Agent选择逻辑
refactor: 重构架构文档结构
docs: 更新成长策略文档
```

### 标签
```bash
v2.0.0          # 版本号
v2.1.0-beta     # 预发布
milestone-100-features  # 里程碑
```

## 🔤 缩写约定

### 允许的缩写
```
config → 配置
utils → 工具
docs → 文档
lib → 库
init → 初始化
repo → 仓库
env → 环境
dev → 开发
```

### 避免的缩写
```
❌ val → validation
❌ fmt → format
❌ chk → check
❌ proc → process
❌ mgr → manager
```

## 📝 注释和文档

### 文件头注释
```python
"""
模块功能简述

详细描述（可选）
"""

# 或者

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Enhancer - 代码验证器
用于验证代码质量和规范
"""
```

### 类和函数文档
```python
class Validator:
    """验证器基类

    用于所有验证器的基类实现
    """

    def validate(self, code: str) -> bool:
        """验证代码

        Args:
            code: 要验证的代码字符串

        Returns:
            验证是否通过
        """
```

## ⚠️ 命名检查清单

创建新文件/目录前，确认：
- [ ] 名称清晰表达用途
- [ ] 遵循对应类型的命名规范
- [ ] 与同类型文件保持一致
- [ ] 没有使用模糊缩写
- [ ] 检查是否有重名

## 🔄 重命名指南

如需重命名：
1. 先在ARCHITECTURE/decisions/记录决策
2. 使用脚本批量重命名
3. 更新所有引用
4. 提交说明清楚原因

---
*命名规范版本：v2.0*
*强制执行日期：2025-09-23起*