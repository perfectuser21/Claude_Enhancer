#!/bin/bash
# Claude Enhancer - 用户友好的Agent选择器
# UX优化版本：更直观的反馈和建议

set -e

# 配置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 读取输入
INPUT=$(cat)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
if [ -z "$TASK_DESC" ]; then
    TASK_DESC=$(echo "$INPUT" | grep -oP '"description"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
fi

# 检测用户经验级别（从配置文件或历史记录）
get_user_level() {
    # 简单的启发式检测
    if [ -f ".claude/user_profile.json" ]; then
        grep -o '"level":"[^"]*' .claude/user_profile.json | cut -d'"' -f4 || echo "beginner"
    else
        echo "beginner"  # 默认新手
    fi
}

# 人性化复杂度描述
describe_complexity() {
    local complexity="$1"
    case "$complexity" in
        simple)
            echo "快速任务"
            ;;
        standard)
            echo "标准开发"
            ;;
        complex)
            echo "复杂项目"
            ;;
        *)
            echo "标准任务"
            ;;
    esac
}

# 解释Agent角色（用类比）
explain_agents() {
    local count="$1"
    local user_level="$2"

    if [ "$user_level" == "beginner" ]; then
        case "$count" in
            4)
                echo "就像一个小团队：程序员、测试员、审查员、文档员"
                ;;
            6)
                echo "就像一个完整的项目组：架构师、程序员、测试员、安全专家、设计师、文档员"
                ;;
            8)
                echo "就像一个专业团队：包含所有专家，确保项目完美"
                ;;
        esac
    else
        # 经验用户显示技术细节
        case "$count" in
            4)
                echo "推荐Agent：backend-engineer, test-engineer, code-reviewer, technical-writer"
                ;;
            6)
                echo "推荐Agent：backend-architect, backend-engineer, test-engineer, security-auditor, api-designer, technical-writer"
                ;;
            8)
                echo "推荐Agent：完整技术栈覆盖，包含性能优化和DevOps支持"
                ;;
        esac
    fi
}

# 提供时间估算
estimate_time() {
    local count="$1"
    case "$count" in
        4)
            echo "5-10分钟"
            ;;
        6)
            echo "10-20分钟"
            ;;
        8)
            echo "20-30分钟"
            ;;
        *)
            echo "10-15分钟"
            ;;
    esac
}

# 智能复杂度检测（改进版）
determine_complexity() {
    local desc="$1"
    local score=0

    # 复杂任务指标
    if echo "$desc" | grep -qiE "architect|design system|integrate|migrate|refactor entire|complex|system|full stack|microservice"; then
        ((score+=3))
    fi

    # 标准任务指标
    if echo "$desc" | grep -qiE "add|implement|create|new feature|endpoint|api|database|auth"; then
        ((score+=2))
    fi

    # 简单任务指标
    if echo "$desc" | grep -qiE "fix bug|typo|minor|quick|simple|small change|update|patch"; then
        ((score+=1))
    fi

    # 技术复杂度指标
    if echo "$desc" | grep -qiE "performance|security|scale|optimization|async|concurrent"; then
        ((score+=2))
    fi

    # 根据评分决定复杂度
    if [ $score -ge 5 ]; then
        echo "complex"
    elif [ $score -le 2 ]; then
        echo "simple"
    else
        echo "standard"
    fi
}

# 主逻辑
if [ -n "$TASK_DESC" ]; then
    USER_LEVEL=$(get_user_level)
    COMPLEXITY=$(determine_complexity "$(echo "$TASK_DESC" | tr '[:upper:]' '[:lower:]')")

    # 确定Agent数量
    case "$COMPLEXITY" in
        simple)
            AGENT_COUNT=4
            ;;
        complex)
            AGENT_COUNT=8
            ;;
        *)
            AGENT_COUNT=6
            ;;
    esac

    # 用户友好的输出格式
    echo "" >&2
    echo -e "${CYAN}🎯 Claude智能分析${NC}" >&2
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2

    # 显示任务理解
    echo -e "${PURPLE}📋 任务理解：${NC}$(echo "$TASK_DESC" | head -c 60)..." >&2
    echo -e "${GREEN}🎨 任务类型：${NC}$(describe_complexity "$COMPLEXITY")" >&2

    # 显示团队配置
    echo -e "${YELLOW}👥 推荐团队：${NC}${AGENT_COUNT}位专家" >&2

    if [ "$USER_LEVEL" == "beginner" ]; then
        echo -e "${BLUE}💭 通俗解释：${NC}$(explain_agents "$AGENT_COUNT" "$USER_LEVEL")" >&2
    else
        echo -e "${BLUE}🔧 技术配置：${NC}$(explain_agents "$AGENT_COUNT" "$USER_LEVEL")" >&2
    fi

    # 显示时间预估
    echo -e "${GREEN}⏱️  预计时间：${NC}$(estimate_time "$AGENT_COUNT")" >&2

    # 给出使用建议
    if [ "$COMPLEXITY" == "complex" ]; then
        echo -e "${YELLOW}💡 建议：${NC}这是复杂任务，会仔细规划每个细节" >&2
    elif [ "$COMPLEXITY" == "simple" ]; then
        echo -e "${GREEN}💡 建议：${NC}快速任务，专注效率" >&2
    else
        echo -e "${BLUE}💡 建议：${NC}标准流程，平衡质量和速度" >&2
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2
    echo "" >&2

    # 记录选择历史（用于学习用户偏好）
    {
        flock -x 200
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: $COMPLEXITY, Agents: $AGENT_COUNT, User: $USER_LEVEL" >> /tmp/claude_agent_history.log
    } 200>/tmp/claude_agent_history.log.lock 2>/dev/null || true

    # 更新用户经验（简单的学习机制）
    if [ "$USER_LEVEL" == "beginner" ] && [ -f "/tmp/claude_agent_history.log" ]; then
        USAGE_COUNT=$(wc -l < /tmp/claude_agent_history.log)
        if [ "$USAGE_COUNT" -gt 10 ]; then
            mkdir -p .claude
            echo '{"level":"intermediate","last_updated":"'$(date -Iseconds)'"}' > .claude/user_profile.json
        fi
    fi
fi

# 输出原始输入（保持Hook透明性）
echo "$INPUT"
exit 0