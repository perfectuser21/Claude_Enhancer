# Claude Enhancer - 项目配置

## 🎯 核心系统

### 8-Phase工作流（从Branch开始）
0. **Git分支创建** ← Hook提醒从这里开始
1. 需求分析
2. 设计规划
3. 实现开发（Agent并行）
4. 本地测试
5. 代码提交（Git Hooks检查）
6. 代码审查
7. 合并部署

### 4-6-8 Agent策略
- **简单任务**：4个Agent（5-10分钟）
- **标准任务**：6个Agent（15-20分钟）
- **复杂任务**：8个Agent（25-30分钟）

## 🤖 关于56个专业Agent

这56个Agent定义来自于我们从GitHub下载的.claude/agents配置文件，不是Claude Code自带的。

我们的策略：
- 从56个可用Agent中智能选择
- 根据任务复杂度选4-6-8个
- 动态组合，不固定搭配

## 🔧 三层质量保证

### 1. Workflow层（框架）
- 8个Phase的标准流程
- 确保开发完整性

### 2. Claude Hooks层（实时）
- `smart_agent_selector.sh` - 智能选择Agent
- 在Phase 3执行时触发
- 提供建议但不强制

### 3. Git Hooks层（把关）
- `pre-commit` - 代码质量检查
- `commit-msg` - 提交信息规范
- `pre-push` - 推送前验证

## 💡 Max 20X理念

- **质量优先**：不在乎Token消耗
- **智能适配**：根据任务动态调整
- **灵活执行**：框架固定，内容灵活

## 📁 核心文件

```
.claude/
├── settings.json         # Claude配置
├── WORKFLOW.md          # 8-Phase工作流
├── AGENT_STRATEGY.md    # 4-6-8策略
├── hooks/
│   ├── smart_agent_selector.sh  # 核心：智能选择
│   ├── simple_pre_commit.sh     # Git: 提交检查
│   ├── simple_commit_msg.sh     # Git: 信息规范
│   └── simple_pre_push.sh       # Git: 推送验证
└── install.sh           # 一键安装
```

## 🚀 使用方法

1. 复制.claude到项目
2. 运行install.sh安装Git Hooks
3. 正常开发，系统自动工作

## ⚠️ 注意

- 这是辅助系统，不是强制规则
- Git Hooks需要手动安装到.git/hooks/
- Agent建议可以根据实际调整