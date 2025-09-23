#!/bin/bash
# Claude Enhancer Smart Agent Validator - 智能提醒模式
# 不阻止执行，提供友好的指导和建议

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 读取输入
INPUT=$(cat)

# 提取agents
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]' || echo "")

# 日志文件
LOG_FILE="/tmp/claude_enhancer_quality.log"

# 检测任务类型
detect_task_type() {
    local desc="$1"

    if echo "$desc" | grep -qiE "认证|登录|用户|auth|login|jwt|password|security"; then
        echo "authentication"
        return
    fi

    if echo "$desc" | grep -qiE "api|接口|rest|endpoint|route|服务"; then
        echo "api_development"
        return
    fi

    if echo "$desc" | grep -qiE "数据库|database|table|schema|sql"; then
        echo "database_design"
        return
    fi

    if echo "$desc" | grep -qiE "前端|界面|页面|组件|frontend|ui|react|vue"; then
        echo "frontend_development"
        return
    fi

    if echo "$desc" | grep -qiE "测试|test|单元|集成|e2e|quality"; then
        echo "testing"
        return
    fi

    echo "general"
}

# 获取任务类型
TASK_TYPE=$(detect_task_type "$TASK_DESC")

# 根据任务类型获取必需的agents
get_required_agents() {
    case "$1" in
        authentication)
            echo "backend-architect security-auditor api-designer database-specialist test-engineer"
            ;;
        api_development)
            echo "api-designer backend-architect test-engineer technical-writer"
            ;;
        database_design)
            echo "database-specialist backend-architect performance-engineer"
            ;;
        frontend_development)
            echo "frontend-specialist react-pro ux-designer test-engineer"
            ;;
        testing)
            echo "test-engineer performance-tester security-auditor code-reviewer"
            ;;
        *)
            echo "backend-architect test-engineer technical-writer"
            ;;
    esac
}

# 获取所需agents
REQUIRED_AGENTS=$(get_required_agents "$TASK_TYPE")
REQUIRED_COUNT=$(echo "$REQUIRED_AGENTS" | wc -w)

# 检查缺失的agents
MISSING_AGENTS=""
for agent in $REQUIRED_AGENTS; do
    if ! echo "$AGENTS" | grep -q "$agent"; then
        MISSING_AGENTS="$MISSING_AGENTS $agent"
    fi
done
MISSING_COUNT=$(echo "$MISSING_AGENTS" | wc -w)

# 计算质量分数
calculate_quality_score() {
    local score=100

    # Agent数量评分 (40分)
    if [ "$AGENT_COUNT" -lt "$REQUIRED_COUNT" ]; then
        local penalty=$((($REQUIRED_COUNT - $AGENT_COUNT) * 10))
        score=$((score - penalty))
    fi

    # 任务匹配度评分 (30分)
    if [ -n "$MISSING_AGENTS" ]; then
        local missing_penalty=$((MISSING_COUNT * 10))
        score=$((score - missing_penalty))
    fi

    # 确保分数在0-100之间
    if [ $score -lt 0 ]; then
        score=0
    fi

    echo $score
}

QUALITY_SCORE=$(calculate_quality_score)

# 记录到日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: $TASK_TYPE | Agents: $AGENT_COUNT/$REQUIRED_COUNT | Score: $QUALITY_SCORE" >> "$LOG_FILE"

# 输出友好的提醒信息
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}" >&2
echo -e "${CYAN}║      ${WHITE}🎯 Claude Enhancer Quality Assistant${CYAN}                 ║${NC}" >&2
echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}" >&2
echo -e "${CYAN}║${NC} ${BLUE}📊 Task Analysis${NC}                                    ${CYAN}║${NC}" >&2
echo -e "${CYAN}║${NC}   Type: ${MAGENTA}$TASK_TYPE${NC}                                   " >&2
echo -e "${CYAN}║${NC}   Quality Score: $(if [ $QUALITY_SCORE -ge 80 ]; then echo -e "${GREEN}$QUALITY_SCORE/100${NC}"; elif [ $QUALITY_SCORE -ge 60 ]; then echo -e "${YELLOW}$QUALITY_SCORE/100${NC}"; else echo -e "${RED}$QUALITY_SCORE/100${NC}"; fi)" >&2
echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}" >&2
echo -e "${CYAN}║${NC} ${BLUE}🤖 Agent Status${NC}                                     ${CYAN}║${NC}" >&2
echo -e "${CYAN}║${NC}   Current: ${WHITE}$AGENT_COUNT${NC} agents                        " >&2
echo -e "${CYAN}║${NC}   Required: ${WHITE}$REQUIRED_COUNT${NC} agents                    " >&2

if [ "$AGENT_COUNT" -lt "$REQUIRED_COUNT" ] || [ -n "$MISSING_AGENTS" ]; then
    echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}" >&2
    echo -e "${CYAN}║${NC} ${YELLOW}⚠️  Recommendations${NC}                                 ${CYAN}║${NC}" >&2

    if [ -n "$MISSING_AGENTS" ]; then
        echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}" >&2
        echo -e "${CYAN}║${NC}   ${WHITE}Add these agents for better quality:${NC}             ${CYAN}║${NC}" >&2
        for agent in $MISSING_AGENTS; do
            echo -e "${CYAN}║${NC}     ${RED}→${NC} ${WHITE}$agent${NC}" >&2
        done
    fi

    echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}" >&2
    echo -e "${CYAN}║${NC} ${BLUE}💡 Correct Usage Example:${NC}                          ${CYAN}║${NC}" >&2
    echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}" >&2
    echo -e "${CYAN}║${NC}   ${WHITE}<function_calls>${NC}                                  ${CYAN}║${NC}" >&2

    local example_count=0
    for agent in $REQUIRED_AGENTS; do
        if [ $example_count -lt 3 ]; then
            echo -e "${CYAN}║${NC}     ${WHITE}<invoke name=\"Task\">${NC}                          ${CYAN}║${NC}" >&2
            echo -e "${CYAN}║${NC}       ${WHITE}<parameter name=\"subagent_type\">${NC}           ${CYAN}║${NC}" >&2
            echo -e "${CYAN}║${NC}         ${GREEN}$agent${NC}                                    ${CYAN}║${NC}" >&2
            echo -e "${CYAN}║${NC}       ${WHITE}</parameter>${NC}                               ${CYAN}║${NC}" >&2
            echo -e "${CYAN}║${NC}     ${WHITE}</invoke>${NC}                                     ${CYAN}║${NC}" >&2
            example_count=$((example_count + 1))
        fi
    done

    if [ $REQUIRED_COUNT -gt 3 ]; then
        echo -e "${CYAN}║${NC}     ${WHITE}... (${REQUIRED_COUNT} agents in total)${NC}          ${CYAN}║${NC}" >&2
    fi

    echo -e "${CYAN}║${NC}   ${WHITE}</function_calls>${NC}                                 ${CYAN}║${NC}" >&2
else
    echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}" >&2
    echo -e "${CYAN}║${NC} ${GREEN}✅ Excellent!${NC} Using recommended agent combination   ${CYAN}║${NC}" >&2
fi

echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}" >&2
echo -e "${CYAN}║${NC} ${BLUE}📈 Best Practices${NC}                                   ${CYAN}║${NC}" >&2
echo -e "${CYAN}║${NC}   • Use all agents in ONE message (parallel)        ${CYAN}║${NC}" >&2
echo -e "${CYAN}║${NC}   • Include test-engineer for quality               ${CYAN}║${NC}" >&2
echo -e "${CYAN}║${NC}   • Add security-auditor for sensitive tasks        ${CYAN}║${NC}" >&2
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}" >&2

# 返回成功（不阻止执行）
exit 0