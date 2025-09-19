# 🎯 Perfect21框架使用指南

> Perfect21是Claude Code的行为规范框架，不是独立的执行系统

## 📋 框架本质

**Perfect21定义规则，Claude Code执行任务**

```
用户需求 → Claude Code分析 → Perfect21规则匹配 → Claude Code按规则执行
```

## 🔑 核心文件

### 1. 规则定义
- `rules/perfect21_rules.yaml` - 完整的规则配置
- `rules/rule_engine.py` - 规则匹配引擎

### 2. 使用方式

```python
from rules.rule_engine import Perfect21RuleEngine

# Claude Code应该这样使用Perfect21
engine = Perfect21RuleEngine()

# 1. 分析任务，获取执行指导
guidance = engine.analyze_task("实现用户登录系统")

# 2. 按照指导执行
agents_to_use = guidance['execution_guidance']['agents_to_use']
execution_mode = guidance['execution_guidance']['execution_mode']

# 3. 如果是并行执行
if execution_mode == 'parallel':
    # 在一个消息中同时调用所有agents
    pass
```

## 📐 规则类型

### 1. Agent组合规则
定义不同任务类型应该使用哪些Agent组合

```yaml
authentication:
  required_agents:
    - backend-architect
    - security-auditor
    - test-engineer
    - api-designer
  execution_mode: parallel
```

### 2. 执行模式规则
定义什么情况下并行，什么情况下顺序执行

```yaml
parallel_conditions:
  - agent_count >= 3
  - time_critical: true
```

### 3. Git Hook规则
定义Git操作时的自动触发行为

```yaml
pre_commit:
  triggers_on: ["git commit"]
  required_agents: [code-reviewer]
```

### 4. 质量门规则
定义必须满足的质量标准

```yaml
code_quality:
  metrics:
    - code_coverage: minimum: 80
    - complexity: maximum: 10
```

## 🎯 框架价值

### ✅ 标准化
每次执行都遵循相同的高标准

### ✅ 最佳实践
积累的经验变成强制规范

### ✅ 质量保证
不会遗漏重要步骤

### ✅ 一致性
相同类型任务得到相同质量的处理

## 💡 重要区别

### ❌ Perfect21不是
- 独立的执行系统
- 工作流引擎
- 自动化工具

### ✅ Perfect21是
- 行为规范
- 执行指南
- 最佳实践集合
- 质量标准定义

## 🚀 使用建议

1. **任务开始前** - 用Perfect21分析任务，获取执行指导
2. **执行过程中** - 严格遵循Perfect21的规则
3. **质量检查时** - 用Perfect21的质量门验证结果
4. **Git操作时** - 遵循Perfect21的Hook规则

## 📊 示例输出

当Claude Code遇到"实现用户登录系统"的任务时：

```
Perfect21分析结果：
- 任务类型: authentication
- 需要Agents: [backend-architect, security-auditor, test-engineer, api-designer]
- 执行模式: parallel（并行）
- 质量要求:
  - 密码必须加密
  - JWT必须有过期时间
  - 必须有rate limiting

Claude Code的执行：
<function_calls>
  <invoke name="Task">backend-architect...</invoke>
  <invoke name="Task">security-auditor...</invoke>
  <invoke name="Task">test-engineer...</invoke>
  <invoke name="Task">api-designer...</invoke>
</function_calls>
```

## 🔄 持续改进

Perfect21的规则会根据实践经验不断优化：

1. 记录哪些Agent组合效果好
2. 识别新的任务模式
3. 更新质量标准
4. 优化执行规则

---

**记住：Perfect21是规范和指南，执行永远由Claude Code完成**