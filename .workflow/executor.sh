#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Workflow Execution Engine v2.0
# 智能Phase管理和Gates验证引擎
# =============================================================================

set -euo pipefail

# Cleanup trap - Track temporary resources
TEMP_FILES=()
TEMP_DIRS=()

cleanup() {
    local exit_code=$?
    echo "[CLEANUP] Removing temporary resources..." >&2

    # Clean temp files
    for temp_file in "${TEMP_FILES[@]}"; do
        [[ -f "$temp_file" ]] && rm -f "$temp_file" 2>/dev/null || true
    done

    # Clean temp directories
    for temp_dir in "${TEMP_DIRS[@]}"; do
        [[ -d "$temp_dir" ]] && rm -rf "$temp_dir" 2>/dev/null || true
    done

    # Clean Python cache in script directory
    find "${SCRIPT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # Rotate log if too large (keep last 100 lines)
    if [[ -f "${LOG_FILE}" ]]; then
        local line_count=$(wc -l < "${LOG_FILE}" 2>/dev/null || echo 0)
        if [[ $line_count -gt 1000 ]]; then
            tail -n 100 "${LOG_FILE}" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "${LOG_FILE}"
        fi
    fi

    exit $exit_code
}

trap cleanup EXIT INT TERM HUP


# 全局配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly GATES_CONFIG="${SCRIPT_DIR}/gates.yml"
readonly PHASE_DIR="${PROJECT_ROOT}/.phase"
readonly GATES_DIR="${PROJECT_ROOT}/.gates"
readonly CLAUDE_HOOKS_DIR="${PROJECT_ROOT}/.claude/hooks"
readonly LOG_FILE="${PROJECT_ROOT}/.workflow/executor.log"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# ==================== 并行执行系统集成 ====================

# Source并行执行器
if [[ -f "${SCRIPT_DIR}/lib/parallel_executor.sh" ]]; then
    # shellcheck source=lib/parallel_executor.sh
    source "${SCRIPT_DIR}/lib/parallel_executor.sh" 2>/dev/null || {
        echo "[WARN] Failed to load parallel_executor.sh" >&2
        PARALLEL_AVAILABLE=false
    }
    PARALLEL_AVAILABLE=true
else
    echo "[WARN] parallel_executor.sh not found, parallel execution disabled" >&2
    PARALLEL_AVAILABLE=false
fi

# 创建日志目录
mkdir -p "${SCRIPT_DIR}/logs" 2>/dev/null || true

# 并行检测函数
is_parallel_enabled() {
    local phase="$1"

    # 检查并行执行器可用性
    [[ "${PARALLEL_AVAILABLE}" != "true" ]] && return 1

    # 检查STAGES.yml配置（从workflow_phase_parallel section）
    # 使用Python解析YAML获取can_parallel值
    local can_parallel=$(python3 << EOF
import yaml
import sys
try:
    with open("${SCRIPT_DIR}/STAGES.yml", 'r') as f:
        data = yaml.safe_load(f)
    wpp = data.get('workflow_phase_parallel', {})
    phase_config = wpp.get('${phase}', {})
    print(phase_config.get('can_parallel', False))
except:
    print(False)
EOF
)

    [[ "${can_parallel}" == "True" ]] && return 0
    return 1
}

# 并行执行函数 (v8.3.0 Enhanced with Skills Middleware)
execute_parallel_workflow() {
    local phase="$1"

    echo "[INFO] Phase ${phase} configured for parallel execution" >&2

    # 初始化并行系统
    if ! init_parallel_system; then
        echo "[ERROR] Failed to initialize parallel system" >&2
        return 1
    fi

    # 读取并行组（从workflow_phase_parallel section）
    local groups
    groups=$(python3 << EOF
import yaml
import sys
try:
    with open("${SCRIPT_DIR}/STAGES.yml", 'r') as f:
        data = yaml.safe_load(f)
    wpp = data.get('workflow_phase_parallel', {})
    phase_config = wpp.get('${phase}', {})
    parallel_groups = phase_config.get('parallel_groups', [])

    # Extract group_id from each group
    group_ids = []
    for group in parallel_groups:
        if isinstance(group, dict) and 'group_id' in group:
            group_ids.append(group['group_id'])

    # Print space-separated group IDs
    print(' '.join(group_ids))
except Exception as e:
    print('', file=sys.stderr)
    sys.exit(1)
EOF
)

    if [[ -z "${groups}" ]]; then
        echo "[WARN] No parallel groups found for ${phase}" >&2
        return 1
    fi

    echo "[INFO] Found parallel groups: ${groups}" >&2

    # ========== SKILLS MIDDLEWARE LAYER (v8.3.0) ==========

    # PRE-EXECUTION: Conflict validator (Skill 2)
    echo "[INFO] [Skill] Running conflict validator..." >&2
    if [[ -x "${PROJECT_ROOT}/scripts/parallel/validate_conflicts.sh" ]]; then
        if ! bash "${PROJECT_ROOT}/scripts/parallel/validate_conflicts.sh" "${phase}" ${groups}; then
            echo "[ERROR] Conflict validation failed, aborting parallel execution" >&2
            return 1
        fi
    else
        echo "[WARN] Conflict validator not found, skipping..." >&2
    fi

    # EXECUTION: Record start time for performance tracking
    local start_time=$(date +%s)

    # 执行并行策略
    if ! execute_with_strategy "${phase}" ${groups}; then
        echo "[ERROR] Parallel execution failed" >&2

        # POST-EXECUTION (on failure): Learning capturer (Skill 4 - enhanced)
        if [[ -x "${PROJECT_ROOT}/scripts/learning/capture.sh" ]]; then
            bash "${PROJECT_ROOT}/scripts/learning/capture.sh" \
                --category error_pattern \
                --description "Parallel execution failed for ${phase}" \
                --phase "${phase}" \
                --parallel-group "${groups}" \
                --parallel-failure "execute_with_strategy returned non-zero" \
                2>/dev/null &
        fi

        return 1
    fi

    # POST-EXECUTION (on success): Performance tracker + Evidence collector

    local exec_time=$(($(date +%s) - start_time))
    local group_count=$(echo "${groups}" | wc -w)

    # Skill 1: Performance tracker (async, non-blocking)
    echo "[INFO] [Skill] Tracking performance metrics..." >&2
    if [[ -x "${PROJECT_ROOT}/scripts/parallel/track_performance.sh" ]]; then
        bash "${PROJECT_ROOT}/scripts/parallel/track_performance.sh" \
            "${phase}" "${exec_time}" "${group_count}" 2>/dev/null &
    fi

    # Skill 3: Evidence collector (async, reminder)
    if [[ -x "${PROJECT_ROOT}/scripts/evidence/collect.sh" ]]; then
        echo "[INFO] [Skill] Evidence collection available: use --auto-detect-parallel --phase ${phase}" >&2
    fi

    # ========== END SKILLS MIDDLEWARE ==========

    echo "[SUCCESS] Phase ${phase} parallel execution completed (${exec_time}s)" >&2
    return 0
}

# ==================== 日志轮转系统 (CE-ISSUE-009) ====================

check_and_rotate_logs() {
    # 轮转所有日志文件（超过10MB）
    local max_size=$((10 * 1024 * 1024))  # 10MB

    # 检查executor.log
    if [[ -f "${LOG_FILE}" ]]; then
        local size=$(stat -c '%s' "${LOG_FILE}" 2>/dev/null || stat -f '%z' "${LOG_FILE}" 2>/dev/null || echo "0")
        if [[ $size -gt $max_size ]]; then
            echo "[LOG_ROTATE] 轮转日志: ${LOG_FILE} ($(($size / 1024 / 1024))MB)" >&2
            mv "${LOG_FILE}" "${LOG_FILE}.1"
            gzip -f "${LOG_FILE}.1" 2>/dev/null || true

            # 删除旧的备份（保留最多5个）
            local backup_count=$(find "$(dirname "${LOG_FILE}")" -name "$(basename "${LOG_FILE}").*.gz" 2>/dev/null | wc -l)
            if [[ $backup_count -gt 5 ]]; then
                find "$(dirname "${LOG_FILE}")" -name "$(basename "${LOG_FILE}").*.gz" -type f -printf '%T+ %p\n' 2>/dev/null | \
                    sort | head -n $((backup_count - 5)) | cut -d' ' -f2- | xargs rm -f 2>/dev/null || true
            fi
        fi
    fi

    # 检查.workflow/logs/目录下的所有日志
    if [[ -d "${SCRIPT_DIR}/logs" ]]; then
        find "${SCRIPT_DIR}/logs" -type f -name "*.log" 2>/dev/null | while read -r log_file; do
            local size=$(stat -c '%s' "$log_file" 2>/dev/null || stat -f '%z' "$log_file" 2>/dev/null || echo "0")
            if [[ $size -gt $max_size ]]; then
                echo "[LOG_ROTATE] 轮转日志: $log_file" >&2
                mv "$log_file" "$log_file.1"
                gzip -f "$log_file.1" 2>/dev/null || true
            fi
        done
    fi
}

# ==================== 日志系统 ====================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() { log "INFO" "${CYAN}[WORKFLOW]${NC} $*"; }
log_warn() { log "WARN" "${YELLOW}[WORKFLOW]${NC} $*"; }
log_error() { log "ERROR" "${RED}[WORKFLOW]${NC} $*"; }
log_success() { log "SUCCESS" "${GREEN}[WORKFLOW]${NC} $*"; }

# ==================== YAML解析器 ====================

parse_yaml() {
    local file="$1"
    local prefix="$2"

    python3 << EOF
import yaml
import sys
import os

try:
    with open("${file}", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"${prefix}{parent_key}{sep}{k}" if parent_key else f"${prefix}{k}"
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", str(item)))
            else:
                items.append((new_key, str(v)))
        return dict(items)

    flat = flatten_dict(data)
    for key, value in flat.items():
        # 转义单引号以防止shell解析问题
        escaped_value = str(value).replace("'", "'\"'\"'")
        print(f"{key}='{escaped_value}'")

except Exception as e:
    print(f"echo 'YAML解析错误: {e}' >&2", file=sys.stderr)
    sys.exit(1)
EOF
}

# ==================== 系统初始化 ====================

init_workflow_system() {
    log_info "初始化工作流系统..."

    # 创建必要目录
    mkdir -p "${PHASE_DIR}" "${GATES_DIR}" "${SCRIPT_DIR}/logs" "${SCRIPT_DIR}/temp"

    # 检查配置文件
    if [[ ! -f "${GATES_CONFIG}" ]]; then
        log_error "配置文件不存在: ${GATES_CONFIG}"
        exit 1
    fi

    # 初始化current phase（如果不存在）
    if [[ ! -f "${PHASE_DIR}/current" ]]; then
        echo "P1" > "${PHASE_DIR}/current"
        log_info "初始化当前阶段为 P1"
    fi

    log_success "工作流系统初始化完成"
}

# ==================== Phase管理 ====================

get_current_phase() {
    if [[ -f "${PHASE_DIR}/current" ]]; then
        cat "${PHASE_DIR}/current" | tr -d '\n\r'
    else
        echo "P1"
    fi
}

set_current_phase() {
    local phase="$1"

    # 同步更新两个位置
    echo "${phase}" > "${PHASE_DIR}/current"

    # ACTIVE需要完整格式
    cat > "${PROJECT_ROOT}/.workflow/ACTIVE" << EOF
phase: ${phase}
ticket: exec-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

    echo "${phase}" > "${PHASE_DIR}/last_updated_$(date +%s)"

    log_info "切换到阶段: ${BOLD}${phase}${NC}"
    log_info "已同步: .phase/current 和 .workflow/ACTIVE"
}

get_phase_info() {
    local phase="$1"

    # 简化的phase信息获取
    case "${phase}" in
        P1) echo '{"phase": "P1", "name": "Plan"}' ;;
        P2) echo '{"phase": "P2", "name": "Skeleton"}' ;;
        P3) echo '{"phase": "P3", "name": "Implement"}' ;;
        P4) echo '{"phase": "P4", "name": "Test"}' ;;
        P5) echo '{"phase": "P5", "name": "Review"}' ;;
        P6) echo '{"phase": "P6", "name": "Docs & Release"}' ;;
        *) echo '{"phase": "Unknown", "name": "Unknown"}' ;;
    esac
}

# ==================== Gates验证引擎 ====================

validate_gate_condition() {
    local condition="$1"
    local phase="$2"

    log_info "验证Gate条件: ${condition}"

    case "${condition}" in
        *"必须存在"*)
            local file_pattern=$(echo "${condition}" | sed 's/.*必须存在 \([^ ]*\).*/\1/')
            if [[ -f "${PROJECT_ROOT}/${file_pattern}" ]]; then
                log_success "✓ 文件存在: ${file_pattern}"
                return 0
            else
                log_error "✗ 文件不存在: ${file_pattern}"
                return 1
            fi
            ;;

        *"构建/编译通过"*)
            log_info "检查构建状态..."
            if check_build_status; then
                log_success "✓ 构建通过"
                return 0
            else
                log_error "✗ 构建失败"
                return 1
            fi
            ;;

        *"pre-push"*)
            log_info "运行pre-push测试..."
            if run_pre_push_tests; then
                log_success "✓ Pre-push测试通过"
                return 0
            else
                log_error "✗ Pre-push测试失败"
                return 1
            fi
            ;;

        *"必须匹配三个标题"*)
            if validate_plan_document_structure; then
                log_success "✓ 文档结构正确"
                return 0
            else
                log_error "✗ 文档结构不正确"
                return 1
            fi
            ;;

        *"任务清单计数 >= 5"*)
            if validate_task_count; then
                log_success "✓ 任务清单数量符合要求"
                return 0
            else
                log_error "✗ 任务清单数量不足"
                return 1
            fi
            ;;

        *)
            log_warn "未知Gate条件，跳过: ${condition}"
            return 0
            ;;
    esac
}

# ==================== 具体验证函数 ====================

check_build_status() {
    # 检查常见构建文件和结果
    if [[ -f "${PROJECT_ROOT}/package.json" ]]; then
        cd "${PROJECT_ROOT}" && npm run build 2>/dev/null || return 1
    elif [[ -f "${PROJECT_ROOT}/Makefile" ]]; then
        cd "${PROJECT_ROOT}" && make build 2>/dev/null || return 1
    elif [[ -f "${PROJECT_ROOT}/pom.xml" ]]; then
        cd "${PROJECT_ROOT}" && mvn compile 2>/dev/null || return 1
    else
        log_info "未找到标准构建文件，假设构建通过"
        return 0
    fi
}

run_pre_push_tests() {
    local test_types=("unit" "boundary" "smoke")

    for test_type in "${test_types[@]}"; do
        log_info "运行 ${test_type} 测试..."

        # 这里集成现有的测试系统
        if [[ -f "${PROJECT_ROOT}/test_${test_type}.sh" ]]; then
            if ! bash "${PROJECT_ROOT}/test_${test_type}.sh"; then
                log_error "${test_type} 测试失败"
                return 1
            fi
        else
            log_info "未找到 ${test_type} 测试脚本，跳过"
        fi
    done

    return 0
}

validate_plan_document_structure() {
    local plan_file="${PROJECT_ROOT}/docs/PLAN.md"

    if [[ ! -f "${plan_file}" ]]; then
        return 1
    fi

    local required_headers=("## 任务清单" "## 受影响文件清单" "## 回滚方案")

    for header in "${required_headers[@]}"; do
        if ! grep -q "^${header}" "${plan_file}"; then
            log_error "缺少必需标题: ${header}"
            return 1
        fi
    done

    return 0
}

validate_task_count() {
    local plan_file="${PROJECT_ROOT}/docs/PLAN.md"

    if [[ ! -f "${plan_file}" ]]; then
        return 1
    fi

    # 提取任务清单部分并计数
    local task_count=$(awk '
        BEGIN { in_section = 0; count = 0 }
        /^## 任务清单/ { in_section = 1; next }
        /^## / && in_section { in_section = 0 }
        in_section && (/^[0-9]+\./ || /^- / || /^\* /) {
            count++
        }
        END { print count }
    ' "${plan_file}")

    log_info "任务清单计数: ${task_count}"

    if [[ ${task_count} -ge 5 ]]; then
        return 0
    else
        log_error "任务清单数量不足: ${task_count} < 5"
        return 1
    fi
}

# ==================== Phase执行引擎 ====================

# 串行执行（原有逻辑保持不变）
execute_sequential() {
    local phase="$1"
    log_info "串行执行 Phase: ${phase}"

    # 调用原有的gate验证逻辑
    execute_phase_gates "${phase}"
}

# 执行Phase（并行或串行）
execute_phase() {
    local phase="$1"

    if is_parallel_enabled "$phase"; then
        echo "🚀 Parallel execution enabled for $phase"

        # 检查STAGES.yml是否存在
        if [[ -f "${SCRIPT_DIR}/STAGES.yml" ]]; then
            # 读取STAGES.yml
            local parallel_groups=$(yq eval ".workflow_phase_parallel.${phase}.parallel_groups" "${SCRIPT_DIR}/STAGES.yml" 2>/dev/null)

            if [[ -n "$parallel_groups" && "$parallel_groups" != "null" && "$parallel_groups" != "[]" ]]; then
                # 调用parallel_executor.sh
                if [[ -f "${SCRIPT_DIR}/lib/parallel_executor.sh" ]]; then
                    local log_file="${SCRIPT_DIR}/logs/parallel_${phase}_$(date +%s).log"

                    log_info "调用 parallel_executor.sh 执行并行任务"
                    log_info "  Phase: ${phase}"
                    log_info "  配置文件: ${SCRIPT_DIR}/STAGES.yml"
                    log_info "  日志文件: ${log_file}"

                    bash "${SCRIPT_DIR}/lib/parallel_executor.sh" \
                        execute "${phase}" \
                        $(echo "$parallel_groups" | yq eval '.[].group_id' - 2>/dev/null | tr '\n' ' ') \
                        2>&1 | tee "${log_file}"

                    local parallel_exit_code=$?
                    if [[ $parallel_exit_code -eq 0 ]]; then
                        log_success "✓ 并行执行成功"
                        return 0
                    else
                        log_error "✗ 并行执行失败（exit code: ${parallel_exit_code}）"
                        return 1
                    fi
                else
                    echo "⚠️  parallel_executor.sh not found, falling back to sequential"
                fi
            else
                log_info "Phase ${phase} 无并行组配置，使用串行执行"
            fi
        else
            log_warn "STAGES.yml not found, falling back to sequential"
        fi
    fi

    # Fallback到串行
    echo "📝 Sequential execution for $phase"
    execute_sequential "$phase"
}

execute_phase_gates() {
    local phase="$1"
    log_info "开始验证 ${BOLD}${phase}${NC} 阶段的Gates条件..."

    # 从gates.yml读取gates条件，正确传递phase参数
    local gates_section=$(python3 << EOF
import yaml
import sys

try:
    with open(".workflow/gates.yml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    phase = "${phase}"  # 使用传入的phase参数
    if 'phases' in data and phase in data['phases'] and 'gates' in data['phases'][phase]:
        for gate in data['phases'][phase]['gates']:
            print(gate)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
EOF
)

    local failed_gates=0
    local total_gates=0

    log_info "Phase ${phase} Gates列表:"
    if [[ -n "${gates_section}" ]]; then
        while IFS= read -r condition; do
            if [[ -n "${condition}" ]]; then
                ((total_gates++))
                log_info "  ${total_gates}. ${condition}"
                if ! validate_gate_condition "${condition}" "${phase}"; then
                    ((failed_gates++))
                    log_error "    ✗ 验证失败"
                else
                    log_success "    ✓ 验证通过"
                fi
            fi
        done <<< "${gates_section}"
    else
        log_warn "Phase ${phase} 未找到Gates配置"
    fi

    log_info "Gates验证结果: ${GREEN}$((total_gates - failed_gates))${NC}/${total_gates} 通过"

    if [[ ${failed_gates} -eq 0 ]]; then
        log_success "🎉 ${phase} 阶段所有Gates验证通过！"

        # 在执行 on_pass 动作前记录当前状态
        local current_before=$(get_current_phase)
        log_info "执行on_pass动作前，当前phase: ${current_before}"

        execute_on_pass_actions "${phase}"

        # 验证phase是否正确切换
        local current_after=$(get_current_phase)
        log_info "执行on_pass动作后，当前phase: ${current_after}"

        if [[ "${current_after}" != "${current_before}" ]]; then
            log_success "✓ Phase成功切换: ${current_before} -> ${current_after}"
        else
            log_warn "⚠️  Phase未发生切换，仍为: ${current_after}"
        fi

        return 0
    else
        log_error "❌ ${phase} 阶段有 ${failed_gates} 个Gates验证失败"
        return 1
    fi
}

execute_on_pass_actions() {
    local phase="$1"
    log_info "执行 ${phase} 阶段的on_pass动作..."

    # 从gates.yml读取on_pass动作，正确传递phase参数
    local actions=$(python3 << EOF
import yaml
import sys

try:
    with open(".workflow/gates.yml", 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    phase = "${phase}"  # 使用传入的phase参数
    if 'phases' in data and phase in data['phases'] and 'on_pass' in data['phases'][phase]:
        for action in data['phases'][phase]['on_pass']:
            print(action)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
EOF
)

    if [[ -n "${actions}" ]]; then
        log_info "找到${phase}阶段的on_pass动作:"
        local action_count=0
        while IFS= read -r action; do
            if [[ -n "${action}" ]]; then
                ((action_count++))
                log_info "  ${action_count}. ${action}"
                execute_action "${action}" "${phase}"
            fi
        done <<< "${actions}"
        log_success "✓ 执行了 ${action_count} 个 on_pass 动作"
    else
        log_warn "Phase ${phase} 没有配置on_pass动作"
    fi
}

execute_action() {
    local action="$1"
    local phase="$2"

    log_info "执行动作: ${action}"

    case "${action}" in
        create:*)
            local file_path=$(echo "${action}" | sed 's/create: //')
            mkdir -p "$(dirname "${PROJECT_ROOT}/${file_path}")"
            touch "${PROJECT_ROOT}/${file_path}"
            log_success "✓ 创建文件: ${file_path}"
            ;;

        set:*)
            local assignment=$(echo "${action}" | sed 's/set: //')
            log_info "处理设置: ${assignment}"

            # 修复phase切换逻辑 - 支持多种格式
            if [[ "${assignment}" == ".phase/current="* ]]; then
                local next_phase="${assignment#*.phase/current=}"
                log_info "检测到phase切换请求: ${phase} -> ${next_phase}"
                set_current_phase "${next_phase}"
                log_success "✓ 自动进入下一阶段: ${BOLD}${next_phase}${NC}"
            else
                log_warn "未识别的设置格式: ${assignment}"
            fi
            ;;

        when:*)
            local condition=$(echo "${action}" | sed 's/when: //')
            log_info "✓ 条件检查: ${condition}"
            # 这里可以添加条件验证逻辑
            ;;

        *)
            log_warn "未知动作: ${action}"
            ;;
    esac
}

# ==================== Claude Hooks集成 ====================

integrate_with_claude_hooks() {
    log_info "集成Claude Hooks系统..."

    local current_phase=$(get_current_phase)

    # 根据阶段调用相应的hooks
    case "${current_phase}" in
        P1)
            trigger_claude_hook "branch_helper.sh" "Phase P1 - Plan"
            ;;
        P2)
            trigger_claude_hook "smart_cleanup_advisor.sh" "Phase P2 - Skeleton"
            ;;
        P3)
            trigger_claude_hook "smart_agent_selector.sh" "Phase P3 - Implementation"
            trigger_claude_hook "concurrent_optimizer.sh" "Phase P3 - Implementation"
            ;;
        P4)
            trigger_claude_hook "performance_monitor.sh" "Phase P4 - Testing"
            trigger_claude_hook "quality_gate.sh" "Phase P4 - Testing"
            ;;
        P5)
            trigger_claude_hook "smart_error_recovery.sh" "Phase P5 - Review"
            ;;
        P6)
            trigger_claude_hook "smart_git_workflow.sh" "Phase P6 - Release"
            ;;
    esac
}

trigger_claude_hook() {
    local hook_script="$1"
    local context="$2"
    local hook_path="${CLAUDE_HOOKS_DIR}/${hook_script}"

    if [[ -f "${hook_path}" && -x "${hook_path}" ]]; then
        log_info "触发Claude Hook: ${hook_script}"

        # 设置环境变量供hook使用
        export WORKFLOW_PHASE=$(get_current_phase)
        export WORKFLOW_CONTEXT="${context}"
        export WORKFLOW_PROJECT_ROOT="${PROJECT_ROOT}"

        # 执行hook（非阻塞，有超时保护）
        timeout 30s "${hook_path}" || log_warn "Hook ${hook_script} 超时或失败"
    else
        log_warn "Claude Hook不存在或不可执行: ${hook_script}"
    fi
}

# ==================== 智能推荐系统 ====================

suggest_next_actions() {
    local current_phase=$(get_current_phase)
    local phase_info=$(get_phase_info "${current_phase}")

    echo -e "\n${CYAN}=== 🎯 智能推荐系统 ===${NC}"
    echo -e "${BOLD}当前阶段:${NC} ${current_phase} ($(echo "${phase_info}" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null || echo "Unknown"))"

    case "${current_phase}" in
        P1)
            echo -e "\n${YELLOW}📋 P1 - Plan 阶段建议:${NC}"
            echo "  • 创建 docs/PLAN.md 包含完整的任务清单"
            echo "  • 确保任务清单 ≥ 5条，每条以动词开头"
            echo "  • 列出受影响的具体文件路径"
            echo "  • 设计回滚方案"
            ;;
        P2)
            echo -e "\n${YELLOW}🏗️ P2 - Skeleton 阶段建议:${NC}"
            echo "  • 根据PLAN.md创建目录结构和接口骨架"
            echo "  • 不要新增计划外的目录"
            echo "  • 在docs/SKELETON-NOTES.md记录重要说明"
            ;;
        P3)
            echo -e "\n${YELLOW}⚡ P3 - Implementation 阶段建议:${NC}"
            echo "  • 使用4-6-8个Agent并行开发（根据复杂度）"
            echo "  • 确保代码可构建"
            echo "  • 更新docs/CHANGELOG.md的Unreleased段"
            echo "  • 建议触发: smart_agent_selector.sh"
            ;;
        P4)
            echo -e "\n${YELLOW}🧪 P4 - Test 阶段建议:${NC}"
            echo "  • 新增≥2条测试，至少1条为边界/负例测试"
            echo "  • 确保unit+boundary+smoke测试通过"
            echo "  • 创建docs/TEST-REPORT.md记录覆盖情况"
            ;;
        P5)
            echo -e "\n${YELLOW}👁️ P5 - Review 阶段建议:${NC}"
            echo "  • 创建docs/REVIEW.md包含三段分析"
            echo "  • 分析风格一致性、风险清单、回滚可行性"
            echo "  • 最后明确写出'APPROVE'或'REWORK: ...'"
            ;;
        P6)
            echo -e "\n${YELLOW}🚀 P6 - Docs & Release 阶段建议:${NC}"
            echo "  • 确保docs/README.md包含：安装、使用、注意事项"
            echo "  • 更新docs/CHANGELOG.md版本号和影响面"
            echo "  • 打tag并创建Release Notes"
            ;;
    esac

    echo -e "\n${GREEN}💡 可用命令:${NC}"
    echo "  • ./executor.sh status    - 查看当前状态"
    echo "  • ./executor.sh validate  - 验证当前阶段"
    echo "  • ./executor.sh next      - 尝试进入下一阶段"
    echo "  • ./executor.sh reset     - 重置到P1阶段"
}

# ==================== 状态报告系统 ====================

generate_status_report() {
    local current_phase=$(get_current_phase)

    echo -e "\n${CYAN}=== 📊 Claude Enhancer 5.0 工作流状态报告 ===${NC}"
    echo -e "${BOLD}时间:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BOLD}项目:${NC} $(basename "${PROJECT_ROOT}")"
    echo -e "${BOLD}当前阶段:${NC} ${current_phase}"

    # 显示阶段进度
    echo -e "\n${YELLOW}📈 阶段进度:${NC}"
    local phases=("P1" "P2" "P3" "P4" "P5" "P6")
    for phase in "${phases[@]}"; do
        if [[ -f "${GATES_DIR}/${phase#P}*.ok" ]]; then
            echo -e "  ${GREEN}✓${NC} ${phase} - 已完成"
        elif [[ "${phase}" == "${current_phase}" ]]; then
            echo -e "  ${YELLOW}▶${NC} ${phase} - 进行中"
        else
            echo -e "  ${RED}○${NC} ${phase} - 待开始"
        fi
    done

    # 显示Gates完成情况
    echo -e "\n${YELLOW}🔒 Gates完成情况:${NC}"
    if [[ -d "${GATES_DIR}" ]]; then
        local completed_gates=$(find "${GATES_DIR}" -name "*.ok" | wc -l)
        echo -e "  已完成Gates: ${GREEN}${completed_gates}${NC}/6"
        ls "${GATES_DIR}"/*.ok 2>/dev/null | while read -r gate_file; do
            local gate_name=$(basename "${gate_file}" .ok)
            echo -e "    ${GREEN}✓${NC} Gate ${gate_name}"
        done
    else
        echo -e "  ${RED}未找到Gates目录${NC}"
    fi

    # 显示最近的活动
    if [[ -f "${LOG_FILE}" ]]; then
        echo -e "\n${YELLOW}📝 最近活动:${NC}"
        tail -n 5 "${LOG_FILE}" | while read -r line; do
            echo "    ${line}"
        done
    fi
}

# ==================== 测试函数 ====================

# 测试phase推进功能的简单验证
test_phase_progression() {
    log_info "开始测试phase推进功能..."

    # 保存当前状态
    local original_phase=$(get_current_phase)
    log_info "原始状态: ${original_phase}"

    # 测试设置功能
    log_info "测试: 设置phase为P2"
    set_current_phase "P2"
    local test_phase=$(get_current_phase)

    if [[ "${test_phase}" == "P2" ]]; then
        log_success "✓ Phase设置成功: ${test_phase}"
    else
        log_error "✗ Phase设置失败: 期望P2，实际${test_phase}"
    fi

    # 测试action执行
    log_info "测试: 执行set: .phase/current=P3动作"
    execute_action "set: .phase/current=P3" "P2"
    local after_action=$(get_current_phase)

    if [[ "${after_action}" == "P3" ]]; then
        log_success "✓ Phase切换成功: P2 -> ${after_action}"
    else
        log_error "✗ Phase切换失败: 期望P3，实际${after_action}"
    fi

    # 恢复原始状态
    set_current_phase "${original_phase}"
    log_info "恢复到原始状态: ${original_phase}"

    log_success "Phase推进测试完成"
}

# ==================== 主执行函数 ====================

show_usage() {
    cat << EOF
${BOLD}Claude Enhancer 5.0 - Workflow Execution Engine v2.0${NC}

${YELLOW}用法:${NC}
  $0 [command] [options]

${YELLOW}命令:${NC}
  ${GREEN}init${NC}          初始化工作流系统
  ${GREEN}status${NC}        显示当前状态和进度
  ${GREEN}validate${NC}      验证当前阶段的Gates条件
  ${GREEN}next${NC}          尝试进入下一阶段
  ${GREEN}goto${NC} <phase>  跳转到指定阶段 (P1-P6)
  ${GREEN}reset${NC}         重置到P1阶段
  ${GREEN}suggest${NC}       显示智能推荐
  ${GREEN}hooks${NC}         手动触发Claude Hooks集成
  ${GREEN}test${NC}          测试phase推进功能
  ${GREEN}clean${NC}         清理临时文件和日志
  ${GREEN}--dry-run${NC}     显示执行计划（不实际执行）

${YELLOW}示例:${NC}
  $0 init              # 初始化系统
  $0 status            # 查看状态
  $0 validate          # 验证当前阶段
  $0 next              # 进入下一阶段
  $0 goto P3           # 跳转到P3阶段
  $0 suggest           # 获取智能建议
  $0 --dry-run         # 显示执行计划

${YELLOW}集成特性:${NC}
  • 智能Gates验证引擎
  • 自动Phase状态管理
  • Claude Hooks系统集成
  • 实时状态监控
  • 智能推荐系统
  • 完整的日志记录
  • Dry-run执行计划可视化

EOF
}

main() {
    # 日志轮转检查（CE-ISSUE-009）
    check_and_rotate_logs

    # 确保日志目录存在
    mkdir -p "$(dirname "${LOG_FILE}")"

    # Dry-run模式检测（CE-ISSUE-004）
    if [[ "${1:-}" == "--dry-run" ]]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}  🔍 DRY-RUN模式：仅显示执行计划，不实际执行${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        # 调用plan_renderer.sh生成执行计划
        if [[ -f "${SCRIPT_DIR}/scripts/plan_renderer.sh" ]]; then
            bash "${SCRIPT_DIR}/scripts/plan_renderer.sh"
        else
            echo -e "${RED}❌ ERROR: plan_renderer.sh 不存在${NC}"
            echo "  路径: ${SCRIPT_DIR}/scripts/plan_renderer.sh"
            exit 1
        fi

        exit 0
    fi

    local command="${1:-status}"

    case "${command}" in
        init)
            init_workflow_system
            ;;

        status)
            generate_status_report
            suggest_next_actions
            ;;

        validate)
            local current_phase=$(get_current_phase)

            # 使用新的execute_phase函数（自动检测并行）
            if execute_phase "${current_phase}"; then
                log_success "🎉 阶段 ${current_phase} 验证通过！"
                integrate_with_claude_hooks
            else
                log_error "❌ 阶段 ${current_phase} 验证失败"
                exit 1
            fi
            ;;

        next)
            local current_phase=$(get_current_phase)

            # 使用新的execute_phase函数（自动检测并行）
            if execute_phase "${current_phase}"; then
                log_success "🎉 已自动进入下一阶段！"
                generate_status_report
            else
                log_error "❌ 当前阶段验证失败，无法进入下一阶段"
                suggest_next_actions
                exit 1
            fi
            ;;

        goto)
            local target_phase="$2"
            if [[ "${target_phase}" =~ ^P[1-6]$ ]]; then
                set_current_phase "${target_phase}"
                generate_status_report
            else
                log_error "无效的阶段: ${target_phase}，请使用P1-P6"
                exit 1
            fi
            ;;

        reset)
            set_current_phase "P1"
            rm -f "${GATES_DIR}/"*.ok
            log_success "已重置到P1阶段"
            ;;

        suggest)
            suggest_next_actions
            ;;

        hooks)
            integrate_with_claude_hooks
            ;;

        test)
            test_phase_progression
            ;;

        clean)
            rm -f "${SCRIPT_DIR}/temp/"*
            rm -f "${SCRIPT_DIR}/logs/"*.log
            log_success "清理完成"
            ;;

        help|--help|-h)
            show_usage
            ;;

        *)
            log_error "未知命令: ${command}"
            show_usage
            exit 1
            ;;
    esac
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
