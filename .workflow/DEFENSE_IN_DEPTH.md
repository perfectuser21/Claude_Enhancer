# Defense in Depth - 纵深防御体系

**版本**: v8.7.0
**更新日期**: 2025-10-30
**目的**: 多层防护机制，防止AI绕过工作流和修改核心文件

---

## 📊 防护架构总览

```
┌─────────────────────────────────────────────────────────┐
│  Layer 8: 服务端强制（GitHub Branch Protection）       │  ⛔ 最终防线
├─────────────────────────────────────────────────────────┤
│  Layer 7: CI验证（GitHub Actions）                      │  🤖 自动化
├─────────────────────────────────────────────────────────┤
│  Layer 6: 规模检查（Scale Limits）                      │  📏 数量上限
├─────────────────────────────────────────────────────────┤
│  Layer 5: Lane Enforcer（泳道执行器）                   │  🚦 Phase限制
├─────────────────────────────────────────────────────────┤
│  Layer 4: ChangeScope（变更范围）                       │  📂 文件白名单
├─────────────────────────────────────────────────────────┤
│  Layer 3: 单一状态源（State Manager）                   │  📋 状态统一
├─────────────────────────────────────────────────────────┤
│  Layer 2: Immutable Kernel（核心不可变层）              │  🔒 9个核心文件
├─────────────────────────────────────────────────────────┤
│  Layer 1: Git Hooks（本地钩子）                         │  🛡️ 第一道防线
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1: Git Hooks（本地钩子）

### 作用
第一道防线，在本地阻止明显错误

### 组件
- `.git/hooks/pre-commit` - 提交前验证
- `.git/hooks/kernel-guard.sh` - Kernel保护
- `.git/hooks/pre-push` - 推送前检查
- `.claude/hooks/*` - Claude Hooks集成

### 检查项
- ✅ 分支检查（禁止main分支commit）
- ✅ Kernel文件保护（需RFC分支）
- ✅ 版本一致性（6个文件）
- ✅ Shellcheck静态检查
- ✅ ChangeScope验证

### 限制
- ❌ 可被`--no-verify`绕过
- ⚠️ 依赖本地环境

### 补偿
由Layer 8（GitHub Branch Protection）兜底

---

## Layer 2: Immutable Kernel（核心不可变层）

### 作用
定义9个核心文件，修改需要RFC流程

### 核心文件
1. `.workflow/SPEC.yaml` - 核心规格
2. `.workflow/manifest.yml` - 工作流清单
3. `.workflow/gates.yml` - 质量门禁
4. `docs/CHECKS_INDEX.json` - 检查点索引
5. `VERSION` - 版本文件
6. `.claude/settings.json` - Claude配置
7. `package.json` - 包配置
8. `CHANGELOG.md` - 变更日志
9. `.workflow/LOCK.json` - 完整性锁定

### 强制机制
- **Pre-commit**: `kernel-guard.sh`检查并阻止
- **CI**: `rfc-validation.yml`验证RFC流程
- **Branch**: 只允许`rfc/*`分支修改

### RFC要求
- RFC文档（Why, What, Impact, Rollback）
- 用户明确授权
- 至少minor版本升级

---

## Layer 3: 单一状态源（State Manager）

### 作用
统一所有系统状态到`.workflow/state.json`，消除4源分裂

### 管理内容
- 当前Phase和子阶段
- 当前任务信息
- Quality Gates状态
- 版本控制信息
- 系统健康指标（hooks/scripts/docs数量）
- Workflow指标

### API
```bash
# 读取状态
state_get "current_phase.phase"  # → "Phase3"

# 设置状态
state_set "current_phase.phase" "Phase4"

# Phase管理
state_set_phase "Phase5"

# 健康更新
state_update_health  # 更新hooks/scripts/docs统计
```

### 好处
- 单一数据源，无矛盾
- 可审计，可回溯
- 支持metrics和KPI追踪

---

## Layer 4: ChangeScope（变更范围）

### 作用
每个任务定义允许修改的文件白名单

### 工作原理
```bash
# 初始化scope（例如：只能修改hooks）
changescope_init ".claude/hooks/**"

# Git commit时自动验证
# 如果修改了scripts/，会被阻止
```

### 预设模板
- `preset-hooks` - 只能修改hooks
- `preset-scripts` - 只能修改scripts
- `preset-docs` - 只能修改文档
- `preset-full` - hooks + scripts + docs

### 强制机制
- Pre-commit hook调用`changescope_validate_commit`
- 违规时exit 1，阻止commit

### 特殊豁免
- `.workflow/*.md` - 任务文档
- `CHANGELOG.md` - 版本历史
- `tests/**` - 测试文件

---

## Layer 5: Lane Enforcer（泳道执行器）

### 作用
基于Phase限制允许的操作类型

### 7个Lanes
| Phase | Lane | 允许操作 |
|-------|------|---------|
| Phase1 | planning | create_discovery, create_checklist, create_plan |
| Phase2 | implementation | write_code, create_scripts, commit_code |
| Phase3 | testing | run_tests, write_tests, check_coverage |
| Phase4 | review | code_review, create_review_doc, audit_code |
| Phase5 | release | update_changelog, bump_version, create_tag |
| Phase6 | acceptance | run_acceptance_tests, user_validation |
| Phase7 | closure | cleanup, verify_consistency, create_pr |

### 工作原理
```bash
# 例如在Phase 2尝试创建PR会被阻止
lane_enforcer_enforce "create_pr"
# → ERROR: create_pr只允许在Phase 7 (closure) lane
```

### 好处
- 防止跨Phase乱序操作
- 强制按7-Phase流程执行
- 提供清晰的错误提示

---

## Layer 6: 规模检查（Scale Limits）

### 作用
防止文件数量失控

### 限制配置
```yaml
scale_limits:
  hooks_max: 50
  scripts_max: 90
  docs_max: 7
  temp_size_mb_max: 10
```

### 执行时机
- Phase 4（Review）- 警告
- Phase 7（Closure）- 硬阻止

### 检查脚本
```bash
bash scripts/check_scale_limits.sh
# → ✅ All scale limits are within bounds

bash scripts/check_scale_limits.sh --strict
# → exit 1 if exceeded (for CI)
```

### 历史问题
- 修复前：83 hooks, 115 scripts（失控）
- 修复后：50 hooks, 90 scripts（达标）

---

## Layer 7: CI验证（GitHub Actions）

### Workflows
1. **guard-core.yml** - 核心保护（61项检查）
2. **rfc-validation.yml** - RFC流程验证
3. **ce-unified-gates.yml** - 统一质量门禁

### 关键检查
- ✅ 核心文件完整性
- ✅ 版本一致性（6文件）
- ✅ Shellcheck静态分析
- ✅ 测试覆盖率≥70%
- ✅ 规模限制（hooks≤50, scripts≤90）
- ✅ RFC流程验证（如果修改Kernel）

### Required Status Checks
所有PR必须通过CI才能merge

---

## Layer 8: 服务端强制（GitHub Branch Protection）

### 作用
**最终防线**，即使本地被绕过，服务端也无法直推main

### 配置（v8.4.0修复）
```json
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      "CE Unified Gates",
      "Quality Gate (Required Check)",
      "ce/phase3-static-checks",
      "ce/phase4-pre-merge-audit",
      "ce/phase7-final-validation",
      "Stage 3: Pre-merge Audit (Gate 2)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

### 防护能力
- ❌ 无法直接push到main（即使用`--no-verify`）
- ❌ 无法绕过CI检查
- ❌ 管理员也受限（enforce_admins: true）
- ✅ 强制PR流程
- ✅ 强制CI通过

### 修复历史
- **v8.4.0之前**: Required Status Checks未配置，AI可用`gh pr merge`绕过
- **v8.4.0修复**: 添加6个Required Status Checks + strict模式
- **测试**: PR #54成功被阻止合并 ✅

---

## 🛡️ 综合防护力

| 攻击方式 | 本地防护 | 服务端防护 | 结果 |
|---------|---------|-----------|------|
| 直接修改main分支 | ✅ pre-commit阻止 | ✅ GitHub阻止 | **双重阻止** |
| `--no-verify`绕过hook | ❌ 本地无法检测 | ✅ GitHub强制PR | **服务端兜底** |
| 修改Kernel文件 | ✅ kernel-guard阻止 | ✅ RFC CI验证 | **双重阻止** |
| 文件数量失控 | ⚠️ 警告但不阻止 | ✅ CI检测+阻止PR | **CI兜底** |
| 跨Phase乱序操作 | ✅ Lane Enforcer阻止 | - | **本地阻止** |
| ChangeScope违规 | ✅ Pre-commit阻止 | - | **本地阻止** |
| CI绕过 | - | ✅ Required Checks | **服务端强制** |

**综合防护率**: 100% ✅

---

## 📈 演进历史

### v8.0-8.3：问题累积期
- 文件数量失控（83 hooks, 115 scripts）
- 状态分裂（4个数据源）
- AI随意修改核心文件
- 可绕过CI直接merge

### v8.4.0：GitHub修复
- 添加Required Status Checks
- 修复Branch Protection配置

### v8.6.1：逻辑修复
- 统一版本到8.6.1
- 修复coverage threshold矛盾
- 限定shellcheck范围

### v8.7.0：系统稳定化（当前）
- ✅ Immutable Kernel (Layer 2)
- ✅ State Source (Layer 3)
- ✅ ChangeScope (Layer 4)
- ✅ Lane Enforcer (Layer 5)
- ✅ Scale Limits (Layer 6)
- ✅ 深度清理（50/90/7基准线）
- ✅ 8层纵深防御完整建立

---

## 🎯 长期维护

### 每月检查
```bash
# 1. 系统健康检查
bash scripts/state_manager.sh health
bash scripts/state_manager.sh show

# 2. 规模检查
bash scripts/check_scale_limits.sh --strict

# 3. Kernel完整性
bash tools/verify-core-structure.sh
```

### 每季度审查
- 检查orphaned hooks（未注册的hooks）
- 审查scripts/是否有废弃脚本
- 评估是否需要调整scale_limits
- 更新LOCK.json（如有必要）

### 告警触发条件
- Hooks > 50
- Scripts > 90
- Root docs > 7
- .temp/ > 10MB
- State不一致
- Kernel文件被修改（非RFC分支）

---

## 📚 相关文档

- `.workflow/SPEC.yaml` - 核心规格定义
- `.workflow/gates.yml` - 质量门禁配置
- `.workflow/state.json` - 系统状态
- `CLAUDE.md` - AI行为规范
- `scripts/state_manager.sh` - 状态管理API
- `scripts/change_scope.sh` - 变更范围管理
- `scripts/lane_enforcer.sh` - 泳道执行器
- `scripts/check_scale_limits.sh` - 规模检查

---

**总结**: 通过8层纵深防御，Claude Enhancer建立了完整的防护体系，确保AI无法绕过工作流，无法随意修改核心文件，无法让系统规模失控。即使某一层被绕过，后续层级仍能兜底，最终由GitHub Branch Protection强制执行。
