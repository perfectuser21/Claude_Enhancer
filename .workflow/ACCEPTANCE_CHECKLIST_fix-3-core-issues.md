# Acceptance Checklist
## 修复11个系统问题（1个CRITICAL + 3个HIGH + 4个MEDIUM + 3个LOW）

**版本**: 8.8.1 → 8.8.2
**日期**: 2025-11-01
**问题总数**: 11个（深度逻辑分析发现）

---

## ✅ 核心问题修复验收

### 问题1: Bypass Permissions失效 ✅

**验收标准**:
- [ ] 1.1 运行`bash tools/verify-bypass-permissions.sh`通过
- [ ] 1.2 全局配置`~/.claude.json`的permissions正确设置
- [ ] 1.3 项目配置`.claude/settings.json`保持不变
- [ ] 1.4 重启Claude Code后不再弹出权限提示窗口
- [ ] 1.5 Task工具可以无提示执行
- [ ] 1.6 执行`bash tools/verify-bypass-permissions.sh`输出100%通过

**测试方法**:
```bash
# 测试1: 验证配置
bash tools/verify-bypass-permissions.sh

# 测试2: 实际使用
# 重启Claude Code，观察是否弹窗
```

**证据要求**:
- 验证脚本输出截图
- Claude Code无弹窗的使用记录

---

### 🔴 问题C1: 全局配置覆盖Bypass Permissions（CRITICAL）✅

**验收标准**:
- [ ] C1.1 检查~/.claude.json的permissions字段
- [ ] C1.2 确认permissions不是null或已修复为bypassPermissions
- [ ] C1.3 重启Claude Code后不再弹出权限窗口
- [ ] C1.4 Task工具可以无提示执行
- [ ] C1.5 并行执行Task不需要授权

**测试方法**:
```bash
# 测试1: 检查全局配置
cat ~/.claude.json | jq '.permissions'

# 测试2: 实际使用
# 重启Claude Code，执行Task工具，应该不弹窗
```

**证据要求**:
- ~/.claude.json内容截图
- Task工具执行无弹窗的证据

---

### 🟠 问题H1: 并行Skill trigger配置错误（HIGH）✅

**验收标准**:
- [ ] H1.1 修改trigger为标准event（before_tool_use）或改用Hook
- [ ] H1.2 Skill在Phase 2时真正触发（有日志证据）
- [ ] H1.3 AI收到"单消息多Task"的提醒
- [ ] H1.4 AI在Phase 2使用**单个消息**调用多个Task工具
- [ ] H1.5 实际执行时间比串行快 ≥3x

**测试方法**:
```bash
# 测试1: 检查Skill trigger配置
cat .claude/skills/parallel-execution-guide.yml | grep -A5 "trigger:"

# 测试2: 进入Phase 2，检查是否收到提醒
# 观察AI输出，应该看到并行执行指南

# 测试3: 验证并行执行
# 观察AI是否在单个消息中调用多个Task
```

**证据要求**:
- Skill trigger配置代码
- AI在单个消息中调用3+个Task的证据
- 执行时间对比数据（并行 vs 串行）

---

### 🟠 问题H2: Immutable Kernel逻辑矛盾（HIGH）✅

**验收标准**:
- [ ] H2.1 重新定义immutable_kernel范围
- [ ] H2.2 只保留架构文件（SPEC.yaml, gates.yml, CHECKS_INDEX.json, PARALLEL_SUBAGENT_STRATEGY.md）
- [ ] H2.3 移出经常变动的文件（VERSION, CHANGELOG, settings.json, package.json）
- [ ] H2.4 更新SPEC.yaml的immutable_kernel定义
- [ ] H2.5 文档说明"不可变"的真实含义

**测试方法**:
```bash
# 测试: 检查immutable_kernel定义
yq '.immutable_kernel.kernel_files' .workflow/SPEC.yaml
# 应该只包含架构文件，不包含VERSION等
```

**证据要求**:
- 更新后的immutable_kernel定义
- 文档说明

---

### 🟠 问题H3: 并行限制配置冲突（HIGH）✅

**验收标准**:
- [ ] H3.1 确定Single Source of Truth（选择gates.yml或settings.json）
- [ ] H3.2 删除另一个配置源的并行限制
- [ ] H3.3 所有Phase的并行限制统一
- [ ] H3.4 文档说明配置来源
- [ ] H3.5 Phase2并行限制一致（统一为6或4）

**测试方法**:
```bash
# 测试1: 检查settings.json
jq '.parallel_execution.Phase2.max_concurrent' .claude/settings.json

# 测试2: 检查gates.yml
yq '.parallel_limits.Phase2' .workflow/gates.yml

# 两者应该一致或只有一个有配置
```

**证据要求**:
- 配置统一性验证输出

---

### 问题2: 并行执行失败 ✅

**验收标准**:
- [ ] 2.1 问题H1已修复（Skill trigger配置正确）
- [ ] 2.2 问题H3已修复（并行限制统一）
- [ ] 2.3 AI在Phase 2使用**单个消息**调用多个Task工具
- [ ] 2.4 实际执行时间比串行快 ≥3x
- [ ] 2.5 所有并行Task正确完成，无冲突

**测试方法**:
```bash
# 测试1: Skill触发
# 进入Phase 2，检查AI是否收到并行执行提醒

# 测试2: 实际并行
# 观察AI是否在单个消息中调用多个Task

# 测试3: 性能验证
# 记录并行执行时间 vs 串行执行时间
```

**证据要求**:
- AI在单个消息中调用3+个Task的代码片段
- 执行时间对比数据（并行 vs 串行）
- Task执行日志显示并发执行

---

### 问题3: Workflow Enforcement工作确认 ✅

**验收标准**:
- [ ] 3.1 `pr_creation_guard.sh`存在且可执行
- [ ] 3.2 Hook在`.claude/settings.json`的PreBash中注册
- [ ] 3.3 尝试在Phase 3创建PR被阻止（返回exit 1）
- [ ] 3.4 Phase 7时创建PR成功
- [ ] 3.5 Hook逻辑检查current_phase正确

**测试方法**:
```bash
# 测试1: Hook存在性
ls -la .claude/hooks/pr_creation_guard.sh

# 测试2: 注册验证
grep "pr_creation_guard" .claude/settings.json

# 测试3: 功能测试
# 手动设置Phase3，尝试gh pr create，应被阻止
```

**证据要求**:
- Hook文件存在性检查
- 注册验证输出
- Phase 3时PR创建被阻止的错误消息

---

## 🛡️ 保护机制完整性验收

### 检查点4: 核心保护机制未被破坏 ✅

**验收标准**:
- [ ] 4.1 运行`bash tools/verify-core-structure.sh`通过
- [ ] 4.2 所有Critical Hooks存在且可执行（5个）
- [ ] 4.3 所有Verification Tools存在（3个主要工具）
- [ ] 4.4 SPEC.yaml的immutable_kernel未被修改
- [ ] 4.5 Protection Integrity Score = 100%

**Critical Hooks清单**:
1. `pr_creation_guard.sh` - 防止Phase 7前创建PR
2. `phase_completion_validator.sh` - Phase转换验证
3. `workflow_enforcer.sh` - 7-Phase强制执行
4. `immutable_kernel_guard.sh` - 核心文件保护
5. `version_increment_enforcer.sh` - 版本号强制升级

**Verification Tools清单**:
1. `tools/verify-core-structure.sh` - 核心结构完整性
2. `tools/verify-bypass-permissions.sh` - Bypass配置验证
3. `scripts/check_version_consistency.sh` - 版本一致性

**测试方法**:
```bash
# 运行核心结构验证
bash tools/verify-core-structure.sh

# 预期输出:
# Core structure verification passed
# {"ok":true,"message":"Core structure verification passed"}
```

**证据要求**:
- verify-core-structure.sh输出100%通过
- 所有Critical Hooks文件大小 >1KB（防止被掏空）

---

### 检查点5: 增强验证功能 ✅

**验收标准**:
- [ ] 5.1 verify-core-structure.sh增加了运行时执行证据验证
- [ ] 5.2 检查Hook调用日志（.temp/*.hook.log）
- [ ] 5.3 检查Sentinel字符串完整性
- [ ] 5.4 检查Hook文件大小（防掏空）
- [ ] 5.5 新增检查通过所有测试

**测试方法**:
```bash
# 测试增强的验证功能
bash tools/verify-core-structure.sh --verbose

# 应该看到:
# - Runtime execution evidence checks
# - Sentinel string verification
# - File size checks
```

**证据要求**:
- verify-core-structure.sh代码diff显示新增检查
- 验证脚本执行日志

---

## 📝 文档和配置验收

### 检查点6: 无重复文件创建 ❌

**验收标准**:
- [ ] 6.1 **没有**创建`.workflow/PROTECTION_MANIFEST.yml`（重复SPEC.yaml）
- [ ] 6.2 **没有**创建新的`verify-protection-integrity.sh`（重复verify-core-structure.sh）
- [ ] 6.3 **没有**创建新的CI workflow（已有guard-core.yml）
- [ ] 6.4 所有改动基于现有文件的增强

**Anti-pattern检测**:
```bash
# 检查是否存在重复文件
! test -f .workflow/PROTECTION_MANIFEST.yml
! test -f tools/verify-protection-integrity.sh (如果是新创建的)
! test -f .github/workflows/verify-protection-integrity.yml (如果是新创建的)
```

**证据要求**:
- Git diff显示只修改了现有文件
- 没有新增重复功能的文件

---

### 检查点7: 版本和文档一致性 ✅

**验收标准**:
- [ ] 7.1 VERSION文件更新为8.8.2
- [ ] 7.2 所有6个版本文件一致（VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml）
- [ ] 7.3 CHANGELOG.md记录了本次修复
- [ ] 7.4 P1_DISCOVERY.md ≥300行
- [ ] 7.5 PLAN.md ≥500行

**测试方法**:
```bash
# 版本一致性检查
bash scripts/check_version_consistency.sh

# 文档大小检查
wc -l .workflow/P1_DISCOVERY_fix-3-core-issues.md
wc -l .workflow/PLAN_fix-3-core-issues.md
```

**证据要求**:
- check_version_consistency.sh输出100%通过
- 文档字数统计

---

## 🧪 质量门禁验收

### Phase 3: 静态检查 ✅

**验收标准**:
- [ ] 8.1 Shell语法验证通过（bash -n）
- [ ] 8.2 Shellcheck warnings ≤1930（基线）
- [ ] 8.3 代码复杂度检查通过
- [ ] 8.4 修改的Hook文件通过所有检查

**测试方法**:
```bash
bash scripts/static_checks.sh
```

**证据要求**:
- static_checks.sh完整输出日志

---

### Phase 4: Pre-merge Audit ✅

**验收标准**:
- [ ] 9.1 配置完整性检查通过
- [ ] 9.2 版本完全一致性检查通过（硬阻止）
- [ ] 9.3 无critical issues
- [ ] 9.4 所有12项audit检查通过
- [ ] 9.5 REVIEW.md文档完整（≥100行）

**测试方法**:
```bash
bash scripts/pre_merge_audit.sh
```

**证据要求**:
- pre_merge_audit.sh完整输出
- 所有检查项显示PASS

---

## 📊 验收总览

| 检查点 | 描述 | 优先级 | 状态 |
|--------|------|--------|------|
| 1.1-1.6 | Bypass Permissions修复 | P0 | ⏳ |
| 2.1-2.5 | 并行执行修复 | P0 | ⏳ |
| 3.1-3.5 | Workflow Enforcement确认 | P1 | ⏳ |
| 4.1-4.5 | 保护机制完整性 | P0 | ⏳ |
| 5.1-5.5 | 增强验证功能 | P1 | ⏳ |
| 6.1-6.4 | 无重复文件 | P0 | ⏳ |
| 7.1-7.5 | 版本文档一致性 | P0 | ⏳ |
| 8.1-8.4 | Phase 3静态检查 | P0 | ⏳ |
| 9.1-9.5 | Phase 4 Pre-merge Audit | P0 | ⏳ |

---

## 🟡 MEDIUM级别问题验收（可选）

### 🟡 问题M1: Hooks vs Skills功能重复

**验收标准**:
- [ ] M1.1 明确Hooks和Skills的分工
- [ ] M1.2 消除Phase 1确认的重复
- [ ] M1.3 消除Phase转换验证的重复
- [ ] M1.4 文档说明设计意图

### 🟡 问题M2: 版本文件数量不一致

**验收标准**:
- [ ] M2.1 verify-core-structure.sh加上SPEC.yaml检查（6个文件）
- [ ] M2.2 或修改文档明确为5个文件
- [ ] M2.3 文档与实现100%一致

### 🟡 问题M3: Lock模式配置过期

**验收标准**:
- [ ] M3.1 更新gates.yml为strict模式
- [ ] M3.2 标记观测期已结束
- [ ] M3.3 确认SPEC.yaml也是strict

### 🟡 问题M4: Phase状态文件分散

**验收标准**:
- [ ] M4.1 统一使用.phase/current
- [ ] M4.2 删除或软链接.workflow/steps/current
- [ ] M4.3 所有脚本读取同一文件

---

## 🟢 LOW级别问题验收（优化）

### 🟢 问题L1: Hooks性能优化

**验收标准**:
- [ ] L1.1 合并相似Hooks
- [ ] L1.2 使用缓存减少重复检查
- [ ] L1.3 总延迟<1秒

### 🟢 问题L2: pr_creation_guard防绕过

**验收标准**:
- [ ] L2.1 文档说明依赖GitHub Branch Protection
- [ ] L2.2 验证GitHub Protection配置正确

### 🟢 问题L3: Phase完成验证覆盖

**验收标准**:
- [ ] L3.1 增加Bash关键操作检查
- [ ] L3.2 验证覆盖git commit等操作

---

**总检查点**: 70+个（原39个 + 新增31个）
**必须通过**: 所有P0检查点（C1, H1-H3）
**建议通过**: MEDIUM级别问题（M1-M4）
**可选优化**: LOW级别问题（L1-L3）

---

## 🎯 最终验收标准

### 核心标准（全部必须满足）

✅ **功能修复**:
- Bypass permissions工作（不再弹窗）
- 并行执行正确（单消息多Task）
- Workflow enforcement工作（Phase 7创建PR）

✅ **质量保障**:
- Protection Integrity Score = 100%
- Static checks全部通过
- Pre-merge audit全部通过

✅ **避免退化**:
- 无重复文件创建
- 基于现有机制改进
- 版本一致性100%

---

**验收签字**: ⏳ 待Phase 6用户确认

**下一步**: 创建PLAN.md定义具体实现方案
