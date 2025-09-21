#!/bin/bash
# Claude Enhancer Task Type Analyzer
# 智能识别任务类型并提供最佳Agent组合建议

set -e

# 读取输入
INPUT=$(cat)

# 任务类型定义和Agent组合
declare -A TASK_PATTERNS
declare -A TASK_AGENTS
declare -A TASK_TIPS

# 认证系统
TASK_PATTERNS["authentication"]="登录|认证|auth|用户|权限|jwt|oauth|session|password|signup|signin|logout"
TASK_AGENTS["authentication"]="backend-architect security-auditor test-engineer api-designer database-specialist"
TASK_TIPS["authentication"]="使用bcrypt加密、JWT过期时间、rate limiting、审计日志"

# API开发
TASK_PATTERNS["api_development"]="api|接口|rest|graphql|endpoint|route|swagger|openapi|webhook"
TASK_AGENTS["api_development"]="api-designer backend-architect test-engineer technical-writer"
TASK_TIPS["api_development"]="RESTful规范、OpenAPI文档、请求验证、错误处理"

# 数据库
TASK_PATTERNS["database_design"]="数据库|database|schema|sql|mongodb|redis|表结构|migration|索引|query"
TASK_AGENTS["database_design"]="database-specialist backend-architect performance-engineer"
TASK_TIPS["database_design"]="索引设计、数据一致性、备份策略、迁移脚本"

# 前端开发
TASK_PATTERNS["frontend_development"]="前端|frontend|react|vue|angular|ui|组件|页面|component|界面|css|样式"
TASK_AGENTS["frontend_development"]="frontend-specialist ux-designer accessibility-auditor test-engineer"
TASK_TIPS["frontend_development"]="响应式设计、可访问性、loading状态、性能优化"

# 全栈开发
TASK_PATTERNS["fullstack_development"]="全栈|fullstack|完整功能|前后端|full-stack|整体|应用|app"
TASK_AGENTS["fullstack_development"]="fullstack-engineer database-specialist test-engineer devops-engineer"
TASK_TIPS["fullstack_development"]="前后端分离、完整测试、容器化部署"

# 性能优化
TASK_PATTERNS["performance_optimization"]="性能|优化|performance|速度|缓存|optimize|cache|慢|快|延迟"
TASK_AGENTS["performance_optimization"]="performance-engineer backend-architect monitoring-specialist"
TASK_TIPS["performance_optimization"]="基准测试、监控指标、优化对比"

# 测试
TASK_PATTERNS["testing"]="测试|test|spec|jest|mocha|pytest|unit|e2e|integration|coverage|断言"
TASK_AGENTS["testing"]="test-engineer e2e-test-specialist performance-tester"
TASK_TIPS["testing"]="单元测试、集成测试、E2E测试、覆盖率"

# 安全
TASK_PATTERNS["security"]="安全|security|漏洞|vulnerability|xss|sql注入|csrf|加密|encrypt"
TASK_AGENTS["security"]="security-auditor backend-architect test-engineer"
TASK_TIPS["security"]="输入验证、加密传输、安全头、审计日志"

# DevOps
TASK_PATTERNS["devops"]="部署|deploy|docker|kubernetes|k8s|ci/cd|pipeline|容器|container"
TASK_AGENTS["devops"]="devops-engineer cloud-architect monitoring-specialist"
TASK_TIPS["devops"]="容器化、CI/CD、监控告警、回滚策略"

# 识别任务类型
detect_task() {
    local text="$1"
    local detected=""
    local confidence=0

    for task_type in "${!TASK_PATTERNS[@]}"; do
        pattern="${TASK_PATTERNS[$task_type]}"
        if echo "$text" | grep -qiE "$pattern"; then
            # 计算匹配的关键词数量
            match_count=$(echo "$text" | grep -oiE "$pattern" | wc -l)
            if [ "$match_count" -gt "$confidence" ]; then
                confidence=$match_count
                detected=$task_type
            fi
        fi
    done

    if [ -n "$detected" ]; then
        echo "$detected"
    else
        echo "general"
    fi
}

# 提取任务描述
PROMPTS=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4)
COMBINED_TEXT=$(echo "$PROMPTS" | tr '\n' ' ' | tr '[:upper:]' '[:lower:]')

# 如果没有找到prompt，检查其他可能的描述字段
if [ -z "$COMBINED_TEXT" ]; then
    COMBINED_TEXT=$(echo "$INPUT" | grep -oP '"description"\s*:\s*"[^"]+' | cut -d'"' -f4 | tr '\n' ' ' | tr '[:upper:]' '[:lower:]')
fi

# 识别任务类型
if [ -n "$COMBINED_TEXT" ]; then
    TASK_TYPE=$(detect_task "$COMBINED_TEXT")

    # 如果识别到特定任务类型，提供建议
    if [ "$TASK_TYPE" != "general" ]; then
        SUGGESTED_AGENTS="${TASK_AGENTS[$TASK_TYPE]}"
        TIPS="${TASK_TIPS[$TASK_TYPE]}"

        # 检查当前使用的agents
        CURRENT_AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u)

        if [ -n "$CURRENT_AGENTS" ]; then
            # 输出任务分析信息到stderr（不影响正常流程）
            echo "📊 Claude Enhancer 任务分析" >&2
            echo "═══════════════════════════════════════════" >&2
            echo "" >&2
            echo "🎯 识别的任务类型: $TASK_TYPE" >&2
            echo "" >&2
            echo "👥 推荐的Agent组合:" >&2
            for agent in $SUGGESTED_AGENTS; do
                if echo "$CURRENT_AGENTS" | grep -q "^$agent$"; then
                    echo "  ✅ $agent" >&2
                else
                    echo "  ⭕ $agent (建议添加)" >&2
                fi
            done
            echo "" >&2
            echo "💡 最佳实践提示:" >&2
            echo "  $TIPS" | tr '、' '\n' | sed 's/^/  • /' >&2
            echo "" >&2
            echo "═══════════════════════════════════════════" >&2
        fi

        # 记录任务类型到日志
        LOG_FILE="/tmp/claude_enhancer_task_analysis.txt"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Type: $TASK_TYPE, Agents: $(echo $CURRENT_AGENTS | tr '\n' ' ')" >> "$LOG_FILE"
    fi
fi

# 输出原始内容
echo "$INPUT"
exit 0