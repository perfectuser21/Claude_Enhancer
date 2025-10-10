#!/bin/bash
# CE Phase 集成示例脚本
# 展示如何使用 CE 命令与 Phase 系统集成功能

# 本脚本是示例代码，用于演示各种场景的使用方法
# 不建议直接执行，而是作为参考和学习材料

set -euo pipefail

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

echo_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

echo_example() {
    echo -e "${YELLOW}示例 $1:${NC} $2"
    echo ""
}

echo_code() {
    echo -e "${GREEN}\$ $1${NC}"
}

echo_output() {
    echo -e "${BLUE}$1${NC}"
}

# ============================================================================
# 示例 1: Phase 感知 - 查询当前 Phase
# ============================================================================

example_01_query_phase() {
    echo_section "示例 1: 查询当前 Phase"

    echo_example "1.1" "最简单的方式 - 读取 .phase/current"
    echo_code "cat .phase/current"
    echo_output "P3"
    echo ""

    echo_example "1.2" "使用封装函数 - 带优先级处理"
    cat << 'EOF'
ce_get_current_phase() {
    # 优先级1: .phase/current
    if [[ -f ".phase/current" ]]; then
        cat .phase/current | tr -d '\n\r'
        return 0
    fi

    # 优先级2: .workflow/ACTIVE
    if [[ -f ".workflow/ACTIVE" ]]; then
        grep "^phase:" .workflow/ACTIVE | awk '{print $2}' | tr -d '\n\r'
        return 0
    fi

    # 默认P0
    echo "P0"
}
EOF
    echo ""
    echo_code "ce_get_current_phase"
    echo_output "P3"
    echo ""

    echo_example "1.3" "获取 Phase 详细信息"
    cat << 'EOF'
ce_get_phase_info() {
    local phase="$1"

    python3 << PYEOF
import yaml

with open(".workflow/gates.yml", 'r') as f:
    data = yaml.safe_load(f)

phase_data = data['phases']['${phase}']
print(f"Name: {phase_data['name']}")
print(f"Gates: {len(phase_data['gates'])}")
print(f"Allowed paths: {', '.join(phase_data['allow_paths'])}")
PYEOF
}
EOF
    echo ""
    echo_code "ce_get_phase_info P3"
    echo_output "Name: Implement"
    echo_output "Gates: 3"
    echo_output "Allowed paths: src/**, docs/CHANGELOG.md"
    echo ""
}

# ============================================================================
# 示例 2: Phase 感知行为 - ce start 命令
# ============================================================================

example_02_phase_aware_start() {
    echo_section "示例 2: Phase 感知的 ce start 命令"

    echo_example "2.1" "在 P0 阶段尝试 start（应该被阻止）"
    echo_code "ce start user-login"
    echo_output "❌ Cannot start feature in P0 Discovery phase"
    echo_output "   P0 is for technical spike and feasibility validation"
    echo_output ""
    echo_output "📋 Suggested actions:"
    echo_output "   1. Complete discovery document: docs/P0_*_DISCOVERY.md"
    echo_output "   2. Run: ce validate  (to pass P0 gates)"
    echo_output "   3. Run: ce next      (to enter P1 Planning)"
    echo ""

    echo_example "2.2" "在 P1 阶段 start（正确时机）"
    echo_code "ce start user-login"
    echo_output "✅ Perfect timing! P1 is ideal for starting new features"
    echo_output "   Creating feature branch with P1 context..."
    echo_output ""
    echo_output "🌿 Branch created: feature/P1-t1-20251009-user-login"
    echo_output "📝 Terminal registered: t1"
    echo_output "🎯 Phase: P1 (Plan)"
    echo ""

    echo_example "2.3" "在 P3 阶段尝试 start（警告）"
    echo_code "ce start payment-checkout"
    echo_output "⚠️  Already in P3 - feature development in progress"
    echo_output "   Cannot start new feature until current phase completes"
    echo_output ""
    echo_output "📋 Options:"
    echo_output "   • Continue current phase work"
    echo_output "   • Run: ce validate  (to check progress)"
    echo_output "   • Run: ce next      (to advance phase)"
    echo ""
}

# ============================================================================
# 示例 3: Gate 验证 - 不同模式
# ============================================================================

example_03_gate_validation() {
    echo_section "示例 3: Gate 验证的不同模式"

    echo_example "3.1" "完整验证（默认）"
    echo_code "ce validate"
    echo_output "🔍 Validating Phase P3 gates (full mode)..."
    echo_output ""
    echo_output "Gate 1: ✅ Build passes"
    echo_output "Gate 2: ✅ CHANGELOG updated"
    echo_output "Gate 3: ✅ No whitelist violations"
    echo_output ""
    echo_output "📊 Results: 3/3 passed"
    echo_output "✅ All gates passed!"
    echo_output ""
    echo_output "🎉 Gate marked as passed: .gates/03.ok"
    echo ""

    echo_example "3.2" "快速验证（使用缓存）"
    echo_code "ce validate --quick"
    echo_output "🔍 Checking cache..."
    echo_output "✅ Using cached validation result (127s old)"
    echo_output "📊 Cache hit rate: 85%"
    echo ""

    echo_example "3.3" "增量验证（仅变更文件）"
    echo_code "ce validate --incremental"
    echo_output "🔍 Incremental validation for P3..."
    echo_output "   Changed files:"
    echo_output "     • src/auth/login.ts"
    echo_output "     • test/auth/login.test.ts"
    echo_output ""
    echo_output "   Checking: src/auth/login.ts"
    echo_output "   ✅ In whitelist + Linting passed"
    echo_output ""
    echo_output "   Checking: test/auth/login.test.ts"
    echo_output "   ✅ In whitelist + Linting passed"
    echo_output ""
    echo_output "✅ All changed files pass incremental validation"
    echo_output "⚡ Time saved: 32s (70% faster)"
    echo ""

    echo_example "3.4" "并行验证（加速）"
    echo_code "ce validate --parallel 4"
    echo_output "🚀 Running 3 gates in parallel (max=4)..."
    echo_output ""
    echo_output "Thread 1: ✅ Gate 1 (3.2s)"
    echo_output "Thread 2: ✅ Gate 2 (2.8s)"
    echo_output "Thread 3: ✅ Gate 3 (4.1s)"
    echo_output ""
    echo_output "📊 Results: 3/3 passed"
    echo_output "⚡ Total time: 4.1s (parallel) vs 10.1s (sequential)"
    echo_output "🚀 Speed improvement: 2.5x"
    echo ""
}

# ============================================================================
# 示例 4: Phase 转换 - ce next
# ============================================================================

example_04_phase_transition() {
    echo_section "示例 4: Phase 转换 (ce next)"

    echo_example "4.1" "从 P3 到 P4 的正常转换"
    echo_code "ce next"
    echo_output "🔍 Validating current phase (P3) before transition..."
    echo_output ""
    echo_output "Gate 1: ✅ Build passes"
    echo_output "Gate 2: ✅ CHANGELOG updated"
    echo_output "Gate 3: ✅ No whitelist violations"
    echo_output ""
    echo_output "✅ P3 gates passed!"
    echo_output "🚀 Advancing to P4..."
    echo_output ""
    echo_output "📝 Executing on_pass actions:"
    echo_output "   1. ✅ Created: .gates/03.ok"
    echo_output "   2. ✅ Updated: .phase/current = P4"
    echo_output ""
    echo_output "🎉 Successfully transitioned: P3 → P4"
    echo ""

    echo_example "4.2" "Gate 失败时的转换阻止"
    echo_code "ce next"
    echo_output "🔍 Validating current phase (P3) before transition..."
    echo_output ""
    echo_output "Gate 1: ✅ Build passes"
    echo_output "Gate 2: ❌ CHANGELOG not updated"
    echo_output "Gate 3: ✅ No whitelist violations"
    echo_output ""
    echo_output "❌ P3 gates failed"
    echo_output "   Cannot advance to next phase"
    echo_output ""
    echo_output "📋 Fix issues and try again:"
    echo_output "   • Update docs/CHANGELOG.md Unreleased section"
    echo_output "   • Add entry for current changes"
    echo_output "   • Run: ce validate  (to verify fix)"
    echo_output "   • Run: ce next      (retry after fixes)"
    echo ""

    echo_example "4.3" "P5 到 P6 需要 APPROVE"
    echo_code "ce next"
    echo_output "🔍 Validating current phase (P5) before transition..."
    echo_output ""
    echo_output "Gate 1: ✅ Review document exists"
    echo_output "Gate 2: ✅ Three sections present"
    echo_output "Gate 3: ❌ Missing APPROVE in docs/REVIEW.md"
    echo_output ""
    echo_output "❌ P5→P6 requires 'APPROVE' in docs/REVIEW.md"
    echo_output ""
    echo_output "💡 Add the following line to docs/REVIEW.md:"
    echo_output "   APPROVE"
    echo ""
}

# ============================================================================
# 示例 5: 多终端状态管理
# ============================================================================

example_05_multi_terminal() {
    echo_section "示例 5: 多终端状态管理"

    echo_example "5.1" "注册新终端"
    echo_code "ce start user-login  # Terminal t1"
    echo_output "✅ Terminal t1 registered"
    echo_output "📝 State saved: .workflow/state/sessions/terminal-t1.state"
    echo_output "🌿 Branch: feature/P3-t1-20251009-user-login"
    echo ""

    echo_example "5.2" "查看所有活跃终端"
    echo_code "ce state terminals"
    echo_output "🖥️  ACTIVE TERMINALS"
    echo_output ""
    echo_output "Terminal t1:"
    echo_output "  Branch: feature/P3-t1-20251009-user-login"
    echo_output "  Phase: P3"
    echo_output "  Status: active"
    echo_output "  Last activity: 2025-10-09 12:30:45"
    echo_output "  Files modified: 3"
    echo_output "  Locks held: 2"
    echo_output ""
    echo_output "Terminal t2:"
    echo_output "  Branch: feature/P3-t2-20251009-payment"
    echo_output "  Phase: P3"
    echo_output "  Status: active"
    echo_output "  Last activity: 2025-10-09 12:35:12"
    echo_output "  Files modified: 5"
    echo_output "  Locks held: 3"
    echo ""

    echo_example "5.3" "检测僵死终端"
    echo_code "ce state clean-stale"
    echo_output "🔍 Scanning for stale terminals..."
    echo_output ""
    echo_output "⚠️  Stale terminals detected:"
    echo_output "   • t3 (inactive for 2 hours)"
    echo_output ""
    echo_output "🧹 Cleaning up:"
    echo_output "   • Removing: .workflow/state/sessions/terminal-t3.state"
    echo_output "   • Releasing locks: 2"
    echo_output "   • Updating global state"
    echo_output ""
    echo_output "✅ Cleaned 1 stale terminal"
    echo ""

    echo_example "5.4" "查看终端状态文件"
    echo_code "cat .workflow/state/sessions/terminal-t1.state"
    cat << 'EOF'
terminal_id: t1
branch: feature/P3-t1-20251009-user-login
phase: P3
started_at: 2025-10-09T10:00:00Z
last_activity: 2025-10-09T12:30:45Z
status: active
gates_passed:
  - 00
  - 01
  - 02
  - 03
files_modified:
  - src/auth/login.ts
  - src/auth/session.ts
  - test/auth/login.test.ts
locks_held:
  - src/auth/login.ts
  - src/auth/session.ts
metrics:
  commits: 5
  lines_added: 234
  lines_deleted: 45
  test_runs: 12
  test_pass_rate: 100%
EOF
    echo ""
}

# ============================================================================
# 示例 6: 冲突检测和解决
# ============================================================================

example_06_conflict_detection() {
    echo_section "示例 6: 冲突检测和解决"

    echo_example "6.1" "检测文件冲突"
    echo_code "ce conflicts"
    echo_output "🔍 Scanning for conflicts..."
    echo_output ""
    echo_output "⚠️  CONFLICTS DETECTED!"
    echo_output ""
    echo_output "❌ Conflict with terminal t2:"
    echo_output "     • src/auth/login.ts"
    echo_output "     • src/auth/session.ts"
    echo_output ""
    echo_output "📊 Conflict probability: 60%"
    echo_output ""
    echo_output "💡 CONFLICT RESOLUTION SUGGESTIONS"
    echo_output ""
    echo_output "✅ Strategy 1: PROCEED (You have priority by terminal ID)"
    echo_output "   Other terminals should wait for your completion"
    echo_output ""
    echo_output "⚠️  Strategy 2: WAIT (Terminal t2 is in phase P4 > P3)"
    echo_output ""
    echo_output "💡 Strategy 3: FILE PARTITIONING"
    echo_output "   Terminal t2 is working on:"
    echo_output "     • src/auth/login.ts"
    echo_output "     • src/auth/session.ts"
    echo_output "   → Suggestion: Work on different files or modules"
    echo_output ""
    echo_output "🚀 RECOMMENDED ACTIONS:"
    echo_output "   1. Communicate with conflicting terminals"
    echo_output "   2. Coordinate merge order (lower terminal ID first)"
    echo_output "   3. Use file locks: ce lock <file>"
    echo_output "   4. Consider rebasing: ce rebase"
    echo ""

    echo_example "6.2" "使用文件锁避免冲突"
    echo_code "ce lock src/auth/login.ts"
    echo_output "🔒 File locked: src/auth/login.ts"
    echo_output "📝 Lock owner: t1"
    echo_output ""
    echo ""
    echo_code "# Terminal t2 尝试锁定同一文件"
    echo_code "ce lock src/auth/login.ts"
    echo_output "❌ File locked by terminal t1: src/auth/login.ts"
    echo_output ""
    echo_output "💡 Suggestions:"
    echo_output "   • Wait for t1 to complete"
    echo_output "   • Contact t1 owner to coordinate"
    echo_output "   • Work on different files"
    echo ""

    echo_example "6.3" "查看所有锁"
    echo_code "ce locks"
    echo_output "🔒 ACTIVE FILE LOCKS"
    echo_output ""
    echo_output "   • src/auth/login.ts"
    echo_output "     Owner: terminal t1"
    echo_output "     Locked at: 2025-10-09 12:15:30"
    echo_output ""
    echo_output "   • src/payment/checkout.ts"
    echo_output "     Owner: terminal t2"
    echo_output "     Locked at: 2025-10-09 12:20:45"
    echo ""

    echo_example "6.4" "释放锁"
    echo_code "ce unlock src/auth/login.ts"
    echo_output "🔓 File unlocked: src/auth/login.ts"
    echo_output "📝 Lock removed from terminal t1 state"
    echo ""
}

# ============================================================================
# 示例 7: 自动化触发器
# ============================================================================

example_07_auto_triggers() {
    echo_section "示例 7: 自动化触发器"

    echo_example "7.1" "P3 → P4 自动触发验证和 Linters"
    echo_code "ce next  # 从 P3 进入 P4"
    echo_output "🎯 Executing phase transition actions..."
    echo_output "🚀 P3 Implementation phase actions:"
    echo_output "   • Auto-validating code quality..."
    echo_output "   ✅ Quick validation passed"
    echo_output ""
    echo_output "   • Running linters..."
    echo_output "   ✅ ESLint: 0 errors, 0 warnings"
    echo_output "   ✅ Prettier: All files formatted"
    echo_output ""
    echo_output "   • Checking uncommitted changes..."
    echo_output "   ✅ All changes committed"
    echo_output ""
    echo_output "🎉 Transitioned to P4"
    echo ""

    echo_example "7.2" "P6 → P7 自动发布（延迟10秒）"
    echo_code "ce next  # 从 P6 进入 P7"
    echo_output "🚀 P6 Release phase actions:"
    echo_output "   • Checking if publish is needed..."
    echo_output "   ✅ Branch ready for publish"
    echo_output ""
    echo_output "   🤖 Auto-publishing in 10 seconds..."
    echo_output "      (Press Ctrl+C to cancel)"
    echo_output ""
    echo_output "   ⏳ 10..."
    echo_output "   ⏳ 9..."
    echo_output "   ..."
    echo_output "   ⏳ 1..."
    echo_output ""
    echo_output "🚀 Starting publish workflow..."
    echo_output "   • Creating PR: feature/P6-t1-20251009-user-login → main"
    echo_output "   • Running final checks..."
    echo_output "   • Merging (squash)..."
    echo_output "   • Creating tag: v1.2.0"
    echo_output "   • Pushing to remote..."
    echo_output ""
    echo_output "✅ Published successfully!"
    echo_output "🎉 Transitioned to P7 (Monitoring)"
    echo ""

    echo_example "7.3" "文件变更触发自动验证"
    echo_code "# 监听器后台运行"
    echo_code "ce watch &"
    echo_output "👀 Watching key files for changes..."
    echo_output ""
    echo ""
    echo_code "# 修改 PLAN.md"
    echo_code "echo '- New task' >> docs/PLAN.md"
    echo_output ""
    echo_output "🔔 PLAN.md updated"
    echo_output "🔍 Validating document structure..."
    echo_output "   ✅ Required headers present"
    echo_output "   ✅ Task count: 6 >= 5"
    echo_output "   ✅ Affected files list valid"
    echo_output ""
    echo_output "✅ PLAN.md validation passed"
    echo ""
}

# ============================================================================
# 示例 8: 性能优化实际效果
# ============================================================================

example_08_performance() {
    echo_section "示例 8: 性能优化实际效果"

    echo_example "8.1" "缓存效果对比"
    echo_code "# 第一次执行（无缓存）"
    echo_code "time ce validate"
    echo_output "🔍 Validating Phase P3 gates..."
    echo_output "[... 验证过程 ...]"
    echo_output "✅ All gates passed!"
    echo_output ""
    echo_output "real    0m12.345s"
    echo ""
    echo ""
    echo_code "# 第二次执行（有缓存）"
    echo_code "time ce validate --quick"
    echo_output "✅ Using cached validation result (45s old)"
    echo_output ""
    echo_output "real    0m0.023s"
    echo_output ""
    echo_output "⚡ Speed improvement: 536x faster!"
    echo ""

    echo_example "8.2" "增量 vs 完整验证"
    echo_code "# 完整验证"
    echo_code "time ce validate --full"
    echo_output "🔍 Validating all files..."
    echo_output "[... 检查 120 个文件 ...]"
    echo_output ""
    echo_output "real    0m15.678s"
    echo ""
    echo ""
    echo_code "# 增量验证（只有 3 个文件变更）"
    echo_code "time ce validate --incremental"
    echo_output "🔍 Incremental validation: 3 files changed"
    echo_output "[... 检查 3 个文件 ...]"
    echo_output ""
    echo_output "real    0m4.521s"
    echo_output ""
    echo_output "⚡ Time saved: 11.2s (71% faster)"
    echo ""

    echo_example "8.3" "并行 vs 串行验证"
    echo_code "# 串行验证"
    echo_code "time ce validate --parallel 1"
    echo_output "🔍 Running 4 gates sequentially..."
    echo_output "Gate 1: ✅ (3.2s)"
    echo_output "Gate 2: ✅ (2.8s)"
    echo_output "Gate 3: ✅ (4.1s)"
    echo_output "Gate 4: ✅ (3.5s)"
    echo_output ""
    echo_output "real    0m13.600s"
    echo ""
    echo ""
    echo_code "# 并行验证（4线程）"
    echo_code "time ce validate --parallel 4"
    echo_output "🚀 Running 4 gates in parallel (max=4)..."
    echo_output "Thread 1: ✅ Gate 1 (3.2s)"
    echo_output "Thread 2: ✅ Gate 2 (2.8s)"
    echo_output "Thread 3: ✅ Gate 3 (4.1s)"
    echo_output "Thread 4: ✅ Gate 4 (3.5s)"
    echo_output ""
    echo_output "real    0m4.100s"
    echo_output ""
    echo_output "⚡ Speed improvement: 3.3x faster!"
    echo ""

    echo_example "8.4" "智能调度（负载感知）"
    echo_code "# 低负载（30%）"
    echo_code "ce validate"
    echo_output "💻 System load: 30%"
    echo_output "   ✅ Low load - running full parallel (8 threads)"
    echo_output ""
    echo ""
    echo_code "# 高负载（85%）"
    echo_code "ce validate"
    echo_output "💻 System load: 85%"
    echo_output "   ⚠️  High load - sequential execution only"
    echo_output "   📊 Protecting system resources"
    echo ""
}

# ============================================================================
# 示例 9: 完整工作流演示
# ============================================================================

example_09_complete_workflow() {
    echo_section "示例 9: 完整工作流演示（P0 → P7）"

    echo_example "9.1" "完整的 Feature 开发生命周期"

    echo ""
    echo_code "# Phase 0: Discovery"
    echo_code "ce phase"
    echo_output "Current Phase: P0 (Discovery)"
    echo ""
    echo_code "# 创建可行性文档"
    echo_code "vi docs/P0_USER_LOGIN_DISCOVERY.md"
    echo_output "[... 编写技术spike和风险评估 ...]"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "✅ P0 gates passed!"
    echo_output "🚀 Advanced to P1"
    echo ""

    echo ""
    echo_code "# Phase 1: Planning"
    echo_code "ce start user-login"
    echo_output "✅ Branch created: feature/P1-t1-20251009-user-login"
    echo ""
    echo_code "# 创建计划文档"
    echo_code "vi docs/PLAN.md"
    echo_output "[... 编写任务清单和受影响文件 ...]"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "✅ P1 gates passed!"
    echo_output "🚀 Advanced to P2"
    echo ""

    echo ""
    echo_code "# Phase 2: Skeleton"
    echo_code "mkdir -p src/auth test/auth"
    echo_code "touch src/auth/login.ts src/auth/session.ts"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "✅ P2 gates passed!"
    echo_output "🚀 Advanced to P3"
    echo ""

    echo ""
    echo_code "# Phase 3: Implementation"
    echo_code "# 实现功能代码"
    echo_code "vi src/auth/login.ts"
    echo_output "[... 编写登录逻辑 ...]"
    echo ""
    echo_code "git add . && git commit -m 'feat: implement user login'"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "🎯 Auto-running linters..."
    echo_output "✅ P3 gates passed!"
    echo_output "🚀 Advanced to P4"
    echo ""

    echo ""
    echo_code "# Phase 4: Testing"
    echo_code "vi test/auth/login.test.ts"
    echo_output "[... 编写测试用例 ...]"
    echo ""
    echo_code "npm run test"
    echo_output "✅ All tests passed!"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "✅ P4 gates passed!"
    echo_output "🚀 Advanced to P5"
    echo ""

    echo ""
    echo_code "# Phase 5: Review"
    echo_code "vi docs/REVIEW.md"
    echo_output "[... 编写审查结论 ...]"
    echo_output "[... 最后一行写: APPROVE ...]"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "✅ P5 gates passed (APPROVE found)!"
    echo_output "🚀 Advanced to P6"
    echo ""

    echo ""
    echo_code "# Phase 6: Release"
    echo_code "vi docs/README.md docs/CHANGELOG.md"
    echo_output "[... 更新文档 ...]"
    echo ""
    echo_code "ce validate && ce next"
    echo_output "🤖 Auto-publishing in 10 seconds..."
    echo_output "[... 自动创建 PR 和合并 ...]"
    echo_output "✅ Published v1.2.0"
    echo_output "🚀 Advanced to P7"
    echo ""

    echo ""
    echo_code "# Phase 7: Monitoring"
    echo_code "ce monitor"
    echo_output "📊 Starting health checks..."
    echo_output "   ✅ Service health: 100%"
    echo_output "   ✅ SLO compliance: 99.9%"
    echo_output "   ✅ Error rate: 0.01%"
    echo_output ""
    echo_output "🎉 Feature successfully deployed and monitored!"
    echo ""
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo "║        CE Phase 集成示例脚本                                          ║"
    echo "║        CE Command Phase Integration Examples                          ║"
    echo "║                                                                       ║"
    echo "║        展示如何使用 CE 命令与 Phase 系统集成功能                      ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}注意: 本脚本是示例代码，用于演示和学习${NC}"
    echo -e "${YELLOW}      不建议直接执行，请根据需要复制相关代码${NC}"
    echo ""

    # 显示所有示例
    example_01_query_phase
    example_02_phase_aware_start
    example_03_gate_validation
    example_04_phase_transition
    example_05_multi_terminal
    example_06_conflict_detection
    example_07_auto_triggers
    example_08_performance
    example_09_complete_workflow

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  示例演示完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}📚 相关文档:${NC}"
    echo "   • 完整设计: docs/CE_PHASE_INTEGRATION_DESIGN.md"
    echo "   • 快速参考: docs/CE_PHASE_INTEGRATION_QUICK_REF.md"
    echo "   • 架构图:   docs/CE_PHASE_INTEGRATION_ARCHITECTURE.txt"
    echo "   • 检查清单: docs/CE_PHASE_INTEGRATION_CHECKLIST.md"
    echo ""
}

# 如果直接执行脚本，运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
