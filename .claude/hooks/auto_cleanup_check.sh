#!/bin/bash
# Claude Enhancer - 自动清理检查Hook
# 当垃圾文件过多时提醒清理

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [auto_cleanup_check.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

set -e

# 计算垃圾文件
TEMP_FILES=$(find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*~" -o -name "*.tmp" -o -name "*.log" \) 2>/dev/null | wc -l)
TEST_SCRIPTS=$(ls -1 *test*.sh *diagnostic*.py *validation*.sh 2>/dev/null | wc -l)
REPORT_FILES=$(find . -maxdepth 2 -name "*REPORT*.md" -o -name "*ANALYSIS*.md" -o -name "*TEST*.md" 2>/dev/null | wc -l)
BACKUP_FILES=$(find .claude -name "*.bak*" -o -name "*backup*" 2>/dev/null | wc -l)

TOTAL_JUNK=$((TEMP_FILES + TEST_SCRIPTS + REPORT_FILES + BACKUP_FILES))

# 阈值
WARN_THRESHOLD=20
CRITICAL_THRESHOLD=50

if [ "$TOTAL_JUNK" -gt "$WARN_THRESHOLD" ]; then
    echo "🧹 清理提醒"
    echo "━━━━━━━━━━━━━━━━━━━━━"
    echo "🗑️ 垃圾文件统计:"
    [ "$TEMP_FILES" -gt 0 ] && echo "  • 临时文件: $TEMP_FILES 个"
    [ "$TEST_SCRIPTS" -gt 0 ] && echo "  • 测试脚本: $TEST_SCRIPTS 个"
    [ "$REPORT_FILES" -gt 0 ] && echo "  • 报告文件: $REPORT_FILES 个"
    [ "$BACKUP_FILES" -gt 0 ] && echo "  • 备份文件: $BACKUP_FILES 个"
    echo "  • 总计: $TOTAL_JUNK 个"

    if [ "$TOTAL_JUNK" -gt "$CRITICAL_THRESHOLD" ]; then
        echo
        echo "🔴 建议立即清理！"
        echo "执行: .claude/scripts/hyper_performance_cleanup.sh"
    else
        echo
        echo "🟡 建议适时清理"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━"
fi

exit 0
