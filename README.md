# Perfect21 - Claude Code行为规范框架

> 🎯 **Perfect21 v5.0.0** - 定义Claude Code工作规范的智能框架
>
> 规则清晰 + 模式标准化 + 质量保证 = 一致的高质量执行

[![规则体系](https://img.shields.io/badge/规则-YAML配置-blue.svg)](rules/perfect21_rules.yaml)
[![架构文档](https://img.shields.io/badge/架构-分层设计-green.svg)](ARCHITECTURE.md)
[![使用指南](https://img.shields.io/badge/指南-框架说明-orange.svg)](FRAMEWORK_GUIDE.md)
[![最佳实践](https://img.shields.io/badge/实践-经验积累-purple.svg)](FEATURE_GUIDES.md)

## 🚀 核心定位

### ✨ Perfect21是什么

**Perfect21 = Claude Code的行为规范框架**

- **定义规则**: 规定Claude Code应该如何选择和调用Agents
- **提供模式**: 积累的最佳Agent组合和执行模式
- **设置标准**: 质量门、Hook触发、错误处理等标准
- **指导执行**: 给出执行建议，而非直接执行

### 🎯 Perfect21不是什么

- ❌ **不是执行系统** - 所有执行由Claude Code完成
- ❌ **不是工作流引擎** - 只提供规则，不运行工作流
- ❌ **不是独立工具** - 是规范和指南的集合

## 📦 框架结构

```
Perfect21/
├── rules/                      # 核心规则定义
│   ├── perfect21_rules.yaml   # 完整规则配置
│   └── rule_engine.py         # 规则匹配引擎
├── features/                   # 功能模块（按规范组织）
├── CLAUDE.md                   # Claude Code行为规范
├── FRAMEWORK_GUIDE.md          # 框架使用指南
└── FEATURE_GUIDES.md           # Feature专项指导
```

## 🔑 工作原理

```
用户需求
    ↓
Claude Code接收并分析
    ↓
Perfect21规则匹配
    ↓
返回执行指导（Agent组合、执行模式、质量要求）
    ↓
Claude Code按规范执行
```

## 📋 规则体系

### 1. Agent组合规则
根据任务类型定义必须使用的Agent组合：

```yaml
authentication:  # 认证系统任务
  required_agents:
    - backend-architect
    - security-auditor
    - test-engineer
    - api-designer
  execution_mode: parallel  # 必须并行执行
```

### 2. 执行模式规则
定义并行或顺序执行的条件：

```yaml
parallel_conditions:
  - agent_count >= 3        # 3个或更多agents时并行
  - time_critical: true      # 紧急任务必须并行
```

### 3. Git Hook规则
定义Git操作的自动触发行为：

```yaml
pre_commit:
  triggers_on: ["git commit"]
  required_agents: [code-reviewer]
  strict_on_main: true      # 主分支严格检查
```

### 4. 质量门规则
定义必须满足的质量标准：

```yaml
code_quality:
  code_coverage: minimum: 80
  response_time: p95: 200ms
  security: no_vulnerabilities
```

## 🚀 使用方式

### 作为Claude Code的行为指南

```python
# Claude Code应该这样使用Perfect21
from rules.rule_engine import Perfect21RuleEngine

engine = Perfect21RuleEngine()

# 1. 分析任务，获取规范
guidance = engine.analyze_task("实现用户登录系统")

# 2. 获取执行指导
agents = guidance['execution_guidance']['agents_to_use']
mode = guidance['execution_guidance']['execution_mode']

# 3. 按规范执行
if mode == 'parallel':
    # 批量并行调用所有agents
    execute_parallel(agents)
else:
    # 顺序执行
    execute_sequential(agents)
```

### 测试规则引擎

```bash
# 运行测试验证规则匹配
python3 test_rule_engine.py
```

## 🎯 核心价值

### ✅ 标准化执行
- 相同类型任务获得一致的处理
- 避免遗漏重要步骤
- 确保质量标准

### ✅ 最佳实践沉淀
- 成功的Agent组合模式
- 经过验证的执行流程
- 持续优化的规则

### ✅ 质量保证
- 内建质量检查点
- 强制执行标准
- 自动触发验证

### ✅ 个人效率提升
- 减少决策时间
- 避免重复错误
- 专注于业务逻辑

## 📊 示例场景

当遇到"实现用户登录系统"任务时：

**Perfect21分析并返回：**
```yaml
任务类型: authentication
需要Agents: [backend-architect, security-auditor, test-engineer, api-designer]
执行模式: parallel
质量要求:
  - 密码必须加密
  - JWT设置过期时间
  - 实现rate limiting
```

**Claude Code执行：**
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">设计认证系统架构</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">security-auditor</parameter>
    <parameter name="prompt">审查安全性</parameter>
  </invoke>
  <!-- 并行调用所有agents -->
</function_calls>
```

## 💡 设计理念

### 规范优于执行
Perfect21专注于定义"应该怎么做"，而不是"去做"

### 规则优于代码
用声明式规则替代复杂的程序逻辑

### 指导优于控制
提供建议和标准，保持执行的灵活性

### 简单优于复杂
清晰的YAML配置，易于理解和维护

## 🔄 持续改进

Perfect21通过以下方式不断优化：

1. **模式识别** - 发现新的成功Agent组合
2. **规则调整** - 基于执行结果优化规则
3. **标准更新** - 跟随最佳实践演进
4. **经验积累** - 记录并学习每次执行

## 📝 相关文档

- [CLAUDE.md](CLAUDE.md) - 核心行为规范
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计说明
- [FRAMEWORK_GUIDE.md](FRAMEWORK_GUIDE.md) - 框架使用指南
- [FEATURE_GUIDES.md](FEATURE_GUIDES.md) - Feature专项指导

## 🎯 项目定位声明

**Perfect21是一个行为规范框架**，它：
- ✅ 定义Claude Code的工作规范
- ✅ 提供最佳实践和质量标准
- ✅ 确保执行的一致性和质量
- ❌ 不是独立的执行系统
- ❌ 不替代Claude Code的执行能力

---

> **版本**: v5.0.0 | **最后更新**: 2025-09-18
>
> **核心理念**: 规范指导执行，质量内建于过程
>
> **设计原则**: 简单、清晰、有效