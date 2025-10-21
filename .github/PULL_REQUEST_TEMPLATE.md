# Pull Request - 7 Phases Evidence-Based Template

## 📋 Phase Information
<!-- 自动检测当前Phase -->
- **当前Phase**: <!-- TODO: Auto-detect from .phase/current -->
- **完成的Phases**:
  - [ ] Phase 1: Discovery & Planning
  - [ ] Phase 2: Implementation
  - [ ] Phase 3: Testing 🔒 Gate 1
  - [ ] Phase 4: Review 🔒 Gate 2
  - [ ] Phase 5: Release
  - [ ] Phase 6: Acceptance
  - [ ] Phase 7: Closure

## 🎯 变更描述
<!-- 简要描述本次PR的主要变更（1-3句话） -->



## 📚 必需文档证据（Required Evidence）

### Phase 1: Discovery & Planning 证据
- [ ] **P2_DISCOVERY.md**: [链接到 docs/P2_DISCOVERY.md](docs/P2_DISCOVERY.md)
  - 可行性结论：<!-- GO/NO-GO/NEEDS-DECISION -->
  - 技术spike验证点：<!-- 至少2个 -->
- [ ] **Acceptance Checklist**: [链接到 docs/ACCEPTANCE_CHECKLIST.md](docs/ACCEPTANCE_CHECKLIST.md)
  - 总项数：<!-- e.g., 52项 -->
  - 完成百分比：<!-- 必须≥90% -->
- [ ] **PLAN.md**: [链接到 docs/PLAN.md](docs/PLAN.md)
  - 任务数量：<!-- 至少5条 -->
- [ ] **Impact Assessment**: [链接到 .workflow/impact_assessments/current.json](.workflow/impact_assessments/current.json)
  - 影响半径分数：<!-- 0-100 -->
  - 推荐Agent数量：<!-- 0/3/6/8 -->
  - 风险等级：<!-- LOW/MEDIUM/HIGH/VERY-HIGH -->

### Phase 2: Implementation 证据
- [ ] **代码实现完成**：所有核心功能已实现
- [ ] **工具脚本创建**：验证脚本、工具脚本已创建
- [ ] **Git提交规范**：所有commits遵循规范格式

### Phase 3: Testing 证据 🔒 质量门禁1
- [ ] **静态检查通过**: `bash scripts/static_checks.sh` ✅
  - [ ] Shell语法验证（bash -n）
  - [ ] Shellcheck linting（0 warnings）
  - [ ] 代码复杂度检查（<150行/函数）
  - [ ] Hook性能测试（<2秒）
- [ ] **测试覆盖率**: [链接到测试报告](docs/TEST-REPORT.md)
  - 覆盖率：<!-- ≥70% -->%
- [ ] **性能benchmark**: [链接到性能报告](.temp/benchmarks/)
  - 性能退化：<!-- <10% -->%

### Phase 4: Review 证据 🔒 质量门禁2
- [ ] **代码审查完成**: [链接到 docs/REVIEW.md](docs/REVIEW.md)
  - 审查结论：<!-- APPROVE/REWORK -->
- [ ] **合并前审计通过**: `bash scripts/pre_merge_audit.sh` ✅
  - [ ] 配置完整性验证
  - [ ] 遗留问题扫描（0 TODO/FIXME）
  - [ ] 垃圾文档检测（根目录≤7个）
  - [ ] 版本完全一致性（5文件匹配）
  - [ ] 文档完整性（REVIEW.md >3KB）
- [ ] **安全审计**: [链接到安全报告](docs/SECURITY-AUDIT.md)
  - Critical问题数：<!-- 必须为0 -->

### Phase 5: Release 证据
- [ ] **文档更新**:
  - [ ] README.md（安装/使用/注意事项 三段齐全）
  - [ ] CHANGELOG.md（版本号递增+影响面）
- [ ] **版本一致性**:
  - VERSION: <!-- e.g., 6.6.0 -->
  - .claude/settings.json: <!-- 必须相同 -->
  - package.json: <!-- 必须相同 -->
  - .workflow/manifest.yml: <!-- 必须相同 -->
  - CHANGELOG.md: <!-- 必须相同 -->

### Phase 6: Acceptance 证据
- [ ] **验收报告**: [链接到 .workflow/VERIFICATION_REPORT.md](.workflow/VERIFICATION_REPORT.md)
  - 验收通过率：<!-- 必须100% -->%
- [ ] **用户确认**: 用户已确认"没问题"

### Phase 7: Closure 证据
- [ ] **.temp/清理**: .temp/目录 <!-- <10MB -->MB
- [ ] **最终版本验证**: `bash scripts/check_version_consistency.sh` ✅
- [ ] **根目录文档规范**: 文档数量 <!-- ≤7个 -->个

## 🔒 核心结构完整性验证（Lockdown Mechanism）

- [ ] **核心结构验证通过**: `bash tools/verify-core-structure.sh` ✅
  ```json
  {"ok": true, "message": "Core structure verification passed"}
  ```
- [ ] **LOCK.json状态**:
  - Lock模式：<!-- soft/strict -->
  - SPEC.yaml指纹：<!-- 匹配/不匹配 -->
  - 7 Phases：<!-- 保持 -->
  - 97 Checkpoints：<!-- 保持 -->
  - 2 Quality Gates：<!-- 保持 -->
  - 8 Hard Blocks：<!-- 保持 -->

## ✅ 质量检查清单

### 自动化检查（CI必须100%通过）
- [ ] 本地pre-commit hooks通过
- [ ] CI所有检查通过
- [ ] Shell语法验证通过（bash -n）
- [ ] Shellcheck通过（0 warnings）
- [ ] 代码复杂度检查通过
- [ ] Hook性能检查通过（<2秒）
- [ ] 测试覆盖率≥70%
- [ ] 无安全问题（无硬编码密钥/secrets）

### 文档规范（规则1强制）
- [ ] 根目录文档≤7个（README.md, CLAUDE.md, INSTALLATION.md, ARCHITECTURE.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE.md）
- [ ] 临时分析已移至.temp/（7天TTL）
- [ ] 无未授权的*_REPORT.md、*_ANALYSIS.md文件

### 版本一致性（Phase 4强制）
- [ ] VERSION文件版本号
- [ ] .claude/settings.json版本号
- [ ] package.json版本号
- [ ] .workflow/manifest.yml版本号
- [ ] CHANGELOG.md最新版本号
- [ ] **5个文件版本号完全一致** ✅

## 📊 影响评估摘要

- **影响半径分数**: <!-- e.g., 78 -->分（满分100）
- **风险等级**: <!-- LOW/MEDIUM/HIGH/VERY-HIGH -->
- **复杂度等级**: <!-- LOW/MEDIUM/HIGH -->
- **影响范围**: <!-- 文件数量、模块数量 -->
- **Agent策略**: <!-- e.g., 8 agents (very-high-risk) -->

## 🧪 测试计划

### 功能测试
<!-- 描述如何测试本次变更的核心功能 -->

### 回归测试
<!-- 描述如何确保没有破坏现有功能 -->

### 性能测试
<!-- 如果涉及性能变更，描述性能测试方法 -->

## 🔄 回滚方案（必填）

### 回滚触发条件
<!-- 什么情况下需要回滚？ -->

### 回滚步骤
1. <!-- 步骤1 -->
2. <!-- 步骤2 -->
3. <!-- 步骤3 -->

### 回滚验证
<!-- 如何验证回滚成功？ -->

## 🔗 关联Issue

Closes #
Related to #

## 📝 审查者注意事项

### 重点审查内容
<!-- 需要审查者特别关注的部分 -->

### 已知限制
<!-- 本次PR的已知限制或未解决问题 -->

### 后续计划
<!-- 本次PR之后的计划 -->

## 🤖 AI生成信息

- **使用的Agents**: <!-- e.g., backend-architect, security-auditor, test-engineer -->
- **执行模式**: <!-- 并行/顺序 -->
- **总执行时间**: <!-- e.g., 45分钟 -->
- **Impact Assessment时间**: <!-- e.g., <50ms -->

## ✍️ 额外说明

<!-- 任何需要审查者注意的额外信息 -->

---

**提交前确认**：
- [ ] 我已阅读并完成所有必需的证据项
- [ ] 所有质量检查项已通过
- [ ] 核心结构完整性验证通过
- [ ] Phase 1 Acceptance Checklist ≥90%完成
- [ ] 版本一致性验证通过
- [ ] 我理解回滚方案并确认可行

**质量门禁状态**：
- 🔒 Gate 1 (Phase 3 Testing): <!-- ✅ PASSED / ❌ FAILED -->
- 🔒 Gate 2 (Phase 4 Review): <!-- ✅ PASSED / ❌ FAILED -->
