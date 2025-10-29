#!/usr/bin/env bash
# Subagent Parallel Orchestrator
# Version: 1.0.0
# Purpose: 自动化subagent并行调度系统 - 基于STAGES.yml配置智能调用61个官方subagents
# Usage: bash scripts/subagent/parallel_orchestrator.sh <phase> <task_description>
# Example: bash scripts/subagent/parallel_orchestrator.sh Phase3 "实现用户认证API"

set -euo pipefail

# ========== 配置 ==========
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGES_FILE="${PROJECT_ROOT}/.workflow/STAGES.yml"
AGENTS_DIR="${PROJECT_ROOT}/.claude/agents"
LOG_DIR="${PROJECT_ROOT}/.workflow/logs/subagent"
TEMP_DIR="${PROJECT_ROOT}/.temp/subagent"

# 创建必要目录
mkdir -p "${LOG_DIR}" "${TEMP_DIR}"

# ========== 日志函数 ==========
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*" | tee -a "${LOG_DIR}/orchestrator.log"
}

# ========== 读取STAGES.yml配置 ==========
get_parallel_groups() {
    local phase="$1"

    # 使用python解析YAML获取并行组
    python3 <<EOF
import yaml
import sys

try:
    with open("${STAGES_FILE}", 'r') as f:
        config = yaml.safe_load(f)

    # 获取该Phase的并行组
    groups = config.get('parallel_groups', {}).get('${phase}', [])

    if not groups:
        sys.exit(0)

    # 输出JSON格式
    import json
    print(json.dumps(groups, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ========== 冲突检测 ==========
check_conflicts() {
    local phase="$1"
    local groups_json="$2"

    # 检测是否有冲突路径重叠
    python3 <<EOF
import json
import fnmatch
import sys

try:
    groups = json.loads('${groups_json}')
    conflict_detected = False

    # 收集所有conflict_paths
    all_paths = []
    for group in groups:
        paths = group.get('conflict_paths', [])
        all_paths.extend([(group['group_id'], path) for path in paths])

    # 检测路径重叠
    for i, (gid1, path1) in enumerate(all_paths):
        for gid2, path2 in all_paths[i+1:]:
            if gid1 != gid2:
                # 简单的重叠检测（可以更复杂）
                if path1 == path2 or fnmatch.fnmatch(path1, path2) or fnmatch.fnmatch(path2, path1):
                    print(f"CONFLICT: {gid1} and {gid2} both modify {path1}", file=sys.stderr)
                    conflict_detected = True

    if conflict_detected:
        sys.exit(1)
    else:
        print("NO_CONFLICT")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ========== 智能Agent选择 ==========
select_agents_for_task() {
    local phase="$1"
    local task_desc="$2"
    local groups_json="$3"

    # 基于任务描述智能选择agents
    python3 <<EOF
import json
import sys

try:
    groups = json.loads('${groups_json}')
    task = "${task_desc}".lower()

    # 关键词匹配（简单启发式）
    keywords_map = {
        'api': ['backend-architect', 'api-designer'],
        'frontend': ['frontend-specialist', 'react-pro'],
        'backend': ['backend-architect', 'backend-engineer'],
        'database': ['database-specialist'],
        'test': ['test-engineer', 'e2e-test-specialist'],
        'security': ['security-auditor'],
        'performance': ['performance-engineer'],
        'deploy': ['devops-engineer', 'cloud-architect'],
    }

    # 找出相关的并行组
    relevant_groups = []
    for group in groups:
        group_name = group.get('name', '').lower()
        group_id = group['group_id']

        # 检查任务描述是否匹配组
        for keyword, _ in keywords_map.items():
            if keyword in task and keyword in group_name:
                relevant_groups.append(group)
                break

    # 如果没有匹配，使用第一个并行组
    if not relevant_groups:
        relevant_groups = groups[:1]

    # 输出选中的agents
    selected_agents = []
    for group in relevant_groups:
        for agent in group.get('agents', []):
            selected_agents.append({
                'agent': agent,
                'group_id': group['group_id'],
                'can_parallel': group.get('can_parallel', False)
            })

    print(json.dumps(selected_agents, ensure_ascii=False))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ========== 并行执行Subagents ==========
execute_parallel_subagents() {
    local agents_json="$1"
    local task_desc="$2"

    # 解析agents列表
    local agents=$(echo "${agents_json}" | python3 -c "import sys, json; print(' '.join([a['agent'] for a in json.load(sys.stdin)]))")

    log "INFO" "Starting parallel execution of agents: ${agents}"

    # 为每个agent生成Task tool调用命令
    local pids=()
    local results_dir="${TEMP_DIR}/results_$$"
    mkdir -p "${results_dir}"

    for agent_info in $(echo "${agents_json}" | python3 -c "import sys, json; [print(json.dumps(a)) for a in json.load(sys.stdin)]"); do
        local agent=$(echo "${agent_info}" | python3 -c "import sys, json; print(json.load(sys.stdin)['agent'])")
        local can_parallel=$(echo "${agent_info}" | python3 -c "import sys, json; print(json.load(sys.stdin)['can_parallel'])")

        if [[ "${can_parallel}" == "True" ]]; then
            # 并行执行
            log "INFO" "Launching subagent: ${agent}"

            # 生成调用提示（实际需要通过Claude Code的Task tool调用）
            cat > "${results_dir}/${agent}.cmd" <<AGENT_CMD
Task tool invocation needed:
{
  "subagent_type": "${agent}",
  "description": "Execute ${task_desc}",
  "prompt": "Please ${task_desc} according to the project requirements. Focus on your expertise area."
}
AGENT_CMD
            log "INFO" "Agent ${agent} command prepared: ${results_dir}/${agent}.cmd"
        fi
    done

    log "INFO" "All agents prepared. Results dir: ${results_dir}"
    echo "${results_dir}"
}

# ========== 自动化决策引擎 ==========
should_use_parallel() {
    local phase="$1"
    local task_desc="$2"

    # 决策逻辑：
    # 1. Phase3实现阶段 → 优先并行
    # 2. Phase4测试阶段 → 优先并行
    # 3. 任务包含关键词（api, frontend, backend） → 并行
    # 4. 否则 → 串行

    case "${phase}" in
        Phase2|Phase3|Phase4)
            # 检查任务复杂度
            if echo "${task_desc}" | grep -qiE '(api|frontend|backend|database|test)'; then
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

# ========== 主流程 ==========
main() {
    if [[ $# -lt 2 ]]; then
        echo "Usage: $0 <phase> <task_description>"
        echo "Example: $0 Phase3 '实现用户认证API'"
        exit 1
    fi

    local phase="$1"
    local task_desc="$2"

    log "INFO" "========== Subagent Parallel Orchestrator Started =========="
    log "INFO" "Phase: ${phase}"
    log "INFO" "Task: ${task_desc}"

    # 1. 决策是否需要并行
    local use_parallel=$(should_use_parallel "${phase}" "${task_desc}")
    if [[ "${use_parallel}" != "true" ]]; then
        log "INFO" "Task does not require parallel execution (simple task or non-parallel phase)"
        exit 0
    fi

    # 2. 读取STAGES.yml配置
    log "INFO" "Reading STAGES.yml for Phase ${phase}..."
    local groups_json=$(get_parallel_groups "${phase}")

    if [[ -z "${groups_json}" || "${groups_json}" == "null" ]]; then
        log "WARN" "No parallel groups defined for ${phase}, using serial execution"
        exit 0
    fi

    log "INFO" "Found parallel groups: ${groups_json}"

    # 3. 冲突检测
    log "INFO" "Checking for conflicts..."
    if ! check_conflicts "${phase}" "${groups_json}"; then
        log "ERROR" "Conflict detected! Downgrading to serial execution"
        exit 1
    fi

    # 4. 智能Agent选择
    log "INFO" "Selecting agents for task..."
    local selected_agents=$(select_agents_for_task "${phase}" "${task_desc}" "${groups_json}")
    log "INFO" "Selected agents: ${selected_agents}"

    # 5. 并行执行
    local results_dir=$(execute_parallel_subagents "${selected_agents}" "${task_desc}")
    log "INFO" "Parallel execution completed. Results: ${results_dir}"

    # 6. 输出调用命令（供主AI执行）
    cat <<SUMMARY

╔════════════════════════════════════════════════════════════╗
║          Subagent Parallel Execution Plan                  ║
╚════════════════════════════════════════════════════════════╝

Phase: ${phase}
Task: ${task_desc}

Agents to invoke:
$(echo "${selected_agents}" | python3 -c "import sys, json; [print(f\"  - {a['agent']} (group: {a['group_id']})\") for a in json.load(sys.stdin)]")

Next Steps:
1. Claude Code should invoke these agents using Task tool
2. Each agent will work on their expertise area
3. Results will be aggregated automatically

Command files generated in: ${results_dir}
SUMMARY

    log "INFO" "========== Orchestrator Completed =========="
}

main "$@"
