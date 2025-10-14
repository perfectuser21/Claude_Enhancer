# 🏥 Claude Enhancer 自愈系统

> 让系统像人体免疫系统一样，自动检测和修复问题

**版本**: 1.0.0 | **最后更新**: 2025-10-13 | **适用人群**: 编程小白也能看懂

---

## 📚 目录

1. [什么是自愈系统？](#what-is)
2. [为什么需要它？](#why)
3. [它如何工作？](#how)
4. [日常使用指南](#usage)
5. [开发者参考](#dev-guide)
6. [故障排除](#troubleshooting)
7. [高级配置](#advanced)
8. [常见问题FAQ](#faq)

---

<a name="what-is"></a>
## 🤔 什么是自愈系统？

### 简单理解

想象你家的房子：
- **传统方式**：你需要定期检查灯泡、水管、电器，坏了再修
- **自愈系统**：房子自己检测问题（灯泡要坏了、水管漏水），自动提醒或修复

Claude Enhancer的自愈系统就像房子的智能管家：
```
┌─────────────────────────────────────┐
│  👀 持续监控                        │
│  ├─ 版本号是否一致？               │
│  ├─ 文档是否重复？                 │
│  ├─ 配置是否冲突？                 │
│  └─ 系统是否太复杂？               │
│                                     │
│  🔧 自动修复                        │
│  ├─ 清理备份文件                   │
│  ├─ 删除临时文件                   │
│  ├─ 同步版本号                     │
│  └─ 修复权限问题                   │
│                                     │
│  📊 健康报告                        │
│  └─ 每天生成健康评分（0-100分）    │
└─────────────────────────────────────┘
```

### 核心能力

| 功能 | 类比 | 说明 |
|------|------|------|
| **预防检测** | 体检 | 在问题恶化前发现 |
| **自动修复** | 吃药 | 自动处理简单问题 |
| **警报通知** | 医生建议 | 复杂问题提醒人工处理 |
| **健康记录** | 病历 | 追踪系统健康趋势 |

---

<a name="why"></a>
## 🎯 为什么需要它？

### 问题场景

**场景1：版本号混乱** 😫
```
❌ 没有自愈系统：
- VERSION文件: 6.2.0
- CLAUDE.md: Claude Enhancer 6.1
- package.json: "version": "6.0.0"
→ 结果：用户不知道真实版本，发布混乱

✅ 有自愈系统：
- 每次提交自动检查
- 发现不一致立即阻止
- 提示如何修复
→ 结果：版本始终统一
```

**场景2：文档越来越多** 📚
```
❌ 没有自愈系统：
- README.md, README2.md, README_NEW.md
- ANALYSIS_REPORT.md, CODE_REVIEW.md, AUDIT.md
→ 结果：找不到有用信息，根目录一团糟

✅ 有自愈系统：
- 限制根目录只能有7个核心文档
- 临时分析放在.temp/自动清理
- 创建新文档前先询问
→ 结果：文档结构清晰
```

**场景3：系统越来越复杂** 🌀
```
❌ 没有自愈系统：
- 从个人工具变成"复杂系统"
- BDD场景从10个增加到100个
- CI workflows从5个增加到20个
→ 结果：启动慢、维护难、违背初心

✅ 有自愈系统：
- 设置复杂度阈值（workflows≤8, BDD≤15）
- 超标时警告
- 强制简化才能继续
→ 结果：保持"个人工具"定位
```

### 9个历史问题（真实案例）

#### 1. **版本号混乱** 🔢
```
问题：
- VERSION: 6.2.0
- CLAUDE.md: 6.1.0
- README.md: 6.0.0
- package.json: 5.3.0

结果：用户困惑、CI失败、发布错误
```

#### 2. **文档泛滥** 📄
```
问题：
- docs/下有82个文档
- 15个README（README.md, README2.md, README_NEW.md...）
- 没人知道哪个是真的

结果：信息过载、到处都是过时文档
```

#### 3. **"个人工具"变成"复杂系统"** 🏢
```
问题：
- 开始是简单的AI助手
- 增加到65个BDD场景（只需15个）
- 增加到12个CI workflows（只需8个）
- 对一个人来说太复杂了

结果：失去初心、太重无法使用
```

#### 4. **备份文件堆积** 🗑️
```
问题：
- hooks.sh.backup
- hooks.sh.backup.20251010
- hooks.sh.backup.old
- hooks.sh.backup.really_old

结果：50+个备份文件堵塞仓库
```

#### 5. **CLAUDE.md太长** 📏
```
问题：
- CLAUDE.md达到1200行
- 需要5分钟阅读
- AI被过多上下文搞混

结果：违反"最多400行"规则
```

#### 6. **Git Hooks泛滥** 🪝
```
问题：
- branch_helper.sh
- branch_helper_v2.sh
- branch_helper_final.sh
- branch_helper_final_for_real.sh

结果：15个hooks，只有3个能用
```

#### 7. **定位漂移** 🏷️
```
问题：
- 文档开始说"企业级"
- 添加"团队协作"功能
- 失去"个人工具"定位

结果：使命漂移、目标用户错误
```

#### 8. **CI工作流臃肿** ⚙️
```
问题：
- 12个CI workflows运行
- 每个5分钟
- 总计：每次push 60分钟

结果：反馈慢、资源浪费
```

#### 9. **没人知道什么是真的** 🤔
```
问题：
- README声称"90个性能预算"
- 实际：30个
- 声称"100个BDD场景"
- 实际：65个

结果：信任问题、虚假宣传
```

### 没有自愈会怎样？

**第1周**：一切正常
**第2周**：版本不匹配出现，被忽略
**第3周**：又创建了5个"临时"文档
**第2个月**：50个备份文件、82个文档、15个git hooks
**第6个月**：系统无法使用，需要完全重写

**类比**：就像从不打扫的厨房。一开始只有几个脏盘子。最终，你连台面都找不到了。

### 自愈如何预防这些？

✅ **每日自动健康检查**（像清洁服务）
✅ **立即检测**（在1个盘子时发现，而不是100个）
✅ **自动修复安全问题**（把盘子放进洗碗机）
✅ **人工审查提醒**（告诉你烤箱需要修理）

---

<a name="how"></a>
## ⚙️ 它如何工作？

### 四层防御架构

就像机场安检有4个关卡：

```
┌──────────────────────────────────────────────────────────┐
│ 第1层：实时预防（值机时的安检）                         │
│ - 在创建文件前阻止错误文档                               │
│ - pre_write_document.sh hook                            │
│ - 运行：每次AI尝试创建文件时                            │
└────────────────────┬─────────────────────────────────────┘
                     │ 如果被阻止 → AI必须修复
                     ↓
┌──────────────────────────────────────────────────────────┐
│ 第2层：每日健康检查（早晨巡逻）                          │
│ - 扫描整个系统查找问题                                   │
│ - scripts/health-checker.sh                             │
│ - 运行：每天凌晨3点UTC                                   │
└────────────────────┬─────────────────────────────────────┘
                     │ 如果发现问题 → 生成报告
                     ↓
┌──────────────────────────────────────────────────────────┐
│ 第3层：自动修复（清洁工）                                │
│ - 自动修复安全问题                                       │
│ - 清理备份、归档旧文件                                   │
│ - 运行：健康检查后如果safe_mode=true                    │
└────────────────────┬─────────────────────────────────────┘
                     │ 如果是关键问题 → 生成详细报告
                     ↓
┌──────────────────────────────────────────────────────────┐
│ 第4层：警报系统（火警）                                  │
│ - 生成健康报告和趋势分析                                 │
│ - 记录历史评分追踪                                       │
│ - 运行：当健康评分 < 75/100时                            │
└──────────────────────────────────────────────────────────┘
```

### 每层做什么

#### 第1层：实时预防

**像**：夜店门口的保镖

**检查**：
- 文档是否在允许的位置创建？
- 文件名是否匹配禁止模式（*_REPORT.md）？
- 根目录限制（7个文件）是否超标？

**示例**：
```bash
AI尝试：Write → README_NEW.md
Hook说：❌ 阻止！根目录已有7个文件
AI必须：更新现有README.md或写入.temp/
```

#### 第2层：每日健康检查

**像**：医生的年度体检

**检查7个方面**：

1. **版本一致性** 🔢
   - VERSION、CLAUDE.md、package.json是否匹配？
   - README中有冲突的版本吗？

2. **文档重复** 📄
   - 根目录 ≤ 7个文件？
   - 只有1个README.md、1个CLAUDE.md？

3. **工作流数量** ⚙️
   - CI workflows ≤ 8？
   - 有禁用的workflows需要清理？

4. **BDD功能数量** 🧪
   - BDD场景 ≤ 15？
   - 总场景数量可接受？

5. **Hooks数量** 🪝
   - Claude hooks ≤ 6？
   - 有禁用的hooks（*.sh.disabled）？

6. **备份文件** 🗑️
   - 备份数量 < 3？
   - 旧备份（>7天）？

7. **配置冲突** 🏗️
   - 多个settings.json文件？
   - 冲突的.env文件？

**输出**：健康评分0-100和详细报告

#### 第3层：自动修复

**像**：睡觉时运行的智能吸尘器

**安全修复**（自动应用）：
- ✅ 删除7天前的备份
- ✅ 归档.temp/下7天前的文件
- ✅ 删除禁用的hooks（*.sh.disabled）
- ✅ 更新文档中的指标计数

**手动修复**（需要批准）：
- ⚠️ 合并重复文档
- ⚠️ 更新版本号
- ⚠️ 删除冲突配置文件

#### 第4层：警报系统

**像**：烟雾探测器

**生成报告的情况**：
- 健康评分降至75/100以下
- 超过关键阈值（如20+个workflows）
- 检测到版本不匹配
- 备份文件 > 10

**报告内容**：
- 详细健康评分
- 问题清单
- 修复建议
- 历史趋势

---

<a name="usage"></a>
## 🚀 日常使用指南

### 零配置模式（推荐）

大多数情况下，你**什么都不用做**，系统自动运行：

```bash
# 你写代码
vim src/my-feature.js

# 提交代码（自动检查）
git add .
git commit -m "feat: add new feature"
  ↓
✅ 自愈系统自动检查（<1秒）
  ├─ 版本一致性 ✅
  ├─ 文档规范 ✅
  ├─ 复杂度检查 ✅
  └─ 允许提交

# 推送代码（自动验证）
git push
  ↓
✅ GitHub CI自动运行（~2分钟）
  ├─ 9项健康检查
  ├─ 健康评分: 95/100
  └─ 通过，可以合并
```

### 手动运行健康检查

#### 快速检查（30秒）

```bash
# 运行所有健康检查
bash scripts/health-checker.sh --check

# 输出示例：
# 🏥 Health Check Mode (Read-Only)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 📦 Check 1: Version Consistency
# ℹ Master version: 6.2.0
# ✓ package.json: 6.2.0
# ✓ CLAUDE.md version references: 3 (acceptable)
# ✓ All versions consistent
#
# 📄 Check 2: Document Duplication
# ℹ Root directory: 7 .md files
# ✓ Root document count: 7 (within limit)
# ✓ Single CLAUDE.md found
#
# ...（其他检查项）
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ╔════════════════════════════════════════════╗
# ║      HEALTH CHECK SUMMARY                  ║
# ╠════════════════════════════════════════════╣
# ║  Score: 100/100 (100%)  ✓ EXCELLENT       ║
# ║                                            ║
# ║  Issues Found:   0                         ║
# ║  Fixes Applied:  0                         ║
# ╚════════════════════════════════════════════╝
```

#### 检查特定区域

```bash
# 只检查版本一致性
bash scripts/health-checker.sh --check-version

# 只检查文档重复
bash scripts/health-checker.sh --check-documents

# 只检查备份文件
bash scripts/health-checker.sh --check-backups
```

#### 自动修复

```bash
# 检查并自动修复问题
bash scripts/health-checker.sh --fix

# 输出示例：
# 🔧 Health Check & Auto-Fix Mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# ...（检查项）
#
# 🔧 Applying Automated Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 🔧 Fixing version inconsistencies...
# ✓ Updated package.json: 6.0.0 → 6.2.0
#
# 🔧 Removing forbidden keywords...
# ✓ Removed forbidden positioning keywords from CLAUDE.md
#
# 🔧 Cleaning up old backup files...
# ✓ Removed: .git/hooks/pre-commit.backup.20251001
# ✓ Removed: scripts/old-script.sh.bak
# ✓ Cleaned up 2 backup files
#
# ℹ Fixes completed. Re-checking...
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ╔════════════════════════════════════════════╗
# ║      HEALTH CHECK SUMMARY                  ║
# ╠════════════════════════════════════════════╣
# ║  Score: 100/100 (100%)  ✓ EXCELLENT       ║
# ║                                            ║
# ║  Issues Found:   0                         ║
# ║  Fixes Applied:  3                         ║
# ╚════════════════════════════════════════════╝
#
# ✓ Fixes applied:
#   • package.json version synchronized to 6.2.0
#   • Removed forbidden positioning keywords
#   • Removed 2 old backup files (>7 days)
```

#### 生成详细报告

```bash
# 生成Markdown格式的详细报告
bash scripts/health-checker.sh --report

# 报告会保存到：
# evidence/health-report-20251013-143022.md

# 查看报告
cat evidence/health-report-20251013-143022.md
```

#### 完整分析（推荐发布前）

```bash
# 检查 + 修复 + 报告（一条龙服务）
bash scripts/health-checker.sh --all

# 适用场景：
# - 发布新版本前
# - 接手他人代码后
# - 长时间未开发后重启
# - 怀疑系统状态时
```

### 理解阈值

所有阈值定义在`.claude/self-check-rules.yaml`：

```yaml
thresholds:
  max_bdd_scenarios: 15        # 更多 = 复杂度蔓延
  max_workflows: 8             # 更多 = CI臃肿
  max_claude_md_lines: 400     # 更多 = 太长
  max_claude_hooks: 6          # 更多 = hooks混乱
  max_git_hooks_backups: 2     # 更多 = 需要清理
  temp_retention_days: 7       # 7天后自动删除
  backup_retention_days: 7     # 7天后自动归档
```

**为什么是这些数字？**
- 基于"个人工具"定位
- 用实际使用模式测试
- 在功能和简单性之间平衡

### 查看健康报告

#### 最新报告

```bash
# 查看最近的健康报告
cat evidence/health-report-$(date +%Y%m%d).md
```

#### 报告格式

```markdown
# 🏥 System Health Check Report

**Date**: 2025-10-13 03:00:00 UTC
**Commit**: abc123def

## 📊 Check Results

| Check | Status | Details |
|-------|--------|---------|
| Version Consistency | ✅ Pass | All versions match 6.2.0 |
| Document Duplication | ✅ Pass | 7 files ≤ 7 limit |
| Workflow Count | ⚠️ Warning | 9 workflows > 8 limit |

## 🎯 Overall Health Score: 88/100
Status: 🟡 Good Health (Minor Issues)

## 📋 Action Items

### 🟡 Warnings (Address Soon)
- Consider consolidating workflows (9 > 8)
- Clean up backup files (4 found)

### ✅ Maintenance
- Run cleanup monthly
- Update VERSION file when releasing
```

### 查看健康趋势

```bash
# 查看历史健康评分
grep "Score:" evidence/health-report-*.md

# 输出示例：
# evidence/health-report-20251001.md:**Score**: 85/100 (85%)
# evidence/health-report-20251005.md:**Score**: 92/100 (92%)
# evidence/health-report-20251010.md:**Score**: 98/100 (98%)
# evidence/health-report-20251013.md:**Score**: 100/100 (100%)
#
# 可以看到：系统健康度在持续提升 📈
```

### 手动清理

如果健康检查建议清理：

```bash
# 清理备份文件
find . -name "*.backup" -mtime +7 -delete
find . -name "*.bak" -mtime +7 -delete

# 清理.temp/目录
find .temp/ -mtime +7 -delete

# 清理禁用的hooks
find .claude/hooks/ -name "*.disabled" -delete
```

---

<a name="dev-guide"></a>
## 👨‍💻 开发者参考

### 添加新的检查规则

#### 步骤1：编辑配置文件

```bash
vim .claude/self-check-rules.yaml
```

```yaml
# 添加新规则示例
rules:
  code_duplication:  # 新规则
    enabled: true
    severity: warning
    description: "检测代码重复（DRY原则）"
    threshold: 5  # 最多允许5行重复
    exclude_paths:
      - "test/"
      - "node_modules/"
    action: warn
```

#### 步骤2：实现检查逻辑

```bash
vim scripts/health-checker.sh
```

在文件中添加新的检查函数（参考现有的check_*函数）。

#### 步骤3：添加测试

```bash
vim test/self-healing-tests.sh
```

添加测试用例验证新规则是否正常工作。

#### 步骤4：运行测试

```bash
bash test/self-healing-tests.sh
```

### 调整阈值

#### 场景：项目成长，需要更宽松的阈值

```yaml
# 编辑 .claude/self-check-rules.yaml
rules:
  complexity_thresholds:
    enabled: true
    limits:
      workflows:
        max: 10  # 从8增加到10
        current_exception: 15  # 临时例外，2025-11-01前过期

      bdd_scenarios:
        max: 20  # 从15增加，项目大了合理
        current_exception: 35
```

⚠️ **重要提醒**：
- 阈值应该**逐步收紧**，而非放松
- 如果需要提高阈值，说明可能需要重构
- 设置`current_exception`（临时例外）+ `expires`（过期时间）
- 过期后自动失效，强制你简化系统

### 集成到CI/CD

自愈系统已经集成到GitHub Actions：
```
.github/workflows/daily-self-check.yml
```

**触发条件**：
- 每天凌晨3点（自动）
- 手动触发（workflow_dispatch）
- 可配置严格模式、问题创建等

**查看结果**：
1. GitHub仓库 → Actions标签
2. "Daily Self-Check & Auto-Healing"
3. 查看最新运行记录
4. 下载Artifacts获取详细报告

---

<a name="troubleshooting"></a>
## 🔧 故障排除

### 常见问题

#### ❌ 问题1：Pre-commit被阻止，版本号不一致

**症状**：
```bash
git commit -m "fix: bug"

❌ [CRITICAL] Version Consistency Check Failed
   VERSION: 6.2.0
   CLAUDE.md: 6.1
   package.json: 6.0.0

⛔ Commit blocked. Fix issues above and try again.
```

**解决方案**：

方案A：自动同步（推荐）
```bash
# 使用version-manager自动同步
python scripts/version-manager.py --fix

# 验证
python scripts/version-manager.py --check

# 重新提交
git add .
git commit -m "fix: bug"
```

方案B：手动修正
```bash
# 1. 检查VERSION文件
cat VERSION  # 输出: 6.2.0

# 2. 手动更新CLAUDE.md
vim CLAUDE.md
# 改为：# Claude Enhancer 6.2

# 3. 手动更新package.json
vim package.json
# 改为："version": "6.2.0"

# 4. 提交
git add .
git commit -m "fix: bug"
```

#### ❌ 问题2：CI报告复杂度超标

**症状**：
```
GitHub Actions failed ❌

⚠️ Workflow count high: 12 (threshold: 8)
⚠️ BDD feature count high: 20 (threshold: 15)
❌ Score: 75/100 (below 90, PR cannot merge)
```

**解决方案**：

步骤1：分析超标项
```bash
# 检查workflows
ls -la .github/workflows/  # 12个文件

# 检查BDD features
find acceptance/features -name "*.feature" | wc -l  # 20个
```

步骤2：简化workflows
```bash
# 合并相关workflows
# 例如：ci-test.yml + ci-lint.yml → ci-quality.yml

# 移动不常用的到archived/
mkdir -p .github/workflows/_archived
mv .github/workflows/old-*.yml .github/workflows/_archived/
```

步骤3：简化BDD场景
```bash
cd acceptance/features

# 合并冗余场景
# 删除过时场景
mkdir -p _archived
mv obsolete-*.feature _archived/
```

步骤4：重新检查
```bash
bash scripts/health-checker.sh --check
# 确保：✓ Score: 95/100
```

#### ❌ 问题3：健康检查运行失败

**症状**：`./scripts/health-checker.sh`显示错误

**可能原因**：
1. 缺少依赖（jq, bc）
2. 脚本损坏
3. 权限问题

**解决方案**：
```bash
# 安装依赖
sudo apt-get install -y jq bc

# 检查权限
chmod +x scripts/health-checker.sh

# 验证脚本完整性
bash -n scripts/health-checker.sh  # 检查语法
```

#### ❌ 问题4：每日检查未运行

**症状**：没有每天生成evidence文件

**可能原因**：
1. Workflow禁用
2. 计划表不正确
3. 分支保护阻止提交

**解决方案**：
```bash
# 检查workflow状态
gh workflow view daily-self-check.yml

# 检查workflow运行
gh run list --workflow=daily-self-check.yml

# 验证cron计划
cat .github/workflows/daily-self-check.yml | grep cron
# 应该看到：- cron: '0 3 * * *'
```

---

<a name="advanced"></a>
## 🔬 高级配置

### 自定义健康规则

编辑`.claude/self-check-rules.yaml`：

```yaml
# 添加自定义禁用关键词
forbidden_keywords:
  - "企业级"
  - "团队协作"
  - "多用户"
  - "商业部署"

# 调整你需要的阈值
thresholds:
  max_workflows: 10  # 如果你需要更多

# 禁用某些项目的自动修复
auto_fix:
  enabled: true
  safe_mode: true
  backup_before_fix: true
  exclude:
    - "version_updates"  # 不自动修复版本
```

### 集成外部工具

你可以在`scripts/health-checker.sh`中添加更多检查，如：
- ESLint代码质量
- npm audit安全扫描
- 代码重复检测

### 解读趋势数据

查看`.temp/analysis/health-history.log`：

```
2025-10-10 95 🟢
2025-10-11 92 🟢
2025-10-12 85 🟡
2025-10-13 78 🟡  ← 下降趋势！
```

**下降趋势意味着**：
- 引入新问题的速度快于修复速度
- 系统复杂性增长
- 需要干预

**行动**：
```bash
# 对比今天与7天前
bash scripts/health-checker.sh --show-trends

# 识别变化
git log --since="7 days ago" --oneline
```

---

<a name="faq"></a>
## ❓ 常见问题FAQ

### Q1: 自愈系统会自动修改我的代码吗？

**A**: 不会！自愈系统**只处理配置和元数据**，永远不会修改你的业务代码。

它只会：
- ✅ 清理备份文件（.bak, .backup）
- ✅ 删除过期临时文件（.temp/）
- ✅ 同步版本号（VERSION, package.json）
- ✅ 替换禁用关键词（文档中）
- ✅ 修复文件权限（git hooks）

它不会：
- ❌ 修改 src/ 下的代码
- ❌ 重构你的函数
- ❌ 改变业务逻辑

---

### Q2: 健康检查会影响性能吗？

**A**: 影响极小，完全可以忽略。

**pre-commit检查**：<1秒（只检查修改的文件）
**CI检查**：~2分钟（完整检查，并行运行）
**daily检查**：凌晨3点运行，不影响工作

对比：
- 传统lint: 10-30秒
- 完整测试: 5-15分钟
- 自愈检查: <1秒（本地），~2分钟（CI）

---

### Q3: 可以在旧项目中使用吗？

**A**: 可以！但需要先"体检"。

步骤：
```bash
# 1. 复制自愈系统文件
cp -r /path/to/claude-enhancer/.claude ./
cp -r /path/to/claude-enhancer/scripts/health-checker.sh ./scripts/

# 2. 安装hooks
bash .claude/install.sh

# 3. 首次检查（可能有很多问题）
bash scripts/health-checker.sh --check

# 4. 批量修复
bash scripts/health-checker.sh --fix

# 5. 手动处理剩余问题

# 6. 再次检查，目标：≥90分
bash scripts/health-checker.sh --check
```

---

### Q4: 可以禁用自愈吗？

**A**: 可以，但不推荐。

```bash
# 禁用自动修复
vim .claude/self-check-rules.yaml
# 设置：auto_fix.enabled = false

# 禁用每日workflow
mv .github/workflows/daily-self-check.yml _workflows_disabled/
```

---

### Q5: 健康检查有误报怎么办？

**A**: 健康检查可能有误报。在`.claude/self-check-rules.yaml`中调整阈值。

---

### Q6: 这要花多少钱？

**A**: GitHub Actions免费套餐包含2000分钟/月。每日检查使用~5分钟/天 = 150分钟/月。完全在免费套餐内。

---

### Q7: 可以只在本地运行吗？

**A**: 可以。只运行`./scripts/health-checker.sh`。GitHub workflow是可选的（但推荐用于持续监控）。

---

## 📊 健康评分解读

### 分数等级

```
100分  🏆 完美（Perfect）
────────────────────────────
 90-99  🟢 优秀（Excellent）
 80-89  🟡 良好（Good）
 70-79  🟠 一般（Fair）
 60-69  🔴 较差（Poor）
  <60   ⛔ 危险（Critical）
```

### 建议行动

| 分数 | 状态 | 行动 |
|------|------|------|
| ≥90 | 🟢 生产就绪 | 持续保持，定期检查 |
| 80-89 | 🟡 需要改进 | 本周内修复问题 |
| 70-79 | 🟠 风险较高 | 今天修复，暂停新功能 |
| <70 | 🔴 禁止发布 | 立即修复，回滚最近修改 |

---

## 🎓 最佳实践

### ✅ 推荐做法

1. **定期检查**（每周一次）
```bash
bash scripts/health-checker.sh --all
```

2. **发布前全面检查**
```bash
bash scripts/health-checker.sh --all
python scripts/version-manager.py --check
npm run test
```

3. **保持简单**
- 宁愿删除功能，也不要超过复杂度阈值
- "Less is more"

4. **关注趋势**
```bash
grep "Score:" evidence/health-report-*.md | tail -7
```

5. **及时修复小问题**
- 不要等到累积成大问题
- "Fix fast, fix early"

### ❌ 避免做法

1. **频繁使用 --no-verify**
```bash
# 错误示范
git commit -m "quick fix" --no-verify
git commit -m "another fix" --no-verify
# → 技术债累积，系统失控
```

2. **放松阈值**
```yaml
# 错误示范
limits:
  workflows:
    max: 20  # 从8增加到20
    # → 系统越来越复杂，违背初心
```

3. **忽略警告**
```bash
# 错误心态
⚠️ BDD features: 18 (limit: 15)
"没关系，还能用" ← 危险！
# → 3个月后变成100个feature，无法维护
```

---

## 🤝 哲学：预防胜于治疗

### 核心原则

1. **早期发现小问题**
   - 1个版本不匹配 → 容易修复
   - 5个版本不匹配 → 需要审计

2. **自动化无聊的事情**
   - 不让人数文件
   - 让脚本执行规则

3. **让规则可见**
   - 所有阈值在`.claude/self-check-rules.yaml`
   - 没有隐藏的魔法数字

4. **信任但验证**
   - AI遵守规则（信任）
   - 每日检查验证（验证）

### 为什么叫"自愈"？

**传统方法**：
- 问题出现
- 用户注意到（也许）
- 用户调查
- 用户手动修复
- 问题稍后再次出现

**自愈方法**：
- 系统自动检测问题
- 如果安全就自动修复
- 如果需要手动修复就提醒
- 系统防止复发

就像身体自动愈合小伤口，而不是需要手术治疗感染。

---

## 📚 相关文档

- **[Health Checker脚本](../scripts/health-checker.sh)** - 实现细节
- **[自检规则](../.claude/self-check-rules.yaml)** - 所有阈值和规则
- **[每日Workflow](../.github/workflows/daily-self-check.yml)** - CI自动化
- **[架构指南](../ARCHITECTURE.md#self-healing-system)** - 技术架构
- **[Version Manager](../scripts/version-manager.py)** - 版本管理工具

---

## 🎯 总结

Claude Enhancer自愈系统就像**数字健康守护者**：

```
┌─────────────────────────────────────────┐
│  🏥 自愈系统 = 预防医学                 │
│                                         │
│  不是等出问题再修（治病）              │
│  而是持续监控预防（体检）              │
│                                         │
│  ✓ 自动检测 - 找到隐患                │
│  ✓ 自动修复 - 处理小问题              │
│  ✓ 警报提醒 - 复杂问题通知人工        │
│  ✓ 健康记录 - 追踪趋势                │
│                                         │
│  结果：系统始终处于健康状态           │
└─────────────────────────────────────────┘
```

**记住这3点**：
1. 🚀 **零配置使用** - 提交代码时自动运行
2. 🔧 **遇到问题就修** - 不要跳过检查
3. 📈 **关注健康趋势** - 定期查看评分

**从今天开始**：
```bash
# 1. 安装自愈系统（如果还没有）
bash .claude/install.sh

# 2. 运行首次检查
bash scripts/health-checker.sh --check

# 3. 修复问题（如果有）
bash scripts/health-checker.sh --fix

# 4. 然后忘记它，让系统自动守护 😊
```

---

**🛡️ 记住**：自愈就像保险。你希望永远不需要它，但当你需要时，你会很高兴有它。

*最后更新：2025-10-13*
*🤖 文档生成时间: 2025-10-13*
*📦 Claude Enhancer版本: 6.2.0*
*💚 保持系统健康，代码更安心！*
