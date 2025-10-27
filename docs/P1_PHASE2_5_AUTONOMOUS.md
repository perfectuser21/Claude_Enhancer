# Phase 1: Discovery - Phase 2-5 Autonomous Enforcement System

## 问题分析

### 当前问题

根据用户反馈，尽管已启用bypass permissions且约定Phase 2-6应完全自动化，但AI仍然频繁在Phase 2-5执行过程中询问用户决策：

**具体表现**：
- ❌ "用A库还是B库？"
- ❌ "发现了bug，要修复吗？"
- ❌ "Phase X完成了，继续吗？"
- ❌ "这样实现可以吗？"

**影响**：
- 中断用户工作流
- 降低自动化程度
- 违背了"Phase 2-6完全自动化"的约定

### 根本原因

1. **CLAUDE.md缺少明确规则**：Phase 2-5定义中没有显式说明"AI完全自主，不问用户"
2. **误导性术语**：Phase 4的"人工验证"被AI误解为"用户手动确认"，实际应为"AI手动检查"
3. **无Phase 2-5专用Hook**：`requirement_clarification.sh`仅适用于Phase 1，Phase 2-5无对应机制
4. **无决策框架**：AI遇到技术问题时，没有明确的决策指引，倾向于"问用户最安全"

## 技术发现

### 现有机制分析

**已有Hook**：
- `requirement_clarification.sh` (UserPromptSubmit)
  - 作用：Phase 1需求澄清指引
  - 优点：明确列出"不要问技术细节"
  - 限制：仅Phase 1适用

- `workflow_enforcer.sh` (PrePrompt)
  - 作用：强制7-Phase工作流执行
  - 限制：未区分Phase，未提供自主决策指引

**问题**：
- 无Phase 2-5特定的自主执行指引
- AI不知道在Phase 2-5中应该如何决策

### Hook vs Skill vs Agent

根据Claude Code文档和用户要求，需要结合三种机制：

| 机制 | 作用 | 强度 | 适用场景 |
|------|------|------|---------|
| **Git Hooks** | 阻止违规commit | 强（硬阻止） | Pre-commit检查（workflow_guardian.sh） |
| **Claude Hooks** | 注入AI行为指引 | 中（软引导） | 每次prompt前提醒AI规则 |
| **Skills** | 详细决策框架 | 弱（参考文档） | AI主动激活，获取详细指引 |

**综合策略**：
- Git Hooks：已有workflow_guardian.sh，确保Phase 1文档存在 ✅
- **Claude Hooks（缺失）**：需要创建phase2_5_autonomous.sh，PrePrompt注入
- **Skills（缺失）**：需要创建phase2-5-autonomous skill，提供决策框架

## 解决方案设计

### 方案：Hook + Skill组合

#### Component 1: Claude Hook (.claude/hooks/phase2_5_autonomous.sh)

**功能**：
1. 检测当前Phase（读取.phase/current）
2. 如果是Phase 2-5且需求已澄清，注入自主指引
3. 明确列出禁止询问的问题类型
4. 提供简洁的决策框架

**触发时机**：PrePrompt（AI每次生成响应前）

**注入内容要点**：
```
🤖 AUTONOMOUS MODE - Phase X 自主执行

【禁止询问】：
❌ 技术选择（库、框架、模式）
❌ 实现细节（代码结构、优化）
❌ 质量问题（bug修复、性能优化）
❌ 进度确认（Phase完成确认）

【自主决策】：
✅ 技术选择 → 参考项目现有技术栈
✅ Bug修复 → 立即修复
✅ 性能优化 → benchmark后优化
✅ 测试策略 → 自己设计，确保≥70%覆盖
```

#### Component 2: Skill (.claude/skills/phase2-5-autonomous/SKILL.md)

**功能**：
1. 详细的决策框架（如何选择库、如何设计测试）
2. Phase特定指引（Phase 2/3/4/5各自的决策标准）
3. 示例场景（正确vs错误的行为）
4. Red flags（何时需要停下来）

**激活方式**：AI主动判断（当遇到技术决策时）

**内容结构**：
```yaml
---
name: phase2-5-autonomous
description: Phase 2-5 autonomous execution guidance
trigger: phase2|phase3|phase4|phase5|implementation|testing
---

## Decision Framework
### 1. Business Requirements → Check Documentation
### 2. Technical Implementation → Apply Standards
### 3. Code Quality → Enforce Thresholds
### 4. Performance → Benchmark & Optimize

## Phase-Specific Guidelines
### Phase 2: Implementation
### Phase 3: Testing
### Phase 4: Review
### Phase 5: Release
```

#### Component 3: CLAUDE.md Updates

**修改内容**：
1. Phase 2-5定义中增加"执行模式：🤖 完全自主"
2. 明确列出"AI自主决策范围"
3. 明确列出"禁止询问用户"的问题类型
4. Phase 4澄清"人工验证"含义（AI manual review，非user confirmation）

### 工作原理

```
用户发送消息
    ↓
PrePrompt Hook触发
    ↓
workflow_enforcer.sh → 检测Phase
    ↓
phase2_5_autonomous.sh → 如果Phase 2-5，注入自主指引
    ↓
AI看到明确规则："Phase X，完全自主，禁止问技术问题"
    ↓
AI遇到技术决策
    ↓
参考Hook注入的简洁规则 + 主动激活Skill获取详细框架
    ↓
AI自己决策，不问用户
    ↓
生成响应："实现了XX，选择了YY（因为ZZ原因）"
```

## 技术栈

- **Bash**: Hook脚本实现
- **YAML**: Skill frontmatter定义
- **Markdown**: Skill内容、文档更新
- **Git**: Hook注册、文件追踪

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| AI误判，不该自主时自主 | 中 | Hook检测AUTO_MODE_ACTIVE标志 |
| AI决策质量下降 | 低 | 提供详细决策框架和质量标准 |
| 与现有Hook冲突 | 低 | 在PrePrompt链中合理排序 |
| 用户不想自主时被强制 | 低 | 删除.workflow/AUTO_MODE_ACTIVE即退出 |

## Impact Assessment

- **Risk**: Low（基于成熟的requirement_clarification.sh模式）
- **Complexity**: Medium（2个新文件 + CLAUDE.md更新）
- **Scope**: 3个文件（1 hook, 1 skill, 1 doc）
- **Impact Radius**: **15** (Low)

**Agent建议**: 0个（简单hook+skill创建，solo work）

---

## 实现计划

### Phase 2: Implementation

**文件清单**：
1. `.claude/hooks/phase2_5_autonomous.sh` (新建)
   - 检测Phase
   - 注入自主指引
   - 约150行

2. `.claude/skills/phase2-5-autonomous/SKILL.md` (新建)
   - Skill frontmatter
   - Decision frameworks
   - Phase-specific guidelines
   - Examples
   - 约300行

3. `.claude/settings.json` (修改)
   - 注册phase2_5_autonomous.sh到PrePrompt hooks

4. `CLAUDE.md` (修改)
   - Phase 2-5定义增加"执行模式"和"AI自主决策范围"
   - 明确"禁止询问用户"清单
   - 澄清"人工验证"含义

### Phase 3: Testing

**验证方法**：
1. 单元测试：Hook在Phase 2-5正确激活，在Phase 1/6/7不激活
2. 集成测试：Hook注入内容正确显示
3. 行为测试：AI在Phase 2-5不问技术问题

**测试场景**：
```bash
# Scenario 1: Phase 2 - Implementation
echo "Phase2" > .phase/current
touch .workflow/AUTO_MODE_ACTIVE
# 预期：AI自己选择库，不问用户

# Scenario 2: Phase 3 - Testing
echo "Phase3" > .phase/current
# 预期：AI发现bug立即修复，不问用户

# Scenario 3: Phase 1 - Discovery
echo "Phase1" > .phase/current
# 预期：Hook不激活（Phase 1应该讨论）
```

### Phase 4: Review

**审查要点**：
1. Hook逻辑正确性（Phase检测、条件判断）
2. Skill内容完整性（覆盖所有Phase 2-5场景）
3. CLAUDE.md更新准确性（不破坏现有结构）
4. 与requirement_clarification.sh一致性（相同模式）

### Phase 5: Release

**部署步骤**：
1. 注册hook到settings.json
2. 更新CLAUDE.md
3. 测试验证
4. 文档说明（本文档）

### Phase 6: Acceptance

**验收标准**：
- [ ] Hook在Phase 2-5正确激活
- [ ] Hook注入的内容清晰可读
- [ ] Skill内容全面覆盖决策场景
- [ ] CLAUDE.md更新不破坏现有内容
- [ ] AI在Phase 2-5不再问技术问题（用户确认）

### Phase 7: Closure

**最终检查**：
- [ ] 代码质量（Shellcheck, 语法检查）
- [ ] 文档完整（本文档 + Skill内容）
- [ ] 版本一致性（settings.json version）
- [ ] 无遗留TODO

---

## 与现有系统的集成

### 与7-Phase工作流的关系

```
Phase 1 (Discovery)
  ↓ requirement_clarification.sh - 需求讨论，可以问业务问题
  ↓ 产出：REQUIREMENTS_DIALOGUE.md, CHECKLIST.md, PLAN.md
  ↓
Phase 2 (Implementation)
  ← phase2_5_autonomous.sh激活 - 完全自主，不问技术问题
  ← phase2-5-autonomous skill提供决策框架
  ↓
Phase 3 (Testing)
  ← phase2_5_autonomous.sh激活 - 自己设计测试，自己修bug
  ↓
Phase 4 (Review)
  ← phase2_5_autonomous.sh激活 - 自己审查，自己修复
  ↓
Phase 5 (Release)
  ← phase2_5_autonomous.sh激活 - 自己配置监控，自己写文档
  ↓
Phase 6 (Acceptance)
  ↓ 用户确认（唯一需要用户参与的地方）
  ↓
Phase 7 (Closure)
  ↓ 用户说"merge"后才执行
```

### 与现有Hooks的协同

**PrePrompt Hook链**（settings.json顺序）：
1. `force_branch_check.sh` - 分支检查
2. `ai_behavior_monitor.sh` - 行为监控
3. `workflow_enforcer.sh` - 工作流强制
4. **`phase2_5_autonomous.sh`** ← 新增
5. `smart_agent_selector.sh` - Agent选择
6. `gap_scan.sh` - 差距扫描
7. `impact_assessment_enforcer.sh` - 影响评估

**位置合理性**：
- 在workflow_enforcer之后（先确认Phase，再注入Phase特定规则）
- 在smart_agent_selector之前（自主决策原则影响Agent选择）

---

## 成功标准

**短期（1周）**：
- [ ] Hook和Skill创建完成
- [ ] 集成测试通过
- [ ] CLAUDE.md更新完成

**中期（1个月）**：
- [ ] AI在Phase 2-5不再问技术问题
- [ ] 用户反馈："工作流很流畅"
- [ ] 无误判（不该自主时强制自主）

**长期（3个月）**：
- [ ] 成为标准模式，所有新任务都使用
- [ ] 决策质量良好（AI选择合理，代码质量高）
- [ ] 用户满意度提升

---

## 经验教训（PR #40）

**问题回顾**：
- v8.0.1开发中，AI频繁问"继续吗？"
- 尽管bypass permissions已启用
- 原因：缺少明确的自主执行指引

**本方案解决**：
- Hook：每次提醒AI当前在Phase 2-5，应该自主
- Skill：提供详细决策框架，AI知道怎么决策
- CLAUDE.md：明确写入规则，作为长期文档

**预防未来问题**：
- 如果AI仍然问问题 → 检查Hook是否激活
- 如果决策质量差 → 改进Skill的决策框架
- 如果用户不满意 → 调整自主程度（修改Hook条件）
