# Perfect21 核心定义

## 🔒 项目核心记忆（永久保留）
- core/claude-code-unified-agents 是这个原始的从 GitHub 上来的程序，我不想改变这个内核
- 我希望的 Perfect21 是在这个基础上添加的新 feature 然后 core 具备扫描 Perfect21 新 feature 的能力
- https://github.com/stretchcloud/claude-code-unified-agents 这个是claude-code-unified-agents项目的官方地址
- 你要记住就是 claude code 不能用 subagent 调用 subagent 只能 claude code 调用

## 🎯 Perfect21本质定义
**Perfect21 = Claude Code + 智能工作流增强层**

- **Claude Code**: 执行层，负责所有SubAgent调用
- **Perfect21**: 策略层，提供工作流模板和执行指导
- **关系**: Perfect21不是独立系统，而是Claude Code的增强体验

## 📋 核心执行原则
1. **工作流优先**: 复杂任务（3步+）必须使用工作流模板
2. **同步点机制**: 关键节点必须停止验证，不可跳过
3. **质量门标准**: 必须达到定义的质量指标才能继续
4. **分层执行**: 阶段内并行，阶段间顺序
5. **Claude Code中心**: 所有SubAgent调用都由Claude Code执行
6. **无嵌套调用**: Perfect21只提供策略，绝不会让subagent调用subagent

## 🔑 触发条件
当用户提到以下关键词时，使用Perfect21工作流：
- "用Perfect21..."
- "实现XXX功能"（复杂任务）
- "开发XXX系统"
- "全面测试"
- "部署到生产"

## 📁 项目结构
```
Perfect21/
├── CLAUDE.md                           # 本文件（核心定义，永不修改）
├── CLAUDE_WORKFLOW.md                  # 工作流详细指南（可更新）
├── WORKFLOW_PATH.md                    # 工作流执行路径说明
├── core/claude-code-unified-agents/    # 56个官方agents（只读）
├── features/                           # Perfect21增强功能
│   ├── dynamic_workflow_generator.py   # 动态工作流生成器
│   ├── workflow_orchestrator/          # 工作流编排器
│   ├── sync_point_manager/            # 同步点管理（验证阶段结果一致性）
│   ├── decision_recorder/             # 决策记录（ADR架构决策记录）
│   ├── learning_feedback/             # 学习反馈（持续优化）
│   ├── quality_gates/                 # 质量门控制（质量标准检查）
│   └── git_workflow/                  # Git工作流（13个hooks集成）
└── .claude/                           # Claude配置目录
```

---
> 📝 详细工作流模板和执行示例见：**CLAUDE_WORKFLOW.md**
>
> **版本**: v3.1 | **最后更新**: 2025-01-17
> **原则**: 本文件包含核心定义，永不删除，只做必要补充