#!/bin/bash
# Claude Hook: Merge确认监听器
# 触发时机：PostToolUse（工具执行后）
# 目的：监听用户的merge确认消息

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"

# 检查是否在等待merge确认
if [[ ! -f "$WORKFLOW_DIR/WAITING_MERGE_CONFIRMATION" ]]; then
    exit 0
fi

# 获取用户消息（如果有的话）
USER_MESSAGE="${CLAUDE_USER_MESSAGE:-}"

if [[ -z "$USER_MESSAGE" ]]; then
    exit 0
fi

# 转换为小写便于匹配
USER_MESSAGE_LOWER=$(echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]')

# 检查用户是否确认merge
if [[ "$USER_MESSAGE_LOWER" =~ (同意merge|merge|可以合并|确认合并|同意|ok|yes) ]]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ✅ 收到merge确认                                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "开始自动merge流程..."
    echo ""

    # 标记用户已确认
    echo "[$(date -Iseconds)] User confirmed merge" > "$WORKFLOW_DIR/MERGE_CONFIRMED"
    echo "User message: $USER_MESSAGE" >> "$WORKFLOW_DIR/MERGE_CONFIRMED"

    # 移除等待标记
    rm -f "$WORKFLOW_DIR/WAITING_MERGE_CONFIRMATION"

    # 触发merge执行脚本
    if [[ -f "$WORKFLOW_DIR/lib/execute_merge.sh" ]]; then
        bash "$WORKFLOW_DIR/lib/execute_merge.sh"
    else
        echo "❌ 错误：找不到merge执行脚本"
        echo "   位置：$WORKFLOW_DIR/lib/execute_merge.sh"
        exit 1
    fi

elif [[ "$USER_MESSAGE_LOWER" =~ (有问题|不对|等等|先别merge|暂停|不merge|不行) ]]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  ⏸️  Merge已暂停                                             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "请告诉我哪里有问题，我会进行修复。"
    echo ""

    # 记录暂停原因
    echo "[$(date -Iseconds)] User paused merge" > "$WORKFLOW_DIR/MERGE_PAUSED"
    echo "User message: $USER_MESSAGE" >> "$WORKFLOW_DIR/MERGE_PAUSED"

    # 移除等待标记
    rm -f "$WORKFLOW_DIR/WAITING_MERGE_CONFIRMATION"
fi

exit 0
