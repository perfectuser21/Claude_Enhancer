#!/bin/bash
# Claude Enhancer Smart Agent Selector v5.2 - Enhanced Output Version

set -e

cleanup() {
    local exit_code=$?
    
    # Rotate log if > 10000 lines
    local log_file="/tmp/claude_agent_selection.log"
    if [[ -f "$log_file" ]]; then
        local lines=$(wc -l < "$log_file" 2>/dev/null || echo 0)
        if [[ $lines -gt 10000 ]]; then
            tail -n 5000 "$log_file" > "$log_file.tmp"
            mv "$log_file.tmp" "$log_file"
        fi
    fi
    
    # Clean lock file
    rm -f "/tmp/claude_agent_selection.log.lock" 2>/dev/null || true
    
    exit $exit_code
}

trap cleanup EXIT INT TERM HUP


# 设置UTF-8支持
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Read input
INPUT=$(cat)

# Extract task description (support multiple field names)
TASK_DESC=""
for field in "prompt" "description" "task" "request"; do
    EXTRACTED=$(echo "$INPUT" | grep -oP "\"$field\"\s*:\s*\"[^\"]+" | cut -d'"' -f4 2>/dev/null || echo "")
    if [ -n "$EXTRACTED" ]; then
        TASK_DESC="$EXTRACTED"
        break
    fi
done

# If no structured field found, extract any quoted text
if [ -z "$TASK_DESC" ]; then
    TASK_DESC=$(echo "$INPUT" | grep -oP '"[^"]{10,}"' | head -1 | sed 's/"//g' || echo "Unknown task")
fi

# Convert to lowercase for matching
TASK_LOWER=$(echo "$TASK_DESC" | tr '[:upper:]' '[:lower:]')

# Determine complexity
determine_complexity() {
    local desc="$1"

    # 标准化输入
    local normalized="${desc//：/:}"  # 全角冒号转半角
    normalized="${normalized//，/,}"  # 全角逗号
    normalized="${normalized//。/.}"  # 全角句号

    # Complex task keywords (8 agents) - 中英文
    if echo "$normalized" | grep -qE "architect|架构|design system|系统设计|integrate|集成|migrate|迁移|refactor entire|全面重构|complex|复杂|大型|整体"; then
        echo "complex"
        return
    fi

    # Simple task keywords (4 agents) - 中英文
    if echo "$normalized" | grep -qE "fix.*bug|修复.*bug|修复.*小|typo|错字|minor|小改|小bug|quick|快速|simple|简单|small.*change|小改动|tiny|微小|trivial|琐碎|修正|修补"; then
        echo "simple"
        return
    fi

    # Default standard task (6 agents)
    echo "standard"
}

# Agent recommendations based on complexity
get_agent_recommendations() {
    local complexity="$1"
    case "$complexity" in
        simple)
            echo "backend-architect, test-engineer, security-auditor, api-designer"
            ;;
        complex)
            echo "system-architect, backend-architect, frontend-architect, database-specialist, security-auditor, performance-engineer, test-engineer, technical-writer"
            ;;
        *)
            echo "backend-architect, frontend-architect, database-specialist, test-engineer, security-auditor, api-designer"
            ;;
    esac
}

# Main logic
if [ -n "$TASK_DESC" ]; then
    COMPLEXITY=$(determine_complexity "$TASK_LOWER")
    AGENT_COUNT=""
    RECOMMENDED_AGENTS=$(get_agent_recommendations "$COMPLEXITY")

    case "$COMPLEXITY" in
        simple) AGENT_COUNT="4" ;;
        complex) AGENT_COUNT="8" ;;
        *) AGENT_COUNT="6" ;;
    esac

    # Enhanced Output - 输出到stderr确保可见性
    echo "" >&2
    echo "╔════════════════════════════════════════════════════════════╗" >&2
    echo "║        🚀 Claude Enhancer Agent Selector v5.2             ║" >&2
    echo "╚════════════════════════════════════════════════════════════╝" >&2
    echo "" >&2
    echo "📋 任务分析 (Task Analysis):" >&2
    echo "   └─ $(echo "$TASK_DESC" | head -c 60)..." >&2
    echo "" >&2
    echo "🎯 复杂度评估 (Complexity Assessment):" >&2
    echo "   └─ $COMPLEXITY 级别 → 需要 $AGENT_COUNT 个Agent" >&2
    echo "" >&2
    echo "🤖 推荐Agent组合 (Recommended Agents):" >&2
    for agent in $(echo "$RECOMMENDED_AGENTS" | tr ',' '\n'); do
        echo "   ✓ $(echo "$agent" | xargs)" >&2
    done
    echo "" >&2
    echo "⚡ 执行模式: 并行执行 (Parallel Execution)" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "" >&2

    # Safe logging with detailed information
    {
        flock -x 200
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: '$TASK_DESC' | Complexity: $COMPLEXITY | Agents: $AGENT_COUNT" >> /tmp/claude_agent_selection.log
    } 200>/tmp/claude_agent_selection.log.lock 2>/dev/null || true
else
    echo "⚠️  No task description found in input" >&2
fi

# Output original content unchanged
echo "$INPUT"
exit 0