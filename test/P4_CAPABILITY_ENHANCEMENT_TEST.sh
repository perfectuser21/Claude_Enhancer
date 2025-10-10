#!/bin/bash
# P4 Test Suite for Capability Enhancement System
# Version: 1.0.0
# Date: 2025-10-09

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test results
TEST_RESULTS=()

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   P4 Testing: Capability Enhancement System             ║"
echo "║   Testing P3 Deliverables                                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""

# Helper functions
pass_test() {
    local test_name="$1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    TEST_RESULTS+=("✅ PASS: $test_name")
    echo -e "${GREEN}✅ PASS${RESET}: $test_name"
}

fail_test() {
    local test_name="$1"
    local reason="$2"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    TEST_RESULTS+=("❌ FAIL: $test_name - $reason")
    echo -e "${RED}❌ FAIL${RESET}: $test_name"
    echo -e "${RED}   Reason: $reason${RESET}"
}

section() {
    echo ""
    echo -e "${CYAN}${BOLD}=== $1 ===${RESET}"
    echo ""
}

# ============================================================================
# Test Suite 1: Bootstrap Script Validation
# ============================================================================
section "Test Suite 1: Bootstrap Script"

# Test 1.1: Bootstrap script exists
if [ -f "tools/bootstrap.sh" ]; then
    pass_test "Bootstrap script exists (tools/bootstrap.sh)"
else
    fail_test "Bootstrap script exists" "File not found"
fi

# Test 1.2: Bootstrap script is executable
if [ -x "tools/bootstrap.sh" ]; then
    pass_test "Bootstrap script is executable"
else
    fail_test "Bootstrap script is executable" "Missing execute permission"
fi

# Test 1.3: Bootstrap script has correct shebang
if head -n1 tools/bootstrap.sh | grep -q "#!/usr/bin/env bash"; then
    pass_test "Bootstrap script has correct shebang"
else
    fail_test "Bootstrap script shebang" "Expected #!/usr/bin/env bash"
fi

# Test 1.4: Bootstrap has required functions
required_funcs=("detect_platform" "check_dependencies" "setup_git_hooks" "set_permissions" "verify_setup")
for func in "${required_funcs[@]}"; do
    if grep -q "^${func}()" tools/bootstrap.sh; then
        pass_test "Bootstrap has function: $func"
    else
        fail_test "Bootstrap function $func" "Function not found"
    fi
done

# Test 1.5: Bootstrap has error handling (set -euo pipefail)
if grep -q "set -euo pipefail" tools/bootstrap.sh; then
    pass_test "Bootstrap has error handling (set -euo pipefail)"
else
    fail_test "Bootstrap error handling" "Missing set -euo pipefail"
fi

# ============================================================================
# Test Suite 2: Pre-commit Auto-Branch Patch
# ============================================================================
section "Test Suite 2: Auto-Branch Creation Patch"

# Test 2.1: Patch exists in pre-commit
if grep -q "Patch B: 自动分支创建机制" .git/hooks/pre-commit; then
    pass_test "Auto-branch patch exists in pre-commit"
else
    fail_test "Auto-branch patch" "Patch B not found in pre-commit"
fi

# Test 2.2: CE_AUTOBRANCH environment variable check
if grep -q 'CE_AUTOBRANCH:-0' .git/hooks/pre-commit; then
    pass_test "CE_AUTOBRANCH environment variable check exists"
else
    fail_test "CE_AUTOBRANCH check" "Environment variable check not found"
fi

# Test 2.3: Auto-branch naming pattern
if grep -q 'feature/P1-auto-' .git/hooks/pre-commit; then
    pass_test "Auto-branch naming pattern (feature/P1-auto-TIMESTAMP)"
else
    fail_test "Auto-branch naming" "Naming pattern not found"
fi

# Test 2.4: Three solution options in error message
solution_count=$(grep -c "方式[123]:" .git/hooks/pre-commit || echo 0)
if [ "$solution_count" -ge 3 ]; then
    pass_test "Pre-commit provides 3 solution options"
else
    fail_test "Solution options" "Expected 3 options, found $solution_count"
fi

# ============================================================================
# Test Suite 3: AI Contract Documentation
# ============================================================================
section "Test Suite 3: AI Contract (AI_CONTRACT.md)"

# Test 3.1: AI Contract file exists
if [ -f "docs/AI_CONTRACT.md" ]; then
    pass_test "AI_CONTRACT.md exists"
else
    fail_test "AI_CONTRACT.md" "File not found"
fi

# Test 3.2: AI Contract has mandatory 3-step sequence
if grep -q "Step 1: Verify Git Repository Status" docs/AI_CONTRACT.md && \
   grep -q "Step 2: Ensure Proper Branch" docs/AI_CONTRACT.md && \
   grep -q "Step 3: Enter Claude Enhancer Workflow" docs/AI_CONTRACT.md; then
    pass_test "AI Contract has mandatory 3-step sequence"
else
    fail_test "3-step sequence" "One or more steps missing"
fi

# Test 3.3: AI Contract has all 5 rejection scenarios
for scenario in 1 2 3 4 5; do
    if grep -q "Scenario $scenario:" docs/AI_CONTRACT.md; then
        pass_test "AI Contract has Scenario $scenario"
    else
        fail_test "Scenario $scenario" "Not found in AI_CONTRACT.md"
    fi
done

# Test 3.4: AI Contract has phase-specific rules for P0-P7
phase_count=$(grep -c "^### P[0-7]" docs/AI_CONTRACT.md || echo 0)
if [ "$phase_count" -ge 8 ]; then
    pass_test "AI Contract has phase-specific rules (P0-P7)"
else
    fail_test "Phase-specific rules" "Expected 8 phases, found $phase_count"
fi

# Test 3.5: AI Contract has usage examples
if grep -q "Usage Example" docs/AI_CONTRACT.md && \
   grep -q "Correct Flow" docs/AI_CONTRACT.md && \
   grep -q "Incorrect Flow" docs/AI_CONTRACT.md; then
    pass_test "AI Contract has usage examples (correct and incorrect)"
else
    fail_test "Usage examples" "Missing usage examples"
fi

# ============================================================================
# Test Suite 4: Capability Matrix Documentation
# ============================================================================
section "Test Suite 4: Capability Matrix (CAPABILITY_MATRIX.md)"

# Test 4.1: Capability Matrix file exists
if [ -f "docs/CAPABILITY_MATRIX.md" ]; then
    pass_test "CAPABILITY_MATRIX.md exists"
else
    fail_test "CAPABILITY_MATRIX.md" "File not found"
fi

# Test 4.2: All C0-C9 capabilities documented
for cap_id in C0 C1 C2 C3 C4 C5 C6 C7 C8 C9; do
    if grep -q "### $cap_id:" docs/CAPABILITY_MATRIX.md; then
        pass_test "Capability $cap_id documented"
    else
        fail_test "Capability $cap_id" "Not found in matrix"
    fi
done

# Test 4.3: Each capability has verification dimensions
required_dimensions=("本地验证" "CI验证" "验证逻辑" "失败表现" "修复动作")
for cap in C0 C1 C2 C3 C4; do
    for dim in "${required_dimensions[@]}"; do
        if grep -A50 "### $cap:" docs/CAPABILITY_MATRIX.md | grep -q "$dim"; then
            pass_test "Capability $cap has dimension: $dim"
        else
            fail_test "$cap dimension: $dim" "Not found"
        fi
    done
done

# Test 4.4: Capability Matrix has test scripts section
if grep -q "## 🧪 测试验证" docs/CAPABILITY_MATRIX.md; then
    pass_test "Capability Matrix has test verification section"
else
    fail_test "Test verification section" "Not found in matrix"
fi

# Test 4.5: Capability Matrix has protection score
if grep -q "总体保障力" docs/CAPABILITY_MATRIX.md; then
    pass_test "Capability Matrix has overall protection score"
else
    fail_test "Protection score" "Not found in matrix"
fi

# ============================================================================
# Test Suite 5: Troubleshooting Guide
# ============================================================================
section "Test Suite 5: Troubleshooting Guide (TROUBLESHOOTING_GUIDE.md)"

# Test 5.1: Troubleshooting Guide exists
if [ -f "docs/TROUBLESHOOTING_GUIDE.md" ]; then
    pass_test "TROUBLESHOOTING_GUIDE.md exists"
else
    fail_test "TROUBLESHOOTING_GUIDE.md" "File not found"
fi

# Test 5.2: All FM-1 to FM-5 documented
failure_modes=("FM-1" "FM-2" "FM-3" "FM-4" "FM-5")
for fm in "${failure_modes[@]}"; do
    if grep -q "## 🔴 $fm:" docs/TROUBLESHOOTING_GUIDE.md || \
       grep -q "## 🟡 $fm:" docs/TROUBLESHOOTING_GUIDE.md || \
       grep -q "## 🟢 $fm:" docs/TROUBLESHOOTING_GUIDE.md; then
        pass_test "Failure mode $fm documented"
    else
        fail_test "Failure mode $fm" "Not found in guide"
    fi
done

# Test 5.3: Each FM has required sections
required_sections=("Description" "Symptoms" "Diagnostic Steps" "Fix Actions" "Verification" "Prevention")
for fm in FM-1 FM-2 FM-3; do
    for section in "${required_sections[@]}"; do
        if grep -A200 "$fm:" docs/TROUBLESHOOTING_GUIDE.md | grep -q "### .*$section"; then
            pass_test "$fm has section: $section"
        else
            fail_test "$fm section: $section" "Not found"
        fi
    done
done

# Test 5.4: Troubleshooting Guide has quick reference
if grep -q "Quick Reference Commands" docs/TROUBLESHOOTING_GUIDE.md; then
    pass_test "Troubleshooting Guide has quick reference"
else
    fail_test "Quick reference" "Not found in guide"
fi

# Test 5.5: Troubleshooting Guide has failure mode summary table
if grep -q "Failure Mode Summary" docs/TROUBLESHOOTING_GUIDE.md; then
    pass_test "Troubleshooting Guide has summary table"
else
    fail_test "Summary table" "Not found in guide"
fi

# ============================================================================
# Test Suite 6: File Size and Quality Checks
# ============================================================================
section "Test Suite 6: Documentation Quality"

# Test 6.1: AI Contract is comprehensive (>500 lines)
ai_contract_lines=$(wc -l < docs/AI_CONTRACT.md)
if [ "$ai_contract_lines" -ge 500 ]; then
    pass_test "AI Contract is comprehensive ($ai_contract_lines lines, ≥500 required)"
else
    fail_test "AI Contract comprehensiveness" "Only $ai_contract_lines lines, expected ≥500"
fi

# Test 6.2: Capability Matrix is comprehensive (>400 lines)
cap_matrix_lines=$(wc -l < docs/CAPABILITY_MATRIX.md)
if [ "$cap_matrix_lines" -ge 400 ]; then
    pass_test "Capability Matrix is comprehensive ($cap_matrix_lines lines, ≥400 required)"
else
    fail_test "Capability Matrix comprehensiveness" "Only $cap_matrix_lines lines, expected ≥400"
fi

# Test 6.3: Troubleshooting Guide is comprehensive (>1000 lines)
troubleshoot_lines=$(wc -l < docs/TROUBLESHOOTING_GUIDE.md)
if [ "$troubleshoot_lines" -ge 1000 ]; then
    pass_test "Troubleshooting Guide is comprehensive ($troubleshoot_lines lines, ≥1000 required)"
else
    fail_test "Troubleshooting Guide comprehensiveness" "Only $troubleshoot_lines lines, expected ≥1000"
fi

# Test 6.4: Total documentation exceeds 2000 lines
total_doc_lines=$((ai_contract_lines + cap_matrix_lines + troubleshoot_lines))
if [ "$total_doc_lines" -ge 2000 ]; then
    pass_test "Total documentation is comprehensive ($total_doc_lines lines, ≥2000 required)"
else
    fail_test "Total documentation" "Only $total_doc_lines lines, expected ≥2000"
fi

# ============================================================================
# Test Suite 7: Git Integration
# ============================================================================
section "Test Suite 7: Git Integration"

# Test 7.1: All gates signed (00-03)
for gate in 00 01 02 03; do
    if [ -f ".gates/${gate}.ok" ] && [ -f ".gates/${gate}.ok.sig" ]; then
        pass_test "Gate ${gate} is signed (ok + signature)"
    else
        fail_test "Gate ${gate}" "Missing ok file or signature"
    fi
done

# Test 7.2: Current phase is P4
current_phase=$(cat .phase/current 2>/dev/null || echo "NONE")
if [ "$current_phase" = "P4" ]; then
    pass_test "Current phase is P4 (testing)"
else
    fail_test "Current phase" "Expected P4, got $current_phase"
fi

# Test 7.3: On feature branch (not main)
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "NONE")
if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
    pass_test "On feature branch ($current_branch)"
else
    fail_test "Branch check" "Currently on protected branch: $current_branch"
fi

# ============================================================================
# Test Suite 8: Cross-Reference Validation
# ============================================================================
section "Test Suite 8: Cross-Reference Validation"

# Test 8.1: AI Contract references Capability Matrix
if grep -q "CAPABILITY_MATRIX.md" docs/AI_CONTRACT.md; then
    pass_test "AI Contract references Capability Matrix"
else
    fail_test "Cross-reference" "AI Contract doesn't reference Capability Matrix"
fi

# Test 8.2: AI Contract references Troubleshooting Guide
if grep -q "TROUBLESHOOTING_GUIDE.md" docs/AI_CONTRACT.md; then
    pass_test "AI Contract references Troubleshooting Guide"
else
    fail_test "Cross-reference" "AI Contract doesn't reference Troubleshooting Guide"
fi

# Test 8.3: Capability Matrix references Troubleshooting Guide
if grep -q "TROUBLESHOOTING_GUIDE.md" docs/CAPABILITY_MATRIX.md; then
    pass_test "Capability Matrix references Troubleshooting Guide"
else
    fail_test "Cross-reference" "Capability Matrix doesn't reference Troubleshooting Guide"
fi

# Test 8.4: Troubleshooting Guide references Capability Matrix
if grep -q "CAPABILITY_MATRIX.md" docs/TROUBLESHOOTING_GUIDE.md; then
    pass_test "Troubleshooting Guide references Capability Matrix"
else
    fail_test "Cross-reference" "Troubleshooting Guide doesn't reference Capability Matrix"
fi

# Test 8.5: Troubleshooting Guide references AI Contract
if grep -q "AI_CONTRACT.md" docs/TROUBLESHOOTING_GUIDE.md; then
    pass_test "Troubleshooting Guide references AI Contract"
else
    fail_test "Cross-reference" "Troubleshooting Guide doesn't reference AI Contract"
fi

# ============================================================================
# Test Results Summary
# ============================================================================
echo ""
echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   TEST RESULTS SUMMARY                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""

# Print all results
for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
done

echo ""
echo -e "${BOLD}Total Tests:${RESET} $TOTAL_TESTS"
echo -e "${GREEN}${BOLD}Passed:${RESET} $PASSED_TESTS"
echo -e "${RED}${BOLD}Failed:${RESET} $FAILED_TESTS"
echo ""

# Calculate success rate
if [ "$TOTAL_TESTS" -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "${BOLD}Success Rate:${RESET} ${SUCCESS_RATE}%"
    echo ""
    
    if [ "$SUCCESS_RATE" -eq 100 ]; then
        echo -e "${GREEN}${BOLD}"
        echo "╔═══════════════════════════════════════════════════════════╗"
        echo "║   🎉🎉🎉  ALL TESTS PASSED! 🎉🎉🎉                     ║"
        echo "║   Capability Enhancement System is PRODUCTION READY!     ║"
        echo "╚═══════════════════════════════════════════════════════════╝"
        echo -e "${RESET}"
        exit 0
    elif [ "$SUCCESS_RATE" -ge 90 ]; then
        echo -e "${YELLOW}${BOLD}"
        echo "╔═══════════════════════════════════════════════════════════╗"
        echo "║   ⚠️  TESTS MOSTLY PASSED (≥90%)                        ║"
        echo "║   Review failed tests before proceeding                  ║"
        echo "╚═══════════════════════════════════════════════════════════╝"
        echo -e "${RESET}"
        exit 1
    else
        echo -e "${RED}${BOLD}"
        echo "╔═══════════════════════════════════════════════════════════╗"
        echo "║   ❌ TESTS FAILED (<90%)                                 ║"
        echo "║   Fix issues before proceeding to next phase             ║"
        echo "╚═══════════════════════════════════════════════════════════╝"
        echo -e "${RESET}"
        exit 1
    fi
fi
