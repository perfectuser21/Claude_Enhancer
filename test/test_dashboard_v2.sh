#!/bin/bash
# Dashboard v2 Comprehensive Test Suite
# Tests: Parsers, API endpoints, caching, HTML rendering
#
# Version: 7.2.0
# Expected: 100% pass rate

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="/home/xx/dev/Claude Enhancer"
cd "$PROJECT_ROOT"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result tracking
pass() {
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
    echo -e "${RED}✗${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Dashboard v2 Test Suite                               ║"
echo "║     Comprehensive Testing                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Test 1: Python Files Exist
# ============================================================================
echo "[1] File Existence Tests"
echo "----------------------------------------"

if [[ -f "tools/data_models.py" ]]; then
    pass "data_models.py exists"
else
    fail "data_models.py missing"
fi

if [[ -f "tools/parsers.py" ]]; then
    pass "parsers.py exists"
else
    fail "parsers.py missing"
fi

if [[ -f "tools/cache.py" ]]; then
    pass "cache.py exists"
else
    fail "cache.py missing"
fi

if [[ -f "tools/dashboard_v2_minimal.py" ]]; then
    pass "dashboard_v2_minimal.py exists"
else
    fail "dashboard_v2_minimal.py missing"
fi

if [[ -f "tools/dashboard_v2.html" ]]; then
    pass "dashboard_v2.html exists"
else
    fail "dashboard_v2.html missing"
fi

echo ""

# ============================================================================
# Test 2: Python Syntax Validation
# ============================================================================
echo "[2] Python Syntax Validation"
echo "----------------------------------------"

if python3 -m py_compile tools/data_models.py 2>/dev/null; then
    pass "data_models.py syntax valid"
else
    fail "data_models.py syntax error"
fi

if python3 -m py_compile tools/parsers.py 2>/dev/null; then
    pass "parsers.py syntax valid"
else
    fail "parsers.py syntax error"
fi

if python3 -m py_compile tools/cache.py 2>/dev/null; then
    pass "cache.py syntax valid"
else
    fail "cache.py syntax error"
fi

if python3 -m py_compile tools/dashboard_v2_minimal.py 2>/dev/null; then
    pass "dashboard_v2_minimal.py syntax valid"
else
    fail "dashboard_v2_minimal.py syntax error"
fi

echo ""

# ============================================================================
# Test 3: Import Tests (Verify module dependencies)
# ============================================================================
echo "[3] Module Import Tests"
echo "----------------------------------------"

# Test data_models imports
if python3 -c "import sys; sys.path.insert(0, 'tools'); from data_models import Capability, Feature, Decision" 2>/dev/null; then
    pass "data_models imports work"
else
    fail "data_models import failed"
fi

# Test parsers imports (depends on data_models)
if python3 -c "import sys; sys.path.insert(0, 'tools'); from parsers import CapabilityParser, FeatureParser" 2>/dev/null; then
    pass "parsers imports work"
else
    fail "parsers import failed"
fi

# Test cache imports
if python3 -c "import sys; sys.path.insert(0, 'tools'); from cache import SimpleCache" 2>/dev/null; then
    pass "cache imports work"
else
    fail "cache import failed"
fi

echo ""

# ============================================================================
# Test 4: Start Dashboard Server
# ============================================================================
echo "[4] Dashboard Server Tests"
echo "----------------------------------------"

# Kill any existing dashboard
pkill -f dashboard_v2_minimal.py || true
sleep 1

# Start dashboard in background
python3 tools/dashboard_v2_minimal.py > /tmp/dashboard_test.log 2>&1 &
DASH_PID=$!
info "Started dashboard with PID: $DASH_PID"

# Wait for startup
sleep 3

# Check if process is running
if ps -p $DASH_PID > /dev/null 2>&1; then
    pass "Dashboard process running"
else
    fail "Dashboard process failed to start"
    cat /tmp/dashboard_test.log
fi

echo ""

# ============================================================================
# Test 5: API Endpoint Tests
# ============================================================================
echo "[5] API Endpoint Tests"
echo "----------------------------------------"

# Test /api/health
HTTP_CODE=$(curl -s -o /tmp/health.json -w "%{http_code}" http://localhost:8888/api/health)
if [[ "$HTTP_CODE" == "200" ]]; then
    pass "/api/health returns 200"

    # Verify JSON structure
    if python3 -c "import json; d=json.load(open('/tmp/health.json')); assert d['status']=='healthy'; assert 'version' in d" 2>/dev/null; then
        pass "/api/health JSON valid"
    else
        fail "/api/health JSON invalid"
    fi
else
    fail "/api/health returns $HTTP_CODE (expected 200)"
fi

# Test /api/capabilities
HTTP_CODE=$(curl -s -o /tmp/capabilities.json -w "%{http_code}" http://localhost:8888/api/capabilities)
if [[ "$HTTP_CODE" == "200" ]]; then
    pass "/api/capabilities returns 200"

    # Verify structure
    if python3 -c "import json; d=json.load(open('/tmp/capabilities.json')); assert 'core_stats' in d; assert 'features' in d" 2>/dev/null; then
        pass "/api/capabilities JSON valid"

        FEATURE_COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/capabilities.json'))['features']))")
        info "Features found: $FEATURE_COUNT"
    else
        fail "/api/capabilities JSON invalid"
    fi
else
    fail "/api/capabilities returns $HTTP_CODE"
fi

# Test /api/learning
HTTP_CODE=$(curl -s -o /tmp/learning.json -w "%{http_code}" http://localhost:8888/api/learning)
if [[ "$HTTP_CODE" == "200" ]]; then
    pass "/api/learning returns 200"

    if python3 -c "import json; d=json.load(open('/tmp/learning.json')); assert 'decisions' in d; assert 'statistics' in d" 2>/dev/null; then
        pass "/api/learning JSON valid"
    else
        fail "/api/learning JSON invalid"
    fi
else
    fail "/api/learning returns $HTTP_CODE"
fi

# Test /api/projects
HTTP_CODE=$(curl -s -o /tmp/projects.json -w "%{http_code}" http://localhost:8888/api/projects)
if [[ "$HTTP_CODE" == "200" ]]; then
    pass "/api/projects returns 200"

    if python3 -c "import json; d=json.load(open('/tmp/projects.json')); assert 'projects' in d; assert 'summary' in d" 2>/dev/null; then
        pass "/api/projects JSON valid"

        PROJECT_COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/projects.json'))['projects']))")
        info "Projects found: $PROJECT_COUNT"
    else
        fail "/api/projects JSON invalid"
    fi
else
    fail "/api/projects returns $HTTP_CODE"
fi

# Test / (HTML dashboard)
HTTP_CODE=$(curl -s -o /tmp/dashboard.html -w "%{http_code}" http://localhost:8888/)
if [[ "$HTTP_CODE" == "200" ]]; then
    pass "/ returns 200"

    HTML_SIZE=$(wc -c < /tmp/dashboard.html)
    if [[ $HTML_SIZE -gt 10000 ]]; then
        pass "HTML size > 10KB ($HTML_SIZE bytes)"
    else
        fail "HTML too small ($HTML_SIZE bytes)"
    fi

    # Check for critical content
    if grep -q "CE Comprehensive Dashboard v2" /tmp/dashboard.html; then
        pass "HTML contains title"
    else
        fail "HTML missing title"
    fi

    if grep -q "CE Capabilities" /tmp/dashboard.html; then
        pass "HTML contains CE Capabilities section"
    else
        fail "HTML missing CE Capabilities section"
    fi

    if grep -q "Multi-Project Monitoring" /tmp/dashboard.html; then
        pass "HTML contains Project Monitoring section"
    else
        fail "HTML missing Project Monitoring section"
    fi
else
    fail "/ returns $HTTP_CODE"
fi

echo ""

# ============================================================================
# Test 6: Caching Tests
# ============================================================================
echo "[6] Caching Performance Tests"
echo "----------------------------------------"

# First request (cold cache)
START=$(date +%s%N)
curl -s http://localhost:8888/api/capabilities > /dev/null
END=$(date +%s%N)
COLD_TIME=$(( (END - START) / 1000000 ))
info "Cold cache: ${COLD_TIME}ms"

# Second request (warm cache)
START=$(date +%s%N)
curl -s http://localhost:8888/api/capabilities > /dev/null
END=$(date +%s%N)
WARM_TIME=$(( (END - START) / 1000000 ))
info "Warm cache: ${WARM_TIME}ms"

if [[ $WARM_TIME -lt $COLD_TIME ]]; then
    pass "Cache is working (warm < cold)"
else
    fail "Cache not effective (warm >= cold)"
fi

if [[ $WARM_TIME -lt 100 ]]; then
    pass "Cached response < 100ms"
else
    fail "Cached response too slow (${WARM_TIME}ms)"
fi

echo ""

# ============================================================================
# Test 7: Parser Unit Tests
# ============================================================================
echo "[7] Parser Unit Tests"
echo "----------------------------------------"

# Test FeatureParser
FEATURE_TEST=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, 'tools')
from parsers import FeatureParser
from pathlib import Path

parser = FeatureParser(Path('tools/web/dashboard.html'))
result = parser.parse()

if result.success:
    features = result.data
    print(f"PASS:{len(features)}")
else:
    print(f"FAIL:{result.error_message}")
PYEOF
)

if [[ "$FEATURE_TEST" == PASS:* ]]; then
    FEATURE_COUNT=${FEATURE_TEST#PASS:}
    if [[ $FEATURE_COUNT -eq 12 ]]; then
        pass "FeatureParser found 12 features"
    else
        fail "FeatureParser found $FEATURE_COUNT features (expected 12)"
    fi
else
    fail "FeatureParser failed: ${FEATURE_TEST#FAIL:}"
fi

echo ""

# ============================================================================
# Test 8: Core Stats Validation
# ============================================================================
echo "[8] Core Stats Validation"
echo "----------------------------------------"

CORE_STATS=$(curl -s http://localhost:8888/api/capabilities | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['core_stats']['total_phases']}:{d['core_stats']['total_checkpoints']}:{d['core_stats']['quality_gates']}:{d['core_stats']['hard_blocks']}\")")

IFS=':' read -r PHASES CHECKPOINTS GATES BLOCKS <<< "$CORE_STATS"

if [[ "$PHASES" == "7" ]]; then
    pass "Total phases = 7"
else
    fail "Total phases = $PHASES (expected 7)"
fi

if [[ "$CHECKPOINTS" == "97" ]]; then
    pass "Total checkpoints = 97"
else
    fail "Total checkpoints = $CHECKPOINTS (expected 97)"
fi

if [[ "$GATES" == "2" ]]; then
    pass "Quality gates = 2"
else
    fail "Quality gates = $GATES (expected 2)"
fi

if [[ "$BLOCKS" == "8" ]]; then
    pass "Hard blocks = 8"
else
    fail "Hard blocks = $BLOCKS (expected 8)"
fi

echo ""

# ============================================================================
# Cleanup
# ============================================================================
info "Stopping dashboard..."
kill $DASH_PID 2>/dev/null || true
wait $DASH_PID 2>/dev/null || true

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    TEST SUMMARY                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests:   $TESTS_RUN"
echo "Passed:        $TESTS_PASSED"
echo "Failed:        $TESTS_FAILED"
echo ""

PASS_RATE=$(( TESTS_PASSED * 100 / TESTS_RUN ))
echo "Pass Rate:     ${PASS_RATE}%"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL TESTS PASSED                 ║${NC}"
    echo -e "${GREEN}║  Dashboard v2 is ready for Phase 4   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME TESTS FAILED                  ║${NC}"
    echo -e "${RED}║  Review failures before proceeding    ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════╝${NC}"
    exit 1
fi
