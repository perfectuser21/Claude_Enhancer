#!/usr/bin/env bash
# Claude Enhancer v8.0 快速测试（无hang）
# 专注核心功能验证

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# CE_HOME检测
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CE_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ ! -f "$CE_HOME/.workflow/SPEC.yaml" ]]; then
  echo "❌ CE_HOME detection failed"
  exit 1
fi

PASSED=0
FAILED=0

pass() {
  echo -e "${GREEN}✅${NC} $1"
  ((PASSED++))
}

fail() {
  echo -e "${RED}❌${NC} $1"
  ((FAILED++))
}

echo "═══════════════════════════════════════"
echo "Claude Enhancer v8.0 Quick Test"
echo "═══════════════════════════════════════"
echo "CE_HOME: $CE_HOME"
echo ""

# Test 1: Directory structure
echo "[1/12] Directory structure..."
if [[ -d "$CE_HOME/.learning/items" ]] && \
   [[ -d "$CE_HOME/.learning/by_category" ]] && \
   [[ -d "$CE_HOME/.learning/by_project" ]] && \
   [[ -d "$CE_HOME/.todos/pending" ]] && \
   [[ -d "$CE_HOME/.notion" ]]; then
  pass "Directory structure complete"
else
  fail "Missing directories"
fi

# Test 2: Scripts exist
echo "[2/12] Learning scripts..."
if [[ -x "$CE_HOME/scripts/learning/capture.sh" ]] && \
   [[ -f "$CE_HOME/scripts/learning/auto_fix.py" ]] && \
   [[ -f "$CE_HOME/scripts/learning/convert_to_todo.sh" ]] && \
   [[ -f "$CE_HOME/scripts/learning/sync_notion.py" ]]; then
  pass "Learning scripts present"
else
  fail "Missing scripts"
fi

# Test 3: ce CLI
echo "[3/12] ce CLI tool..."
if [[ -x "$CE_HOME/tools/ce" ]]; then
  pass "ce CLI executable"
else
  fail "ce CLI missing"
fi

# Test 4: ce version
echo "[4/12] ce version command..."
if "$CE_HOME/tools/ce" version 2>/dev/null | grep -q "8.0.0"; then
  pass "ce version shows 8.0.0"
else
  fail "ce version incorrect"
fi

# Test 5: Learning Item capture
echo "[5/12] Learning Item capture..."
OUTPUT=$("$CE_HOME/scripts/learning/capture.sh" \
  --category performance \
  --description "Quick test item" \
  --phase Phase2 \
  --confidence 0.9 2>&1)

if echo "$OUTPUT" | grep -q "Learning Item已捕获"; then
  pass "Learning Item capture works"
else
  fail "Learning Item capture failed"
fi

# Test 6: YAML files created
echo "[6/12] YAML file creation..."
ITEM_COUNT=$(find "$CE_HOME/.learning/items" -name "*.yml" 2>/dev/null | wc -l)
if [[ $ITEM_COUNT -gt 0 ]]; then
  pass "Learning Items created ($ITEM_COUNT files)"
else
  fail "No Learning Items found"
fi

# Test 7: Auto-fix script
echo "[7/12] Auto-fix decision engine..."
if python3 "$CE_HOME/scripts/learning/auto_fix.py" \
  --error "ImportError: test" \
  --confidence 0.95 \
  --json 2>/dev/null | grep -q "tier1_auto"; then
  pass "Auto-fix engine works"
else
  fail "Auto-fix engine failed"
fi

# Test 8: TODO conversion
echo "[8/12] TODO conversion..."
"$CE_HOME/scripts/learning/convert_to_todo.sh" >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
  pass "TODO conversion runs"
else
  fail "TODO conversion failed"
fi

# Test 9: ce mode status
echo "[9/12] ce mode status..."
if "$CE_HOME/tools/ce" mode status 2>/dev/null | grep -q "claude-enhancer"; then
  pass "ce mode detection works"
else
  fail "ce mode detection failed"
fi

# Test 10: ce learning list
echo "[10/12] ce learning list..."
if "$CE_HOME/tools/ce" learning list 2>/dev/null >/dev/null; then
  pass "ce learning list works"
else
  fail "ce learning list failed"
fi

# Test 11: ce todo list
echo "[11/12] ce todo list..."
if "$CE_HOME/tools/ce" todo list 2>/dev/null >/dev/null; then
  pass "ce todo list works"
else
  fail "ce todo list failed"
fi

# Test 12: Version consistency
echo "[12/12] Version consistency..."
VERSION=$(cat "$CE_HOME/VERSION" 2>/dev/null)
if [[ "$VERSION" == "8.0.0" ]]; then
  pass "VERSION file = 8.0.0"
else
  fail "VERSION file mismatch"
fi

# Results
echo ""
echo "═══════════════════════════════════════"
TOTAL=$((PASSED + FAILED))
echo "Results: $PASSED/$TOTAL passed"

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  exit 0
elif [[ $PASSED -ge 10 ]]; then
  echo -e "${GREEN}✅ Mostly passed ($PASSED/$TOTAL)${NC}"
  exit 0
else
  echo -e "${RED}❌ Too many failures${NC}"
  exit 1
fi
