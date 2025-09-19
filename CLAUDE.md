# Perfect21 项目核心文档

> 🎯 **项目身份**: Perfect21 - Claude Code的智能工作流增强层
> 🔑 **核心原则**: 质量优先 + 智能编排 + 持续学习

## 🔒 项目核心记忆（永久保留）
- core/claude-code-unified-agents 是这个原始的从 GitHub 上来的程序，我不想改变这个内核
- 我希望的 Perfect21 是在这个基础上添加的新 feature 然后 core 具备扫描 Perfect21 新 feature 的能力
- https://github.com/stretchcloud/claude-code-unified-agents 这个是claude-code-unified-agents项目的官方地址
- 你要记住就是 claude code 不能用 subagent 调用 subagent 只能 claude code 调用

## 🔔 自动监督机制 【Hook会强制执行！】

**Perfect21通过3层监督确保Claude Code遵守规则：**

### 1️⃣ **Claude Code Hooks** - 工具执行前后自动检查
   📍 位置：`.claude/hooks/`
   - `pre-edit.sh` - 编辑前验证Agent选择（阻止少于3个Agent）
   - `post-task.sh` - 任务后检查健康分数（低于80分警告）
   - `on-error.sh` - 错误时提供修复建议（分析错误类型）

### 2️⃣ **Git Hooks** - Git操作时强制验证
   📍 位置：`hooks/`
   - `pre-commit` - 代码质量检查（运行所有测试）
   - `pre-push` - 测试和安全扫描（验证通过才能推送）
   - `commit-msg` - 提交消息格式（必须符合规范）

### 3️⃣ **Rule Guardian** - 实时监督和指导
   📍 位置：`features/guardian/rule_guardian.py`
   - 在5个关键检查点主动验证
   - 违规立即警告并阻止继续
   - 提供自动修复建议

⚠️ **重要**：Hooks会阻止违规操作！必须满足要求才能继续。

## 🎯 Perfect21定位声明
**Perfect21 = 个人编程助理**

- **身份定位**: 个人专属编程助理，专注提升个人开发效率
- **使用场景**: 单用户本地使用，不考虑多用户和商业化
- **优化方向**: 本地性能、个人工作流、使用体验
- **核心价值**: 让一个人拥有整个开发团队的能力

## 🎯 Perfect21本质定义
**Perfect21 = Claude Code的行为规范框架**

- **核心定位**: 定义Claude Code应该如何工作的规则和标准
- **不是什么**: 不是独立执行系统，不是工作流引擎，不能分析，不能执行
- **是什么**: 是规范、是指南、是最佳实践、是规则定义
- **执行流程**: 用户需求 → Claude Code分析 → Claude Code查看Perfect21规则 → Claude Code按规则执行

**重要认知**：
- Perfect21只提供规则定义，不具备任何执行能力
- 所有分析、决策、执行都由Claude Code完成
- Perfect21生成的"指令"是给Claude Code看的模板和指导

## 📜 Perfect21规则体系

### 核心规则文件
- **rules/perfect21_rules.yaml** - 完整的规则定义
- **rules/rule_engine.py** - 规则匹配引擎
- **FEATURE_GUIDES.md** - Feature专项指导

## ⚡ 执行规则

### 🔔 自动检查点 【必须通过所有检查！】
**Claude Code在以下时刻必须检查规则：**

| 检查点 | 触发时机 | 检查内容 | 失败后果 |
|--------|---------|----------|----------|
| 📥 **任务分析** | 接到任务时 | 识别任务类型，确定Agent需求 | 选择错误Agent组合 |
| 👥 **Agent选择** | 选择Agent时 | 验证≥3个并行执行 | Hook阻止执行 |
| ⚡ **执行前** | 开始执行前 | 确认质量要求和反馈机制 | 缺少质量保障 |
| 🧪 **测试后** | 测试完成后 | 失败必须触发反馈循环 | 直接提交错误代码 |
| 📦 **提交前** | Git提交前 | 检查格式、测试、质量门 | Git Hook阻止提交 |

### 📋 执行前自检清单
在执行任何编程任务前，Claude Code必须确认：
- [ ] 识别了任务类型？（认证/API/数据库等）
- [ ] 选择了≥3个Agent？（Hook会检查）
- [ ] 使用并行执行模式？（单个function_calls）
- [ ] 配置了反馈循环？（测试失败自动修复）
- [ ] 设置了质量门？（覆盖率>80%）

### 规则1：批量并行执行【最重要！】
**记住：批量调用 = 真正的并行执行**

```xml
<!-- ✅ 正确：一个消息中同时调用3-5个agents -->
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">设计用户认证API</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">security-auditor</parameter>
    <parameter name="prompt">审查认证安全性</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">test-engineer</parameter>
    <parameter name="prompt">编写认证测试</parameter>
  </invoke>
</function_calls>
```

### 规则2：智能Agent选择 【Hook强制执行】
- **🔴 永远不要只用1-2个agents，至少选择3-5个！**
- **🟡 优先使用成功模式组合**
- **🟢 相关agents必须一起调用**

⚠️ **Hook执行流程**：
```
你选择Agent → pre-edit.sh检查 →
  ├─ ✅ ≥3个Agent → 继续执行
  └─ ❌ <3个Agent → 阻止并要求修正
```

### 规则3：任务识别与Agent选择 【强制组合】
**Perfect21会根据任务类型自动匹配最佳Agent组合**

| 任务类型 | 必须Agent组合 | 最少数量 |
|----------|--------------|----------|
| 🔐 认证系统 | backend-architect, security-auditor, test-engineer, api-designer, database-specialist | 5个 |
| 🌐 API开发 | api-designer, backend-architect, test-engineer, technical-writer | 4个 |
| 💾 数据库 | database-specialist, backend-architect, performance-engineer | 3个 |
| 🎨 前端开发 | frontend-specialist, ux-designer, test-engineer | 3个 |
| ⚡ 性能优化 | performance-engineer, backend-architect, database-specialist | 3个 |

📌 **完整定义**：`rules/perfect21_rules.yaml`

### 规则4：Git Hook自动触发
**在特定时机自动执行检查**
- pre-commit: 代码审查
- pre-push: 测试和安全扫描
- post-merge: 部署准备

### 规则5：质量门标准
**必须满足的质量要求**
- 代码覆盖率 > 80%
- API响应时间 P95 < 200ms
- 无安全漏洞

## 🏗️ 架构设计（4层结构）

```
Perfect21/
├── main/           # 入口层 - 统一的执行入口
├── features/       # 功能层 - 可插拔的业务功能
├── core/           # 核心层 - 不可变的基础能力
└── modules/        # 工具层 - 共享的基础设施
```

**依赖原则**：上层 → 下层 ✅ | 下层 → 上层 ❌

## 📁 项目结构

```
Perfect21/
├── CLAUDE.md                           # 本文件（核心定义，保持稳定）
├── ARCHITECTURE.md                     # 架构详细说明
├── FEATURE_GUIDES.md                   # 各Feature专项指导
├── core/claude-code-unified-agents/    # 56个官方agents（只读）
├── features/                           # Perfect21增强功能
│   ├── workflow/                       # 工作流引擎
│   ├── agents/                         # Agent管理
│   ├── quality/                        # 质量保证
│   ├── git/                           # Git集成
│   ├── learning/                       # 学习反馈
│   ├── auth/                          # 认证系统
│   └── monitoring/                     # 监控告警
└── main/                               # 入口程序
    ├── cli.py                         # 命令行接口
    ├── api.py                         # API服务
    └── perfect21.py                   # 主程序
```

## 🚀 快速命令

```bash
# 并行执行任务（强制使用5个agents）
python3 main/cli.py parallel "任务描述" --agents 5

# 安装所有Git hooks
python3 main/cli.py hooks install complete

# 查看系统状态
python3 main/cli.py status
```

## 📋 核心原则

1. **工作流优先**: 复杂任务（3步+）必须使用工作流模板
2. **同步点机制**: 关键节点必须停止验证，不可跳过
3. **质量门标准**: 必须达到定义的质量指标才能继续
4. **分层执行**: 阶段内并行，阶段间顺序
5. **Claude Code中心**: 所有SubAgent调用都由Claude Code执行
6. **无嵌套调用**: Perfect21只提供策略，绝不会让subagent调用subagent

## 💭 个人助理优化思考

### 本地性能优化
- **Agent结果缓存**: 相同任务本地缓存，秒级响应
- **模板预编译**: 常用工作流模板预编译，减少解析时间
- **Git缓存利用**: 充分利用.git目录缓存，加速Git操作
- **资源池管理**: 连接池复用，减少资源创建开销

### 个人工作流增强
- **习惯学习**: 记录个人编程习惯，自动推荐最佳Agent组合
- **知识库积累**: 基于历史项目建立个人知识库
- **风格适配**: 学习个人代码风格，生成符合习惯的代码
- **常用模式**: 保存个人常用的开发模式和解决方案

### 使用体验改进
- **命令简化**: 支持别名和快捷方式，减少输入
- **实时反馈**: 流式显示执行进度，知道系统在做什么
- **智能提示**: 错误时提供清晰的修复建议和解决方案
- **历史记录**: 保存执行历史，支持快速重放

### 效率提升重点
1. **真实API集成**: 替换模拟执行为真实Claude API调用（当前最重要）
2. **流式响应**: 不等待全部完成，实时显示结果
3. **智能缓存**: 避免重复执行相同任务
4. **增量执行**: 只处理变更部分，节省时间
5. **并行优化**: 智能判断并行度，最大化执行效率

### 个人数据管理
- **本地存储**: 所有数据本地保存，完全隐私
- **项目隔离**: 不同项目的学习数据独立管理
- **快速备份**: 支持配置和知识库的快速备份恢复
- **轻量运行**: 优化内存占用，适合个人设备

---

> 📝 **使用提示**:
> - 详细架构说明见 **ARCHITECTURE.md**
> - Feature专项指导见 **FEATURE_GUIDES.md**
> - 本文件是核心定义，应保持稳定，避免频繁修改
>
> **版本**: v5.1 | **最后更新**: 2025-09-19
> **核心理念**: Perfect21是行为规范框架，不是执行系统
> **原则**: 规则清晰、指导明确、专注规范