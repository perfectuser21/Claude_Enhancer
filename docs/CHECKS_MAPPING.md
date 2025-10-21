# Claude Enhancer 检查点映射表
# Checkpoint Mapping - 97 Validation Points

**版本**: 6.6.0
**生成时间**: 2025-10-20
**总检查点**: 97个
**质量门禁**: 2个（Phase 3, Phase 4）
**硬性阻止**: 8个

---

## 📊 检查点分布总览

| Phase | 名称 | 检查点数 | 质量门禁 | 硬性阻止 |
|-------|------|---------|---------|---------|
| Phase 1 | Discovery & Planning | 33 | - | 1 |
| Phase 2 | Implementation | 15 | - | 0 |
| Phase 3 | Testing | 15 | 🔒 Gate 1 | 2 |
| Phase 4 | Review | 10 | 🔒 Gate 2 | 2 |
| Phase 5 | Release | 15 | - | 2 |
| Phase 6 | Acceptance | 5 | - | 1 |
| Phase 7 | Closure | 4 | - | 0 |
| **总计** | **7 Phases** | **97** | **2** | **8** |

---

## 🔍 详细检查点映射

### Phase 1: Discovery & Planning（探索与规划）- 33检查点

#### 1.1 Branch Check（分支前置检查）- 5检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| PD_S001 | 检查当前分支 | `git rev-parse --abbrev-ref HEAD` | ⛔ BLOCKING | 否 |
| PD_S002 | 判断是否在main/master | 字符串匹配 | ⛔ BLOCKING | 否 |
| PD_S003 | 评估分支与任务相关性 | AI语义分析 | ⚠️  WARNING | 否 |
| PD_S004 | 创建新分支（如需要） | `git checkout -b feature/xxx` | ⛔ BLOCKING | 否 |
| PD_S005 | 验证分支创建成功 | `git branch` | ⛔ BLOCKING | 否 |

**硬性阻止条件**：在main/master分支上执行Write/Edit操作

#### 1.2 Requirements Discussion（需求讨论）- 5检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P1_S001 | 需求明确性检查 | AI理解确认 | ⚠️  WARNING | 是 |
| P1_S002 | 技术可行性初评 | 经验库匹配 | ⚠️  WARNING | 是 |
| P1_S003 | 成功标准定义 | 明确验收标准 | ⚠️  WARNING | 是 |
| P1_S004 | 风险初步识别 | 关键字扫描 | ⚠️  WARNING | 是 |
| P1_S005 | 用户确认理解 | 交互确认 | ⚠️  WARNING | 是 |

#### 1.3 Technical Discovery（技术探索）- 8检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P2_S001 | P2_DISCOVERY.md存在 | `test -f docs/P2_DISCOVERY.md` | ⛔ BLOCKING | 否 |
| P2_S002 | 文档长度≥300行 | `wc -l` | ⛔ BLOCKING | 是（阈值） |
| P2_S003 | 可行性结论明确 | 包含GO/NO-GO/NEEDS-DECISION | ⛔ BLOCKING | 否 |
| P2_S004 | 技术spike验证点≥2 | 关键字匹配 | ⛔ BLOCKING | 是（阈值） |
| P2_S005 | 风险评估完整 | 包含技术/业务/时间三维度 | ⛔ BLOCKING | 否 |
| P2_S006 | ACCEPTANCE_CHECKLIST.md存在 | `test -f` | ⛔ BLOCKING | 否 |
| P2_S007 | Checklist包含验收标准 | 内容检查 | ⛔ BLOCKING | 否 |
| P2_S008 | 无TODO占位符 | `grep -r "TODO"` | ⛔ BLOCKING | 否 |

#### 1.4 Impact Assessment（影响评估）- 3检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| IA_S001 | Impact Assessment完成 | `test -f .workflow/impact_assessments/current.json` | ⚠️  WARNING | 否 |
| IA_S002 | 影响半径分数计算 | `jq .scores.impact_radius` | ⚠️  WARNING | 是（公式） |
| IA_S003 | Agent策略推荐 | `jq .agent_strategy.min_agents` | ⚠️  WARNING | 是（阈值） |

**自动化工具**：`.claude/scripts/impact_radius_assessor.sh`（<50ms，86%准确率）

#### 1.5 Architecture Planning（架构规划）- 12检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P3_S001 | PLAN.md存在 | `test -f docs/PLAN.md` | ⛔ BLOCKING | 否 |
| P3_S002 | 文档长度≥1000行 | `wc -l` | ⛔ BLOCKING | 是（阈值） |
| P3_S003 | 包含"任务清单"标题 | `grep "## 任务清单"` | ⛔ BLOCKING | 否 |
| P3_S004 | 包含"受影响文件"标题 | `grep "## 受影响文件"` | ⛔ BLOCKING | 否 |
| P3_S005 | 包含"回滚方案"标题 | `grep "## 回滚方案"` | ⛔ BLOCKING | 否 |
| P3_S006 | 任务清单≥5条 | 任务数量统计 | ⛔ BLOCKING | 是（阈值） |
| P3_S007 | 任务以动词开头 | 正则匹配 | ⚠️  WARNING | 否 |
| P3_S008 | 受影响文件为路径格式 | 路径格式验证 | ⛔ BLOCKING | 否 |
| P3_S009 | 包含架构设计 | 关键字检查 | ⚠️  WARNING | 是 |
| P3_S010 | 包含技术栈选择 | 关键字检查 | ⚠️  WARNING | 是 |
| P3_S011 | 包含风险识别 | 关键字检查 | ⚠️  WARNING | 是 |
| P3_S012 | Agent策略应用 | 匹配IA结果 | ⚠️  WARNING | 是 |

---

### Phase 2: Implementation（实现开发）- 15检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P4_S001 | 代码实现完成 | 人工验证 | ⛔ BLOCKING | 是 |
| P4_S002 | 构建/编译通过 | `npm run build` 或类似 | ⛔ BLOCKING | 是 |
| P4_S003 | 验证脚本创建 | `test -f scripts/workflow_validator_v97.sh` | ⛔ BLOCKING | 否 |
| P4_S004 | 工具脚本创建 | `test -f scripts/local_ci.sh` 等 | ⛔ BLOCKING | 否 |
| P4_S005 | Git hooks配置 | `test -x .git/hooks/pre-commit` | ⛔ BLOCKING | 否 |
| P4_S006 | CHANGELOG.md更新 | `git diff CHANGELOG.md` | ⛔ BLOCKING | 否 |
| P4_S007 | Commits规范格式 | commit message格式检查 | ⚠️  WARNING | 是 |
| P4_S008 | 不得改动非白名单目录 | 路径检查 | ⛔ BLOCKING | 是（白名单） |
| P4_S009 | Pre-write验证通过 | Hook执行结果 | ⛔ BLOCKING | 是（验证逻辑） |
| P4_S010 | 核心结构完整性验证 | `bash tools/verify-core-structure.sh` | ⛔ BLOCKING | 否 |
| P4_S011 | 7 Phases保持 | SPEC.yaml验证 | ⛔ BLOCKING | 否 |
| P4_S012 | 97 Checkpoints保持 | CHECKS_INDEX.json验证 | ⛔ BLOCKING | 否 |
| P4_S013 | 2 Quality Gates保持 | gates.yml验证 | ⛔ BLOCKING | 否 |
| P4_S014 | 8 Hard Blocks保持 | gates.yml验证 | ⛔ BLOCKING | 否 |
| P4_S015 | LOCK.json指纹匹配 | SHA256比对 | ⛔ BLOCKING | 否 |

---

### Phase 3: Testing（质量验证）- 15检查点 🔒 质量门禁1

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P5_S001 | Shell语法验证 | `bash -n *.sh` | ⛔ BLOCKING | 否 |
| P5_S002 | Shellcheck linting | `shellcheck -S warning` | ⛔ BLOCKING | 否 |
| P5_S003 | Shellcheck问题数≤277 | 计数统计（Quality Ratchet） | ⛔ BLOCKING | 是（阈值递减） |
| P5_S004 | 代码复杂度检查 | 函数行数<150 | ⛔ BLOCKING | 是（阈值） |
| P5_S005 | Hook性能测试 | 执行时间<2秒 | ⛔ BLOCKING | 是（阈值） |
| P5_S006 | 单元测试通过 | `npm test` | ⛔ BLOCKING | 是 |
| P5_S007 | 集成测试通过 | `npm run test:integration` | ⛔ BLOCKING | 是 |
| P5_S008 | BDD场景测试 | Cucumber执行 | ⚠️  WARNING | 是 |
| P5_S009 | 测试覆盖率≥70% | Coverage报告 | ⛔ BLOCKING | 是（阈值） |
| P5_S010 | 覆盖率容差±0.5% | 浮点数比较 | ⚠️  WARNING | 是（容差） |
| P5_S011 | 性能benchmark完成 | 报告存在 | ⚠️  WARNING | 是 |
| P5_S012 | 性能退化<10% | 与baseline对比 | ⛔ BLOCKING | 是（阈值） |
| P5_S013 | 敏感信息检测 | `grep -r "password\|secret\|key"` | ⛔ BLOCKING | 否 |
| P5_S014 | TEST-REPORT.md存在 | `test -f docs/TEST-REPORT.md` | ⛔ BLOCKING | 否 |
| P5_S015 | 报告包含覆盖点清单 | 内容检查 | ⛔ BLOCKING | 否 |

**强制执行脚本**：`bash scripts/static_checks.sh`（任何失败都阻止进入Phase 4）

**硬性阻止条件**：
- 语法错误
- Shellcheck警告超标

---

### Phase 4: Review（代码审查）- 10检查点 🔒 质量门禁2

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P6_S001 | REVIEW.md存在 | `test -f docs/REVIEW.md` | ⛔ BLOCKING | 否 |
| P6_S002 | 文档长度>100行 | `wc -l` | ⛔ BLOCKING | 是（阈值） |
| P6_S003 | 包含"风格一致性"章节 | `grep "风格一致性"` | ⛔ BLOCKING | 否 |
| P6_S004 | 包含"风险清单"章节 | `grep "风险清单"` | ⛔ BLOCKING | 否 |
| P6_S005 | 包含"回滚可行性"章节 | `grep "回滚可行性"` | ⛔ BLOCKING | 否 |
| P6_S006 | 审查结论明确 | 包含APPROVE或REWORK | ⛔ BLOCKING | 否 |
| P6_S007 | 无Critical安全问题 | 安全审计报告 | ⛔ BLOCKING | 否 |
| P6_S008 | 无Critical质量问题 | Pre-merge audit | ⛔ BLOCKING | 否 |
| P6_S009 | 版本完全一致性 | 5文件版本号匹配 | ⛔ BLOCKING | 否 |
| P6_S010 | Phase 1 Checklist≥90% | 完成百分比统计 | ⛔ BLOCKING | 是（阈值） |

**强制执行脚本**：`bash scripts/pre_merge_audit.sh`

**检查项包括**：
- 配置完整性（hooks注册、权限）
- 遗留问题扫描（TODO/FIXME）
- 垃圾文档检测（根目录≤7个）
- 版本完全一致性（VERSION, settings.json, package.json, manifest.yml, CHANGELOG.md）
- 代码模式一致性
- 文档完整性（REVIEW.md >3KB）

**硬性阻止条件**：
- 存在Critical安全问题
- 版本不一致

---

### Phase 5: Release（发布监控）- 15检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| P7_S001 | README.md包含"安装" | `grep "##.*安装"` | ⛔ BLOCKING | 否 |
| P7_S002 | README.md包含"使用" | `grep "##.*使用"` | ⛔ BLOCKING | 否 |
| P7_S003 | README.md包含"注意事项" | `grep "##.*注意"` | ⛔ BLOCKING | 否 |
| P7_S004 | CHANGELOG.md版本号递增 | Semver比较 | ⛔ BLOCKING | 否 |
| P7_S005 | CHANGELOG.md写明影响面 | 内容检查 | ⛔ BLOCKING | 否 |
| P7_S006 | 版本一致性（5文件） | 完全匹配 | ⛔ BLOCKING | 否 |
| P7_S007 | 根目录文档≤7个 | `find . -maxdepth 1 -name "*.md" \| wc -l` | ⛔ BLOCKING | 否 |
| P7_S008 | Phase 1 Checklist≥90% | 完成百分比 | ⛔ BLOCKING | 是（阈值） |
| P7_S009 | Git tag创建成功 | `git tag` | ⛔ BLOCKING | 否 |
| P7_S010 | Tag格式符合semver | 正则匹配 | ⛔ BLOCKING | 否 |
| P7_S011 | Release notes存在 | GitHub Releases | ⚠️  WARNING | 是 |
| P7_S012 | 部署文档更新 | 内容检查 | ⚠️  WARNING | 是 |
| P7_S013 | Post-merge healthcheck通过 | 冒烟测试 | ⛔ BLOCKING | 是 |
| P7_S014 | 健康检查失败触发回滚 | 自动回滚逻辑 | ⛔ BLOCKING | 是（触发条件） |
| P7_S015 | 回滚到上一tag成功 | `git reset --hard` | ⛔ BLOCKING | 是 |

**硬性阻止条件**：
- 根目录文档>7个（规则1强制）
- Phase 1 Checklist完成度<90%

---

### Phase 6: Acceptance（验收确认）- 5检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| AC_S001 | ACCEPTANCE_CHECKLIST.md存在 | `test -f` | ⛔ BLOCKING | 否 |
| AC_S002 | AI逐项验证所有checklist项 | AI执行 | ⛔ BLOCKING | 是 |
| AC_S003 | VERIFICATION_REPORT.md生成 | `test -f .workflow/VERIFICATION_REPORT.md` | ⛔ BLOCKING | 否 |
| AC_S004 | 验收通过率100% | 报告统计 | ⛔ BLOCKING | 否 |
| AC_S005 | 用户确认"没问题" | 交互确认 | ⛔ BLOCKING | 否 |

**硬性阻止条件**：用户未确认

**流程**：
1. AI对照Phase 1 Acceptance Checklist逐项验证
2. AI生成验收报告
3. AI说："我已完成所有验收项，请您确认"
4. 等待用户说："没问题"

---

### Phase 7: Closure（收尾合并）- 4检查点

| ID | 检查项 | 验证方法 | 严重度 | 是否可修改 |
|----|--------|----------|--------|-----------|
| CL_S001 | .temp/目录清理 | 大小<10MB | ⛔ BLOCKING | 是（阈值） |
| CL_S002 | 最终版本一致性验证 | `bash scripts/check_version_consistency.sh` | ⛔ BLOCKING | 否 |
| G002 | 根目录文档规范 | ≤7个 | ⛔ BLOCKING | 否 |
| G003 | 核心结构完整性 | `bash tools/verify-core-structure.sh` | ⛔ BLOCKING | 否 |

**强制执行脚本**：`bash scripts/check_version_consistency.sh`

**等待用户**：用户明确说"merge"才能合并到主线

---

## 🔒 质量门禁详细定义

### 🔒 Gate 1: Phase 3 Testing（技术质量门禁）

**Phase**: Phase 3
**名称**: 技术质量门禁
**描述**: 自动化测试和静态检查，确保代码质量

**强制执行**：`bash scripts/static_checks.sh`

**阻止条件**：
- 任何语法错误（bash -n失败）
- Shellcheck警告超标（>277，Quality Ratchet）
- 函数复杂度超标（>150行）
- Hook性能超标（>2秒）
- 测试覆盖率<70%

**执行模式**：硬阻止（hard blocking）- 任何失败都阻止进入Phase 4

---

### 🔒 Gate 2: Phase 4 Review（代码质量门禁）

**Phase**: Phase 4
**名称**: 代码质量门禁
**描述**: 人工审查和自动化审计，确保发布质量

**强制执行**：`bash scripts/pre_merge_audit.sh`

**阻止条件**：
- 存在Critical安全问题
- 存在Critical质量问题
- 版本不一致（5文件不匹配）
- 根目录文档>7个
- Phase 1 Checklist完成度<90%

**执行模式**：硬阻止（hard blocking）- 任何失败都阻止进入Phase 5

---

## 🚫 硬性阻止条件汇总（8个）

| Phase | 阻止条件 | 检查点ID | 严重度 |
|-------|---------|---------|--------|
| Phase 1 | 在main/master分支执行Write/Edit | PD_S001-S002 | ⛔ CRITICAL |
| Phase 3 | 语法错误 | P5_S001 | ⛔ CRITICAL |
| Phase 3 | Shellcheck警告超标 | P5_S003 | ⛔ CRITICAL |
| Phase 4 | Critical安全/质量问题 | P6_S007-S008 | ⛔ CRITICAL |
| Phase 4 | 版本不一致 | P6_S009 | ⛔ CRITICAL |
| Phase 5 | 根目录文档>7个 | P7_S007 | ⛔ CRITICAL |
| Phase 5 | Phase 1 Checklist<90% | P7_S008 | ⛔ CRITICAL |
| Phase 6 | 用户未确认 | AC_S005 | ⛔ CRITICAL |

---

## 📝 检查点修改策略

### 不可修改的检查点（核心结构）

**Layer 1: Core Immutable**
- 7 Phases结构（Phase 1-7）
- 97 Checkpoints总数
- 2 Quality Gates（Gate 1, Gate 2）
- 8 Hard Blocks

**修改要求**：
- 必须提供CHANGELOG说明
- 必须提供Impact Assessment
- 必须用户确认

---

### 可调整的检查点（阈值优化）

**Layer 2: Adjustable Thresholds**

以下阈值可以基于证据调整：
- 测试覆盖率阈值（当前70%）
- 代码复杂度阈值（当前150行）
- Hook性能阈值（当前2秒）
- Shellcheck警告阈值（当前277，只能递减）
- 文档长度阈值（P2_DISCOVERY.md >300行, PLAN.md >1000行）

**修改要求**：
- 必须提供baseline数据
- 必须更新gates.yml
- 必须提供CHANGELOG说明

---

### 自由修改的检查点（实现层）

**Layer 3: Implementation Layer**

实现逻辑可以自由修改，只要满足：
- 97个检查点全部通过
- 不降级核心结构（7/97/2/8保持）

---

## 🔧 自动化工具清单

| 工具脚本 | 用途 | 性能 | 准确率 |
|---------|-----|------|--------|
| tools/verify-core-structure.sh | 核心结构完整性验证 | <50ms | 100% |
| tools/update-lock.sh | 更新LOCK.json指纹 | <500ms | N/A |
| scripts/workflow_validator_v97.sh | 97步验证 | <5s | 95% |
| scripts/static_checks.sh | Phase 3静态检查 | <30s | 98% |
| scripts/pre_merge_audit.sh | Phase 4合并前审计 | <10s | 96% |
| scripts/check_version_consistency.sh | 5文件版本一致性 | <1s | 100% |
| .claude/scripts/impact_radius_assessor.sh | 影响半径评估 | <50ms | 86% |

---

## 📚 相关文档

- **核心规范**: `.workflow/SPEC.yaml` - 定义7 Phases/97检查点/2门禁/8阻止
- **锁定状态**: `.workflow/LOCK.json` - 文件指纹锁定
- **质量门禁**: `.workflow/gates.yml` - 7 Phases详细配置
- **检查点索引**: `docs/CHECKS_INDEX.json` - 机器可读格式
- **本文档**: `docs/CHECKS_MAPPING.md` - 人类可读映射表

---

## 🔄 更新历史

- **v6.6.0** (2025-10-20): 初始版本，7 Phases系统，97检查点
- **v6.5.1** (2025-10-15): 前代版本，8 Phases系统，95检查点

---

**维护者**: Claude Enhancer System
**更新频率**: 每次核心结构变更时同步更新
**单一事实来源**: `docs/CHECKS_INDEX.json` ← `scripts/workflow_validator_v97.sh`
