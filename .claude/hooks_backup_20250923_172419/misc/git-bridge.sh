#!/bin/bash
# Git Bridge - Git操作提醒和最佳实践

echo "🔗 Git Operations Guide" >&2
echo "" >&2

# 检测当前Git状态
if command -v git &> /dev/null; then
    echo "📊 Current Git Status:" >&2
    git status --short 2>/dev/null | head -5 >&2
    echo "" >&2
fi

echo "📝 Commit Best Practices:" >&2
echo "" >&2
echo "1. Stage your changes:" >&2
echo "   git add <files>" >&2
echo "" >&2

echo "2. Write clear commit messages:" >&2
echo "   Format: <type>: <description>" >&2
echo "   Types: feat, fix, docs, test, refactor" >&2
echo "" >&2

echo "3. Verify before committing:" >&2
echo "   • Review changes: git diff --staged" >&2
echo "   • Run tests" >&2
echo "   • Check for sensitive data" >&2
echo "" >&2

echo "4. Push to remote:" >&2
echo "   git push origin <branch>" >&2
echo "" >&2

echo "💡 Tips:" >&2
echo "  • Commit often with small, focused changes" >&2
echo "  • Use branches for features" >&2
echo "  • Create pull requests for review" >&2
echo "" >&2

exit 0