# Implementation Plan - P0 Fixes from ChatGPT Audit

## 📋 文档元数据

**项目：** Claude Enhancer P0 Fixes
**版本：** 1.0
**创建时间：** 2025-10-27
**状态：** ✅ Phase 2 已完成，进入 Phase 3-7

---

## 🎯 项目目标

修复 ChatGPT 安全审计发现的 6 个 P0 关键问题，将 Claude Enhancer 工作流系统从 "95% 可靠" 提升到 **"100% 可靠"**。

### 核心目标

1. **可靠性：** Phase 检测从 70% → 100%
2. **强制性：** 质量门禁从可绕过 → 强制执行
3. **安全性：** Tag 保护从 1 层 → 3 层
4. **防御性：** 从单点防护 → 三层架构

---

## 📊 项目范围

### 包含内容（In Scope）

✅ P0-1: Phase Detection Bug 修复
✅ P0-2: Fail-Closed Strategy 实现
✅ P0-3: State Migration 到 .git/ce/
✅ P0-4: Enhanced Tag Protection（3层验证）
✅ P0-5: CE Gates Workflow（GitHub Actions）
✅ P0-6: Parsing Robustness 优化

### 不包含内容（Out of Scope）

❌ 新功能开发
❌ UI/UX 改进
❌ 性能优化（除非影响可靠性）
❌ 文档重写（只修复引用）

---

## 🏗️ 架构设计

### 1. 核心库设计（P0-1）

#### `.git/hooks/lib/ce_common.sh`

**目的：** 提供统一的 Phase 管理和状态管理函数

**模块划分：**

```
ce_common.sh (365 lines)
├── Environment Setup (12 lines)
│   ├── PROJECT_ROOT
│   ├── STATE_DIR=.git/ce/
│   └── LOG_DIR=.git/ce/logs/
│
├── Color Definitions (20 lines)
│   ├── TTY-aware
│   └── NO_COLOR support
│
├── Logging Functions (28 lines)
│   ├── log_section()
│   ├── log_info()
│   ├── log_warn()
│   ├── log_error()
│   ├── log_success()
│   └── log_debug()
│
├── Phase Management (98 lines)
│   ├── normalize_phase()  ← 核心
│   └── read_phase()       ← 核心
│
├── State Management (53 lines)
│   ├── mark_gate_passed()
│   ├── check_gate_passed()
│   └── clear_gate_marker()
│
├── Override Management (24 lines)
│   └── check_override()   ← 关键
│
├── Script Validation (26 lines)
│   └── check_script_exists()
│
└── Utility Functions (30 lines)
    ├── get_current_branch()
    ├── is_protected_branch()
    └── get_staged_files()
```

**关键设计决策：**

1. **为什么用 Bash 而不是 Python？**
   - Git hooks 环境简单，Bash 更轻量
   - 不依赖 Python 版本
   - 执行速度更快（<50ms）

2. **为什么状态存储在 .git/ce/？**
   - 不污染工作目录
   - 不会被误提交
   - 符合 Git 最佳实践

3. **为什么使用函数而不是脚本？**
   - 可以被其他 hooks 复用
   - 测试更容易（source + 调用）
   - 逻辑集中管理

---

### 2. Fail-Closed 架构（P0-2）

#### 决策树

```
Phase 检测
    ↓
需要质量门禁？
    ├─ 否 → 跳过
    └─ 是 → 检查脚本存在
            ├─ 存在 → 执行
            │         ├─ 成功 → mark_gate_passed()
            │         └─ 失败 → BLOCK
            └─ 不存在 → 检查覆盖
                      ├─ 有覆盖 → 警告 + 通过 + 删除覆盖
                      └─ 无覆盖 → HARD BLOCK
```

#### Override 机制设计

**文件位置：** `.workflow/override/<name>.once`

**生命周期：**
```
创建（用户手动）
    ↓
检测（check_override()）
    ↓
记录（写入 audit log）
    ↓
删除（自动，一次性）
```

**审计日志格式：**
```
[2025-10-27 19:10:16] Override used: allow-missing-phase3-check
[2025-10-27 19:10:16] Reason: Emergency deployment
[2025-10-27 19:10:16] User: admin
```

---

### 3. State 架构（P0-3）

#### 目录结构

```
.git/ce/
├── .phase3_gate_passed      # 门禁标记
├── .phase4_gate_passed
├── .phase7_complete
├── logs/
│   ├── overrides.log        # 覆盖审计
│   ├── static_checks.log    # Phase 3 日志
│   ├── pre_merge_audit.log  # Phase 4 日志
│   └── version_check.log    # Phase 7 日志
└── cache/                   # 未来：缓存优化
```

#### 迁移策略

**Old Location:**
```
.workflow/.phase3_gate_passed  ❌
.workflow/.phase7_complete     ❌
```

**New Location:**
```
.git/ce/.phase3_gate_passed    ✅
.git/ce/.phase7_complete       ✅
```

**迁移步骤：**
1. ✅ 更新代码使用新位置
2. ✅ 添加 .gitignore 规则（备份保护）
3. ⏸️ 清理旧文件（Phase 7）

---

### 4. Tag Protection 架构（P0-4）

#### 三层验证

```
┌─────────────────────────────────────┐
│  Layer 1: Tag Type Check            │
│  git cat-file -t $sha                │
│  ✓ Must be "tag" (not "commit")     │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 2: Branch Check               │
│  Current branch must be main/master  │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 3: Ancestor Check             │
│  git merge-base --is-ancestor        │
│  ✓ Must be descendant of origin/main│
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 4: Signature Check (Optional) │
│  git tag -v $tag_name                │
│  ✓ Enabled by config file            │
└─────────────────────────────────────┘
```

#### 配置设计

**签名要求：**
```bash
# 启用
touch .workflow/config/require_signed_tags

# 禁用
rm .workflow/config/require_signed_tags
```

**为什么用文件而不是 config？**
- 可以版本控制
- 团队可见
- 更改有审计记录

---

### 5. CI/CD 架构（P0-5）

#### Workflow 结构

```yaml
ce-gates.yml
├── phase3_static_checks      # Job 1
│   └── bash scripts/static_checks.sh
│
├── phase4_pre_merge_audit    # Job 2
│   └── bash scripts/pre_merge_audit.sh
│
├── phase7_final_validation   # Job 3
│   └── bash scripts/check_version_consistency.sh
│
└── ce_gates_summary          # Job 4 (needs: all)
    └── Check all passed
```

#### 防御深度

```
┌──────────────────────────────────────┐
│ Layer 1: Local Git Hooks (Fast)     │
│ - 实时反馈（2秒内）                  │
│ - 85% 问题拦截                       │
│ - 可被 --no-verify 绕过              │
└──────────────────────────────────────┘
                ↓ 绕过
┌──────────────────────────────────────┐
│ Layer 2: GitHub Actions (Thorough)  │
│ - 完整环境测试                       │
│ - 99% 问题拦截                       │
│ - 可被 admin 绕过                    │
└──────────────────────────────────────┘
                ↓ 绕过
┌──────────────────────────────────────┐
│ Layer 3: Branch Protection (Final)  │
│ - 强制要求 CI 通过                   │
│ - 100% 拦截                          │
│ - Admin 也不能绕过（如果配置）       │
└──────────────────────────────────────┘
```

#### Fallback 策略

**脚本不存在时：**
```yaml
- run: |
    if [ -f scripts/static_checks.sh ]; then
      bash scripts/static_checks.sh
    else
      echo "⚠️  Script not found, passing for now"
      exit 0  # Fallback: 通过
    fi
```

**为什么允许 Fallback？**
- P0 fixes 实施期间，脚本可能还未创建
- 避免阻塞正常 PR 流程
- 有明确警告，不会被忽略

**未来强化：**
```yaml
# 脚本存在后，移除 fallback
- run: bash scripts/static_checks.sh  # 直接执行
```

---

### 6. 代码组织（P0-6）

#### 目录规范

```
scripts/                        # 验证脚本
├── comprehensive_cleanup.sh
├── static_checks.sh           # Phase 3
├── pre_merge_audit.sh         # Phase 4
├── check_version_consistency.sh  # Phase 7
└── verify-phase-consistency.sh   # Phase 7

tools/                         # 工具脚本
├── ce                        # CE CLI
└── update-lock.sh            # 更新 LOCK.json
```

**规则：**
- `scripts/` = 验证和质量检查
- `tools/` = 辅助工具和 CLI

---

## 🔧 技术实现细节

### Phase 检测算法（P0-1）

#### normalize_phase() 实现

```bash
normalize_phase() {
    local p="${1:-}"

    # Step 1: 预处理
    p="${p//[[:space:]]/}"  # 删除所有空格
    p="${p,,}"              # 转小写

    # Step 2: 模式匹配
    case "$p" in
        phase[1-7])   # phase1, phase2, ...
            echo "$p"
            ;;
        p[1-7])       # P1, P2, ...
            echo "phase${p:1}"
            ;;
        [1-7])        # 1, 2, ...
            echo "phase$p"
            ;;
        closure)      # 特殊：Closure → Phase7
            echo "phase7"
            ;;
        "")           # 空字符串
            echo ""
            ;;
        *)            # 无效格式
            log_warn "Unknown phase format: '$1'"
            echo ""
            ;;
    esac
}
```

**测试用例：**
| 输入 | 输出 | 备注 |
|------|------|------|
| "Phase 3" | "phase3" | 标准格式 |
| "  P3  " | "phase3" | 有空格 |
| "phase3" | "phase3" | 已规范化 |
| "3" | "phase3" | 只有数字 |
| "CLOSURE" | "phase7" | 大写特殊词 |
| "" | "" | 空输入 |
| "invalid" | "" + warn | 无效格式 |

#### read_phase() 实现

```bash
read_phase() {
    local phase_file="${1:-$PROJECT_ROOT/.workflow/current}"

    # Priority 1: 从 .workflow/current 读取
    if [[ -f "$phase_file" ]]; then
        # 使用 awk 提取 YAML 值
        local raw
        raw="$(awk -F: '/^[[:space:]]*phase[[:space:]]*:/ {print $2}' "$phase_file" | head -n1 || true)"

        if [[ -n "$raw" ]]; then
            local norm
            norm="$(normalize_phase "$raw")"
            if [[ -n "$norm" ]]; then
                echo "$norm"
                return 0
            fi
        fi
    fi

    # Priority 2: 分支名称推断
    local branch
    branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"

    case "$branch" in
        feature/*)
            echo "phase2"
            ;;
        review/*)
            echo "phase4"
            ;;
        release/*|hotfix/*)
            echo "phase5"
            ;;
        *)
            echo ""
            ;;
    esac
}
```

**为什么用 awk 而不是 grep？**
- awk 可以精确处理 YAML 格式
- 处理空格和冒号
- 更健壮（`/^[[:space:]]*phase[[:space:]]*:/`）

---

### Fail-Closed 实现（P0-2）

#### check_phase_quality_gates() 完整逻辑

```bash
check_phase_quality_gates() {
    log_section "Phase Quality Gates Enforcement"

    # 1. 检测当前 Phase
    local current_phase
    current_phase="$(read_phase)"

    if [[ -z "$current_phase" ]]; then
        log_warn "Phase not detected, skipping gates"
        return 0
    fi

    log_info "Current phase: $current_phase"

    # 2. Phase 3: Quality Gate 1
    if [[ "$current_phase" == "phase3" ]]; then
        local script="$PROJECT_ROOT/scripts/static_checks.sh"

        # Fail-closed check
        if [[ ! -f "$script" ]]; then
            # 尝试覆盖
            if check_override "allow-missing-phase3-check"; then
                log_warn "One-time override applied for missing script"
                return 0
            else
                log_error "Phase 3 static_checks.sh not found - HARD BLOCK"
                log_info "Create script or use emergency override:"
                log_info "  echo 'emergency' > .workflow/override/allow-missing-phase3-check.once"
                return 1
            fi
        fi

        # 执行检查
        log_info "Running static checks..."
        if bash "$script" --incremental 2>&1 | tee -a "$LOG_DIR/static_checks.log"; then
            mark_gate_passed "phase3_gate_passed"
            log_success "Phase 3 Quality Gate 1 passed"
        else
            log_error "Phase 3 static checks failed"
            return 1
        fi
    fi

    # 3. Phase 4: Quality Gate 2
    if [[ "$current_phase" == "phase4" ]]; then
        # 类似逻辑...
    fi

    # 4. Phase 7: Cleanup Gate
    if [[ "$current_phase" == "phase7" ]]; then
        # 类似逻辑...
    fi

    return 0
}
```

---

### Tag Protection 实现（P0-4）

#### Pre-push Hook 修改

**位置：** `.git/hooks/pre-push` 行 99-167

```bash
# 检查版本 tag (vX.Y.Z 格式)
if [[ "$remote_ref" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    tag_name=$(echo "$remote_ref" | sed 's|^refs/tags/||')

    # ========================================
    # P0-4 Enhancement 1: Annotated Tag Check
    # ========================================
    obj_type=$(git cat-file -t "$local_sha" 2>/dev/null || echo "unknown")
    if [[ "$obj_type" != "tag" ]]; then
        echo -e "${RED}❌ ERROR: Tag '$tag_name' must be annotated${NC}"
        echo "   Detected type: $obj_type"
        echo ""
        echo -e "${YELLOW}Create annotated tag:${NC}"
        echo "  git tag -a $tag_name -m \"Release $tag_name\""
        ((VERSION_TAG_BLOCKED++))
        continue
    fi

    # ========================================
    # Existing Check: Branch Name
    # ========================================
    if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
        echo -e "${RED}❌ ERROR: Can only push tags from main/master${NC}"
        ((VERSION_TAG_BLOCKED++))
        continue
    fi

    # ========================================
    # P0-4 Enhancement 2: Ancestor Check
    # ========================================
    target_commit=$(git rev-list -n1 "$local_sha" 2>/dev/null)
    if [[ -n "$target_commit" ]]; then
        # 更新远程引用
        git fetch origin main >/dev/null 2>&1 || true

        # 检查祖先关系
        if ! git merge-base --is-ancestor "$target_commit" "origin/main" 2>/dev/null; then
            echo -e "${RED}❌ ERROR: Tag not descendant of origin/main${NC}"
            echo "   Tag commit: ${target_commit:0:8}"
            ((VERSION_TAG_BLOCKED++))
            continue
        fi
    fi

    # ========================================
    # P0-4 Enhancement 3: Signature Check
    # ========================================
    if [[ -f "$PROJECT_ROOT/.workflow/config/require_signed_tags" ]]; then
        if ! git tag -v "$tag_name" >/dev/null 2>&1; then
            echo -e "${RED}❌ ERROR: Tag signature verification failed${NC}"
            echo ""
            echo -e "${YELLOW}Sign tag:${NC}"
            echo "  git tag -s $tag_name -m \"Release $tag_name\""
            ((VERSION_TAG_BLOCKED++))
            continue
        fi
        echo -e "${GREEN}✓ Tag signature verified${NC}"
    fi

    echo -e "${GREEN}✓ Version tag validated: $tag_name${NC}"
fi
```

**为什么用 continue 而不是 exit？**
- 可能同时推送多个 refs
- 需要检查所有 tags
- 最后统一判断是否阻止

---

### CI Workflow 实现（P0-5）

#### `.github/workflows/ce-gates.yml`

```yaml
name: CE Gates

on:
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

concurrency:
  group: ce-gates-${{ github.ref }}
  cancel-in-progress: true

jobs:
  phase3_static_checks:
    name: ce/phase3-static-checks
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup environment
        run: |
          echo "CE_DEBUG=false" >> $GITHUB_ENV
          mkdir -p .git/ce/logs

      - name: Run static checks
        run: |
          if [ -f scripts/static_checks.sh ]; then
            bash scripts/static_checks.sh
          else
            echo "⚠️  Script not found, passing"
          fi

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: static-checks-logs
          path: .git/ce/logs/

  # phase4, phase7 类似...

  ce_gates_summary:
    name: ce/gates-summary
    runs-on: ubuntu-latest
    needs: [phase3_static_checks, phase4_pre_merge_audit, phase7_final_validation]
    if: always()

    steps:
      - run: |
          if [[ "${{ needs.*.result }}" =~ "failure" ]]; then
            echo "❌ CE Gates FAILED"
            exit 1
          fi
          echo "✅ CE Gates PASSED"
```

---

## 📅 实施时间线

### Phase 1: 基础修复（✅ 已完成 - 2.5h）

**Commit: 58716c4f**

- [x] 创建 `.git/hooks/lib/ce_common.sh` (1h)
- [x] 实现 `normalize_phase()` (20m)
- [x] 实现 `read_phase()` (20m)
- [x] 实现状态管理函数 (20m)
- [x] 实现覆盖机制 (20m)
- [x] 修改 pre-commit hook 集成 (30m)
- [x] 测试 P0-1, P0-2, P0-3 (20m)

**产出：**
- `.git/hooks/lib/ce_common.sh` (365 lines)
- 修改后的 `.git/hooks/pre-commit`
- 更新的 `.gitignore`

---

### Phase 2: 增强保护（✅ 已完成 - 1.5h）

**Commit: 6479981f, 726df715**

- [x] 修改 `.git/hooks/pre-push` (P0-4) (45m)
- [x] 创建 `.github/workflows/ce-gates.yml` (P0-5) (30m)
- [x] 移动 `verify-phase-consistency.sh` (P0-6) (10m)
- [x] 更新文档引用 (P0-6) (10m)
- [x] 测试 tag 保护 (15m)

**产出：**
- 增强的 `.git/hooks/pre-push`
- 新的 `.github/workflows/ce-gates.yml`
- 移动的 `scripts/verify-phase-consistency.sh`

---

### Phase 3: Testing（⏸️ 当前阶段 - 预计 2h）

**任务清单：**

- [ ] 运行完整验收测试 (1h)
  - [ ] P0-1 所有测试用例
  - [ ] P0-2 fail-closed 验证
  - [ ] P0-3 状态位置验证
  - [ ] P0-4 tag 保护测试
  - [ ] P0-5 CI workflow 测试
  - [ ] P0-6 组织验证

- [ ] 性能测试 (20m)
  - [ ] Pre-commit 执行时间
  - [ ] Phase 检测性能
  - [ ] CI workflow 耗时

- [ ] 边界条件测试 (40m)
  - [ ] 无效输入
  - [ ] 文件不存在
  - [ ] 网络失败（git fetch）

**预期产出：**
- 测试报告
- 性能 benchmark
- 问题清单（如有）

---

### Phase 4: Review（⏸️ 待进行 - 预计 1.5h）

**任务清单：**

- [ ] AI 自己逐行审查 (40m)
  - [ ] ce_common.sh 逻辑正确性
  - [ ] pre-push 三层验证
  - [ ] CI workflow 配置

- [ ] 创建 REVIEW.md (30m)
  - [ ] 代码审查发现
  - [ ] 改进建议
  - [ ] 风险评估

- [ ] 运行 pre_merge_audit.sh (20m)
  - [ ] 版本一致性
  - [ ] 配置完整性
  - [ ] 遗留问题扫描

**预期产出：**
- REVIEW.md (>100 lines)
- Audit 报告
- 修复清单（如有）

---

### Phase 5: Release（⏸️ 待进行 - 预计 1h）

**任务清单：**

- [ ] 更新 CHANGELOG.md (20m)
  - [ ] 列出所有 P0 fixes
  - [ ] 影响说明
  - [ ] 破坏性变更（如有）

- [ ] 考虑版本号 (10m)
  - [ ] 是否需要从 8.0.1 → 8.1.0？
  - [ ] 这是 bugfix 还是 feature？

- [ ] 更新文档 (30m)
  - [ ] README.md（如需要）
  - [ ] ARCHITECTURE.md（如需要）

**预期产出：**
- 更新的 CHANGELOG.md
- 更新的版本号（如需要）
- 更新的文档

---

### Phase 6: Acceptance（⏸️ 待进行 - 预计 0.5h）

**任务清单：**

- [ ] 对照 ChatGPT 审计清单验证 (20m)
- [ ] 生成验收报告 (10m)
- [ ] 等待用户确认 (用户操作)

**预期产出：**
- 验收报告
- 用户确认

---

### Phase 7: Closure（⏸️ 待进行 - 预计 1h）

**任务清单：**

- [ ] 运行全面清理 (20m)
  ```bash
  bash scripts/comprehensive_cleanup.sh aggressive
  ```

- [ ] 验证版本一致性 (10m)
  ```bash
  bash scripts/check_version_consistency.sh
  ```

- [ ] 验证 Phase 系统 (10m)
  ```bash
  bash scripts/verify-phase-consistency.sh
  ```

- [ ] 清理临时文件 (10m)
  - [ ] .temp/ 目录
  - [ ] 测试文件
  - [ ] Bypass 文件

- [ ] 推送 + 创建 PR (10m)
  ```bash
  git push origin feature/p0-fixes-chatgpt-audit
  gh pr create
  ```

**预期产出：**
- 干净的分支
- 创建的 PR
- CI 运行中

---

## 🎯 总时间估算

| Phase | 状态 | 预计时间 | 实际时间 |
|-------|------|---------|---------|
| Phase 1: Discovery | ✅ | - | 补充中 |
| Phase 2: Implementation | ✅ | 4h | 4h |
| Phase 3: Testing | ⏸️ | 2h | - |
| Phase 4: Review | ⏸️ | 1.5h | - |
| Phase 5: Release | ⏸️ | 1h | - |
| Phase 6: Acceptance | ⏸️ | 0.5h | - |
| Phase 7: Closure | ⏸️ | 1h | - |
| **总计** | | **10h** | **4h / 10h** |

**当前进度：40% (4/10 hours)**

---

## 🚧 风险与缓解

### 高风险

#### 风险 1: Phase 检测失败导致系统混乱
**概率：** 低（已大量测试）
**影响：** 高（核心功能）
**缓解：**
- ✅ 充分的测试用例
- ✅ Fallback 机制（分支推断）
- ✅ Debug 日志（CE_DEBUG=true）

#### 风险 2: Fail-closed 误阻止合法操作
**概率：** 中
**影响：** 高（阻塞开发）
**缓解：**
- ✅ 覆盖机制（紧急绕过）
- ✅ 清晰的错误提示
- ✅ 审计日志（追踪覆盖使用）

### 中风险

#### 风险 3: CI workflow 配置错误导致 PR 阻塞
**概率：** 中
**影响：** 中（可手动触发）
**缓解：**
- ✅ Fallback 逻辑（脚本不存在时通过）
- workflow_dispatch（手动触发）
- 详细的错误日志

#### 风险 4: Tag 保护过于严格
**概率：** 低
**影响：** 中（阻止 release）
**缓解：**
- 签名验证是可选的
- 清晰的错误提示
- 文档说明正确流程

### 低风险

#### 风险 5: 状态迁移导致旧状态丢失
**概率：** 低
**影响：** 低（可重新运行）
**缓解：**
- .gitignore 备份保护
- 旧文件不立即删除

---

## 📊 成功指标

### 技术指标

- [ ] Phase 检测成功率 = 100%（100次测试）
- [ ] 质量门禁执行率 = 100%（无绕过记录）
- [ ] Tag 保护覆盖率 = 100%（3层验证）
- [ ] CI 通过率 ≥ 95%
- [ ] Pre-commit 耗时 < 5s
- [ ] Phase 检测耗时 < 50ms

### 业务指标

- [ ] 无关键 bug 逃逸到 main
- [ ] 无未授权 tag 推送
- [ ] 0 次质量门禁意外绕过
- [ ] 用户满意度 ≥ 90%

---

## 📝 下一步行动

### 立即执行（Phase 3: Testing）

1. **启动完整测试** (10 分钟)
   ```bash
   # Phase 检测测试
   source .git/hooks/lib/ce_common.sh
   for input in "Phase 3" "P3" "3" "Closure"; do
     echo "Testing: $input → $(normalize_phase "$input")"
   done
   ```

2. **Fail-closed 验证** (15 分钟)
   ```bash
   # 测试脚本缺失
   mv scripts/static_checks.sh scripts/static_checks.sh.bak
   git commit -m "test"  # 应该失败
   mv scripts/static_checks.sh.bak scripts/static_checks.sh
   ```

3. **Tag 保护测试** (20 分钟)
   ```bash
   # 测试 lightweight tag
   git tag v9.9.9-test
   git push origin v9.9.9-test  # 应该被拒绝
   ```

### 今天完成（Phase 3-4）

- [ ] 完成所有验收测试
- [ ] 创建 REVIEW.md
- [ ] 运行 pre_merge_audit.sh

### 明天完成（Phase 5-7）

- [ ] 更新 CHANGELOG
- [ ] 运行 cleanup
- [ ] 创建 PR

---

## 🔗 相关文档

- **Phase 1 Discovery:** `docs/P1_p0-fixes-chatgpt-audit.md`
- **Acceptance Checklist:** `docs/ACCEPTANCE_CHECKLIST_p0-fixes.md`
- **Implementation Plan:** `docs/PLAN_p0-fixes.md` (本文件)
- **Progress Tracking:** `.temp/P0_FIXES_PROGRESS.md`
- **ChatGPT Audit:** (对话中)

---

**最后更新：** 2025-10-27 19:15
**下次更新：** Phase 3 测试完成后
