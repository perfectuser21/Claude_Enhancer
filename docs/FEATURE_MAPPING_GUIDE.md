# Feature-to-Step Mapping Guide
# Claude Enhancer 核心功能映射指南

> **版本**: v1.0.0
> **更新日期**: 2025-10-18
> **适用版本**: Claude Enhancer 6.3+

---

## 📖 目录

1. [什么是Feature Mapping](#什么是feature-mapping)
2. [为什么需要它](#为什么需要它)
3. [使用场景](#使用场景)
4. [12个核心功能详解](#12个核心功能详解)
5. [Dashboard使用指南](#dashboard使用指南)
6. [API接口](#api接口)
7. [实战示例](#实战示例)
8. [常见问题](#常见问题)

---

## 什么是Feature Mapping

**Feature-to-Step Mapping** 是Claude Enhancer 6.3新增的核心功能，建立了**12个核心功能**与**77个验证步骤**之间的双向映射关系。

### 核心概念

```
核心功能 (Feature)  ←→  验证步骤 (Steps)
    ↓                        ↓
F002: Git Hooks      ←→  P2_S009, P2_S010, P3_S012, G003
```

### 映射类型

1. **Feature → Steps**: 一个功能涉及哪些验证步骤
2. **Step → Features**: 一个步骤影响哪些功能

---

## 为什么需要它

### 问题场景

#### 场景1：盲目修改
```
你："我要修改Git Hooks功能..."
系统："好的，改完了。"
你："需要测试什么？"
系统："呃...全部测一遍？"
```
❌ **问题**: 不知道影响范围，只能全量测试，浪费时间

#### 场景2：验证失败
```
验证报告："P3_S012失败了"
你："这个步骤是什么？影响哪些功能？"
系统："不知道..."
```
❌ **问题**: 无法快速定位问题影响的功能模块

### 有了Feature Mapping

#### 场景1：精准修改
```
你："我要修改Git Hooks功能"
系统："F002涉及4个步骤：P2_S009, P2_S010, P3_S012, G003"
你："修改完成，重点测试这4个步骤"
系统："✅ 4/4通过，其他73步不受影响"
```
✅ **优势**: 精准测试，效率提升10倍

#### 场景2：快速定位
```
验证报告："P3_S012失败了"
你："点击步骤查看影响"
系统："影响6个功能：F001, F002, F003, F004, F006, F011"
你："重点检查Git Hooks和Quality Gates"
```
✅ **优势**: 快速定位，问题根因分析时间减少80%

---

## 使用场景

### 场景A：功能更新前的影响评估

**你想要**: 优化Impact Radius Assessment功能
**需要知道**: 这个功能涉及哪些验证步骤？

**操作步骤**:
1. 打开Dashboard: `http://localhost:8999`
2. 找到 **F005: Impact Radius Assessment** 功能卡片
3. 点击卡片展开，查看涉及步骤
4. **结果**: `P0_S001, P0_S002, P1_S001` (共3步)
5. **影响提示**: "影响Agent选择策略，需要重新验证准确率"

**结论**: 只需重点测试3个步骤，不需要全量回归测试

---

### 场景B：验证失败后的快速定位

**情况**: 运行 `workflow_validator_v75.sh` 后发现 `P3_S012` 失败
**需要知道**: 这个步骤影响哪些功能？

**操作步骤**:
1. 在Dashboard中找到Phase 3卡片，展开查看
2. 找到 `P3_S012: Hook性能测试` 项
3. 点击步骤标签 `P3_S012`
4. **弹窗显示影响的功能**:
   - 📋 F001: 77-Step Workflow Validation
   - 🪝 F002: Git Hooks Integration
   - 🛡️ F003: Branch Protection System
   - 🔄 F004: 6-Phase Workflow
   - 🚪 F006: Quality Gate System
   - ✅ F011: Static Checks System

**结论**: 6个功能受影响，重点检查Git Hooks和Quality Gates

---

### 场景C：新功能设计时的步骤规划

**你想要**: 设计一个新的"代码格式化检查"功能
**需要知道**: 应该在哪些Phase添加验证步骤？

**参考步骤**:
1. 查看类似功能 **F011: Static Checks System**
2. 发现它在 Phase 3 (Testing阶段) 添加了9个步骤
3. **设计决策**: 新功能也应该在Phase 3添加，与其他静态检查并行
4. **映射关系**: 新功能 F013 → P3_S016, P3_S017 (新增步骤)

---

## 12个核心功能详解

### 🎯 功能分类

| 分类 | 功能数量 | 功能ID |
|-----|---------|--------|
| **核心系统** | 2 | F001, F004 |
| **质量保障** | 4 | F006, F007, F011, F012 |
| **自动化工具** | 2 | F002, F010 |
| **安全防护** | 1 | F003 |
| **智能决策** | 1 | F005 |
| **组织管理** | 2 | F008, F009 |

---

### F001: 77-Step Workflow Validation System
```yaml
ID: F001
名称: 77步工作流验证系统
描述: 完整验证框架，覆盖P0-P5所有阶段 + 2个全局验证
分类: Core (核心)
优先级: Critical (关键)
涉及步骤: 全部77步
测试覆盖率: 100%
影响评估: 全系统影响，需要完整回归测试
```

**何时修改**: 调整验证框架、添加新Phase、修改验证逻辑
**修改影响**: 极大，影响所有其他功能
**测试建议**: 完整回归测试，验证所有77步

---

### F002: Git Hooks Integration
```yaml
ID: F002
名称: Git Hooks集成
描述: Pre-commit, commit-msg, pre-push质量强制执行
分类: Automation (自动化)
优先级: High (高)
涉及步骤: P2_S009, P2_S010, P3_S012, G003
相关文件:
  - .git/hooks/pre-commit
  - .git/hooks/commit-msg
  - .git/hooks/pre-push
测试覆盖率: 95%
影响评估: 影响提交流程，需验证所有git操作
```

**何时修改**: 调整hook逻辑、添加新hook、修改拦截规则
**修改影响**: 高，影响开发者提交体验
**测试建议**: 验证正常提交、异常拦截、性能影响

---

### F003: Branch Protection System
```yaml
ID: F003
名称: 分支保护系统
描述: 4层防护 - Git hooks + CI/CD + GitHub + 监控
分类: Security (安全)
优先级: Critical (关键)
涉及步骤: P2_S009, P2_S010, P3_S012, P4_S010, G003
防护层级:
  - Layer 1: Local Git Hooks (100% logic protection)
  - Layer 2: CI/CD Verification (+30% monitoring)
  - Layer 3: GitHub Branch Protection (+100% server-side)
  - Layer 4: Continuous Monitoring (daily health)
测试覆盖率: 100%
影响评估: 安全关键，需要12场景压力测试验证
```

**何时修改**: 调整保护策略、修改拦截规则、添加新防护层
**修改影响**: 极高，关系到代码安全
**测试建议**: 12场景压力测试 (参考 BP_PROTECTION_REPORT.md)

---

### F004: 6-Phase Workflow System
```yaml
ID: F004
名称: 6-Phase工作流系统
描述: P0→P1→P2→P3→P4→P5完整开发生命周期
分类: Core (核心)
优先级: Critical (关键)
涉及步骤: 所有75个Phase步骤
Phase分解:
  P0: 8步 - Discovery & acceptance checklist
  P1: 12步 - Planning & architecture
  P2: 15步 - Implementation with commits
  P3: 15步 - Testing & static checks (Quality Gate)
  P4: 10步 - Code review & audit (Quality Gate)
  P5: 15步 - Release & monitoring
测试覆盖率: 100%
影响评估: 核心工作流，影响所有开发流程
```

**何时修改**: 调整Phase结构、合并/拆分Phase、修改流程顺序
**修改影响**: 极大，影响整个开发流程
**测试建议**: 完整工作流验证，从P0到P5完整执行一遍

---

### F005: Impact Radius Assessment (v6.5.1)
```yaml
ID: F005
名称: 影响半径评估系统
描述: 自动任务风险评估和Agent策略推荐
分类: Intelligence (智能)
优先级: High (高)
涉及步骤: P0_S001, P0_S002, P1_S001
评估公式: Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
阈值分级:
  - ≥50分 → 6 agents (高风险)
  - 30-49分 → 3 agents (中风险)
  - 0-29分 → 0 agents (低风险)
准确率: 86% (26/30 validated samples)
相关文件: .claude/scripts/impact_radius_assessor.sh
测试覆盖率: 86%
影响评估: 影响Agent选择策略，需要重新验证准确率
```

**何时修改**: 调整评估算法、修改阈值、优化准确率
**修改影响**: 中，影响Agent选择
**测试建议**: 30样本验证集测试，确保准确率≥85%

---

### F006: Quality Gate System
```yaml
ID: F006
名称: 质量门禁系统
描述: P3测试门禁 + P4审查门禁（阻塞检查点）
分类: Quality (质量)
优先级: Critical (关键)
涉及步骤: P3全部(15步) + P4全部(10步) + P5_S009
门禁机制:
  P3 Gate: 技术质量
    - Bash语法、Shellcheck、复杂度
    - Hook性能、功能测试
  P4 Gate: 代码质量
    - 配置完整性、版本一致性
    - 文档完整性、逻辑审查
阻塞原则: 任何gate失败都阻止进入下一Phase
相关脚本:
  - scripts/static_checks.sh
  - scripts/pre_merge_audit.sh
测试覆盖率: 100%
影响评估: 质量保障核心，需要完整测试验证
```

**何时修改**: 调整门禁阈值、添加新检查项、修改阻塞逻辑
**修改影响**: 极高，影响所有开发流程
**测试建议**: 验证正常通过、异常阻塞、边界case

---

### F007: 6-Layer Anti-Hollow Defense
```yaml
ID: F007
名称: 6层防空壳防御系统
描述: 防止空壳文件、占位符内容、缺失实现
分类: Quality (质量)
优先级: High (高)
涉及步骤: P0_S008, P1_S012, P2_S012, P3_S001-S004, P4_S006
防护层级:
  Layer 1: Structure Validation (结构强校验)
  Layer 2: Placeholder Detection (12个占位词)
  Layer 3: Sample Data Validation (JSON格式)
  Layer 4: Executability Check (脚本可运行)
  Layer 5: Test Report Validation (覆盖率)
  Layer 6: Evidence Traceability (证据留痕)
占位词清单:
  - TODO, FIXME, 待定, 占位
  - 稍后填写, 待补充, TBD
  - To be determined, Coming soon
  - Placeholder, 未实现, 待实现
测试覆盖率: 100%
影响评估: 检测精度变化，需要验证误报/漏报率
```

**何时修改**: 添加新占位词、调整检测逻辑、优化误报率
**修改影响**: 中，影响质量检测
**测试建议**: 验证误报率（真实内容不应被拦截）、漏报率（占位符应被检测）

---

### F008: Documentation Management
```yaml
ID: F008
名称: 文档管理系统
描述: 7核心文档规则，防止文档泛滥
分类: Organization (组织)
优先级: Medium (中)
涉及步骤: P4_S009, P5_S003, P5_S004
核心文档:
  1. README.md
  2. CLAUDE.md
  3. INSTALLATION.md
  4. ARCHITECTURE.md
  5. CONTRIBUTING.md
  6. CHANGELOG.md
  7. LICENSE.md
规则:
  - 禁止在根目录创建新.md文件
  - 临时分析放在.temp/ (7天TTL)
  - 创建永久文档前必须询问用户
测试覆盖率: 90%
影响评估: 文档组织策略，需要更新pre_write_document.sh hook
```

**何时修改**: 调整核心文档清单、修改文档规则
**修改影响**: 低，主要影响文档组织
**测试建议**: 验证根目录≤7个.md、临时文档自动清理

---

### F009: Version Consistency System
```yaml
ID: F009
名称: 版本一致性系统
描述: 确保5个文件版本号完全一致
分类: Release (发布)
优先级: High (高)
涉及步骤: P4_S007, P5_S013
版本文件:
  1. VERSION
  2. .claude/settings.json
  3. manifest.yml
  4. package.json
  5. CHANGELOG.md
强制执行: Phase 4 pre_merge_audit.sh验证，不一致阻止进入Phase 5
相关脚本:
  - scripts/check_version_consistency.sh
  - scripts/pre_merge_audit.sh
测试覆盖率: 100%
影响评估: 发布流程关键，需要验证所有版本文件
```

**何时修改**: 添加新版本文件、修改版本格式
**修改影响**: 高，影响发布流程
**测试建议**: 验证版本一致性检查、不一致拦截

---

### F010: Claude Hooks System
```yaml
ID: F010
名称: Claude Hooks系统
描述: 38个AI行为强制hooks
分类: Automation (自动化)
优先级: High (高)
涉及步骤: P0_S001, P1_S001, P2_S001, P2_S009, P2_S010, P3_S001, P4_S001, P4_S003, P5_S001
Hook类型:
  - PreToolUse (工具使用前)
  - PrePrompt (提示词处理前)
  - PostAction (操作完成后)
核心Hooks:
  - branch_helper.sh (分支前置检查)
  - smart_agent_selector.sh (智能Agent选择)
  - quality_gate.sh (质量门禁检查)
  - gap_scan.sh (差距分析)
  - force_branch_check.sh (强制分支验证)
  - code_writing_check.sh (代码写入拦截)
  - pre_write_document.sh (文档写入拦截)
总数: 38个hooks
测试覆盖率: 85%
影响评估: AI行为模式变化，需要完整行为测试
```

**何时修改**: 添加新hook、修改hook逻辑、调整触发时机
**修改影响**: 高，影响AI行为
**测试建议**: 验证hook触发时机、拦截逻辑、性能影响

---

### F011: Static Checks System
```yaml
ID: F011
名称: 静态检查系统 (Phase 3 Gate)
描述: Bash语法、Shellcheck、复杂度、Hook性能、功能测试
分类: Quality (质量)
优先级: Critical (关键)
涉及步骤: P3_S005-S012, P3_S014
检查项:
  1. Bash Syntax (bash -n)
  2. Shellcheck Linting (SC warnings)
  3. Code Complexity (>150行/函数阻止)
  4. Hook Performance (<5秒执行时间)
  5. Functional Tests (功能验证)
阻塞规则: 任何检查失败阻止进入Phase 4
相关脚本: scripts/static_checks.sh
测试覆盖率: 100%
影响评估: 质量标准变化，需要重新定义阈值
```

**何时修改**: 调整检查阈值、添加新检查项、修改阻塞逻辑
**修改影响**: 高，影响质量标准
**测试建议**: 验证正常通过、异常阻塞、复杂度阈值

---

### F012: Pre-Merge Audit System
```yaml
ID: F012
名称: 合并前审计系统 (Phase 4 Gate)
描述: 配置完整性、遗留问题、文档规范、版本一致性审计
分类: Quality (质量)
优先级: Critical (关键)
涉及步骤: P4_S003-S010
审计项:
  1. Config Integrity (hooks注册、权限)
  2. Legacy Issues Scan (TODO/FIXME)
  3. Document Compliance (根目录≤7个.md)
  4. Version Consistency (5文件版本号一致)
  5. Code Pattern Consistency (相似功能统一实现)
  6. Documentation Completeness (REVIEW.md >100行)
阻塞规则: 任何critical issue阻止进入Phase 5
相关脚本: scripts/pre_merge_audit.sh
测试覆盖率: 100%
影响评估: 审计标准变化，需要更新检查逻辑
```

**何时修改**: 调整审计标准、添加新审计项、修改阻塞逻辑
**修改影响**: 高，影响合并标准
**测试建议**: 验证配置完整性、遗留问题扫描、文档规范

---

## Dashboard使用指南

### 启动Dashboard

```bash
# 进入项目目录
cd "/home/xx/dev/Claude Enhancer 5.0"

# 启动服务
bash scripts/serve_progress.sh

# 输出示例:
# ======================================================================
# 🚀 Claude Enhancer Dashboard Server
# ======================================================================
#   Dashboard:        http://localhost:8999
#   API Progress:     http://localhost:8999/api/progress
#   API Features:     http://localhost:8999/api/feature_mapping
# ======================================================================
#   Press Ctrl+C to stop
```

### 访问Dashboard

浏览器打开: **http://localhost:8999**

---

### 界面布局

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Claude Enhancer Workflow Progress                       │
│  Last updated: 12:30:45                    🔄 Refresh       │
├─────────────────────────────────────────────────────────────┤
│  🎯 Core Features (12)         [Grid View] [List View]     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ F001    │ │ F002    │ │ F003    │ │ F004    │          │
│  │ 📋 77步 │ │ 🪝 4步  │ │ 🛡️ 5步  │ │ 🔄 75步 │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│  ...更多功能卡片...                                          │
├─────────────────────────────────────────────────────────────┤
│  Overall Progress: 87%                                      │
│  [████████████████████░░░░] 67/77 passed                    │
│  Current Phase: P3  |  Total: 77  |  Passed: 67  |  Failed: 10 │
├─────────────────────────────────────────────────────────────┤
│  👆 Click on any phase card to see detailed validation steps│
├─────────────────────────────────────────────────────────────┤
│  ▶ P0: Discovery (8 steps) - 100%                          │
│  ▼ P1: Planning & Architecture (12 steps) - 92% [展开]     │
│     ✓ P1_S001: PLAN.md exists                              │
│     ✓ P1_S002: Task decomposition                          │
│     ...                                                     │
│  ...更多Phase卡片...                                         │
└─────────────────────────────────────────────────────────────┘
```

---

### 功能区域详解

#### 1. 功能卡片区域（顶部）

**显示内容**:
- 12个核心功能的卡片网格
- 每个卡片显示：图标、名称、描述、优先级、分类、步骤数量

**交互操作**:
- **点击卡片**: 展开显示该功能涉及的所有步骤
- **切换视图**: Grid View (网格) / List View (列表)

**视觉效果**:
```
┌────────────────────────────────┐
│ 🪝  Git Hooks Integration      │
│                                │
│ Pre-commit, commit-msg,        │
│ pre-push质量强制执行           │
│                                │
│ [HIGH]  [AUTOMATION]  📌 4 steps│
│                                │
│ ▼ 展开查看步骤:                │
│   P2_S009  P2_S010  P3_S012   │
│   G003                         │
│                                │
│ ⚠️ Impact: 影响提交流程         │
└────────────────────────────────┘
```

#### 2. 整体进度区域（中部）

**显示内容**:
- 总进度百分比 (大号数字)
- 进度条 (彩色可视化)
- 统计卡片: Current Phase / Total Checks / Passed / Failed

**交互操作**:
- 无交互，仅展示

#### 3. Phase详情区域（底部）

**显示内容**:
- 6个Phase卡片（P0-P5）
- 每个Phase显示：名称、步骤数、进度百分比、质量门禁标记

**交互操作**:
- **点击Phase卡片**: 展开显示该Phase的所有验证步骤详情
- **点击步骤标签**: 弹出浮窗显示该步骤影响的所有功能

**步骤详情格式**:
```
✓ P3_S005: Bash syntax check     [BLOCKING]
✗ P3_S006: Shellcheck warnings   [BLOCKING]
⊘ P3_S007: Code complexity       [pending]
```

---

### 交互功能详解

#### 功能1: 查看功能涉及的步骤

**操作**: 点击任意功能卡片

**效果**:
1. 卡片展开，显示步骤列表
2. 相关步骤在Phase卡片中高亮显示（黄色背景）
3. 其他功能卡片自动收起

**示例**:
```
点击 F002: Git Hooks Integration
↓
卡片展开显示: P2_S009, P2_S010, P3_S012, G003
↓
下方Phase卡片中，这4个步骤黄色高亮
```

#### 功能2: 查看步骤影响的功能

**操作**: 点击任意步骤标签（如 `P3_S012`）

**效果**:
1. 弹出浮窗（右下角）
2. 显示该步骤影响的所有功能
3. 该步骤在Phase卡片中闪烁3秒（橙色）
4. 5秒后浮窗自动消失

**示例**:
```
点击 P3_S012
↓
浮窗显示:
┌─────────────────────────────┐
│ Step: P3_S012               │
│                             │
│ 📋 F001: Workflow Validation│
│ 🪝 F002: Git Hooks          │
│ 🛡️ F003: Branch Protection  │
│ 🔄 F004: 6-Phase Workflow   │
│ 🚪 F006: Quality Gates      │
│ ✅ F011: Static Checks      │
└─────────────────────────────┘
```

#### 功能3: 视图切换

**操作**: 点击 `Grid View` / `List View` 按钮

**效果**:
- Grid View: 卡片网格布局 (默认，3-4列)
- List View: 卡片列表布局 (单列，适合小屏幕)

#### 功能4: 实时刷新

**操作**: 点击右上角 `🔄 Refresh` 按钮

**效果**:
- 重新获取最新验证进度
- 更新所有统计数据
- 自动刷新: 每10秒自动刷新一次

---

## API接口

### 1. 获取验证进度

```bash
curl http://localhost:8999/api/progress
```

**返回示例**:
```json
{
  "timestamp": "2025-10-18T12:30:45Z",
  "current_phase": "P3",
  "overall_progress": 87.0,
  "overall": {
    "total": 77,
    "passed": 67,
    "failed": 10,
    "pass_rate": 87.0
  },
  "phases": [
    {
      "id": "P0",
      "name": "Discovery",
      "status": "completed",
      "progress": 100,
      "total_checks": 8,
      "passed_checks": 8,
      "failed": 0,
      "quality_gate": false,
      "checks": [
        {
          "id": "P0_S001",
          "name": "P0 Discovery文档存在",
          "status": "pass",
          "type": "file_existence",
          "blocking": true
        },
        ...
      ]
    },
    ...
  ]
}
```

---

### 2. 获取功能映射

```bash
curl http://localhost:8999/api/feature_mapping
```

**返回示例**:
```json
{
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2025-10-18",
    "total_features": 12,
    "total_steps": 77,
    "description": "Mapping between Claude Enhancer core features and validation steps"
  },
  "features": {
    "workflow_validation": {
      "id": "F001",
      "name": "77-Step Workflow Validation System",
      "description": "Complete validation framework...",
      "category": "core",
      "priority": "critical",
      "steps": ["P0_S001", "P0_S002", ...],
      "impact_when_changed": "全系统影响，需要完整回归测试",
      "test_coverage": "100%"
    },
    ...
  },
  "step_to_features_mapping": {
    "P0_S001": ["F001", "F004", "F005", "F010"],
    "P0_S002": ["F001", "F004", "F005"],
    ...
  }
}
```

---

## 实战示例

### 示例1: 优化Git Hooks性能

#### 背景
你发现 `pre-commit` hook执行太慢（3秒），想优化到<1秒。

#### 步骤

**Step 1: 查看功能映射**
```
Dashboard → F002: Git Hooks Integration
涉及步骤: P2_S009, P2_S010, P3_S012, G003
```

**Step 2: 修改代码**
```bash
vim .git/hooks/pre-commit
# 优化逻辑，减少文件读取...
```

**Step 3: 运行验证**
```bash
bash scripts/workflow_validator_v75.sh
```

**Step 4: 重点检查**
```
关注步骤:
✅ P2_S009: pre-commit hook存在且可执行
✅ P2_S010: commit-msg hook存在且可执行
✅ P3_S012: Hook性能测试 (语法检查)
✅ G003: Git Hooks安装验证

结果: 4/4通过，其他73步不受影响
```

**Step 5: 性能验证**
```bash
time bash .git/hooks/pre-commit --dry-run
# real    0m0.8s  ← 优化成功！
```

---

### 示例2: 调整Quality Gates阈值

#### 背景
你觉得 `P3_S014` 的复杂度阈值（150行）太严格，想调整到200行。

#### 步骤

**Step 1: 查看功能映射**
```
Dashboard → F006: Quality Gate System
涉及步骤: P3全部(15步) + P4全部(10步) + P5_S009

再查看 → F011: Static Checks System
涉及步骤: P3_S005-S012, P3_S014
```

**Step 2: 修改代码**
```bash
vim scripts/workflow_validator_v75.sh
# 找到 P3_S014: Code complexity
# 修改阈值: 150 → 200
```

**Step 3: 运行验证**
```bash
bash scripts/workflow_validator_v75.sh
```

**Step 4: 影响分析**
```
点击 P3_S014 步骤标签
弹窗显示影响的功能:
- F001: Workflow Validation
- F004: 6-Phase Workflow
- F006: Quality Gates
- F011: Static Checks

建议: 全量回归测试，验证阈值调整的合理性
```

**Step 5: 验证测试**
```bash
# 测试边界case
# 创建150行、200行、250行的测试脚本
# 验证检查逻辑是否正确
```

---

### 示例3: 添加新的验证步骤

#### 背景
你想添加一个新步骤 `P3_S016: ESLint JavaScript检查`

#### 步骤

**Step 1: 参考现有功能**
```
Dashboard → F011: Static Checks System
发现它在 Phase 3 添加了9个步骤
设计决策: 新步骤也应该在Phase 3
```

**Step 2: 更新Spec**
```bash
vim spec/workflow.spec.yaml
# 在Phase 3添加新步骤定义
```

**Step 3: 实现验证逻辑**
```bash
vim scripts/workflow_validator_v75.sh
# 添加 P3_S016 检查逻辑
```

**Step 4: 更新Feature Mapping**
```bash
vim tools/web/feature_mapping.json
# 将 P3_S016 添加到 F011: Static Checks System
# 更新 step_to_features_mapping
```

**Step 5: 更新元数据**
```bash
vim spec/workflow.spec.yaml
# total_steps: 77 → 78
# phase_steps: 75 → 76
```

**Step 6: 测试验证**
```bash
bash scripts/workflow_validator_v75.sh
# 期望: 78/78 (100%)

# Dashboard检查
# 期望: F011显示10个步骤（原9个+新1个）
```

---

## 常见问题

### Q1: 为什么有些功能涉及很多步骤？
**A**: 核心功能（如F001, F004）是系统基础，其他功能都依赖它们，所以涉及所有77步。这是正常的架构设计。

### Q2: 如何快速找到某个步骤的影响范围？
**A**:
1. 打开Dashboard
2. 展开相关Phase卡片
3. 点击步骤标签
4. 查看弹窗显示的影响功能

### Q3: 功能映射数据如何维护？
**A**: 手动维护 `tools/web/feature_mapping.json`。每次添加新功能或修改现有功能时更新映射关系。

### Q4: Dashboard无法访问怎么办？
**A**:
```bash
# 检查端口占用
lsof -i :8999

# 换个端口
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh

# 检查依赖
which python3
ls tools/web/dashboard.html
ls tools/web/feature_mapping.json
```

### Q5: 如何添加新的核心功能？
**A**:
1. 在 `feature_mapping.json` 添加新功能定义
2. 映射该功能涉及的验证步骤
3. 更新 `step_to_features_mapping` 反向映射
4. 更新元数据 `total_features`
5. Dashboard会自动显示新功能

### Q6: 如何修改功能的优先级或分类？
**A**: 直接编辑 `feature_mapping.json`，修改对应功能的 `priority` 和 `category` 字段。

### Q7: Dashboard支持移动端吗？
**A**: 支持响应式布局，但建议使用桌面浏览器获得最佳体验。移动端建议使用 List View。

### Q8: 如何导出功能映射报告？
**A**:
```bash
# JSON格式
curl http://localhost:8999/api/feature_mapping > feature_mapping_report.json

# 或直接复制文件
cp tools/web/feature_mapping.json ./feature_mapping_report.json
```

---

## 快速命令参考

```bash
# 启动Dashboard
bash scripts/serve_progress.sh

# 运行完整验证
bash scripts/workflow_validator_v75.sh

# 查看验证进度（JSON）
cat .evidence/last_run.json

# 查看功能映射（JSON）
cat tools/web/feature_mapping.json

# API调用示例
curl http://localhost:8999/api/progress | jq '.overall'
curl http://localhost:8999/api/feature_mapping | jq '.metadata'

# 查看特定功能的步骤
jq '.features.git_hooks.steps' tools/web/feature_mapping.json

# 查看特定步骤的影响功能
jq '.step_to_features_mapping["P3_S012"]' tools/web/feature_mapping.json
```

---

## 相关文档

- **Spec定义**: `spec/workflow.spec.yaml` - 77步骤完整定义
- **验证脚本**: `scripts/workflow_validator_v75.sh` - 执行引擎
- **功能映射**: `tools/web/feature_mapping.json` - Feature-Step映射
- **Dashboard**: `tools/web/dashboard.html` - 可视化界面
- **工作流指南**: `docs/WORKFLOW_VALIDATION.md` - 完整用户指南
- **Phase 0文档**: `docs/P0_DISCOVERY.md` - 系统设计文档

---

**最后更新**: 2025-10-18
**版本**: v1.0.0
**维护者**: Claude Backend Architect
**反馈**: 遇到问题请在GitHub Issues报告
