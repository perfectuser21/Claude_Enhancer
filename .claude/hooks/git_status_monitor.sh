#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - Git状态监控Hook
# 当有大量未提交更改时提醒

# 获取Git状态
MODIFIED=$(git status --porcelain 2>/dev/null | wc -l)
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# 阈值设置
WARN_THRESHOLD=10
CRITICAL_THRESHOLD=50

if [ "$MODIFIED" -gt 0 ]; then
    echo "📊 Git状态监控"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌿 当前分支: $BRANCH"
    echo "📝 未提交更改: $MODIFIED 个文件"

    if [ "$MODIFIED" -gt "$CRITICAL_THRESHOLD" ]; then
        echo "🔴 警告: 大量未提交更改！"
        echo "💡 建议: 考虑分批提交或创建备份"
        echo
        echo "快速操作:"
        echo "  • 查看状态: git status"
        echo "  • 查看差异: git diff --stat"
        echo "  • 暂存所有: git add -A"
        echo "  • 提交更改: git commit -m 'feat: ...'"
    elif [ "$MODIFIED" -gt "$WARN_THRESHOLD" ]; then
        echo "🟡 提醒: 有较多未提交更改"
        echo "💡 建议: 适时提交以保存进度"
    else
        echo "🟢 状态: 正常"
    fi

    # 显示主要更改类型
    echo
    echo "📁 更改类型:"
    git status --porcelain | cut -c1-2 | sort | uniq -c | while read count status; do
        case "$status" in
            "M ") echo "  • 修改: $count 个文件" ;;
            "A ") echo "  • 新增: $count 个文件" ;;
            "D ") echo "  • 删除: $count 个文件" ;;
            "??" ) echo "  • 未跟踪: $count 个文件" ;;
        esac
    done

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

exit 0