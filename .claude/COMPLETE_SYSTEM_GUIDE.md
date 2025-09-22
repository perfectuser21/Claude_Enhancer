# 🎯 Claude Enhancer 完整系统指南
> 模式、Hooks、Git Hooks全解析

## 📊 系统三层架构

```
┌────────────────────────────────────────────────────────┐
│                     用户请求                            │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│      Layer 1: Claude Hooks (实时拦截与建议)             │
│  • UserPromptSubmit → 用户输入时触发                    │
│  • PreToolUse → 工具调用前触发                         │
│  • PostToolUse → 工具调用后触发                        │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│        Layer 2: Claude Code (执行引擎)                  │
│  • 解析用户意图                                        │
│  • 选择执行策略                                        │
│  • 调用工具和Agent                                     │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│         Layer 3: Git Hooks (代码质量把关)               │
│  • pre-commit → 提交前检查                             │
│  • commit-msg → 提交信息规范                           │
│  • pre-push → 推送前验证                               │
└────────────────────────────────────────────────────────┘
```

## 🚀 四种执行模式

### 1. 🟢 主动模式 (Proactive Mode)

**定义**：Claude Code主动采取行动，无需用户明确指示每一步

**触发条件和行为**：
```yaml
场景1 - 检测到错误:
  触发: 发现语法错误、类型错误
  主动行为:
    - 立即修复错误
    - 运行测试验证
    - 报告修复结果

场景2 - Phase自动流转:
  触发: 完成当前Phase任务
  主动行为:
    - 自动进入下一Phase
    - 执行Phase对应的任务
    - 如Phase 5自动运行cleanup

场景3 - 安全隐患:
  触发: 检测到敏感信息、安全漏洞
  主动行为:
    - 立即停止操作
    - 清理敏感数据
    - 提供安全建议

场景4 - 优化机会:
  触发: 发现性能问题、代码冗余
  主动行为:
    - 提出优化方案
    - 实施优化
    - 对比优化前后效果
```

**实际例子**：
```
用户: "实现用户登录功能"

主动模式下Claude Code会:
1. ✅ 自动创建feature分支 (Phase 0)
2. ✅ 自动分析需求 (Phase 1)
3. ✅ 自动设计架构 (Phase 2)
4. ✅ 自动选择6个Agent并行开发 (Phase 3)
5. ✅ 自动运行测试 (Phase 4)
6. ✅ 自动清理和格式化代码 (Phase 5)
7. ✅ 自动创建PR (Phase 6)
```

### 2. 🔵 被动模式 (Passive Mode)

**定义**：严格按照用户指令执行，不做额外动作

**特征**：
```yaml
行为准则:
  - 只做明确要求的事
  - 不添加额外功能
  - 不自动优化或改进
  - 等待下一步指令

适用场景:
  - 用户需要精确控制
  - 学习或调试目的
  - 特定合规要求
```

**实际例子**：
```
用户: "创建一个login.js文件"

被动模式下Claude Code会:
✅ 创建login.js文件
❌ 不会添加登录逻辑
❌ 不会创建相关测试
❌ 不会优化代码结构
```

### 3. 🟡 建议模式 (Advisory Mode) - 当前默认

**定义**：提供建议和提醒，但由Claude Code决定是否采纳

**工作流程**：
```
Hook检测 → 分析情况 → 提供建议 → Claude决定 → 执行或忽略
```

**实际例子**：
```
场景：用户要求实现API

Hook建议: "📊 检测到API开发任务，建议使用6个Agent"
Claude可以:
  选项1: 接受建议，使用6个Agent
  选项2: 根据情况调整为4个Agent
  选项3: 忽略建议，单独处理
```

### 4. 🔴 强制模式 (Enforcement Mode)

**定义**：必须满足所有规则才能继续，无法绕过

**强制规则**：
```yaml
规则1 - 最少Agent数量:
  条件: 编程任务
  要求: 最少3个Agent
  违规处理: 阻止执行，必须重新设计

规则2 - 并行执行:
  条件: 多Agent任务
  要求: 同一消息中调用
  违规处理: 拒绝串行调用

规则3 - 安全检查:
  条件: 包含敏感操作
  要求: 通过安全扫描
  违规处理: 禁止继续
```

**实际例子**：
```
用户: "实现支付功能"

强制模式检查:
❌ 检测到只用了2个Agent → 阻止
提示: "支付功能属于高风险任务，必须使用至少6个Agent，包括security-auditor"

✅ 重新设计使用6个Agent → 通过
继续执行...
```

## 🔗 Claude Hooks 完整列表

### 已实现的Hooks

| Hook脚本 | 触发时机 | 功能 | 状态 |
|---------|---------|------|------|
| `branch_helper.sh` | UserPromptSubmit | 检查分支，提醒Phase | ✅ 激活 |
| `smart_agent_selector.sh` | PreToolUse (Task) | 4-6-8 Agent策略建议 | ✅ 激活 |
| `phase_checker.sh` | 手动调用 | 检查当前Phase状态 | ⚪ 可用 |
| `phase_flow_monitor.sh` | 手动调用 | 监控工作流进度 | ⚪ 可用 |
| `dynamic_task_analyzer.sh` | 手动调用 | 分析任务复杂度 | ⚪ 可用 |
| `enforcer.sh` | PreToolUse (*) | 强制多Agent执行 | 🔴 未启用 |

### Hook配置示例

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "bash .claude/hooks/branch_helper.sh",
        "timeout": 1000
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",  // 只在Task工具时触发
        "type": "command",
        "command": "bash .claude/hooks/smart_agent_selector.sh",
        "timeout": 5000
      }
    ],
    "PostToolUse": []  // 当前未配置
  }
}
```

## 🔧 Git Hooks 完整列表

### 已安装的Git Hooks

| Hook名称 | 触发时机 | 功能 | 来源 |
|---------|---------|------|------|
| **pre-commit** | `git commit`前 | 代码质量检查 | Claude Enhancer |
| **commit-msg** | 提交信息写入前 | 规范提交信息格式 | Claude Enhancer |
| **pre-push** | `git push`前 | 运行测试，检查TODO | Claude Enhancer |
| **post-commit** | 提交完成后 | 记录提交，更新Phase | Perfect21 |
| **post-checkout** | 切换分支后 | 环境检查，依赖更新 | Perfect21 |
| **post-merge** | 合并完成后 | 冲突检查，依赖同步 | Perfect21 |

### Git Hooks执行流程

```
开发流程中的Hook触发点：

1. 切换分支
   └─→ post-checkout → 检查环境

2. 编写代码
   └─→ (无Hook)

3. git add
   └─→ (无Hook)

4. git commit
   ├─→ pre-commit → 质量检查、格式化、清理
   ├─→ commit-msg → 规范提交信息
   └─→ post-commit → 更新状态

5. git push
   ├─→ pre-push → 测试验证
   └─→ 推送到远程

6. git merge
   └─→ post-merge → 合并后处理
```

### 关键Git Hook内容

#### pre-commit (Phase 5触发点)
```bash
#!/bin/bash
# 主要功能：
- 语法检查（eslint, pylint等）
- 代码格式化（prettier, black等）
- 敏感信息扫描
- 清理临时文件
- 移除调试代码
```

#### commit-msg (提交规范)
```bash
#!/bin/bash
# 规范格式：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具
```

#### pre-push (Phase 6前置检查)
```bash
#!/bin/bash
# 主要功能：
- 运行单元测试
- 检查测试覆盖率
- 验证无TODO/FIXME
- 确保无构建错误
```

## 🎮 模式切换方法

### 1. 通过配置文件切换

```json
// .claude/settings.json
{
  "environment": {
    "CLAUDE_ENHANCER_MODE": "proactive",  // 可选: proactive, passive, advisory, enforcement
    "AUTO_CLEANUP": "true",
    "ENFORCE_PARALLEL": "true"
  }
}
```

### 2. 通过命令切换

```bash
# 切换到主动模式
echo '{"mode": "proactive"}' > .claude/current_mode.json

# 切换到强制模式
echo '{"mode": "enforcement"}' > .claude/current_mode.json
```

### 3. 通过对话指定

```
"用主动模式帮我开发..."
"切换到强制模式"
"使用被动模式执行"
```

## 📈 模式选择建议

| 场景 | 推荐模式 | 原因 |
|-----|---------|------|
| 快速原型开发 | 主动模式 | 自动化程度高，快速迭代 |
| 学习和理解 | 被动模式 | 精确控制，便于理解每一步 |
| 日常开发 | 建议模式 | 平衡自动化和控制 |
| 生产环境 | 强制模式 | 确保质量和安全 |
| 团队协作 | 强制模式 | 统一标准和流程 |

## 🔄 Hook执行时序图

```
用户输入
    ↓
[UserPromptSubmit Hook]
    ├→ branch_helper.sh (检查分支)
    ↓
Claude Code 解析
    ↓
准备调用工具
    ↓
[PreToolUse Hook]
    ├→ smart_agent_selector.sh (如果是Task)
    ├→ enforcer.sh (如果启用强制模式)
    ↓
执行工具
    ↓
[PostToolUse Hook]
    ├→ (当前未配置)
    ↓
返回结果
    ↓
用户执行git操作
    ↓
[Git Hooks]
    ├→ pre-commit
    ├→ commit-msg
    ├→ pre-push
    └→ ...
```

## 💡 实用技巧

### 1. 查看当前模式
```bash
cat .claude/current_mode.json
```

### 2. 查看Hook日志
```bash
tail -f /tmp/claude_*.log
```

### 3. 测试Hook
```bash
echo '{"prompt": "test"}' | .claude/hooks/smart_agent_selector.sh
```

### 4. 跳过Git Hook（紧急情况）
```bash
git commit --no-verify
git push --no-verify
```

### 5. 手动触发清理
```bash
.claude/scripts/cleanup.sh 5  # Phase 5清理
.claude/scripts/cleanup.sh 7  # Phase 7清理
```

## 🎯 总结

**三个层次的Hook系统**：
1. **Claude Hooks** - 实时拦截和建议（开发时）
2. **Claude Code** - 执行决策（运行时）
3. **Git Hooks** - 质量把关（提交时）

**四种执行模式**：
1. **主动** - 全自动化
2. **被动** - 完全手动
3. **建议** - 半自动（当前默认）
4. **强制** - 规则驱动

**使用建议**：
- 开发初期用主动模式快速搭建
- 关键功能用强制模式确保质量
- 学习时用被动模式理解细节
- 日常开发用建议模式保持灵活

---

*记住：模式和Hooks是工具，目的是提高开发效率和代码质量！*