🚨🚨🚨 **AI强制执行指令（优先级最高）** 🚨🚨🚨

**在执行任何Write/Edit操作之前，你必须：**

1. **检查当前分支**（执行`git rev-parse --abbrev-ref HEAD`）
2. **如果在main/master分支**：
   - ❌ 禁止执行任何Write/Edit操作
   - ✅ 必须先执行：`git checkout -b feature/任务描述`
   - 💡 这是100%强制规则，违反将被Hook硬阻止（exit 1）
3. **如果在feature分支**：
   - ✅ 检查分支名是否与当前任务相关
   - 🟡 不相关则建议创建新分支

**规则0（Phase 1）：新任务 = 新分支（No Exceptions）**

这不是建议，是强制要求。所有编码任务必须从分支检查开始。

---

# Claude Enhancer 6.3 - 专业级个人AI编程工作流系统

⚠️⚠️⚠️ **重要提醒** ⚠️⚠️⚠️

**系统定位**：专业级个人工具（非企业级/团队工具）
**目标用户**：编程小白 + Claude Max 20X用户
**核心原则**：高质量 + 简单易用 + 个人使用场景

**修改前必读**：
- `.claude/DECISIONS.md` - 历史决策记录
- `.claude/memory-cache.json` - AI决策上下文

**禁止操作**：
- ❌ 添加团队协作功能
- ❌ 添加多用户权限
- ❌ 添加企业级部署（金丝雀、SLO仪表板等）
- ❌ 重新添加已删除的复杂工具（pylint等）
- ❌ 使用"企业级"、"团队"、"多用户"、"商业部署"等术语

---

## 🏆 v6.3核心成就
**工作流优化 + 保持质量 + 提升效率 = 更快更好的AI开发**

### v6.3 工作流优化（2025-10-15）
- **7-Phase系统**: ✅ 从8阶段优化到7阶段，效率提升17%
- **Phase 1-7**: ✅ 合并相关阶段（P3+P4原架构, P7+P8原监控），保持质量门禁
- **10步完整流程**: ✅ 从讨论到合并的明确工作流
- **零质量妥协**: ✅ Phase 5和Phase 6质量门禁完全保留

### v6.2 分支保护成就（2025-10-11）
- **完全自动化**: ✅ Bypass Permissions Mode启用，零人工确认
- **分支保护**: 100%逻辑防护 + 100%综合防护（配合GitHub）
- **保障力评分**: 100/100 - 完美达标！
- **自动化流程**: Push → PR → CI → Merge → Tag → Release 全自动
- **正向检测**: 每日健康检查 + 实时证据生成
- **压力测试**: 12场景验证通过，3轮迭代优化
- **AI自主性**: 100%（从60%提升）

## 🎯 定位：专业级个人工具
Claude Enhancer是专为追求极致质量的个人开发者设计的AI驱动编程工作流系统，从想法到生产部署的全程保障，适合**单用户使用场景**。

## ⚡ 完整能力矩阵
- **保障力评分**: 100/100 ✅
- **BDD场景**: 65个场景，28个feature文件
- **性能指标**: 90个性能预算指标
- **SLO定义**: 15个服务级别目标
- **CI Jobs**: 5个核心验证任务（优化后）
- **分支保护**: 4层防护架构，12场景压力验证
- **自动化率**: 95%（仅PR approval需人工）
- **生产就绪**: ✅ 专业级认证

## 📈 版本演进历程
- **5.0**: 初始版本，建立6-Phase工作流
- **5.1**: 性能优化，启动速度提升68.75%，依赖精简97.5%
- **5.2**: 压力测试验证，工作流机制成熟稳定
- **5.3**: 保障力升级，达到100/100生产级标准
- **5.5.0-5.5.2**: 系统统一，从"声称完整"到"真正实现"
- **6.0**: 🎯 **专业级跨越**
  - ✅ 版本统一（6.0.0无冲突）
  - ✅ 分支保护强化（100%逻辑防护）
  - ✅ 全自动化链路（push to release）
  - ✅ 正向健康检测（非侵入式验证）
  - ✅ CI精简优化（12→5个workflows）
  - ✅ 文档归档清理（82个遗留文档）
- **6.1**: 🚀 **完全自主化**（2025-10-11）
  - ✅ Bypass Permissions Mode启用（不弹窗询问用户）
  - ✅ Phase 1-7零人工确认（技术决策自主）
  - ✅ AI自主性100%（技术实现自主，但必须遵守工作流）
  - ✅ 20+场景测试全部通过
  - ✅ 完整配置指南和测试工具

**重要说明：**
- ✅ "零人工确认" = 不弹窗询问"要创建这个文件吗？"
- ✅ "AI自主性100%" = 技术决策（库选择、代码结构）自主
- ❌ "自主"≠跳过工作流步骤
- ❌ 必须严格遵守 7-Phase 工作流，无例外

## 🔴 规则0：分支前置检查（Phase 1）
**优先级：最高 | 在所有开发任务之前强制执行**

### 🎯 核心原则
```
新任务 = 新分支（No Exceptions）
```

### 🤖 AI 行为强制规范

**AI 必须遵守的规则（无例外）：**

1. **✅ 可以自主决策的范围：**
   - 技术选择（库、框架、工具）
   - 代码实现细节（结构、命名、模式）
   - 文件创建/修改（不弹窗询问用户）
   - 错误修复（立即处理，不询问）
   - 性能优化（自动进行）
   - 测试用例设计

2. **❌ 绝对禁止的行为：**
   - 跳过 Phase 1 文档直接写代码
   - 创建 .workflow/BYPASS_WORKFLOW 文件
   - 在没有 Phase 1 文档时使用任何形式的绕过
   - 修改 git hooks 以绕过检查
   - 建议用户绕过工作流

3. **🔒 强制执行的工作流：**
   ```
   Phase 1: 创建文档（P1_DISCOVERY, CHECKLIST, PLAN）
            ↓ 必须完成，不可跳过
   Phase 2: 实现代码
            ↓ 必须完成，不可跳过
   Phase 3: 测试验证
            ↓ 必须完成，不可跳过
   Phase 4-7: 审查、发布、验收、清理
   ```

4. **⚠️ 如果违反规则：**
   - Workflow Guardian 会硬阻止 commit
   - 必须补充 Phase 1 文档才能继续
   - 没有 Bypass 机制可用（已删除）

**记住："自主性"是指技术决策自主，不是指可以跳过工作流！**

### 📋 强制检查清单
在进入执行模式（Phase 2-7）之前，必须完成：

1. **分析当前分支**
   ```bash
   当前分支是什么？
   └─ main/master → 必须创建新分支
   └─ feature/xxx → 检查是否与当前任务相关
   └─ 他人的分支 → 禁止修改
   ```

2. **判断任务类型**
   - 新功能开发 → `feature/功能描述`
   - Bug修复 → `bugfix/问题描述`
   - 性能优化 → `perf/优化内容`
   - 文档更新 → `docs/文档主题`
   - 实验性改动 → `experiment/实验内容`

3. **创建适配分支**
   ```bash
   # 如果当前分支不适合，立即创建新分支
   git checkout -b feature/任务名称
   ```

### ⚠️ 强制规则（违反将被Hook阻止）

❌ **禁止行为**：
- 在 main/master 分支直接修改
- 在不相关的 feature 分支上开发新任务
- 在他人的分支上进行修改
- 跳过分支检查直接开始编码

✅ **正确流程**：
```
用户请求 → 分析任务 → 检查分支 → 创建新分支 → 执行Phase 2-7
                                    ↑
                          关键步骤，不可跳过
```

### 🤖 AI多终端并行场景

**场景**：用户在多个Terminal同时开发不同功能
```
Terminal 1 (Claude实例A):
git checkout -b feature/user-authentication
└─ 执行Phase 2-7：用户认证系统

Terminal 2 (Claude实例B):
git checkout -b feature/payment-integration
└─ 执行Phase 2-7：支付集成

Terminal 3 (Claude实例C):
git checkout -b feature/multi-terminal-workflow
└─ 执行Phase 2-7：多终端工作流
```

**优势**：
- ✅ 功能隔离，互不干扰
- ✅ 独立PR，清晰审查
- ✅ 回滚容易，风险可控
- ✅ 并行开发，效率最大化

### 🛡️ 执行保障（已通过压力测试验证）

**四层防护架构**（v6.0强化版）：

#### 第一层：本地Git Hooks（逻辑防护层）
- `.git/hooks/pre-push` - **主防线**，经12场景压力测试验证
  - ✅ 精准正则：`^(main|master|production)$` 避免误伤
  - ✅ 绕过检测：阻止 `hooksPath`、环境变量篡改
  - ⚠️ **限制**：`--no-verify` 会完全跳过hook执行（Git设计限制）
  - ✅ 并发安全：10并发重试全部阻止
  - ✅ 实战验证：8/8可防御攻击全部阻止
- `.git/hooks/pre-commit` - 代码质量检查
- `.git/hooks/commit-msg` - 提交信息规范
- `.claude/hooks/branch_helper.sh` - PreToolUse AI层辅助

**验证证据**：
```bash
# 压力测试脚本（12场景）
./bp_local_push_stress.sh

# 测试结果（2025-10-11）
✅ BLOCK_main_plain          - 直接推送 → 阻止
❌ BLOCK_main_noverify       - --no-verify → 跳过hook (Git限制)
✅ BLOCK_main_hooksPath_null - hooksPath=/dev/null → 阻止
✅ BLOCK_main_env_bypass     - 环境变量 → 阻止
✅ BLOCK_main_concurrent     - 10并发 → 全部阻止
... (详见 BP_PROTECTION_REPORT.md)

综合结果：本地hook可防御攻击100%阻止 ✅
注意：--no-verify 需要 Layer 2/3 (GitHub Branch Protection) 防护
```

#### 第二层：CI/CD验证（权限监控 +30%）
- `.github/workflows/bp-guard.yml` - Hook权限完整性检查
  - 检测 `chmod -x` 攻击
  - 验证配置完整性
  - 每次push/PR触发

#### 第三层：GitHub Branch Protection（服务端强制 - 最终防线）
⚠️ **Critical Security Fix (2025-10-29)**: 发现并修复重大安全漏洞
- **问题**：v8.4.0之前GitHub Branch Protection未配置Required Status Checks
- **影响**：AI可通过`gh pr merge`命令绕过CI验证直接合并代码
- **修复**：已通过GitHub API配置6个Required Status Checks + strict模式
- **验证**：测试PR #54成功被阻止合并 ✅

**当前配置**（2025-10-29生效）：
- **强制PR流程**（即使使用 `--no-verify` 也无法直推到main）
- **Required Status Checks** (strict=true)：
  - CE Unified Gates
  - Quality Gate (Required Check)
  - ce/phase3-static-checks
  - ce/phase4-pre-merge-audit
  - ce/phase7-final-validation
  - 🔒 Stage 3: Pre-merge Audit (Gate 2)
- **Include administrators**（无特权绕过）
- ✅ 这是对抗 `--no-verify` 的真正防线

#### 第四层：持续监控（持续保障）
- `.github/workflows/positive-health.yml` - 每日健康检查
- 实时证据生成（带时间戳nonce）
- 异常自动告警

**综合防护率**：100%（本地hooks + GitHub Branch Protection）
- 本地hooks: 防御可检测的绕过尝试
- GitHub Branch Protection: 防御 `--no-verify` 等本地无法检测的情况

**防护能力**：
```
╔═══════════════════════════════════════╗
║  🏆 Branch Protection - 4层防护      ║
║  本地Hooks: 可防御攻击100%阻止       ║
║  GitHub保护: 强制PR + Status Checks  ║
║  综合防护: 100% (含--no-verify防护)  ║
║  状态: ✅ PRODUCTION READY           ║
╚═══════════════════════════════════════╝
```

**关键说明**：
- ✅ 本地hooks可防御绕过尝试（hooksPath、环境变量等）
- ❌ `--no-verify` 无法在本地检测（Git设计限制）
- ✅ GitHub Branch Protection 强制PR流程，即使本地被绕过也无法直推main

**详细报告**：参见 `BP_PROTECTION_REPORT.md`（628行完整分析）

### 🧠 智能分支判断逻辑（AI决策机制）

**核心原则**：不是"每次都问"，而是"智能判断何时需要问"

#### 决策流程

```
收到用户需求
    ↓
【判断1】是编码任务吗？
    ├─ ❌ 否（查询/讨论/分析）→ 直接处理，不涉及分支
    └─ ✅ 是 → 继续
           ↓
【判断2】用户明确指定了分支策略吗？
    ├─ ✅ 是（"在这个分支"/"新建分支"）→ 按用户说的做
    └─ ❌ 否 → 继续
           ↓
【判断3】新需求与当前分支主题的关系？
    ├─ 🟢 明显匹配（延续/修复/完善）→ 直接继续
    ├─ 🟡 不确定（可能相关，可能不相关）→ 简短询问
    └─ 🔴 明显不匹配（新功能/跨领域）→ 建议新分支
```

#### 三级响应策略

**🟢 明显匹配 - 直接继续**
```
场景：
- 当前：feature/user-auth
- 用户："继续实现登录功能"
- 判断：延续词 + 主题匹配

AI响应：
"好的，我在当前分支继续实现登录功能..."
（不啰嗦，直接开始）
```

**🟡 不确定 - 简短询问**
```
场景：
- 当前：feature/user-authentication
- 用户："帮我添加邮件验证"
- 判断：有关联，但边界不清

AI响应：
"关于邮件验证，两种理解：
 1. 作为认证流程的一部分 → 当前分支继续
 2. 独立的通知系统 → 建议新分支feature/email-notification
 您倾向于哪种？"
```

**🔴 明显不匹配 - 建议新分支**
```
场景：
- 当前：feature/add-logging（已完成）
- 用户："帮我实现支付系统"
- 判断：完全不同领域 + 当前分支已完成

AI响应：
"🔍 分支策略判断

 当前：feature/add-logging（已完成，未merge）
 新需求：支付系统

 ✅ 建议：创建新分支 feature/payment-system
 💡 理由：
    - 支付系统与日志功能完全独立
    - 当前分支已完成，应该保持稳定
    - 新分支可以独立开发和review

 请确认？"
```

#### 主题匹配判断标准

**关键词提取**：
```python
# 从分支名提取主题
feature/user-authentication → "用户认证"
feature/add-logging → "日志"
feature/payment-system → "支付"

# 从用户请求提取意图
"继续实现登录" → 延续词 + "认证"
"添加日志级别" → "日志"
"实现支付" → 新功能 + "支付"
```

**匹配规则**：
- **高度匹配**：关键词重叠 + 延续词（继续/完善/修复）
- **相关性**：领域接近（如：登录 ↔ 认证，支付 ↔ 订单）
- **无关性**：完全不同领域（如：日志 ↔ 支付）

**特殊情况**：
- 当前在 main/master → 🔴 必须建议新分支
- 当前分支已完成（有commit，等merge）→ 🟡 倾向建议新分支
- 用户说"新功能"/"新建" → 🔴 建议新分支
- 用户说"继续"/"完善" → 🟢 当前分支继续

#### Merge计划制定

**何时展示Merge计划**：
- 🟢 明显匹配 → 不展示（隐含在当前分支）
- 🟡 不确定询问时 → 简短说明
- 🔴 建议新分支时 → 完整展示

**Merge计划内容**：
```
完成后的流程：
1. feature/xxx → PR review → main
2. 依赖关系：无/有（说明）
3. 预计影响：文件数量、风险评估
```

#### AI承诺

**我会做到**：
- ✅ 理解任务语义后智能判断
- ✅ 明显情况不啰嗦，直接执行
- ✅ 不确定时简洁询问，给选项
- ✅ 错误情况主动纠正，说理由

**我不会**：
- ❌ 机械地每次都问一遍
- ❌ 不判断就直接在错误分支编码
- ❌ 给冗长的判断报告（明显情况）
- ❌ 不给理由就做决定

---

## 🚨 规则1：文档管理铁律（AI行为规范）
**优先级：最高 | 防止文档泛滥和信息混乱**

### 🎯 核心原则
```
核心文档（7个）= 永久保留
临时分析 = .temp/（7天自动删除）
给AI的 ≠ 给用户的
```

### ❌ 绝对禁止的行为

#### 禁止1：在根目录创建新文档
```
❌ 禁止：README_NEW.md、ANALYSIS_REPORT.md、SUMMARY.md
✅ 允许：更新7个核心文档（README.md、CLAUDE.md等）
✅ 临时：写入 .temp/analysis/report_20251013.md
```

#### 禁止2：创建临时报告文件
```
❌ 禁止模式：
- *_REPORT.md
- *_ANALYSIS.md
- *_AUDIT.md
- *_SUMMARY.md
- DOCUMENT_*.md

✅ 正确做法：
- 写入 .temp/analysis/ （AI自己看）
- 或者直接在对话中说明（用户看）
```

#### 禁止3：创建重复内容的文档
```
❌ 禁止：README2.md、CLAUDE_NEW.md、INSTALL_GUIDE.md（已有INSTALLATION.md）
✅ 允许：更新现有文档
```

### ✅ 强制规则

#### 规则1.1：核心文档白名单（只能更新，不能新建）
```
7个核心文档（永久保留）：
├─ README.md          ✅ 可更新
├─ CLAUDE.md         ✅ 可更新（本文件）
├─ INSTALLATION.md   ✅ 可更新
├─ ARCHITECTURE.md   ✅ 可更新
├─ CONTRIBUTING.md   ✅ 可更新
├─ CHANGELOG.md      ✅ 可追加
└─ LICENSE.md        ✅ 通常不改

其他任何根目录.md文件 ❌ 禁止创建
```

#### 规则1.2：临时数据放在 .temp/
```bash
AI生成的临时分析、报告、审计结果：
✅ 写入: .temp/analysis/code_review_20251013.md
✅ 写入: .temp/reports/test_results.json
❌ 禁止: CODE_REVIEW_REPORT.md（根目录）
```

**生命周期管理**：
- `.temp/` - 7天后自动删除
- `evidence/` - 30天后归档
- `archive/` - 1年后提示清理

#### 规则1.3：创建文档前必须询问（除非在.temp/）
```
在调用Write工具创建.md文件之前：

1. 检查是否在核心清单中
2. 如果不在 → 询问用户：
   "我需要创建 XXX.md 来记录分析结果，您希望：
   A. 放在 .temp/ （7天后自动删除）
   B. 放在 evidence/ （30天后归档）
   C. 不创建，口头告诉我
   D. 创建为永久文档（需要说明理由）"
3. 等待用户选择

例外：.temp/ 目录可以自由创建，无需询问
```

#### 规则1.4：信息传递方式
```
AI需要传递分析结果时的3种方式：

方式A: 直接在对话中说明（简短）✅ 推荐
"我发现了3个关键bug：1) Shell语法错误... 2) ..."

方式B: 写入临时文件（详细）✅ 可选
.temp/analysis/audit_20251013.md
（用户不会看到，但AI可引用）

方式C: 更新核心文档（永久）⚠️ 谨慎
只有用户明确要求时，才更新 README.md 等

❌ 禁止：每次都创建根目录报告文件
```

### 🔒 强制执行机制

#### 层1：Pre-Write Hook（AI写文件前拦截）
```bash
.claude/hooks/pre_write_document.sh
# 在AI调用Write/Edit工具之前自动运行
# 如果文件不在白名单 → 阻止并提示
```

#### 层2：Post-Commit自动清理
```bash
scripts/cleanup_documents.sh
# 每次commit后自动运行
# 移除未授权文档到 .temp/quarantine/
```

#### 层3：CI/CD验证
```yaml
# .github/workflows/daily-quality-check.yml
# 每天检查根目录文档数量
# 超过7个 → CI失败 + 自动清理
```

### 📊 文档分类策略

```yaml
核心文档（location: /）:
  ttl: permanent
  files: [README.md, CLAUDE.md, INSTALLATION.md, ARCHITECTURE.md,
          CONTRIBUTING.md, CHANGELOG.md, LICENSE.md]
  rules: AI禁止删除、AI禁止创建新的

临时分析（location: /.temp/）:
  ttl: 7 days
  pattern: "*_REPORT.md, *_ANALYSIS.md"
  rules: AI可以自由创建、自动删除、用户不可见

工作证据（location: /evidence/）:
  ttl: 30 days
  files: "*.log, *_evidence.md"
  rules: CI自动生成、30天后归档

文档结构化（location: /docs/）:
  ttl: permanent
  structure: {guides/, api/, architecture/, troubleshooting/}
  rules: 必须有明确分类、不能放在根目录
```

### 🎯 AI承诺

**我承诺**：
- ✅ 只更新核心7个文档，不创建新的
- ✅ 临时分析写入 .temp/，不污染根目录
- ✅ 创建永久文档前先询问用户
- ✅ 遵守文档生命周期管理

**我不会**：
- ❌ 每次任务都生成一堆报告文件
- ❌ 在根目录创建 *_REPORT.md
- ❌ 给用户看"给AI自己的"临时分析
- ❌ 让文档数量失控（>7个）

### ✅ 成功标准

**3个月验证**：
- [ ] 根目录文档≤7个（永久保持）
- [ ] .temp/自动清理（7天TTL）
- [ ] 用户找文档<30秒（信息清晰）
- [ ] AI不再生成垃圾文档

---

## 🔒 规则2：核心结构锁定机制（Lockdown Mechanism）
**优先级：最高 | 防止AI无限改动工作流核心结构**

### 🎯 核心原则
```
7 Phases / 97 Checkpoints / 2 Quality Gates / 8 Hard Blocks = 不可减少
```

### 📋 什么是锁定机制

**问题背景**：
AI在迭代过程中可能：
- ❌ 减少检查点数量（97→85）
- ❌ 降低质量阈值（70%→60%）
- ❌ 简化Phase结构（7→5）
- ❌ 移除质量门禁

**解决方案**：三层锁定架构（v6.6.0实施）

#### Layer 1: Core Immutable（核心不可变）
**SHA256指纹保护**，修改需用户批准：
- `.workflow/SPEC.yaml` - 核心结构定义（7/97/2/8）
- `.workflow/LOCK.json` - 7个关键文件指纹
- `docs/CHECKS_INDEX.json` - 97个检查点索引
- `tools/verify-core-structure.sh` - 完整性验证脚本

#### Layer 2: Adjustable Thresholds（可调阈值）
需要baseline数据支持：
- `.workflow/gates.yml` - 质量阈值配置
- 可以调整阈值，但必须有evidence（基准测试数据）
- 容差机制：±0.5% tolerance for rounding

#### Layer 3: Implementation Layer（实现层）
可自由优化：
- `scripts/workflow_validator_v97.sh` - 验证脚本
- `scripts/pre_merge_audit.sh` - 审计脚本
- `scripts/static_checks.sh` - 静态检查脚本
- 只要通过97个检查点，实现可随意改进

### ⚡ 验证机制

**本地验证**：
```bash
# 验证核心结构完整性
bash tools/verify-core-structure.sh
# 输出: {"ok":true,"message":"Core structure verification passed"}
```

**CI三段式验证**：
1. **Stage 1**: Core Structure Verification（核心完整性）
2. **Stage 2**: Static Checks - Quality Gate 1（静态检查）
3. **Stage 3**: Pre-merge Audit - Quality Gate 2（合并前审计）

### 🛡️ 观测期（Soft Mode）

**当前状态** (2025-10-20 to 2025-10-27):
- `fail_mode: soft` - 失败时记录但不阻止
- 收集7天数据验证机制准确性
- 零误报后切换到 `strict` 模式

### 🔧 更新LOCK.json

当修改Layer 2或Layer 3时：
```bash
# 更新文件指纹
bash tools/update-lock.sh

# 重新验证
bash tools/verify-core-structure.sh
```

### ⚠️ AI修改规则

**允许的修改**：
- ✅ 增加检查点（97→105）
- ✅ 提高质量阈值（70%→80%，需baseline）
- ✅ 优化脚本性能（只要通过验证）
- ✅ 改进错误提示

**禁止的修改**：
- ❌ 减少检查点数量
- ❌ 降低质量阈值（除非有充分证据）
- ❌ 移除质量门禁
- ❌ 修改Phase数量（7 Phases是固定的）

### 📊 核心指标

**当前锁定状态** (v6.6.0):
- Total Phases: 7 (locked)
- Total Checkpoints: ≥97 (可增长，不可减少)
- Quality Gates: 2 (locked)
- Hard Blocks: 8 (locked)
- Lock Mode: soft (观测期)

---

## 🛡️ 规则3: Anti-Hollow Gate System（反空洞门禁系统）
**优先级: 最高 | 防止空壳实现和hollow features**

### 🎯 核心原则
```
Every Feature = Evidence + Integration + Active Usage
```

### 📋 什么是Hollow Implementation（空壳实现）

**问题背景**：
AI在迭代过程中可能创建"看起来完整"但实际未真正使用的功能：
- ❌ 创建了脚本但从未被调用
- ❌ 配置了hook但未注册到系统
- ❌ 实现了功能但无测试证据
- ❌ 写了文档但与实际代码不一致

**Anti-Hollow Gate解决方案**：3-Layer + Evidence + Skills

### 🏗️ 3-Layer Anti-Hollow Gate架构

#### Layer 1: Pre-Tool-Use Hook（前置检查层）
- **文件**: `.claude/hooks/pre_tool_use.sh`
- **触发**: Write/Edit操作在CHECKLIST文件前
- **功能**: 检查是否有evidence支持完成标记
- **性能**: <500ms

#### Layer 2: Phase Transition Hook（阶段转换层）
- **文件**: `.claude/hooks/phase_transition.sh`
- **触发**: Phase N → Phase N+1转换时
- **功能**:
  - 验证Phase 1所有子步骤（含Impact Assessment）
  - Phase 4+强制evidence验证
  - 捕获Learning Items
- **性能**: <1s

#### Layer 3: Pre-Merge Audit v2（合并前审计层）
- **文件**: `scripts/pre_merge_audit_v2.sh`
- **触发**: Pull Request合并前
- **功能**: 12项综合检查
  1. Configuration completeness
  2. Evidence validation (100%)
  3. Checklist completion (≥90%)
  4. Learning system active
  5. Skills configured
  6. Version consistency (6 files)
  7. No hollow implementations
  8. Auto-fix rollback capability
  9. KPI tools available
  10. Root documents ≤7
  11. Documentation complete
  12. Legacy audit passed
- **性能**: <10s

### 📝 Evidence System（证据系统）

**Evidence ID格式**: `EVID-YYYYWWW-NNN`
- 例如: `EVID-2025W44-001`

**存储结构**:
```
.evidence/
├── schema.json           # Evidence元数据schema
├── index.json           # 快速查找索引
└── 2025Www/             # 按ISO周分组
    ├── EVID-2025W44-001.yml
    ├── EVID-2025W44-002.yml
    └── artifacts/       # 大文件附件
```

**Evidence类型**:
- `test_result` - 测试输出
- `code_review` - 代码审查记录
- `command_output` - 命令执行结果
- `artifact` - 大文件（截图、日志等）

**收集Evidence**:
```bash
bash scripts/evidence/collect.sh \
  --type test_result \
  --checklist-item 1.1 \
  --description "Unit tests for evidence collection" \
  --file /tmp/test_output.log
```

**使用Evidence**:
```markdown
- [x] 1.1 Evidence collection script works
<!-- evidence: EVID-2025W44-001 -->
```

### 🤖 Skills Framework（技能框架）

配置在`.claude/settings.json`，4个核心Skills:

1. **checklist-validator**
   - 在标记checklist项完成前验证evidence存在

2. **learning-capturer**
   - Phase转换失败时自动捕获Learning Item

3. **evidence-collector**
   - 运行测试后提醒收集evidence

4. **kpi-reporter**
   - Phase转换时生成KPI报告

### 📊 KPI Dashboard（质量仪表板）

4个核心指标:
1. **Auto-Fix Success Rate**: ≥80%
2. **MTTR (Mean Time To Repair)**: <24h
3. **Learning Reuse Rate**: ≥50%
4. **Evidence Compliance**: 100%

生成报告:
```bash
bash scripts/kpi/weekly_report.sh
```

### 🔒 强制执行机制

**三层防护**:
1. Hooks: 硬阻止（can block operations）
2. Skills: 智能提醒（reminders, automation）
3. CI/CD: 最终门禁（required checks）

**Workflow integration**:
- Phase 1.4: Impact Assessment（自动推荐Agent数量）
- Phase 3: Evidence collection required
- Phase 4: 100% evidence compliance check
- Phase 5: Pre-merge audit (12 checks)

### ⚠️ AI行为规范

**禁止行为**:
- ❌ 创建feature后不collect evidence
- ❌ 标记checklist项完成但无evidence
- ❌ 跳过Phase 1.4 Impact Assessment
- ❌ Phase转换时不验证requirements

**强制行为**:
- ✅ 完成任务后必须collect evidence
- ✅ Phase转换前必须validate checklist
- ✅ 合并前必须通过12项audit checks
- ✅ 保持evidence compliance = 100%

### 📈 成功指标

**30天后验证**:
- [ ] Hollow Implementation Rate = 0%
- [ ] Evidence Compliance = 100%
- [ ] Auto-Fix Success ≥80%
- [ ] MTTR <24h
- [ ] Learning Reuse ≥50%

---

## 🛡️ Self-Enforcing Quality System (Anti-Regression)

### Problem We're Solving
AI iterations can accidentally remove or break critical features. This happened with:
- Parallel execution (code existed but never ran)
- Phase management (scripts existed but never called)
- Bypass permissions (configured but didn't work)

### Three Layers of Defense

#### Layer 1: Protected Core Files (CODEOWNERS)
These files CANNOT be modified without @perfectuser21 approval:
- All hooks in /.claude/hooks/**
- Workflow configs in /.workflow/**
- Core scripts: pre_merge_audit.sh, static_checks.sh
- Configuration: settings.json, CLAUDE.md, VERSION, SPEC.yaml

**AI Rule**: Never modify these files unless explicitly instructed by user.

#### Layer 2: Sentinel Checks (CI)
CI workflow `guard-core.yml` runs on every PR/push and verifies:
- Critical files still exist (31 checks)
- Critical configurations intact (bypass permissions, 7-phase system)
- Anti-Hollow sentinel strings present in codebase
- Version consistency across all files

**Failure = PR blocked**

#### Layer 3: Contract Tests
Tests verify features **actually work**, not just exist:
- `parallel_subagent_suggester.sh` must have execution logs
- `phase_manager.sh` transitions must update .phase/current
- Evidence collection must produce .yml files
- Bypass permissions must not prompt user

**Location**: tests/contract/test_anti_hollow.sh

### Runtime Validation in pre_merge_audit.sh
Pre-merge audit now checks:
- Hook execution logs (not just file existence)
- Phase state maintenance (staleness detection)
- Evidence collection activity (last 7 days)

**FAIL if**: Critical hook never executed (hollow implementation detected!)

### AI Responsibilities
1. **Before modifying core files**: Check if CODEOWNERS allows it
2. **After adding features**: Collect evidence of actual execution
3. **During phase transitions**: Update .phase/current file
4. **When claiming "feature works"**: Provide execution logs as proof

### Phase State Management
**New Hook**: phase_state_tracker.sh (PrePrompt[1])
- Displays current phase on every AI prompt
- Reminds AI to update .phase/current on transitions
- Detects stale phase state (>7 days)

**AI Must**:
- Update .phase/current when transitioning phases: `echo Phase3 > .phase/current`
- Never let phase state become stale

### Weekly Hollow Scan
TODO: Add weekly CI job to scan for hollow implementations and create issues automatically.

---

## 🚨 规则4: 7-Phase完整执行强制（100%强制）
**优先级: 最高 | 硬阻止PR创建和版本不升级**

### 🎯 核心原则
```
Phase 1 开始 → Phase 7 完成 → 才能创建PR
每次修改 = 版本号必须升级
```

### ❌ 绝对禁止的行为

#### 禁止1: 在Phase 7之前创建PR
```
❌ Phase 1-6任意阶段 → gh pr create  # 被pr_creation_guard.sh硬阻止 (exit 1)
✅ Phase 7完成 → gh pr create         # 允许
```

**问题**：过早创建PR导致Phase不完整，缺少关键步骤（版本升级、最终清理、验收测试）

**强制机制**：
- **Hook**: `.claude/hooks/pr_creation_guard.sh` (PreBash)
- **检查**: 读取 `.phase/current`，必须是 `Phase7`
- **阻止**: 如果不是Phase7，exit 1 + 清晰错误消息
- **绕过**: 无法绕过，硬阻止

#### 禁止2: 跳过任何Phase
```
❌ Phase 1 → Phase 3 (跳过Phase 2)  # phase_completion_validator.sh阻止
❌ Phase 2 → Phase 5 (跳过Phase 3-4)  # phase_completion_validator.sh阻止
✅ Phase 1 → Phase 2 → ... → Phase 7  # 正确流程
```

**问题**：跳过Phase导致质量门禁失效（如跳过Phase 3测试，Phase 4审查）

**强制机制**：
- **Hook**: `.claude/hooks/phase_completion_validator.sh` (PostToolUse)
- **检查**: 每个Phase有明确完成标准（文档、测试、审查）
- **阻止**: Phase未完成时无法转换到下一Phase
- **绕过**: 无法绕过，必须满足完成标准

#### 禁止3: 不升级版本号
```
❌ 修改代码但VERSION不变  # version_increment_enforcer.sh硬阻止 (exit 1)
❌ 版本号倒退 (8.6.0 → 8.5.0)  # version_increment_enforcer.sh阻止
✅ 修改代码 + VERSION升级 (8.5.1 → 8.6.0)  # 允许
```

**问题**：不升级版本导致无法追踪变更，merge冲突，release混乱

**强制机制**：
- **Hook**: `.claude/hooks/version_increment_enforcer.sh` (PreCommit)
- **检查**: 比较当前分支VERSION与main分支VERSION
- **阻止**: 如果版本相同或倒退，exit 1 + 清晰错误消息
- **要求**: 必须升级6个文件版本一致（VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml）

### ✅ 强制执行机制

**4层硬阻止**：

1. **PreBash Hook** (`.claude/hooks/pr_creation_guard.sh`)
   - 触发时机: AI执行 `gh pr create` 或 `git push --set-upstream` 前
   - 检查内容:
     - `.phase/current` 必须是 `Phase7`
     - `.workflow/ACCEPTANCE_REPORT_*.md` 必须存在
     - `scripts/check_version_consistency.sh` 必须通过
   - 失败后果: exit 1，命令被阻止，显示错误消息

2. **Phase Validator** (`.claude/hooks/phase_completion_validator.sh`)
   - 触发时机: PostToolUse (工具使用后)
   - 检查内容:
     - Phase 1: P1_DISCOVERY.md, ACCEPTANCE_CHECKLIST.md, PLAN.md 存在
     - Phase 2: 代码已提交 (feat:/fix:/refactor: commit)
     - Phase 3: static_checks.sh 通过（质量门禁1）
     - Phase 4: pre_merge_audit.sh 通过（质量门禁2）
     - Phase 5: VERSION升级 + CHANGELOG更新
     - Phase 6: ACCEPTANCE_REPORT存在
     - Phase 7: 清理完成 + 版本一致 + Git status干净
   - 失败后果: Phase转换被阻止

3. **PreCommit Hook** (`.claude/hooks/version_increment_enforcer.sh`)
   - 触发时机: Git commit前
   - 检查内容:
     - 获取main分支VERSION
     - 比较当前分支VERSION
     - 版本必须大于main (semver比较)
   - 失败后果: exit 1，commit被阻止，提示使用 `bump_version.sh`

4. **CI Checks** (`.github/workflows/guard-core.yml`)
   - 触发时机: 每次push、每次PR
   - 检查内容:
     - 61项检查（关键文件、配置、sentinel字符串、运行时行为）
     - 版本一致性（6个文件）
     - Phase完整性
   - 失败后果: CI红灯，PR无法merge

### 🔒 违反后果

**立即阻止 + 清晰指导**：

```bash
# 示例1: 在Phase 4尝试创建PR
$ gh pr create
════════════════════════════════════════════════════════════
❌ ERROR: Cannot create PR before Phase 7 completion
════════════════════════════════════════════════════════════

Current Phase: Phase4
Required Phase: Phase7

📋 7-Phase Workflow (mandatory, no skipping):

  ✅ Phase 1: Discovery & Planning
  ✅ Phase 2: Implementation
  ✅ Phase 3: Testing (Quality Gate 1)
  ✅ Phase 4: Review (Quality Gate 2)
  ⏳ Phase 5: Release Preparation ← YOU MUST COMPLETE THIS
  ⏳ Phase 6: Acceptance Testing
  ⏳ Phase 7: Final Cleanup

💡 To proceed:
   1. Complete all remaining phases
   2. Update .phase/current to Phase7
   3. Then create PR

🚨 This is a HARD BLOCK - cannot be bypassed
════════════════════════════════════════════════════════════
# 命令被阻止，exit code = 1
```

```bash
# 示例2: 不升级版本号就commit
$ git commit -m "feat: add new feature"
════════════════════════════════════════════════════════════
❌ ERROR: Version must be incremented
════════════════════════════════════════════════════════════

Main branch version: 8.5.1
Your branch version: 8.5.1

🚨 RULE: Every code change requires version increment!

📋 Update these 6 files with new version:
   1. VERSION
   2. .claude/settings.json
   3. .workflow/manifest.yml
   4. package.json
   5. CHANGELOG.md
   6. .workflow/SPEC.yaml

💡 Recommended commands:
   # Patch version (bug fix): 8.5.1 → 8.5.2
   bash scripts/bump_version.sh patch

   # Minor version (new feature): 8.5.1 → 8.6.0
   bash scripts/bump_version.sh minor

   # Major version (breaking change): 8.5.1 → 9.0.0
   bash scripts/bump_version.sh major

🔍 Or manually update all 6 files to the same new version
════════════════════════════════════════════════════════════
# Commit被阻止，exit code = 1
```

### 📋 AI必须遵守的完整流程

```
用户提出需求
    ↓
【Phase 1: Discovery & Planning】
  - 创建 P1_DISCOVERY.md (>300行)
  - 创建 ACCEPTANCE_CHECKLIST.md (定义验收标准)
  - 创建 PLAN.md (>500行架构规划)
  - phase_completion_validator检查 ✓
    ↓
【Phase 2: Implementation】
  - 实现代码
  - 提交 feat:/fix:/refactor: commit
  - phase_completion_validator检查 ✓
    ↓
【Phase 3: Testing】🔒 质量门禁1
  - 运行 static_checks.sh (shellcheck, bash -n, 复杂度)
  - 所有测试通过
  - phase_completion_validator检查 ✓
    ↓
【Phase 4: Review】🔒 质量门禁2
  - 运行 pre_merge_audit.sh (12项检查)
  - 创建 REVIEW.md (>100行)
  - phase_completion_validator检查 ✓
    ↓
【Phase 5: Release Preparation】
  - ⚠️ 升级版本号 (version_increment_enforcer检查)
  - 更新 CHANGELOG.md
  - 更新 README.md
  - phase_completion_validator检查 ✓
    ↓
【Phase 6: Acceptance Testing】
  - 对照Phase 1 Checklist验证
  - 创建 ACCEPTANCE_REPORT.md
  - 用户确认 "没问题"
  - phase_completion_validator检查 ✓
    ↓
【Phase 7: Final Cleanup】
  - 运行 comprehensive_cleanup.sh
  - 运行 check_version_consistency.sh (6个文件一致)
  - Git status 干净
  - phase_completion_validator检查 ✓
    ↓
【创建PR】← 只有到这里才能 gh pr create
  - pr_creation_guard.sh检查 ✓
  - 允许创建PR
    ↓
【等待CI】
  - guard-core.yml运行61项检查
  - 所有检查通过 ✓
    ↓
【用户说"merge"】
  - gh pr merge --auto --squash
  - GitHub Actions自动创建tag
  - 完成 ✅
```

### 🎯 关键时间点

| 时间点 | 检查内容 | 强制机制 | 绕过可能性 |
|--------|---------|---------|-----------|
| **Phase转换时** | Phase完成标准 | phase_completion_validator.sh | ❌ 无法绕过 |
| **Commit时** | 版本号升级 | version_increment_enforcer.sh | ❌ 无法绕过 |
| **创建PR时** | Phase7完成 | pr_creation_guard.sh | ❌ 无法绕过 |
| **Push时** | CI检查 | guard-core.yml (61 checks) | ❌ 无法绕过 |

### 🚀 实施历史

- **v8.6.0**: 实现3个强制hook (pr_creation_guard, version_increment_enforcer, 强化phase_completion_validator)
- **目标**: 7-Phase完整执行率100%，零Phase跳过，零版本不升级

### 📊 成功指标

**30天后验证**：
- [ ] 7-Phase完整执行率 = 100%
- [ ] Phase跳过次数 = 0
- [ ] 版本未升级commit数 = 0
- [ ] 提前创建PR次数 = 0

---

## 🚀 核心工作流：7-Phase系统（v6.6统一版）

### 完整7 Phases开发周期

**从需求到合并的完整旅程**（97个自动化检查点，零质量损失）

```
╔═══════════════════════════════════════════════════════════╗
║  Phase 1: Discovery & Planning（探索与规划）- 33检查点   ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：理解问题 + 制定计划 + 确定验收标准

【包含内容】：
  1.1 Branch Check（分支前置检查）⛔ 强制
      - 检查当前分支 → 判断是否需要新分支 → 创建工作分支
      - 检查点：5个（PD_S001-S005）

  1.2 Requirements Discussion（需求讨论）
      - 需求澄清、技术可行性初步评估
      - 检查点：5个（P1_S001-S005）

  1.3 Technical Discovery（技术探索）✅ 核心
      - 技术spike、可行性验证、问题分析
      - 产出：P2_DISCOVERY.md + Acceptance Checklist
      - 检查点：8个（P2_S001-S008）

  1.4 Impact Assessment（影响评估）⚙️ 自动化
      - 自动计算影响半径分数（0-100分）
      - 智能推荐Agent数量（0/3/6 agents）
      - 公式：Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
      - 性能：<50ms，准确率86%
      - 检查点：3个（IA_S001-S003）

  1.5 Architecture Planning（架构规划）✅ 核心
      - 系统架构设计、技术栈选择、风险识别
      - 应用Impact Assessment结果选择Agent策略
      - 产出：PLAN.md + 项目目录结构
      - 检查点：12个（P3_S001-S012）

【核心产出】：
  ✅ P2_DISCOVERY.md（>300行）
  ✅ Acceptance Checklist（定义"完成"的标准）
  ✅ PLAN.md（>1000行）
  ✅ 完整的项目骨架
  ✅ Agent策略（基于影响评估）

【质量保障】：无TODO占位符（防空壳检查）

---

## 🎯 Phase 1完成确认机制（强制）

**触发时机**：Phase 1.5 (Architecture Planning)完成后

**必须做的3件事**：

1. ✅ **用人话说明白要做什么**
   - 不用技术术语
   - 举例说明before/after
   - 一句话总结核心价值

2. ✅ **展示详细Checklist**
   - 7-Phase强制检查步骤
   - 实际可运行的测试用例
   - N项验收标准（来自user_request.md）
   - 回滚机制和问题处理

3. ✅ **等待用户确认**
   - 必须等用户说"我理解了，开始Phase 2"
   - 不能自动进入Phase 2
   - 用户说"有疑问"或"方案不行" → 重新设计

**详细规范**：见`.claude/phase1_confirmation.yml`

**禁止行为**：
- ❌ Phase 1结束后直接写代码
- ❌ 只给技术文档不总结
- ❌ 用技术术语解释
- ❌ 不等用户确认就继续

### 🛡️ 双层保障机制（v8.7.0新增）

**问题**：AI可能在用户说"开始吧"/"继续"时，跳过Phase 1确认直接进入Phase 2

**解决方案**：Skills主动提醒 + Hooks被动阻止

#### Layer 1: Skill "phase1-completion-reminder" (主动提醒层)
- **触发**：检测到Phase 1文档完成但无确认标记时
- **行为**：温馨提醒AI执行确认流程
- **优势**：90%情况下AI看到提醒后会主动确认，用户体验好
- **配置**：`.claude/settings.json` → `skills` → `phase1-completion-reminder`

**Skill提醒内容**：
```
⚠️ Phase 1 Completion Detected

📋 Required Actions:
1. Display 7-Phase checklist to user
2. Summarize what we'll implement (in plain language)
3. Wait for user to say 'I understand, start Phase 2'
4. Then create .phase/phase1_confirmed marker
5. Update .phase/current to Phase2

❌ Do NOT start coding until user confirms!
```

#### Layer 2: Hook "phase1_completion_enforcer.sh" (强制阻止层)
- **触发**：PreToolUse (Write/Edit/Bash前)
- **检查**：Phase1完成 + 无`.phase/phase1_confirmed`标记
- **行为**：硬阻止（exit 1），显示详细错误消息
- **作用**：最后防线，即使AI忽略Skill提醒也能阻止
- **位置**：`.claude/hooks/phase1_completion_enforcer.sh`

**Hook阻止条件**：
```bash
if [[ "$CURRENT_PHASE" == "Phase1" ]] && \
   [[ -f "docs/P1_DISCOVERY.md" ]] && \
   [[ -f ".workflow/ACCEPTANCE_CHECKLIST.md" ]] && \
   [[ -f "docs/PLAN.md" ]] && \
   [[ ! -f ".phase/phase1_confirmed" ]]; then
    # 硬阻止并显示5步确认流程
    exit 1
fi
```

#### 工作流示例

**正常流程（AI遵守Skill提醒）**：
```
用户: "开始吧"
   ↓
【Skill提醒】phase1-completion-reminder显示
   ↓
AI响应: "Phase 1已完成！让我展示接下来的计划..."
   ↓
用户: "我理解了，开始Phase 2"
   ↓
AI: touch .phase/phase1_confirmed
AI: echo Phase2 > .phase/current
   ↓
Phase 2顺利执行 ✅
```

**异常流程（AI忽略Skill，Hook拦截）**：
```
用户: "开始吧"
   ↓
【Skill提醒】（AI忽略或未看到）
   ↓
AI尝试执行Write/Edit
   ↓
【Hook阻止】phase1_completion_enforcer.sh
   ↓
错误消息: "❌ ERROR: Phase 1 completion requires user confirmation"
   ↓
AI看到错误，补充确认流程 ✅
```

#### 对比：Skill vs Hook

| 维度 | Skill (主动提醒) | Hook (被动阻止) |
|------|-----------------|----------------|
| **触发时机** | before_tool_use | PreToolUse |
| **行为** | 温馨提示 💡 | 硬阻止 🛑 |
| **性能** | 0ms | <50ms |
| **用户体验** | 好（主动引导） | 差（被动阻止） |
| **作用** | 第一道防线 | 最后防线 |

**设计理念**：
- ✅ 主动提醒优于被动阻止（90%情况下Skill就够了）
- ✅ 双层保障确保100%覆盖（Hook是最后防线）
- ✅ 性能优异（Skill 0ms，Hook <50ms）
- ✅ 可扩展（同样模式可用于其他Phase转换）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 2: Implementation（实现开发）- 15检查点            ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：编码实现核心功能

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

【核心活动】：
  - 按照PLAN.md实现功能
  - 创建验证脚本和工具
  - 配置Git Hooks
  - 提交规范的commits

【核心产出】：
  ✅ 可运行的代码
  ✅ workflow_validator.sh（>50步验证）
  ✅ 工具和脚本（local_ci.sh, serve_progress.sh等）
  ✅ Git commits（规范格式）

【检查点】：15个（P4_S001-S015）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 3: Testing（质量验证）- 15检查点 🔒 质量门禁1      ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：确保代码质量和功能正确性

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

【必须执行】：`bash scripts/static_checks.sh`

【核心检查】：
  ✅ Shell语法验证（bash -n）
  ✅ Shellcheck linting
  ✅ 代码复杂度检查（<150行/函数）
  ✅ Hook性能测试（<2秒）
  ✅ 单元测试 + 集成测试
  ✅ BDD场景测试
  ✅ 测试覆盖率（≥70%）
  ✅ 敏感信息检测

【核心产出】：
  ✅ 测试报告
  ✅ 覆盖率报告
  ✅ 性能benchmark

【阻止标准】：⛔ 任何检查失败都阻止进入Phase 4

【检查点】：15个（P5_S001-S015）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 4: Review（代码审查）- 10检查点 🔒 质量门禁2       ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：AI手动审查 + 合并前审计

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

【必须执行】：`bash scripts/pre_merge_audit.sh`

【自动化检查】：
  ✅ 配置完整性（hooks注册、权限）
  ✅ 遗留问题扫描（TODO/FIXME）
  ✅ 垃圾文档检测（根目录≤7个）
  ✅ 版本完全一致性（6文件匹配）⛔
  ✅ 代码模式一致性
  ✅ 文档完整性（REVIEW.md >3KB）

【AI手动验证】：
  🤖 逻辑正确性（IF判断、return语义）- AI自己检查
  🤖 代码一致性（统一实现模式）- AI自己检查
  🤖 Phase 1 checklist对照验证 - AI自己检查

**注意**："人工验证"指AI手动检查，不是用户参与

【审查标准】：
  1. 逻辑正确性：条件判断完整、返回值正确、边界处理
  2. 代码一致性：相同功能用相同模式、命名统一、风格一致
  3. 完整性验证：Phase 1 checklist ≥90%完成

【核心产出】：
  ✅ REVIEW.md（完整审查报告，>100行）
  ✅ Audit报告

【阻止标准】：⛔ critical issue都阻止进入Phase 5

【检查点】：10个（P6_S001-S010）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 5: Release（发布监控）- 15检查点                   ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：发布代码 + 配置监控

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

【核心活动】：
  ✅ 更新CHANGELOG.md
  ✅ 更新README.md
  ✅ 创建Git Tag（semver格式）
  ✅ 配置健康检查
  ✅ 配置SLO监控
  ✅ 更新部署文档

【核心产出】：
  ✅ Release notes
  ✅ Git tag
  ✅ 监控配置

【质量要求】：
  - 根目录文档≤7个 ⛔
  - Phase 1 checklist ≥90%完成

【检查点】：15个（P7_S001-S015）

【铁律】：不应该在此阶段发现bugs（发现→返回Phase 4）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 6: Acceptance（验收确认）- 5检查点                 ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：AI生成验收报告 + 用户确认

【核心活动】：
  - AI对照Phase 1 Acceptance Checklist逐项验证
  - 生成验收报告
  - AI说："我已完成所有验收项，请您确认"
  - 等待用户说："没问题"

【核心产出】：
  ✅ Acceptance Report
  ✅ 用户确认标记

【阻止标准】：⛔ 存在critical问题无法验收

【检查点】：5个（AC_S001-S005）

---

╔═══════════════════════════════════════════════════════════╗
║  Phase 7: Closure（收尾合并）- 4检查点                    ║
╚═══════════════════════════════════════════════════════════╝

【阶段目标】：全面清理 + 最终验证 + 准备合并

【核心活动】：
  🧹 全面清理过期信息和临时文件
  🔍 最终版本一致性验证 ⛔（6个文件）
  🔄 Phase系统一致性验证
  📝 检查文档规范
  🚀 准备PR

【必须执行的脚本】：
  1. `bash scripts/comprehensive_cleanup.sh [mode]` - 全面清理（3种模式）
     - `aggressive` - 激进清理，删除所有过期内容（推荐）
     - `conservative` - 保守清理，归档而不删除
     - `minimal` - 最小清理，只删除明确过期的
     - `interactive` - 交互式选择模式（默认）

  2. `bash scripts/check_version_consistency.sh` - 验证6个文件版本统一

  3. `bash scripts/verify-phase-consistency.sh` - 验证Phase系统一致性

【全面清理Checklist】：

  过期文件清理（comprehensive_cleanup.sh执行）：
  - [ ] .temp/目录清空（保留结构）
  - [ ] 旧版本文件删除（*_v[0-9]*, *_old*, *.bak）
  - [ ] 重复文档删除（PLAN*.md等）
  - [ ] 归档目录整合（archive/统一管理）
  - [ ] 测试会话数据清理
  - [ ] 过期配置删除（*.backup_old_*等）
  - [ ] 大文件清理（7天以上的日志和报告）
  - [ ] Git仓库清理（git gc）

  版本文件（6个必须一致）：
  - [ ] VERSION
  - [ ] .claude/settings.json
  - [ ] .workflow/manifest.yml
  - [ ] package.json
  - [ ] CHANGELOG.md
  - [ ] .workflow/SPEC.yaml

  Phase系统（必须统一为7 Phases）：
  - [ ] SPEC.yaml: total_phases = 7
  - [ ] manifest.yml: phases数组长度 = 7
  - [ ] manifest.yml: Phase ID格式 = Phase1-Phase7
  - [ ] CLAUDE.md: 描述为7-Phase系统

  文档规范验证：
  - [ ] 根目录文档 ≤7个 ⛔
  - [ ] .temp/目录大小 <10MB
  - [ ] 无临时报告文件（*_REPORT.md等）

  核心结构验证：
  - [ ] `bash tools/verify-core-structure.sh` 通过
  - [ ] LOCK.json已更新（如有必要）

【清理后验证】：
  ✅ 根目录文档数量（应≤7个）
  ✅ .temp/大小（应<10MB）
  ✅ Git工作区状态（应干净）
  ✅ 版本一致性（6/6文件统一）
  ✅ 未提交更改数量（准备commit）

【核心产出】：
  ✅ 干净的分支（无过期文件）
  ✅ 版本完全一致（6/6文件）
  ✅ Phase系统统一（7 Phases）
  ✅ 释放空间（~10-20MB）
  ✅ merge-ready状态

【检查点】：4个（CL_S001-S002 + G002-G003）

【等待用户】：用户明确说"merge"后才能合并到主线

---

### 📊 Phase 7清理模式对比

| 模式 | 清理范围 | 风险 | 适用场景 |
|------|---------|------|---------|
| **aggressive** | 删除所有过期内容 | 低 | 发布前清理（推荐） |
| **conservative** | 归档而不删除 | 极低 | 不确定是否需要保留 |
| **minimal** | 只删除明确过期的 | 极低 | 快速清理 |
| **interactive** | 由用户选择 | 自定 | 首次使用 |

**推荐用法**：
```bash
# 发布前全面清理
bash scripts/comprehensive_cleanup.sh aggressive

# 查看清理效果
git status
du -sh .temp/
ls -1 *.md | wc -l  # 应该≤7
```

---

### ⚠️ Phase 7 正确工作流（Critical）

**基于PR #40经验教训和ChatGPT审核反馈**

#### ❌ 错误做法（绝对禁止）

```bash
# ❌ 错误1：在feature分支直接merge到main
git checkout main
git merge feature/xxx
git push origin main  # 会被hook阻止

# ❌ 错误2：创建PR后立即merge，不等CI
gh pr create --title "feat: xxx"
gh pr merge --squash  # ❌ CI还没跑完就merge了

# ❌ 错误3：从feature分支创建tag
git checkout feature/dashboard-v2
git tag v7.2.0
git push origin v7.2.0  # ❌ Tag应该从main创建
```

**为什么错误**：
- 错误1：绕过了GitHub的Required Status Checks
- 错误2：CI没跑完就merge，检查失败也会合并进去
- 错误3：Tag应该标记main分支的稳定版本，不是feature分支

---

#### ✅ 正确做法（Phase 7标准流程）

**Step 1: 推送feature分支**
```bash
# 确保在feature分支
git checkout feature/xxx

# 推送到远程
git push -u origin feature/xxx
```

**Step 2: 创建Pull Request**
```bash
# 创建PR（不要立即merge）
gh pr create \
  --title "feat: 功能描述" \
  --body "$(cat <<'EOF'
## Summary
- 实现了xxx功能
- 修复了xxx问题

## Test Plan
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 静态检查通过

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**Step 3: 等待CI完成（Critical）**
```bash
# 监控CI状态（必须等待）
gh pr checks --watch

# 输出示例：
# ✓ CE Unified Gates        pass  2m 30s
# ✓ Quality Gate           pass  45s
# ✓ Test Suite             pass  1m 15s
# ✓ Security Scan          pass  30s
# ✓ Syntax Validation      pass  20s
# ✓ Performance Check      pass  15s
```

**Step 4: CI通过后才能merge**
```bash
# 方式A: 自动合并（推荐）
gh pr merge --auto --squash

# 方式B: 手动确认merge
# 1. 检查所有checks都是绿色✓
# 2. 确认PR已up-to-date
# 3. 执行merge
gh pr merge --squash
```

**Step 5: Merge后由GitHub Actions自动创建tag**
```yaml
# .github/workflows/release.yml会自动执行：
# 1. 检测到main有新commit
# 2. 读取VERSION文件
# 3. 创建对应tag（例如v7.2.0）
# 4. 推送到GitHub
```

---

#### 🔒 强制保障机制

**三层防护确保正确流程**：

1. **Local Git Hooks**: 阻止直接push到main
   ```bash
   # .git/hooks/pre-push会阻止：
   git push origin main  # ❌ BLOCKED
   ```

2. **GitHub Branch Protection**: 要求CI通过
   ```yaml
   required_status_checks:
     strict: true
     checks: ["CE Unified Gates"]
   ```

3. **Repository Rulesets**: 保护tag创建
   ```json
   {
     "target": "tag",
     "conditions": {"ref_name": {"include": ["refs/tags/v*"]}},
     "rules": [{"type": "creation"}, {"type": "required_signatures"}]
   }
   ```

---

#### 📋 Phase 7 完整Checklist

**在说"merge"之前必须确认**：

- [ ] ✅ 代码已推送到feature分支
- [ ] ✅ PR已创建（包含完整描述）
- [ ] ✅ CI全部通过（`gh pr checks`显示全绿✓）
- [ ] ✅ PR已up-to-date with main
- [ ] ✅ 没有merge conflicts
- [ ] ✅ 版本号已更新（VERSION等6个文件一致）
- [ ] ✅ CHANGELOG.md已更新
- [ ] ✅ .temp/目录已清理
- [ ] ❌ 没有在feature分支创建tag

**确认后执行**：
```bash
gh pr merge --auto --squash
```

**Merge完成后**：
- ✅ GitHub Actions自动创建tag
- ✅ Tag自动推送到GitHub
- ✅ Release notes自动生成
- ✅ feature分支可以删除

---

#### 🎯 关键原则

1. **Never bypass CI**: 永远等待CI完成再merge
2. **Tags from main only**: Tag只从main分支创建，由GitHub Actions自动完成
3. **PR is mandatory**: 即使是自己的项目，也必须走PR流程
4. **Auto-merge preferred**: 使用`--auto`让GitHub在条件满足时自动merge

---

#### 📊 时间线示例（正确流程）

```
T+0:00  → git push origin feature/xxx
T+0:10  → gh pr create
T+0:11  → CI开始运行（CE Unified Gates触发）
T+0:15  → Quality Gate ✓
T+0:30  → Test Suite ✓
T+0:45  → Security Scan ✓
T+1:00  → Syntax Validation ✓
T+1:10  → Performance Check ✓
T+1:15  → CE Unified Gates ✓ (汇总通过)
T+1:20  → gh pr merge --auto --squash (自动merge)
T+1:25  → GitHub Actions检测到main新commit
T+1:30  → 自动创建tag v7.2.0
T+1:35  → Tag推送完成 ✅
```

**关键点**：从PR创建到merge完成，等待了1分钟让CI运行完成。

---

#### 🚨 如果CI失败怎么办

```bash
# 查看失败原因
gh pr checks

# 输出示例：
# ✗ Syntax Validation      fail  45s
# ✓ Quality Gate          pass  30s
# ...

# 查看详细日志
gh pr checks --web  # 在浏览器打开

# 修复问题后重新推送
git add .
git commit -m "fix: 修复CI问题"
git push

# CI会自动重新运行
gh pr checks --watch
```

**不要**：
- ❌ 不要用`--admin`或`--force`强制merge
- ❌ 不要修改branch protection绕过检查
- ❌ 不要在local merge然后force push

**应该**：
- ✅ 修复问题让CI通过
- ✅ 如果是CI误报，修复CI配置
- ✅ 保持质量门禁的完整性
```

---

### 📊 7 Phases统计总览

| Phase | 名称 | 检查点 | 质量门禁 | 硬性阻止 |
|-------|------|--------|---------|---------|
| Phase 1 | Discovery & Planning | 33 | - | 1个 |
| Phase 2 | Implementation | 15 | - | - |
| Phase 3 | Testing | 15 | 🔒 Gate 1 | 2个 |
| Phase 4 | Review | 10 | 🔒 Gate 2 | 2个 |
| Phase 5 | Release | 15 | - | 2个 |
| Phase 6 | Acceptance | 5 | - | 1个 |
| Phase 7 | Closure | 4 | - | - |
| **总计** | **7 Phases** | **97个** | **2个** | **8个** |

---

### 🎯 关键转折点

```
Phase 1 → Phase 2: Acceptance Checklist定义完成 ✅
Phase 2 → Phase 3: 核心功能实现完成 ✅
Phase 3 → Phase 4: 所有自动化测试通过 ⛔ 门禁1
Phase 4 → Phase 5: 代码审查通过 + 无critical issue ⛔ 门禁2
Phase 5 → Phase 6: Phase 1 checklist ≥90%完成 ✅
Phase 6 → Phase 7: 用户确认"没问题" ✅
Phase 7 → Merge: 用户明确说"merge" ✅
```

---

### 🤖 智能Agent策略（自动化）

**Impact Assessment自动触发**（Phase 1.4）：
- 分析任务描述（风险+复杂度+影响范围）
- 计算影响半径：`Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)`
- 智能推荐Agent数量

**Agent数量映射**：
- **高风险任务** (Radius ≥50): **6 agents** - CVE修复、架构变更、数据库迁移
- **中风险任务** (Radius 30-49): **3 agents** - Bug修复、性能优化、模块重构
- **低风险任务** (Radius 0-29): **0 agents** - 文档更新、代码格式化、注释修改

**性能指标**: <50ms执行时间，86%准确率（26/30样本验证）✅

### 🎯 质量门禁策略（Quality Gates）

**核心原则：左移测试（Shift Left）**
- 越早发现问题，修复成本越低
- Phase 3发现 > Phase 4发现 > Phase 5发现

**三阶段检查体系**：

#### Phase 3阶段：技术质量门禁 🔒 Gate 1
- **自动化检查**（必须100%通过）：
  - Shell语法验证（`bash -n`）- 防止语法错误
  - Shellcheck linting - 防止常见bug模式
  - 代码复杂度 - 防止函数过长（>150行阻止）
  - Hook性能 - 防止执行过慢（>5秒阻止）
  - 功能测试 - 防止功能回归

- **产出要求**：
  - 测试覆盖率报告
  - 性能benchmark结果
  - 所有自动化检查通过证明

#### Phase 4阶段：代码质量门禁 🔒 Gate 2
- **自动化检查**（必须100%通过）：
  - 配置完整性 - 所有hooks正确注册
  - 文档规范性 - 根目录≤7个核心文档
  - **版本完全一致性 - VERSION + settings.json + manifest.yml + package.json + CHANGELOG.md 必须完全相同**
  - 代码模式一致性 - 相似功能用相同实现

- **人工验证**（必须完成）：
  - 逻辑正确性（IF判断、return值语义）
  - 代码一致性（6个Layers统一逻辑）
  - 文档完整性（REVIEW.md >100行）
  - Phase 1 checklist对照验证

- **产出要求**：
  - REVIEW.md（完整审查报告）
  - 代码一致性验证报告
  - Pre-merge checklist全部✓

#### Phase 5阶段：最终发布门禁
- **唯一职责**：确认Phase 1-4所有工作完成 + 发布配置
- **禁止行为**：在Phase 5发现bugs
- **处理原则**：发现bugs → 返回Phase 4重新审查

**质量指标追踪**：
- 短期目标：Phase 5发现bugs的比例<10%
- 中期目标：90%的bugs在Phase 3-4被发现
- 长期目标：Phase 5变成纯确认阶段（0 bugs）

**经验教训**（PR #19案例）：
- ❌ 语法错误在Phase 5发现 → 应该在Phase 3静态检查发现
- ❌ Layers 1-5逻辑bug在Phase 5发现 → 应该在Phase 4代码审查发现
- ✅ Layer 6缺失在Phase 3发现 → 正确的发现时机
- 📝 改进措施：建立Phase 3/Phase 4自动化检查脚本

## 🛡️ 五层质量保障体系【v7.4增强】

### 1. 质量守护层【新增 2025-10-25】
- **Script Size Guardian**: 强制脚本≤300行，防止大文件产生
- **Version Cleaner**: 自动清理旧版本，防止版本累积
- **Quality Guardian**: 主动预防质量问题，而非事后修复
- **Performance Monitor**: 实时性能监控，建立基线对比

### 2. 契约驱动层
- **OpenAPI规范**: 完整的API契约定义
- **BDD场景**: 65个可执行的验收标准
- **性能预算**: 90个性能指标阈值
- **SLO监控**: 15个服务级别目标

### 3. Workflow框架层
- 标准化7个Phase流程（Phase 1-7）
- 从分支检查到监控的完整生命周期

### 4. Claude Hooks辅助层
- `branch_helper.sh` - 分支管理助手
- `smart_agent_selector.sh` - 智能Agent选择
- `quality_gate.sh` - 质量门禁检查
- `gap_scan.sh` - 差距分析

### 5. Git Hooks强制层
- `pre-commit` - 硬拦截 + 质量守护检查
- `commit-msg` - 提交信息规范
- `pre-push` - 推送前验证
- 包含脚本大小限制、版本控制检查

## 🎨 专业级质量保障

### 自动化质量门禁
- **BDD验收**: 65个场景必须通过
- **性能基准**: 不能低于预算阈值
- **安全扫描**: 自动检测敏感信息
- **分支保护**: 4层防护架构，防止误操作

### 监控与告警
- **性能监控**: 90个性能指标实时跟踪
- **健康检查**: 每日自动健康检查
- **告警系统**: 违反阈值自动告警
- **自愈系统**: 自动检测和防止自我矛盾

## 📁 完整项目结构【扩展】

```
.claude/
├── settings.json                # Claude配置
├── WORKFLOW.md                  # 工作流详解
├── AGENT_STRATEGY.md            # Agent策略说明
├── DECISIONS.md                 # 重要决策记录【新增】
├── hooks/                       # Claude Hooks
│   ├── branch_helper.sh         # 分支助手
│   ├── smart_agent_selector.sh  # Agent选择器
│   ├── quality_gate.sh          # 质量检查
│   └── gap_scan.sh              # 差距分析【新增】
├── core/                        # 核心模块
│   └── lazy_orchestrator.py     # 懒加载优化
└── install.sh                   # 一键安装

acceptance/                      # BDD测试【新增】
├── features/                    # 场景文件
│   ├── auth.feature
│   ├── workflow.feature
│   ├── session_timeout.feature
│   └── generated/              # 自动生成的场景
└── steps/                      # 步骤定义

api/                            # API契约【新增】
├── openapi.yaml               # OpenAPI规范
└── schemas/                    # Schema定义

metrics/                        # 性能管理【新增】
├── perf_budget.yml            # 性能预算（90个指标）
└── metrics.yml                # 度量定义

observability/                  # 可观测性【新增】
├── slo/
│   └── slo.yml                # SLO定义（15个）
├── alerts/                    # 告警配置
└── probes/                    # 健康探针

migrations/                    # 数据库迁移【新增】
└── *.sql                     # 包含rollback

scripts/                       # 工具脚本【新增】
├── gap_scan.sh               # 差距扫描
├── gen_bdd_from_openapi.mjs # BDD生成器
├── run_to_100.sh            # 一键优化
├── capability_snapshot.sh    # 能力快照
├── static_checks.sh         # Phase 3静态检查【新增】
└── pre_merge_audit.sh       # Phase 4合并前审计【新增】

.git/hooks/                   # Git Hooks（强制）
├── pre-commit               # 硬拦截检查
├── commit-msg              # 信息规范
└── pre-push               # 推送验证

.github/workflows/           # CI/CD【增强】
└── ci-enhanced-5.3.yml    # 9个验证jobs
```

## 🎮 快速开始

### 1. 安装系统
```bash
cd your-project
cp -r .claude ./
./.claude/install.sh  # 安装Git Hooks
```

### 2. 验证能力
```bash
# 运行能力快照
./capability_snapshot.sh

# 查看保障力评分
bash test/validate_enhancement.sh
```

### 3. 使用质量检查工具
```bash
# Phase 3阶段：运行静态检查
bash scripts/static_checks.sh

# Phase 4阶段：运行合并前审计
bash scripts/pre_merge_audit.sh

# 运行BDD测试
npm run bdd
```

### 3. 一键优化到100分
```bash
# 如果评分不足100
./run_to_100.sh
```

## 🏅 质量指标

| 指标 | 目标 | 实际 | 状态 |
|-----|-----|-----|-----|
| 保障力评分 | 100 | 100 | ✅ |
| BDD场景 | ≥25 | 65 | ✅ |
| 性能指标 | ≥30 | 90 | ✅ |
| SLO定义 | ≥10 | 15 | ✅ |
| CI Jobs | ≥7 | 9 | ✅ |
| 代码覆盖率 | ≥80% | 85% | ✅ |
| 性能退化 | <10% | 0% | ✅ |

## 💡 使用理念

### Max 20X思维
- **质量第一**：100/100的完美标准
- **全程保障**：从探索到监控的完整覆盖
- **生产级别**：不是玩具，是生产工具

### 契约驱动
- **API First**：先定义契约，再实现
- **BDD验收**：行为驱动的质量保证
- **性能契约**：每个指标有明确预算

### 持续监控
- **实时监控**：性能指标持续跟踪
- **健康检查**：每日自动检查系统健康
- **自愈机制**：防止AI自我矛盾和回归

## 🚨 重要提醒

1. **这是专业级个人工具**：高质量但适合个人使用场景
2. **Git Hooks是强制的**：必须通过才能提交
3. **BDD是可执行的**：不是文档，是活的规范
4. **性能预算是红线**：超过阈值会触发告警
5. **自愈系统已启用**：防止AI重复犯错和自我矛盾

## 🎖️ 认证标志

```
╔═══════════════════════════════════════╗
║   Claude Enhancer 6.3.0 Certified      ║
║   保障力评分: 100/100                ║
║   生产就绪: ✅                        ║
║   质量等级: EXCELLENT                 ║
╚═══════════════════════════════════════╝
```

---

*Claude Enhancer 6.3 - 让AI编程达到专业级标准*
*Your Professional AI Programming Partner*
