#!/bin/bash
# Claude Enhancer 5.0 - Parallel Task Manager
# 并行Agent任务管理器，支持队列管理、负载均衡、监控和依赖管理
# Version: 1.0.0
# Author: Claude Enhancer Team

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly TASK_QUEUE_DIR="${PROJECT_ROOT}/.workflow/queue"
readonly TASK_LOGS_DIR="${PROJECT_ROOT}/.workflow/logs"
readonly TASK_STATE_DIR="${PROJECT_ROOT}/.workflow/state"
readonly CONFIG_DIR="${PROJECT_ROOT}/.claude"
readonly MAX_CONCURRENT_TASKS=8
readonly TASK_TIMEOUT=1800  # 30分钟
readonly MONITOR_INTERVAL=5  # 5秒检查间隔
readonly LOAD_BALANCE_THRESHOLD=0.7  # CPU使用率阈值

# 初始化目录结构
init_directories() {
    mkdir -p "${TASK_QUEUE_DIR}" "${TASK_LOGS_DIR}" "${TASK_STATE_DIR}"
    mkdir -p "${TASK_QUEUE_DIR}/pending" "${TASK_QUEUE_DIR}/running" "${TASK_QUEUE_DIR}/completed" "${TASK_QUEUE_DIR}/failed"
    mkdir -p "${TASK_STATE_DIR}/agents" "${TASK_STATE_DIR}/resources" "${TASK_STATE_DIR}/dependencies"
}

# 日志函数
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*" | tee -a "${TASK_LOGS_DIR}/parallel_manager.log"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_debug() { log "DEBUG" "$@"; }

# 错误处理
error_handler() {
    local exit_code=$?
    local line_no=$1
    log_error "脚本在第 ${line_no} 行出错，退出码: ${exit_code}"
    cleanup_on_exit
    exit "${exit_code}"
}
trap 'error_handler ${LINENO}' ERR

# 清理函数
cleanup_on_exit() {
    log_info "清理资源..."
    # 停止所有运行中的任务
    for pid_file in "${TASK_STATE_DIR}/agents"/*.pid; do
        [[ -f "$pid_file" ]] || continue
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "停止任务进程: $pid"
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            kill -KILL "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
    done
}
trap cleanup_on_exit EXIT INT TERM

# 任务状态枚举
declare -r TASK_PENDING="pending"
declare -r TASK_RUNNING="running"
declare -r TASK_COMPLETED="completed"
declare -r TASK_FAILED="failed"
declare -r TASK_WAITING="waiting"

# 任务优先级
declare -r PRIORITY_HIGH=1
declare -r PRIORITY_NORMAL=5
declare -r PRIORITY_LOW=10

# 系统资源监控
get_system_load() {
    # CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

    # 内存使用率
    local mem_usage=$(free | grep Mem | awk '{printf("%.1f", ($3/$2) * 100.0)}')

    # 磁盘使用率
    local disk_usage=$(df "${PROJECT_ROOT}" | tail -1 | awk '{print $5}' | sed 's/%//')

    # 负载平均值
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    echo "{\"cpu\":${cpu_usage},\"memory\":${mem_usage},\"disk\":${disk_usage},\"load_avg\":${load_avg}}"
}

# 资源可用性检查
check_resource_availability() {
    local system_load=$(get_system_load)
    local cpu_usage=$(echo "$system_load" | jq -r '.cpu')
    local mem_usage=$(echo "$system_load" | jq -r '.memory')

    # 检查是否超过阈值
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        echo "high_cpu"
        return 1
    fi

    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        echo "high_memory"
        return 1
    fi

    # 检查运行中的任务数
    local running_tasks=$(ls "${TASK_QUEUE_DIR}/running" | wc -l)
    if (( running_tasks >= MAX_CONCURRENT_TASKS )); then
        echo "max_tasks_reached"
        return 1
    fi

    echo "available"
    return 0
}

# 任务创建
create_task() {
    local task_name="$1"
    local agent_list="$2"
    local dependencies="${3:-}"
    local priority="${4:-$PRIORITY_NORMAL}"
    local timeout="${5:-$TASK_TIMEOUT}"
    local description="${6:-}"

    local task_id="${task_name}_$(date +%s)_$$"
    local task_file="${TASK_QUEUE_DIR}/pending/${task_id}.json"

    # 验证Agent列表
    local agent_count=$(echo "$agent_list" | jq -r '. | length')
    if (( agent_count < 4 || agent_count > 8 )); then
        log_error "Agent数量必须在4-8个之间，当前: $agent_count"
        return 1
    fi

    # 验证Agent是否存在
    for agent in $(echo "$agent_list" | jq -r '.[]'); do
        local agent_file="${CONFIG_DIR}/agents/${agent}.md"
        if [[ ! -f "$agent_file" ]]; then
            log_error "Agent不存在: $agent"
            return 1
        fi
    done

    # 创建任务定义
    cat > "$task_file" << EOF
{
    "task_id": "$task_id",
    "task_name": "$task_name",
    "status": "$TASK_PENDING",
    "agents": $agent_list,
    "dependencies": [$(echo "$dependencies" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | paste -sd,)],
    "priority": $priority,
    "timeout": $timeout,
    "description": "$description",
    "created_at": "$(date -Iseconds)",
    "updated_at": "$(date -Iseconds)",
    "progress": 0,
    "resource_usage": {},
    "agent_status": {}
}
EOF

    log_info "任务已创建: $task_id"
    echo "$task_id"
}

# 依赖检查
check_dependencies() {
    local task_id="$1"
    local task_file="${TASK_QUEUE_DIR}/pending/${task_id}.json"

    [[ -f "$task_file" ]] || return 1

    local dependencies=$(jq -r '.dependencies[]' "$task_file" 2>/dev/null || echo "")

    # 如果没有依赖，直接返回成功
    [[ -z "$dependencies" ]] && return 0

    # 检查每个依赖是否完成
    while read -r dep_task_id; do
        [[ -z "$dep_task_id" ]] && continue

        local dep_file="${TASK_QUEUE_DIR}/completed/${dep_task_id}.json"
        if [[ ! -f "$dep_file" ]]; then
            log_debug "依赖任务未完成: $dep_task_id"
            return 1
        fi
    done <<< "$dependencies"

    return 0
}

# 任务调度器
schedule_next_task() {
    # 获取系统资源状态
    local resource_status
    resource_status=$(check_resource_availability)

    if [[ "$resource_status" != "available" ]]; then
        log_debug "系统资源不足: $resource_status"
        return 1
    fi

    # 按优先级排序获取待执行任务
    local next_task=""
    local best_priority=999

    for task_file in "${TASK_QUEUE_DIR}/pending"/*.json; do
        [[ -f "$task_file" ]] || continue

        local task_id=$(basename "$task_file" .json)
        local priority=$(jq -r '.priority' "$task_file")

        # 检查依赖
        if ! check_dependencies "$task_id"; then
            continue
        fi

        # 选择优先级最高的任务
        if (( priority < best_priority )); then
            best_priority=$priority
            next_task="$task_id"
        fi
    done

    if [[ -n "$next_task" ]]; then
        execute_task "$next_task"
    fi
}

# Agent执行器
execute_agent() {
    local task_id="$1"
    local agent_name="$2"
    local agent_index="$3"
    local total_agents="$4"

    local agent_pid_file="${TASK_STATE_DIR}/agents/${task_id}_${agent_name}.pid"
    local agent_log_file="${TASK_LOGS_DIR}/${task_id}_${agent_name}.log"
    local agent_result_file="${TASK_STATE_DIR}/agents/${task_id}_${agent_name}_result.json"

    # 记录进程ID
    echo $$ > "$agent_pid_file"

    log_info "启动Agent: $agent_name (任务: $task_id)"

    # 获取Agent配置
    local agent_config_file="${CONFIG_DIR}/agents/${agent_name}.md"

    # 执行Agent（模拟 - 实际环境中会调用真实的Agent）
    {
        echo "=== Agent执行开始: $agent_name ==="
        echo "任务ID: $task_id"
        echo "Agent索引: $agent_index/$total_agents"
        echo "开始时间: $(date)"
        echo

        # 模拟Agent工作
        local work_duration=$((RANDOM % 30 + 10))  # 10-40秒随机工作时间
        local progress_step=$((100 / work_duration))

        for ((i=1; i<=work_duration; i++)); do
            sleep 1
            local progress=$((i * progress_step))
            [[ $progress -gt 100 ]] && progress=100

            # 更新Agent状态
            local status_update=$(cat << EOF
{
    "agent": "$agent_name",
    "task_id": "$task_id",
    "progress": $progress,
    "status": "running",
    "updated_at": "$(date -Iseconds)"
}
EOF
)
            echo "$status_update" > "${TASK_STATE_DIR}/agents/${task_id}_${agent_name}_status.json"

            echo "Progress: $progress% - Working on task..."
        done

        echo
        echo "=== Agent执行完成: $agent_name ==="
        echo "结束时间: $(date)"

        # 创建结果文件
        local result=$(cat << EOF
{
    "agent": "$agent_name",
    "task_id": "$task_id",
    "status": "completed",
    "exit_code": 0,
    "duration": $work_duration,
    "completed_at": "$(date -Iseconds)",
    "output": "Agent $agent_name completed successfully"
}
EOF
)
        echo "$result" > "$agent_result_file"

    } > "$agent_log_file" 2>&1

    # 清理进程ID文件
    rm -f "$agent_pid_file"

    return 0
}

# 任务执行
execute_task() {
    local task_id="$1"
    local task_file="${TASK_QUEUE_DIR}/pending/${task_id}.json"
    local running_file="${TASK_QUEUE_DIR}/running/${task_id}.json"

    # 移动任务到运行队列
    mv "$task_file" "$running_file"

    # 更新任务状态
    jq '.status = "running" | .started_at = "'$(date -Iseconds)'"' "$running_file" > "${running_file}.tmp"
    mv "${running_file}.tmp" "$running_file"

    local agents=$(jq -r '.agents[]' "$running_file")
    local agent_count=$(jq -r '.agents | length' "$running_file")
    local task_timeout=$(jq -r '.timeout' "$running_file")

    log_info "开始执行任务: $task_id (Agents: $agent_count)"

    # 并行启动所有Agent
    local pids=()
    local agent_index=1

    while read -r agent; do
        execute_agent "$task_id" "$agent" "$agent_index" "$agent_count" &
        pids+=($!)
        ((agent_index++))
    done <<< "$agents"

    # 监控Agent执行
    monitor_task_execution "$task_id" "${pids[@]}" "$task_timeout" &
    local monitor_pid=$!

    # 等待所有Agent完成或超时
    local all_success=true
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            all_success=false
            log_error "Agent进程失败: PID $pid"
        fi
    done

    # 停止监控进程
    kill "$monitor_pid" 2>/dev/null || true

    # 处理任务结果
    if $all_success; then
        complete_task "$task_id" "success"
    else
        complete_task "$task_id" "failed"
    fi
}

# 任务执行监控
monitor_task_execution() {
    local task_id="$1"
    shift
    local pids=("$@")
    local timeout="${pids[-1]}"
    unset 'pids[-1]'  # 移除最后一个元素（timeout）

    local start_time=$(date +%s)
    local running_file="${TASK_QUEUE_DIR}/running/${task_id}.json"

    while true; do
        sleep $MONITOR_INTERVAL

        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # 检查超时
        if (( elapsed > timeout )); then
            log_error "任务超时: $task_id (${elapsed}s > ${timeout}s)"

            # 终止所有Agent进程
            for pid in "${pids[@]}"; do
                kill -TERM "$pid" 2>/dev/null || true
            done
            sleep 5
            for pid in "${pids[@]}"; do
                kill -KILL "$pid" 2>/dev/null || true
            done

            complete_task "$task_id" "timeout"
            return 1
        fi

        # 检查所有进程是否仍在运行
        local any_running=false
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                any_running=true
                break
            fi
        done

        # 如果所有进程都结束了，退出监控
        if ! $any_running; then
            break
        fi

        # 更新任务进度
        update_task_progress "$task_id"

        # 记录资源使用情况
        local system_load=$(get_system_load)
        jq --argjson load "$system_load" '.resource_usage = $load | .updated_at = "'$(date -Iseconds)'"' \
            "$running_file" > "${running_file}.tmp"
        mv "${running_file}.tmp" "$running_file"
    done
}

# 更新任务进度
update_task_progress() {
    local task_id="$1"
    local running_file="${TASK_QUEUE_DIR}/running/${task_id}.json"

    # 计算所有Agent的平均进度
    local total_progress=0
    local agent_count=0

    for status_file in "${TASK_STATE_DIR}/agents/${task_id}_"*"_status.json"; do
        [[ -f "$status_file" ]] || continue

        local agent_progress=$(jq -r '.progress // 0' "$status_file")
        total_progress=$((total_progress + agent_progress))
        ((agent_count++))
    done

    if (( agent_count > 0 )); then
        local avg_progress=$((total_progress / agent_count))
        jq --arg progress "$avg_progress" '.progress = ($progress | tonumber)' \
            "$running_file" > "${running_file}.tmp"
        mv "${running_file}.tmp" "$running_file"
    fi
}

# 任务完成处理
complete_task() {
    local task_id="$1"
    local result="$2"  # success, failed, timeout

    local running_file="${TASK_QUEUE_DIR}/running/${task_id}.json"
    local target_dir=""

    case "$result" in
        "success")
            target_dir="${TASK_QUEUE_DIR}/completed"
            log_info "任务成功完成: $task_id"
            ;;
        "failed"|"timeout")
            target_dir="${TASK_QUEUE_DIR}/failed"
            log_error "任务执行失败: $task_id (原因: $result)"
            ;;
    esac

    local final_file="${target_dir}/${task_id}.json"

    # 收集所有Agent结果
    local agent_results="[]"
    for result_file in "${TASK_STATE_DIR}/agents/${task_id}_"*"_result.json"; do
        [[ -f "$result_file" ]] || continue

        local agent_result=$(cat "$result_file")
        agent_results=$(echo "$agent_results" | jq --argjson result "$agent_result" '. += [$result]')
    done

    # 更新最终状态
    jq --arg status "$result" --argjson results "$agent_results" \
        '.status = $status | .completed_at = "'$(date -Iseconds)'" | .agent_results = $results | .progress = 100' \
        "$running_file" > "$final_file"

    # 清理运行文件
    rm -f "$running_file"

    # 清理Agent状态文件
    rm -f "${TASK_STATE_DIR}/agents/${task_id}_"*

    # 触发依赖任务检查
    check_dependent_tasks "$task_id"
}

# 检查依赖此任务的其他任务
check_dependent_tasks() {
    local completed_task_id="$1"

    # 检查等待队列中是否有依赖此任务的任务
    for pending_file in "${TASK_QUEUE_DIR}/pending"/*.json; do
        [[ -f "$pending_file" ]] || continue

        local dependencies=$(jq -r '.dependencies[]?' "$pending_file" 2>/dev/null || echo "")

        while read -r dep_task_id; do
            [[ -z "$dep_task_id" ]] && continue

            if [[ "$dep_task_id" == "$completed_task_id" ]]; then
                local task_id=$(basename "$pending_file" .json)
                log_info "依赖任务完成，重新调度: $task_id"
                # 下次调度循环会自动处理这个任务
                break
            fi
        done <<< "$dependencies"
    done
}

# 负载均衡器
balance_load() {
    local system_load=$(get_system_load)
    local cpu_usage=$(echo "$system_load" | jq -r '.cpu')
    local mem_usage=$(echo "$system_load" | jq -r '.memory')

    # 如果资源使用率过高，暂停新任务调度
    if (( $(echo "$cpu_usage > $(echo "$LOAD_BALANCE_THRESHOLD * 100" | bc)" | bc -l) )); then
        log_warn "CPU使用率过高 (${cpu_usage}%)，暂停新任务调度"
        return 1
    fi

    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        log_warn "内存使用率过高 (${mem_usage}%)，暂停新任务调度"
        return 1
    fi

    return 0
}

# 任务统计
show_task_statistics() {
    echo "=== 任务统计 ==="
    echo "待执行: $(ls "${TASK_QUEUE_DIR}/pending" 2>/dev/null | wc -l)"
    echo "运行中: $(ls "${TASK_QUEUE_DIR}/running" 2>/dev/null | wc -l)"
    echo "已完成: $(ls "${TASK_QUEUE_DIR}/completed" 2>/dev/null | wc -l)"
    echo "失败: $(ls "${TASK_QUEUE_DIR}/failed" 2>/dev/null | wc -l)"
    echo

    echo "=== 系统资源 ==="
    local system_load=$(get_system_load)
    echo "CPU使用率: $(echo "$system_load" | jq -r '.cpu')%"
    echo "内存使用率: $(echo "$system_load" | jq -r '.memory')%"
    echo "磁盘使用率: $(echo "$system_load" | jq -r '.disk')%"
    echo "负载平均值: $(echo "$system_load" | jq -r '.load_avg')"
    echo
}

# 任务列表
list_tasks() {
    local status="${1:-all}"

    case "$status" in
        "pending"|"running"|"completed"|"failed")
            echo "=== ${status^^} 任务 ==="
            for task_file in "${TASK_QUEUE_DIR}/${status}"/*.json; do
                [[ -f "$task_file" ]] || continue

                local task_info=$(jq -r '.task_id + " | " + .task_name + " | " + .status + " | " + (.progress|tostring) + "%"' "$task_file")
                echo "$task_info"
            done
            ;;
        "all")
            list_tasks "pending"
            list_tasks "running"
            list_tasks "completed"
            list_tasks "failed"
            ;;
    esac
}

# 主调度循环
main_scheduler() {
    log_info "启动并行任务管理器"

    while true; do
        # 负载均衡检查
        if balance_load; then
            # 调度下一个任务
            schedule_next_task
        fi

        # 等待下次调度
        sleep $MONITOR_INTERVAL
    done
}

# 命令行接口
main() {
    init_directories

    case "${1:-}" in
        "create")
            # create_task <name> <agents_json> [dependencies] [priority] [timeout] [description]
            create_task "$2" "$3" "${4:-}" "${5:-$PRIORITY_NORMAL}" "${6:-$TASK_TIMEOUT}" "${7:-}"
            ;;
        "start")
            main_scheduler
            ;;
        "stats")
            show_task_statistics
            ;;
        "list")
            list_tasks "${2:-all}"
            ;;
        "execute")
            # 手动执行指定任务
            execute_task "$2"
            ;;
        "test")
            # 创建测试任务
            local test_agents='["backend-architect", "api-designer", "database-specialist", "backend-engineer", "security-auditor", "test-engineer"]'
            create_task "test_parallel_execution" "$test_agents" "" "$PRIORITY_NORMAL" "300" "测试并行执行功能"
            ;;
        *)
            echo "用法: $0 {create|start|stats|list|execute|test}"
            echo
            echo "命令说明:"
            echo "  create <name> <agents_json> [deps] [priority] [timeout] [desc] - 创建任务"
            echo "  start                                                          - 启动调度器"
            echo "  stats                                                          - 显示统计信息"
            echo "  list [status]                                                  - 列出任务"
            echo "  execute <task_id>                                              - 手动执行任务"
            echo "  test                                                           - 创建测试任务"
            echo
            echo "示例:"
            echo "  $0 create 'api_development' '[\"backend-architect\",\"api-designer\",\"test-engineer\",\"technical-writer\"]'"
            exit 1
            ;;
    esac
}

# 如果直接执行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi