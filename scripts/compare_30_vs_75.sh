#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Comparison Script: 30-Step vs 75-Step Validator
# 展示75步版本相比30步版本的提升
# ═══════════════════════════════════════════════════════════
set -euo pipefail

echo "═══════════════════════════════════════════════════════════════"
echo "  Workflow Validator Comparison: 30-Step vs 75-Step"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 检查脚本存在性
if [ ! -f "scripts/workflow_validator.sh" ]; then
  echo "❌ Error: 30-step validator not found (scripts/workflow_validator.sh)"
  exit 1
fi

if [ ! -f "scripts/workflow_validator_v75_complete.sh" ]; then
  echo "❌ Error: 75-step validator not found (scripts/workflow_validator_v75_complete.sh)"
  exit 1
fi

# 创建临时目录存储结果
TEMP_DIR=".temp/comparison_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEMP_DIR"

echo "Running 30-step validator..."
echo "─────────────────────────────────────────────────────────────"
if bash scripts/workflow_validator.sh > "$TEMP_DIR/30step_output.txt" 2>&1; then
  V30_EXIT=0
else
  V30_EXIT=$?
fi

V30_TOTAL=$(grep "^Total:" "$TEMP_DIR/30step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V30_PASSED=$(grep "^Passed:" "$TEMP_DIR/30step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V30_FAILED=$(grep "^Failed:" "$TEMP_DIR/30step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V30_RATE=$(grep "^Pass Rate:" "$TEMP_DIR/30step_output.txt" 2>/dev/null | awk '{print $3}' || echo "0%")

echo "✓ 30-step validator complete"
echo ""

echo "Running 75-step validator..."
echo "─────────────────────────────────────────────────────────────"
if bash scripts/workflow_validator_v75_complete.sh > "$TEMP_DIR/75step_output.txt" 2>&1; then
  V75_EXIT=0
else
  V75_EXIT=$?
fi

V75_TOTAL=$(grep "^Total:" "$TEMP_DIR/75step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V75_PASSED=$(grep "^Passed:" "$TEMP_DIR/75step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V75_FAILED=$(grep "^Failed:" "$TEMP_DIR/75step_output.txt" 2>/dev/null | awk '{print $2}' || echo "0")
V75_RATE=$(grep "^Pass Rate:" "$TEMP_DIR/75step_output.txt" 2>/dev/null | awk '{print $3}' || echo "0%")

echo "✓ 75-step validator complete"
echo ""

# ═══════════════════════════════════════════════════════════════
# 生成对比表格
# ═══════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo "  Comparison Results"
echo "═══════════════════════════════════════════════════════════════"
echo ""

printf "%-25s | %-15s | %-15s | %-10s\n" "Metric" "30-Step" "75-Step" "Difference"
printf "%-25s-+-%-15s-+-%-15s-+-%-10s\n" "-------------------------" "---------------" "---------------" "----------"
printf "%-25s | %-15s | %-15s | %-10s\n" "Total Checks" "$V30_TOTAL" "$V75_TOTAL" "+$((V75_TOTAL - V30_TOTAL))"
printf "%-25s | %-15s | %-15s | %-10s\n" "Passed" "$V30_PASSED" "$V75_PASSED" "+$((V75_PASSED - V30_PASSED))"
printf "%-25s | %-15s | %-15s | %-10s\n" "Failed" "$V30_FAILED" "$V75_FAILED" "$((V75_FAILED - V30_FAILED))"
printf "%-25s | %-15s | %-15s | %-10s\n" "Pass Rate" "$V30_RATE" "$V75_RATE" "-"
printf "%-25s | %-15s | %-15s | %-10s\n" "Exit Code" "$V30_EXIT" "$V75_EXIT" "-"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  What 75-Step Catches That 30-Step Misses"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat <<EOF
📊 Enhanced Coverage:

Phase 0 (Discovery):
  • 30-step: Basic P0_DISCOVERY.md existence
  • 75-step: + Content validation (>300 lines)
             + Problem Statement completeness
             + Background section validation
             + Feasibility analysis verification
             + Impact Radius assessment
             + Anti-hollow placeholder detection

Phase 1 (Planning):
  • 30-step: PLAN.md existence, basic structure
  • 75-step: + Executive Summary validation
             + System Architecture verification
             + Agent Strategy documentation
             + Implementation Plan completeness
             + Technology stack documentation
             + Risk identification checks

Phase 2 (Implementation):
  • 30-step: File existence checks
  • 75-step: + Git commit validation
             + Shell script syntax checking
             + Sensitive data detection
             + Large file detection
             + Comment ratio validation
             + README/CONTRIBUTING updates

🔒 Phase 3 (Testing) - Quality Gate 1:
  • 30-step: Not present
  • 75-step: ✓ Static checks execution (blocking)
             ✓ Shell syntax validation
             ✓ Shellcheck linting
             ✓ Unit test execution
             ✓ BDD test execution
             ✓ Test coverage validation (≥70%)
             ✓ Performance benchmarks
             ✓ Hook performance testing (<2s)
             ✓ Sensitive data detection
             ✓ Code complexity checks
             ✓ Evidence recording

🔒 Phase 4 (Review) - Quality Gate 2:
  • 30-step: Not present
  • 75-step: ✓ Pre-merge audit execution (blocking)
             ✓ REVIEW.md completeness (>3KB)
             ✓ Review content validation
             ✓ Review findings documentation
             ✓ Version consistency check (blocking)
             ✓ P0 checklist verification
             ✓ Evidence recording

📦 Phase 5 (Release & Monitor):
  • 30-step: Not present
  • 75-step: ✓ CHANGELOG.md updates
             ✓ README.md final checks
             ✓ Internal link validation
             ✓ Git tag verification
             ✓ Semantic versioning validation
             ✓ Release notes verification
             ✓ Health check configuration
             ✓ SLO monitoring setup
             ✓ CI/CD configuration checks
             ✓ Deployment documentation
             ✓ API documentation
             ✓ Security audit verification
             ✓ Root directory cleanup (≤7 docs)
             ✓ P0 checklist final confirmation
             ✓ Evidence recording

🎯 Key Improvements:

1. Quality Gates (2 blocking checkpoints):
   - Phase 3: Technical quality (static checks, tests)
   - Phase 4: Code quality (audit, version consistency)

2. Anti-Hollow Checks (6 layers):
   - Structure validation
   - Placeholder detection (TODO/TBD/待定)
   - Sample data validation
   - Executability verification
   - Test report validation
   - Evidence traceability

3. Blocking Checks (5 critical):
   - static_checks.sh execution
   - pre_merge_audit.sh execution
   - Version consistency validation
   - All must pass to proceed

4. Comprehensive Coverage:
   - 30-step: P0-P2 only (35 checks)
   - 75-step: P0-P5 complete (75 checks)
   - Coverage increase: 114% more checks

5. Evidence Generation:
   - All phases (P0-P5) generate timestamped evidence
   - SHA256 hashes for document integrity
   - Complete audit trail

EOF

# ═══════════════════════════════════════════════════════════════
# Failed Checks Comparison
# ═══════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo "  Failed Checks Breakdown"
echo "═══════════════════════════════════════════════════════════════"
echo ""

V30_FAILED_LIST=$(grep "^Failed checks:" "$TEMP_DIR/30step_output.txt" 2>/dev/null | sed 's/Failed checks://' || echo "")
V75_FAILED_LIST=$(grep "^Failed checks:" "$TEMP_DIR/75step_output.txt" 2>/dev/null | sed 's/Failed checks://' || echo "")

echo "30-Step Failed Checks:$V30_FAILED_LIST"
echo ""
echo "75-Step Failed Checks:$V75_FAILED_LIST"
echo ""

# ═══════════════════════════════════════════════════════════════
# Recommendations
# ═══════════════════════════════════════════════════════════════
echo "═══════════════════════════════════════════════════════════════"
echo "  Recommendations"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ "$V75_FAILED" -gt "$V30_FAILED" ]; then
  echo "🔍 75-step validator found MORE issues than 30-step:"
  echo "   This is expected and GOOD! The additional checks caught problems"
  echo "   that 30-step would have missed."
  echo ""
  echo "   ➜ Fix the failed checks revealed by 75-step validator"
  echo "   ➜ These issues would have surfaced later (in production)"
  echo "   ➜ Early detection = lower fix cost"
elif [ "$V75_FAILED" -eq "$V30_FAILED" ]; then
  echo "✅ Both validators found the same number of issues"
  echo "   75-step provides more detailed validation without false positives"
elif [ "$V75_FAILED" -lt "$V30_FAILED" ]; then
  echo "✨ 75-step validator found FEWER issues than 30-step:"
  echo "   This could mean some checks were relaxed or better designed"
  echo "   Review the differences to understand why"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Coverage Improvement: $((V75_TOTAL - V30_TOTAL)) additional checks (+$((((V75_TOTAL - V30_TOTAL) * 100) / V30_TOTAL))%)"
echo "Quality Gates Added: 2 (Phase 3 + Phase 4)"
echo "Phases Covered: P0-P5 (complete workflow)"
echo ""
echo "Detailed outputs saved to:"
echo "  - $TEMP_DIR/30step_output.txt"
echo "  - $TEMP_DIR/75step_output.txt"
echo ""

# 退出码：如果75步版本失败更多，使用75步的退出码
if [ $V75_EXIT -ne 0 ]; then
  echo "⚠️  75-step validator found issues that need fixing"
  exit $V75_EXIT
elif [ $V30_EXIT -ne 0 ]; then
  echo "⚠️  30-step validator found issues"
  exit $V30_EXIT
else
  echo "✅ Both validators passed!"
  exit 0
fi
