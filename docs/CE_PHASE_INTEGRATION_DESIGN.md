# CE 命令 Phase 集成设计文档
> Phase 感知的智能命令系统设计

**版本**: 1.0.0
**日期**: 2025-10-09
**状态**: 设计完成，待实施

---

## 📋 目录

1. [Phase 感知设计](#1-phase-感知设计)
2. [Gate 集成策略](#2-gate-集成策略)
3. [多终端状态管理](#3-多终端状态管理)
4. [冲突检测算法](#4-冲突检测算法)
5. [自动化触发点](#5-自动化触发点)
6. [性能优化](#6-性能优化)

---

## 1. Phase 感知设计

### 1.1 Phase 状态读取机制

`ce` 命令需要从多个位置感知 Phase 状态：

```bash
# 状态源优先级（从高到低）
1. .phase/current          # 主状态文件（单行，如 "P1"）
2. .workflow/ACTIVE        # YAML格式，包含phase/ticket/started_at
3. .gates/*.ok             # Gate通过标记（如 00.ok, 01.ok）
```

**实现函数**:
```bash
#!/bin/bash
# ce-phase-reader.sh - Phase状态读取器

# 主函数：获取当前Phase
ce_get_current_phase() {
    local phase=""

    # 优先级1: .phase/current
    if [[ -f ".phase/current" ]]; then
        phase=$(tr -d '\n\r' < .phase/current)
        if [[ "$phase" =~ ^P[0-7]$ ]]; then
            echo "$phase"
            return 0
        fi
    fi

    # 优先级2: .workflow/ACTIVE
    if [[ -f ".workflow/ACTIVE" ]]; then
        phase=$(grep "^phase:" .workflow/ACTIVE 2>/dev/null | awk '{print $2}' | tr -d '\n\r')
        if [[ "$phase" =~ ^P[0-7]$ ]]; then
            echo "$phase"
            return 0
        fi
    fi

    # 优先级3: 从gates推断
    local latest_gate=$(ls -t .gates/*.ok 2>/dev/null | head -1)
    if [[ -n "$latest_gate" ]]; then
        local gate_num=$(basename "$latest_gate" .ok)
        echo "P$((gate_num + 1))"
        return 0
    fi

    # 默认P0
    echo "P0"
}

# 获取Phase详细信息
ce_get_phase_info() {
    local phase="$1"

    # 从gates.yml读取Phase定义
    python3 << EOF
import yaml
import sys

try:
    with open(".workflow/gates.yml", 'r') as f:
        data = yaml.safe_load(f)

    phase_data = data.get('phases', {}).get('${phase}', {})

    print(f"name: {phase_data.get('name', 'Unknown')}")
    print(f"allow_paths: {','.join(phase_data.get('allow_paths', []))}")
    print(f"gates_count: {len(phase_data.get('gates', []))}")
    print(f"must_produce_count: {len(phase_data.get('must_produce', []))}")

except Exception as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# 验证Phase转换合法性
ce_validate_phase_transition() {
    local from_phase="$1"
    local to_phase="$2"

    # Phase顺序定义
    local phase_order="P0 P1 P2 P3 P4 P5 P6 P7"

    # 提取数字
    local from_num="${from_phase#P}"
    local to_num="${to_phase#P}"

    # 规则1: 只能前进（允许+1）或跳转到任意阶段（手动操作）
    if [[ "$to_num" -eq $((from_num + 1)) ]]; then
        echo "SEQUENTIAL"  # 顺序推进
        return 0
    elif [[ "$to_num" -gt "$from_num" ]]; then
        echo "SKIP_AHEAD"  # 跳跃前进（需警告）
        return 0
    elif [[ "$to_num" -lt "$from_num" ]]; then
        echo "ROLLBACK"    # 回滚（需确认）
        return 0
    else
        echo "SAME"        # 相同阶段
        return 1
    fi
}
```

### 1.2 Phase 感知行为调整

不同 Phase 下 `ce` 命令的行为差异：

```bash
#!/bin/bash
# ce-phase-behavior.sh - Phase感知行为适配器

ce_adapt_command_to_phase() {
    local command="$1"
    local current_phase="$2"

    case "$command" in
        start)
            ce_start_behavior "$current_phase"
            ;;
        validate)
            ce_validate_behavior "$current_phase"
            ;;
        next)
            ce_next_behavior "$current_phase"
            ;;
        publish)
            ce_publish_behavior "$current_phase"
            ;;
    esac
}

# ce start <feature> 的Phase感知行为
ce_start_behavior() {
    local phase="$1"

    case "$phase" in
        P0)
            echo "❌ Cannot start feature in P0 Discovery phase"
            echo "   P0 is for technical spike and feasibility validation"
            echo ""
            echo "📋 Suggested actions:"
            echo "   1. Complete discovery document: docs/P0_*_DISCOVERY.md"
            echo "   2. Run: ce validate  (to pass P0 gates)"
            echo "   3. Run: ce next      (to enter P1 Planning)"
            return 1
            ;;
        P1)
            echo "✅ Perfect timing! P1 is ideal for starting new features"
            echo "   Creating feature branch with P1 context..."
            return 0
            ;;
        P2|P3|P4|P5)
            echo "⚠️  Already in ${phase} - feature development in progress"
            echo "   Cannot start new feature until current phase completes"
            echo ""
            echo "📋 Options:"
            echo "   • Continue current phase work"
            echo "   • Run: ce validate  (to check progress)"
            echo "   • Run: ce next      (to advance phase)"
            return 1
            ;;
        P6|P7)
            echo "⚠️  In release/monitoring phase (${phase})"
            echo "   Finish current release before starting new feature"
            echo ""
            echo "📋 Suggested actions:"
            echo "   1. Complete current release"
            echo "   2. Run: ce next  (to complete cycle)"
            echo "   3. Then: ce start <new-feature>"
            return 1
            ;;
    esac
}

# ce validate 的Phase感知行为
ce_validate_behavior() {
    local phase="$1"

    echo "🔍 Validating Phase ${phase} gates..."
    echo ""

    # 调用对应Phase的验证脚本
    case "$phase" in
        P0)
            validate_p0_gates
            ;;
        P1)
            validate_p1_gates
            ;;
        P2)
            validate_p2_gates
            ;;
        P3)
            validate_p3_gates
            ;;
        P4)
            validate_p4_gates
            ;;
        P5)
            validate_p5_gates
            ;;
        P6)
            validate_p6_gates
            ;;
        P7)
            validate_p7_gates
            ;;
    esac
}

# ce next 的Phase感知行为
ce_next_behavior() {
    local phase="$1"
    local phase_num="${phase#P}"
    local next_phase="P$((phase_num + 1))"

    # 检查是否已到达最后阶段
    if [[ "$phase_num" -ge 7 ]]; then
        echo "🎉 Congratulations! Already at final phase (P7)"
        echo "   System is in production monitoring state"
        echo ""
        echo "📋 Next steps:"
        echo "   • Monitor SLO metrics"
        echo "   • Start new feature: ce start <feature>"
        return 0
    fi

    # 验证当前Phase
    echo "🔍 Validating current phase (${phase}) before transition..."
    if ce validate; then
        echo "✅ ${phase} gates passed!"
        echo "🚀 Advancing to ${next_phase}..."

        # 自动切换（通过gates.yml的on_pass机制）
        .workflow/executor.sh next
    else
        echo "❌ ${phase} gates failed"
        echo "   Cannot advance to next phase"
        echo ""
        echo "📋 Fix issues and try again:"
        echo "   ce validate    # Check what's failing"
        echo "   ce next        # Retry after fixes"
        return 1
    fi
}

# ce publish 的Phase感知行为
ce_publish_behavior() {
    local phase="$1"

    case "$phase" in
        P0|P1|P2|P3|P4|P5)
            echo "⚠️  Cannot publish in ${phase}"
            echo "   Publishing is only available in P6 (Release) phase"
            echo ""
            echo "📋 Current phase: ${phase}"
            echo "   Need to reach P6 first"
            echo ""
            echo "🚀 Quick path to P6:"
            echo "   ce validate && ce next  # Repeat until P6"
            return 1
            ;;
        P6)
            echo "✅ Perfect! P6 is the publish phase"
            echo "🚀 Starting publish workflow..."
            ce_do_publish
            return 0
            ;;
        P7)
            echo "ℹ️  Already published and in monitoring phase"
            echo "   Feature is live in production"
            echo ""
            echo "📋 Options:"
            echo "   • Check monitoring: ce monitor"
            echo "   • Start new feature: ce start <feature>"
            return 0
            ;;
    esac
}
```

### 1.3 Phase 转换规则验证

```bash
#!/bin/bash
# ce-phase-validator.sh - Phase转换规则引擎

# Phase转换矩阵
declare -A PHASE_TRANSITION_RULES=(
    ["P0->P1"]="ALLOWED_AUTO"      # P0完成后自动进入P1
    ["P1->P2"]="ALLOWED_AUTO"      # P1完成后自动进入P2
    ["P2->P3"]="ALLOWED_AUTO"      # P2完成后自动进入P3
    ["P3->P4"]="ALLOWED_AUTO"      # P3完成后自动进入P4
    ["P4->P5"]="ALLOWED_AUTO"      # P4完成后自动进入P5
    ["P5->P6"]="ALLOWED_CONDITIONAL"  # P5需要APPROVE才能进入P6
    ["P6->P7"]="ALLOWED_AUTO"      # P6完成后自动进入P7
    ["P7->P0"]="ALLOWED_MANUAL"    # P7完成后可手动开始新循环

    # 回滚规则
    ["P1->P0"]="ALLOWED_MANUAL"    # 允许手动回滚到P0
    ["P2->P1"]="ALLOWED_MANUAL"    # 允许手动回滚到P1
    ["P3->P2"]="ALLOWED_MANUAL"    # 允许手动回滚到P2
    ["P4->P3"]="ALLOWED_MANUAL"    # 允许手动回滚到P3
    ["P5->P4"]="ALLOWED_MANUAL"    # 允许手动回滚到P4
    ["P6->P5"]="ALLOWED_MANUAL"    # 允许手动回滚到P5
)

# 验证Phase转换
ce_validate_transition() {
    local from="$1"
    local to="$2"
    local mode="${3:-auto}"  # auto | manual

    local key="${from}->${to}"
    local rule="${PHASE_TRANSITION_RULES[$key]:-FORBIDDEN}"

    case "$rule" in
        ALLOWED_AUTO)
            if [[ "$mode" == "auto" ]]; then
                return 0
            else
                echo "⚠️  Transition ${key} should be automatic"
                return 0
            fi
            ;;
        ALLOWED_CONDITIONAL)
            # 检查特殊条件（如P5的APPROVE）
            if ce_check_special_conditions "$from" "$to"; then
                return 0
            else
                echo "❌ Transition ${key} failed: conditions not met"
                return 1
            fi
            ;;
        ALLOWED_MANUAL)
            if [[ "$mode" == "manual" ]]; then
                echo "⚠️  Manual transition: ${key}"
                echo "   Confirm? (y/N)"
                read -r confirm
                [[ "$confirm" =~ ^[Yy]$ ]] && return 0 || return 1
            else
                echo "❌ Transition ${key} requires manual confirmation"
                return 1
            fi
            ;;
        FORBIDDEN)
            echo "❌ Transition ${key} is not allowed"
            return 1
            ;;
    esac
}

# 检查特殊转换条件
ce_check_special_conditions() {
    local from="$1"
    local to="$2"

    case "${from}->${to}" in
        "P5->P6")
            # 检查REVIEW.md中的APPROVE
            if [[ -f "docs/REVIEW.md" ]]; then
                if grep -q "^APPROVE" docs/REVIEW.md; then
                    return 0
                else
                    echo "❌ P5->P6 requires 'APPROVE' in docs/REVIEW.md"
                    return 1
                fi
            else
                echo "❌ P5->P6 requires docs/REVIEW.md"
                return 1
            fi
            ;;
    esac

    return 0
}
```

---

## 2. Gate 集成策略

### 2.1 Gate 验证调用机制

`ce validate` 如何调用现有的质量闸门：

```bash
#!/bin/bash
# ce-gate-integrator.sh - Gate集成器

# 主验证函数
ce_validate_gates() {
    local phase="$1"
    local mode="${2:-full}"  # full | quick | strict

    echo "🔍 Validating ${phase} gates (${mode} mode)..."
    echo ""

    # 调用executor.sh的验证引擎
    if .workflow/executor.sh validate; then
        echo "✅ All gates passed!"

        # 创建gate标记
        ce_mark_gate_passed "$phase"

        return 0
    else
        echo "❌ Gate validation failed"

        # 提供详细报告
        ce_generate_failure_report "$phase"

        return 1
    fi
}

# 快速验证（缓存优化）
ce_quick_validate() {
    local phase="$1"

    # 检查缓存
    local cache_file=".workflow/state/gates/${phase}.cache"
    if [[ -f "$cache_file" ]]; then
        local cache_age=$(($(date +%s) - $(stat -c %Y "$cache_file")))

        # 5分钟内的缓存有效
        if [[ $cache_age -lt 300 ]]; then
            echo "✅ Using cached validation result (${cache_age}s old)"
            return 0
        fi
    fi

    # 执行完整验证
    ce_validate_gates "$phase" "full"
    local result=$?

    # 更新缓存
    if [[ $result -eq 0 ]]; then
        mkdir -p "$(dirname "$cache_file")"
        date +%s > "$cache_file"
    fi

    return $result
}

# 增量验证（只检查变更文件）
ce_incremental_validate() {
    local phase="$1"

    # 获取变更文件列表
    local changed_files=$(git diff --name-only HEAD 2>/dev/null)

    if [[ -z "$changed_files" ]]; then
        echo "ℹ️  No changes detected, skipping validation"
        return 0
    fi

    echo "🔍 Incremental validation for ${phase}..."
    echo "   Changed files:"
    echo "$changed_files" | sed 's/^/     • /'
    echo ""

    # 从gates.yml读取allow_paths
    local allowed_paths=$(ce_get_phase_allowed_paths "$phase")

    # 检查所有变更文件是否在白名单内
    local violations=0
    while IFS= read -r file; do
        if ! ce_file_allowed "$file" "$allowed_paths"; then
            echo "❌ Violation: $file not in Phase ${phase} whitelist"
            ((violations++))
        fi
    done <<< "$changed_files"

    if [[ $violations -gt 0 ]]; then
        echo ""
        echo "❌ Found $violations file path violations"
        return 1
    fi

    echo "✅ All changed files pass incremental validation"
    return 0
}

# 获取Phase允许的文件路径
ce_get_phase_allowed_paths() {
    local phase="$1"

    python3 << EOF
import yaml

with open(".workflow/gates.yml", 'r') as f:
    data = yaml.safe_load(f)

allow_paths = data.get('phases', {}).get('${phase}', {}).get('allow_paths', [])
for path in allow_paths:
    print(path)
EOF
}

# 检查文件是否在允许列表
ce_file_allowed() {
    local file="$1"
    local allowed_paths="$2"

    while IFS= read -r pattern; do
        # 转换glob模式到regex
        local regex=$(echo "$pattern" | sed 's/\*\*/.*/' | sed 's/\*/[^\/]*/')

        if [[ "$file" =~ $regex ]]; then
            return 0
        fi
    done <<< "$allowed_paths"

    return 1
}

# 标记Gate通过
ce_mark_gate_passed() {
    local phase="$1"
    local phase_num="${phase#P}"

    local gate_file=".gates/${phase_num}.ok"

    # 创建.ok标记
    touch "$gate_file"

    # 生成签名（如果配置了GPG）
    if command -v gpg &> /dev/null && [[ -n "${GPG_KEY_ID:-}" ]]; then
        .workflow/scripts/sign_gate_GPG.sh "$gate_file"
    fi

    echo "✅ Gate marked as passed: $gate_file"
}

# 生成失败报告
ce_generate_failure_report() {
    local phase="$1"
    local report_file=".workflow/state/reports/${phase}_failure_$(date +%Y%m%d_%H%M%S).md"

    mkdir -p "$(dirname "$report_file")"

    cat > "$report_file" << EOF
# Phase ${phase} Validation Failure Report

**Time**: $(date)
**Branch**: $(git rev-parse --abbrev-ref HEAD)
**Commit**: $(git rev-parse HEAD)

## Failed Gates

$(ce_list_failed_gates "$phase")

## Files Changed

\`\`\`
$(git diff --name-only HEAD)
\`\`\`

## Suggested Fixes

$(ce_suggest_fixes "$phase")

EOF

    echo "📄 Failure report generated: $report_file"
}
```

### 2.2 Gate 并行检查优化

多个 gates 同时运行，提升验证速度：

```bash
#!/bin/bash
# ce-parallel-gates.sh - 并行Gate验证

# 并行验证所有gates
ce_parallel_validate() {
    local phase="$1"
    local max_parallel="${2:-4}"  # 默认4个并行

    # 从gates.yml读取gates列表
    local gates_list=()
    while IFS= read -r gate; do
        [[ -n "$gate" ]] && gates_list+=("$gate")
    done < <(ce_get_gates_for_phase "$phase")

    local total_gates=${#gates_list[@]}
    echo "🔍 Running $total_gates gates in parallel (max=$max_parallel)..."
    echo ""

    # 创建临时目录存储结果
    local temp_dir=$(mktemp -d)

    # 并行执行gates
    local pids=()
    local running=0
    local index=0

    for gate in "${gates_list[@]}"; do
        # 等待有空闲槽位
        while [[ $running -ge $max_parallel ]]; do
            for pid in "${pids[@]}"; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    wait "$pid"
                    ((running--))
                fi
            done
            sleep 0.1
        done

        # 启动gate检查
        ce_validate_single_gate "$phase" "$gate" "$temp_dir/$index" &
        pids+=($!)
        ((running++))
        ((index++))
    done

    # 等待所有gates完成
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    # 汇总结果
    local failed=0
    local passed=0

    for i in $(seq 0 $((total_gates - 1))); do
        if [[ -f "$temp_dir/$i.pass" ]]; then
            ((passed++))
        else
            ((failed++))
        fi
    done

    # 清理临时目录
    rm -rf "$temp_dir"

    echo ""
    echo "📊 Results: ${passed} passed, ${failed} failed"

    [[ $failed -eq 0 ]]
}

# 验证单个gate
ce_validate_single_gate() {
    local phase="$1"
    local gate="$2"
    local result_file="$3"

    # 这里调用executor.sh中的validate_gate_condition
    # 或直接实现gate逻辑

    if .workflow/executor.sh validate_gate_condition "$gate" "$phase"; then
        touch "${result_file}.pass"
        echo "✅ $gate"
    else
        touch "${result_file}.fail"
        echo "❌ $gate"
    fi
}
```

---

## 3. 多终端状态管理

### 3.1 状态文件结构设计

```yaml
# 目录结构
.workflow/state/
├── sessions/                    # 终端会话状态
│   ├── terminal-t1.state        # 终端1状态
│   ├── terminal-t2.state        # 终端2状态
│   └── terminal-t3.state        # 终端3状态
├── branches/                    # 分支元数据
│   ├── feature-P3-t1-login.meta
│   └── feature-P3-t2-payment.meta
├── locks/                       # 资源锁
│   ├── src-auth-login.ts.lock
│   └── docs-PLAN.md.lock
└── global.state                 # 全局状态
```

**终端状态文件格式** (`.workflow/state/sessions/terminal-t1.state`):

```yaml
# Terminal State File
terminal_id: t1
branch: feature/P3-t1-20251009-login
phase: P3
started_at: 2025-10-09T10:00:00Z
last_activity: 2025-10-09T12:30:00Z
status: active  # active | idle | stale

# Gates passed
gates_passed:
  - 00
  - 01
  - 02
  - 03

# Files modified
files_modified:
  - src/auth/login.ts
  - src/auth/session.ts
  - test/auth/login.test.ts

# File locks held
locks_held:
  - src/auth/login.ts
  - src/auth/session.ts

# Metrics
metrics:
  commits: 5
  lines_added: 234
  lines_deleted: 45
  test_runs: 12
  test_pass_rate: 100%

# Health
health:
  last_commit: 2025-10-09T12:15:00Z
  uncommitted_changes: 3
  merge_conflicts: 0
```

**分支元数据文件格式** (`.workflow/state/branches/feature-P3-t1-login.meta`):

```yaml
# Branch Metadata
branch_name: feature/P3-t1-20251009-login
terminal_id: t1
phase: P3
feature_name: login
base_branch: main
created_at: 2025-10-09T10:00:00Z
updated_at: 2025-10-09T12:30:00Z

# Phase progress
phase_progress:
  P0: completed
  P1: completed
  P2: completed
  P3: in_progress
  P4: pending
  P5: pending
  P6: pending
  P7: pending

# Quality metrics
quality:
  code_coverage: 85%
  lint_errors: 0
  test_pass_rate: 100%
  complexity_score: 7

# Dependencies
depends_on: []
blocks: []

# Conflicts
conflicts:
  with_branches: []
  with_files: []
```

**全局状态文件格式** (`.workflow/state/global.state`):

```yaml
# Global Workflow State
version: "5.3.0"
updated_at: 2025-10-09T12:30:00Z

# Active terminals
active_terminals:
  - t1
  - t2

# Active branches
active_branches:
  - feature/P3-t1-20251009-login
  - feature/P3-t2-20251009-payment

# Resource locks
resource_locks:
  "src/auth/login.ts": t1
  "src/payment/checkout.ts": t2

# Phase statistics
phase_stats:
  P0: 2 completed
  P1: 5 completed
  P2: 5 completed
  P3: 2 in_progress
  P4: 0
  P5: 0
  P6: 3 completed
  P7: 1 monitoring

# System health
system_health:
  total_branches: 2
  total_commits: 45
  avg_cycle_time: 4.5h
  gate_pass_rate: 95%
```

### 3.2 状态管理器实现

```bash
#!/bin/bash
# ce-state-manager.sh - 状态管理器

STATE_DIR=".workflow/state"
SESSIONS_DIR="$STATE_DIR/sessions"
BRANCHES_DIR="$STATE_DIR/branches"
LOCKS_DIR="$STATE_DIR/locks"
GLOBAL_STATE="$STATE_DIR/global.state"

# 初始化状态系统
ce_state_init() {
    mkdir -p "$SESSIONS_DIR" "$BRANCHES_DIR" "$LOCKS_DIR"

    if [[ ! -f "$GLOBAL_STATE" ]]; then
        cat > "$GLOBAL_STATE" << EOF
version: "5.3.0"
updated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
active_terminals: []
active_branches: []
resource_locks: {}
EOF
    fi
}

# 注册终端会话
ce_state_register_terminal() {
    local terminal_id="$1"
    local branch="$2"
    local phase="$3"

    local state_file="$SESSIONS_DIR/terminal-${terminal_id}.state"

    cat > "$state_file" << EOF
terminal_id: ${terminal_id}
branch: ${branch}
phase: ${phase}
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
last_activity: $(date -u +%Y-%m-%dT%H:%M:%SZ)
status: active
gates_passed: []
files_modified: []
locks_held: []
metrics:
  commits: 0
  lines_added: 0
  lines_deleted: 0
  test_runs: 0
  test_pass_rate: 0%
EOF

    echo "✅ Terminal ${terminal_id} registered"
}

# 更新终端活动时间
ce_state_update_activity() {
    local terminal_id="$1"
    local state_file="$SESSIONS_DIR/terminal-${terminal_id}.state"

    if [[ -f "$state_file" ]]; then
        # 使用python更新YAML（避免破坏格式）
        python3 << EOF
import yaml
from datetime import datetime

with open("${state_file}", 'r') as f:
    data = yaml.safe_load(f) or {}

data['last_activity'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
data['status'] = 'active'

with open("${state_file}", 'w') as f:
    yaml.dump(data, f, default_flow_style=False)
EOF
    fi
}

# 检测僵死终端（超过1小时无活动）
ce_state_detect_stale_terminals() {
    local stale_threshold=$((60 * 60))  # 1小时
    local current_time=$(date +%s)
    local stale_terminals=()

    for state_file in "$SESSIONS_DIR"/terminal-*.state; do
        [[ ! -f "$state_file" ]] && continue

        local last_activity=$(python3 << EOF
import yaml
from datetime import datetime

with open("${state_file}", 'r') as f:
    data = yaml.safe_load(f) or {}

last_activity = data.get('last_activity', '')
if last_activity:
    dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
    print(int(dt.timestamp()))
else:
    print(0)
EOF
)

        local age=$((current_time - last_activity))

        if [[ $age -gt $stale_threshold ]]; then
            local terminal_id=$(basename "$state_file" .state | sed 's/terminal-//')
            stale_terminals+=("$terminal_id")
        fi
    done

    if [[ ${#stale_terminals[@]} -gt 0 ]]; then
        echo "⚠️  Stale terminals detected:"
        for term in "${stale_terminals[@]}"; do
            echo "   • $term (inactive for > 1 hour)"
        done

        echo ""
        echo "🧹 Cleanup options:"
        echo "   ce state clean-stale  # Remove stale terminal states"
    fi
}

# 获取所有活跃终端
ce_state_list_active_terminals() {
    local terminals=()

    for state_file in "$SESSIONS_DIR"/terminal-*.state; do
        [[ ! -f "$state_file" ]] && continue

        local status=$(grep "^status:" "$state_file" | awk '{print $2}')

        if [[ "$status" == "active" ]]; then
            local terminal_id=$(basename "$state_file" .state | sed 's/terminal-//')
            terminals+=("$terminal_id")
        fi
    done

    printf '%s\n' "${terminals[@]}"
}

# 创建分支元数据
ce_state_create_branch_meta() {
    local branch_name="$1"
    local terminal_id="$2"
    local phase="$3"
    local feature_name="$4"

    local meta_file="$BRANCHES_DIR/${branch_name}.meta"

    cat > "$meta_file" << EOF
branch_name: ${branch_name}
terminal_id: ${terminal_id}
phase: ${phase}
feature_name: ${feature_name}
base_branch: main
created_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
updated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
phase_progress:
  P0: pending
  P1: pending
  P2: pending
  P3: pending
  P4: pending
  P5: pending
  P6: pending
  P7: pending
quality:
  code_coverage: 0%
  lint_errors: 0
  test_pass_rate: 0%
  complexity_score: 0
depends_on: []
blocks: []
conflicts:
  with_branches: []
  with_files: []
EOF

    echo "✅ Branch metadata created: $meta_file"
}
```

---

## 4. 冲突检测算法

### 4.1 文件级冲突检测

```bash
#!/bin/bash
# ce-conflict-detector.sh - 冲突检测算法

# 主冲突检测函数
ce_detect_conflicts() {
    local current_terminal="$1"

    echo "🔍 Scanning for conflicts..."
    echo ""

    # 获取当前终端修改的文件
    local current_files=$(ce_get_terminal_files "$current_terminal")

    # 扫描其他终端
    local conflicts=()
    local warnings=()

    for state_file in "$SESSIONS_DIR"/terminal-*.state; do
        [[ ! -f "$state_file" ]] && continue

        local other_terminal=$(basename "$state_file" .state | sed 's/terminal-//')

        # 跳过自己
        [[ "$other_terminal" == "$current_terminal" ]] && continue

        # 检查状态
        local other_status=$(grep "^status:" "$state_file" | awk '{print $2}')
        [[ "$other_status" != "active" ]] && continue

        # 获取对方修改的文件
        local other_files=$(ce_get_terminal_files "$other_terminal")

        # 计算交集
        local common_files=$(comm -12 <(echo "$current_files" | sort) <(echo "$other_files" | sort))

        if [[ -n "$common_files" ]]; then
            conflicts+=("$other_terminal:$common_files")
        fi
    done

    # 报告冲突
    if [[ ${#conflicts[@]} -gt 0 ]]; then
        echo "⚠️  CONFLICTS DETECTED!"
        echo ""

        for conflict in "${conflicts[@]}"; do
            local other_term="${conflict%%:*}"
            local files="${conflict#*:}"

            echo "❌ Conflict with terminal ${other_term}:"
            echo "$files" | sed 's/^/     • /'
            echo ""
        done

        # 计算冲突概率
        local conflict_prob=$(ce_calculate_conflict_probability "${conflicts[@]}")
        echo "📊 Conflict probability: ${conflict_prob}%"
        echo ""

        # 提供解决建议
        ce_suggest_conflict_resolution "$current_terminal" "${conflicts[@]}"

        return 1
    else
        echo "✅ No conflicts detected"
        return 0
    fi
}

# 获取终端修改的文件
ce_get_terminal_files() {
    local terminal_id="$1"
    local state_file="$SESSIONS_DIR/terminal-${terminal_id}.state"

    if [[ -f "$state_file" ]]; then
        python3 << EOF
import yaml

with open("${state_file}", 'r') as f:
    data = yaml.safe_load(f) or {}

files = data.get('files_modified', [])
for file in files:
    print(file)
EOF
    fi
}

# 计算冲突概率
ce_calculate_conflict_probability() {
    local conflicts=("$@")
    local total_conflicts=${#conflicts[@]}

    # 简单模型：每个冲突终端增加30%概率，上限90%
    local prob=$((total_conflicts * 30))
    [[ $prob -gt 90 ]] && prob=90

    echo "$prob"
}

# 冲突解决建议
ce_suggest_conflict_resolution() {
    local current_terminal="$1"
    shift
    local conflicts=("$@")

    echo "💡 CONFLICT RESOLUTION SUGGESTIONS"
    echo ""

    # 策略1: 按Terminal ID优先级
    local terminals=("$current_terminal")
    for conflict in "${conflicts[@]}"; do
        terminals+=("${conflict%%:*}")
    done

    local sorted_terminals=$(printf '%s\n' "${terminals[@]}" | sort | uniq)
    local first_terminal=$(echo "$sorted_terminals" | head -1)

    if [[ "$current_terminal" == "$first_terminal" ]]; then
        echo "✅ Strategy 1: PROCEED (You have priority by terminal ID)"
        echo "   Other terminals should wait for your completion"
    else
        echo "⚠️  Strategy 1: WAIT (Terminal ${first_terminal} has priority)"
        echo "   Suggestion: Pause until ${first_terminal} completes"
    fi

    echo ""

    # 策略2: 按Phase优先级
    local current_phase=$(ce_get_terminal_phase "$current_terminal")
    local other_phases=()

    for conflict in "${conflicts[@]}"; do
        local other_term="${conflict%%:*}"
        other_phases+=("$(ce_get_terminal_phase "$other_term")")
    done

    local highest_phase=$(printf '%s\n' "$current_phase" "${other_phases[@]}" | sort -r | head -1)

    if [[ "$current_phase" == "$highest_phase" ]]; then
        echo "✅ Strategy 2: PROCEED (You are in the highest phase)"
    else
        echo "⚠️  Strategy 2: WAIT (Another terminal is in phase ${highest_phase})"
    fi

    echo ""

    # 策略3: 文件分割
    echo "💡 Strategy 3: FILE PARTITIONING"
    echo "   Consider splitting work by file ownership:"

    for conflict in "${conflicts[@]}"; do
        local other_term="${conflict%%:*}"
        local files="${conflict#*:}"

        echo ""
        echo "   Terminal ${other_term} is working on:"
        echo "$files" | sed 's/^/     • /'
        echo "   → Suggestion: Work on different files or modules"
    done

    echo ""
    echo "🚀 RECOMMENDED ACTIONS:"
    echo "   1. Communicate with conflicting terminals"
    echo "   2. Coordinate merge order (lower terminal ID first)"
    echo "   3. Use file locks: ce lock <file>"
    echo "   4. Consider rebasing: ce rebase"
}

# 获取终端的Phase
ce_get_terminal_phase() {
    local terminal_id="$1"
    local state_file="$SESSIONS_DIR/terminal-${terminal_id}.state"

    if [[ -f "$state_file" ]]; then
        grep "^phase:" "$state_file" | awk '{print $2}' | tr -d '\n'
    fi
}
```

### 4.2 文件锁机制

```bash
#!/bin/bash
# ce-file-locker.sh - 文件锁管理

# 获取文件锁
ce_lock_file() {
    local file="$1"
    local terminal_id="$2"

    local lock_file="$LOCKS_DIR/$(echo "$file" | tr '/' '-').lock"

    # 检查是否已被锁定
    if [[ -f "$lock_file" ]]; then
        local lock_owner=$(cat "$lock_file")

        if [[ "$lock_owner" != "$terminal_id" ]]; then
            echo "❌ File locked by terminal ${lock_owner}: $file"
            return 1
        else
            echo "ℹ️  File already locked by you: $file"
            return 0
        fi
    fi

    # 创建锁
    echo "$terminal_id" > "$lock_file"

    # 更新终端状态
    ce_state_add_lock "$terminal_id" "$file"

    echo "🔒 File locked: $file"
}

# 释放文件锁
ce_unlock_file() {
    local file="$1"
    local terminal_id="$2"

    local lock_file="$LOCKS_DIR/$(echo "$file" | tr '/' '-').lock"

    if [[ -f "$lock_file" ]]; then
        local lock_owner=$(cat "$lock_file")

        if [[ "$lock_owner" == "$terminal_id" ]]; then
            rm -f "$lock_file"
            ce_state_remove_lock "$terminal_id" "$file"
            echo "🔓 File unlocked: $file"
        else
            echo "❌ Cannot unlock: file owned by terminal ${lock_owner}"
            return 1
        fi
    else
        echo "ℹ️  File not locked: $file"
    fi
}

# 列出所有锁
ce_list_locks() {
    echo "🔒 ACTIVE FILE LOCKS"
    echo ""

    if [[ ! -d "$LOCKS_DIR" ]] || [[ -z "$(ls -A "$LOCKS_DIR" 2>/dev/null)" ]]; then
        echo "   No active locks"
        return
    fi

    for lock_file in "$LOCKS_DIR"/*.lock; do
        [[ ! -f "$lock_file" ]] && continue

        local file=$(basename "$lock_file" .lock | tr '-' '/')
        local owner=$(cat "$lock_file")

        echo "   • $file"
        echo "     Owner: terminal $owner"
    done
}

# 清理僵死锁（对应终端不活跃）
ce_clean_stale_locks() {
    local active_terminals=$(ce_state_list_active_terminals)
    local cleaned=0

    for lock_file in "$LOCKS_DIR"/*.lock; do
        [[ ! -f "$lock_file" ]] && continue

        local owner=$(cat "$lock_file")

        if ! echo "$active_terminals" | grep -q "^${owner}$"; then
            echo "🧹 Cleaning stale lock (owner $owner inactive):"
            local file=$(basename "$lock_file" .lock | tr '-' '/')
            echo "   • $file"
            rm -f "$lock_file"
            ((cleaned++))
        fi
    done

    echo ""
    echo "✅ Cleaned $cleaned stale locks"
}
```

---

## 5. 自动化触发点

### 5.1 Phase 转换触发器

```bash
#!/bin/bash
# ce-auto-triggers.sh - 自动化触发点管理

# Phase转换监听器
ce_watch_phase_transitions() {
    local last_phase=$(ce_get_current_phase)

    while true; do
        sleep 5  # 每5秒检查一次

        local current_phase=$(ce_get_current_phase)

        if [[ "$current_phase" != "$last_phase" ]]; then
            echo "🔔 Phase transition detected: ${last_phase} → ${current_phase}"

            # 触发phase切换事件
            ce_on_phase_changed "$last_phase" "$current_phase"

            last_phase="$current_phase"
        fi
    done
}

# Phase切换事件处理
ce_on_phase_changed() {
    local from_phase="$1"
    local to_phase="$2"

    echo "🎯 Executing phase transition actions..."

    # 根据目标Phase执行相应动作
    case "$to_phase" in
        P1)
            ce_trigger_p1_actions
            ;;
        P2)
            ce_trigger_p2_actions
            ;;
        P3)
            ce_trigger_p3_actions
            ;;
        P4)
            ce_trigger_p4_actions
            ;;
        P5)
            ce_trigger_p5_actions
            ;;
        P6)
            ce_trigger_p6_actions
            ;;
        P7)
            ce_trigger_p7_actions
            ;;
    esac
}

# P3结束时自动验证
ce_trigger_p3_actions() {
    echo "🚀 P3 Implementation phase actions:"
    echo "   • Auto-validating code quality..."

    if ce validate --quick; then
        echo "   ✅ Quick validation passed"
    else
        echo "   ⚠️  Quick validation failed - manual check needed"
    fi

    echo "   • Running linters..."
    if command -v eslint &> /dev/null; then
        eslint src/ --fix || true
    fi

    echo "   • Checking uncommitted changes..."
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "   ⚠️  Uncommitted changes detected"
        echo "      Run: git add . && git commit"
    fi
}

# P4结束时自动运行测试
ce_trigger_p4_actions() {
    echo "🧪 P4 Testing phase actions:"
    echo "   • Running test suite..."

    if npm run test 2>/dev/null || python3 -m pytest 2>/dev/null; then
        echo "   ✅ Tests passed"
    else
        echo "   ❌ Tests failed - blocking phase transition"
        return 1
    fi

    echo "   • Collecting coverage report..."
    ce generate-coverage-report
}

# P6结束时自动发布
ce_trigger_p6_actions() {
    echo "🚀 P6 Release phase actions:"
    echo "   • Checking if publish is needed..."

    local current_branch=$(git rev-parse --abbrev-ref HEAD)

    if [[ "$current_branch" =~ ^feature/P6 ]]; then
        echo "   ✅ Branch ready for publish"
        echo ""
        echo "   🤖 Auto-publishing in 10 seconds..."
        echo "      (Press Ctrl+C to cancel)"

        sleep 10

        ce publish --auto
    else
        echo "   ℹ️  Not in P6 branch, skipping auto-publish"
    fi
}

# P7进入时启动监控
ce_trigger_p7_actions() {
    echo "📊 P7 Monitoring phase actions:"
    echo "   • Starting health checks..."

    if [[ -f "scripts/healthcheck.sh" ]]; then
        bash scripts/healthcheck.sh
    fi

    echo "   • Validating SLO compliance..."
    ce monitor --slo-check

    echo "   • Generating monitoring report..."
    ce monitor --report
}
```

### 5.2 文件变更触发器

```bash
#!/bin/bash
# ce-file-watcher.sh - 文件变更监听器

# 监听关键文件变化
ce_watch_files() {
    local watch_files=(
        ".phase/current"
        ".workflow/ACTIVE"
        ".gates/*.ok"
        "docs/PLAN.md"
        "docs/REVIEW.md"
    )

    echo "👀 Watching key files for changes..."

    # 使用inotifywait（Linux）或fswatch（macOS）
    if command -v inotifywait &> /dev/null; then
        inotifywait -m -e modify,create,delete \
            --format '%w%f %e' \
            "${watch_files[@]}" | \
        while read -r file event; do
            ce_on_file_changed "$file" "$event"
        done
    elif command -v fswatch &> /dev/null; then
        fswatch -0 "${watch_files[@]}" | \
        while read -r -d "" file; do
            ce_on_file_changed "$file" "MODIFY"
        done
    else
        echo "⚠️  File watcher not available (install inotifywait or fswatch)"

        # Fallback: 轮询
        ce_poll_file_changes "${watch_files[@]}"
    fi
}

# 文件变更事件处理
ce_on_file_changed() {
    local file="$1"
    local event="$2"

    case "$file" in
        *.phase/current)
            echo "🔔 Phase changed detected"
            ce_sync_phase_state
            ;;

        *.workflow/ACTIVE)
            echo "🔔 Active workflow changed"
            ce_sync_active_state
            ;;

        *.gates/*.ok)
            echo "🔔 Gate passed: $file"
            ce_update_gate_status
            ;;

        */PLAN.md)
            echo "🔔 PLAN.md updated"
            ce_validate_plan_document
            ;;

        */REVIEW.md)
            echo "🔔 REVIEW.md updated"
            ce_check_review_approval
            ;;
    esac
}

# 轮询模式（fallback）
ce_poll_file_changes() {
    local files=("$@")
    declare -A last_modified

    # 初始化时间戳
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            last_modified["$file"]=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
        fi
    done

    while true; do
        sleep 2

        for file in "${files[@]}"; do
            if [[ -f "$file" ]]; then
                local current_mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)

                if [[ "${last_modified[$file]:-0}" != "$current_mtime" ]]; then
                    ce_on_file_changed "$file" "MODIFY"
                    last_modified["$file"]="$current_mtime"
                fi
            fi
        done
    done
}
```

---

## 6. 性能优化

### 6.1 缓存系统

```bash
#!/bin/bash
# ce-cache-manager.sh - 缓存管理系统

CACHE_DIR=".workflow/cache"
CACHE_TTL=300  # 5分钟

# 初始化缓存
ce_cache_init() {
    mkdir -p "$CACHE_DIR"

    # 清理过期缓存
    find "$CACHE_DIR" -type f -mmin +5 -delete 2>/dev/null
}

# 读取缓存
ce_cache_get() {
    local key="$1"
    local cache_file="$CACHE_DIR/$(echo "$key" | md5sum | awk '{print $1}').cache"

    if [[ -f "$cache_file" ]]; then
        local cache_age=$(($(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null)))

        if [[ $cache_age -lt $CACHE_TTL ]]; then
            cat "$cache_file"
            return 0
        else
            rm -f "$cache_file"
        fi
    fi

    return 1
}

# 写入缓存
ce_cache_set() {
    local key="$1"
    local value="$2"
    local cache_file="$CACHE_DIR/$(echo "$key" | md5sum | awk '{print $1}').cache"

    echo "$value" > "$cache_file"
}

# 缓存Phase状态（避免重复读取）
ce_cache_phase_state() {
    local phase=$(ce_get_current_phase)
    ce_cache_set "current_phase" "$phase"
}

# 从缓存读取Phase
ce_cached_get_phase() {
    local cached_phase=$(ce_cache_get "current_phase")

    if [[ -n "$cached_phase" ]]; then
        echo "$cached_phase"
        return 0
    else
        # 缓存未命中，读取并缓存
        local phase=$(ce_get_current_phase)
        ce_cache_set "current_phase" "$phase"
        echo "$phase"
    fi
}

# 缓存Gate验证结果
ce_cache_gate_validation() {
    local phase="$1"
    local result="$2"  # pass | fail

    local cache_key="gate_${phase}_$(date +%Y%m%d_%H%M)"
    ce_cache_set "$cache_key" "$result"
}

# 检查Gate验证缓存
ce_cached_gate_validation() {
    local phase="$1"
    local cache_key="gate_${phase}_$(date +%Y%m%d_%H%M)"

    ce_cache_get "$cache_key"
}
```

### 6.2 增量验证优化

```bash
#!/bin/bash
# ce-incremental-validator.sh - 增量验证优化

# 增量验证（只检查变更部分）
ce_incremental_validate() {
    local phase="$1"

    # 获取变更文件
    local changed_files=$(git diff --name-only HEAD 2>/dev/null)

    if [[ -z "$changed_files" ]]; then
        echo "✅ No changes, skipping validation"
        return 0
    fi

    local changed_count=$(echo "$changed_files" | wc -l)
    echo "🔍 Incremental validation: $changed_count files changed"

    # 只对变更文件运行检查
    local failed=0

    while IFS= read -r file; do
        echo "   Checking: $file"

        # 文件级验证
        if ! ce_validate_file "$file" "$phase"; then
            ((failed++))
        fi
    done <<< "$changed_files"

    if [[ $failed -eq 0 ]]; then
        echo "✅ All changed files passed validation"
        return 0
    else
        echo "❌ $failed files failed validation"
        return 1
    fi
}

# 单文件验证
ce_validate_file() {
    local file="$1"
    local phase="$2"

    # 检查文件是否在Phase白名单
    if ! ce_file_in_phase_whitelist "$file" "$phase"; then
        echo "❌ $file: not in Phase $phase whitelist"
        return 1
    fi

    # 运行文件级linters
    case "$file" in
        *.sh)
            shellcheck "$file" 2>/dev/null || return 1
            ;;
        *.ts|*.js)
            eslint "$file" 2>/dev/null || return 1
            ;;
        *.py)
            pylint "$file" 2>/dev/null || return 1
            ;;
    esac

    return 0
}

# 检查文件是否在Phase白名单
ce_file_in_phase_whitelist() {
    local file="$1"
    local phase="$2"

    local allowed_paths=$(ce_get_phase_allowed_paths "$phase")

    while IFS= read -r pattern; do
        if [[ "$file" =~ $(echo "$pattern" | sed 's/\*\*/.*/g' | sed 's/\*/[^\/]*/g') ]]; then
            return 0
        fi
    done <<< "$allowed_paths"

    return 1
}
```

### 6.3 并行检查优化

```bash
#!/bin/bash
# ce-parallel-checker.sh - 并行检查优化

# 并行运行多个检查
ce_parallel_check() {
    local phase="$1"
    local max_parallel="${2:-$(nproc)}"  # 默认CPU核心数

    local checks=(
        "lint:Linting code"
        "type:Type checking"
        "test:Running tests"
        "security:Security scan"
    )

    echo "🚀 Running $((${#checks[@]})) checks in parallel (max=$max_parallel)..."

    local pids=()
    local results=()

    for check in "${checks[@]}"; do
        local check_type="${check%%:*}"
        local check_desc="${check#*:}"

        echo "   • $check_desc..."

        ce_run_check "$check_type" "$phase" &
        pids+=($!)
    done

    # 等待所有检查完成
    local failed=0
    for i in "${!pids[@]}"; do
        if wait "${pids[$i]}"; then
            echo "   ✅ ${checks[$i]#*:}"
        else
            echo "   ❌ ${checks[$i]#*:}"
            ((failed++))
        fi
    done

    echo ""
    echo "📊 Results: $((${#checks[@]} - failed))/${#checks[@]} passed"

    [[ $failed -eq 0 ]]
}

# 运行单个检查
ce_run_check() {
    local check_type="$1"
    local phase="$2"

    case "$check_type" in
        lint)
            ce_check_lint
            ;;
        type)
            ce_check_types
            ;;
        test)
            ce_check_tests
            ;;
        security)
            ce_check_security
            ;;
    esac
}

# Lint检查
ce_check_lint() {
    if command -v eslint &> /dev/null; then
        eslint src/ --quiet 2>/dev/null
    fi
}

# 类型检查
ce_check_types() {
    if command -v tsc &> /dev/null; then
        tsc --noEmit 2>/dev/null
    fi
}

# 测试检查
ce_check_tests() {
    if [[ -f "package.json" ]]; then
        npm run test -- --silent 2>/dev/null
    fi
}

# 安全检查
ce_check_security() {
    if command -v trivy &> /dev/null; then
        trivy fs --quiet --severity HIGH,CRITICAL . 2>/dev/null
    fi
}
```

### 6.4 智能调度优化

```bash
#!/bin/bash
# ce-scheduler.sh - 智能任务调度器

# 根据系统负载智能调度验证任务
ce_smart_schedule() {
    local phase="$1"

    # 检查系统负载
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local cpu_count=$(nproc)
    local load_ratio=$(awk -v load="$load_avg" -v cpu="$cpu_count" 'BEGIN {print int(load/cpu*100)}')

    echo "💻 System load: ${load_ratio}%"

    # 根据负载调整并行度
    local max_parallel
    if [[ $load_ratio -lt 50 ]]; then
        max_parallel=$cpu_count
        echo "   ✅ Low load - running full parallel ($max_parallel threads)"
    elif [[ $load_ratio -lt 80 ]]; then
        max_parallel=$((cpu_count / 2))
        echo "   ⚠️  Medium load - throttling to $max_parallel threads"
    else
        max_parallel=1
        echo "   ⚠️  High load - sequential execution only"
    fi

    # 执行验证
    ce_parallel_validate "$phase" "$max_parallel"
}

# 优先级调度（紧急检查优先）
ce_priority_schedule() {
    local checks=(
        "critical:security"
        "critical:gate_validation"
        "high:lint"
        "high:test"
        "medium:type_check"
        "low:documentation"
    )

    echo "🎯 Priority-based scheduling..."

    # 按优先级排序执行
    for check in "${checks[@]}"; do
        local priority="${check%%:*}"
        local check_name="${check#*:}"

        echo "   [$priority] Running $check_name..."
        ce_run_check "$check_name"
    done
}
```

---

## 📊 性能基准测试

### 预期性能指标

| 操作 | 未优化 | 优化后 | 提升 |
|-----|--------|--------|-----|
| `ce validate` | 45s | 12s | 73% |
| `ce start` | 3s | 0.5s | 83% |
| `ce next` | 50s | 15s | 70% |
| Phase状态读取 | 0.2s | 0.01s | 95% |
| Gate验证 | 30s | 8s | 73% |
| 冲突检测 | 5s | 0.5s | 90% |

### 优化策略汇总

1. **缓存机制**: 5分钟TTL，减少95%文件读取
2. **增量验证**: 只检查变更文件，节省70%时间
3. **并行检查**: 利用多核CPU，提升3-4倍速度
4. **智能调度**: 根据系统负载动态调整
5. **状态复用**: 避免重复解析YAML配置

---

## 🎯 集成验证清单

完成 `ce` 命令集成后的验证项：

- [ ] Phase状态读取正确（.phase/current优先级最高）
- [ ] Phase感知行为在所有命令中生效
- [ ] Phase转换规则验证工作正常
- [ ] Gate集成调用executor.sh成功
- [ ] 并行Gate验证功能正常（4线程）
- [ ] 多终端状态文件正确创建
- [ ] 文件冲突检测算法准确
- [ ] 文件锁机制防止并发冲突
- [ ] 自动化触发器响应Phase变化
- [ ] 缓存系统减少重复读取
- [ ] 增量验证只检查变更文件
- [ ] 智能调度根据负载调整并行度

---

## 📝 总结

本设计文档提供了 `ce` 命令与 Claude Enhancer 8-Phase 工作流的完整集成方案，涵盖：

1. **Phase 感知**: 从三个位置读取状态，智能适配命令行为
2. **Gate 集成**: 复用现有验证引擎，支持并行和增量检查
3. **状态管理**: YAML格式的多终端状态跟踪系统
4. **冲突检测**: 文件级冲突检测 + 锁机制防止并发问题
5. **自动化**: Phase转换和文件变更的自动触发器
6. **性能优化**: 缓存、增量、并行、智能调度四重优化

**实施优先级**:
1. Phase感知设计（核心功能）
2. Gate集成策略（质量保障）
3. 缓存和增量验证（性能提升）
4. 多终端状态管理（协作支持）
5. 冲突检测和自动化（高级特性）

---

**作者**: Claude Enhancer Team
**审阅**: Pending
**状态**: 设计完成，待实施
