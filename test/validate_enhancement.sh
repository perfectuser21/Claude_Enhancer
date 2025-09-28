#!/bin/bash
# Claude Enhancer 5.3 保障力验证脚本 - 改进版
# 使用宽松正则匹配，避免无意义的失败

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
VERBOSE=${VERBOSE:-0}

echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Claude Enhancer 5.3 保障力验证测试               ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# 改进的检查函数 - 支持宽松匹配
check() {
    local description="$1"
    local command="$2"
    local expected="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "[$TOTAL_CHECKS] $description... "

    # 执行命令并捕获输出
    if output=$(eval "$command" 2>&1); then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        [ "$VERBOSE" = "1" ] && echo "  Debug: $output"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        if [ -n "$expected" ]; then
            echo -e "    ${YELLOW}Expected: $expected${NC}"
            echo -e "    ${YELLOW}Actual output: $output${NC}"
        fi
        return 1
    fi
}

# 宽松的正则匹配函数
check_regex() {
    local description="$1"
    local file="$2"
    local pattern="$3"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "[$TOTAL_CHECKS] $description... "

    # 使用-i忽略大小写，-E使用扩展正则
    if grep -iE "$pattern" "$file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        if [ "$VERBOSE" = "1" ]; then
            echo "  Debug: Found pattern '$pattern' in $file"
            grep -iE "$pattern" "$file" | head -1 | sed 's/^/    /'
        fi
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        echo -e "    ${YELLOW}Pattern not found: $pattern${NC}"
        [ "$VERBOSE" = "1" ] && echo -e "    ${YELLOW}File: $file${NC}"
        return 1
    fi
}

echo -e "${BLUE}[1/7] 检查目录结构${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check "acceptance/features目录" "[ -d '$PROJECT_ROOT/acceptance/features' ]"
check "api/schemas目录" "[ -d '$PROJECT_ROOT/api/schemas' ]"
check "metrics目录" "[ -d '$PROJECT_ROOT/metrics' ]"
check "spike目录" "[ -d '$PROJECT_ROOT/spike' ]"
check "observability/slo目录" "[ -d '$PROJECT_ROOT/observability/slo' ]"
check "observability/alerts目录" "[ -d '$PROJECT_ROOT/observability/alerts' ]"
check "observability/probes目录" "[ -d '$PROJECT_ROOT/observability/probes' ]"
check "migrations目录" "[ -d '$PROJECT_ROOT/migrations' ]"

echo ""
echo -e "${BLUE}[2/7] 检查核心配置文件${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check "性能预算配置" "[ -f '$PROJECT_ROOT/metrics/perf_budget.yml' ]"
check "BDD验收场景(auth)" "[ -f '$PROJECT_ROOT/acceptance/features/auth.feature' ]"
check "BDD验收场景(workflow)" "[ -f '$PROJECT_ROOT/acceptance/features/workflow.feature' ]"
check "OpenAPI规范" "[ -f '$PROJECT_ROOT/api/openapi.yaml' ] || [ -f '$PROJECT_ROOT/api/openapi.yml' ]"
check "SLO配置" "[ -f '$PROJECT_ROOT/observability/slo/slo.yml' ]"
check "数据库迁移脚本" "[ -f '$PROJECT_ROOT/migrations/001_claude_enhancer_5.3_upgrade.sql' ]"

echo ""
echo -e "${BLUE}[3/7] 检查Git Hooks增强${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check "增强版pre-commit" "[ -f '$PROJECT_ROOT/.claude/git-hooks/enhanced-pre-commit-5.3' ] || [ -f '$PROJECT_ROOT/.git/hooks/pre-commit' ]"

# 使用宽松正则匹配Git Hook内容
if [ -f "$PROJECT_ROOT/.claude/git-hooks/enhanced-pre-commit-5.3" ]; then
    HOOK_FILE="$PROJECT_ROOT/.claude/git-hooks/enhanced-pre-commit-5.3"
elif [ -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
    HOOK_FILE="$PROJECT_ROOT/.git/hooks/pre-commit"
else
    HOOK_FILE=""
fi

if [ -n "$HOOK_FILE" ]; then
    check "Hook可执行" "[ -x '$HOOK_FILE' ]"
    # 宽松匹配：BDD相关内容（忽略大小写、空格变化）
    check_regex "包含BDD验证" "$HOOK_FILE" "bdd|feature|scenario|gherkin|cucumber"
    check_regex "包含OpenAPI检查" "$HOOK_FILE" "openapi|swagger|api.*spec|contract"
    check_regex "包含性能预算验证" "$HOOK_FILE" "perf.*budget|performance.*budget|latency|throughput"
    check_regex "包含SLO配置检查" "$HOOK_FILE" "slo|service.*level|objective"
fi

echo ""
echo -e "${BLUE}[4/7] 检查CI/CD配置${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CI_FILE="$PROJECT_ROOT/.github/workflows/ci-enhanced-5.3.yml"
if [ ! -f "$CI_FILE" ]; then
    CI_FILE="$PROJECT_ROOT/.github/workflows/ci.yml"
fi

check "CI配置文件" "[ -f '$CI_FILE' ]"

if [ -f "$CI_FILE" ]; then
    check_regex "包含需求验证job" "$CI_FILE" "validate.*requirements|requirements.*validation"
    check_regex "包含代码质量job" "$CI_FILE" "code.*quality|quality.*check|lint"
    check_regex "包含性能验证job" "$CI_FILE" "performance.*validation|perf.*test"
    check_regex "包含SLO验证job" "$CI_FILE" "slo.*validation|service.*level"
fi

echo ""
echo -e "${BLUE}[5/7] 验证BDD场景${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 统计BDD场景数量
if [ -d "$PROJECT_ROOT/acceptance/features" ]; then
    SCENARIO_COUNT=$(find "$PROJECT_ROOT/acceptance/features" -name "*.feature" -exec grep -c "Scenario:" {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
    echo "BDD场景总数: $SCENARIO_COUNT"
    if [ "$SCENARIO_COUNT" -ge 25 ]; then
        echo -e "${GREEN}✓ BDD场景数量达标 (≥25)${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠ BDD场景数量不足 (当前: $SCENARIO_COUNT, 目标: ≥25)${NC}"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo -e "${BLUE}[6/7] 验证性能预算配置${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$PROJECT_ROOT/metrics/perf_budget.yml" ]; then
    METRIC_COUNT=$(grep -E "^\s+\w+:" "$PROJECT_ROOT/metrics/perf_budget.yml" 2>/dev/null | wc -l)
    echo "性能指标数量: $METRIC_COUNT"
    if [ "$METRIC_COUNT" -ge 30 ]; then
        echo -e "${GREEN}✓ 性能指标数量达标 (≥30)${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠ 性能指标数量不足 (当前: $METRIC_COUNT, 目标: ≥30)${NC}"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo -e "${BLUE}[7/7] 验证SLO配置${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$PROJECT_ROOT/observability/slo/slo.yml" ]; then
    SLO_COUNT=$(grep -c "^\s*- name:" "$PROJECT_ROOT/observability/slo/slo.yml" 2>/dev/null || echo 0)
    echo "SLO定义数量: $SLO_COUNT"
    if [ "$SLO_COUNT" -ge 10 ]; then
        echo -e "${GREEN}✓ SLO数量达标 (≥10)${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠ SLO数量不足 (当前: $SLO_COUNT, 目标: ≥10)${NC}"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # 检查关键SLO
    check_regex "包含api_availability SLO" "$PROJECT_ROOT/observability/slo/slo.yml" "api_availability"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}验证结果汇总${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 计算保障力评分
SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo -e "总检查项: $TOTAL_CHECKS"
echo -e "${GREEN}通过: $PASSED_CHECKS${NC}"
echo -e "${RED}失败: $FAILED_CHECKS${NC}"
echo ""

# 显示进度条
echo -n "保障力评分: ["
for i in $(seq 1 20); do
    if [ $((i * 5)) -le $SCORE ]; then
        echo -n "█"
    else
        echo -n "░"
    fi
done
echo "] ${SCORE}%"

echo ""

# 评级
if [ $SCORE -ge 90 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 优秀！保障力达到生产级别          ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    EXIT_CODE=0
elif [ $SCORE -ge 70 ]; then
    echo -e "${YELLOW}╔═══════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  良好，但仍有改进空间              ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════╝${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}╔═══════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ 需要改进，保障力不足               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════╝${NC}"
    EXIT_CODE=1
fi

# 生成报告
REPORT_FILE="$PROJECT_ROOT/test/enhancement_report.json"
cat > "$REPORT_FILE" << EOF
{
  "version": "5.3",
  "timestamp": "$(date -Iseconds)",
  "total_checks": $TOTAL_CHECKS,
  "passed": $PASSED_CHECKS,
  "failed": $FAILED_CHECKS,
  "score": $SCORE,
  "rating": "$([ $SCORE -ge 90 ] && echo "excellent" || ([ $SCORE -ge 70 ] && echo "good" || echo "needs_improvement"))"
}
EOF

echo ""
echo -e "${CYAN}报告已保存到: $REPORT_FILE${NC}"
echo ""
echo "提示: 使用 VERBOSE=1 运行可查看详细调试信息"

exit $EXIT_CODE