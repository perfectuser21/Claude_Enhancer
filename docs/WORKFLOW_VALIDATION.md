# 工作流验证系统 - 用户指南

> **Claude Enhancer 6.5.1 完成标准验证系统**
> 让"完成"可验证、可证明、有信心

---

## 📖 目录

1. [什么是工作流验证系统](#什么是工作流验证系统)
2. [为什么需要它](#为什么需要它)
3. [快速开始（3分钟上手）](#快速开始)
4. [完整验证体系（75步）](#完整验证体系)
5. [如何使用](#如何使用)
6. [理解验证结果](#理解验证结果)
7. [如何修复失败项](#如何修复失败项)
8. [Dashboard可视化](#dashboard可视化)
9. [6层防空壳机制](#6层防空壳机制)
10. [常见问题FAQ](#常见问题faq)
11. [最佳实践](#最佳实践)

---

## 什么是工作流验证系统

### 简单类比：装修验收报告

想象你装修房子，装修公司说"完成了"。你会相信吗？

**传统方式**：
```
装修公司："我们完成了！"
你："真的吗？"
装修公司："真的！"
你："但我怎么知道？"
装修公司："相信我们吧..."
```

**有验收报告的方式**：
```
装修公司："我们完成了！这是验收清单：
✅ 水电布线 - 已验收（附照片）
✅ 墙面粉刷 - 已验收（附质检报告）
✅ 地板铺设 - 已验收（附防水测试）
✅ 家具安装 - 已验收（附稳固性测试）
总评分：96/100（优秀）"

你："太棒了！有证据我就放心了！"
```

### Claude Enhancer的验证系统

工作流验证系统就是你的"开发任务验收报告生成器"。

**它做什么**：
1. **检查Phase 2-7的完成情况** - 像装修监理检查每个房间
2. **生成证据文件** - 像装修照片和质检报告
3. **计算完成百分比** - 像装修进度条：[██████████░] 85%
4. **给出明确建议** - 像装修监理告诉你"插座还没装，赶紧补上"

---

## 为什么需要它

### 问题场景

**场景1：AI说"完成了"，但实际上...**
```
你："帮我实现用户认证系统"
AI："已完成！代码已提交"
你："测试通过了吗？"
AI："呃...我写了测试文件..."
你："那文档呢？"
AI："呃...好像忘了..."
```

**场景2：不知道还剩多少工作**
```
你："现在进度如何？"
AI："已经做了很多工作！"
你："具体多少？"
AI："挺多的..."（毫无帮助）
```

**场景3：无法向老板/同事证明**
```
老板："这个功能完成了吗？"
你："AI说完成了..."
老板："有证明吗？"
你："呃...相信我？"（老板黑脸）
```

### 解决方案：75步验证系统

```
┌──────────────────────────────────────────┐
│  工作流验证系统 (75步完整检查)           │
│  "用证据说话，不用猜测"                   │
├──────────────────────────────────────────┤
│  ✅ Phase 2完成度：100% (10/10项)        │
│  ✅ Phase 1完成度：100% (10/10项)        │
│  ✅ Phase 2完成度：100% (9/9项)          │
│  ⚠️  Phase 3完成度：80% (12/15项)        │
│     └─ 缺失：性能测试报告                │
│  ❌ Phase 4完成度：60% (6/10项)          │
│     └─ 缺失：代码审查报告                │
│     └─ 缺失：安全审计                    │
│  ❌ Phase 5完成度：0% (0/15项)           │
│                                          │
│  📊 总体完成度：70% - 不推荐合并          │
│  📋 证据文件：.evidence/last_run.json   │
│  🎯 下一步：完成Phase 3和Phase 4         │
│                                          │
│  🛡️ 防空壳机制：6层检查全部通过 ✅       │
└──────────────────────────────────────────┘
```

**好处**：
1. **透明** - 一眼看出完成了什么、还缺什么
2. **可证明** - 有数据文件，不是空口说
3. **可信** - 80%+完成度才说"完成"
4. **省时** - 不用一项项手动检查
5. **防空壳** - 6层机制防止"只有框架没有实现"

---

## 快速开始

### 1分钟快速验证

```bash
# 进入你的项目目录
cd /home/xx/dev/Claude\ Enhancer\ 5.0

# 运行验证脚本（只需这一步！）
bash scripts/workflow_validator.sh

# 等待5-10秒，看结果
```

**你会看到**：
```
╔════════════════════════════════════════╗
║  Claude Enhancer 工作流验证           ║
╚════════════════════════════════════════╝

检查 Phase 2 (Discovery)...
  ✅ P0_S001: P0_DISCOVERY.md exists
  ✅ P0_S002: P0_DISCOVERY.md substantial (384 lines)
  ✅ P0_S003: Problem Statement section
  ✅ P0_S004: Background section
  ✅ P0_S005: Feasibility analysis
  ✅ P0_S006: Acceptance Checklist
  ✅ P0_S007: Impact Radius assessment
  ✅ P0_S008: No placeholders (anti-hollow)
  Phase 2: 100% (10/10) ✅

检查 Phase 1 (Planning & Architecture)...
  ✅ P1_S001: PLAN.md exists
  ✅ P1_S002: PLAN.md substantial (1257 lines)
  ... (其他检查)
  Phase 1: 100% (10/10) ✅

... (其他Phase检查)

════════════════════════════════════════
📊 总体完成度：70%
📋 证据文件：.evidence/last_run.json
🎯 建议：还有23个必须项需要完成

详细报告已生成！
════════════════════════════════════════
```

### 2分钟查看可视化Dashboard

```bash
# 启动Dashboard服务（图形化界面）
bash scripts/serve_progress.sh

# 浏览器自动打开或手动访问
# http://localhost:8999
```

**Dashboard显示**：
```
┌─────────────────────────────────────────────────┐
│  Claude Enhancer Workflow Dashboard             │
│  75步验证系统可视化                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  总体完成度: 70% ████████████░░░░░░              │
│                                                 │
│  Phase 2: Discovery          100% ████████████  │
│  Phase 1: Planning           100% ████████████  │
│  Phase 2: Implementation     100% ████████████  │
│  Phase 3: Testing             80% ███████████░  │
│  Phase 4: Review              60% █████████░░░  │
│  Phase 5: Release              0% ░░░░░░░░░░░░  │
│                                                 │
│  🛡️ 防空壳机制：6/6层通过 ✅                     │
│  ⚠️  质量门禁1 (P3)：未达标                      │
│  ❌ 质量门禁2 (P4)：未激活                       │
│                                                 │
│  [点击Phase查看详情] [刷新数据] [生成报告]       │
└─────────────────────────────────────────────────┘
```

---

## 完整验证体系（75步）

### 验证架构总览

```
╔═══════════════════════════════════════════════════════════╗
║           75步完整验证体系（6 Phases + 3 Global）          ║
╚═══════════════════════════════════════════════════════════╝

Phase 1: Branch Check (分支前置检查) - 5 steps
├─ S-101: Git仓库有效性
├─ S-102: 当前分支检测
├─ S-103: 主分支保护检查 [CRITICAL]
├─ S-104: 分支命名规范
└─ S-105: Hook完整性检查

Phase 2: Discovery (探索与验收) - 10 steps
├─ S001: P0文档存在性 [CRITICAL]
├─ S002: 问题陈述定义 [CRITICAL]
├─ S003: 可行性分析 [CRITICAL]
├─ S004: 验收清单存在性 [CRITICAL]
├─ S005: 验收清单项数量（≥5）
├─ S006: 成功标准定义
├─ S007: 占位词检测 [防空壳 Layer 2]
├─ S008: 空章节检测 [防空壳 Layer 1]
├─ S009: P0证据目录
└─ S010: P0时间戳记录 [防空壳 Layer 6]

Phase 1: Planning & Architecture (规划+架构) - 10 steps
├─ S101: PLAN.md存在性 [CRITICAL]
├─ S102: 任务分解章节
├─ S103: 任务描述非空 [防空壳 Layer 2]
├─ S104: 架构设计章节
├─ S105: 技术栈定义
├─ S106: Agent策略定义
├─ S107: 目录结构文档
├─ S108: 关键目录创建
├─ S109: API接口定义（如适用）
└─ S110: P1证据记录 [防空壳 Layer 6]

Phase 2: Implementation (实现开发) - 9 steps
├─ S201: Git提交存在性 [CRITICAL]
├─ S202: Commit规范检查
├─ S203: 代码文件修改 [防空壳 Layer 4]
├─ S204: Shell语法预检查 [防空壳 Layer 4]
├─ S205: 敏感信息检测 [CRITICAL]
├─ S206: 大文件检测
├─ S207: 注释存在性（≥10%）
├─ S208: README更新（重大变更）
└─ S209: P2证据记录 [防空壳 Layer 6]

Phase 3: Testing (质量验证) [质量门禁1] - 8 steps
├─ S301: 静态检查脚本存在 [CRITICAL]
├─ S302: 静态检查执行通过 [CRITICAL, BLOCKING]
├─ S303: 测试文件存在性 [防空壳 Layer 5]
├─ S304: 测试执行通过 [防空壳 Layer 5]
├─ S305: 测试覆盖率（≥70%）[防空壳 Layer 5]
├─ S306: BDD场景存在性
├─ S307: BDD测试执行
└─ S308: P3证据记录 [防空壳 Layer 6]

Phase 4: Review (代码审查) [质量门禁2] - 10 steps
├─ S401: 审计脚本存在 [CRITICAL]
├─ S402: 合并前审计通过 [CRITICAL, BLOCKING]
├─ S403: REVIEW.md存在性 [CRITICAL]
├─ S404: 审查内容完整性
├─ S405: 审查发现记录
├─ S406: 版本一致性脚本存在 [CRITICAL]
├─ S407: 版本一致性验证 [CRITICAL, BLOCKING]
├─ S408: 遗留问题扫描（TODO/FIXME）
├─ S409: P0验收清单验证
└─ S410: P4证据记录 [防空壳 Layer 6]

Phase 5: Release & Monitor (发布+监控) - 10 steps
├─ S501: CHANGELOG更新
├─ S502: README最终检查
├─ S503: 文档链接有效性
├─ S504: Git Tag存在性
├─ S505: Tag格式验证（semver）
├─ S506: Release Notes
├─ S507: 健康检查脚本
├─ S508: SLO定义（如适用）
├─ S509: P0验收清单最终确认
└─ S510: P5证据记录 [防空壳 Layer 6]

Global Validations (全局验证) - 3 steps
├─ G001: 根目录文档数量限制（≤7）
├─ G002: 临时文件检查（<10MB）
└─ G003: Git Hooks安装验证

════════════════════════════════════════════════════════════
总计：75步验证
  - Critical (关键): 18步 - 失败则阻止继续
  - High (高优先级): 12步 - 强烈建议修复
  - Medium (中优先级): 25步 - 建议修复
  - Low (低优先级): 20步 - 可选优化
  - Blocking (阻塞性): 8步 - 质量门禁，必须通过
════════════════════════════════════════════════════════════
```

### 验证步骤分类

#### 1. 关键步骤（Critical - 18步）

这些步骤失败会**立即阻止**工作流继续：

```yaml
Phase 1:
  - S-103: 主分支保护检查（禁止在main/master开发）

Phase 2:
  - S001: P0文档存在性
  - S002: 问题陈述定义
  - S003: 可行性分析
  - S004: 验收清单存在性

Phase 1:
  - S101: PLAN.md存在性

Phase 2:
  - S201: Git提交存在性
  - S205: 敏感信息检测

Phase 3:
  - S301: 静态检查脚本存在
  - S302: 静态检查执行通过 [BLOCKING]

Phase 4:
  - S401: 审计脚本存在
  - S402: 合并前审计通过 [BLOCKING]
  - S403: REVIEW.md存在性
  - S406: 版本一致性脚本存在
  - S407: 版本一致性验证 [BLOCKING]
```

#### 2. 防空壳步骤（Anti-Shell - 31步）

这些步骤确保实现是**真实的，非占位符**：

```yaml
Layer 1: 结构强校验（20步）
  - 验证文件存在性
  - 验证章节完整性
  - 验证内容长度（>100行）

Layer 2: 占位词拦截（2步）
  - S007: P0占位词检测
  - S103: P1占位词检测
  - 检测：TODO, FIXME, 待定, TBD, 占位, Coming soon

Layer 3: 样例数据验证（5步）
  - 确保数据真实非示例

Layer 4: 可执行性验证（4步）
  - S203: 代码文件修改检测
  - S204: Shell语法检查
  - S301: 静态检查脚本存在
  - S401: 审计脚本存在

Layer 5: 测试报告验证（P3阶段）
  - S303: 测试文件存在性
  - S304: 测试执行通过
  - S305: 测试覆盖率≥70%

Layer 6: 证据留痕（每Phase）
  - S010, S110, S209, S308, S410, S510
  - 每个Phase生成时间戳证据文件
```

#### 3. 质量门禁步骤（Quality Gates - 2个）

这些步骤是**阻塞性检查点**，必须100%通过：

```yaml
质量门禁1 (Phase 3):
  - S302: 静态检查执行通过
  - 包含：Shell语法、Shellcheck、复杂度、性能
  - 失败 → 阻止进入Phase 4

质量门禁2 (Phase 4):
  - S402: 合并前审计通过
  - S407: 版本一致性验证
  - 包含：配置完整性、遗留问题、文档规范
  - 失败 → 阻止进入Phase 5
```

---

## 如何使用

### 场景1：开发过程中检查进度

**何时使用**：完成某个Phase后，想知道是否真的"完成"了

```bash
# 例如：你刚完成Phase 2（实现阶段）
git add .
git commit -m "feat: implement user authentication"

# 提交前运行验证
bash scripts/workflow_validator.sh

# 查看Phase 2的完成度
# 如果<80%，说明还有东西没做
```

**实际例子**：
```
你："AI，帮我实现登录功能"
AI："已完成实现阶段（Phase 2）"
你：（运行validator）
验证结果：
  ✅ S201: 代码已提交
  ✅ S202: Commit规范正确
  ✅ S203: 代码文件已修改
  ❌ S207: 注释覆盖率5%（目标10%+）
  ❌ S208: README未更新
  Phase 2: 56% - 未完成！

你："AI，你说完成了，但验证显示只有56%"
AI："抱歉，我补上注释和文档"
（真正完成后）
Phase 2: 100% ✅
```

### 场景2：准备合并到主分支前

**何时使用**：功能开发完，想合并到main，需要确保质量

```bash
# 在feature分支上
git checkout feature/user-auth

# 全面验证
bash scripts/workflow_validator.sh

# 查看总体完成度
# 如果≥80%，可以放心合并
# 如果<80%，说明质量不够，继续完善
```

**决策标准**：
```
完成度 ≥ 80% ✅ - 可以合并
完成度 60-79% ⚠️ - 谨慎合并（可能有风险）
完成度 < 60% ❌ - 不要合并（质量不够）

质量门禁：
  - Phase 3门禁未通过 ❌ - 不能合并
  - Phase 4门禁未通过 ❌ - 不能合并
  - 两个门禁都通过 ✅ - 可以合并
```

### 场景3：使用可视化Dashboard监控

**启动Dashboard**：

```bash
# 方式1：使用内置服务器（推荐）
bash scripts/serve_progress.sh

# 方式2：手动启动
python3 -m http.server 8999 --directory tools/web
```

**访问**：
- URL: http://localhost:8999
- API: http://localhost:8999/api/progress

**Dashboard功能**：
1. **实时刷新** - 每次刷新重新执行validator
2. **Phase详情** - 点击Phase查看所有检查项
3. **失败项追踪** - 红色标记失败的步骤
4. **防空壳指示器** - 显示6层检查状态
5. **质量门禁状态** - 显示是否可以进入下一Phase

### 场景4：向老板/同事证明完成度

**何时使用**：需要展示工作成果，提供可信证据

```bash
# 生成验证报告
bash scripts/workflow_validator.sh

# 复制证据文件（带时间戳）
cp .evidence/last_run.json ./work_evidence_$(date +%Y%m%d).json

# 生成PDF报告（可选）
# 使用Dashboard截图或导出JSON
```

**邮件模板**：
```
主题：用户认证功能 - 开发完成报告

Hi Boss,

用户认证功能已完成开发，以下是验证报告：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 75步验证系统报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Phase 2-4：100%完成（29/29步）
✅ Phase 3：100%完成（8/8步）
✅ Phase 4：95%完成（9/10步）
✅ Phase 5：100%完成（10/10步）

📊 总体质量：98/100（优秀）
🛡️ 防空壳机制：6/6层通过
✅ 质量门禁1：通过
✅ 质量门禁2：通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 证据文件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

详细证据见附件：work_evidence_20251017.json

Dashboard可视化：http://localhost:8999
（或截图见附件）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 结论
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

可以放心部署到生产环境。

Best,
[Your Name]
```

---

## 理解验证结果

### 命令行输出格式

```bash
════════════════════════════════════════
Phase 2 (Discovery): ✅ 100% (10/10)
  ✅ P0_S001: P0_DISCOVERY.md exists
  ✅ P0_S002: P0_DISCOVERY.md substantial (384 lines)
  ✅ P0_S003: Problem Statement section
  ✅ P0_S004: Background section
  ✅ P0_S005: Feasibility analysis
  ✅ P0_S006: Acceptance Checklist defined
  ✅ P0_S007: Impact Radius assessment
  ✅ P0_S008: No placeholders (anti-hollow)
  ✅ P0_S009: Evidence directory created
  ✅ P0_S010: P0 timestamp recorded

Phase 1 (Planning & Architecture): ⚠️ 90% (9/10)
  ✅ P1_S001: PLAN.md exists
  ✅ P1_S002: PLAN.md substantial (1257 lines)
  ✅ P1_S003: Executive Summary section
  ✅ P1_S004: System Architecture section
  ✅ P1_S005: Agent Strategy mentioned
  ✅ P1_S006: Implementation Plan exists
  ✅ P1_S007: Project directory structure
  ✅ P1_S008: .workflow/current tracking file
  ❌ P1_S009: Technology stack not documented
  ✅ P1_S010: No placeholders (anti-hollow)

════════════════════════════════════════
📊 总体完成度：95% (71/75)
🛡️ 防空壳机制：6/6层通过
✅ 质量门禁1：通过
✅ 质量门禁2：通过
📋 证据文件：.evidence/last_run.json
════════════════════════════════════════
```

**符号含义**：
- ✅ **绿色对勾** - 完成且质量合格
- ⚠️ **黄色警告** - 完成但有小问题，或可选项缺失
- ❌ **红色叉号** - 必须项缺失，阻止"完成"声明

**百分比含义**：
```
100%    = 完美！所有必须项+可选项都完成
80-99%  = 优秀！必须项完成，部分可选项缺失
60-79%  = 及格，但有必须项缺失
<60%    = 不及格，大量必须项缺失
```

### 证据文件（.evidence/last_run.json）

```json
{
  "timestamp": "2025-10-17T10:30:00Z",
  "overall_progress": 95,
  "total_checks": 75,
  "passed_checks": 71,
  "failed_checks": 4,
  "pass_rate": 95,

  "phases": {
    "phase0": {
      "id": "P0",
      "name": "Discovery",
      "total": 10,
      "passed": 10,
      "failed": 0,
      "progress": 100,
      "status": "completed",
      "completed_at": "2025-10-17T09:00:00Z",
      "evidence_hash": "abc123...",
      "anti_shell_layers": {
        "layer_1": "passed",
        "layer_2": "passed",
        "layer_6": "passed"
      }
    },
    "phase1": {
      "id": "P1",
      "name": "Planning & Architecture",
      "total": 10,
      "passed": 9,
      "failed": 1,
      "progress": 90,
      "status": "mostly_complete",
      "failed_checks": ["P1_S009"]
    }
    // ... 其他Phase
  },

  "anti_shell_report": {
    "layer_1_structure": { "checks": 20, "passed": 20, "status": "✅" },
    "layer_2_placeholder": { "checks": 2, "passed": 2, "status": "✅" },
    "layer_3_sample_data": { "checks": 5, "passed": 5, "status": "✅" },
    "layer_4_executability": { "checks": 4, "passed": 4, "status": "✅" },
    "layer_5_test_report": { "checks": 3, "passed": 3, "status": "✅" },
    "layer_6_evidence": { "checks": 6, "passed": 6, "status": "✅" },
    "overall": "6/6 layers passed"
  },

  "quality_gates": {
    "P3_testing": { "status": "passed", "blocking_checks": ["P3_S302"] },
    "P4_review": { "status": "passed", "blocking_checks": ["P4_S402", "P4_S407"] }
  },

  "merge_ready": true,
  "merge_readiness_score": 95,

  "recommendations": [
    "补充P1技术栈文档（P1_S009）",
    "建议添加性能测试（可选）",
    "考虑增加BDD场景覆盖（可选）"
  ]
}
```

---

## 如何修复失败项

### 通用修复流程（3步）

```
1. 运行验证 → 2. 识别问题 → 3. 修复并重新验证
     ↓              ↓              ↓
   validator     看红色❌       补上缺失的
                 看黄色⚠️       修复问题
                                 ↓
                          重新运行validator
                                 ↓
                            绿色✅ = 完成
```

### 常见失败项及修复方法

#### 失败1：P0_S004 - 验收清单缺失

**问题**：
```
Phase 2: ❌ 60% (6/10)
  ❌ P0_S004: Acceptance Checklist missing
```

**原因**：你跳过了Phase 0，直接开始编码

**修复**：
```bash
# 1. 回到Phase 0，创建验收清单
cat >> docs/P0_DISCOVERY.md << 'EOF'

## Acceptance Checklist

验收标准（"完成"的定义）：

当满足以下条件时，认为任务完成：

- [ ] 用户可以注册账号（用户名+密码）
- [ ] 用户可以登录并获得token
- [ ] 受保护的API需要token才能访问
- [ ] 密码加密存储（不能明文）
- [ ] 测试覆盖率≥80%
- [ ] 文档完整（README + API文档）
- [ ] 代码审查通过
- [ ] 安全审计通过
- [ ] 性能测试通过（响应时间<200ms）
- [ ] 所有75步验证通过
EOF

# 2. 重新验证
bash scripts/workflow_validator.sh

# 3. 确认修复
# Phase 2: ✅ 100% (10/10)
```

#### 失败2：P3_S302 - 静态检查失败 [BLOCKING]

**问题**：
```
Phase 3: ❌ BLOCKED
  ❌ P3_S302: static_checks failed (BLOCKING)
  → 阻止进入Phase 4
```

**原因**：代码有语法错误或不符合规范

**修复**：
```bash
# 1. 运行静态检查查看详细错误
bash scripts/static_checks.sh

# 示例输出：
# ❌ Shell语法错误（文件：deploy.sh 行:15）
#    → if [ $VAR = "test" ]  # 缺少引号
# ❌ Shellcheck警告（SC2086：变量未加引号）
#    → FILES=$FILES_LIST  # 应该 FILES="$FILES_LIST"

# 2. 修复错误
# 原代码（错误）：
# if [ $VAR = "test" ]; then
#   FILES=$FILES_LIST
# fi

# 修复后：
# if [ "$VAR" = "test" ]; then
#   FILES="$FILES_LIST"
# fi

# 3. 重新运行静态检查
bash scripts/static_checks.sh
# ✅ 所有检查通过

# 4. 重新验证
bash scripts/workflow_validator.sh
# Phase 3: ✅ 100% (8/8)
# ✅ 质量门禁1：通过
```

#### 失败3：P4_S407 - 版本不一致 [BLOCKING]

**问题**：
```
Phase 4: ❌ BLOCKED
  ❌ P4_S407: version mismatch (BLOCKING)
  → VERSION: 6.5.1
  → package.json: 6.5.0
  → CHANGELOG.md: 6.5.1
  → 阻止进入Phase 5
```

**原因**：多个文件版本号不一致

**修复**：
```bash
# 1. 查看不一致的文件
bash scripts/check_version_consistency.sh

# 2. 统一版本号到6.5.1
echo "6.5.1" > VERSION
jq '.version = "6.5.1"' package.json > tmp && mv tmp package.json
sed -i 's/version: .*/version: 6.5.1/' .claude/settings.json
sed -i 's/version: .*/version: 6.5.1/' .claude/manifest.yml

# 3. 更新CHANGELOG（如果需要）
# 确保CHANGELOG.md包含[6.5.1]条目

# 4. 重新验证版本一致性
bash scripts/check_version_consistency.sh
# ✅ All 5 files match: 6.5.1

# 5. 重新验证工作流
bash scripts/workflow_validator.sh
# Phase 4: ✅ 100% (10/10)
# ✅ 质量门禁2：通过
```

#### 失败4：防空壳Layer 2 - 检测到占位词

**问题**：
```
Phase 2: ⚠️ 90% (9/10)
  ❌ P0_S007: Placeholders detected (anti-hollow)
  → Found: "TODO", "待定", "稍后填写"
  → Layer 2防空壳机制触发
```

**原因**：文档包含占位词，内容不完整

**修复**：
```bash
# 1. 查找占位词位置
grep -n "TODO\|FIXME\|待定\|TBD" docs/P0_DISCOVERY.md

# 示例输出：
# 45: ## 技术栈选择：TODO
# 67: ## 风险评估：待定

# 2. 替换占位词为实际内容
# 原文档：
# ## 技术栈选择：TODO

# 修复后：
# ## 技术栈选择
#
# 经过技术调研，选择以下技术栈：
# - 后端框架：Express.js 4.18
# - 数据库：PostgreSQL 14
# - 缓存：Redis 7.0
# - 加密：bcrypt + JWT

# 3. 重新验证
bash scripts/workflow_validator.sh
# ✅ P0_S007: No placeholders (anti-hollow)
# 🛡️ Layer 2: 2/2 checks passed
```

#### 失败5：防空壳Layer 5 - 测试报告缺失

**问题**：
```
Phase 3: ⚠️ 80% (12/15)
  ❌ P3_S305: Test coverage report missing
  → Layer 5防空壳机制触发
```

**原因**：测试没有生成覆盖率报告

**修复**：
```bash
# 1. 运行测试并生成覆盖率
npm test -- --coverage

# 或（对于Python项目）
pytest --cov=src --cov-report=json

# 2. 验证覆盖率文件存在
ls -lh coverage/coverage-summary.json
# -rw-r--r-- 1 user user 2.5K Oct 17 10:30 coverage/coverage-summary.json

# 3. 检查覆盖率数值
jq '.total.lines.pct' coverage/coverage-summary.json
# 87.5  (目标≥70%)

# 4. 重新验证
bash scripts/workflow_validator.sh
# ✅ P3_S305: Test coverage 87.5% (≥70%)
# 🛡️ Layer 5: 3/3 checks passed
```

### 快速修复指南（速查表）

| 失败项 | 快速修复命令 | 预计时间 |
|-------|------------|---------|
| P0验收清单缺失 | 创建`docs/P0_DISCOVERY.md` + 添加Checklist章节 | 5分钟 |
| P1技术栈未定义 | 补充`docs/PLAN.md`技术栈章节 | 10分钟 |
| P3静态检查失败 | `bash scripts/static_checks.sh` + 修复 | 10-20分钟 |
| P4版本不一致 | `bash scripts/check_version_consistency.sh` + 统一 | 5分钟 |
| P5 CHANGELOG未更新 | 添加新版本条目到`CHANGELOG.md` | 5分钟 |
| 占位词检测失败 | 替换TODO/待定为实际内容 | 10-30分钟 |
| 测试覆盖率不足 | `npm test -- --coverage` + 补充测试 | 20-60分钟 |

---

## Dashboard可视化

### Dashboard功能

**URL**: http://localhost:8999

**功能列表**：

1. **实时进度显示**
   - 总体完成度进度条
   - 6个Phase独立进度条
   - 百分比数值显示

2. **Phase详情卡片**
   - 点击Phase展开详情
   - 显示所有检查项
   - 失败项高亮显示（红色）
   - 成功项显示（绿色）

3. **防空壳指示器**
   - 6层防空壳机制状态
   - 每层通过/失败显示
   - 总体通过率

4. **质量门禁状态**
   - 质量门禁1（P3）状态
   - 质量门禁2（P4）状态
   - 阻塞提示

5. **Git Hooks状态**
   - pre-commit状态
   - commit-msg状态
   - pre-push状态
   - 最后检查时间

6. **Claude Hooks状态**
   - branch_helper.sh状态
   - smart_agent_selector.sh状态
   - 触发时机说明

7. **操作按钮**
   - 刷新数据（重新运行validator）
   - 生成报告（导出JSON）
   - 查看证据（打开.evidence/）

### 启动Dashboard

```bash
# 方式1：使用内置服务器（推荐）
bash scripts/serve_progress.sh

# 输出：
# ╔═══════════════════════════════════════╗
# ║  🚀 Claude Enhancer Dashboard Server  ║
# ╚═══════════════════════════════════════╝
#   URL:  http://localhost:8999
#   API:  http://localhost:8999/api/progress
# ══════════════════════════════════════════
#   Press Ctrl+C to stop

# 方式2：更改端口
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh
```

### API端点

**GET /api/progress**

返回当前工作流进度的JSON数据：

```json
{
  "timestamp": "2025-10-17T10:30:00Z",
  "current_phase": "P2",
  "overall_progress": 70,
  "validation_system": "75-step",
  "phases": [
    {
      "id": "P0",
      "name": "Discovery",
      "total_checks": 10,
      "passed_checks": 10,
      "progress": 100,
      "status": "completed"
    }
    // ... 其他Phase
  ],
  "anti_shell_layers": {
    "layer_1_structure_validation": {
      "checks": 20,
      "passed": 20,
      "status": "✅"
    }
    // ... 其他层
  },
  "quality_gates": {
    "P3_testing": { "status": "not_reached" },
    "P4_review": { "status": "not_reached" }
  }
}
```

---

## 6层防空壳机制

### 什么是"空壳"问题？

**空壳实现**指的是：
- ✅ 文件存在
- ✅ 目录结构正确
- ❌ **但内容是占位符、示例、TODO**
- ❌ **代码不能运行或测试不通过**

**例子**：
```python
# 空壳实现（看起来完成了，但没有实际功能）
def authenticate_user(username, password):
    # TODO: 实现认证逻辑
    pass

# 测试也是空壳
def test_authenticate():
    # TODO: 补充测试
    assert True
```

### 6层防空壳机制

Claude Enhancer使用**6层递进式检查**防止空壳实现：

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: 结构强校验 (20 checks)                      │
│  ├─ 文件存在性验证                                    │
│  ├─ 文件大小验证（>1KB）                              │
│  ├─ 章节完整性验证                                    │
│  └─ 内容长度验证（>100行）                            │
├──────────────────────────────────────────────────────┤
│  Layer 2: 占位词拦截 (2 checks)                       │
│  ├─ 检测：TODO, FIXME, TBD, 待定                      │
│  ├─ 检测：占位, Coming soon, Placeholder              │
│  └─ 检测：稍后填写, 待补充, 未实现                     │
├──────────────────────────────────────────────────────┤
│  Layer 3: 样例数据验证 (5 checks)                     │
│  ├─ 检测示例数据（example@example.com）               │
│  ├─ 检测测试数据（test123, dummy）                    │
│  └─ 确保有真实数据                                    │
├──────────────────────────────────────────────────────┤
│  Layer 4: 可执行性验证 (4 checks)                     │
│  ├─ Shell脚本语法检查（bash -n）                      │
│  ├─ Shellcheck静态分析                               │
│  ├─ 代码复杂度检查（McCabe）                          │
│  └─ 性能测试（执行时间<2秒）                          │
├──────────────────────────────────────────────────────┤
│  Layer 5: 测试报告验证 (3 checks)                     │
│  ├─ 测试文件存在性                                    │
│  ├─ 测试执行通过                                      │
│  └─ 测试覆盖率≥70%                                    │
├──────────────────────────────────────────────────────┤
│  Layer 6: 证据留痕 (6 checks)                         │
│  ├─ 每个Phase生成证据文件                             │
│  ├─ 包含时间戳                                        │
│  ├─ 包含文件哈希                                      │
│  └─ 可溯源、可审计                                    │
└──────────────────────────────────────────────────────┘

总计：40个防空壳检查（占75步的53%）
```

### 防空壳检查示例

#### Layer 1: 结构强校验

**检查**：P0_S002 - P0文档内容充实性

```bash
# 失败示例（空壳）
docs/P0_DISCOVERY.md:
  ## Problem Statement
  (empty - 空章节)

# 通过示例（真实内容）
docs/P0_DISCOVERY.md:
  ## Problem Statement

  当前用户认证系统存在以下问题：
  1. 密码明文存储，存在安全隐患
  2. 没有token机制，每次请求都需要验证用户名密码
  3. 没有会话管理，用户体验差

  (>100行详细分析...)
```

#### Layer 2: 占位词拦截

**检查**：P0_S007, P1_S103 - 占位词检测

```bash
# 失败示例（包含占位词）
docs/PLAN.md:
  ## 技术栈选择
  TODO: 补充技术栈

# 通过示例（实际内容）
docs/PLAN.md:
  ## 技术栈选择

  经过技术调研，选择以下技术栈：
  - 后端：Express.js 4.18（轻量、生态成熟）
  - 数据库：PostgreSQL 14（ACID保证）
  - 缓存：Redis 7.0（高性能会话存储）
  - 加密：bcrypt + JWT（业界标准）
```

#### Layer 4: 可执行性验证

**检查**：P2_S204, P3_S302 - Shell脚本可执行性

```bash
# 失败示例（语法错误）
scripts/deploy.sh:
  if [ $VAR = "test" ]  # 未加引号，shellcheck警告
    echo "Starting..."
  fi  # 缺少then

# 通过示例（正确语法）
scripts/deploy.sh:
  if [ "$VAR" = "test" ]; then
    echo "Starting..."
  fi
```

#### Layer 5: 测试报告验证

**检查**：P3_S303, P3_S304, P3_S305 - 测试真实性

```bash
# 失败示例（空壳测试）
test/auth.test.js:
  describe('Authentication', () => {
    it('should authenticate user', () => {
      // TODO: 补充测试
      expect(true).toBe(true);  # 无意义断言
    });
  });

# 通过示例（真实测试）
test/auth.test.js:
  describe('Authentication', () => {
    it('should authenticate valid user', async () => {
      const user = await authenticate('john', 'secret123');
      expect(user).toBeDefined();
      expect(user.username).toBe('john');
      expect(user.token).toMatch(/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/);
    });

    it('should reject invalid credentials', async () => {
      await expect(
        authenticate('john', 'wrong')
      ).rejects.toThrow('Invalid credentials');
    });
  });

# 覆盖率报告存在
coverage/coverage-summary.json:
  { "total": { "lines": { "pct": 87.5 } } }
```

#### Layer 6: 证据留痕

**检查**：P0_S010, P1_S110, ... - 可验证证据

```bash
# 每个Phase完成后自动生成
.evidence/p2/timestamp.yml:
  completed_at: 2025-10-17T10:30:00Z
  phase: P0
  hash: abc123def456...  # 文件哈希，防篡改

.evidence/p1/timestamp.yml:
  completed_at: 2025-10-17T11:00:00Z
  phase: P1
  plan_hash: def456abc789...

.evidence/p2/timestamp.yml:
  completed_at: 2025-10-17T12:30:00Z
  phase: P2
  commits:
    - a1b2c3d: feat(auth): add user authentication (John Doe, 2 hours ago)
    - e4f5g6h: test(auth): add authentication tests (John Doe, 1 hour ago)
```

### 防空壳验证报告

运行validator后，在Dashboard或JSON中可以看到：

```json
{
  "anti_shell_report": {
    "overall_status": "6/6 layers passed ✅",
    "layer_1_structure_validation": {
      "name": "结构强校验",
      "checks": 20,
      "passed": 20,
      "failed": 0,
      "status": "✅",
      "description": "所有文件存在且内容充实"
    },
    "layer_2_placeholder_detection": {
      "name": "占位词拦截",
      "checks": 2,
      "passed": 2,
      "failed": 0,
      "status": "✅",
      "description": "无TODO/TBD/待定等占位词"
    },
    "layer_3_sample_data_validation": {
      "name": "样例数据验证",
      "checks": 5,
      "passed": 5,
      "failed": 0,
      "status": "✅",
      "description": "无example@example.com等示例数据"
    },
    "layer_4_executability_check": {
      "name": "可执行性验证",
      "checks": 4,
      "passed": 4,
      "failed": 0,
      "status": "✅",
      "description": "所有脚本语法正确且可执行"
    },
    "layer_5_test_report_validation": {
      "name": "测试报告验证",
      "checks": 3,
      "passed": 3,
      "failed": 0,
      "status": "✅",
      "description": "测试存在、通过且覆盖率87.5%"
    },
    "layer_6_evidence_traceability": {
      "name": "证据留痕",
      "checks": 6,
      "passed": 6,
      "failed": 0,
      "status": "✅",
      "description": "所有Phase证据完整且可追溯"
    }
  }
}
```

---

## 常见问题FAQ

### Q1: 验证脚本在哪里？

**A:**
```bash
# 主验证脚本
bash scripts/workflow_validator.sh

# 分阶段检查脚本
bash scripts/static_checks.sh        # Phase 3检查
bash scripts/pre_merge_audit.sh      # Phase 4检查
bash scripts/check_version_consistency.sh  # 版本一致性

# Dashboard
bash scripts/serve_progress.sh       # 启动可视化Dashboard
```

### Q2: 为什么总步数是75步而不是固定数字？

**A:** 因为有些检查是**条件性**的（如适用则检查）

**示例**：
- P1_S109: API接口定义（只有API项目才检查）
- P3_S306-S307: BDD测试（只有使用BDD的项目才检查）
- P5_S504-S506: Git Tag相关（只有打tag的项目才检查）

**实际统计**：
- 固定检查：60步（必定执行）
- 条件检查：15步（根据项目类型）
- **总计最多**：75步

### Q3: 完成度<100%但显示"完成"？

**A:** 因为有些项是**可选的**（nice-to-have）

**规则**：
- **必须项（Must）**: 不完成=未完成
- **可选项（Should）**: 不完成=仍然算完成，但有改进空间

**示例**：
```
Phase 1: 90% (9/10)
  ✅ PLAN.md（必须）
  ✅ Agent策略（必须）
  ✅ 任务分解（必须）
  ✅ 验收标准（必须）
  ❌ 时间估计（可选）← 不影响"完成"判断

结论：Phase 1完成 ✅（因为所有必须项都完成）
```

### Q4: 证据文件能删除吗？

**A:** 证据文件在`.evidence/`目录

```bash
.evidence/
├── last_run.json          # 最近一次验证结果
├── p2/timestamp.yml       # Phase 0证据
├── p1/timestamp.yml       # Phase 1证据
├── p2/timestamp.yml       # Phase 2证据
├── p3/timestamp.yml       # Phase 3证据
├── p4/timestamp.yml       # Phase 4证据
├── p5/timestamp.yml       # Phase 5证据
└── history/               # 历史记录（30天自动清理）
```

**能删除吗？**
- ❌ 不建议删除`last_run.json`（会影响验证）
- ✅ 可以删除历史文件（30天前的）
- ✅ `.evidence/`本身被`.gitignore`忽略（不会提交到Git）

**如果误删了怎么办？**
```bash
# 重新运行validator即可重新生成
bash scripts/workflow_validator.sh
```

### Q5: 验证通过了，但实际有bug怎么办？

**A:** 验证系统不是银弹，它只能检测**流程完整性**，不能检测**业务逻辑正确性**

**验证系统能检测**：
- ✅ 文件是否存在
- ✅ 测试是否运行
- ✅ 代码是否通过静态检查
- ✅ 文档是否更新

**验证系统不能检测**：
- ❌ 业务逻辑是否正确（例如：登录密码验证有漏洞）
- ❌ 用户体验是否好（例如：按钮位置不合理）
- ❌ 性能是否达标（例如：查询慢）

**解决方案**：
1. **提高测试质量** - 写更多边界测试、集成测试
2. **人工审查** - Phase 4的代码审查很重要
3. **生产监控** - Phase 5的监控能发现实际问题

### Q6: 多人协作时，证据文件冲突怎么办？

**A:** `.evidence/`不应该提交到Git

**正确做法**：
```bash
# .gitignore中应该有：
.evidence/
!.evidence/.gitkeep

# 如果需要分享证据：
# 方法1：复制到其他目录
cp .evidence/last_run.json ./evidence_reports/report_$(date +%Y%m%d).json
git add evidence_reports/
git commit -m "chore: add validation evidence"

# 方法2：CI中自动生成
# （在CI中运行validator，结果作为PR comment）
```

### Q7: 验证需要多长时间？

**A:** 取决于项目大小和检查项数量

| 项目规模 | 文件数量 | 验证时间 | 说明 |
|---------|---------|---------|------|
| 小型 | <50个文件 | 5-10秒 | 个人项目 |
| 中型 | 50-200个文件 | 10-20秒 | 小团队项目 |
| 大型 | >200个文件 | 20-30秒 | 企业级项目 |

**Claude Enhancer项目**：
- 文件数：~200个
- 验证时间：7-10秒
- 包含：75步检查 + 6层防空壳

**优化建议**：
- 使用缓存（`.evidence/cache/`）
- 只验证变更的Phase（`--phase P3`参数）

### Q8: 可以自定义验证规则吗？

**A:** 可以！通过配置文件

```yaml
# spec/workflow.spec.yaml

# 修改阈值
config:
  thresholds:
    min_completion_rate: 80  # 改为90%
    max_execution_time: 10   # 改为5秒

# 添加自定义检查
custom_validations:
  - id: "CUSTOM_001"
    name: "API版本检查"
    phase: "P1"
    validation:
      type: "grep"
      file: "api/openapi.yaml"
      pattern: 'version: "v1.0"'
    severity: "high"

# 修改占位词黑名单
config:
  placeholder_keywords:
    - "TODO"
    - "FIXME"
    - "待定"
    - "YOUR_CUSTOM_PLACEHOLDER"  # 添加自定义占位词
```

### Q9: Dashboard不显示怎么办？

**A:** 检查以下几点：

```bash
# 1. 检查端口是否被占用
lsof -i :8999
# 如果被占用，换个端口：
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh

# 2. 检查Dashboard文件是否存在
ls -lh tools/web/dashboard.html
# 应该显示HTML文件

# 3. 检查Python是否安装
python3 --version
# 应该≥3.8

# 4. 手动访问API
curl http://localhost:8999/api/progress
# 应该返回JSON数据

# 5. 查看服务器日志
# 如果有错误，会在终端显示
```

### Q10: 如何在CI/CD中集成验证？

**A:** 添加到GitHub Actions workflow

```yaml
# .github/workflows/validation.yml
name: Workflow Validation

on:
  pull_request:
  push:
    branches: [main, master]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Workflow Validator
        run: |
          bash scripts/workflow_validator.sh

      - name: Check Completion Rate
        run: |
          RATE=$(jq -r '.overall_progress' .evidence/last_run.json)
          if [ "$RATE" -lt 80 ]; then
            echo "❌ Completion rate ${RATE}% < 80%"
            exit 1
          fi
          echo "✅ Completion rate ${RATE}% ≥ 80%"

      - name: Upload Evidence
        uses: actions/upload-artifact@v3
        with:
          name: validation-evidence
          path: .evidence/last_run.json

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const evidence = JSON.parse(fs.readFileSync('.evidence/last_run.json'));
            const comment = `## 🔍 Workflow Validation Report

            **Overall Completion**: ${evidence.overall_progress}%

            | Phase | Progress | Status |
            |-------|----------|--------|
            ${Object.values(evidence.phases).map(p =>
              `| ${p.name} | ${p.progress}% | ${p.status} |`
            ).join('\n')}

            **Anti-Shell Layers**: ${evidence.anti_shell_report.overall_status}

            ${evidence.merge_ready ? '✅ Ready to merge' : '⚠️ Not ready to merge'}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## 最佳实践

### 1. 开发过程中持续验证

**不要**：
```
开发3天 → 最后验证 → 发现一堆问题 → 花2天修复
```

**要做**：
```
Phase 2 → 验证 → Phase 1 → 验证 → Phase 2 → 验证 ...
每个Phase完成后立即验证，发现问题立即修复
```

**好处**：
- 问题早发现，修复成本低
- 避免积累技术债
- 心里有底，知道进度

### 2. 在PR描述中附加验证结果

**模板**：
```markdown
## 🔍 Workflow Validation Report

bash scripts/workflow_validator.sh

**Results**:
- Phase 2-4: ✅ 100% (29/29)
- Phase 3: ✅ 100% (8/8)
- Phase 4: ✅ 95% (9/10)
- Phase 5: ✅ 100% (10/10)
- **Overall: 98%** ✅

**Anti-Shell Layers**: 6/6 passed ✅
**Quality Gates**:
  - Gate 1 (P3): ✅ Passed
  - Gate 2 (P4): ✅ Passed

**Evidence**: Attached .evidence/last_run.json

**Merge Ready**: ✅ Yes (score ≥ 80%)
```

### 3. 设置Git Hook自动验证

```bash
# .git/hooks/pre-push
#!/bin/bash
echo "🔍 Running workflow validation..."
bash scripts/workflow_validator.sh

COMPLETION=$(jq -r '.overall_progress' .evidence/last_run.json)

if [ "$COMPLETION" -lt 80 ]; then
  echo "❌ Completion ${COMPLETION}% < 80%, blocking push"
  echo "Please fix failed checks first"
  exit 1
fi

echo "✅ Validation passed (${COMPLETION}%), pushing..."
exit 0
```

### 4. 用Dashboard追踪进度

```bash
# 启动Dashboard（在后台运行）
bash scripts/serve_progress.sh &

# 在浏览器中打开
open http://localhost:8999

# 开发过程中随时刷新查看进度
# 完成一个Phase → 刷新Dashboard → 看到进度条增长
```

### 5. 团队内制定完成度标准

**建议标准**：
```
个人开发：
- 60%可以提交到feature分支
- 80%可以发起PR
- 95%可以合并到main

团队开发：
- 70%可以提交到feature分支
- 85%可以发起PR
- 95%可以合并到main
- 100%才能发布到生产环境

质量门禁（强制）：
- 质量门禁1（P3）：必须100%通过
- 质量门禁2（P4）：必须100%通过
```

---

## 总结：核心要点

### 3个核心原则

1. **"完成"必须有证据** - 不是AI说完成就完成，要有数据证明
2. **80%是合格线** - 低于80%不要说"完成"
3. **持续验证，不要积累** - 每个Phase结束立即验证

### 5个关键命令

```bash
# 1. 运行验证（最重要）
bash scripts/workflow_validator.sh

# 2. 查看证据
cat .evidence/last_run.json | jq '.'

# 3. 查看完成度
jq -r '.overall_progress' .evidence/last_run.json

# 4. 查看失败项
jq -r '.phases[] | select(.failed > 0) | "\(.name): \(.failed) failed"' .evidence/last_run.json

# 5. 启动Dashboard
bash scripts/serve_progress.sh
```

### 工作流集成（完整流程）

```
┌─────────────────────────────────────────────┐
│ 1. 用户需求（Discussion Mode）              │
│    "实现用户认证"                            │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 2. Phase 1: 分支检查                       │
│    git checkout -b feature/user-auth        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 3. Phase 2: 创建验收清单                    │
│    → 运行验证 ✅ 100% (10/10)                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 4. Phase 1: 创建PLAN.md                     │
│    → 运行验证 ✅ 100% (10/10)                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 5. Phase 2: 编码实现                        │
│    → 运行验证 ✅ 100% (9/9)                  │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 6. Phase 3: 测试 + 静态检查                 │
│    bash scripts/static_checks.sh            │
│    → 运行验证 ✅ 100% (8/8)                  │
│    → 质量门禁1 ✅ 通过                       │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 7. Phase 4: 代码审查 + 审计                 │
│    bash scripts/pre_merge_audit.sh          │
│    → 运行验证 ✅ 100% (10/10)                │
│    → 质量门禁2 ✅ 通过                       │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 8. Phase 5: 文档更新 + 发布准备             │
│    → 运行验证 ✅ 100% (10/10)                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 9. 最终验证                                 │
│    bash scripts/workflow_validator.sh       │
│    检查：overall_progress ≥ 80%             │
│    检查：防空壳机制 6/6 通过                 │
│    检查：质量门禁 2/2 通过                   │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ 10. 合并到main（如果≥80%）                  │
│     附加证据文件到PR                         │
│     Dashboard截图（可选）                    │
└─────────────────────────────────────────────┘
```

---

## 附录：完整检查项列表

### Phase 1: Branch Check (5 steps)

- [ ] S-101: Git仓库有效性检查
- [ ] S-102: 当前分支检测
- [ ] S-103: 主分支保护检查 [CRITICAL]
- [ ] S-104: 分支命名规范检查
- [ ] S-105: Hook完整性检查

### Phase 2: Discovery (10 steps)

- [ ] S001: P0文档存在性 [CRITICAL]
- [ ] S002: 问题陈述定义 [CRITICAL]
- [ ] S003: 可行性分析 [CRITICAL]
- [ ] S004: 验收清单存在性 [CRITICAL]
- [ ] S005: 验收清单项数量（≥5）
- [ ] S006: 成功标准定义
- [ ] S007: 占位词检测 [防空壳]
- [ ] S008: 空章节检测
- [ ] S009: P0证据目录
- [ ] S010: P0时间戳记录 [防空壳]

### Phase 1: Planning & Architecture (10 steps)

- [ ] S101: PLAN.md存在性 [CRITICAL]
- [ ] S102: 任务分解章节
- [ ] S103: 任务描述非空 [防空壳]
- [ ] S104: 架构设计章节
- [ ] S105: 技术栈定义
- [ ] S106: Agent策略定义
- [ ] S107: 目录结构文档
- [ ] S108: 关键目录创建
- [ ] S109: API接口定义（如适用）
- [ ] S110: P1证据记录 [防空壳]

### Phase 2: Implementation (9 steps)

- [ ] S201: Git提交存在性 [CRITICAL]
- [ ] S202: Commit规范检查
- [ ] S203: 代码文件修改 [防空壳]
- [ ] S204: Shell语法预检查 [防空壳]
- [ ] S205: 敏感信息检测 [CRITICAL]
- [ ] S206: 大文件检测
- [ ] S207: 注释存在性（≥10%）
- [ ] S208: README更新（重大变更）
- [ ] S209: P2证据记录 [防空壳]

### Phase 3: Testing [质量门禁1] (8 steps)

- [ ] S301: 静态检查脚本存在 [CRITICAL]
- [ ] S302: 静态检查执行通过 [CRITICAL, BLOCKING]
- [ ] S303: 测试文件存在性 [防空壳]
- [ ] S304: 测试执行通过 [防空壳]
- [ ] S305: 测试覆盖率（≥70%）[防空壳]
- [ ] S306: BDD场景存在性
- [ ] S307: BDD测试执行
- [ ] S308: P3证据记录 [防空壳]

### Phase 4: Review [质量门禁2] (10 steps)

- [ ] S401: 审计脚本存在 [CRITICAL]
- [ ] S402: 合并前审计通过 [CRITICAL, BLOCKING]
- [ ] S403: REVIEW.md存在性 [CRITICAL]
- [ ] S404: 审查内容完整性
- [ ] S405: 审查发现记录
- [ ] S406: 版本一致性脚本存在 [CRITICAL]
- [ ] S407: 版本一致性验证 [CRITICAL, BLOCKING]
- [ ] S408: 遗留问题扫描（TODO/FIXME）
- [ ] S409: P0验收清单验证
- [ ] S410: P4证据记录 [防空壳]

### Phase 5: Release & Monitor (10 steps)

- [ ] S501: CHANGELOG更新
- [ ] S502: README最终检查
- [ ] S503: 文档链接有效性
- [ ] S504: Git Tag存在性
- [ ] S505: Tag格式验证（semver）
- [ ] S506: Release Notes
- [ ] S507: 健康检查脚本
- [ ] S508: SLO定义（如适用）
- [ ] S509: P0验收清单最终确认
- [ ] S510: P5证据记录 [防空壳]

### Global Validations (3 steps)

- [ ] G001: 根目录文档数量限制（≤7）
- [ ] G002: 临时文件检查（<10MB）
- [ ] G003: Git Hooks安装验证

---

**记住**：验证系统是你的"质量保镖"，它帮你确保工作真的"完成"了，而不是"看起来完成了"。

**用证据说话，不用猜测！** 🎯

---

*Claude Enhancer 6.5.1 - 75步验证系统*
*Last Updated: 2025-10-17*
