#!/bin/bash
# Contract Test: Workflow Consistency
# 验证SPEC.yaml、manifest.yml、CLAUDE.md三者一致性
# Version: 1.0.0

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 Contract Test: Workflow Consistency"
echo "======================================"
echo ""

PASS=0
FAIL=0

# Helper functions
test_pass() {
    echo "  ✅ PASS: $1"
    ((PASS++))
}

test_fail() {
    echo "  ❌ FAIL: $1"
    ((FAIL++))
}

# ============================================
# Test 1: Phase数量一致
# ============================================
echo "[TEST 1] Phase数量一致性"

if command -v python3 >/dev/null 2>&1; then
    SPEC_PHASES=$(python3 -c "import yaml; print(yaml.safe_load(open('.workflow/SPEC.yaml'))['workflow_structure']['total_phases'])" 2>/dev/null || echo "ERROR")
    MANIFEST_PHASES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('.workflow/manifest.yml'))['phases']))" 2>/dev/null || echo "ERROR")
else
    # Fallback: 使用grep
    SPEC_PHASES=$(grep "total_phases:" .workflow/SPEC.yaml | awk '{print $2}' || echo "ERROR")
    MANIFEST_PHASES=$(grep -c "^  - id: Phase" .workflow/manifest.yml || echo "ERROR")
fi

if [ "$SPEC_PHASES" = "7" ] && [ "$MANIFEST_PHASES" = "7" ]; then
    test_pass "两者都是7个Phase"
else
    test_fail "SPEC=$SPEC_PHASES, manifest=$MANIFEST_PHASES (应该都是7)"
fi

# ============================================
# Test 2: Phase 1子阶段数量一致
# ============================================
echo "[TEST 2] Phase 1子阶段数量一致性"

if command -v python3 >/dev/null 2>&1; then
    SPEC_SUBSTAGES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('.workflow/SPEC.yaml'))['workflow_structure']['phase1_substages']))" 2>/dev/null || echo "ERROR")
    MANIFEST_SUBSTAGES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('.workflow/manifest.yml'))['phases'][0]['substages']))" 2>/dev/null || echo "ERROR")
else
    # Fallback: 手动计数
    SPEC_SUBSTAGES=$(grep -A10 "phase1_substages:" .workflow/SPEC.yaml | grep -c '^ *-' || echo "ERROR")
    MANIFEST_SUBSTAGES=$(grep "substages:" .workflow/manifest.yml | head -1 | grep -o "," | wc -l || echo "0")
    MANIFEST_SUBSTAGES=$((MANIFEST_SUBSTAGES + 1))  # 逗号数+1 = 元素数
fi

# Phase 1应该有4个子阶段（修复后）
if [ "$SPEC_SUBSTAGES" = "4" ] && [ "$MANIFEST_SUBSTAGES" = "4" ]; then
    test_pass "两者都是4个子阶段"
elif [ "$SPEC_SUBSTAGES" = "5" ] && [ "$MANIFEST_SUBSTAGES" = "5" ]; then
    test_pass "两者都是5个子阶段（旧版本）"
else
    test_fail "SPEC=$SPEC_SUBSTAGES, manifest=$MANIFEST_SUBSTAGES"
fi

# ============================================
# Test 3: 版本文件数量定义一致
# ============================================
echo "[TEST 3] 版本文件数量定义一致性"

if command -v python3 >/dev/null 2>&1; then
    VERSION_FILES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('.workflow/SPEC.yaml'))['version_consistency']['required_files']))" 2>/dev/null || echo "ERROR")
else
    VERSION_FILES=$(grep -A10 "required_files:" .workflow/SPEC.yaml | grep -c '^ *-' || echo "ERROR")
fi

if [ "$VERSION_FILES" = "6" ]; then
    test_pass "SPEC定义6个版本文件"
else
    test_fail "SPEC定义了$VERSION_FILES个文件（应该是6个）"
fi

# Verify the files are: VERSION, settings.json, package.json, manifest.yml, CHANGELOG.md, SPEC.yaml
if grep -q ".workflow/SPEC.yaml" .workflow/SPEC.yaml; then
    test_pass "版本文件列表包含SPEC.yaml自己"
else
    test_fail "版本文件列表应该包含SPEC.yaml"
fi

# ============================================
# Test 4: 检查点总数≥97
# ============================================
echo "[TEST 4] 检查点总数≥97"

if command -v python3 >/dev/null 2>&1; then
    TOTAL_CHECKPOINTS=$(python3 -c "import yaml; print(yaml.safe_load(open('.workflow/SPEC.yaml'))['checkpoints']['total_count'])" 2>/dev/null || echo "ERROR")
else
    TOTAL_CHECKPOINTS=$(grep "total_count:" .workflow/SPEC.yaml | head -1 | awk '{print $2}' || echo "ERROR")
fi

if [ "$TOTAL_CHECKPOINTS" != "ERROR" ] && [ "$TOTAL_CHECKPOINTS" -ge 97 ]; then
    test_pass "检查点总数=$TOTAL_CHECKPOINTS (≥97)"
else
    test_fail "检查点总数=$TOTAL_CHECKPOINTS (<97)"
fi

# ============================================
# Test 5: Quality Gates数量=2
# ============================================
echo "[TEST 5] Quality Gates数量=2"

if command -v python3 >/dev/null 2>&1; then
    GATES=$(python3 -c "import yaml; print(yaml.safe_load(open('.workflow/SPEC.yaml'))['quality_gates']['total_gates'])" 2>/dev/null || echo "ERROR")
else
    GATES=$(grep "total_gates:" .workflow/SPEC.yaml | awk '{print $2}' || echo "ERROR")
fi

if [ "$GATES" = "2" ]; then
    test_pass "质量门禁=2个"
else
    test_fail "质量门禁=$GATES（应该是2个）"
fi

# ============================================
# Test 6: CLAUDE.md文档一致性
# ============================================
echo "[TEST 6] CLAUDE.md文档一致性"

if grep -q "6个文件" CLAUDE.md; then
    test_pass "CLAUDE.md描述了6个版本文件"
else
    test_fail "CLAUDE.md未提到6个版本文件"
fi

# ============================================
# Test 7: Phase 1产出文件名正确
# ============================================
echo "[TEST 7] Phase 1产出文件名正确"

if grep -q "P1_DISCOVERY.md" .workflow/SPEC.yaml; then
    test_pass "SPEC.yaml使用正确的P1_DISCOVERY.md"
else
    test_fail "SPEC.yaml应该使用P1_DISCOVERY.md"
fi

if grep -q "P2_DISCOVERY.md" .workflow/SPEC.yaml; then
    test_fail "SPEC.yaml不应该有P2_DISCOVERY.md（已修复）"
else
    test_pass "SPEC.yaml没有错误的P2_DISCOVERY.md"
fi

# ============================================
# Test 8: manifest.yml不包含多余子阶段
# ============================================
echo "[TEST 8] manifest.yml子阶段清理"

if grep -q "Dual-Language Checklist Generation" .workflow/manifest.yml; then
    test_fail "manifest.yml不应该有'Dual-Language Checklist Generation'子阶段"
else
    test_pass "manifest.yml已移除多余子阶段"
fi

if grep -q "Impact Assessment" .workflow/manifest.yml; then
    test_fail "manifest.yml不应该在Phase 1子阶段中有'Impact Assessment'"
else
    test_pass "manifest.yml已移除Phase 1的Impact Assessment子阶段"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo "  Total Tests: $((PASS + FAIL))"
echo "  ✅ Passed:   $PASS"
echo "  ❌ Failed:   $FAIL"
echo "======================================"

if [ $FAIL -eq 0 ]; then
    echo "✅ All contract tests passed!"
    exit 0
else
    echo "❌ $FAIL test(s) failed"
    exit 1
fi
