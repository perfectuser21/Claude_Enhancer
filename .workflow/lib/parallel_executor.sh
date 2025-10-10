#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Parallel Execution Engine v1.0
# 集成互斥锁和冲突检测的并行执行引擎
# =============================================================================
# Purpose: 安全的并行任务执行，自动处理冲突和互斥
# Features:
#   - 集成mutex_lock.sh和conflict_detector.sh
#   - 自动冲突检测和降级
#   - 死锁检测和恢复
#   - 完整的执行追踪
# =============================================================================

set -euo pipefail

# 全局配置（避免readonly冲突）
PARALLEL_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARALLEL_PROJECT_ROOT="$(cd "${PARALLEL_SCRIPT_DIR}/../.." && pwd)"

# 加载依赖
source "${PARALLEL_SCRIPT_DIR}/mutex_lock.sh"
source "${PARALLEL_SCRIPT_DIR}/conflict_detector.sh"

# 执行日志
PARALLEL_EXECUTION_LOG="${PARALLEL_PROJECT_ROOT}/.workflow/logs/parallel_execution.log"


# ==================== 初始化 ====================

init_parallel_system() {
    log_info "Initializing parallel execution system..."

    # 初始化互斥锁系统
    init_lock_system

    # 创建日志目录
    mkdir -p "$(dirname "${PARALLEL_EXECUTION_LOG}")"

    log_success "Parallel execution system ready"
}

# ==================== 并行执行核心 ====================

execute_parallel_group() {
    local phase="$1"
    local group_id="$2"
    shift 2
    local command=("$@")

    log_info "================================"
    log_info "Executing parallel group: ${group_id}"
    log_info "Phase: ${phase}"
    log_info "Command: ${command[*]}"
    log_info "================================"

    local start_time=$(date +%s)
    local execution_id="${group_id}_${start_time}_$$"

    # 记录执行开始
    log_execution_start "${execution_id}" "${phase}" "${group_id}"

    # 尝试获取锁
    if ! acquire_lock "${group_id}"; then
        log_error "Failed to acquire lock for ${group_id}"
        log_execution_failed "${execution_id}" "LOCK_TIMEOUT"
        return 1
    fi

    # 执行命令
    local exit_code=0
    if "${command[@]}"; then
        log_success "✓ Group ${group_id} completed successfully"
        log_execution_success "${execution_id}"
    else
        exit_code=$?
        log_error "✗ Group ${group_id} failed with exit code ${exit_code}"
        log_execution_failed "${execution_id}" "COMMAND_FAILED:${exit_code}"
    fi

    # 释放锁
    release_lock "${group_id}"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "Group ${group_id} execution time: ${duration}s"

    return ${exit_code}
}

execute_parallel_groups() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Planning parallel execution for phase ${phase}"
    log_info "Groups: ${groups[*]}"

    # 步骤1: 冲突检测
    log_info "Step 1/3: Conflict detection..."
    if ! validate_parallel_execution "${phase}" "${groups[@]}"; then
        log_warn "Conflicts detected, applying resolution strategy..."

        # 获取推荐策略
        local strategy=$(recommend_execution_strategy "${phase}" "${groups[@]}")
        log_warn "Recommended strategy: ${strategy}"

        if [[ "${strategy}" == "SERIAL" ]]; then
            log_warn "⬇️  Downgrading to serial execution"
            execute_serial_groups "${phase}" "${groups[@]}"
            return $?
        fi
    fi

    # 步骤2: 并行执行（后台进程）
    log_info "Step 2/3: Parallel execution..."

    local pids=()
    local group_status=()

    for group_id in "${groups[@]}"; do
        log_info "Starting group: ${group_id} (background)"

        # 每个group在后台执行
        (
            execute_parallel_group "${phase}" "${group_id}" echo "Executing ${group_id}"
        ) &

        local pid=$!
        pids+=("${pid}")
        group_status+=("${group_id}:${pid}:RUNNING")

        log_info "Group ${group_id} started with PID ${pid}"
    done

    # 步骤3: 等待所有group完成
    log_info "Step 3/3: Waiting for completion..."

    local failed_count=0
    for i in "${!pids[@]}"; do
        local pid="${pids[i]}"
        local group_id="${groups[i]}"

        if wait "${pid}"; then
            log_success "✓ Group ${group_id} (PID ${pid}) completed"
            group_status[i]="${group_id}:${pid}:SUCCESS"
        else
            local exit_code=$?
            log_error "✗ Group ${group_id} (PID ${pid}) failed with exit code ${exit_code}"
            group_status[i]="${group_id}:${pid}:FAILED:${exit_code}"
            ((failed_count++))
        fi
    done

    # 总结
    log_info "================================"
    log_info "Parallel execution summary:"
    log_info "Total groups: ${#groups[@]}"
    log_info "Successful: $((${#groups[@]} - failed_count))"
    log_info "Failed: ${failed_count}"
    log_info "================================"

    if [[ ${failed_count} -gt 0 ]]; then
        return 1
    else
        return 0
    fi
}

execute_serial_groups() {
    local phase="$1"
    shift
    local groups=("$@")

    log_warn "Executing groups serially (fallback mode)"

    local failed_count=0
    for group_id in "${groups[@]}"; do
        log_info "Executing group: ${group_id}"

        if execute_parallel_group "${phase}" "${group_id}" echo "Executing ${group_id}"; then
            log_success "✓ Group ${group_id} completed"
        else
            log_error "✗ Group ${group_id} failed"
            ((failed_count++))
        fi
    done

    if [[ ${failed_count} -gt 0 ]]; then
        log_error "Serial execution failed: ${failed_count} groups failed"
        return 1
    else
        log_success "Serial execution completed successfully"
        return 0
    fi
}

# ==================== 智能执行决策 ====================

decide_execution_mode() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Analyzing execution mode..."

    # 规则1: 单个group，直接执行
    if [[ ${#groups[@]} -eq 1 ]]; then
        echo "DIRECT"
        return 0
    fi

    # 规则2: 检测冲突
    if ! validate_parallel_execution "${phase}" "${groups[@]}" >/dev/null 2>&1; then
        echo "SERIAL"
        return 0
    fi

    # 规则3: 检查系统资源
    local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local load_int=${load%.*}

    if [[ ${load_int} -gt 4 ]]; then
        log_warn "High system load: ${load}, recommending serial execution"
        echo "SERIAL"
        return 0
    fi

    # 规则4: 默认并行
    echo "PARALLEL"
}

execute_with_strategy() {
    local phase="$1"
    shift
    local groups=("$@")

    local mode=$(decide_execution_mode "${phase}" "${groups[@]}")
    log_info "Execution mode: ${mode}"

    case "${mode}" in
        DIRECT)
            execute_parallel_group "${phase}" "${groups[0]}" echo "Executing ${groups[0]}"
            ;;
        SERIAL)
            execute_serial_groups "${phase}" "${groups[@]}"
            ;;
        PARALLEL)
            execute_parallel_groups "${phase}" "${groups[@]}"
            ;;
        *)
            log_error "Unknown execution mode: ${mode}"
            return 1
            ;;
    esac
}

# ==================== 死锁监控 ====================

start_deadlock_monitor() {
    log_info "Starting deadlock monitor..."

    (
        while true; do
            sleep "${DEADLOCK_CHECK_INTERVAL}"
            check_deadlock
        done
    ) &

    local monitor_pid=$!
    echo "${monitor_pid}" > "${LOCK_DIR}/deadlock_monitor.pid"

    log_info "Deadlock monitor started with PID ${monitor_pid}"
}

stop_deadlock_monitor() {
    local pid_file="${LOCK_DIR}/deadlock_monitor.pid"

    if [[ -f "${pid_file}" ]]; then
        local monitor_pid=$(cat "${pid_file}")
        if kill -0 "${monitor_pid}" 2>/dev/null; then
            log_info "Stopping deadlock monitor (PID ${monitor_pid})"
            kill "${monitor_pid}" 2>/dev/null || true
        fi
        rm -f "${pid_file}"
    fi
}

# ==================== 执行追踪 ====================

log_execution_start() {
    local execution_id="$1"
    local phase="$2"
    local group_id="$3"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local log_entry=$(cat <<EOF
{"timestamp":"${timestamp}","execution_id":"${execution_id}","phase":"${phase}","group_id":"${group_id}","status":"STARTED","pid":$$}
EOF
)

    echo "${log_entry}" >> "${PARALLEL_EXECUTION_LOG}"
}

log_execution_success() {
    local execution_id="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local log_entry=$(cat <<EOF
{"timestamp":"${timestamp}","execution_id":"${execution_id}","status":"SUCCESS"}
EOF
)

    echo "${log_entry}" >> "${PARALLEL_EXECUTION_LOG}"
}

log_execution_failed() {
    local execution_id="$1"
    local reason="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local log_entry=$(cat <<EOF
{"timestamp":"${timestamp}","execution_id":"${execution_id}","status":"FAILED","reason":"${reason}"}
EOF
)

    echo "${log_entry}" >> "${PARALLEL_EXECUTION_LOG}"
}

# ==================== 报告 ====================

show_execution_report() {
    echo -e "\n${C_CYAN}=== Parallel Execution Report ===${C_NC}\n"

    if [[ ! -f "${PARALLEL_EXECUTION_LOG}" ]]; then
        echo -e "${C_YELLOW}No execution history yet${C_NC}"
        return 0
    fi

    # 统计
    local total=$(grep -c '"execution_id"' "${PARALLEL_EXECUTION_LOG}" 2>/dev/null || echo 0)
    local success=$(grep -c '"status":"SUCCESS"' "${PARALLEL_EXECUTION_LOG}" 2>/dev/null || echo 0)
    local failed=$(grep -c '"status":"FAILED"' "${PARALLEL_EXECUTION_LOG}" 2>/dev/null || echo 0)

    echo -e "${C_YELLOW}Statistics:${C_NC}"
    echo -e "  Total Executions: ${total}"
    echo -e "  ${C_GREEN}Successful: ${success}${C_NC}"
    echo -e "  ${C_RED}Failed: ${failed}${C_NC}"
    if [[ ${total} -gt 0 ]]; then
        echo -e "  Success Rate: $(awk "BEGIN {printf \"%.1f%%\", ($success/$total)*100}")"
    fi

    # 按Phase统计
    echo -e "\n${C_YELLOW}By Phase:${C_NC}"
    jq -r 'select(.phase) | .phase' "${PARALLEL_EXECUTION_LOG}" 2>/dev/null | sort | uniq -c | sort -rn || true

    # 最近10次执行
    echo -e "\n${C_YELLOW}Recent Executions (last 10):${C_NC}"
    tail -n 20 "${PARALLEL_EXECUTION_LOG}" | \
        jq -r 'select(.execution_id) | "\(.timestamp) | \(.phase // "N/A") | \(.group_id // "N/A") | \(.status)"' 2>/dev/null | \
        tail -n 10 || tail -n 10 "${PARALLEL_EXECUTION_LOG}"
}

# ==================== 工具函数 ====================

log_info() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_CYAN}[PARALLEL]${C_NC} $*" >&2
}

log_success() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_GREEN}[PARALLEL]${C_NC} $*" >&2
}

log_warn() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_YELLOW}[PARALLEL]${C_NC} $*" >&2
}

log_error() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_RED}[PARALLEL]${C_NC} $*" >&2
}

# ==================== CLI ====================

show_usage() {
    cat << EOF
${C_CYAN}Claude Enhancer - Parallel Execution Engine${C_NC}

${C_YELLOW}Usage:${C_NC}
  $0 <command> [options]

${C_YELLOW}Commands:${C_NC}
  ${C_GREEN}init${C_NC}                                Initialize parallel system
  ${C_GREEN}execute${C_NC} <phase> <group1> <group2> ... Execute groups with auto-strategy
  ${C_GREEN}parallel${C_NC} <phase> <group1> <group2> ...Force parallel execution
  ${C_GREEN}serial${C_NC} <phase> <group1> <group2> ... Force serial execution
  ${C_GREEN}report${C_NC}                              Show execution report
  ${C_GREEN}monitor-start${C_NC}                       Start deadlock monitor
  ${C_GREEN}monitor-stop${C_NC}                        Stop deadlock monitor

${C_YELLOW}Examples:${C_NC}
  $0 init
  $0 execute P3 impl-backend impl-frontend
  $0 parallel P4 test-unit test-integration test-performance
  $0 serial P6 release-prep
  $0 report

EOF
}

main() {
    local command="${1:-}"

    case "${command}" in
        init)
            init_parallel_system
            ;;

        execute)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            execute_with_strategy "${phase}" "$@"
            ;;

        parallel)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            execute_parallel_groups "${phase}" "$@"
            ;;

        serial)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            execute_serial_groups "${phase}" "$@"
            ;;

        report)
            show_execution_report
            ;;

        monitor-start)
            start_deadlock_monitor
            ;;

        monitor-stop)
            stop_deadlock_monitor
            ;;

        help|--help|-h)
            show_usage
            ;;

        *)
            log_error "Unknown command: ${command}"
            show_usage
            exit 1
            ;;
    esac
}

# 如果直接执行，运行main函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
