#!/usr/bin/env bash
# Simplified Test Suite for Impact Radius Assessor
# 80+ comprehensive test cases

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSESSOR="$PROJECT_ROOT/.claude/scripts/impact_radius_assessor.sh"

# Colors
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; NC='\033[0m'

# Counters
TOTAL=0; PASS=0; FAIL=0

# Test function
test_case() {
    local task="$1" expected="$2" name="$3"
    ((TOTAL++))

    local actual
    actual=$("$ASSESSOR" "$task" 2>/dev/null | jq -r '.agent_strategy.min_agents // "error"')

    if [ "$actual" = "$expected" ]; then
        echo -e "${G}✓${NC} $name"
        ((PASS++))
    else
        echo -e "${R}✗${NC} $name (Expected: $expected, Got: $actual)"
        ((FAIL++))
    fi
}

echo -e "${B}═══════════════════════════════════════════════════${NC}"
echo -e "${B}  Impact Radius Assessor - Test Suite (80+ tests)${NC}"
echo -e "${B}═══════════════════════════════════════════════════${NC}\n"

# Test Suite 1: High-Risk Tasks (6 agents) - 15 tests
echo -e "${B}Test Suite 1: High-Risk Tasks (15 tests)${NC}"
test_case "Fix CVE-2024-1234 vulnerability" 6 "T1.01: CVE fix"
test_case "Security breach in authentication" 6 "T1.02: Security breach"
test_case "Patch critical exploit" 6 "T1.03: Exploit patch"
test_case "Migrate database to PostgreSQL" 6 "T1.04: Database migration"
test_case "Refactor authentication system" 6 "T1.05: Auth refactor"
test_case "Architecture redesign" 6 "T1.06: Architecture"
test_case "Distributed system implementation" 6 "T1.07: Distributed system"
test_case "Critical bug in production" 6 "T1.08: Critical production bug"
test_case "System-wide configuration change" 6 "T1.09: System-wide change"
test_case "Entire codebase refactor" 6 "T1.10: Entire refactor"
test_case "修复安全漏洞" 6 "T1.11: Chinese security"
test_case "重构系统架构" 6 "T1.12: Chinese architecture"
test_case "数据库迁移" 6 "T1.13: Chinese DB migration"
test_case "Fix security vulnerability in payment" 6 "T1.14: Payment security"
test_case "Implement distributed session management" 6 "T1.15: Distributed sessions"

# Test Suite 2: Medium-Risk Tasks (3 agents) - 20 tests
echo -e "\n${B}Test Suite 2: Medium-Risk Tasks (20 tests)${NC}"
test_case "Fix bug in login page" 3 "T2.01: Login bug"
test_case "Optimize API query performance" 3 "T2.02: API optimization"
test_case "Refactor user management module" 3 "T2.03: Module refactor"
test_case "Add logging functionality" 3 "T2.04: Add logging"
test_case "Update dependency packages" 3 "T2.05: Update dependencies"
test_case "Improve error handling" 3 "T2.06: Error handling"
test_case "Add unit tests for core" 3 "T2.07: Unit tests"
test_case "Performance benchmarking" 3 "T2.08: Benchmarking"
test_case "Code review fixes" 3 "T2.09: Review fixes"
test_case "Refactor database queries" 3 "T2.10: Query refactor"
test_case "Fix memory leak" 3 "T2.11: Memory leak"
test_case "Optimize rendering performance" 3 "T2.12: Rendering optimization"
test_case "Update API endpoints" 3 "T2.13: API endpoints"
test_case "Add caching layer" 3 "T2.14: Caching"
test_case "Improve code structure" 3 "T2.15: Code structure"
test_case "优化数据库查询性能" 3 "T2.16: Chinese optimization"
test_case "修复登录页面错误" 3 "T2.17: Chinese login fix"
test_case "Add validation logic" 3 "T2.18: Validation"
test_case "Update configuration settings" 3 "T2.19: Config update"
test_case "Implement retry mechanism" 3 "T2.20: Retry mechanism"

# Test Suite 3: Low-Risk Tasks (0 agents) - 20 tests
echo -e "\n${B}Test Suite 3: Low-Risk Tasks (20 tests)${NC}"
test_case "Fix typo in README" 0 "T3.01: README typo"
test_case "Update code comments" 0 "T3.02: Comment update"
test_case "Format code style" 0 "T3.03: Code formatting"
test_case "Add TODO markers" 0 "T3.04: TODO markers"
test_case "Fix spelling errors in variables" 0 "T3.05: Spelling errors"
test_case "Cleanup temporary files" 0 "T3.06: Cleanup"
test_case "Update documentation" 0 "T3.07: Documentation"
test_case "Rename variables for readability" 0 "T3.08: Variable rename"
test_case "Add comments to functions" 0 "T3.09: Add comments"
test_case "Fix indentation" 0 "T3.10: Indentation"
test_case "Update README sections" 0 "T3.11: README update"
test_case "Fix grammar in docs" 0 "T3.12: Grammar fix"
test_case "Add inline documentation" 0 "T3.13: Inline docs"
test_case "Update changelog" 0 "T3.14: Changelog"
test_case "Format JSON files" 0 "T3.15: JSON formatting"
test_case "更新开发文档" 0 "T3.16: Chinese doc update"
test_case "Clean up code style" 0 "T3.17: Style cleanup"
test_case "Remove unused comments" 0 "T3.18: Remove comments"
test_case "Update license headers" 0 "T3.19: License headers"
test_case "Add whitespace for readability" 0 "T3.20: Whitespace"

# Test Suite 4: Compound/Mixed Tasks - 10 tests
echo -e "\n${B}Test Suite 4: Compound/Mixed Tasks (10 tests)${NC}"
test_case "Fix README typo and refactor authentication" 6 "T4.01: Typo + auth (high wins)"
test_case "Update docs and fix CVE-2024-5678" 6 "T4.02: Docs + CVE (high wins)"
test_case "Format code and migrate database" 6 "T4.03: Format + migrate (high wins)"
test_case "Fix bug and update comments" 3 "T4.04: Bug + comments (medium wins)"
test_case "Optimize and fix typos" 3 "T4.05: Optimize + typo (medium wins)"
test_case "Fix typo and update docs" 0 "T4.06: Typo + docs (low)"
test_case "Cleanup and formatting" 0 "T4.07: Cleanup + format (low)"
test_case "Critical security issue in production" 6 "T4.08: Complex compound (high)"
test_case "Small bug fix in module" 3 "T4.09: Small bug (medium)"
test_case "Performance optimization with architecture" 6 "T4.10: Perf + arch (high)"

# Test Suite 5: Edge Cases - 10 tests
echo -e "\n${B}Test Suite 5: Edge Cases (10 tests)${NC}"
test_case "Fix 🐛 bug with emojis" 3 "T5.01: Emoji handling"
test_case "Update path/to/file.js" 0 "T5.02: Path handling"
test_case "Fix bug in user@domain.com" 3 "T5.03: Email symbol"
test_case "FIX CVE-2024-1234 SECURITY" 6 "T5.04: All caps"
test_case "fix    bug    with    spaces" 3 "T5.05: Multiple spaces"
test_case "Fix bug"$'\n'"in code" 3 "T5.06: Newline handling"
test_case "xyz123 unknown pattern qwerty" 3 "T5.07: No pattern match"
test_case "修正代码中的错误" 3 "T5.08: Chinese fix"
test_case "ARCHITECTURE REDESIGN" 6 "T5.09: Uppercase detection"
test_case "update DOCUMENTATION and README" 0 "T5.10: Mixed case docs"

# Test Suite 6: Boundary Cases - 5 tests
echo -e "\n${B}Test Suite 6: Boundary Cases (5 tests)${NC}"
test_case "Small bug in security validation" 5 "T6.01: Boundary 45-49 points" || \
test_case "Small bug in security validation" 6 "T6.01: Boundary 45-49 points (alt)"
test_case "Refactor single function" 3 "T6.02: Boundary 30-34 points"
test_case "Update one line of code" 0 "T6.03: Boundary 25-29 points"
test_case "Critical comment update" 0 "T6.04: Critical + doc (doc wins)"
test_case "Simple architecture review" 6 "T6.05: Simple + arch (arch wins)"

# Performance Test
echo -e "\n${B}Performance Test (1 test)${NC}"
START=$(date +%s%N)
for i in {1..10}; do
    "$ASSESSOR" "Fix bug $i" >/dev/null 2>&1
done
END=$(date +%s%N)
DURATION=$(( (END - START) / 10000000 ))
if [ "$DURATION" -lt 100 ]; then
    echo -e "${G}✓${NC} T7.01: Average execution <100ms (${DURATION}ms avg for 10 runs)"
    ((TOTAL++)); ((PASS++))
else
    echo -e "${R}✗${NC} T7.01: Average execution >100ms (${DURATION}ms avg)"
    ((TOTAL++)); ((FAIL++))
fi

# Summary
echo -e "\n${B}═══════════════════════════════════════════════════${NC}"
echo -e "${B}  Test Results Summary${NC}"
echo -e "${B}═══════════════════════════════════════════════════${NC}"
echo -e "\nTotal Tests:  $TOTAL"
echo -e "${G}Passed:       $PASS${NC}"
echo -e "${R}Failed:       $FAIL${NC}"

PASS_RATE=$(( PASS * 100 / TOTAL ))
echo -e "\n${B}Pass Rate:    ${PASS_RATE}%${NC}"

if [ "$FAIL" -eq 0 ]; then
    echo -e "\n${G}✓ ALL $TOTAL TESTS PASSED${NC}"
    exit 0
else
    echo -e "\n${R}✗ $FAIL TEST(S) FAILED${NC}"
    exit 1
fi
