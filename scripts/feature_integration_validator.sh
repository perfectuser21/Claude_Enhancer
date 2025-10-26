#!/bin/bash
# Feature Integration Validator - 新功能集成验证器
# 确保新功能完全落地，而非空壳

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PROJECT_ROOT
REGISTRY="${PROJECT_ROOT}/.claude/FEATURE_REGISTRY.yaml"
readonly REGISTRY
TEMP_DIR="${PROJECT_ROOT}/.temp/feature_validation"
readonly TEMP_DIR

# 颜色定义
GREEN='\033[0;32m'
readonly GREEN
RED='\033[0;31m'
readonly RED
YELLOW='\033[1;33m'
readonly YELLOW
NC='\033[0m'
readonly NC

# 创建临时目录
mkdir -p "$TEMP_DIR"

# 验证结果
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# ===== 验证函数 =====

# 1. 验证功能文件存在
check_feature_exists() {
    local feature_name="$1"
    local location="$2"

    echo -n "  检查功能文件存在性... "
    if [[ -f "${PROJECT_ROOT}/${location}" ]]; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗ 文件不存在: ${location}${NC}"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# 2. 验证功能可执行
check_feature_executable() {
    local feature_name="$1"
    local location="$2"

    echo -n "  检查功能可执行性... "
    if [[ -x "${PROJECT_ROOT}/${location}" ]]; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗ 不可执行${NC}"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# 3. 验证功能有实际内容（非空壳）
check_feature_content() {
    local feature_name="$1"
    local location="$2"

    echo -n "  检查功能实质内容... "
    local lines=$(wc -l < "${PROJECT_ROOT}/${location}" 2>/dev/null || echo 0)
    local functions=$(grep -c "^[a-zA-Z_][a-zA-Z0-9_]*\s*()" "${PROJECT_ROOT}/${location}" 2>/dev/null || echo 0)

    if [[ $lines -gt 50 ]] && [[ $functions -gt 0 ]]; then
        echo -e "${GREEN}✓ ${lines}行, ${functions}个函数${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗ 内容过少（${lines}行, ${functions}函数）${NC}"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# 4. 验证Phase集成
check_phase_integration() {
    local feature_name="$1"

    echo -n "  检查Phase集成... "
    # 检查是否在对应Phase脚本中被调用
    local integrated=false

    if grep -q "$feature_name" "${PROJECT_ROOT}"/scripts/phase*.sh 2>/dev/null || \
       grep -q "$feature_name" "${PROJECT_ROOT}"/.claude/hooks/*.sh 2>/dev/null; then
        integrated=true
    fi

    if $integrated; then
        echo -e "${GREEN}✓ 已集成${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠ 未找到集成点${NC}"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# 5. 验证测试覆盖
check_test_coverage() {
    local feature_name="$1"
    local test_suite="$2"

    echo -n "  检查测试覆盖... "
    if [[ -n "$test_suite" ]] && [[ -f "${PROJECT_ROOT}/${test_suite}" ]]; then
        echo -e "${GREEN}✓ 测试存在${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}✗ 缺少测试${NC}"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# 6. 验证CI集成
check_ci_integration() {
    local feature_name="$1"

    echo -n "  检查CI/CD集成... "
    if grep -q "$feature_name" "${PROJECT_ROOT}"/.github/workflows/*.yml 2>/dev/null; then
        echo -e "${GREEN}✓ CI已集成${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠ CI未集成${NC}"
        # 不算失败，因为不是所有功能都需要CI
    fi
    ((TOTAL_CHECKS++))
}

# 7. 验证文档
check_documentation() {
    local feature_name="$1"

    echo -n "  检查文档完整性... "
    local doc_found=false

    # 检查README或CLAUDE.md中是否有说明
    if grep -qi "$feature_name" "${PROJECT_ROOT}/README.md" 2>/dev/null || \
       grep -qi "$feature_name" "${PROJECT_ROOT}/CLAUDE.md" 2>/dev/null; then
        doc_found=true
    fi

    if $doc_found; then
        echo -e "${GREEN}✓ 已文档化${NC}"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠ 缺少文档${NC}"
    fi
    ((TOTAL_CHECKS++))
}

# 8. 验证性能基线
check_performance_baseline() {
    local feature_name="$1"
    local type="$2"

    if [[ "$type" != "performance" ]]; then
        return
    fi

    echo -n "  检查性能基线... "
    # 这里应该运行实际的性能测试
    echo -e "${YELLOW}⚠ 需要运行性能测试${NC}"
    ((TOTAL_CHECKS++))
}

# ===== 主流程 =====

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   功能集成完整性验证                                   ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# 解析FEATURE_REGISTRY.yaml
if [[ ! -f "$REGISTRY" ]]; then
    echo -e "${RED}错误: FEATURE_REGISTRY.yaml 不存在${NC}"
    exit 1
fi

# 提取所有功能
features=$(grep "^  [a-z_]*:" "$REGISTRY" | sed 's/://g' | tr -d ' ')

echo "发现 $(echo "$features" | wc -w) 个注册功能"
echo ""

# 逐个验证功能
for feature in $features; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "验证功能: $feature"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 提取功能信息（简化的YAML解析）
    location=$(grep -A20 "^  ${feature}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)
    type=$(grep -A20 "^  ${feature}:" "$REGISTRY" | grep "type:" | head -1 | cut -d'"' -f2)
    test_suite=$(grep -A20 "^  ${feature}:" "$REGISTRY" | grep "test_suite:" | head -1 | cut -d'"' -f2)

    # 运行验证
    check_feature_exists "$feature" "$location"
    check_feature_executable "$feature" "$location"
    check_feature_content "$feature" "$location"
    check_phase_integration "$feature"
    check_test_coverage "$feature" "$test_suite"
    check_ci_integration "$feature"
    check_documentation "$feature"
    check_performance_baseline "$feature" "$type"

    echo ""
done

# ===== 生成报告 =====

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   验证结果总结                                         ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "总检查项: $TOTAL_CHECKS"
echo -e "通过: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "失败: ${RED}$FAILED_CHECKS${NC}"
echo "成功率: ${success_rate}%"
echo ""

if [[ $success_rate -ge 90 ]]; then
    echo -e "${GREEN}✅ 功能集成良好${NC}"
    exit 0
elif [[ $success_rate -ge 70 ]]; then
    echo -e "${YELLOW}⚠️  功能集成需要改进${NC}"
    exit 0
else
    echo -e "${RED}❌ 功能集成不完整${NC}"
    exit 1
fi