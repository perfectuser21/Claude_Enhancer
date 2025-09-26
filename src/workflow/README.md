# Claude Enhancer 5.0 - Workflow Permission System

## 概述 | Overview

Claude Enhancer 5.0 的工作流权限控制系统，基于 8-Phase 工作流框架，提供严格的权限控制和安全审计功能。

## 核心功能 | Core Features

### 🛡️ Phase-Based Access Control
- **P0 (Branch Creation)**: 仅允许 Git 操作
- **P1 (Requirements)**: 只读分析模式
- **P2 (Design)**: 文档和设计工件
- **P3 (Implementation)**: 完整开发权限 (4-8 Agent)
- **P4 (Testing)**: 测试执行和有限代码修改
- **P5 (Commit)**: 仅 Git 提交操作
- **P6 (Review)**: PR 和审查操作

### 🚫 Restriction Engine
1. **Tool Restrictions**: 基于阶段的工具使用限制
2. **File Access Control**: 白名单/黑名单文件访问控制
3. **Agent Limits**: 并行 Agent 数量限制
4. **Command Filtering**: Bash 命令过滤和验证

### 📊 Security Audit System
- Real-time violation detection
- Comprehensive audit logging
- Permission violation reports
- Security incident tracking

## 架构设计 | Architecture

```
src/workflow/
├── permission_controller.sh          # 核心权限控制器
├── README.md                         # 系统文档
├── config/                          # 配置管理
│   ├── permission_rules.json        # 权限规则配置
│   ├── phase_definitions.json       # 阶段定义
│   └── security_policies.json       # 安全策略
├── validators/                      # 验证器模块
│   ├── tool_validator.sh           # 工具使用验证
│   ├── file_validator.sh           # 文件访问验证
│   └── agent_validator.sh          # Agent 数量验证
└── reports/                        # 报告生成器
    ├── violation_reporter.sh        # 违规报告生成器
    └── audit_analyzer.sh           # 审计日志分析器
```

## 使用方法 | Usage

### 基本命令 | Basic Commands

```bash
# 验证工具使用权限
./permission_controller.sh validate-tool Write '{"file_path": "src/main.js"}'

# 检查文件修改权限
./permission_controller.sh check-file src/components/App.jsx

# 检查 Agent 数量限制
./permission_controller.sh check-agents 6

# 获取当前阶段
./permission_controller.sh get-phase

# 设置当前阶段
./permission_controller.sh set-phase P3

# 生成违规报告
./permission_controller.sh generate-report

# 显示阶段权限
./permission_controller.sh show-permissions P3
```

### 集成示例 | Integration Examples

#### 在 Claude Code Hook 中使用

```bash
#!/bin/bash
# .claude/hooks/permission_check.sh

PERMISSION_CONTROLLER="./src/workflow/permission_controller.sh"

# 检查工具使用权限
if ! $PERMISSION_CONTROLLER validate-tool "$TOOL_NAME" "$CONTEXT_DATA"; then
    echo "❌ Permission denied for tool: $TOOL_NAME"
    exit 1
fi

echo "✅ Tool usage approved"
```

#### 在 CI/CD 流程中使用

```yaml
# .github/workflows/permission-check.yml
name: Permission Check
on: [push, pull_request]

jobs:
  permission-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate Permission Report
        run: |
          ./src/workflow/permission_controller.sh generate-report
          cat .claude/logs/permission_violation_report.json
```

## 权限矩阵 | Permission Matrix

| Phase | Tools Allowed | File Access | Max Agents | Restrictions |
|-------|---------------|-------------|------------|--------------|
| **P0** | Bash, Read | .git/**, README | 0 | Git operations only |
| **P1** | Read, Grep, Glob | docs/**, .claude/** | 0 | Read-only analysis |
| **P2** | Read, Write, Grep | docs/**, design/** | 2 | Documentation only |
| **P3** | Task, Write, MultiEdit | src/**, test/** | 4-8 | Full development |
| **P4** | Bash, Read, Write | test/**, src/** | 3 | Testing focused |
| **P5** | Bash, Read | .git/** | 0 | Commit operations |
| **P6** | Bash, Read | .git/**, .github/** | 0 | Review operations |

## 配置管理 | Configuration Management

### 权限规则配置 | Permission Rules

```json
{
  "phases": {
    "P3": {
      "name": "Implementation",
      "allowed_tools": ["Task", "Write", "MultiEdit"],
      "forbidden_tools": ["Bash"],
      "max_agents": 8,
      "file_whitelist": ["src/**", "test/**"],
      "file_blacklist": [".git/**", "node_modules/**"],
      "restrictions": {
        "parallel_agents_required": true,
        "minimum_agents": 4
      }
    }
  }
}
```

### 全局限制 | Global Restrictions

```json
{
  "global_restrictions": {
    "sensitive_files": [".env*", "**/*.key", "**/*.pem"],
    "max_concurrent_agents": 8,
    "max_file_modifications_per_phase": {
      "P3": 100,
      "P4": 20
    }
  }
}
```

## 安全审计 | Security Audit

### 违规检测 | Violation Detection

系统会自动检测以下违规行为：
- 在错误阶段使用禁用工具
- 修改非白名单文件
- 超出 Agent 数量限制
- 执行未授权的 Bash 命令

### 审计日志 | Audit Logs

```json
{
  "timestamp": "2025-09-26T15:30:45.123Z",
  "phase": "P1",
  "tool": "Write",
  "violation_type": "FORBIDDEN_TOOL",
  "details": "Tool 'Write' not allowed in phase 'P1'",
  "severity": "HIGH",
  "action_taken": "BLOCKED"
}
```

### 违规报告 | Violation Reports

系统会生成详细的违规报告，包括：
- 违规总数统计
- 按阶段分类的违规情况
- 按工具分类的违规情况
- 详细的违规记录

## 最佳实践 | Best Practices

### 1. 阶段驱动开发 | Phase-Driven Development

```bash
# P1: 需求分析
./permission_controller.sh set-phase P1
# 只能使用 Read, Grep, Glob 进行分析

# P2: 设计规划
./permission_controller.sh set-phase P2
# 可以创建设计文档和架构图

# P3: 实现开发
./permission_controller.sh set-phase P3
# 使用 4-8 个 Agent 并行开发

# P4: 本地测试
./permission_controller.sh set-phase P4
# 运行测试并修复问题

# P5: 代码提交
./permission_controller.sh set-phase P5
# 提交代码到 Git
```

### 2. 权限验证集成 | Permission Integration

在执行任何工具操作前，都应先验证权限：

```bash
# 验证工具权限
if ./permission_controller.sh validate-tool "$TOOL"; then
    # 执行工具操作
    execute_tool "$TOOL" "$ARGS"
else
    # 权限被拒绝
    echo "Permission denied for tool: $TOOL"
    exit 1
fi
```

### 3. 自动化权限检查 | Automated Permission Checks

```bash
# 在 pre-commit hook 中检查
#!/bin/bash
VIOLATIONS=$(./src/workflow/permission_controller.sh generate-report | jq '.summary.total_violations')
if [[ "$VIOLATIONS" -gt 0 ]]; then
    echo "❌ Permission violations detected: $VIOLATIONS"
    exit 1
fi
```

## 故障排除 | Troubleshooting

### 常见问题 | Common Issues

1. **权限被拒绝**
   ```bash
   # 检查当前阶段
   ./permission_controller.sh get-phase

   # 查看阶段权限
   ./permission_controller.sh show-permissions P3
   ```

2. **配置文件错误**
   ```bash
   # 重新初始化配置
   ./permission_controller.sh init-config
   ```

3. **审计日志查看**
   ```bash
   # 查看最近的审计记录
   ./permission_controller.sh audit-log 50
   ```

## 性能优化 | Performance Optimization

- **缓存机制**: 配置文件和规则缓存
- **惰性加载**: 按需加载权限规则
- **批量验证**: 支持批量权限检查
- **异步日志**: 非阻塞审计日志记录

## 扩展性 | Extensibility

系统设计支持：
- 自定义权限规则
- 插件化验证器
- 多租户权限隔离
- 动态权限策略更新

## 监控和告警 | Monitoring & Alerting

```bash
# 监控违规情况
watch -n 60 './permission_controller.sh generate-report | jq .summary'

# 设置告警阈值
if [[ $(jq '.summary.total_violations' report.json) -gt 10 ]]; then
    echo "🚨 High violation count detected"
    # 发送告警通知
fi
```

## 版本历史 | Version History

- **v5.0.0**: 初始版本，支持完整的 8-Phase 权限控制
- 基于 Claude Enhancer 5.0 架构设计
- 支持实时权限验证和安全审计

---

> **注意**: 此系统是 Claude Enhancer 5.0 的核心安全组件，确保工作流的规范性和安全性。在生产环境中使用前，请充分测试所有权限规则和验证逻辑。