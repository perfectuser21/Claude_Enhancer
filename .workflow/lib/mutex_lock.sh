#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Mutex Lock System v1.0
# 生产级并行执行互斥锁机制
# =============================================================================
# Purpose: 实现基于flock的互斥锁，防止并行任务冲突
# Features:
#   - POSIX文件锁（flock）
#   - 死锁检测和超时
#   - 资源追踪和清理
#   - 异常恢复机制
# =============================================================================

set -euo pipefail

# 全局配置
readonly LOCK_DIR="${LOCK_DIR:-/tmp/ce_locks}"
readonly LOCK_REGISTRY="${LOCK_DIR}/registry.log"
readonly LOCK_TIMEOUT="${LOCK_TIMEOUT:-300}"  # 默认5分钟超时
readonly DEADLOCK_CHECK_INTERVAL=60           # 死锁检查间隔（秒）
readonly MAX_LOCK_AGE=600                     # 最大锁存活时间（10分钟）

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# ==================== 初始化 ====================

init_lock_system() {
    # 创建锁目录
    mkdir -p "${LOCK_DIR}"

    # 初始化注册表
    if [[ ! -f "${LOCK_REGISTRY}" ]]; then
        cat > "${LOCK_REGISTRY}" << 'EOF'
# Claude Enhancer Lock Registry
# Format: lock_id:pid:group_id:timestamp:status
# Status: ACTIVE|RELEASED|TIMEOUT|FAILED
EOF
    fi

    # 清理孤儿锁（启动时）
    cleanup_orphan_locks

    log_info "Mutex lock system initialized"
}

# ==================== 核心锁机制 ====================

acquire_lock() {
    local group_id="$1"
    local timeout="${2:-$LOCK_TIMEOUT}"
    local lock_file="${LOCK_DIR}/${group_id}.lock"
    local lock_fd=200  # 使用固定的文件描述符

    log_info "Attempting to acquire lock: ${group_id} (timeout: ${timeout}s)"

    # 打开锁文件（如果不存在则创建）
    eval "exec ${lock_fd}>${lock_file}"

    # 尝试获取排他锁，带超时
    local start_time=$(date +%s)
    if flock -x -w "${timeout}" "${lock_fd}"; then
        local end_time=$(date +%s)
        local wait_time=$((end_time - start_time))

        # 记录锁信息
        local lock_record="${group_id}:$$:${group_id}:${start_time}:ACTIVE"
        echo "${lock_record}" >> "${LOCK_REGISTRY}"

        log_success "✓ Acquired lock: ${group_id} (waited ${wait_time}s, PID: $$)"

        # 设置trap确保异常时释放锁
        trap "release_lock '${group_id}' ${lock_fd}" EXIT INT TERM

        return 0
    else
        log_error "✗ Failed to acquire lock: ${group_id} (timeout after ${timeout}s)"
        eval "exec ${lock_fd}>&-"  # 关闭文件描述符
        return 1
    fi
}

release_lock() {
    local group_id="$1"
    local lock_fd="${2:-200}"
    local lock_file="${LOCK_DIR}/${group_id}.lock"

    log_info "Releasing lock: ${group_id} (PID: $$)"

    # 更新注册表状态
    local timestamp=$(date +%s)
    sed -i "s/^\(${group_id}:$$:.*:\)ACTIVE$/\1RELEASED:${timestamp}/" "${LOCK_REGISTRY}" 2>/dev/null || true

    # 释放文件锁
    if [[ -e /proc/$$/fd/${lock_fd} ]]; then
        eval "exec ${lock_fd}>&-"
        log_success "✓ Released lock: ${group_id}"
    else
        log_warn "Lock FD already closed: ${group_id}"
    fi

    # 清理锁文件（可选，保留可以防止竞态条件）
    # rm -f "${lock_file}" 2>/dev/null || true
}

# ==================== 高级锁API ====================

execute_with_lock() {
    local group_id="$1"
    shift
    local command=("$@")

    log_info "Executing with lock: ${group_id}"
    log_info "Command: ${command[*]}"

    # 获取锁
    if ! acquire_lock "${group_id}"; then
        log_error "Cannot acquire lock for ${group_id}, aborting"
        return 1
    fi

    # 执行命令
    local exit_code=0
    "${command[@]}" || exit_code=$?

    # 释放锁
    release_lock "${group_id}"

    return ${exit_code}
}

try_lock() {
    local group_id="$1"
    local lock_file="${LOCK_DIR}/${group_id}.lock"
    local lock_fd=201

    # 非阻塞尝试获取锁
    eval "exec ${lock_fd}>${lock_file}"

    if flock -x -n "${lock_fd}"; then
        echo "${lock_fd}"  # 返回文件描述符
        return 0
    else
        eval "exec ${lock_fd}>&-"
        return 1
    fi
}

# ==================== 死锁检测 ====================

check_deadlock() {
    log_info "Checking for deadlocks..."

    local now=$(date +%s)
    local deadlocks=0

    # 读取所有活动锁
    while IFS=':' read -r lock_id pid group_id timestamp status; do
        # 跳过注释和空行
        [[ "$lock_id" =~ ^# ]] && continue
        [[ -z "$lock_id" ]] && continue

        # 只检查活动锁
        [[ "$status" != "ACTIVE" ]] && continue

        local lock_age=$((now - timestamp))

        # 检查是否超过最大存活时间
        if [[ ${lock_age} -gt ${MAX_LOCK_AGE} ]]; then
            log_warn "⚠️  Stale lock detected: ${lock_id} (age: ${lock_age}s, PID: ${pid})"

            # 检查进程是否还存在
            if ! kill -0 "${pid}" 2>/dev/null; then
                log_error "Process ${pid} not found, cleaning up orphan lock: ${lock_id}"
                cleanup_lock "${lock_id}" "${pid}"
                ((deadlocks++))
            else
                log_warn "Process ${pid} still running but lock is stale (${lock_age}s)"
                # 可选：发送警告信号或强制清理
            fi
        fi
    done < "${LOCK_REGISTRY}"

    if [[ ${deadlocks} -gt 0 ]]; then
        log_warn "Cleaned up ${deadlocks} deadlocked/orphan locks"
    else
        log_info "No deadlocks detected"
    fi

    return ${deadlocks}
}

cleanup_orphan_locks() {
    log_info "Cleaning up orphan locks..."

    local cleaned=0
    local temp_file="${LOCK_REGISTRY}.tmp"

    # 创建临时文件保存有效锁
    : > "${temp_file}"

    while IFS=':' read -r lock_id pid group_id timestamp status; do
        # 保留注释行
        if [[ "$lock_id" =~ ^# ]]; then
            echo "${lock_id}:${pid}:${group_id}:${timestamp}:${status}" >> "${temp_file}"
            continue
        fi

        # 跳过空行
        [[ -z "$lock_id" ]] && continue

        # 如果是活动锁且进程不存在，标记为清理
        if [[ "$status" == "ACTIVE" ]] && ! kill -0 "${pid}" 2>/dev/null; then
            log_warn "Cleaning orphan lock: ${lock_id} (PID: ${pid})"
            echo "${lock_id}:${pid}:${group_id}:${timestamp}:ORPHAN_CLEANED" >> "${temp_file}"

            # 删除锁文件
            rm -f "${LOCK_DIR}/${lock_id}.lock" 2>/dev/null || true
            ((cleaned++))
        else
            # 保留有效记录
            echo "${lock_id}:${pid}:${group_id}:${timestamp}:${status}" >> "${temp_file}"
        fi
    done < "${LOCK_REGISTRY}"

    # 替换注册表
    mv "${temp_file}" "${LOCK_REGISTRY}"

    log_info "Cleaned up ${cleaned} orphan locks"
    return ${cleaned}
}

cleanup_lock() {
    local lock_id="$1"
    local pid="$2"
    local timestamp=$(date +%s)

    # 更新注册表
    sed -i "s/^\(${lock_id}:${pid}:.*:\)ACTIVE$/\1TIMEOUT:${timestamp}/" "${LOCK_REGISTRY}" 2>/dev/null || true

    # 删除锁文件
    rm -f "${LOCK_DIR}/${lock_id}.lock" 2>/dev/null || true
}

# ==================== 监控和报告 ====================

show_lock_status() {
    echo -e "\n${CYAN}=== Lock System Status ===${NC}"
    echo -e "${CYAN}Lock Directory: ${LOCK_DIR}${NC}"
    echo -e "${CYAN}Active Locks:${NC}\n"

    local now=$(date +%s)
    local active_count=0

    # 表头
    printf "%-20s %-8s %-20s %-12s %-10s\n" "LOCK_ID" "PID" "GROUP_ID" "AGE(s)" "STATUS"
    printf "%-20s %-8s %-20s %-12s %-10s\n" "--------------------" "--------" "--------------------" "------------" "----------"

    while IFS=':' read -r lock_id pid group_id timestamp status; do
        [[ "$lock_id" =~ ^# ]] && continue
        [[ -z "$lock_id" ]] && continue

        local age=$((now - timestamp))

        # 颜色化状态
        local status_color="${NC}"
        case "$status" in
            ACTIVE) status_color="${GREEN}"; ((active_count++)) ;;
            RELEASED) status_color="${CYAN}" ;;
            TIMEOUT) status_color="${YELLOW}" ;;
            FAILED|ORPHAN*) status_color="${RED}" ;;
        esac

        printf "%-20s %-8s %-20s %-12s ${status_color}%-10s${NC}\n" \
            "${lock_id}" "${pid}" "${group_id}" "${age}" "${status}"
    done < "${LOCK_REGISTRY}"

    echo -e "\n${GREEN}Active Locks: ${active_count}${NC}"
    echo -e "${YELLOW}Lock Files: $(ls -1 "${LOCK_DIR}"/*.lock 2>/dev/null | wc -l)${NC}"
}

# ==================== 管理工具 ====================

force_release_all() {
    log_warn "Force releasing all locks..."

    # 更新所有活动锁为FORCE_RELEASED
    local timestamp=$(date +%s)
    sed -i "s/:ACTIVE$/:FORCE_RELEASED:${timestamp}/" "${LOCK_REGISTRY}"

    # 删除所有锁文件
    rm -f "${LOCK_DIR}"/*.lock 2>/dev/null || true

    log_success "All locks force released"
}

reset_lock_system() {
    log_warn "Resetting lock system..."

    # 备份注册表
    if [[ -f "${LOCK_REGISTRY}" ]]; then
        cp "${LOCK_REGISTRY}" "${LOCK_REGISTRY}.backup.$(date +%s)"
    fi

    # 清空锁目录
    rm -rf "${LOCK_DIR}"

    # 重新初始化
    init_lock_system

    log_success "Lock system reset complete"
}

# ==================== 工具函数 ====================

log_info() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${CYAN}[MUTEX]${NC} $*" >&2
}

log_success() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}[MUTEX]${NC} $*" >&2
}

log_warn() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}[MUTEX]${NC} $*" >&2
}

log_error() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}[MUTEX]${NC} $*" >&2
}

# ==================== CLI ====================

show_usage() {
    cat << EOF
${CYAN}Claude Enhancer - Mutex Lock System${NC}

${YELLOW}Usage:${NC}
  $0 <command> [options]

${YELLOW}Commands:${NC}
  ${GREEN}init${NC}                    Initialize lock system
  ${GREEN}acquire${NC} <group_id>      Acquire lock for group
  ${GREEN}release${NC} <group_id>      Release lock for group
  ${GREEN}status${NC}                  Show all locks status
  ${GREEN}check-deadlock${NC}          Check for deadlocks
  ${GREEN}cleanup${NC}                 Cleanup orphan locks
  ${GREEN}force-release-all${NC}       Force release all locks (dangerous!)
  ${GREEN}reset${NC}                   Reset entire lock system

${YELLOW}Examples:${NC}
  $0 init
  $0 acquire impl-backend
  $0 release impl-backend
  $0 status
  $0 check-deadlock

${YELLOW}Environment Variables:${NC}
  LOCK_DIR              Lock directory (default: /tmp/ce_locks)
  LOCK_TIMEOUT          Lock timeout in seconds (default: 300)

EOF
}

main() {
    local command="${1:-}"

    case "${command}" in
        init)
            init_lock_system
            ;;
        acquire)
            [[ -z "${2:-}" ]] && { log_error "Missing group_id"; show_usage; exit 1; }
            acquire_lock "$2" "${3:-$LOCK_TIMEOUT}"
            ;;
        release)
            [[ -z "${2:-}" ]] && { log_error "Missing group_id"; show_usage; exit 1; }
            release_lock "$2"
            ;;
        status)
            show_lock_status
            ;;
        check-deadlock)
            check_deadlock
            ;;
        cleanup)
            cleanup_orphan_locks
            ;;
        force-release-all)
            force_release_all
            ;;
        reset)
            reset_lock_system
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
