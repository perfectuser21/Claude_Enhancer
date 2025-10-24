#!/usr/bin/env bash
# 增量静态检查脚本 - 修正版
# 基于ChatGPT审核反馈：移除|| true，让错误真实暴露
# 日期: 2025-10-24

set -euo pipefail

echo "🔍 Incremental Static Checks"
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
    echo "$SHELL_FILES" | xargs -r -n1 shellcheck
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

echo "✅ Incremental checks completed"
