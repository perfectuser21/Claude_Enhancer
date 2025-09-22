# 🎯 Claude Enhancer 系统总览

## 文档结构说明

### 1. `/CLAUDE.md` （项目根目录）
- **作用**：快速概览，给用户看的简介
- **内容**：核心概念介绍
- **详细度**：⭐⭐

### 2. `/.claude/` 目录（核心系统）
- **作用**：Claude Code实际执行的详细规则
- **内容**：完整的实现细节
- **详细度**：⭐⭐⭐⭐⭐

## 📁 完整文档体系

### 核心执行文档
- `DETAILED_WORKFLOW.md` - 8-Phase详细步骤
- `AGENT_RULES.md` - Agent调用规则
- `SELF_CHECK_MECHANISM.md` - 自检机制
- `ENFORCEMENT_STRATEGY.md` - 强制策略

### 安全与控制
- `SAFETY_RULES.md` - 危险操作防护
- `OUTPUT_CONTROL_STRATEGY.md` - 输出长度控制
- `PHASE_FLOW_CONTROLLER.md` - Phase流程控制

### 使用指南
- `QUICK_START.md` - 快速开始
- `ISSUES_AND_SOLUTIONS.md` - 问题与解决

### 策略文档
- `AGENT_STRATEGY.md` - Agent选择策略
- `PHASE_AGENT_STRATEGY.md` - Phase与Agent映射
- `CODE_FIRST_POLICY.md` - 代码优先策略

## 🔄 文档使用流程

```
用户 → 读CLAUDE.md（了解概念）
     ↓
Claude Code → 读.claude/下所有文档（执行细节）
     ↓
执行任务 → 遵循详细规则
```

## 💡 关键认识

**CLAUDE.md ≠ Claude Enhancer完整系统**

- CLAUDE.md是"菜单"
- .claude/下的文档是"食谱"
- 真正的执行依赖.claude/下的详细规则

## 推荐做法

1. **保持CLAUDE.md简洁** - 用户友好
2. **详细规则放.claude/** - Claude Code执行
3. **两者保持同步** - 概念一致

这样用户不会被复杂细节困扰，而Claude Code有详细指导。