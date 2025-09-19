# Perfect21 Hooks System - 完全Claude Hook实现

## 🎯 系统架构

Perfect21的所有规则现已完全转化为Claude Hooks，实现自动化验证和执行。

```
用户请求
    ↓
Claude Code接收
    ↓
Perfect21 Hooks Chain
    ├── task_analyzer     (任务类型识别)
    ├── agent_validator   (Agent数量验证)
    ├── parallel_checker  (并行执行检查)
    └── quality_gates     (质量门控制)
    ↓
执行或阻止
```

## 📦 Hook组件

### 1. **perfect21_task_analyzer.sh**
- 智能识别任务类型（认证、API、数据库等）
- 提供最佳Agent组合建议
- 显示相关最佳实践

### 2. **perfect21_agent_validator.sh**
- 验证Agent数量（最少3个）
- 检查特定任务的必需Agent
- 阻止不符合规则的执行

### 3. **perfect21_parallel_checker.sh**
- 检测执行模式（并行/顺序）
- 警告顺序执行行为
- 推荐并行执行模式

### 4. **perfect21_quality_gates.sh**
- Git提交前质量检查
- 代码编辑后提醒
- 安全扫描和测试验证

### 5. **perfect21_master.sh**
- 主控制器
- 协调所有hooks执行
- 管理执行流程

## 🚀 快速开始

### 安装
```bash
cd /home/xx/dev/Perfect21/.claude/hooks
bash install.sh
```

### 测试
```bash
./test_hooks.sh
```

### 查看日志
```bash
tail -f /tmp/perfect21_*.log
```

## 📋 规则执行

### Agent数量规则
```yaml
最少要求: 3个Agent
推荐数量: 5-7个Agent
执行方式: 强制阻止（少于3个）
```

### 任务类型规则
| 任务类型 | 必需Agent | 推荐Agent |
|---------|-----------|-----------|
| 认证系统 | backend-architect, security-auditor, test-engineer | api-designer, database-specialist |
| API开发 | api-designer, backend-architect, test-engineer | technical-writer |
| 数据库设计 | database-specialist, backend-architect | performance-engineer |
| 前端开发 | frontend-specialist, ux-designer | test-engineer, accessibility-auditor |

### 执行模式规则
- ✅ 并行执行：所有Agent在同一个function_calls块
- ❌ 顺序执行：分开调用（会收到警告）

## 🔧 配置

配置文件：`.claude/hooks/perfect21_config.yaml`

```yaml
hooks:
  agent_validator:
    strict: true      # 严格模式
    min_agents: 3

  parallel_checker:
    strict: false     # 警告模式

  quality_gates:
    checks:
      - test_before_commit
      - lint_check
```

## 📊 Hook行为

### 阻止型（Blocking）
- `agent_validator` - Agent数量不足时阻止
- 返回exit code 1，停止执行

### 警告型（Warning）
- `parallel_checker` - 顺序执行时警告
- `task_analyzer` - 提供建议
- `quality_gates` - 质量提醒

## 💡 工作流示例

### 正确的工作流
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">设计认证架构</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">security-auditor</parameter>
    <parameter name="prompt">安全审查</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">test-engineer</parameter>
    <parameter name="prompt">编写测试</parameter>
  </invoke>
</function_calls>
```
✅ Hook通过：3个Agent，并行执行

### 会被阻止的工作流
```xml
<invoke name="Task">
  <parameter name="subagent_type">backend-architect</parameter>
  <parameter name="prompt">实现所有功能</parameter>
</invoke>
```
❌ Hook阻止：只有1个Agent

## 📝 日志和调试

### 日志文件
- `/tmp/perfect21_master.log` - 主执行日志
- `/tmp/perfect21_agent_log.txt` - Agent选择日志
- `/tmp/perfect21_parallel_log.txt` - 并行执行日志
- `/tmp/perfect21_task_analysis.txt` - 任务分析日志
- `/tmp/perfect21_quality_log.txt` - 质量检查日志
- `/tmp/perfect21_errors.log` - 错误日志

### 调试命令
```bash
# 查看最近的执行
tail -n 50 /tmp/perfect21_master.log

# 查看错误
cat /tmp/perfect21_errors.log

# 实时监控
watch -n 1 "tail -20 /tmp/perfect21_*.log"
```

## 🎯 核心优势

1. **完全自动化** - 无需手动检查规则
2. **智能提醒** - 根据任务类型给出建议
3. **灵活配置** - 可调整严格程度
4. **透明执行** - 详细的日志和反馈
5. **渐进式改进** - 警告和阻止相结合

## 🔄 与原Perfect21对比

| 特性 | 原Perfect21 | Hook版本 |
|-----|------------|----------|
| 规则执行 | 需要手动遵守 | 自动执行 |
| Agent验证 | 事后检查 | 事前阻止 |
| 任务识别 | 手动判断 | 自动识别 |
| 质量检查 | 依赖Git hooks | 集成在Claude hooks |
| 反馈机制 | 延迟反馈 | 实时反馈 |

## 🚦 状态说明

- 🟢 **正常执行** - 所有规则通过
- 🟡 **警告继续** - 有建议但不阻止
- 🔴 **阻止执行** - 违反强制规则
- 🔵 **智能建议** - 提供优化建议

## 📚 扩展和定制

可以通过修改hooks或配置文件来：
- 添加新的任务类型
- 调整Agent组合要求
- 改变阻止/警告行为
- 添加自定义规则

---

*Perfect21 Hooks System v2.0 - 让Claude Code自动遵守最佳实践*