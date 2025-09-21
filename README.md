# Claude Enhancer

## 🎯 这是什么？

一个智能的开发工作流系统，为Claude Code Max 20X用户优化，提供：
- **8-Phase工作流** - 从分支创建到部署的完整流程
- **4-6-8 Agent策略** - 从56个可用Agent中智能选择
- **自动质量保证** - 代码检查、测试提醒、提交规范

## 🤖 关于56个Agent

Claude Code提供56个专业Agent，涵盖：
- 开发类：backend-architect, frontend-specialist, fullstack-engineer等
- 语言专家：python-pro, golang-pro, rust-pro, java-enterprise等
- 框架专家：react-pro, vue-specialist, angular-expert, nextjs-pro等
- 专业领域：database-specialist, security-auditor, performance-engineer等
- 支持角色：test-engineer, devops-engineer, documentation-writer等

**我们的策略**：不是用所有56个，而是根据任务智能选择4-6-8个最合适的。

## 🚀 快速开始

### 1. 复制到你的项目
```bash
cp -r .claude /your-project/
cd /your-project
```

### 2. 安装（可选）
```bash
./.claude/install.sh
```

## 📋 工作原理

### 8-Phase工作流
0. **Git分支** - 版本控制
1. **需求分析** - 理解任务
2. **设计规划** - 技术方案
3. **实现开发** - Agent并行执行
4. **本地测试** - 质量验证
5. **代码提交** - Git Hooks检查
6. **代码审查** - PR Review
7. **合并部署** - 上线发布

### 4-6-8 Agent策略
| 复杂度 | Agent数量 | 从56个中选择 | 执行时间 |
|--------|-----------|--------------|----------|
| 简单 | 4个 | 基础组合 | 5-10分钟 |
| 标准 | 6个 | 平衡组合 | 15-20分钟 |
| 复杂 | 8个 | 全面组合 | 25-30分钟 |

## 📁 核心文件

```
.claude/
├── settings.json         # Claude配置
├── WORKFLOW.md          # 8-Phase详细说明
├── AGENT_STRATEGY.md    # 4-6-8策略说明
├── hooks/
│   ├── smart_agent_selector.sh  # 智能选择器
│   ├── simple_pre_commit.sh     # Git检查
│   └── ...
└── install.sh           # 一键安装
```

## 💡 Max 20X理念

- **质量优先** - 不在乎Token消耗
- **智能选择** - 56个Agent中选最合适的
- **灵活执行** - 框架固定，内容灵活

## 🛠️ 适用项目

任何需要高质量代码的项目：
- Web应用、API服务
- 命令行工具、库/框架
- 微服务、全栈应用
- AI/ML项目、数据工程

## 📝 License

MIT