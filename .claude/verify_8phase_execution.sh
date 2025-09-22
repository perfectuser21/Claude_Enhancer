#!/bin/bash

# 8-Phase执行验证器 - 用户端验证工具

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 8-Phase执行验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查TodoWrite日志
check_todo_logs() {
    echo ""
    echo "📋 检查TodoWrite记录..."

    if [ -f "/root/.claude/todos/*.json" ]; then
        # 统计Phase相关的todo项
        PHASE_COUNT=$(grep -c "Phase [0-7]" /root/.claude/todos/*.json 2>/dev/null || echo 0)

        if [ "$PHASE_COUNT" -ge 8 ]; then
            echo -e "${GREEN}✅ 找到8个Phase的TodoWrite记录${NC}"
        else
            echo -e "${RED}❌ 只找到 $PHASE_COUNT 个Phase记录${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ 未找到TodoWrite记录${NC}"
    fi
}

# 检查Git提交
check_git_commits() {
    echo ""
    echo "📝 检查Git提交记录..."

    # 检查最近的提交是否包含Phase信息
    LAST_COMMIT=$(git log -1 --oneline 2>/dev/null)
    if [[ "$LAST_COMMIT" == *"Phase"* ]]; then
        echo -e "${GREEN}✅ 最近提交包含Phase信息${NC}"
    else
        echo -e "${YELLOW}⚠️ 最近提交未包含Phase信息${NC}"
    fi
}

# 检查分支
check_branch() {
    echo ""
    echo "🌿 检查分支状态..."

    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
    if [[ "$CURRENT_BRANCH" == feature/* ]] || [[ "$CURRENT_BRANCH" == fix/* ]]; then
        echo -e "${GREEN}✅ 在功能分支: $CURRENT_BRANCH${NC}"
    else
        echo -e "${YELLOW}⚠️ 不在功能分支: $CURRENT_BRANCH${NC}"
    fi
}

# 检查Phase状态文件
check_phase_state() {
    echo ""
    echo "📊 检查Phase状态文件..."

    if [ -f ".claude/phase_state.json" ]; then
        COMPLETED=$(jq '[.phases[] | select(.status == "completed")] | length' .claude/phase_state.json)
        TOTAL=$(jq '.phases | length' .claude/phase_state.json)

        echo -e "进度: ${COMPLETED}/${TOTAL} Phases完成"

        if [ "$COMPLETED" -eq 8 ]; then
            echo -e "${GREEN}✅ 所有8个Phase已完成${NC}"
        else
            echo -e "${YELLOW}⏳ 还有 $((8 - COMPLETED)) 个Phase未完成${NC}"
        fi
    else
        echo -e "${RED}❌ 未找到Phase状态文件${NC}"
        echo -e "${YELLOW}提示: 运行 'bash .claude/hooks/phase_flow_monitor.sh init' 初始化${NC}"
    fi
}

# 生成报告
generate_report() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 验证结果"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    SCORE=0

    # 评分
    [ -f ".claude/phase_state.json" ] && SCORE=$((SCORE + 25))
    [ "$COMPLETED" -eq 8 ] && SCORE=$((SCORE + 25))
    [[ "$CURRENT_BRANCH" == feature/* ]] && SCORE=$((SCORE + 25))
    [ "$PHASE_COUNT" -ge 8 ] && SCORE=$((SCORE + 25))

    echo ""
    if [ "$SCORE" -ge 75 ]; then
        echo -e "${GREEN}✅ 8-Phase执行良好 (${SCORE}%)${NC}"
    elif [ "$SCORE" -ge 50 ]; then
        echo -e "${YELLOW}⚠️ 8-Phase执行部分 (${SCORE}%)${NC}"
    else
        echo -e "${RED}❌ 8-Phase执行不完整 (${SCORE}%)${NC}"
    fi

    echo ""
    echo "建议："
    if [ "$SCORE" -lt 100 ]; then
        echo "1. 确保Claude Code使用TodoWrite记录所有8个Phase"
        echo "2. 运行 phase_flow_monitor.sh 追踪Phase进度"
        echo "3. 在功能分支上工作"
        echo "4. 每个Phase完成后更新状态"
    else
        echo "继续保持良好的8-Phase工作流！"
    fi
}

# 主流程
main() {
    check_branch
    check_phase_state
    check_todo_logs
    check_git_commits
    generate_report
}

main "$@"