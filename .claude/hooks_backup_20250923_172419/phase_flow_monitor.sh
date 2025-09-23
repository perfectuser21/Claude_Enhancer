#!/bin/bash

# Phase流程监控器 - 确保8个Phase完整执行

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Phase定义
declare -a PHASES=(
    "Phase 0: 创建分支"
    "Phase 1: 需求分析"
    "Phase 2: 设计规划"
    "Phase 3: 开发实现"
    "Phase 4: 本地测试"
    "Phase 5: 代码提交"
    "Phase 6: 代码审查"
    "Phase 7: 合并部署"
)

# Phase Agent要求
declare -A PHASE_MIN_AGENTS=(
    [0]=0
    [1]=1
    [2]=2
    [3]=4
    [4]=2
    [5]=0
    [6]=1
    [7]=1
)

# 状态文件路径
STATE_FILE=".claude/phase_state.json"

# 初始化Phase状态
init_phase_state() {
    local task_name="$1"

    cat > "$STATE_FILE" << EOF
{
    "task": "$task_name",
    "start_time": "$(date -Iseconds)",
    "current_phase": 0,
    "phases": [
        {"id": 0, "name": "创建分支", "status": "pending", "agents_required": 0, "agents_used": 0},
        {"id": 1, "name": "需求分析", "status": "pending", "agents_required": 1, "agents_used": 0},
        {"id": 2, "name": "设计规划", "status": "pending", "agents_required": 2, "agents_used": 0},
        {"id": 3, "name": "开发实现", "status": "pending", "agents_required": 4, "agents_used": 0},
        {"id": 4, "name": "本地测试", "status": "pending", "agents_required": 2, "agents_used": 0},
        {"id": 5, "name": "代码提交", "status": "pending", "agents_required": 0, "agents_used": 0},
        {"id": 6, "name": "代码审查", "status": "pending", "agents_required": 1, "agents_used": 0},
        {"id": 7, "name": "合并部署", "status": "pending", "agents_required": 1, "agents_used": 0}
    ]
}
EOF

    echo -e "${GREEN}✅ 初始化8-Phase工作流${NC}"
    echo -e "${BLUE}任务: $task_name${NC}"
}

# 检查当前Phase
check_current_phase() {
    if [ ! -f "$STATE_FILE" ]; then
        echo -e "${YELLOW}⚠️ 未找到Phase状态文件${NC}"
        echo -e "${YELLOW}请先初始化8-Phase工作流${NC}"
        return 1
    fi

    local current_phase=$(jq -r '.current_phase' "$STATE_FILE")
    local phase_name=$(jq -r ".phases[$current_phase].name" "$STATE_FILE")
    local phase_status=$(jq -r ".phases[$current_phase].status" "$STATE_FILE")

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📍 当前Phase: Phase $current_phase - $phase_name${NC}"
    echo -e "${BLUE}📊 状态: $phase_status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 显示Phase进度
show_phase_progress() {
    if [ ! -f "$STATE_FILE" ]; then
        return 1
    fi

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📊 8-Phase工作流进度${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    for i in {0..7}; do
        local phase_name=$(jq -r ".phases[$i].name" "$STATE_FILE")
        local phase_status=$(jq -r ".phases[$i].status" "$STATE_FILE")
        local agents_required=$(jq -r ".phases[$i].agents_required" "$STATE_FILE")
        local agents_used=$(jq -r ".phases[$i].agents_used" "$STATE_FILE")

        case $phase_status in
            "completed")
                echo -e "✅ Phase $i: $phase_name ${GREEN}[完成]${NC} (Agents: $agents_used/$agents_required)"
                ;;
            "in_progress")
                echo -e "⏳ Phase $i: $phase_name ${YELLOW}[进行中]${NC} (Agents: $agents_used/$agents_required)"
                ;;
            "pending")
                echo -e "⬜ Phase $i: $phase_name [待执行] (需要Agents: $agents_required)"
                ;;
            *)
                echo -e "❓ Phase $i: $phase_name [未知状态]"
                ;;
        esac
    done

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 开始Phase
start_phase() {
    local phase_id="$1"
    local agent_count="${2:-0}"

    if [ ! -f "$STATE_FILE" ]; then
        echo -e "${RED}❌ 错误：Phase状态文件不存在${NC}"
        return 1
    fi

    # 检查是否按顺序执行
    local current_phase=$(jq -r '.current_phase' "$STATE_FILE")
    if [ "$phase_id" != "$current_phase" ]; then
        echo -e "${RED}❌ 错误：必须按顺序执行Phase${NC}"
        echo -e "${RED}当前应该执行Phase $current_phase${NC}"
        return 1
    fi

    # 检查Agent数量
    local required_agents=${PHASE_MIN_AGENTS[$phase_id]}
    if [ "$agent_count" -lt "$required_agents" ]; then
        echo -e "${RED}❌ Phase $phase_id 需要至少 $required_agents 个Agent${NC}"
        echo -e "${RED}当前只有 $agent_count 个${NC}"
        return 1
    fi

    # 更新状态
    local tmp=$(mktemp)
    jq ".phases[$phase_id].status = \"in_progress\" | .phases[$phase_id].agents_used = $agent_count" "$STATE_FILE" > "$tmp"
    mv "$tmp" "$STATE_FILE"

    echo -e "${GREEN}✅ 开始执行Phase $phase_id${NC}"
    echo -e "${GREEN}使用 $agent_count 个Agent${NC}"
}

# 完成Phase
complete_phase() {
    local phase_id="$1"

    if [ ! -f "$STATE_FILE" ]; then
        echo -e "${RED}❌ 错误：Phase状态文件不存在${NC}"
        return 1
    fi

    # 更新状态
    local tmp=$(mktemp)
    jq ".phases[$phase_id].status = \"completed\" | .current_phase = $phase_id + 1" "$STATE_FILE" > "$tmp"
    mv "$tmp" "$STATE_FILE"

    echo -e "${GREEN}✅ Phase $phase_id 完成${NC}"

    # 检查是否所有Phase完成
    local next_phase=$((phase_id + 1))
    if [ "$next_phase" -eq 8 ]; then
        echo -e "${GREEN}🎉 恭喜！所有8个Phase已完成！${NC}"
        show_phase_progress
    else
        echo -e "${BLUE}下一步: Phase $next_phase - ${PHASES[$next_phase]}${NC}"
    fi
}

# 重置Phase状态
reset_phase_state() {
    if [ -f "$STATE_FILE" ]; then
        rm "$STATE_FILE"
        echo -e "${YELLOW}♻️ Phase状态已重置${NC}"
    fi
}

# 主函数
main() {
    local command="${1:-check}"

    case "$command" in
        init)
            init_phase_state "${2:-New Task}"
            ;;
        check)
            check_current_phase
            show_phase_progress
            ;;
        start)
            start_phase "$2" "${3:-0}"
            ;;
        complete)
            complete_phase "$2"
            ;;
        progress)
            show_phase_progress
            ;;
        reset)
            reset_phase_state
            ;;
        *)
            echo "用法："
            echo "  $0 init [任务名称]     - 初始化8-Phase工作流"
            echo "  $0 check               - 检查当前Phase"
            echo "  $0 start [phase_id] [agent_count] - 开始执行Phase"
            echo "  $0 complete [phase_id] - 完成Phase"
            echo "  $0 progress            - 显示进度"
            echo "  $0 reset               - 重置状态"
            ;;
    esac
}

# 执行主函数
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi