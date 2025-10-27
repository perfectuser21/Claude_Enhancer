# Implementation Plan - Phase 2-5 Autonomous Enforcement System

## 项目概述

**目标**：创建Hook + Skill组合系统，确保AI在Phase 2-5完全自主执行，不询问用户技术决策

**交付物**：
1. `.claude/hooks/phase2_5_autonomous.sh` - Claude Hook
2. `.claude/skills/phase2-5-autonomous/SKILL.md` - Skill定义
3. `.claude/settings.json` - Hook注册
4. `CLAUDE.md` - Phase 2-5定义更新

**预计工作量**：2-3小时

---

## Phase 2: Implementation

### Task 2.1: 创建Phase 2-5 Autonomous Hook

**文件**：`.claude/hooks/phase2_5_autonomous.sh`

**实现步骤**：

1. **创建文件并设置基础结构**
```bash
#!/bin/bash
# Claude Hook: Phase 2-5 Autonomous Enforcement
# 触发时机：PrePrompt
# 目的：确保Phase 2-5完全自主执行

set -euo pipefail
```

2. **实现Phase检测函数**
```bash
get_current_phase() {
    if [[ -f "$PHASE_DIR/current" ]]; then
        cat "$PHASE_DIR/current"
    else
        echo "Phase1"
    fi
}

CURRENT_PHASE=$(get_current_phase)
```

3. **实现激活条件检查**
```bash
# 只在Phase 2-5时激活
if [[ ! "$CURRENT_PHASE" =~ ^Phase[2-5]$ ]]; then
    exit 0
fi

# 需要AUTO_MODE_ACTIVE或REQUIREMENTS_CLARIFIED
if [[ -f "$WORKFLOW_DIR/AUTO_MODE_ACTIVE" || -f "$WORKFLOW_DIR/REQUIREMENTS_CLARIFIED" ]]; then
    # 注入自主指引
fi
```

4. **设计注入内容结构**
```
╔═══════════════════════════════════════════════════════════════╗
║  🤖 AUTONOMOUS MODE - Phase X                                 ║
╚═══════════════════════════════════════════════════════════════╝

【核心原则】
🚫 绝对禁止问用户的问题类型：...
✅ 你应该自己决定：...

【决策框架】
1️⃣  这是业务需求吗？ → 查文档
2️⃣  这是技术实现吗？ → YOU DECIDE
3️⃣  这是质量问题吗？ → FIX IMMEDIATELY
4️⃣  这是工作流问题吗？ → 参考CLAUDE.md

【Phase特定指引】
Phase 2: ...
Phase 3: ...
Phase 4: ...
Phase 5: ...
```

5. **实现错误处理**
```bash
# 确保即使出错也不阻止AI工作
exit 0
```

**验收标准**：
- [ ] Shellcheck通过
- [ ] Bash -n通过
- [ ] 执行时间<0.5秒
- [ ] 正确检测Phase
- [ ] 正确检测条件（AUTO_MODE_ACTIVE等）
- [ ] 注入内容清晰可读

---

### Task 2.2: 创建Phase 2-5 Autonomous Skill

**文件**：`.claude/skills/phase2-5-autonomous/SKILL.md`

**实现步骤**：

1. **创建目录结构**
```bash
mkdir -p .claude/skills/phase2-5-autonomous
```

2. **编写YAML frontmatter**
```yaml
---
name: phase2-5-autonomous
description: Phase 2-5 autonomous execution guidance - Activate when Claude needs to decide technical choices
version: 1.0.0
trigger: phase2|phase3|phase4|phase5|implementation|testing|review|release
---
```

3. **编写核心章节**

**Section 1: Skill Purpose** (说明用途)
- 何时激活
- 解决什么问题
- 与Hook的关系

**Section 2: Forbidden Questions** (禁止的问题)
- 技术选择类
- 实现细节类
- 质量问题类
- 工作流进度类

**Section 3: Decision-Making Framework** (决策框架)
```
### 1. Business Requirements → Check Documentation
- Where: .workflow/REQUIREMENTS_DIALOGUE.md, CHECKLIST.md
- How: Search for keyword, match requirement
- Example: Error message text → Check requirements

### 2. Technical Implementation → Apply Standards
- Where: Existing codebase, PLAN.md
- How: Match existing patterns, industry best practices
- Example: Testing framework → Check existing tests

### 3. Code Quality → Enforce Thresholds
- Where: CLAUDE.md quality standards
- How: Measure and compare
- Example: Function >150 lines → Refactor

### 4. Performance → Benchmark & Optimize
- Where: Performance budgets (hooks <2s)
- How: Profile, optimize, measure
- Example: Hook takes 3s → Find bottleneck, fix
```

**Section 4: Phase-Specific Guidelines**
```
### Phase 2: Implementation
- Autonomous actions
- Quality standards
- Output format

### Phase 3: Testing
- Autonomous actions
- Quality gates
- Output format

### Phase 4: Review
- Autonomous actions
- Critical checks
- Output format

### Phase 5: Release
- Autonomous actions
- Release checklist
- Output format
```

**Section 5: Examples** (示例场景)
- 正确示例：发现bug → 立即修复并报告
- 错误示例：发现bug → 问用户"要修吗"

**Section 6: Red Flags** (何时需要停下来)
- 矛盾的需求
- 缺失关键信息
- 外部依赖问题

**验收标准**：
- [ ] YAML frontmatter正确
- [ ] 内容≥300行
- [ ] 覆盖所有Phase 2-5场景
- [ ] 包含决策框架
- [ ] 包含示例
- [ ] Markdown格式正确

---

### Task 2.3: 注册Hook到settings.json

**文件**：`.claude/settings.json`

**实现步骤**：

1. **读取现有settings.json**
```bash
cat .claude/settings.json
```

2. **找到PrePrompt hooks数组**
```json
"PrePrompt": [
  ".claude/hooks/force_branch_check.sh",
  ".claude/hooks/ai_behavior_monitor.sh",
  ".claude/hooks/workflow_enforcer.sh",
  ".claude/hooks/smart_agent_selector.sh",
  ...
]
```

3. **在workflow_enforcer之后添加新hook**
```json
"PrePrompt": [
  ".claude/hooks/force_branch_check.sh",
  ".claude/hooks/ai_behavior_monitor.sh",
  ".claude/hooks/workflow_enforcer.sh",
  ".claude/hooks/phase2_5_autonomous.sh",  ← 新增
  ".claude/hooks/smart_agent_selector.sh",
  ...
]
```

4. **验证JSON格式**
```bash
jq '.' .claude/settings.json
```

**验收标准**：
- [ ] Hook添加到正确位置
- [ ] JSON格式正确（jq验证通过）
- [ ] 不影响其他hooks

---

### Task 2.4: 更新CLAUDE.md Phase 2-5定义

**文件**：`CLAUDE.md`

**实现步骤**：

1. **Phase 2更新** (约行684-702)

**添加内容**（在"【阶段目标】"之后）：
```markdown
【执行模式】：🤖 完全自主 - AI自己决定所有技术实现

【AI自主决策范围】：
  ✅ 技术选择：选择库、框架、工具（基于项目现有技术栈）
  ✅ 架构设计：设计模块、选择模式（遵循项目现有模式）
  ✅ 代码实现：编写代码、处理错误、添加日志
  ✅ 脚本创建：创建工具脚本（放在scripts/或tools/）
  ✅ Hook配置：注册hooks（.git/hooks/ + .claude/hooks/）

【禁止询问用户】：
  ❌ "用A库还是B库？"
  ❌ "这样实现可以吗？"
  ❌ "需要添加XX功能吗？"
  ❌ "Phase 2完成了，继续吗？"

【决策原则】：
  1. 参考Phase 1需求文档（REQUIREMENTS_DIALOGUE.md, CHECKLIST.md）
  2. 遵循技术方案（PLAN.md）
  3. 保持项目一致性（匹配现有代码风格和模式）
  4. 应用质量标准（函数<150行，复杂度<15）
```

2. **Phase 3更新** (约行706-729)

**添加内容**：
```markdown
【执行模式】：🤖 完全自主 - AI自己设计测试并修复所有问题

【AI自主决策范围】：
  ✅ 测试策略：决定测试类型、覆盖范围、用例设计
  ✅ Bug修复：发现bug立即修复，不询问
  ✅ 性能优化：检测性能问题并优化（hooks <2秒）
  ✅ 质量改进：降低复杂度、重构代码、提高可读性
  ✅ 迭代执行：失败→修复→重测，直到全部通过

【禁止询问用户】：
  ❌ "发现X个bug，要修复吗？"
  ❌ "测试覆盖率75%，要提高吗？"
  ❌ "性能3秒，需要优化吗？"
  ❌ "Shellcheck有warning，处理吗？"

【自动修复原则】：
  1. 语法错误 → 立即修复（bash -n检查）
  2. Linting警告 → 全部处理（Shellcheck）
  3. 性能问题 → benchmark后优化（目标<2秒）
  4. 复杂度过高 → 重构简化（目标<150行/函数）
  5. 覆盖率不足 → 补充测试（目标≥70%）
```

3. **Phase 4更新** (约行778-803)

**修改"【阶段目标】"**：
```markdown
【阶段目标】：AI手动审查 + 合并前审计
```

**添加内容**：
```markdown
【执行模式】：🤖 完全自主 - AI执行全面审查并修复所有问题

【AI自主决策范围】：
  ✅ 代码审查：逐行检查逻辑、语义、一致性
  ✅ 问题修复：发现问题立即修复，不询问
  ✅ 文档完善：补充遗漏的文档和注释
  ✅ 版本统一：确保6个文件版本100%一致
  ✅ Checklist验证：对照Phase 1验收清单逐项检查

【禁止询问用户】：
  ❌ "发现逻辑问题，要修复吗？"
  ❌ "代码模式不一致，要统一吗？"
  ❌ "REVIEW.md要写多详细？"
  ❌ "审查完成，进入Phase 5吗？"

【AI手动验证】：
  🤖 逻辑正确性（IF判断、return语义）- AI自己检查
  🤖 代码一致性（统一实现模式）- AI自己检查
  🤖 Phase 1 checklist对照验证 - AI自己检查

**注意**："人工验证"指AI手动检查，不是用户参与
```

4. **Phase 5更新** (约行809-830)

**添加内容**：
```markdown
【执行模式】：🤖 完全自主 - AI自己完成所有发布配置

【AI自主决策范围】：
  ✅ 文档更新：CHANGELOG.md、README.md内容和格式
  ✅ Tag创建：格式v{VERSION}，从VERSION文件读取
  ✅ 监控配置：健康检查端点、SLO阈值设定
  ✅ 部署文档：更新安装、配置、使用说明

【禁止询问用户】：
  ❌ "CHANGELOG写什么内容？"
  ❌ "README要更新哪些部分？"
  ❌ "Tag格式用v8.1.0还是8.1.0？"
  ❌ "SLO阈值设多少合适？"

【决策标准】：
  1. CHANGELOG：列出所有新功能、修复、改进（参考git log）
  2. README：更新版本号、新增功能说明
  3. Git Tag：严格使用v{VERSION}格式
  4. 监控：参考行业标准（99.9% uptime, <200ms p95）
```

**验收标准**：
- [ ] 所有4个Phase更新完成
- [ ] 不破坏现有结构
- [ ] Markdown格式正确
- [ ] 术语统一

---

### Task 2.5: 设置Hook权限

**实现步骤**：

```bash
chmod +x .claude/hooks/phase2_5_autonomous.sh
```

**验收标准**：
- [ ] Hook可执行

---

## Phase 3: Testing

### Test 3.1: Hook单元测试

**测试场景**：

```bash
# Test 1: Phase 2激活
echo "Phase2" > .phase/current
touch .workflow/AUTO_MODE_ACTIVE
bash .claude/hooks/phase2_5_autonomous.sh
# 预期：输出自主指引

# Test 2: Phase 1不激活
echo "Phase1" > .phase/current
bash .claude/hooks/phase2_5_autonomous.sh
# 预期：无输出，exit 0

# Test 3: Phase 6不激活
echo "Phase6" > .phase/current
bash .claude/hooks/phase2_5_autonomous.sh
# 预期：无输出，exit 0

# Test 4: Phase 3无AUTO_MODE不激活
echo "Phase3" > .phase/current
rm -f .workflow/AUTO_MODE_ACTIVE
rm -f .workflow/REQUIREMENTS_CLARIFIED
bash .claude/hooks/phase2_5_autonomous.sh
# 预期：无输出，exit 0
```

**验收标准**：
- [ ] 所有测试通过
- [ ] Hook执行时间<0.5秒

---

### Test 3.2: Skill格式验证

**测试步骤**：

1. 验证YAML frontmatter
```bash
head -10 .claude/skills/phase2-5-autonomous/SKILL.md
# 检查YAML格式
```

2. 验证trigger关键词
```bash
grep "trigger:" .claude/skills/phase2-5-autonomous/SKILL.md
# 确认包含phase2|phase3|phase4|phase5
```

**验收标准**：
- [ ] YAML语法正确
- [ ] Trigger关键词包含所有Phase 2-5

---

### Test 3.3: 集成测试

**测试场景**：模拟实际工作流

```bash
# Setup
echo "Phase2" > .phase/current
touch .workflow/AUTO_MODE_ACTIVE
mkdir -p .workflow/

# Simulate PrePrompt hook chain
.claude/hooks/workflow_enforcer.sh
.claude/hooks/phase2_5_autonomous.sh
.claude/hooks/smart_agent_selector.sh

# Check output
# 预期：phase2_5_autonomous.sh输出Phase 2指引
```

**验收标准**：
- [ ] Hook链正确执行
- [ ] 各Hook不冲突
- [ ] 输出清晰可读

---

### Test 3.4: 静态检查

**检查项**：

```bash
# Shellcheck
shellcheck .claude/hooks/phase2_5_autonomous.sh

# Syntax check
bash -n .claude/hooks/phase2_5_autonomous.sh

# JSON validation
jq '.' .claude/settings.json
```

**验收标准**：
- [ ] Shellcheck无warning
- [ ] 语法检查通过
- [ ] JSON格式正确

---

## Phase 4: Review

### Review 4.1: 代码审查

**检查清单**：

- [ ] Hook逻辑正确（Phase检测、条件判断）
- [ ] 错误处理完善（set -euo pipefail, exit 0）
- [ ] 变量命名清晰
- [ ] 注释充分
- [ ] 无硬编码路径

---

### Review 4.2: 文档审查

**检查清单**：

- [ ] P1_DISCOVERY完整（>300行）
- [ ] Acceptance Checklist覆盖所有验收点
- [ ] PLAN详细明确（本文档）
- [ ] Skill文档清晰易读
- [ ] CLAUDE.md更新准确

---

### Review 4.3: 一致性审查

**检查清单**：

- [ ] Hook模式与requirement_clarification.sh一致
- [ ] 术语使用统一
- [ ] 格式风格统一
- [ ] 中英文混用合理

---

## Phase 5: Release

### Release 5.1: 版本标记

**步骤**：

1. 确认版本号（8.0.1，不改变）
2. 更新CHANGELOG.md（添加本feature说明）
3. Git commit
4. Git tag（如需要）

---

### Release 5.2: 文档发布

**检查清单**：

- [ ] README更新（如需要）
- [ ] CLAUDE.md已更新
- [ ] Phase 1文档齐全

---

## Phase 6: Acceptance

**用户验收步骤**：

1. 用户实际使用1周
2. 观察AI在Phase 2-5的行为
3. 确认AI不再问技术问题
4. 确认AI决策质量符合预期
5. 用户说"没问题"

---

## Phase 7: Closure

### Final Checks

- [ ] 所有代码已commit
- [ ] 所有文档已完成
- [ ] 测试全部通过
- [ ] 用户验收通过
- [ ] 无遗留TODO

### Merge

等待用户说"merge"后执行PR流程

---

## 技术细节

### Hook执行流程图

```
PrePrompt触发
  ↓
检测.phase/current
  ├─ Phase1 → exit 0
  ├─ Phase2-5 → 继续
  └─ Phase6-7 → exit 0
      ↓
检查AUTO_MODE_ACTIVE或REQUIREMENTS_CLARIFIED
  ├─ 存在 → 注入指引
  └─ 不存在 → exit 0
      ↓
注入Phase特定内容
  ├─ Phase2 → Implementation指引
  ├─ Phase3 → Testing指引
  ├─ Phase4 → Review指引
  └─ Phase5 → Release指引
      ↓
exit 0（不阻止AI工作）
```

### Skill激活流程图

```
AI遇到决策点
  ↓
识别关键词（phase2/phase3/implementation/testing等）
  ↓
激活phase2-5-autonomous skill
  ↓
读取SKILL.md内容
  ↓
应用Decision Framework
  ↓
做出决策并执行
```

---

## 依赖关系

### 文件依赖
- `phase2_5_autonomous.sh` 依赖：
  - `.phase/current`（Phase检测）
  - `.workflow/AUTO_MODE_ACTIVE`或`REQUIREMENTS_CLARIFIED`（条件检测）

- `SKILL.md` 依赖：
  - CLAUDE.md（质量标准参考）
  - PLAN.md（技术方案参考）

### Hook执行顺序依赖
- 必须在`workflow_enforcer.sh`之后（先确定Phase）
- 应该在`smart_agent_selector.sh`之前（自主原则影响Agent选择）

---

## 风险缓解

| 风险 | 缓解措施 | 责任人 |
|------|---------|-------|
| AI误判自主范围 | Hook明确列出禁止问题类型 | AI |
| Hook冲突 | 正确排序，测试验证 | AI |
| 性能下降 | Hook快速执行（<0.5s） | AI |
| 用户不满意 | 提供退出机制（删除AUTO_MODE_ACTIVE） | 用户 |

---

## 成功标准

**技术标准**：
- [ ] 所有测试通过
- [ ] 代码质量符合标准
- [ ] 文档完整

**用户标准**：
- [ ] Phase 2-5期间AI不问技术问题
- [ ] AI决策质量符合预期
- [ ] 工作流流畅

**长期标准**：
- [ ] 1个月无问题
- [ ] 成为标准模式
- [ ] 用户满意度提升

---

## 预计时间线

- **Phase 2** (Implementation): 1-1.5小时
  - Task 2.1: 30分钟
  - Task 2.2: 30分钟
  - Task 2.3: 10分钟
  - Task 2.4: 20分钟

- **Phase 3** (Testing): 30分钟

- **Phase 4** (Review): 20分钟

- **Phase 5** (Release): 10分钟

- **Phase 6** (Acceptance): 1周（用户实际使用）

- **Phase 7** (Closure): 10分钟

**总计**：2-3小时开发 + 1周验证
