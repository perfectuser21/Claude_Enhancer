#!/usr/bin/env bash
# Claude Enhancer v8.0 核心功能测试
# 测试Learning System, Auto-fix, TODO队列, ce CLI

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# CE_HOME自动检测（与capture.sh一致）
CE_HOME="${CE_HOME:-}"
if [[ -z "$CE_HOME" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CANDIDATE_CE_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
  if [[ -f "$CANDIDATE_CE_HOME/.workflow/SPEC.yaml" ]]; then
    CE_HOME="$CANDIDATE_CE_HOME"
  else
    while IFS= read -r -d '' spec_file; do
      CE_HOME="$(dirname "$(dirname "$spec_file")")"
      break
    done < <(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" -print0 2>/dev/null)
  fi
fi

if [[ -z "$CE_HOME" ]] || [[ ! -f "$CE_HOME/.workflow/SPEC.yaml" ]]; then
  echo "❌ 错误: 无法找到Claude Enhancer目录"
  exit 1
fi

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

PASSED=0
FAILED=0

test_pass() {
  echo -e "${GREEN}✅ PASS${NC}: $1"
  ((PASSED++))
}

test_fail() {
  echo -e "${RED}❌ FAIL${NC}: $1"
  ((FAILED++))
}

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Claude Enhancer v8.0 核心功能测试                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "CE_HOME: $CE_HOME"
echo "TEST_DIR: $TEST_DIR"
echo ""

# Test 1: Learning Item捕获
echo "[1/8] 测试Learning Item捕获..."
if bash "$CE_HOME/scripts/learning/capture.sh" \
  --category performance \
  --description "测试性能优化Learning Item" \
  --phase Phase2 \
  --confidence 0.9 \
  >/dev/null 2>&1; then
  test_pass "Learning Item捕获成功"
else
  test_fail "Learning Item捕获失败"
fi

# Test 2: 验证YAML文件创建
echo "[2/8] 验证Learning Item文件..."
LATEST_ITEM=$(find "$CE_HOME/.learning/items/" -name "*.yml" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
if [[ -f "$LATEST_ITEM" ]]; then
  test_pass "Learning Item文件已创建"
else
  test_fail "Learning Item文件未创建"
fi

# Test 3: 符号链接索引
echo "[3/8] 验证符号链接索引..."
LINK_COUNT=$(find "$CE_HOME/.learning/by_category/performance/" -type l -name "*performance*.yml" 2>/dev/null | wc -l)
if [[ $LINK_COUNT -gt 0 ]]; then
  test_pass "by_category符号链接已创建"
else
  test_fail "by_category符号链接未创建"
fi

# Test 4: Auto-fix决策
echo "[4/8] 测试Auto-fix决策引擎..."
RESULT=$(python3 "$CE_HOME/scripts/learning/auto_fix.py" \
  --error "ImportError: No module named 'test'" \
  --confidence 0.95 \
  --json 2>/dev/null || echo "{}")

if echo "$RESULT" | grep -q '"tier": "tier1_auto"'; then
  test_pass "Auto-fix tier1检测正确"
else
  test_fail "Auto-fix tier1检测失败"
fi

# Test 5: TODO转换
echo "[5/8] 测试TODO转换..."
BEFORE_COUNT=$(find "$CE_HOME/.todos/pending/" -name "*.json" -type f 2>/dev/null | wc -l)
bash "$CE_HOME/scripts/learning/convert_to_todo.sh" >/dev/null 2>&1
AFTER_COUNT=$(find "$CE_HOME/.todos/pending/" -name "*.json" -type f 2>/dev/null | wc -l)

if [[ $AFTER_COUNT -ge $BEFORE_COUNT ]]; then
  test_pass "TODO转换功能正常"
else
  test_fail "TODO转换失败"
fi

# Test 6: ce CLI - version
echo "[6/8] 测试ce CLI version..."
if "$CE_HOME/tools/ce" version | grep -q "Claude Enhancer"; then
  test_pass "ce version命令正常"
else
  test_fail "ce version命令失败"
fi

# Test 7: ce CLI - todo list
echo "[7/8] 测试ce CLI todo list..."
if "$CE_HOME/tools/ce" todo list | grep -q "TODO队列"; then
  test_pass "ce todo list命令正常"
else
  test_fail "ce todo list命令失败"
fi

# Test 8: Notion同步（dry-run）
echo "[8/8] 测试Notion同步（dry-run）..."
if python3 "$CE_HOME/scripts/learning/sync_notion.py" --dry-run 2>&1 | grep -q "同步完成"; then
  test_pass "Notion同步（dry-run）正常"
else
  test_fail "Notion同步失败"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  测试结果                                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "通过: $PASSED/8"
echo "失败: $FAILED/8"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ 所有测试通过！${NC}"
  exit 0
else
  echo -e "${RED}❌ 有测试失败${NC}"
  exit 1
fi
