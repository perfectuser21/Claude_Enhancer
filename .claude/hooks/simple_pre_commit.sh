#!/bin/bash
# 简单实用的pre-commit hook

echo "🔍 检查代码质量..."

# 1. 检查Python语法（如果有.py文件）
if git diff --cached --name-only | grep -q "\.py$"; then
    echo "  Python语法检查..."
    for file in $(git diff --cached --name-only | grep "\.py$"); do
        python3 -m py_compile "$file" 2>/dev/null || {
            echo "❌ Python语法错误: $file"
            exit 1
        }
    done
fi

# 2. 检查JavaScript语法（如果有.js文件）
if git diff --cached --name-only | grep -q "\.js$"; then
    if command -v node >/dev/null 2>&1; then
        echo "  JavaScript语法检查..."
        for file in $(git diff --cached --name-only | grep "\.js$"); do
            node -c "$file" 2>/dev/null || {
                echo "❌ JavaScript语法错误: $file"
                exit 1
            }
        done
    fi
fi

# 3. 检查敏感信息
echo "  检查敏感信息..."
PATTERNS="password=|api_key=|secret=|token=|AWS_ACCESS_KEY"
if git diff --cached | grep -iE "$PATTERNS" | grep -v "^-"; then
    echo "⚠️  警告：可能包含敏感信息"
    echo "继续提交？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 4. 检查文件大小（避免提交大文件）
for file in $(git diff --cached --name-only); do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$size" -gt 10485760 ]; then  # 10MB
            echo "❌ 文件太大: $file ($(($size / 1048576))MB)"
            exit 1
        fi
    fi
done

echo "✅ 代码检查通过"
exit 0