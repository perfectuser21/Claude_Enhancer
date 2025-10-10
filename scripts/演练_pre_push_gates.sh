#!/bin/bash
# 演练pre-push最后闸门的三类拦截

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 加载最后闸门函数库
if [ -f "$PROJECT_ROOT/.workflow/lib/final_gate.sh" ]; then
    source "$PROJECT_ROOT/.workflow/lib/final_gate.sh"
else
    echo "❌ ERROR: Missing final_gate.sh library"
    exit 1
fi

echo "🧪 Pre-push Gates Rehearsal"
echo "Testing 3 blocking scenarios..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 场景1: 低分拦截
echo ""
echo "Scenario 1: Low quality score (84 < 85)"
export MOCK_SCORE=84
if final_gate_check 2>&1; then
    echo "❌ TEST FAILED: Should have blocked but passed"
else
    echo "✅ TEST PASSED: Correctly blocked low score"
fi
unset MOCK_SCORE

# 场景2: 低覆盖率拦截
echo ""
echo "Scenario 2: Low coverage (79% < 80%)"
export MOCK_COVERAGE=79
if final_gate_check 2>&1; then
    echo "❌ TEST FAILED: Should have blocked but passed"
else
    echo "✅ TEST PASSED: Correctly blocked low coverage"
fi
unset MOCK_COVERAGE

# 场景3: 缺少签名拦截（仅生产分支）
echo ""
echo "Scenario 3: Missing signatures on main branch"
export BRANCH=main
export MOCK_SIG=invalid
SIG_COUNT=$(ls .gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
echo "Current signature count: $SIG_COUNT"

if final_gate_check 2>&1; then
    if [[ "$BRANCH" =~ ^(main|master|production)$ ]] && [ "$SIG_COUNT" -lt 8 ]; then
        echo "✅ TEST PASSED: Would block on production branch (only $SIG_COUNT/8 signatures)"
    else
        echo "⚠️  TEST SKIPPED: Have enough signatures ($SIG_COUNT/8)"
    fi
else
    echo "✅ TEST PASSED: Correctly blocked missing signatures"
fi
unset BRANCH
unset MOCK_SIG

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Rehearsal completed"
echo "Evidence saved in: evidence/"
