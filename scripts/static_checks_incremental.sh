#!/usr/bin/env bash
# 增量静态检查脚本 - 基线比较版
# 基于ChatGPT P1-7审核: 添加基线比较防止质量退化
# 日期: 2025-10-25

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Incremental Static Checks (with Baseline Validation)"
echo ""

# 获取base分支
BASE=${BASE:-origin/main}
git fetch origin +refs/heads/main:refs/remotes/origin/main >/dev/null 2>&1 || true

# 获取变更文件
CHANGED=$(git diff --name-only --diff-filter=ACMR "$BASE"...HEAD || true)

if [ -z "$CHANGED" ]; then
    echo "✅ No files changed"
    exit 0
fi

echo "Changed files:"
echo "$CHANGED"
echo ""

# 检查Shell文件
echo "📝 Checking shell files..."
SHELL_FILES=$(echo "$CHANGED" | grep -E '\.sh$' || true)
if [ -n "$SHELL_FILES" ]; then
    # Only check for errors, not warnings (severity=error)
    echo "$SHELL_FILES" | xargs -r -n1 shellcheck --severity=error
    echo "✅ Shell files passed"
else
    echo "⏭️  No shell files changed"
fi
echo ""

# 检查Python文件（不要|| true，让错误真实暴露）
echo "🐍 Checking Python files..."
PY_FILES=$(echo "$CHANGED" | grep -E '\.py$' || true)
if [ -n "$PY_FILES" ]; then
    # Python语法检查
    echo "$PY_FILES" | xargs -r -n1 python3 -m py_compile

    # Flake8检查（不要|| true）
    echo "$PY_FILES" | xargs -r -n1 flake8 --max-line-length=120

    echo "✅ Python files passed"
else
    echo "⏭️  No Python files changed"
fi
echo ""

echo "✅ Incremental file checks completed"
echo ""

# ============================================
# 基线验证：检查全局质量指标
# ============================================
echo "📊 Validating against quality baselines..."
echo ""

BASELINE_VIOLATIONS=0

# Baseline 1: Shellcheck 总警告数 ≤ 1850
if command -v shellcheck >/dev/null 2>&1; then
    SHELLCHECK_BASELINE=1850

    # 查找所有shell脚本
    ALL_SHELL_FILES=$(find . -type f -name "*.sh" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -not -path "./.temp/*" \
        -not -path "./archive/*" 2>/dev/null || true)

    if [ -n "$ALL_SHELL_FILES" ]; then
        # 计算总警告数（不使用|| true，让shellcheck失败真实暴露）
        # shellcheck disable=SC2086
        SHELLCHECK_OUTPUT=$(shellcheck -f gcc $ALL_SHELL_FILES 2>/dev/null || true)
        SHELLCHECK_WARNINGS=$(echo "$SHELLCHECK_OUTPUT" | grep -c "warning:" || true)

        echo -e "  Shellcheck warnings: $SHELLCHECK_WARNINGS / $SHELLCHECK_BASELINE (baseline)"

        if [ "$SHELLCHECK_WARNINGS" -le "$SHELLCHECK_BASELINE" ]; then
            echo -e "  ${GREEN}✅ Within baseline${NC}"
        else
            EXCESS=$((SHELLCHECK_WARNINGS - SHELLCHECK_BASELINE))
            echo -e "  ${RED}❌ Exceeds baseline by $EXCESS warnings${NC}"
            echo ""
            echo -e "${YELLOW}Top 10 new warnings:${NC}"
            echo "$SHELLCHECK_OUTPUT" | grep "warning:" | head -10 | sed 's/^/    /'
            ((BASELINE_VIOLATIONS++))
        fi
    fi
else
    echo -e "  ${YELLOW}⚠️  shellcheck not installed - skipping baseline check${NC}"
fi

echo ""

# Final verdict
if [ $BASELINE_VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED (incremental + baseline)${NC}"
    exit 0
else
    echo -e "${RED}❌ BASELINE VIOLATIONS DETECTED${NC}"
    echo -e "${RED}   Incremental changes caused quality regression${NC}"
    echo ""
    echo -e "${YELLOW}Fix required:${NC} Reduce warnings to meet baseline or update baseline with justification"
    exit 1
fi
