#!/bin/bash
# 超快速Agent选择器 - 50ms内完成选择
# 基于预编译模式匹配和缓存机制

set -euo pipefail

# 配置
readonly TIMEOUT=0.05  # 50ms超时
readonly CACHE_FILE="/tmp/.claude_agent_cache"
readonly PATTERNS_FILE="/tmp/.claude_patterns_cache"

# 预编译的任务模式（避免重复正则编译）
init_patterns() {
    cat > "$PATTERNS_FILE" << 'EOF'
SIMPLE_PATTERNS="fix bug|typo|minor|quick|simple|small change|修复bug|小改动|简单|快速"
COMPLEX_PATTERNS="architect|design system|integrate|migrate|refactor entire|complex|全栈|架构|重构整个|复杂"
API_PATTERNS="api|接口|endpoint|rest|graphql"
DB_PATTERNS="数据|database|sql|mysql|postgres|mongodb"
AUTH_PATTERNS="auth|login|认证|登录|security|安全"
EOF
    source "$PATTERNS_FILE"
}

# 超快速复杂度判断
quick_complexity() {
    local task="$1"
    local task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    # 使用预编译模式
    if echo "$task_lower" | grep -qE "$COMPLEX_PATTERNS"; then
        echo "complex"
    elif echo "$task_lower" | grep -qE "$SIMPLE_PATTERNS"; then
        echo "simple"
    else
        echo "standard"
    fi
}

# 快速Agent组合选择
quick_agent_selection() {
    local complexity="$1"
    local task="$2"

    case "$complexity" in
        simple)
            echo "backend-engineer,test-engineer,code-reviewer,technical-writer"
            ;;
        complex)
            echo "backend-architect,api-designer,database-specialist,backend-engineer,security-auditor,test-engineer,performance-engineer,technical-writer"
            ;;
        *)
            # 根据任务类型快速选择第5个Agent
            if echo "$task" | grep -qiE "$API_PATTERNS"; then
                echo "backend-architect,backend-engineer,test-engineer,security-auditor,api-designer,technical-writer"
            elif echo "$task" | grep -qiE "$DB_PATTERNS"; then
                echo "backend-architect,backend-engineer,test-engineer,security-auditor,database-specialist,technical-writer"
            elif echo "$task" | grep -qiE "$AUTH_PATTERNS"; then
                echo "backend-architect,security-auditor,backend-engineer,test-engineer,api-designer,technical-writer"
            else
                echo "backend-architect,backend-engineer,test-engineer,security-auditor,code-reviewer,technical-writer"
            fi
            ;;
    esac
}

# 主逻辑（超快速版本）
main() {
    # 超时保护
    (sleep $TIMEOUT; exit 0) &
    local timeout_pid=$!

    # 初始化模式
    [[ -f "$PATTERNS_FILE" ]] || init_patterns
    source "$PATTERNS_FILE"

    # 快速读取输入
    local input
    if ! input=$(timeout 0.01 cat 2>/dev/null); then
        echo "⚡ Agent选择器: 快速模式" >&2
        echo "$input"
        exit 0
    fi

    # 提取任务描述（优化版）
    local task_desc
    task_desc=$(echo "$input" | grep -om1 '"prompt"[[:space:]]*:[[:space:]]*"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "")
    [[ -z "$task_desc" ]] && task_desc=$(echo "$input" | grep -om1 '"description"[[:space:]]*:[[:space:]]*"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "")

    if [[ -n "$task_desc" ]]; then
        # 快速复杂度判断
        local complexity=$(quick_complexity "$task_desc")
        local agents=$(quick_agent_selection "$complexity" "$task_desc")
        local agent_count=$(echo "$agents" | tr ',' '\n' | wc -l)

        # 简化输出
        {
            echo "🤖 选择策略: $complexity ($agent_count agents)"
            echo "👥 推荐: $(echo "$agents" | tr ',' ' ')"
        } >&2

        # 缓存结果用于后续快速查询
        echo "$task_desc|$complexity|$agents" >> "$CACHE_FILE" &
    fi

    # 清理并输出
    kill $timeout_pid 2>/dev/null || true
    echo "$input"
    exit 0
}

main "$@"