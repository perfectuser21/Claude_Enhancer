#!/bin/bash
# 工单卡管理器 - 物理限制并发

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Lock file tracking for cleanup
LOCK_DIR=""

cleanup() {
    local exit_code=$?
    
    # Release lock if we have it
    if [[ -n "$LOCK_DIR" ]] && [[ -d "$LOCK_DIR" ]]; then
        rmdir "$LOCK_DIR" 2>/dev/null || true
        echo "[CLEANUP] Lock released" >&2
    fi
    
    exit $exit_code
}

trap cleanup EXIT INT TERM HUP

# 目录定义
TICKETS_DIR=".tickets"
LIMITS_DIR=".limits"
PHASE_FILE=".phase/current"

# 获取当前Phase
get_current_phase() {
    cat "$PHASE_FILE" 2>/dev/null || echo "P1"
}

# 获取Phase并发上限
get_phase_limit() {
    local phase=$1
    cat "$LIMITS_DIR/$phase/max" 2>/dev/null || echo "4"
}

# 获取活动工单数
get_active_tickets() {
    ls -1 "$TICKETS_DIR"/*.todo 2>/dev/null | wc -l
}

# 创建新工单
create_ticket() {
    local description=$1
    local phase=$(get_current_phase)
    local max_limit=$(get_phase_limit "$phase")

    # 使用简单的mkdir作为原子锁
    LOCK_DIR="/tmp/claude_ticket.lock"
    local max_wait=20  # 最多等待2秒（20 * 0.1秒）
    local waited=0

    # 尝试获取锁
    while [ "$waited" -lt "$max_wait" ]; do
        if mkdir "$LOCK_DIR" 2>/dev/null; then
            # 成功获取锁
            break
        fi
        sleep 0.1
        waited=$((waited + 1))
    done

    if [ "$waited" -ge "$max_wait" ]; then
        echo -e "${RED}❌ 无法获取锁，系统繁忙${NC}" >&2
        return 1
    fi

    # 在锁内重新检查活动工单数
    local active=$(get_active_tickets)

    # 检查并发限制
    if [ "$active" -ge "$max_limit" ]; then
        echo -e "${RED}❌ 无法创建工单：活动工单数($active)已达$phase上限($max_limit)${NC}"
        echo "请先完成现有工单或等待空闲位置"
        rmdir "$LOCK_DIR" 2>/dev/null; LOCK_DIR=""  # Release and clear
        return 1
    fi

    # 生成工单ID
    local ticket_id="T-$(date +%s%N)-$$-$RANDOM"
    local ticket_file="$TICKETS_DIR/$ticket_id.todo"

    # 创建工单文件
    cat > "$ticket_file" << EOF
{
    "id": "$ticket_id",
    "phase": "$phase",
    "description": "$description",
    "created": "$(date '+%Y-%m-%d %H:%M:%S')",
    "status": "todo",
    "assigned_agents": []
}
EOF

    # 释放锁
    rmdir "$LOCK_DIR" 2>/dev/null; LOCK_DIR=""  # Release and clear

    echo -e "${GREEN}✅ 创建工单：$ticket_id${NC}"
    echo "   Phase: $phase"
    echo "   活动工单: $((active + 1))/$max_limit"

    return 0
}

# 完成工单
complete_ticket() {
    local ticket_id=$1
    local todo_file="$TICKETS_DIR/$ticket_id.todo"
    local done_file="$TICKETS_DIR/$ticket_id.done"

    if [ ! -f "$todo_file" ]; then
        echo -e "${RED}❌ 工单不存在：$ticket_id${NC}"
        exit 1
    fi

    # 标记完成
    mv "$todo_file" "$done_file"

    # 添加完成信息
    echo "\"completed\": \"$(date '+%Y-%m-%d %H:%M:%S')\"" >> "$done_file"

    echo -e "${GREEN}✅ 工单完成：$ticket_id${NC}"

    # 显示剩余活动工单
    local active=$(get_active_tickets)
    local phase=$(get_current_phase)
    local max_limit=$(get_phase_limit "$phase")
    echo "   剩余活动工单: $active/$max_limit"
}

# 列出工单
list_tickets() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}工单列表${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 活动工单
    echo -e "${YELLOW}活动工单(.todo):${NC}"
    for ticket in "$TICKETS_DIR"/*.todo; do
        if [ -f "$ticket" ]; then
            basename "$ticket" .todo
        fi
    done | column

    # 完成工单
    echo -e "${GREEN}完成工单(.done):${NC}"
    for ticket in "$TICKETS_DIR"/*.done; do
        if [ -f "$ticket" ]; then
            basename "$ticket" .done
        fi
    done | column

    # 阻塞工单
    echo -e "${RED}阻塞工单(.blocked):${NC}"
    for ticket in "$TICKETS_DIR"/*.blocked; do
        if [ -f "$ticket" ]; then
            basename "$ticket" .blocked
        fi
    done | column

    # 统计信息
    local phase=$(get_current_phase)
    local active=$(get_active_tickets)
    local max_limit=$(get_phase_limit "$phase")

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "当前Phase: $phase"
    echo "活动工单: $active/$max_limit"
    echo "可用位置: $((max_limit - active))"
}

# 自适应节流
adaptive_throttle() {
    local phase=$(get_current_phase)
    local current_limit=$(get_phase_limit "$phase")

    # 检查最近两次Gate结果
    local recent_gates=$(ls -1t .gates/*.ok 2>/dev/null | head -2 | wc -l)

    if [ "$recent_gates" -eq 2 ]; then
        # 连续成功，增加并发
        local new_limit=$((current_limit + 2))
        local phase_max=$(get_phase_limit "$phase")

        if [ "$new_limit" -le "$phase_max" ]; then
            echo "$new_limit" > "$LIMITS_DIR/$phase/max"
            echo -e "${GREEN}✅ 自适应提升：$phase并发限制 $current_limit → $new_limit${NC}"
        fi
    fi

    # 检查失败（blocked工单）
    local blocked=$(ls -1 "$TICKETS_DIR"/*.blocked 2>/dev/null | wc -l)
    if [ "$blocked" -ge 2 ]; then
        # 连续失败，降低并发
        local new_limit=$((current_limit - 2))

        if [ "$new_limit" -ge 2 ]; then
            echo "$new_limit" > "$LIMITS_DIR/$phase/max"
            echo -e "${YELLOW}⚠️ 自适应降低：$phase并发限制 $current_limit → $new_limit${NC}"
        fi
    fi
}

# 主命令处理
case "${1:-help}" in
    create)
        create_ticket "${2:-No description}"
        ;;
    complete)
        if [ -z "$2" ]; then
            echo "用法: $0 complete <ticket-id>"
            exit 1
        fi
        complete_ticket "$2"
        ;;
    list)
        list_tickets
        ;;
    throttle)
        adaptive_throttle
        ;;
    help)
        echo "工单管理器用法:"
        echo "  $0 create <描述>    - 创建新工单"
        echo "  $0 complete <ID>    - 完成工单"
        echo "  $0 list            - 列出所有工单"
        echo "  $0 throttle        - 自适应并发调整"
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        exit 1
        ;;
esac