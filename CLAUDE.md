# Claude Enhancer - 项目配置

## 📚 智能文档加载策略
**重要**: Claude Enhancer使用智能加载避免上下文污染

### 文档加载规则
1. **默认只加载本文件** - 防止Token超量导致Claude被kill
2. **按需加载架构文档** - 根据任务自动判断
3. **智能触发机制**:
   - 提到"新功能" → 加载 `GROWTH-STRATEGY.md`
   - 提到"架构/重构" → 加载 `v2.0-FOUNDATION.md`
   - 提到"命名" → 加载 `NAMING-CONVENTIONS.md`
   - 提到"为什么" → 加载 `decisions/*.md`

**核心目的**: 防止上下文超量，不是为了节省Token（Max 20X用户不在乎Token）

### 架构文档位置（按需查阅）
- `.claude/ARCHITECTURE/SMART_LOADING_STRATEGY.md` - 智能加载策略
- `.claude/ARCHITECTURE/INDEX.md` - 架构文档索引
- `.claude/ARCHITECTURE/v2.0-FOUNDATION.md` - 核心架构定义
- `.claude/ARCHITECTURE/LAYER-DEFINITION.md` - 层级详细说明

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

## 🤖 关于专业Agent系统

**标准Agent**: 56个专业Agent，涵盖全栈开发各领域
**特殊Agent**: 5个系统Agent（orchestrator, claude_enhancer等）
**总计**: 61个Agent文件

重要说明：
- **只有Claude Code可以调用Agent**（SubAgent不能调用SubAgent）
- 根据任务复杂度选4-6-8个Agent并行执行
- 动态组合，智能选择，不固定搭配

## 🔧 三层质量保证

### 1. Workflow层（框架）
- 8个Phase的标准流程（Phase 0-7）
- 从分支创建到部署的完整性

### 2. Claude Hooks层（实时辅助）✅ 已完善
核心Hook（建议性，非阻塞）：
- `branch_helper.sh` - Phase 0时提醒创建分支
- `smart_agent_selector.sh` - Phase 3时智能选择4-6-8个Agent
- `quality_gate.sh` - 质量检查建议
- `performance_monitor.sh` - 性能监控（新增）
- `error_handler.sh` - 错误处理助手（新增）

特点：
- 所有Hook都是**非阻塞**（blocking: false）
- 超时保护（500-3000ms）
- 只提供建议，不强制执行

### 3. Git Hooks层（质量把关）
- `pre-commit` - Phase 5时检查代码质量
- `commit-msg` - Phase 5时规范提交信息
- `pre-push` - Phase 6前验证测试通过

## 💡 Max 20X理念

- **质量优先**：不在乎Token消耗，要最好的结果
- **防止被kill**：智能文档加载防止上下文超量
- **智能适配**：根据任务动态调整Agent数量
- **灵活执行**：框架固定，内容灵活
- **安全第一**：无死循环，无嵌套调用

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