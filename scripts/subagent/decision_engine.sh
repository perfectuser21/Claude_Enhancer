#!/usr/bin/env bash
# Subagent Decision Engine
# Version: 1.0.0
# Purpose: 智能决策是否需要subagent并行、选择哪些agents、无需用户确认
# Usage: bash scripts/subagent/decision_engine.sh <phase> <task_description>

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ========== 智能决策函数 ==========

# 计算任务复杂度 (0-100分)
calculate_complexity() {
    local task="$1"
    local score=0

    # 关键词权重
    local -A keywords=(
        ["api"]=15
        ["database"]=20
        ["frontend"]=15
        ["backend"]=15
        ["auth"]=10
        ["security"]=10
        ["performance"]=10
        ["test"]=8
        ["deploy"]=12
    )

    # 统计关键词
    for keyword in "${!keywords[@]}"; do
        if echo "${task}" | grep -qiE "${keyword}"; then
            ((score += keywords[${keyword}]))
        fi
    done

    # 任务长度影响复杂度
    local word_count=$(echo "${task}" | wc -w)
    if [[ ${word_count} -gt 10 ]]; then
        ((score += 10))
    fi

    # 限制在0-100
    if [[ ${score} -gt 100 ]]; then
        score=100
    fi

    echo "${score}"
}

# 推荐Agent数量 (基于复杂度)
recommend_agent_count() {
    local complexity="$1"

    if [[ ${complexity} -ge 70 ]]; then
        echo "6"  # 高复杂度 → 6 agents
    elif [[ ${complexity} -ge 40 ]]; then
        echo "3"  # 中复杂度 → 3 agents
    else
        echo "0"  # 低复杂度 → 不需要并行
    fi
}

# 决策是否自动执行（无需用户确认）
should_auto_execute() {
    local phase="$1"
    local complexity="$2"

    # 规则：
    # 1. Phase2-4 + 复杂度≥40 → 自动执行
    # 2. 复杂度≥70 → 总是自动执行
    # 3. 其他 → 不执行

    if [[ ${complexity} -ge 70 ]]; then
        echo "true"
        return
    fi

    case "${phase}" in
        Phase2|Phase3|Phase4)
            if [[ ${complexity} -ge 40 ]]; then
                echo "true"
            else
                echo "false"
            fi
            ;;
        *)
            echo "false"
            ;;
    esac
}

# 选择最佳Agent组合
select_best_agents() {
    local task="$1"
    local agent_count="$2"

    # 基于任务关键词匹配agents
    python3 <<EOF
import sys

task = "${task}".lower()
agent_count = int("${agent_count}")

# Agent映射表（基于关键词）
agent_map = {
    'api': ['backend-architect', 'api-designer', 'backend-engineer'],
    'frontend': ['frontend-specialist', 'react-pro', 'ux-designer'],
    'backend': ['backend-architect', 'backend-engineer', 'database-specialist'],
    'database': ['database-specialist', 'backend-architect'],
    'test': ['test-engineer', 'e2e-test-specialist', 'performance-tester'],
    'security': ['security-auditor', 'backend-architect'],
    'deploy': ['devops-engineer', 'cloud-architect', 'deployment-manager'],
    'performance': ['performance-engineer', 'performance-tester'],
}

# 收集相关agents
selected = set()
for keyword, agents in agent_map.items():
    if keyword in task:
        selected.update(agents[:agent_count])

# 如果没有匹配，使用通用agents
if not selected:
    selected = {'backend-engineer', 'frontend-specialist', 'test-engineer'}

# 限制数量
selected_list = list(selected)[:agent_count]

# 输出JSON
import json
print(json.dumps(selected_list))
EOF
}

# ========== 主流程 ==========
main() {
    if [[ $# -lt 2 ]]; then
        echo "Usage: $0 <phase> <task_description>"
        exit 1
    fi

    local phase="$1"
    local task="$2"

    # 1. 计算复杂度
    local complexity=$(calculate_complexity "${task}")

    # 2. 推荐Agent数量
    local agent_count=$(recommend_agent_count "${complexity}")

    # 3. 决策是否自动执行
    local auto_execute=$(should_auto_execute "${phase}" "${complexity}")

    # 4. 选择最佳agents
    local agents="[]"
    if [[ ${agent_count} -gt 0 ]]; then
        agents=$(select_best_agents "${task}" "${agent_count}")
    fi

    # 5. 输出决策结果（JSON格式）
    cat <<JSON
{
  "phase": "${phase}",
  "task": "${task}",
  "complexity": ${complexity},
  "recommended_agents": ${agent_count},
  "auto_execute": ${auto_execute},
  "selected_agents": ${agents},
  "reason": "Complexity score: ${complexity}/100 → ${agent_count} agents recommended"
}
JSON
}

main "$@"
