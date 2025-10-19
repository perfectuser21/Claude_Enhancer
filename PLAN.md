# 四层架构分层系统实现计划

## 项目概述

**任务目标**: 为Claude Enhancer建立清晰的四层架构分层系统（Main/Core/Feature/Module），固化核心逻辑，支持灵活扩展。

**版本**: 6.5.1 → 6.6.0（Minor版本升级，新增架构分层功能）

**Impact Radius**: 65分（high-risk）→ 使用6个专业Agent并行

## 架构设计

### 四层架构定义

```
┌─────────────────────────────────────────────┐
│  Layer 1: Main（主控层）                     │
│  - 职责: 入口编排，调用其他层                 │
│  - 位置: /, .claude/                         │
│  - 示例: CLAUDE.md, settings.json           │
│  - 修改权限: 任何时候（用户配置）              │
└─────────────────────────────────────────────┘
              ↓ 调用
┌─────────────────────────────────────────────┐
│  Layer 2: Core（核心层）                     │
│  - 职责: 框架规则，系统核心逻辑                │
│  - 位置: .claude/core/                       │
│  - 示例: phase_definitions.yml, loader.py   │
│  - 修改权限: 仅Major版本升级（如v6→v7）        │
│  - 保护机制: pre-commit hook强制检查          │
└─────────────────────────────────────────────┘
              ↓ 被扩展
┌─────────────────────────────────────────────┐
│  Layer 3: Feature（特性层）                  │
│  - 职责: 可插拔的功能扩展                     │
│  - 位置: .claude/features/, acceptance/     │
│  - 示例: BDD场景，检查项，智能加载             │
│  - 修改权限: Minor版本升级（如v6.5→v6.6）      │
│  - 注册机制: registry.yml集中管理             │
└─────────────────────────────────────────────┘
              ↓ 调用
┌─────────────────────────────────────────────┐
│  Layer 4: Module（模块层）                   │
│  - 职责: 通用工具，无业务逻辑                  │
│  - 位置: scripts/, .claude/modules/         │
│  - 示例: 静态检查，版本验证，清理脚本           │
│  - 修改权限: Patch版本升级（如v6.5.1→v6.5.2）  │
│  - 版本追踪: versions.json记录               │
└─────────────────────────────────────────────┘
```

### 依赖规则

```yaml
依赖关系:
  Main:
    can_depend_on: [Core, Feature, Module]
    description: "主控层可以调用任何层"

  Core:
    can_depend_on: [Module]
    cannot_depend_on: [Feature]
    description: "核心层只能依赖Module，不能依赖Feature（保持核心纯粹）"

  Feature:
    can_depend_on: [Core, Module]
    cannot_depend_on: [Feature]
    description: "Feature可以依赖Core和Module，但Feature之间不互相依赖"

  Module:
    can_depend_on: []
    description: "Module完全独立，不依赖任何层（最底层）"
```

## 实现计划

### Phase 1: 规划与架构（当前）

**产出**:
- PLAN.md（本文件）
- 目录结构设计
- 文件清单

**目录结构**:
```
.claude/
├── ARCHITECTURE_LAYERS.md          # 新增：四层架构完整文档
├── core/
│   ├── phase_definitions.yml       # 新增：6-Phase系统定义
│   ├── workflow_rules.yml          # 新增：11步工作流规则
│   ├── quality_thresholds.yml      # 新增：质量阈值
│   ├── loader.py                   # 现有：懒加载优化器
│   └── ...（其他现有core文件）
├── features/
│   ├── registry.yml                # 新增：Feature注册表
│   ├── basic/                      # 现有
│   ├── standard/                   # 现有
│   └── advanced/                   # 现有
└── modules/
    └── versions.json               # 新增：Module版本追踪

scripts/                            # Module层
├── static_checks.sh               # 现有
├── pre_merge_audit.sh            # 现有
└── check_version_consistency.sh  # 现有

.git/hooks/
└── pre-commit                     # 修改：添加Core保护机制
```

### Phase 2: 实现

**任务分解**:

1. **创建Core层定义文件**（api-designer负责）
   - phase_definitions.yml: 定义Phase 0-5的详细规则
   - workflow_rules.yml: 定义11步工作流的转折点
   - quality_thresholds.yml: 定义质量门禁的阈值

2. **创建Feature注册表**（system-architect负责）
   - registry.yml: 注册所有现有Features
   - 定义Feature元数据（版本、依赖、启用状态）

3. **创建Module版本追踪**（devops-engineer负责）
   - versions.json: 记录所有Module的版本
   - 定义Module更新规则

4. **编写架构文档**（technical-writer负责）
   - ARCHITECTURE_LAYERS.md: 完整的四层架构文档
   - 包含：定义、规则、示例、FAQ

5. **修改保护机制**（devops-engineer负责）
   - 在pre-commit中添加Core保护检查
   - 符合Bypass Permissions Mode要求

6. **代码审查**（code-reviewer负责）
   - 验证所有配置文件格式
   - 确保文档完整性

### Phase 3: 测试验证

**测试项**:
1. YAML/JSON文件语法验证
2. Core保护机制功能测试
3. 版本一致性检查
4. 依赖规则验证

### Phase 4: 代码审查

**审查重点**:
1. 配置文件的完整性和正确性
2. 文档的清晰度和准确性
3. 保护机制的有效性
4. 与现有系统的兼容性

### Phase 5: 发布与监控

**发布清单**:
1. 更新VERSION: 6.5.1 → 6.6.0
2. 更新CHANGELOG.md
3. 更新settings.json
4. 创建git tag
5. 验收清单对照

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| Core定义过于严格 | 限制灵活性 | 提供Feature扩展机制 |
| 保护机制阻碍开发 | 开发效率降低 | 支持Bypass Mode，重大升级时可临时禁用 |
| 现有文件分类混乱 | 实施困难 | 先建立分层规则，再逐步迁移 |
| 版本号冲突 | 版本管理混乱 | 使用统一的版本一致性检查 |

## 技术决策

### 决策1: Core层修改权限

**选择**: 仅在Major版本升级时允许修改Core

**理由**:
- Core层是系统基础，频繁修改会导致不稳定
- Major版本允许Breaking Changes，符合语义化版本规范
- 通过Feature层扩展可以满足大部分需求

### 决策2: 保护机制实现方式

**选择**: 在pre-commit中添加检查，支持自动模式bypass

**理由**:
- 符合现有的Bypass Permissions Mode设计
- 不阻碍自动化流程
- 给用户明确的警告信息

### 决策3: 配置文件格式

**选择**: YAML用于定义类配置，JSON用于数据追踪

**理由**:
- YAML更易读，适合人工编辑（phase_definitions.yml）
- JSON更规范，适合程序解析（versions.json）
- 符合业界最佳实践

## Documentation Plan

### README.md Structure

**Target Audience**: Developers who want to check Python/Shell code quality

**Structure**:

```markdown
# Code Quality Checker

## Overview
- One-line description
- Key benefits (3-5 bullet points)
- Use case examples

## Features
- Complexity Detection
  - Cyclomatic complexity analysis
  - Function length monitoring
  - Nesting depth detection
- Naming Convention Check
  - Variable naming patterns
  - Function naming standards
  - Class naming rules
- Report Generation
  - JSON format (machine-readable)
  - Markdown format (human-readable)
  - HTML format (visual reports)

## Installation

### Prerequisites
- Python 3.8+
- pip or pipenv

### Quick Install
```bash
pip install code-quality-checker
```

### From Source
```bash
git clone https://github.com/your-org/code-quality-checker.git
cd code-quality-checker
pip install -e .
```

## Quick Start

### Basic Usage
```bash
# Check a single file
cqc check myfile.py

# Check a directory
cqc check src/

# Generate JSON report
cqc check src/ --format json --output report.json

# Generate Markdown report
cqc check src/ --format markdown --output report.md
```

### Configuration File
```bash
# Generate default config
cqc init

# Use custom config
cqc check src/ --config custom-rules.yml
```

## Command-Line Arguments

### Global Options
| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version | - |
| `--help` | Show help | - |
| `--verbose`, `-v` | Verbose output | false |
| `--quiet`, `-q` | Suppress output | false |

### Check Command
| Option | Description | Default |
|--------|-------------|---------|
| `--format`, `-f` | Output format: json, markdown, html | json |
| `--output`, `-o` | Output file path | stdout |
| `--config`, `-c` | Configuration file | .cqc.yml |
| `--threshold`, `-t` | Fail if score below threshold | 0 |
| `--exclude`, `-e` | Exclude patterns | [] |
| `--include`, `-i` | Include patterns | ['*.py', '*.sh'] |

### Examples
```bash
# Check with custom threshold
cqc check src/ --threshold 80

# Exclude test files
cqc check src/ --exclude "test_*.py" "*.test.py"

# Multiple formats
cqc check src/ -f json -o report.json
cqc check src/ -f markdown -o report.md
cqc check src/ -f html -o report.html
```

## Configuration File

### Structure (rules.yml)
```yaml
# Complexity thresholds
complexity:
  cyclomatic_max: 10        # Maximum cyclomatic complexity
  function_length_max: 50   # Maximum lines per function
  nesting_depth_max: 4      # Maximum nesting depth

# Naming conventions
naming:
  variable_pattern: "^[a-z_][a-z0-9_]*$"     # snake_case
  function_pattern: "^[a-z_][a-z0-9_]*$"     # snake_case
  class_pattern: "^[A-Z][a-zA-Z0-9]*$"       # PascalCase
  constant_pattern: "^[A-Z_][A-Z0-9_]*$"     # UPPER_CASE

# Report settings
report:
  show_suggestions: true
  show_file_metrics: true
  show_summary: true

# Exclusions
exclude:
  - "test_*.py"
  - "*.test.py"
  - "__pycache__"
  - ".venv"
```

### Advanced Configuration
```yaml
# Custom rules
custom_rules:
  - name: "no_print_statements"
    pattern: "\\bprint\\("
    message: "Avoid using print(), use logging instead"
    severity: warning

  - name: "no_global_variables"
    pattern: "^global\\s+"
    message: "Avoid global variables"
    severity: error

# File-specific overrides
overrides:
  - files: "tests/**/*.py"
    complexity:
      cyclomatic_max: 15  # Allow higher complexity in tests
```

## Sample Output

### JSON Report
See [examples/sample_report.json](examples/sample_report.json)

### Markdown Report
See [examples/sample_report.md](examples/sample_report.md)

### HTML Report (Visual)
![Sample HTML Report](docs/images/sample-html-report.png)

## Integration

### CI/CD Integration
```yaml
# .github/workflows/quality-check.yml
- name: Run Code Quality Checks
  run: |
    pip install code-quality-checker
    cqc check src/ --threshold 80 --format json --output cqc-report.json
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/your-org/code-quality-checker
  rev: v1.0.0
  hooks:
    - id: cqc-check
      args: ['--threshold', '80']
```

## Troubleshooting

### Common Issues

#### Issue: "Module not found"
**Solution**: Ensure Python path is configured correctly
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

#### Issue: "Config file not found"
**Solution**: Generate default config
```bash
cqc init
```

#### Issue: "High complexity false positives"
**Solution**: Adjust thresholds in config file or use inline ignores
```python
# cqc: ignore-complexity
def complex_function():
    # ... complex logic
```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
MIT License - see [LICENSE](LICENSE)

## Changelog
See [CHANGELOG.md](CHANGELOG.md)
```

### examples/ Directory Structure

**Purpose**: Provide complete, working examples for users to understand tool behavior

**Directory Layout**:
```
examples/
├── README.md                     # Index of all examples
├── sample_code.py                # Python file with various quality issues
├── sample_script.sh              # Shell script with quality issues
├── sample_report.json            # Example JSON output
├── sample_report.md              # Example Markdown output
├── sample_report.html            # Example HTML output
├── rules.yml                     # Example configuration file
├── rules_strict.yml              # Strict ruleset example
├── rules_relaxed.yml             # Relaxed ruleset example
├── integration/
│   ├── github_actions.yml        # GitHub Actions integration
│   ├── gitlab_ci.yml             # GitLab CI integration
│   └── pre_commit_hook.sh        # Pre-commit hook example
└── output_samples/
    ├── perfect_score.json        # Perfect quality score (100)
    ├── medium_score.json         # Medium quality score (60)
    └── low_score.json            # Low quality score (30)
```

**File Details**:

#### examples/sample_code.py
```python
"""
Sample Python code with various quality issues for demonstration.

This file intentionally contains code quality problems to demonstrate
what the Code Quality Checker can detect.
"""

# Issue 1: Complexity - Cyclomatic complexity too high
def complex_function(x, y, z):
    """Example of overly complex function (cyclomatic > 10)."""
    if x > 0:
        if y > 0:
            if z > 0:
                if x > y:
                    if y > z:
                        return x
                    elif z > x:
                        return z
                    else:
                        return y
                else:
                    if z > x:
                        return z
                    else:
                        return x
            else:
                return y
        else:
            return x
    else:
        return 0


# Issue 2: Function too long (>50 lines)
def very_long_function():
    """Example of function exceeding length limit."""
    result = []
    # ... 60 lines of code ...
    for i in range(100):
        temp = i * 2
        if temp % 2 == 0:
            result.append(temp)
        else:
            result.append(temp + 1)
    # ... more repetitive code ...
    return result


# Issue 3: Naming convention violations
def BadFunctionName():  # Should be snake_case
    """Function name should be snake_case."""
    pass


class snake_case_class:  # Should be PascalCase
    """Class name should be PascalCase."""
    pass


MyVariable = 10  # Variable should be snake_case
CONSTANT_value = 20  # Constant should be UPPER_CASE


# Issue 4: Deep nesting (>4 levels)
def deeply_nested():
    """Example of excessive nesting."""
    for i in range(10):
        if i > 0:
            for j in range(10):
                if j > 0:
                    for k in range(10):
                        if k > 0:
                            print(f"{i}, {j}, {k}")  # Nesting level 5


# Issue 5: No docstring
def missing_docstring(param1, param2):
    return param1 + param2


# Good example: Clean, well-documented function
def calculate_average(numbers: list[float]) -> float:
    """
    Calculate the average of a list of numbers.

    Args:
        numbers: List of numeric values

    Returns:
        float: The average value

    Raises:
        ValueError: If the list is empty

    Example:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

#### examples/sample_script.sh
```bash
#!/bin/bash
# Sample Shell script with quality issues

# Issue 1: Function too complex (many branches)
check_status() {
    if [ "$1" = "ok" ]; then
        if [ "$2" = "yes" ]; then
            if [ "$3" = "true" ]; then
                if [ "$4" = "1" ]; then
                    echo "All good"
                else
                    echo "Step 4 failed"
                fi
            else
                echo "Step 3 failed"
            fi
        else
            echo "Step 2 failed"
        fi
    else
        echo "Step 1 failed"
    fi
}

# Issue 2: Function too long
very_long_function() {
    # 70+ lines of bash code
    echo "Start"
    # ... repetitive code ...
    echo "End"
}

# Issue 3: No error handling
run_command() {
    git pull origin main
    npm install
    npm run build
    # Missing: set -e, error checks, validation
}

# Good example: Clean shell function
setup_environment() {
    # Clean function with error handling
    # Description: Initialize development environment
    # Args: $1 - environment name (dev/staging/prod)
    # Returns: 0 on success, 1 on failure

    set -euo pipefail

    local env="${1:-dev}"

    if [[ ! "$env" =~ ^(dev|staging|prod)$ ]]; then
        echo "Error: Invalid environment '$env'" >&2
        return 1
    fi

    echo "Setting up $env environment..."
    # ... implementation ...
    return 0
}
```

#### examples/sample_report.json
```json
{
  "metadata": {
    "tool": "code-quality-checker",
    "version": "1.0.0",
    "timestamp": "2025-01-19T12:00:00Z",
    "files_analyzed": 2,
    "total_issues": 15
  },
  "summary": {
    "overall_score": 45,
    "grade": "D",
    "complexity_score": 30,
    "naming_score": 60,
    "documentation_score": 50
  },
  "files": [
    {
      "path": "examples/sample_code.py",
      "score": 40,
      "issues": [
        {
          "rule": "cyclomatic_complexity",
          "severity": "error",
          "line": 8,
          "function": "complex_function",
          "message": "Cyclomatic complexity (15) exceeds threshold (10)",
          "suggestion": "Break function into smaller functions"
        },
        {
          "rule": "function_length",
          "severity": "warning",
          "line": 28,
          "function": "very_long_function",
          "message": "Function length (60 lines) exceeds threshold (50)",
          "suggestion": "Extract code into helper functions"
        }
      ]
    }
  ],
  "recommendations": [
    "Reduce cyclomatic complexity in 3 functions",
    "Fix 5 naming convention violations",
    "Add docstrings to 2 functions",
    "Reduce nesting depth in 1 function"
  ]
}
```

#### examples/sample_report.md
```markdown
# Code Quality Report

**Generated**: 2025-01-19 12:00:00 UTC
**Tool**: code-quality-checker v1.0.0

## Summary

| Metric | Score | Grade |
|--------|-------|-------|
| Overall | 45/100 | D |
| Complexity | 30/100 | F |
| Naming | 60/100 | C |
| Documentation | 50/100 | D |

**Files Analyzed**: 2
**Total Issues**: 15

## Issues by Severity

| Severity | Count |
|----------|-------|
| Error | 5 |
| Warning | 7 |
| Info | 3 |

## Detailed Findings

### examples/sample_code.py (Score: 40/100)

#### Errors (3)

1. **Line 8**: Cyclomatic complexity exceeds threshold
   - Function: `complex_function`
   - Actual: 15, Threshold: 10
   - Suggestion: Break function into smaller functions

2. **Line 45**: Naming convention violation
   - Function: `BadFunctionName`
   - Expected: snake_case
   - Suggestion: Rename to `bad_function_name`

3. **Line 55**: Excessive nesting depth
   - Function: `deeply_nested`
   - Depth: 5, Threshold: 4
   - Suggestion: Extract nested logic into helper functions

#### Warnings (4)

1. **Line 28**: Function too long
   - Function: `very_long_function`
   - Length: 60 lines, Threshold: 50
   - Suggestion: Extract code into helper functions

## Recommendations

1. Reduce cyclomatic complexity in 3 functions
2. Fix 5 naming convention violations
3. Add docstrings to 2 functions
4. Reduce nesting depth in 1 function

## Next Steps

- Review and refactor functions with complexity > 10
- Apply consistent naming conventions
- Add comprehensive docstrings
- Consider breaking large functions into smaller units
```

#### examples/rules.yml
```yaml
# Code Quality Checker - Example Configuration
# This file demonstrates all available configuration options

# ==============================================================================
# Complexity Thresholds
# ==============================================================================
complexity:
  # Maximum cyclomatic complexity per function
  # Higher values indicate more complex control flow
  cyclomatic_max: 10

  # Maximum lines per function (excluding comments and blank lines)
  function_length_max: 50

  # Maximum nesting depth (if/for/while/try blocks)
  nesting_depth_max: 4

  # Maximum number of parameters per function
  parameter_count_max: 5

# ==============================================================================
# Naming Conventions (Regex Patterns)
# ==============================================================================
naming:
  # Variables: snake_case (lowercase with underscores)
  variable_pattern: "^[a-z_][a-z0-9_]*$"

  # Functions/Methods: snake_case
  function_pattern: "^[a-z_][a-z0-9_]*$"

  # Classes: PascalCase (capitalize first letter of each word)
  class_pattern: "^[A-Z][a-zA-Z0-9]*$"

  # Constants: UPPER_CASE (all caps with underscores)
  constant_pattern: "^[A-Z_][A-Z0-9_]*$"

  # Private members: _leading_underscore
  private_pattern: "^_[a-z_][a-z0-9_]*$"

# ==============================================================================
# Documentation Requirements
# ==============================================================================
documentation:
  # Require docstrings for functions
  require_function_docstring: true

  # Require docstrings for classes
  require_class_docstring: true

  # Minimum docstring length (characters)
  min_docstring_length: 20

  # Docstring style: google, numpy, sphinx
  docstring_style: "google"

# ==============================================================================
# Report Settings
# ==============================================================================
report:
  # Show detailed suggestions for each issue
  show_suggestions: true

  # Show file-level metrics (LOC, complexity, etc.)
  show_file_metrics: true

  # Show overall summary
  show_summary: true

  # Highlight top N issues
  highlight_top_issues: 10

  # Sort issues by: severity, file, line
  sort_by: "severity"

# ==============================================================================
# Exclusions (Files/Directories to Skip)
# ==============================================================================
exclude:
  # Test files
  - "test_*.py"
  - "*.test.py"
  - "tests/"

  # Generated code
  - "*_pb2.py"
  - "*_pb2_grpc.py"

  # Virtual environments
  - ".venv/"
  - "venv/"
  - "env/"

  # Cache directories
  - "__pycache__/"
  - ".pytest_cache/"
  - ".mypy_cache/"

  # Build artifacts
  - "dist/"
  - "build/"
  - "*.egg-info/"

# ==============================================================================
# Inclusions (Override Exclusions)
# ==============================================================================
include:
  - "*.py"      # Python files
  - "*.sh"      # Shell scripts
  - "*.bash"    # Bash scripts

# ==============================================================================
# Severity Levels
# ==============================================================================
severity:
  # Fail build if any errors found
  fail_on_error: true

  # Fail build if warnings exceed threshold
  fail_on_warning_count: 10

  # Minimum overall score to pass (0-100)
  min_score: 70

# ==============================================================================
# Custom Rules
# ==============================================================================
custom_rules:
  # Disallow print statements (use logging instead)
  - name: "no_print_statements"
    pattern: "\\bprint\\("
    message: "Avoid using print(), use logging instead"
    severity: warning

  # Disallow global variables
  - name: "no_global_variables"
    pattern: "^global\\s+"
    message: "Avoid global variables, use dependency injection"
    severity: error

  # Disallow TODO comments without ticket reference
  - name: "todo_requires_ticket"
    pattern: "# TODO(?!.*TICKET-\\d+)"
    message: "TODO comments must reference a ticket (e.g., TICKET-123)"
    severity: info

# ==============================================================================
# File-Specific Overrides
# ==============================================================================
overrides:
  # Allow higher complexity in test files
  - files: "tests/**/*.py"
    complexity:
      cyclomatic_max: 15
      function_length_max: 100

  # Relax naming for migration scripts
  - files: "migrations/*.py"
    naming:
      function_pattern: ".*"  # Allow any naming
```

### Code Comment Standards

**Function Docstring Format (Google Style)**:
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    One-line summary of what the function does.

    More detailed description if needed. This can span multiple lines
    and provide context about when to use this function.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter
            Can span multiple lines if needed

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> function_name("value1", "value2")
        "expected_output"

    Note:
        Additional notes or warnings
    """
    # Implementation
    pass
```

**Complex Logic Comments**:
```python
# Good: Explain WHY, not WHAT
# Use binary search because dataset can be > 1M records
result = binary_search(data, target)

# Bad: Obvious comment
# Increment counter by 1
counter += 1

# Good: Complex algorithm explanation
# Apply Knuth-Morris-Pratt algorithm for O(n+m) pattern matching
# instead of naive O(n*m) approach because text length can exceed 100k
pattern_index = kmp_search(text, pattern)
```

**Multi-line Complex Logic**:
```python
def process_data(data):
    """Process user data with validation and transformation."""

    # Step 1: Validate input data structure
    # We need to check both schema and data types because
    # downstream consumers expect strict typing
    if not validate_schema(data):
        raise ValueError("Invalid schema")

    # Step 2: Transform to canonical format
    # Apply normalization rules from RFC-5322 for email addresses
    # and E.164 for phone numbers to ensure consistency
    normalized = normalize_data(data)

    # Step 3: Enrich with metadata
    # Add timestamp and version info for audit trail compliance
    enriched = add_metadata(normalized)

    return enriched
```

**TODO/FIXME Comments**:
```python
# TODO(username, TICKET-123): Implement caching layer for performance
# Expected improvement: 50% reduction in API latency

# FIXME(username, TICKET-456): Race condition in concurrent writes
# Temporary workaround: Use global lock (remove when DB supports MVCC)

# HACK(username): Workaround for third-party library bug
# Remove when issue #789 is fixed in library v2.0
```

### Configuration File Comment Standards

**rules.yml Comments**:
```yaml
# ==============================================================================
# Section Header (Use separators for major sections)
# ==============================================================================

complexity:
  # Setting Name: Brief description
  # Why this value: Reasoning behind the threshold
  # Impact: What happens if violated
  cyclomatic_max: 10  # Recommended: 10, Strict: 5, Relaxed: 15

  # Multi-line explanation for complex settings
  # Line 1: What this setting controls
  # Line 2: Why this is important
  # Line 3: How to adjust for your project
  function_length_max: 50

# Inline comments for non-obvious values
naming:
  variable_pattern: "^[a-z_][a-z0-9_]*$"  # snake_case (Python PEP 8)
  class_pattern: "^[A-Z][a-zA-Z0-9]*$"    # PascalCase (Python PEP 8)

# Warning comments for critical settings
severity:
  fail_on_error: true  # WARNING: Setting to false disables quality gates!
```

## Agent分工

| Agent | 职责 | 产出 |
|-------|------|------|
| technical-writer | 编写ARCHITECTURE_LAYERS.md + 文档规划 | 完整架构文档 + Documentation Plan |
| requirements-analyst | 分析需求，创建PLAN.md | 本文件 |
| api-designer | 设计Core层配置文件 | 3个yml文件 |
| system-architect | 设计Feature注册机制 | registry.yml |
| devops-engineer | 修改Hook，创建Module追踪 | 更新的pre-commit + versions.json |
| code-reviewer | 审查所有产出 | REVIEW.md |

## 时间估计

- Phase 0: 已完成（30分钟）
- Phase 1: 进行中（20分钟）
- Phase 2: 预计40分钟（6个Agent并行）
- Phase 3: 预计15分钟
- Phase 4: 预计20分钟
- Phase 5: 预计10分钟

**总计**: 约2.5小时

## 验收标准

参考Phase 0创建的Acceptance Checklist，所有项必须✅才能完成。

---

**规划完成**: 准备进入Phase 2实现阶段
