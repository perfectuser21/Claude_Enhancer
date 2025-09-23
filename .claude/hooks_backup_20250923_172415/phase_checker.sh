#!/bin/bash

# Phase检查器 - 在每个阶段开始前验证Agent数量

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 任务类型与最少Agent数量映射
declare -A TASK_MIN_AGENTS=(
    ["authentication"]=5
    ["api_development"]=4
    ["database_design"]=4
    ["frontend"]=4
    ["bug_fix"]=3
    ["refactoring"]=4
    ["testing"]=3
    ["documentation"]=2
    ["deployment"]=4
    ["security"]=5
)

# 检查函数
check_agent_count() {
    local task_type=$1
    local planned_count=$2
    local min_required=${TASK_MIN_AGENTS[$task_type]:-3}  # 默认最少3个

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🔍 Phase Agent数量自检${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "📋 任务类型: $task_type"
    echo "📊 最少需要: $min_required 个Agent"
    echo "📝 当前规划: $planned_count 个Agent"
    echo ""

    if [ "$planned_count" -lt "$min_required" ]; then
        echo -e "${RED}❌ 检查失败：Agent数量不足！${NC}"
        echo -e "${RED}需要至少 $min_required 个Agent，当前只有 $planned_count 个${NC}"
        echo ""
        echo -e "${YELLOW}🔄 请重新规划，添加以下类型的Agent：${NC}"

        # 根据任务类型建议缺少的Agent
        case $task_type in
            "authentication")
                echo "  • security-auditor - 安全审查"
                echo "  • backend-architect - 后端架构"
                echo "  • database-specialist - 数据库设计"
                echo "  • test-engineer - 测试实施"
                echo "  • api-designer - API设计"
                ;;
            "api_development")
                echo "  • api-designer - API设计"
                echo "  • backend-architect - 后端实现"
                echo "  • test-engineer - 测试覆盖"
                echo "  • technical-writer - 文档编写"
                ;;
            "database_design")
                echo "  • database-specialist - 数据库专家"
                echo "  • backend-architect - 架构设计"
                echo "  • performance-engineer - 性能优化"
                echo "  • data-engineer - 数据工程"
                ;;
            *)
                echo "  • 根据任务需要选择合适的Agent"
                ;;
        esac
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 检查通过：Agent数量满足要求${NC}"
        echo -e "${GREEN}可以继续执行！${NC}"
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        return 0
    fi
}

# 主逻辑
main() {
    # 从环境变量或参数获取信息
    TASK_TYPE=${1:-${CLAUDE_TASK_TYPE:-"general"}}
    AGENT_COUNT=${2:-${CLAUDE_AGENT_COUNT:-0}}

    # 执行检查
    check_agent_count "$TASK_TYPE" "$AGENT_COUNT"
    exit_code=$?

    # 记录检查结果
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Task: $TASK_TYPE, Agents: $AGENT_COUNT, Result: $exit_code" >> /tmp/phase_check.log

    exit $exit_code
}

# 如果直接运行脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi