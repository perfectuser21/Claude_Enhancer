#!/bin/bash
# Claude Enhancer - Branch创建辅助

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [branch_helper.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD)

# 如果在主分支，提醒创建feature分支
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    echo "🌿 Claude Enhancer 提醒" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "📍 当前在主分支: $current_branch" >&2
    echo "" >&2
    echo "💡 建议创建feature分支开发：" >&2
    echo "  git checkout -b feature/your-feature" >&2
    echo "" >&2
    echo "📝 分支命名建议：" >&2
    echo "  • feature/xxx - 新功能" >&2
    echo "  • fix/xxx - 修复bug" >&2
    echo "  • refactor/xxx - 重构" >&2
    echo "  • docs/xxx - 文档更新" >&2
    echo "" >&2
    echo "🔄 工作流将从这里开始：" >&2
    echo "  Phase 0: 创建分支 ← 现在" >&2
    echo "  Phase 1: 需求分析" >&2
    echo "  Phase 2: 设计规划" >&2
    echo "  Phase 3: 实现开发" >&2
    echo "  Phase 4: 本地测试" >&2
    echo "  Phase 5: 代码提交" >&2
    echo "  Phase 6: 代码审查" >&2
    echo "  Phase 7: 合并部署" >&2
    echo "" >&2
    echo "═══════════════════════════════════════════" >&2
else
    echo "🌿 当前分支: $current_branch" >&2
    echo "✅ 已在feature分支，可以开始开发" >&2
fi

exit 0
