# Claude Enhancer - 智能开发工作流系统

## 🏗️ v2.0架构文档（重要！）
**Claude Code执行任务时应读取这些架构文档：**
- `ARCHITECTURE/INDEX.md` - 📚 架构文档索引入口
- `ARCHITECTURE/v2.0-FOUNDATION.md` - 🎯 四层架构定义
- `ARCHITECTURE/LAYER-DEFINITION.md` - 📊 层级详细说明
- `ARCHITECTURE/GROWTH-STRATEGY.md` - 🚀 Feature成长策略
- `ARCHITECTURE_LOADER.md` - 🔄 文档加载指南

## 🎯 核心理念
- **四层架构** - Core/Framework/Services/Features智能分层
- **框架固定，内容灵活** - 8个Phase的工作流程
- **4-6-8 Agent策略** - 根据任务复杂度智能选择
- **三层质量保证** - Workflow + Claude Hooks + Git Hooks

## 📁 文件结构
```
.claude/
├── ARCHITECTURE/             # 🔒 架构文档（永久保护）
│   ├── INDEX.md             # 文档索引
│   ├── v2.0-FOUNDATION.md   # 核心架构
│   ├── LAYER-DEFINITION.md  # 层级定义
│   ├── GROWTH-STRATEGY.md   # 成长策略
│   └── decisions/           # 架构决策记录
├── README.md                 # 本文档
├── settings.json            # Claude Code配置
├── ARCHITECTURE_LOADER.md   # 架构加载器
├── WORKFLOW.md              # 8 Phase工作流说明
├── AGENT_STRATEGY.md        # 4-6-8 Agent策略
├── hooks/
│   ├── smart_agent_selector.sh  # 智能Agent选择(核心)
│   ├── test_reminder.sh         # 测试提醒
│   ├── commit_helper.sh         # 提交辅助
│   ├── simple_pre_commit.sh     # Git: 提交前检查
│   ├── simple_commit_msg.sh     # Git: 提交信息规范
│   └── simple_pre_push.sh       # Git: 推送前验证
└── install.sh                   # 一键安装脚本
```

## 🚀 快速开始

### 1. 复制到你的项目
```bash
cp -r .claude /your/project/
cd /your/project
```

### 2. 安装（可选）
```bash
./.claude/install.sh
```

### 3. 使用
系统会自动：
- 分析你的任务复杂度
- 选择合适的Agent数量（4/6/8个）
- 在适当的Phase执行检查

## 📊 工作流程（8 Phases）

1. **Phase 0**: Git分支创建
2. **Phase 1**: 需求分析
3. **Phase 2**: 设计规划
4. **Phase 3**: 实现开发（Agent并行执行）
5. **Phase 4**: 本地测试
6. **Phase 5**: 代码提交（Git Hooks检查）
7. **Phase 6**: 代码审查
8. **Phase 7**: 合并部署

## 🤖 Agent策略（4-6-8）

| 复杂度 | Agent数 | 适用场景 | 执行时间 |
|--------|---------|----------|----------|
| 简单 | 4个 | Bug修复、小改动 | 5-10分钟 |
| 标准 | 6个 | 新功能、API开发 | 15-20分钟 |
| 复杂 | 8个 | 系统设计、架构 | 25-30分钟 |

## 💡 Max 20X理念

- **质量优先**：最少4个Agent保证基础质量
- **智能适配**：根据任务自动调整
- **不限Token**：追求最佳结果

## 🛠️ 自定义配置

编辑 `.claude/settings.json` 可调整：
- 最小/最大Agent数量
- Hook触发条件
- 超时设置

## ⚠️ 注意事项

1. 这是辅助系统，不是强制规则
2. 可以根据实际需要调整Agent数量
3. Git Hooks需要手动安装到.git/hooks/

## 📝 版本

- 版本：2.0
- 更新：2024-09
- 作者：Claude Enhancer Team