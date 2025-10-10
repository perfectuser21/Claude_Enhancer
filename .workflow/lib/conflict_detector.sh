#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Conflict Detection System v1.0
# 基于STAGES.yml的智能冲突检测
# =============================================================================
# Purpose: 检测并行任务的文件路径冲突，自动降级策略
# Features:
#   - Glob模式匹配
#   - 基于STAGES.yml规则
#   - 自动降级（并行→串行）
#   - 冲突审计日志
# =============================================================================

set -euo pipefail

# 全局配置（避免readonly冲突）
CONFLICT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFLICT_PROJECT_ROOT="$(cd "${CONFLICT_SCRIPT_DIR}/../.." && pwd)"
CONFLICT_STAGES_CONFIG="${CONFLICT_PROJECT_ROOT}/.workflow/STAGES.yml"
CONFLICT_LOG="${CONFLICT_PROJECT_ROOT}/.workflow/logs/conflicts.log"

# 颜色输出
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_CYAN='\033[0;36m'
readonly C_NC='\033[0m'

# ==================== YAML解析 ====================

parse_conflict_rules() {
    python3 << 'EOF'
import yaml
import sys
import os

config_file = os.environ.get('CONFLICT_STAGES_CONFIG', '.workflow/STAGES.yml')

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if 'conflict_detection' not in data:
        print("# No conflict detection rules", file=sys.stderr)
        sys.exit(0)

    rules = data['conflict_detection'].get('rules', [])

    for rule in rules:
        name = rule.get('name', '')
        severity = rule.get('severity', 'MAJOR')
        action = rule.get('action', 'downgrade_to_serial')
        paths = rule.get('paths', [])

        for path in paths:
            # 输出格式: rule_name|severity|action|path_pattern
            print(f"{name}|{severity}|{action}|{path}")

except Exception as e:
    print(f"Error parsing STAGES.yml: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

parse_parallel_group() {
    local phase="$1"
    local group_id="$2"

    python3 << EOF
import yaml
import sys
import os

config_file = os.environ.get('CONFLICT_STAGES_CONFIG', '.workflow/STAGES.yml')

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    phase_groups = data.get('parallel_groups', {}).get('${phase}', [])

    for group in phase_groups:
        if group.get('group_id') == '${group_id}':
            conflict_paths = group.get('conflict_paths', [])
            for path in conflict_paths:
                print(path)
            break

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ==================== 冲突检测核心 ====================

check_path_conflict() {
    local path1="$1"
    local path2="$2"

    # 规范化路径
    path1=$(realpath -m "${CONFLICT_PROJECT_ROOT}/${path1}" 2>/dev/null || echo "${CONFLICT_PROJECT_ROOT}/${path1}")
    path2=$(realpath -m "${CONFLICT_PROJECT_ROOT}/${path2}" 2>/dev/null || echo "${CONFLICT_PROJECT_ROOT}/${path2}")

    # 精确匹配
    if [[ "${path1}" == "${path2}" ]]; then
        echo "EXACT"
        return 0
    fi

    # 父子关系检测
    if [[ "${path1}" == "${path2}"* ]] || [[ "${path2}" == "${path1}"* ]]; then
        echo "PARENT_CHILD"
        return 0
    fi

    # 同目录检测
    local dir1=$(dirname "${path1}")
    local dir2=$(dirname "${path2}")
    if [[ "${dir1}" == "${dir2}" ]]; then
        echo "SAME_DIR"
        return 0
    fi

    echo "NONE"
    return 1
}

match_glob_pattern() {
    local file_path="$1"
    local pattern="$2"

    # 使用bash内置的glob匹配
    # 将**转换为*（简化版）
    local bash_pattern="${pattern//\*\*/\*}"

    if [[ "${file_path}" == ${bash_pattern} ]]; then
        return 0
    else
        return 1
    fi
}

detect_conflicts() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Detecting conflicts for phase ${phase}, groups: ${groups[*]}"

    local conflicts=0
    local conflict_details=()

    # 获取所有group的冲突路径
    declare -A group_paths
    for group_id in "${groups[@]}"; do
        local paths=$(parse_parallel_group "${phase}" "${group_id}")
        group_paths["${group_id}"]="${paths}"
    done

    # 两两比较
    local group_array=("${groups[@]}")
    for ((i=0; i<${#group_array[@]}; i++)); do
        for ((j=i+1; j<${#group_array[@]}; j++)); do
            local group1="${group_array[i]}"
            local group2="${group_array[j]}"

            log_info "Checking conflict between ${group1} and ${group2}"

            # 比较路径模式
            while IFS= read -r path1; do
                [[ -z "${path1}" ]] && continue

                while IFS= read -r path2; do
                    [[ -z "${path2}" ]] && continue

                    # 检查路径冲突
                    local conflict_type=$(check_path_conflict "${path1}" "${path2}")
                    if [[ "${conflict_type}" != "NONE" ]]; then
                        log_warn "⚠️  Conflict detected: ${group1} vs ${group2}"
                        log_warn "    Path1: ${path1}"
                        log_warn "    Path2: ${path2}"
                        log_warn "    Type: ${conflict_type}"

                        ((conflicts++))
                        conflict_details+=("${group1}:${group2}:${conflict_type}:${path1}:${path2}")

                        # 记录到审计日志
                        log_conflict "${phase}" "${group1}" "${group2}" "${conflict_type}" "${path1}" "${path2}"
                    fi
                done <<< "${group_paths[${group2}]}"
            done <<< "${group_paths[${group1}]}"
        done
    done

    if [[ ${conflicts} -gt 0 ]]; then
        log_error "❌ Total conflicts detected: ${conflicts}"

        # 输出冲突详情
        for detail in "${conflict_details[@]}"; do
            echo "${detail}"
        done

        return 1
    else
        log_success "✓ No conflicts detected"
        return 0
    fi
}

# ==================== 规则匹配 ====================

find_matching_rule() {
    local file_path="$1"

    # 设置环境变量供Python使用
    export CONFLICT_STAGES_CONFIG

    # 解析所有规则
    while IFS='|' read -r rule_name severity action path_pattern; do
        [[ -z "${rule_name}" ]] && continue
        [[ "${rule_name}" =~ ^# ]] && continue

        # 检查路径是否匹配规则
        if match_glob_pattern "${file_path}" "${path_pattern}"; then
            echo "${rule_name}|${severity}|${action}"
            return 0
        fi
    done < <(parse_conflict_rules)

    # 默认规则
    echo "default|MAJOR|downgrade_to_serial"
}

apply_conflict_action() {
    local action="$1"
    local group1="$2"
    local group2="$3"

    log_info "Applying action: ${action} for ${group1}, ${group2}"

    case "${action}" in
        downgrade_to_serial)
            log_warn "⬇️  Downgrading to serial execution"

            # 硬化：记录降级证据（Trust-but-Verify）
            local downgrade_log="${PROJECT_ROOT:-.}/.workflow/logs/executor_downgrade.log"
            mkdir -p "$(dirname "$downgrade_log")"
            echo "DOWNGRADE: reason=conflict_detected action=${action} group1=${group1} group2=${group2} stage=${CURRENT_PHASE:-unknown} ts=$(date -Is)" | tee -a "$downgrade_log" >&2

            echo "SERIAL"
            ;;

        mutex_lock)
            log_warn "🔒 Applying mutex lock"
            echo "MUTEX"
            ;;

        queue_execution)
            log_warn "📋 Queueing execution"
            echo "QUEUE"
            ;;

        serialize_operations)
            log_warn "⏭️  Serializing operations"
            echo "SERIALIZE"
            ;;

        abort)
            log_error "🛑 Aborting execution due to conflict"
            echo "ABORT"
            return 1
            ;;

        *)
            log_warn "Unknown action: ${action}, defaulting to serial"
            echo "SERIAL"
            ;;
    esac
}

# ==================== 审计日志 ====================

log_conflict() {
    local phase="$1"
    local group1="$2"
    local group2="$3"
    local conflict_type="$4"
    local path1="$5"
    local path2="$6"

    mkdir -p "$(dirname "${CONFLICT_LOG}")"

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local log_entry=$(cat <<EOF
{
  "timestamp": "${timestamp}",
  "phase": "${phase}",
  "group1": "${group1}",
  "group2": "${group2}",
  "conflict_type": "${conflict_type}",
  "path1": "${path1}",
  "path2": "${path2}"
}
EOF
)

    echo "${log_entry}" >> "${CONFLICT_LOG}"
}

# ==================== 报告 ====================

show_conflict_report() {
    echo -e "\n${C_CYAN}=== Conflict Detection Report ===${C_NC}"

    if [[ ! -f "${CONFLICT_LOG}" ]]; then
        echo -e "${C_GREEN}No conflicts detected yet${C_NC}"
        return 0
    fi

    local total_conflicts=$(grep -c '"timestamp"' "${CONFLICT_LOG}" 2>/dev/null || echo 0)
    echo -e "${C_YELLOW}Total Conflicts: ${total_conflicts}${C_NC}\n"

    # 按类型统计
    echo -e "${C_YELLOW}By Type:${C_NC}"
    jq -r '.conflict_type' "${CONFLICT_LOG}" 2>/dev/null | sort | uniq -c | sort -rn || true

    # 最近10条冲突
    echo -e "\n${C_YELLOW}Recent Conflicts (last 10):${C_NC}"
    tail -n 10 "${CONFLICT_LOG}" | jq -r '"\(.timestamp) | \(.phase) | \(.group1) vs \(.group2) | \(.conflict_type)"' 2>/dev/null || \
        tail -n 10 "${CONFLICT_LOG}"
}

# ==================== 高级API ====================

validate_parallel_execution() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Validating parallel execution plan..."
    log_info "Phase: ${phase}"
    log_info "Groups: ${groups[*]}"

    # 设置环境变量
    export CONFLICT_STAGES_CONFIG

    # 检测冲突
    if detect_conflicts "${phase}" "${groups[@]}"; then
        log_success "✓ Parallel execution validated, no conflicts"
        return 0
    else
        log_error "✗ Conflicts detected, parallel execution not recommended"
        return 1
    fi
}

recommend_execution_strategy() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Analyzing execution strategy..."

    # 设置环境变量
    export CONFLICT_STAGES_CONFIG

    if detect_conflicts "${phase}" "${groups[@]}" >/dev/null 2>&1; then
        echo "PARALLEL"
        log_success "✓ Recommend: PARALLEL execution"
    else
        echo "SERIAL"
        log_warn "⚠️  Recommend: SERIAL execution (conflicts detected)"
    fi
}

# ==================== 工具函数 ====================

log_info() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_CYAN}[CONFLICT]${C_NC} $*" >&2
}

log_success() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_GREEN}[CONFLICT]${C_NC} $*" >&2
}

log_warn() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_YELLOW}[CONFLICT]${C_NC} $*" >&2
}

log_error() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${C_RED}[CONFLICT]${C_NC} $*" >&2
}

# ==================== CLI ====================

show_usage() {
    cat << EOF
${C_CYAN}Claude Enhancer - Conflict Detection System${C_NC}

${C_YELLOW}Usage:${C_NC}
  $0 <command> [options]

${C_YELLOW}Commands:${C_NC}
  ${C_GREEN}detect${C_NC} <phase> <group1> <group2> ...    Detect conflicts between groups
  ${C_GREEN}validate${C_NC} <phase> <group1> <group2> ...  Validate parallel execution
  ${C_GREEN}recommend${C_NC} <phase> <group1> <group2> ... Recommend execution strategy
  ${C_GREEN}report${C_NC}                                  Show conflict report
  ${C_GREEN}rules${C_NC}                                   List all conflict rules

${C_YELLOW}Examples:${C_NC}
  $0 detect P3 impl-backend impl-frontend
  $0 validate P3 impl-backend impl-frontend impl-infrastructure
  $0 recommend P4 test-unit test-integration
  $0 report

EOF
}

main() {
    local command="${1:-}"

    # 设置环境变量
    export CONFLICT_STAGES_CONFIG

    case "${command}" in
        detect)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            detect_conflicts "${phase}" "$@"
            ;;

        validate)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            validate_parallel_execution "${phase}" "$@"
            ;;

        recommend)
            [[ -z "${2:-}" ]] && { log_error "Missing phase"; show_usage; exit 1; }
            local phase="$2"
            shift 2
            recommend_execution_strategy "${phase}" "$@"
            ;;

        report)
            show_conflict_report
            ;;

        rules)
            echo -e "${C_CYAN}Conflict Detection Rules:${C_NC}\n"
            parse_conflict_rules | column -t -s '|' -N "RULE,SEVERITY,ACTION,PATH_PATTERN"
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
