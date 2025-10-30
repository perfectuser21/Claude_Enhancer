#!/bin/bash
# Claude Hook: PR创建门禁
# 触发时机: PreBash (在AI执行bash命令前)
# 目的: 强制Phase 1-7完整执行后才能创建PR
# 优先级: 最高 - 硬阻止

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PHASE_CURRENT="${PROJECT_ROOT}/.phase/current"

# 提取bash命令
BASH_COMMAND="${BASH_COMMAND:-}"

# 检查是否是PR创建命令
if [[ "$BASH_COMMAND" =~ (gh[[:space:]]+pr[[:space:]]+create|git[[:space:]]+push.*--set-upstream) ]]; then

    # 检查.phase/current文件是否存在
    if [[ ! -f "$PHASE_CURRENT" ]]; then
        echo "❌ ERROR: Cannot create PR - .phase/current file missing"
        echo ""
        echo "Phase tracking not initialized. Are you in a feature branch?"
        exit 1
    fi

    # 获取当前Phase
    current_phase=$(tr -d '[:space:]' < "$PHASE_CURRENT" 2>/dev/null || echo "Phase1")

    # 检查是否在Phase 7
    if [[ "$current_phase" != "Phase7" ]]; then
        echo "════════════════════════════════════════════════════════════"
        echo "❌ ERROR: Cannot create PR before Phase 7 completion"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo "Current Phase: $current_phase"
        echo "Required Phase: Phase7"
        echo ""
        echo "📋 7-Phase Workflow (mandatory, no skipping):"
        echo ""
        echo "  ✅ Phase 1: Discovery & Planning"
        echo "  ✅ Phase 2: Implementation"
        echo "  ✅ Phase 3: Testing (Quality Gate 1)"
        echo "  ✅ Phase 4: Review (Quality Gate 2)"
        if [[ "$current_phase" == "Phase1" ]] || [[ "$current_phase" == "Phase2" ]] || \
           [[ "$current_phase" == "Phase3" ]] || [[ "$current_phase" == "Phase4" ]]; then
            echo "  ⏳ Phase 5: Release Preparation ← YOU MUST COMPLETE THIS"
            echo "  ⏳ Phase 6: Acceptance Testing"
            echo "  ⏳ Phase 7: Final Cleanup"
        elif [[ "$current_phase" == "Phase5" ]]; then
            echo "  ✅ Phase 5: Release Preparation"
            echo "  ⏳ Phase 6: Acceptance Testing ← YOU MUST COMPLETE THIS"
            echo "  ⏳ Phase 7: Final Cleanup"
        elif [[ "$current_phase" == "Phase6" ]]; then
            echo "  ✅ Phase 5: Release Preparation"
            echo "  ✅ Phase 6: Acceptance Testing"
            echo "  ⏳ Phase 7: Final Cleanup ← YOU MUST COMPLETE THIS"
        fi
        echo ""
        echo "💡 To proceed:"
        echo "   1. Complete all remaining phases"
        echo "   2. Update .phase/current to Phase7"
        echo "   3. Then create PR"
        echo ""
        echo "🚨 This is a HARD BLOCK - cannot be bypassed"
        echo "════════════════════════════════════════════════════════════"
        exit 1
    fi

    # Phase 7检查：必须有Acceptance Report
    if ! ls "$PROJECT_ROOT"/.workflow/ACCEPTANCE_REPORT_*.md >/dev/null 2>&1; then
        echo "════════════════════════════════════════════════════════════"
        echo "❌ ERROR: Phase 6 Acceptance Report missing"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo "Phase 7 requires Phase 6 Acceptance Report to exist."
        echo ""
        echo "Expected file: .workflow/ACCEPTANCE_REPORT_*.md"
        echo ""
        echo "💡 To fix:"
        echo "   1. Complete Phase 6 Acceptance Testing"
        echo "   2. Create ACCEPTANCE_REPORT"
        echo "   3. Then proceed to create PR"
        echo ""
        exit 1
    fi

    # Phase 7检查：版本一致性
    if [[ -f "$PROJECT_ROOT/scripts/check_version_consistency.sh" ]]; then
        if ! bash "$PROJECT_ROOT/scripts/check_version_consistency.sh" >/dev/null 2>&1; then
            echo "════════════════════════════════════════════════════════════"
            echo "❌ ERROR: Version inconsistency detected"
            echo "════════════════════════════════════════════════════════════"
            echo ""
            echo "All 6 version files must have identical version:"
            echo "  1. VERSION"
            echo "  2. .claude/settings.json"
            echo "  3. .workflow/manifest.yml"
            echo "  4. package.json"
            echo "  5. CHANGELOG.md"
            echo "  6. .workflow/SPEC.yaml"
            echo ""
            echo "💡 To fix:"
            echo "   Run: bash scripts/check_version_consistency.sh"
            echo "   (will show which files are inconsistent)"
            echo ""
            exit 1
        fi
    fi

    # 全部通过
    echo "✅ Phase 7 complete - PR creation allowed"
    echo "   All quality gates passed ✓"
    echo "   Acceptance report exists ✓"
    echo "   Version consistency verified ✓"
    echo ""
fi

# 不是PR创建命令，或所有检查通过，允许继续
exit 0
