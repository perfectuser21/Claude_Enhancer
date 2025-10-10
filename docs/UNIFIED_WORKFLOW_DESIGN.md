# Claude Enhancer 统一工作流设计方案

**设计日期**: 2025-10-10
**版本**: v5.4.0-proposed
**基于**: 矛盾点分析报告
**目标**: 解决15个已识别矛盾，建立一致的工作流体系

---

## 🎯 设计原则

### 原则1：明确定位

```
Claude Enhancer定位为："可配置强度的质量保障系统"

不是：
❌ 完全自由（无约束）
❌ 完全强制（无灵活性）

而是：
✅ 分层保障（可选择强度）
✅ 明确规则（清晰边界）
✅ 合理例外（有记录的bypass）
```

### 原则2：实现匹配承诺

```
文档说"强制"→ 实现必须强制
文档说"建议"→ 实现是建议
不再使用模糊词汇
```

### 原则3：用户为中心

```
非程序员：需要简单、清晰的指导
程序员：需要详细、准确的规范
Owner：需要明确的权限和责任定义
```

### 原则4：可验证性

```
每个规则必须：
- 可以自动检测违反
- 有清晰的错误信息
- 提供修复建议
```

---

## 📊 三层保障体系（重新设计）

### 层级定义

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Advisory（建议层）                     │
│  ├─ Claude Hooks (branch_helper.sh等)          │
│  ├─ 作用：友好提示，可以忽略                      │
│  └─ 绕过：允许，但会记录                          │
├─────────────────────────────────────────────────┤
│  Layer 2: Enforcement（执行层）                  │
│  ├─ Git Hooks (pre-commit, pre-push等)        │
│  ├─ 作用：强制检查，阻止不合规操作                 │
│  └─ 绕过：--no-verify（仅限特定场景）            │
├─────────────────────────────────────────────────┤
│  Layer 3: Protection（保护层）                   │
│  ├─ GitHub Branch Protection                   │
│  ├─ 作用：服务端强制，完全无法绕过                 │
│  └─ 绕过：不可绕过（除非Admin临时禁用）            │
└─────────────────────────────────────────────────┘

注：Layer 3是可选的，但强烈推荐用于团队项目
```

### 层级选择指南

**个人项目（Solo Owner）**：
```
推荐配置：Layer 1 + Layer 2
理由：
- 有足够提示避免错误
- 保留必要灵活性
- 可以快速迭代
```

**小团队项目（2-5人）**：
```
推荐配置：Layer 1 + Layer 2 + Layer 3（基础）
理由：
- 防止团队成员误操作
- 保持代码质量一致
- 保留owner的紧急修复能力
```

**大团队/生产项目**：
```
推荐配置：Layer 1 + Layer 2 + Layer 3（严格）
理由：
- 完全强制PR流程
- 包括admin在内都需遵守
- 审计和合规要求
```

---

## 🔄 统一工作流定义

### Phase -1 → P7 → Merge的完整流程

```
┌─────────────────────────────────────────────────────────┐
│                  Phase -1: 分支准备                      │
│  ────────────────────────────────────────────────────── │
│  位置：任何分支                                           │
│  触发：用户提出新任务                                      │
│  行为：                                                   │
│  1. AI检查当前分支                                        │
│  2. 如果在main → 创建feature分支                          │
│  3. 如果在feature → 智能判断是否继续或新建                  │
│  4. 确认后进入P0                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              P0-P7: 标准开发流程                         │
│  ────────────────────────────────────────────────────── │
│  位置：feature/xxx分支                                    │
│  约束：                                                   │
│  - 禁止在main分支执行                                     │
│  - 每个Phase有明确的allow_paths                           │
│  - 每个Phase完成后切换到下一Phase                          │
│                                                          │
│  P0: 探索 → P1: 规划 → P2: 骨架 → P3: 实现               │
│  → P4: 测试 → P5: 审查 → P6: 发布 → P7: 监控             │
│                                                          │
│  P7完成标志：                                            │
│  - observability/*_MONITOR_REPORT.md已创建                │
│  - SLO定义完成                                           │
│  - 监控仪表板配置                                         │
│  - .phase/current=P7                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Phase 8 (新增): PR & Merge                  │
│  ────────────────────────────────────────────────────── │
│  位置：feature/xxx → GitHub → main                        │
│  步骤：                                                   │
│  1. 确认P7完成                                           │
│  2. Push feature分支到远程                                │
│  3. 在GitHub创建Pull Request                             │
│  4. 等待CI检查通过                                        │
│  5. 等待Code Review（如果配置）                           │
│  6. 在GitHub上Merge（不是本地merge！）                    │
│  7. Pull最新的main分支                                    │
│  8. Tag在main分支创建                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Post-Merge: 清理和验证                       │
│  ────────────────────────────────────────────────────── │
│  1. 删除本地feature分支（可选）                            │
│  2. 删除远程feature分支（在GitHub上）                      │
│  3. 验证main分支的健康状态                                 │
│  4. 触发生产部署（如果有CI/CD）                            │
└─────────────────────────────────────────────────────────┘
```

### 关键变更

**变更1：新增Phase 8（P8: PR & Merge）**
```
之前：P7完成后直接git merge
现在：P7完成后进入P8，走GitHub PR流程

理由：
- 解决矛盾2.1（Merge命令冲突）
- 统一团队和个人的流程
- 提供CI自动检查的入口
```

**变更2：Tag在main创建，不在feature创建**
```
之前：P6在feature分支创建tag
现在：P8在main分支merge后创建tag

理由：
- 解决矛盾2.2（Tag时机不明）
- Tag应该指向main的commit
- 符合Git最佳实践
```

**变更3：明确P6和P7的边界**
```
P6（发布准备）：
- 在feature分支执行
- 更新文档（README, CHANGELOG）
- 准备release notes
- 创建PR描述

P7（监控配置）：
- 在feature分支执行
- 配置监控方案
- 定义SLO
- 创建监控报告

P8（PR & Merge）：
- 从feature到main的过程
- 在GitHub上执行
- CI检查和人工审查
- Merge后在main创建tag
```

---

## 🛡️ Hook规则重新定义

### Hook分类

```yaml
Advisory Hooks (建议性):
  - .claude/hooks/branch_helper.sh
  - .claude/hooks/smart_agent_selector.sh
  - .claude/hooks/quality_gate.sh
  特点:
    - 提供指导和建议
    - 不阻止操作
    - 记录到日志
    - 可以完全忽略

Enforcement Hooks (执行性):
  - .git/hooks/pre-commit
  - .git/hooks/commit-msg
  - .git/hooks/pre-push
  特点:
    - 阻止不合规操作
    - exit 1会中断git操作
    - 可以用--no-verify绕过（特定场景）
    - 绕过需要在commit message中说明

Protection (保护性):
  - GitHub Branch Protection Rules
  特点:
    - 服务端强制
    - 完全无法绕过（除非Admin临时禁用）
    - 适用于所有人（可配置include administrators）
```

### --no-verify使用场景定义

**允许使用--no-verify的场景**：

1. **工作流元操作**
   ```
   场景：修改gates.yml, hooks等工作流基础设施
   原因：避免递归依赖
   要求：在commit message中说明理由
   审计：记录到特殊日志
   ```

2. **紧急生产修复（Owner Only）**
   ```
   场景：Critical bug需要立即修复
   原因：业务连续性优先于流程
   要求：
   - 必须是Owner或指定的On-call人员
   - 修复后24小时内补充完整流程
   - 记录到incident log
   ```

3. **Bootstrap操作**
   ```
   场景：首次安装Claude Enhancer
   原因：Hook还未安装时需要commit hooks本身
   要求：仅限install.sh脚本使用
   ```

**禁止使用--no-verify的场景**：

```
❌ "不想等测试跑完"
❌ "觉得这个改动很小"
❌ "只是临时修改"
❌ "我是Owner所以可以"（除非是上述允许场景）
```

### Hook执行流程图

```
用户执行：git commit

         ↓
┌────────────────────┐
│ Pre-commit Hook    │
│ 执行检查           │
└────────┬───────────┘
         │
    检查通过? ─No→ 显示错误信息 → 用户修复 → 重试
         │
        Yes
         ↓
┌────────────────────┐
│ Commit-msg Hook    │
│ 验证commit message │
└────────┬───────────┘
         │
    格式正确? ─No→ 显示错误信息 → 用户修正 → 重试
         │
        Yes
         ↓
    Commit成功创建
         ↓
用户执行：git push

         ↓
┌────────────────────┐
│ Pre-push Hook      │
│ 最终检查           │
└────────┬───────────┘
         │
    可以推送? ─No→ 显示错误（禁止推送main）→ 停止
         │           推荐创建PR
        Yes
         ↓
    推送到远程feature分支
         ↓
┌────────────────────┐
│ 创建PR (GitHub)    │
└────────┬───────────┘
         │
         ↓
┌────────────────────┐
│ CI Checks          │
│ - Lint             │
│ - Tests            │
│ - Security Scan    │
│ - Gate Validation  │
└────────┬───────────┘
         │
    全部通过? ─No→ 修复问题 → Push修复 → CI重新运行
         │
        Yes
         ↓
┌────────────────────┐
│ Code Review        │
│ (如果配置)         │
└────────┬───────────┘
         │
    Approved? ─No→ 修改代码 → 重新Review
         │
        Yes
         ↓
┌────────────────────┐
│ Merge to Main      │
│ (在GitHub上)       │
└────────┬───────────┘
         ↓
    Merge成功
         ↓
    触发部署
```

---

## 📋 Owner权限策略

### Owner Bypass Policy

**基本原则**：
```
Owner是规则的守护者，不是规则的例外。
Owner应该以身作则，遵守规则。
```

**Owner的特殊权限**：

1. **配置权限**
   ```
   可以：
   - 修改gates.yml
   - 修改hook配置
   - 临时禁用GitHub保护（紧急情况）

   不可以：
   - 随意绕过规则
   - 不记录bypass原因
   ```

2. **紧急权限**
   ```
   在Critical Incident时：
   - 可以使用--no-verify
   - 可以直接push到main
   - 可以临时禁用保护

   但必须：
   - 记录incident ticket
   - 24小时内补充流程
   - 进行事后复盘
   ```

3. **审计责任**
   ```
   Owner的所有bypass操作：
   - 记录到audit log
   - 每月生成报告
   - 在CHANGELOG中说明
   ```

### Bypass记录格式

```bash
# 使用--no-verify时，commit message必须包含：
git commit --no-verify -m "fix: emergency patch for CVE-xxx

BYPASS JUSTIFICATION:
- Type: Emergency Production Fix
- Severity: Critical (P0)
- Incident: INC-2025-001
- Approved By: [Owner Name]
- Follow-up: Created #123 for post-incident review

This bypass is recorded in audit log."
```

---

## 🔧 具体实施方案

### 方案A：渐进式升级（推荐）

**适合**：现有项目，不想breaking change

**阶段1：文档修正（v5.3.6）**
```
时间：1-2天
任务：
1. 更新所有冲突文档
2. 统一Merge流程说明
3. 明确--no-verify使用场景
4. 发布文档勘误

影响：无破坏性变更
```

**阶段2：Hook增强（v5.4.0）**
```
时间：3-5天
任务：
1. 增强pre-push检测GitHub PR
2. 添加bypass记录机制
3. 创建audit log
4. 更新hook文档

影响：
- 如果在feature分支，行为不变
- 如果推送main，会建议创建PR
- 仍可用--no-verify绕过
```

**阶段3：GitHub保护配置（v5.4.0+）**
```
时间：根据项目决定
任务：
1. 执行./scripts/setup_branch_protection.sh
2. 配置CI workflows
3. 配置CODEOWNERS
4. 测试PR流程

影响：
- main分支完全保护
- 必须通过GitHub PR
- 提供migration guide
```

### 方案B：Clean Slate（全新开始）

**适合**：新项目，或愿意breaking change的项目

**一次性实施**：
```
1. 更新所有文档（统一版本）
2. 重写hooks（按新规则）
3. 配置GitHub保护
4. 提供完整示例
5. 发布v6.0.0（表明breaking change）
```

---

## 📐 修正后的文档结构

### 文档层级

```
Level 1: 快速开始
├─ QUICKSTART.md
└─ QUICKSTART_PR_SETUP.md (updated)

Level 2: 核心概念
├─ CLAUDE.md (updated)
├─ README.md (updated)
└─ UNIFIED_WORKFLOW_DESIGN.md (new)

Level 3: 详细指南
├─ docs/P0_TO_P7_GUIDE.md
├─ docs/P8_PR_MERGE_GUIDE.md (new)
├─ docs/BRANCH_PROTECTION_SETUP.md (updated)
└─ docs/PHASE_INTERRUPTION_GUIDE.md

Level 4: 参考文档
├─ docs/HOOK_REFERENCE.md (new)
├─ docs/BYPASS_POLICY.md (new)
└─ docs/TROUBLESHOOTING_GUIDE.md (updated)

Level 5: ADR (Architecture Decision Records)
└─ docs/adr/
    ├─ 001-three-layer-protection.md
    ├─ 002-phase-8-pr-merge.md
    └─ 003-owner-bypass-policy.md
```

### 文档一致性检查表

```yaml
consistency_checks:
  - name: "Merge流程一致性"
    files:
      - CLAUDE.md
      - README.md
      - docs/PR-RULE0.md
      - docs/P8_PR_MERGE_GUIDE.md
    check: "所有文档必须说走GitHub PR流程"

  - name: "Hook强制性描述一致"
    files:
      - CLAUDE.md
      - docs/HOOK_REFERENCE.md
    check: "明确区分Advisory/Enforcement/Protection"

  - name: "--no-verify场景一致"
    files:
      - docs/BYPASS_POLICY.md
      - CLAUDE.md
    check: "允许场景必须完全匹配"

  - name: "P6/P7边界一致"
    files:
      - .workflow/gates.yml
      - CLAUDE.md
      - docs/P0_TO_P7_GUIDE.md
    check: "P6和P7的产出描述必须一致"
```

---

## 🎯 解决矛盾的映射表

| 矛盾ID | 矛盾点 | 解决方案 | 实施阶段 |
|--------|--------|----------|----------|
| 1.1 | Hook可绕过 | 明确定义为Enforcement层，可绕过但需记录 | 阶段1 |
| 1.2 | GitHub保护未配置 | 提供配置脚本和指南，标记为可选Layer 3 | 阶段3 |
| 1.3 | 执行模式检测不全 | 增强检测，包括merge操作 | 阶段2 |
| 2.1 | Merge命令冲突 | 统一为P8: GitHub PR流程 | 阶段1 |
| 2.2 | Tag创建时机不明 | 明确在main merge后创建 | 阶段1 |
| 2.3 | P6定位模糊 | 明确P6在feature分支，P8负责merge | 阶段1 |
| 3.1 | Hook类型未分类 | 创建HOOK_REFERENCE.md明确分类 | 阶段1 |
| 3.2 | --no-verify场景未定义 | 创建BYPASS_POLICY.md定义场景 | 阶段1 |
| 4.1 | 工作流终点不一致 | 新增P8明确终点 | 阶段1 |
| 4.2 | 质量层级夸大 | 修正为3层，明确Layer 3可选 | 阶段1 |
| 4.3 | Phase-1定位混乱 | 明确Phase-1用于新任务，P8用于merge | 阶段1 |
| 4.4 | Owner角色未定义 | 创建Owner Bypass Policy | 阶段1 |
| 5.1 | P6/P7边界模糊 | 明确定义每个Phase的产出 | 阶段1 |
| 5.2 | 多终端merge未说明 | 在P8指南中说明顺序merge策略 | 阶段1 |
| 6.1 | Owner Bypass Policy缺失 | 创建完整的Owner Bypass Policy | 阶段1 |

---

## 📊 成功指标

### 定量指标

```yaml
metrics:
  - name: "文档一致性"
    target: "100%"
    measurement: "自动化检查通过率"

  - name: "用户理解度"
    target: ">90%"
    measurement: "用户调查：能正确描述merge流程"

  - name: "Bypass记录完整性"
    target: "100%"
    measurement: "所有--no-verify都有justification"

  - name: "GitHub保护采用率"
    target: ">80%"
    measurement: "active项目中配置了Branch Protection"
```

### 定性指标

```
Success Criteria:
✅ 用户能清楚地知道："我应该走GitHub PR"
✅ 开发者能清楚地知道："什么时候可以--no-verify"
✅ Owner能清楚地知道："我的权限和责任"
✅ 文档之间不再有冲突
✅ 实现匹配文档的承诺
```

---

## 🚀 立即可执行的行动

### 对当前规则0的处理

**选项1：保持现状，记录例外（推荐）**
```bash
# 1. 创建例外记录
cat > docs/adr/001-rule0-merge-exception.md << 'EOF'
# ADR 001: 规则0直接Merge例外

## 背景
规则0(v5.3.5)在实施时，直接merge到main而非走GitHub PR。

## 决策
接受这个例外，理由：
- 规则0本身是定义PR流程的
- 当时GitHub Branch Protection未配置
- 作为Owner的一次性操作
- 代码已通过完整P3-P7验证

## 后果
- 规则0生效后，所有后续更新必须走GitHub PR
- 这个例外记录在案
- 不设先例
EOF

# 2. 补充commit说明
git notes add HEAD -m "EXCEPTION DOCUMENTED: docs/adr/001-rule0-merge-exception.md"
```

**选项2：回退重做（标准但耗时）**
```bash
# 1. 回退main
git reset --hard HEAD~1  # 回退merge commit

# 2. 配置GitHub保护
./scripts/setup_branch_protection.sh

# 3. 创建PR
gh pr create -f docs/PR-RULE0.md

# 4. Merge via GitHub
# (在GitHub UI上操作)
```

### 你的决策

作为Owner，你需要决定：

**问题1：Claude Enhancer的定位**
```
A. 指导性框架（hooks可以绕过）
B. 半强制系统（推荐配置GitHub保护）
C. 完全强制系统（必须配置GitHub保护）

推荐：B（适合最多用户）
```

**问题2：当前规则0的处理**
```
A. 保持现状，记录例外
B. 回退重做，走标准流程

推荐：A（实用主义，已经验证过质量）
```

**问题3：实施计划**
```
A. 渐进式升级（阶段1→阶段2→阶段3）
B. 一次性升级（发布v6.0）

推荐：A（降低影响，逐步改进）
```

---

## 📝 总结

### 核心改进

1. **新增P8: PR & Merge阶段**
   - 解决merge流程矛盾
   - 统一团队和个人流程

2. **三层保障明确定义**
   - Advisory（建议）
   - Enforcement（执行）
   - Protection（保护-可选）

3. **Owner Bypass Policy**
   - 明确权限和责任
   - 定义bypass场景
   - 要求记录和审计

4. **文档一致性保证**
   - 层级化结构
   - 自动化一致性检查
   - ADR记录决策

### 下一步

等待你的决策：
1. 选择定位（A/B/C）
2. 选择当前规则0的处理（A/B）
3. 选择实施计划（A/B）

然后我会生成：
- 具体的修复步骤
- 更新的文档
- 实施脚本
- 测试计划

---

*本设计方案基于WORKFLOW_CONTRADICTIONS_ANALYSIS.md*
*设计时间: 2025-10-10*
*等待用户确认后实施*
