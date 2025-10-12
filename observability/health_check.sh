#!/bin/bash
# Claude Enhancer Health Check Script
# Validates system readiness and SLO compliance

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Enhancer Health Check v6.2.0         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Helper function for checks
check() {
    local name="$1"
    local command="$2"
    local critical="${3:-false}"

    ((TOTAL_CHECKS++)) || true
    echo -n "🔍 Checking: $name... "

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED_CHECKS++)) || true
        return 0
    else
        if [ "$critical" = "true" ]; then
            echo -e "${RED}❌ FAIL (CRITICAL)${NC}"
            ((FAILED_CHECKS++)) || true
        else
            echo -e "${YELLOW}⚠️  WARNING${NC}"
            ((WARNING_CHECKS++)) || true
        fi
        return 1
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. Core System Components${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "Git availability" "command -v git" true || true
check "Python 3 availability" "command -v python3" true || true
check "Node.js availability" "command -v node" true || true
check "jq availability" "command -v jq" true || true
check "yq availability" "command -v yq" false || true

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. Configuration Files${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "VERSION file exists" "test -f VERSION" true || true
check "CHANGELOG.md exists" "test -f CHANGELOG.md" true || true
check "gates.yml exists" "test -f .workflow/gates.yml" true || true
check "manifest.yml exists" "test -f .workflow/manifest.yml" true || true
check "settings.json exists" "test -f .claude/settings.json" true || true

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. Claude Hooks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "branch_helper.sh exists" "test -f .claude/hooks/branch_helper.sh" true || true
check "agent_evidence_collector.sh exists" "test -f .claude/hooks/agent_evidence_collector.sh" true || true
check "task_namespace.sh exists" "test -f .claude/core/task_namespace.sh" true || true
check "atomic_ops.sh exists" "test -f .claude/core/atomic_ops.sh" true || true

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. Git Hooks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "pre-commit hook exists" "test -f .git/hooks/pre-commit" true || true
check "pre-commit hook executable" "test -x .git/hooks/pre-commit" true || true
check "commit-msg hook exists" "test -f .git/hooks/commit-msg" false || true
check "pre-push hook exists" "test -f .git/hooks/pre-push" true || true

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5. Observability & Monitoring${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "SLO definitions exist" "test -f observability/slo/slo.yml" true || true
check "Performance budget exists" "test -f metrics/perf_budget.yml" true || true
check "Metrics config exists" "test -f metrics/metrics.yml" true || true

# Count SLOs
if [ -f observability/slo/slo.yml ]; then
    SLO_COUNT=$(python3 -c "import yaml; f=open('observability/slo/slo.yml'); slos=yaml.safe_load(f); print(len(slos.get('slos', [])))" 2>/dev/null || echo "0")
    echo -e "   ${GREEN}→${NC} Found $SLO_COUNT SLO definitions"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6. Testing Infrastructure${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "Unit tests exist" "test -d test/unit" true || true
check "Integration tests exist" "test -d test/integration" true || true
check "Stress tests exist" "test -d test/stress" true || true
check "Test runner exists" "test -f test/run_all_tests.sh" true || true

# Check test results if available
if [ -f docs/TEST-REPORT.md ]; then
    echo -e "   ${GREEN}→${NC} Test report available: docs/TEST-REPORT.md"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}7. Documentation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "README.md exists" "test -f README.md" true || true
check "CLAUDE.md exists" "test -f CLAUDE.md" false || true
check "Review report exists" "test -f docs/REVIEW.md" false || true
check "Release notes exist" "test -f docs/RELEASE-6.2.0.md" false || true

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}8. Version Consistency${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VERSION=$(cat VERSION 2>/dev/null || echo "unknown")
echo -e "   ${BLUE}Version:${NC} $VERSION"

# Check version consistency across files
SETTINGS_VER=$(python3 -c "import json; print(json.load(open('.claude/settings.json'))['version'])" 2>/dev/null || echo "unknown")
MANIFEST_VER=$(python3 -c "import yaml; print(yaml.safe_load(open('.workflow/manifest.yml'))['version'])" 2>/dev/null || echo "unknown")
PACKAGE_VER=$(python3 -c "import json; print(json.load(open('package.json'))['version'])" 2>/dev/null || echo "unknown")

if [ "$VERSION" = "$SETTINGS_VER" ] && [ "$VERSION" = "$MANIFEST_VER" ] && [ "$VERSION" = "$PACKAGE_VER" ]; then
    echo -e "   ${GREEN}✅ All version files consistent ($VERSION)${NC}"
    ((PASSED_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
else
    echo -e "   ${RED}❌ Version inconsistency detected:${NC}"
    echo -e "      VERSION: $VERSION"
    echo -e "      settings.json: $SETTINGS_VER"
    echo -e "      manifest.yml: $MANIFEST_VER"
    echo -e "      package.json: $PACKAGE_VER"
    ((FAILED_CHECKS++)) || true
    ((TOTAL_CHECKS++)) || true
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}9. CI/CD Workflows${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

check "Unified gates workflow exists" "test -f .github/workflows/ce-unified-gates.yml" true || true
check "Branch protection workflow exists" "test -f .github/workflows/bp-guard.yml" false || true

WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" 2>/dev/null | wc -l)
echo -e "   ${GREEN}→${NC} Found $WORKFLOW_COUNT CI/CD workflow files"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}10. Phase & Gate Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ -f .phase/current ]; then
    CURRENT_PHASE=$(cat .phase/current)
    echo -e "   ${BLUE}Current Phase:${NC} $CURRENT_PHASE"
fi

# Check gate markers
GATE_DIR=$(find .gates -type d -name "*-*" 2>/dev/null | head -1)
if [ -n "$GATE_DIR" ]; then
    GATE_COUNT=$(find "$GATE_DIR" -name "*.ok" 2>/dev/null | wc -l)
    echo -e "   ${GREEN}→${NC} Completed gates: $GATE_COUNT"
    ls -1 "$GATE_DIR"/*.ok 2>/dev/null | sed 's/.*\///; s/\.ok$//' | sed 's/^/      /'
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Health Check Summary              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"

echo -e "   ${BLUE}Total Checks:${NC}    $TOTAL_CHECKS"
echo -e "   ${GREEN}✅ Passed:${NC}       $PASSED_CHECKS"
echo -e "   ${YELLOW}⚠️  Warnings:${NC}     $WARNING_CHECKS"
echo -e "   ${RED}❌ Failed:${NC}       $FAILED_CHECKS"

# Calculate pass rate
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "   ${BLUE}Pass Rate:${NC}       ${PASS_RATE}%"
fi

echo ""

# Determine overall status
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        ✅ System Status: HEALTHY               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    exit 0
elif [ $FAILED_CHECKS -le 2 ] && [ $PASSED_CHECKS -ge $((TOTAL_CHECKS * 80 / 100)) ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║      ⚠️  System Status: DEGRADED              ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════╝${NC}"
    exit 1
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║        ❌ System Status: UNHEALTHY             ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
    exit 2
fi
