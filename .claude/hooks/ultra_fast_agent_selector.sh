#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 超快速Agent选择器
# 优化版本：<50ms执行时间，智能缓存，最小资源消耗

set -euo pipefail

# 性能优化设置
export LC_ALL=C
HOOK_START_TIME=$(date +%s.%N)
CACHE_DIR="/tmp/claude_agent_cache"
CACHE_TTL=60  # 1分钟缓存

# 创建缓存目录
mkdir -p "$CACHE_DIR" 2>/dev/null || true

# 获取输入上下文
HOOK_CONTEXT="${HOOK_CONTEXT:-{}}"
TASK_TYPE=""
COMPLEXITY="medium"

# 快速解析上下文（避免使用jq）
if [[ "$HOOK_CONTEXT" =~ \"task_type\":\"([^\"]+)\" ]]; then
    TASK_TYPE="${BASH_REMATCH[1]}"
fi

if [[ "$HOOK_CONTEXT" =~ \"complexity\":\"([^\"]+)\" ]]; then
    COMPLEXITY="${BASH_REMATCH[1]}"
fi

# 如果没有明确的task_type，从环境变量快速推断
if [[ -z "$TASK_TYPE" ]]; then
    if [[ "${PWD}" =~ backend ]] || [[ "${PWD}" =~ api ]]; then
        TASK_TYPE="backend_development"
    elif [[ "${PWD}" =~ frontend ]] || [[ "${PWD}" =~ ui ]]; then
        TASK_TYPE="frontend_development"
    elif [[ "${PWD}" =~ test ]] || [[ "${PWD}" =~ spec ]]; then
        TASK_TYPE="testing"
    elif [[ "${PWD}" =~ deploy ]] || [[ "${PWD}" =~ k8s ]]; then
        TASK_TYPE="deployment"
    else
        TASK_TYPE="general_development"
    fi
fi

# 缓存键生成
CACHE_KEY="${TASK_TYPE}_${COMPLEXITY}"
CACHE_FILE="${CACHE_DIR}/agents_${CACHE_KEY}"

# 检查缓存（快速路径）
if [[ -f "$CACHE_FILE" ]]; then
    CACHE_AGE=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [[ $CACHE_AGE -lt $CACHE_TTL ]]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# 预定义的高性能Agent组合（避免文件读取）
declare -A AGENT_COMBINATIONS=(
    # 后端开发 (6 agents)
    ["backend_development_simple"]="backend-architect,api-designer,database-specialist,test-engineer"
    ["backend_development_medium"]="backend-architect,api-designer,database-specialist,test-engineer,security-auditor,performance-engineer"
    ["backend_development_complex"]="backend-architect,api-designer,database-specialist,test-engineer,security-auditor,performance-engineer,devops-engineer,technical-writer"

    # 前端开发 (6 agents)
    ["frontend_development_simple"]="frontend-architect,ui-designer,javascript-specialist,test-engineer"
    ["frontend_development_medium"]="frontend-architect,ui-designer,javascript-specialist,test-engineer,performance-engineer,accessibility-specialist"
    ["frontend_development_complex"]="frontend-architect,ui-designer,javascript-specialist,test-engineer,performance-engineer,accessibility-specialist,ux-researcher,technical-writer"

    # 全栈开发 (8 agents)
    ["fullstack_development_simple"]="fullstack-architect,backend-architect,frontend-architect,database-specialist,test-engineer"
    ["fullstack_development_medium"]="fullstack-architect,backend-architect,frontend-architect,database-specialist,test-engineer,api-designer,security-auditor"
    ["fullstack_development_complex"]="fullstack-architect,backend-architect,frontend-architect,database-specialist,test-engineer,api-designer,security-auditor,performance-engineer"

    # 测试相关 (5 agents)
    ["testing_simple"]="test-engineer,qa-specialist,automation-engineer"
    ["testing_medium"]="test-engineer,qa-specialist,automation-engineer,performance-engineer,security-auditor"
    ["testing_complex"]="test-engineer,qa-specialist,automation-engineer,performance-engineer,security-auditor,test-architect,technical-writer"

    # 部署运维 (6 agents)
    ["deployment_simple"]="devops-engineer,infrastructure-specialist,monitoring-engineer"
    ["deployment_medium"]="devops-engineer,infrastructure-specialist,monitoring-engineer,security-auditor,performance-engineer"
    ["deployment_complex"]="devops-engineer,infrastructure-specialist,monitoring-engineer,security-auditor,performance-engineer,cloud-architect,technical-writer"

    # 安全相关 (5 agents)
    ["security_simple"]="security-auditor,backend-architect,test-engineer"
    ["security_medium"]="security-auditor,backend-architect,test-engineer,devops-engineer,compliance-specialist"
    ["security_complex"]="security-auditor,backend-architect,test-engineer,devops-engineer,compliance-specialist,penetration-tester,technical-writer"

    # 数据库相关 (5 agents)
    ["database_simple"]="database-specialist,backend-architect,performance-engineer"
    ["database_medium"]="database-specialist,backend-architect,performance-engineer,security-auditor,test-engineer"
    ["database_complex"]="database-specialist,backend-architect,performance-engineer,security-auditor,test-engineer,data-architect,technical-writer"

    # API开发 (6 agents)
    ["api_development_simple"]="api-designer,backend-architect,test-engineer,technical-writer"
    ["api_development_medium"]="api-designer,backend-architect,test-engineer,technical-writer,security-auditor,performance-engineer"
    ["api_development_complex"]="api-designer,backend-architect,test-engineer,technical-writer,security-auditor,performance-engineer,integration-specialist,documentation-specialist"

    # 通用开发 (4-6 agents)
    ["general_development_simple"]="backend-architect,frontend-architect,test-engineer,technical-writer"
    ["general_development_medium"]="backend-architect,frontend-architect,test-engineer,technical-writer,security-auditor,performance-engineer"
    ["general_development_complex"]="fullstack-architect,backend-architect,frontend-architect,test-engineer,technical-writer,security-auditor,performance-engineer,devops-engineer"
)

# 快速选择Agent组合
LOOKUP_KEY="${TASK_TYPE}_${COMPLEXITY}"
SELECTED_AGENTS="${AGENT_COMBINATIONS[$LOOKUP_KEY]:-${AGENT_COMBINATIONS["general_development_medium"]}}"

# 构建输出
OUTPUT=$(cat <<EOF
{
  "recommended_agents": [$(echo "$SELECTED_AGENTS" | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/')],
  "task_type": "$TASK_TYPE",
  "complexity": "$COMPLEXITY",
  "agent_count": $(echo "$SELECTED_AGENTS" | tr ',' '\n' | wc -l),
  "execution_mode": "parallel",
  "estimated_time": "$([[ "$COMPLEXITY" == "simple" ]] && echo "5-10min" || [[ "$COMPLEXITY" == "medium" ]] && echo "15-20min" || echo "25-30min")",
  "cache_used": false,
  "selection_time": "$(echo "scale=3; $(date +%s.%N) - $HOOK_START_TIME" | bc 2>/dev/null || echo "0.001")s"
}
EOF
)

# 缓存结果（异步，不阻塞）
echo "$OUTPUT" > "$CACHE_FILE" &

# 输出结果
echo "$OUTPUT"

# 性能日志（可选，仅在调试时启用）
if [[ "${DEBUG_HOOKS:-false}" == "true" ]]; then
    EXECUTION_TIME=$(echo "scale=3; $(date +%s.%N) - $HOOK_START_TIME" | bc 2>/dev/null || echo "0.001")
    echo "DEBUG: ultra_fast_agent_selector executed in ${EXECUTION_TIME}s" >&2
fi

exit 0