#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# 优化的pre-commit hook - 使用Claude Enhancer Plus Git优化系统

# 检查是否有Node.js环境来运行优化版本
if command -v node >/dev/null 2>&1 && [ -f "src/git/OptimizedHooks.js" ]; then
    echo "🚀 使用优化版本检查代码质量..."

    # 运行优化的Git hooks
    node -e "
        const OptimizedHooks = require('./src/git/OptimizedHooks');
        const hooks = new OptimizedHooks();

        hooks.executePreCommit()
            .then(result => {
                if (result.success) {
                    console.log('✅ 优化版本检查通过');
                    process.exit(0);
                } else {
                    console.error('❌ 检查失败:', result.error);
                    process.exit(1);
                }
            })
            .catch(error => {
                console.error('❌ 优化版本执行失败:', error.message);
                console.log('🔄 回退到标准版本...');
                process.exit(2); // 使用特殊退出码指示回退
            });
    "

    # 检查优化版本的结果
    OPTIMIZED_RESULT=$?
    if [ $OPTIMIZED_RESULT -eq 0 ]; then
        exit 0
    elif [ $OPTIMIZED_RESULT -eq 1 ]; then
        exit 1
    fi

    # 如果退出码是2，表示需要回退到标准版本
    echo "⚠️ 优化版本不可用，使用标准检查..."
fi

# 标准版本检查（回退方案）
echo "🔍 检查代码质量..."

# 1. 快速检查 - 如果没有暂存文件，直接退出
STAGED_FILES=$(git diff --cached --name-only)
if [ -z "$STAGED_FILES" ]; then
    echo "✅ 没有暂存文件，跳过检查"
    exit 0
fi

echo "📁 检查暂存文件: $(echo "$STAGED_FILES" | wc -l) 个"

# 2. 并行语法检查函数
check_python_syntax() {
    local python_files=$(echo "$STAGED_FILES" | grep "\.py$" || true)
    if [ -n "$python_files" ]; then
        echo "  🐍 Python语法检查..."
        echo "$python_files" | while read -r file; do
            if [ -n "$file" ]; then
                python3 -m py_compile "$file" 2>/dev/null || {
                    echo "❌ Python语法错误: $file" >&2
                    exit 1
                }
            fi
        done
    fi
}

check_javascript_syntax() {
    local js_files=$(echo "$STAGED_FILES" | grep "\.js$" || true)
    if [ -n "$js_files" ] && command -v node >/dev/null 2>&1; then
        echo "  📜 JavaScript语法检查..."
        echo "$js_files" | while read -r file; do
            if [ -n "$file" ]; then
                node -c "$file" 2>/dev/null || {
                    echo "❌ JavaScript语法错误: $file" >&2
                    exit 1
                }
            fi
        done
    fi
}

# 并行执行语法检查
check_python_syntax &
PYTHON_PID=$!
check_javascript_syntax &
JS_PID=$!

# 等待所有检查完成
wait $PYTHON_PID
PYTHON_RESULT=$?
wait $JS_PID
JS_RESULT=$?

if [ $PYTHON_RESULT -ne 0 ] || [ $JS_RESULT -ne 0 ]; then
    echo "❌ 语法检查失败"
    exit 1
fi

# 3. 优化的敏感信息检查 - 只检查新增的行
echo "  🔐 检查敏感信息..."
PATTERNS="password\\s*[:=]|api[_-]?key\\s*[:=]|secret\\s*[:=]|token\\s*[:=]|AWS_ACCESS_KEY"

# 只检查新增的行，不检查删除的行
SENSITIVE_LINES=$(git diff --cached | grep "^+" | grep -vE "^\+\+\+" | grep -iE "$PATTERNS" || true)
if [ -n "$SENSITIVE_LINES" ]; then
    echo "⚠️  警告：检测到可能的敏感信息："
    echo "$SENSITIVE_LINES"
    echo "这些行包含潜在的敏感信息，继续提交？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 4. 并行文件大小检查
echo "  📏 检查文件大小..."
LARGE_FILES=""
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        if [ "$size" -gt 10485760 ]; then  # 10MB
            LARGE_FILES="$LARGE_FILES\n$file ($(($size / 1048576))MB)"
        fi
    fi
done

if [ -n "$LARGE_FILES" ]; then
    echo "❌ 发现大文件，不建议提交到Git:"
    echo -e "$LARGE_FILES"
    echo "继续提交大文件？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 5. 简单的代码质量提示
echo "  ⭐ 质量检查..."
QUALITY_WARNINGS=""

# 检查是否有TODO注释增加
NEW_TODOS=$(git diff --cached | grep "^+" | grep -i "TODO\|FIXME\|XXX" | wc -l)
if [ "$NEW_TODOS" -gt 0 ]; then
    QUALITY_WARNINGS="$QUALITY_WARNINGS\n💡 新增 $NEW_TODOS 个待办事项（TODO/FIXME/XXX）"
fi

# 检查是否有console.log增加（JavaScript）
NEW_CONSOLE_LOGS=$(git diff --cached | grep "^+" | grep "console\.log" | wc -l)
if [ "$NEW_CONSOLE_LOGS" -gt 0 ]; then
    QUALITY_WARNINGS="$QUALITY_WARNINGS\n💡 新增 $NEW_CONSOLE_LOGS 个console.log，建议提交前清理"
fi

if [ -n "$QUALITY_WARNINGS" ]; then
    echo "📋 质量提示:"
    echo -e "$QUALITY_WARNINGS"
fi

echo "✅ 代码检查通过"
exit 0