#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# AI行为监控器
# Claude Enhancer v6.5.0 - Task-Branch Binding System
# ═══════════════════════════════════════════════════════════════
# Hook类型：PrePrompt
# 触发时机：AI思考前
# 功能：检测频繁分支切换行为并发出警告
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/ai_behavior_monitor.log"

# 颜色
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 配置
CHAOS_THRESHOLD=3  # 1小时内分支切换次数阈值

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') $*" >> "$LOG_FILE"
}

# ═══════════════════════════════════════════════════════════════
# 检测分支切换频率
# ═══════════════════════════════════════════════════════════════

detect_branch_chaos() {
    # 统计最近1小时内的分支切换次数
    local switches=0
    if command -v git >/dev/null 2>&1; then
        switches=$(git reflog --since="1 hour ago" 2>/dev/null | grep -c "checkout:" || echo 0)
    fi

    log "BRANCH_SWITCHES_1H: $switches (threshold: $CHAOS_THRESHOLD)"

    # 如果超过阈值，显示警告
    if [[ $switches -ge $CHAOS_THRESHOLD ]]; then
        cat <<EOF >&2

${BOLD}${RED}⚠️⚠️⚠️ 警告：检测到频繁分支切换 ⚠️⚠️⚠️${NC}

${YELLOW}过去1小时内切换分支: ${BOLD}$switches 次${NC}${YELLOW}（阈值: $CHAOS_THRESHOLD）${NC}

${BOLD}可能原因：${NC}
  1. 任务规划不清晰，导致反复切换
  2. 遇到问题未在当前分支解决
  3. 违反"一任务一分支"原则
  4. 忘记当前任务应该在哪个分支

${BOLD}建议操作：${NC}
  • 暂停当前工作
  • 回顾任务目标和计划
  • 确认正确的工作分支
  • 在一个分支上完成整个任务

${BOLD}查看当前任务状态：${NC}
  ${CYAN}bash .claude/hooks/task_lifecycle.sh status${NC}

${BOLD}═══════════════════════════════════════════════════════════${NC}

EOF
        log "CHAOS_DETECTED: Switches=$switches, Warning shown"
    fi
}

# ═══════════════════════════════════════════════════════════════
# 执行检测
# ═══════════════════════════════════════════════════════════════

detect_branch_chaos

# PrePrompt hook不应该阻止操作，仅警告
exit 0
