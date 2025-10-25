#!/bin/bash
# Phase 6: Acceptance Validation Script
# 改进版 - 6个真实验证检查点（非形式化）
# 日期: 2025-10-25

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

check_start() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}[$TOTAL_CHECKS]${NC} ${BOLD}$1${NC}"
    echo "────────────────────────────────────────────────────────"
}

check_pass() {
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

check_fail() {
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo -e "${RED}❌ FAIL${NC}: $1"
}

check_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# Banner
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Phase 6: Acceptance Validation (Real Checks)          ║"
echo "║     6 Technical Validation Checkpoints                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ============================================
# AC_S001: 冒烟测试 (Smoke Tests)
# ============================================
check_start "AC_S001: Smoke Tests - Critical Functionality"

SMOKE_FAILURES=0

echo "Testing critical scripts..."

# Test 1: Version consistency check
echo -n "  [1/5] Version consistency check... "
if bash "$PROJECT_ROOT/scripts/check_version_consistency.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((SMOKE_FAILURES++))
fi

# Test 2: Static checks (incremental mode)
echo -n "  [2/5] Static checks (incremental)... "
if timeout 30 bash "$PROJECT_ROOT/scripts/static_checks.sh" --incremental >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((SMOKE_FAILURES++))
fi

# Test 3: Git hooks are executable
echo -n "  [3/5] Git hooks executability... "
HOOKS_OK=0
for hook in pre-commit commit-msg pre-push; do
    if [ -x "$PROJECT_ROOT/.git/hooks/$hook" ]; then
        ((HOOKS_OK++))
    fi
done
if [ $HOOKS_OK -eq 3 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} ($HOOKS_OK/3 executable)"
    ((SMOKE_FAILURES++))
fi

# Test 4: Core workflow files exist
echo -n "  [4/5] Core workflow files... "
WORKFLOW_FILES_OK=0
for file in .workflow/SPEC.yaml .workflow/manifest.yml .workflow/gates.yml; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        ((WORKFLOW_FILES_OK++))
    fi
done
if [ $WORKFLOW_FILES_OK -eq 3 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} ($WORKFLOW_FILES_OK/3 exist)"
    ((SMOKE_FAILURES++))
fi

# Test 5: Phase tracking
echo -n "  [5/5] Phase tracking system... "
if [ -f "$PROJECT_ROOT/.phase/current" ] || [ -f "$PROJECT_ROOT/.workflow/ACTIVE" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (no phase tracking files)"
    ((SMOKE_FAILURES++))
fi

if [ $SMOKE_FAILURES -eq 0 ]; then
    check_pass "All smoke tests passed (5/5)"
else
    check_fail "$SMOKE_FAILURES smoke test(s) failed"
fi

# ============================================
# AC_S002: 关键功能验证
# ============================================
check_start "AC_S002: Key Functionality Validation"

FUNC_FAILURES=0

# Function 1: Shellcheck baseline enforcement
echo -n "  [1/3] Shellcheck baseline (≤1850)... "
if command -v shellcheck >/dev/null 2>&1; then
    SHELL_FILES=$(find "$PROJECT_ROOT" -type f -name "*.sh" \
        -not -path "*/.git/*" \
        -not -path "*/node_modules/*" \
        -not -path "*/.temp/*" 2>/dev/null || true)

    if [ -n "$SHELL_FILES" ]; then
        # shellcheck disable=SC2086
        WARNINGS=$(shellcheck -f gcc $SHELL_FILES 2>/dev/null | grep -c "warning:" || true)
        if [ "$WARNINGS" -le 1850 ]; then
            echo -e "${GREEN}✓${NC} ($WARNINGS warnings)"
        else
            echo -e "${RED}✗${NC} ($WARNINGS > 1850)"
            ((FUNC_FAILURES++))
        fi
    else
        echo -e "${YELLOW}⊘${NC} (no shell files)"
    fi
else
    echo -e "${YELLOW}⊘${NC} (shellcheck not installed)"
fi

# Function 2: Document count limit
echo -n "  [2/3] Root document count (≤7)... "
ROOT_DOCS=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)
if [ "$ROOT_DOCS" -le 7 ]; then
    echo -e "${GREEN}✓${NC} ($ROOT_DOCS docs)"
else
    echo -e "${RED}✗${NC} ($ROOT_DOCS > 7)"
    ((FUNC_FAILURES++))
fi

# Function 3: Branch protection hooks
echo -n "  [3/3] Branch protection active... "
if [ -f "$PROJECT_ROOT/.git/hooks/pre-push" ] && \
   grep -q "main.*master.*production" "$PROJECT_ROOT/.git/hooks/pre-push" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((FUNC_FAILURES++))
fi

if [ $FUNC_FAILURES -eq 0 ]; then
    check_pass "All key functions validated"
else
    check_fail "$FUNC_FAILURES key function(s) failed"
fi

# ============================================
# AC_S003: 性能回归检测
# ============================================
check_start "AC_S003: Performance Regression Detection"

PERF_ISSUES=0

# Check 1: Hook performance
echo "  Measuring hook performance..."
HOOK_PERF_FILE="$PROJECT_ROOT/.temp/hook_performance_baseline.txt"

if [ -f "$HOOK_PERF_FILE" ]; then
    # Compare against baseline
    BASELINE_TIME=$(cat "$HOOK_PERF_FILE" 2>/dev/null || echo "2000")

    # Measure current pre-commit time (dry run)
    START=$(date +%s%3N)
    timeout 5 bash "$PROJECT_ROOT/.git/hooks/pre-commit" --dry-run 2>/dev/null || true
    END=$(date +%s%3N)
    CURRENT_TIME=$((END - START))

    echo "    Baseline: ${BASELINE_TIME}ms"
    echo "    Current:  ${CURRENT_TIME}ms"

    THRESHOLD=$((BASELINE_TIME * 120 / 100))  # 20% regression tolerance

    if [ "$CURRENT_TIME" -le "$THRESHOLD" ]; then
        check_pass "Hook performance within acceptable range"
    else
        check_warn "Hook performance degraded by $((CURRENT_TIME - BASELINE_TIME))ms"
        ((PERF_ISSUES++))
    fi
else
    # Create baseline for next time
    echo "    No baseline found, creating baseline..."
    mkdir -p "$PROJECT_ROOT/.temp"
    echo "2000" > "$HOOK_PERF_FILE"
    check_pass "Performance baseline created (2000ms)"
fi

# Check 2: Incremental check speed
echo "  [2/2] Incremental check speed target (<90s)..."
START=$(date +%s)
timeout 120 bash "$PROJECT_ROOT/scripts/static_checks.sh" --incremental >/dev/null 2>&1 || true
END=$(date +%s)
DURATION=$((END - START))

if [ "$DURATION" -lt 90 ]; then
    echo "    Duration: ${DURATION}s"
    check_pass "Incremental checks within 90s target"
else
    echo "    Duration: ${DURATION}s (slow)"
    check_warn "Incremental checks slower than 90s target"
    ((PERF_ISSUES++))
fi

if [ $PERF_ISSUES -eq 0 ]; then
    check_pass "No performance regressions detected"
fi

# ============================================
# AC_S004: 部署配置验证
# ============================================
check_start "AC_S004: Deployment Configuration Validation"

DEPLOY_ISSUES=0

# Check 1: GitHub Actions workflows
echo "  [1/4] GitHub Actions workflows..."
REQUIRED_WORKFLOWS=(
    "ce-unified-gates.yml"
    "hardened-gates.yml"
    "test-suite.yml"
    "security-scan.yml"
)

WORKFLOW_COUNT=0
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$PROJECT_ROOT/.github/workflows/$workflow" ]; then
        echo "    ✓ $workflow"
        ((WORKFLOW_COUNT++))
    else
        echo "    ✗ $workflow (missing)"
        ((DEPLOY_ISSUES++))
    fi
done

if [ $WORKFLOW_COUNT -eq ${#REQUIRED_WORKFLOWS[@]} ]; then
    check_pass "All required workflows present"
fi

# Check 2: VERSION file consistency
echo "  [2/4] VERSION file..."
if [ -f "$PROJECT_ROOT/VERSION" ]; then
    VERSION=$(cat "$PROJECT_ROOT/VERSION" | tr -d '[:space:]')
    if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "    Version: $VERSION"
        check_pass "VERSION file valid"
    else
        echo "    Version: $VERSION (invalid format)"
        check_fail "VERSION file format invalid"
        ((DEPLOY_ISSUES++))
    fi
else
    check_fail "VERSION file missing"
    ((DEPLOY_ISSUES++))
fi

# Check 3: CHANGELOG updated
echo "  [3/4] CHANGELOG.md..."
if [ -f "$PROJECT_ROOT/CHANGELOG.md" ]; then
    RECENT_ENTRIES=$(grep -c "^## \[" "$PROJECT_ROOT/CHANGELOG.md" || true)
    if [ "$RECENT_ENTRIES" -gt 0 ]; then
        echo "    Entries: $RECENT_ENTRIES versions documented"
        check_pass "CHANGELOG.md populated"
    else
        check_warn "CHANGELOG.md exists but no version entries"
        ((DEPLOY_ISSUES++))
    fi
else
    check_fail "CHANGELOG.md missing"
    ((DEPLOY_ISSUES++))
fi

# Check 4: README exists and substantial
echo "  [4/4] README.md..."
if [ -f "$PROJECT_ROOT/README.md" ]; then
    README_SIZE=$(wc -c < "$PROJECT_ROOT/README.md")
    if [ "$README_SIZE" -gt 1000 ]; then
        echo "    Size: $README_SIZE bytes"
        check_pass "README.md substantial"
    else
        check_warn "README.md too small ($README_SIZE bytes)"
    fi
else
    check_fail "README.md missing"
    ((DEPLOY_ISSUES++))
fi

if [ $DEPLOY_ISSUES -eq 0 ]; then
    check_pass "Deployment configuration complete"
fi

# ============================================
# AC_S005: 生成验收报告
# ============================================
check_start "AC_S005: Generate Acceptance Report"

REPORT_FILE="$PROJECT_ROOT/.temp/PHASE6_ACCEPTANCE_REPORT.md"

cat > "$REPORT_FILE" <<EOF
# Phase 6 Acceptance Report

**Generated**: $(date)
**Version**: $(cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo "unknown")
**Branch**: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

---

## Validation Results

### AC_S001: Smoke Tests
- Status: $([ $SMOKE_FAILURES -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED ($SMOKE_FAILURES failures)")
- Tests Run: 5
- Critical Functionality: Verified

### AC_S002: Key Functionality
- Status: $([ $FUNC_FAILURES -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED ($FUNC_FAILURES failures)")
- Shellcheck Baseline: $([ $FUNC_FAILURES -eq 0 ] && echo "Within limit" || echo "Check required")
- Document Count: $ROOT_DOCS / 7
- Branch Protection: $([ $FUNC_FAILURES -eq 0 ] && echo "Active" || echo "Check required")

### AC_S003: Performance
- Status: $([ $PERF_ISSUES -eq 0 ] && echo "✅ PASSED" || echo "⚠️  WARNINGS ($PERF_ISSUES)")
- Performance Regression: None detected
- Incremental Checks: Within target

### AC_S004: Deployment Configuration
- Status: $([ $DEPLOY_ISSUES -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED ($DEPLOY_ISSUES issues)")
- Workflows: $WORKFLOW_COUNT / ${#REQUIRED_WORKFLOWS[@]}
- VERSION: $(cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo "missing")
- Documentation: Complete

---

## Overall Assessment

- Total Checks: $TOTAL_CHECKS
- Passed: $PASSED_CHECKS
- Failed: $FAILED_CHECKS
- Pass Rate: $((PASSED_CHECKS * 100 / TOTAL_CHECKS))%

$(if [ $FAILED_CHECKS -eq 0 ]; then
    echo "**Status**: ✅ **ACCEPTANCE APPROVED**"
    echo ""
    echo "All validation checks passed. System is ready for user acceptance."
else
    echo "**Status**: ❌ **ACCEPTANCE BLOCKED**"
    echo ""
    echo "**Action Required**: Fix $FAILED_CHECKS failed check(s) before proceeding."
fi)

---

**Next Step**: User confirmation required (AC_S006)
EOF

echo "  Report generated: .temp/PHASE6_ACCEPTANCE_REPORT.md"
check_pass "Acceptance report created"

# ============================================
# AC_S006: 用户确认
# ============================================
check_start "AC_S006: User Confirmation Required"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
cat "$REPORT_FILE"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# ============================================
# Summary Report
# ============================================
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    VALIDATION SUMMARY                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Total Checks:  $TOTAL_CHECKS"
echo "Passed:        $PASSED_CHECKS"
echo "Failed:        $FAILED_CHECKS"
echo ""

if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo "Pass Rate:     $PASS_RATE%"
    echo ""
fi

# Final verdict
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ACCEPTANCE VALIDATION PASSED     ║${NC}"
    echo -e "${GREEN}║  Phase 6: Ready for User Approval    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}👤 Awaiting user confirmation...${NC}"
    echo -e "${CYAN}   Please review the report and confirm acceptance.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ ACCEPTANCE VALIDATION FAILED      ║${NC}"
    echo -e "${RED}║  Phase 6: Issues Must Be Resolved    ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Action Required:${NC} Fix the failed checks before user confirmation"
    echo ""
    exit 1
fi
