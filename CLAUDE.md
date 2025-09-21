# Claude Enhancer - 项目配置

## 🎯 核心系统

### 8-Phase工作流（Phase 0-7）
**完整的8个阶段，从分支创建到部署上线**

- **Phase 0**: Git分支创建 ← 起点（branch_helper.sh提醒）
- **Phase 1**: 需求分析
- **Phase 2**: 设计规划
- **Phase 3**: 实现开发（Agent并行，4-6-8策略）
- **Phase 4**: 本地测试
- **Phase 5**: 代码提交（Git Hooks质量检查）
- **Phase 6**: 代码审查（PR Review）
- **Phase 7**: 合并部署 ← 终点

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
- 8个Phase的标准流程（Phase 0-7）
- 从分支创建到部署的完整性

### 2. Claude Hooks层（实时辅助）
- `branch_helper.sh` - Phase 0时提醒创建分支
- `smart_agent_selector.sh` - Phase 3时智能选择4-6-8个Agent
- 提供建议但不强制

### 3. Git Hooks层（质量把关）
- `pre-commit` - Phase 5时检查代码质量
- `commit-msg` - Phase 5时规范提交信息
- `pre-push` - Phase 6前验证测试通过

## 💡 Max 20X理念

- **质量优先**：不在乎Token消耗
- **智能适配**：根据任务动态调整
- **灵活执行**：框架固定，内容灵活

## 📁 核心文件

```
.claude/
├── settings.json                # Claude配置
├── WORKFLOW.md                  # 8-Phase工作流详解
├── AGENT_STRATEGY.md            # 4-6-8策略说明
├── hooks/
│   ├── branch_helper.sh         # Phase 0: 分支提醒
│   ├── smart_agent_selector.sh  # Phase 3: Agent选择
│   ├── simple_pre_commit.sh     # Phase 5: 代码检查
│   ├── simple_commit_msg.sh     # Phase 5: 信息规范
│   └── simple_pre_push.sh       # Phase 6: 推送验证
└── install.sh                   # 一键安装脚本
```

## 🚀 使用方法

1. 复制.claude到项目
2. 运行install.sh安装Git Hooks
3. 正常开发，系统自动工作

## ⚠️ 注意

- 这是辅助系统，不是强制规则
- Git Hooks需要手动安装到.git/hooks/
- Agent建议可以根据实际调整