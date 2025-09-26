#!/bin/bash

# Gate Validator v5.0 — Claude Enhancer 5.0 完整验证系统
# 功能：根据当前phase检查必须产出文件、验证路径白名单、检查并行限制
# 版本：5.0.0 | 更新：2025-09-26

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GATES_CONFIG="$SCRIPT_DIR/gates.yml"
PHASE_FILE="$PROJECT_ROOT/.phase/current"
GATES_DIR="$PROJECT_ROOT/.gates"
LOGS_DIR="$PROJECT_ROOT/.workflow/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_debug() { [[ "${DEBUG:-0}" == "1" ]] && echo -e "${PURPLE}[DEBUG]${NC} $*" >&2 || true; }

# 确保必要目录存在
ensure_directories() {
    mkdir -p "$LOGS_DIR" "$GATES_DIR" "$(dirname "$PHASE_FILE")"
}

# 获取当前phase
get_current_phase() {
    if [[ -f "$PHASE_FILE" ]]; then
        cat "$PHASE_FILE" 2>/dev/null || echo "P1"
    else
        echo "P1"
    fi
}

# 解析YAML配置 (简化版)
parse_yaml_value() {
    local key="$1"
    local yaml_file="$2"

    if [[ -f "$yaml_file" ]]; then
        grep -E "^\s*${key}:" "$yaml_file" | sed 's/.*: *//' | tr -d '"' || echo ""
    fi
}

parse_yaml_array() {
    local key="$1"
    local yaml_file="$2"

    if [[ -f "$yaml_file" ]]; then
        awk -v key="$key" '
        BEGIN { in_array = 0; in_phase = 0 }
        /^[a-zA-Z]/ { in_phase = 0 }
        $0 ~ "^  " key ":" { in_phase = 1; next }
        in_phase && /^    allow_paths:/ { in_array = 1; next }
        in_array && /^    [a-zA-Z]/ { in_array = 0 }
        in_array && /^      - / {
            gsub(/^      - "/, "");
            gsub(/"$/, "");
            print
        }
        ' "$yaml_file"
    fi
}

parse_yaml_must_produce() {
    local phase="$1"
    local yaml_file="$2"

    if [[ -f "$yaml_file" ]]; then
        awk -v phase="$phase" '
        BEGIN { in_phase = 0; in_must_produce = 0 }
        $0 ~ "^  " phase ":" { in_phase = 1; next }
        /^  [A-Z]/ && in_phase { in_phase = 0; in_must_produce = 0 }
        in_phase && /^    must_produce:/ { in_must_produce = 1; next }
        in_must_produce && /^    [a-zA-Z]/ { in_must_produce = 0 }
        in_must_produce && /^      - / {
            gsub(/^      - "/, "");
            gsub(/"$/, "");
            print
        }
        ' "$yaml_file"
    fi
}

parse_yaml_gates() {
    local phase="$1"
    local yaml_file="$2"

    if [[ -f "$yaml_file" ]]; then
        awk -v phase="$phase" '
        BEGIN { in_phase = 0; in_gates = 0 }
        $0 ~ "^  " phase ":" { in_phase = 1; next }
        /^  [A-Z]/ && in_phase { in_phase = 0; in_gates = 0 }
        in_phase && /^    gates:/ { in_gates = 1; next }
        in_gates && /^    [a-zA-Z]/ { in_gates = 0 }
        in_gates && /^      - / {
            gsub(/^      - "/, "");
            gsub(/"$/, "");
            print
        }
        ' "$yaml_file"
    fi
}

# 获取并行限制
get_parallel_limit() {
    local phase="$1"

    if [[ -f "$GATES_CONFIG" ]]; then
        grep -A 10 "parallel_limits:" "$GATES_CONFIG" | grep "  $phase:" | awk '{print $2}' || echo "4"
    else
        echo "4"
    fi
}

# 验证路径白名单
validate_path_whitelist() {
    local phase="$1"
    local violations=()

    log_info "验证路径白名单 (Phase $phase)..."

    # 获取允许的路径模式
    local allowed_paths
    mapfile -t allowed_paths < <(parse_yaml_array "$phase" "$GATES_CONFIG")

    if [[ ${#allowed_paths[@]} -eq 0 ]]; then
        log_warn "未找到Phase $phase的路径白名单配置"
        return 0
    fi

    log_debug "允许的路径模式: ${allowed_paths[*]}"

    # 检查git变更的文件
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local changed_files
        mapfile -t changed_files < <(git diff --name-only HEAD 2>/dev/null || true)

        for file in "${changed_files[@]}"; do
            [[ -z "$file" ]] && continue

            local allowed=false
            for pattern in "${allowed_paths[@]}"; do
                # 简单的glob匹配
                if [[ "$file" == $pattern || "$file" == ${pattern%/\*\*}/* ]]; then
                    allowed=true
                    break
                fi
            done

            if [[ "$allowed" == false ]]; then
                violations+=("$file")
            fi
        done
    fi

    if [[ ${#violations[@]} -gt 0 ]]; then
        log_error "路径白名单违规："
        printf '%s\n' "${violations[@]}" | sed 's/^/  - /'
        return 1
    else
        log_success "路径白名单验证通过"
        return 0
    fi
}

# 检查必须产出的文件
validate_must_produce() {
    local phase="$1"
    local failures=()

    log_info "检查必须产出文件 (Phase $phase)..."

    # 获取必须产出的要求
    local must_produce_items
    mapfile -t must_produce_items < <(parse_yaml_must_produce "$phase" "$GATES_CONFIG")

    if [[ ${#must_produce_items[@]} -eq 0 ]]; then
        log_warn "未找到Phase $phase的必须产出配置"
        return 0
    fi

    for item in "${must_produce_items[@]}"; do
        [[ -z "$item" ]] && continue

        log_debug "检查要求: $item"

        # 解析不同类型的要求
        if [[ "$item" =~ ^([^:]+):(.*) ]]; then
            # 文件存在性检查 (格式: "filename: description")
            local file_path="${BASH_REMATCH[1]// /}"
            local description="${BASH_REMATCH[2]}"

            if [[ ! -f "$PROJECT_ROOT/$file_path" ]]; then
                failures+=("缺少文件: $file_path ($description)")
            else
                log_debug "文件存在: $file_path"

                # 检查文件内容要求
                if [[ "$description" =~ "包含三级标题" ]]; then
                    if ! grep -q "^## " "$PROJECT_ROOT/$file_path"; then
                        failures+=("$file_path 缺少三级标题")
                    fi
                fi

                if [[ "$description" =~ "三段：" ]]; then
                    local section_count
                    section_count=$(grep -c "^## " "$PROJECT_ROOT/$file_path" 2>/dev/null || echo "0")
                    if [[ "$section_count" -lt 3 ]]; then
                        failures+=("$file_path 缺少必需的三个段落")
                    fi
                fi
            fi
        elif [[ "$item" =~ "任务清单≥([0-9]+)条" ]]; then
            # 任务清单数量检查
            local min_count="${BASH_REMATCH[1]}"
            if [[ -f "$PROJECT_ROOT/docs/PLAN.md" ]]; then
                local task_count
                task_count=$(grep -c "^- " "$PROJECT_ROOT/docs/PLAN.md" 2>/dev/null || echo "0")
                if [[ "$task_count" -lt "$min_count" ]]; then
                    failures+=("任务清单少于 $min_count 条 (当前: $task_count)")
                fi
            fi
        elif [[ "$item" =~ "新增.*测试.*≥.*([0-9]+)" ]]; then
            # 测试数量检查
            local min_tests="${BASH_REMATCH[1]}"
            if [[ -d "$PROJECT_ROOT/tests" ]]; then
                local test_count
                test_count=$(find "$PROJECT_ROOT/tests" -name "*.test.*" -o -name "*_test.*" | wc -l)
                if [[ "$test_count" -lt "$min_tests" ]]; then
                    failures+=("测试数量少于 $min_tests 个 (当前: $test_count)")
                fi
            else
                failures+=("缺少tests目录")
            fi
        else
            # 通用描述性要求
            log_debug "通用要求: $item"
        fi
    done

    if [[ ${#failures[@]} -gt 0 ]]; then
        log_error "必须产出验证失败："
        printf '%s\n' "${failures[@]}" | sed 's/^/  - /'
        return 1
    else
        log_success "必须产出验证通过"
        return 0
    fi
}

# 验证gates条件
validate_gates() {
    local phase="$1"
    local failures=()

    log_info "验证gates条件 (Phase $phase)..."

    # 获取gates条件
    local gate_conditions
    mapfile -t gate_conditions < <(parse_yaml_gates "$phase" "$GATES_CONFIG")

    if [[ ${#gate_conditions[@]} -eq 0 ]]; then
        log_warn "未找到Phase $phase的gates配置"
        return 0
    fi

    for condition in "${gate_conditions[@]}"; do
        [[ -z "$condition" ]] && continue

        log_debug "检查条件: $condition"

        case "$condition" in
            "必须存在 "*|"必须匹配 "*)
                local file_pattern="${condition#必须存在 }"
                file_pattern="${file_pattern#必须匹配 }"
                if [[ ! -f "$PROJECT_ROOT/$file_pattern" ]]; then
                    failures+=("条件失败: $condition")
                fi
                ;;
            "构建/编译通过")
                if command -v npm >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/package.json" ]]; then
                    if ! npm run build >/dev/null 2>&1; then
                        failures+=("构建失败")
                    fi
                elif command -v make >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/Makefile" ]]; then
                    if ! make build >/dev/null 2>&1; then
                        failures+=("构建失败")
                    fi
                fi
                ;;
            "pre-push: "*)
                local test_types="${condition#pre-push: }"
                log_debug "检查测试类型: $test_types"
                # 简化的测试检查
                if [[ -f "$PROJECT_ROOT/package.json" ]]; then
                    if ! npm test >/dev/null 2>&1; then
                        failures+=("测试失败: $test_types")
                    fi
                fi
                ;;
            *)
                log_debug "未识别的条件: $condition"
                ;;
        esac
    done

    if [[ ${#failures[@]} -gt 0 ]]; then
        log_error "Gates条件验证失败："
        printf '%s\n' "${failures[@]}" | sed 's/^/  - /'
        return 1
    else
        log_success "Gates条件验证通过"
        return 0
    fi
}

# 检查并行限制
validate_parallel_limits() {
    local phase="$1"
    local agent_count="${2:-0}"

    log_info "检查并行限制 (Phase $phase)..."

    local limit
    limit=$(get_parallel_limit "$phase")

    if [[ "$agent_count" -gt "$limit" ]]; then
        log_error "并行限制超出: 使用了 $agent_count 个agent，但Phase $phase 限制为 $limit"
        return 1
    else
        log_success "并行限制验证通过: $agent_count/$limit agents"
        return 0
    fi
}

# 创建gate通过标记
mark_gate_passed() {
    local phase="$1"
    local gate_file="$GATES_DIR/${phase#P}.ok"

    echo "$(date -Iseconds)" > "$gate_file"
    log_success "Gate通过标记已创建: $gate_file"
}

# 生成验证报告
generate_report() {
    local phase="$1"
    local status="$2"
    local details="$3"
    local timestamp
    timestamp=$(date -Iseconds)

    local report_file="$LOGS_DIR/gate_validation_${phase}_${timestamp}.log"

    cat > "$report_file" <<EOF
# Gate Validation Report
Phase: $phase
Status: $status
Timestamp: $timestamp

## Validation Details
$details

## Environment
Project Root: $PROJECT_ROOT
Git Status: $(git status --porcelain 2>/dev/null | wc -l) files changed
Current Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || "unknown")

## Configuration
Parallel Limit: $(get_parallel_limit "$phase")
Gates Config: $GATES_CONFIG
EOF

    log_info "验证报告已生成: $report_file"
}

# 主验证函数
validate_gate() {
    local phase="${1:-}"
    local agent_count="${2:-0}"
    local verbose="${3:-0}"

    if [[ "$verbose" == "1" ]]; then
        export DEBUG=1
    fi

    # 如果没有指定phase，自动获取当前phase
    if [[ -z "$phase" ]]; then
        phase=$(get_current_phase)
        log_info "自动检测到当前Phase: $phase"
    fi

    log_info "开始验证 Phase $phase (使用 $agent_count agents)..."

    local validation_results=()
    local overall_status="PASS"

    # 验证路径白名单
    if validate_path_whitelist "$phase"; then
        validation_results+=("✓ 路径白名单验证通过")
    else
        validation_results+=("✗ 路径白名单验证失败")
        overall_status="FAIL"
    fi

    # 验证必须产出
    if validate_must_produce "$phase"; then
        validation_results+=("✓ 必须产出验证通过")
    else
        validation_results+=("✗ 必须产出验证失败")
        overall_status="FAIL"
    fi

    # 验证gates条件
    if validate_gates "$phase"; then
        validation_results+=("✓ Gates条件验证通过")
    else
        validation_results+=("✗ Gates条件验证失败")
        overall_status="FAIL"
    fi

    # 验证并行限制
    if validate_parallel_limits "$phase" "$agent_count"; then
        validation_results+=("✓ 并行限制验证通过")
    else
        validation_results+=("✗ 并行限制验证失败")
        overall_status="FAIL"
    fi

    # 生成报告
    local details
    details=$(printf '%s\n' "${validation_results[@]}")
    generate_report "$phase" "$overall_status" "$details"

    # 输出最终结果
    echo
    if [[ "$overall_status" == "PASS" ]]; then
        log_success "Gate验证通过 (Phase $phase)"
        mark_gate_passed "$phase"
        return 0
    else
        log_error "Gate验证失败 (Phase $phase)"
        echo "验证结果："
        printf '%s\n' "${validation_results[@]}" | sed 's/^/  /'
        return 1
    fi
}

# 显示帮助信息
show_help() {
    cat <<EOF
Gate Validator v5.0 - Claude Enhancer 5.0 完整验证系统

用法: $0 [选项] [phase] [agent_count]

参数:
  phase         要验证的Phase (P1-P6)，默认自动检测当前Phase
  agent_count   使用的Agent数量，用于并行限制检查，默认为0

选项:
  -h, --help    显示帮助信息
  -v, --verbose 详细输出模式
  --current     显示当前Phase
  --status      显示所有Phase的状态

示例:
  $0                    # 验证当前Phase
  $0 P3 6              # 验证P3阶段，使用6个agents
  $0 -v P2             # 详细模式验证P2阶段
  $0 --current         # 显示当前Phase
  $0 --status          # 显示所有Phase状态

验证内容:
  ✓ 路径白名单 - 确保只修改允许的文件和目录
  ✓ 必须产出 - 验证Phase要求的文件和内容存在
  ✓ Gates条件 - 检查构建、测试等条件
  ✓ 并行限制 - 确保Agent数量不超过Phase限制

配置文件: $GATES_CONFIG
EOF
}

# 显示当前Phase
show_current_phase() {
    local current_phase
    current_phase=$(get_current_phase)
    echo "Current Phase: $current_phase"
}

# 显示所有Phase状态
show_status() {
    echo "Phase Status Overview:"
    echo "======================"

    for phase in P1 P2 P3 P4 P5 P6; do
        local gate_file="$GATES_DIR/${phase#P}.ok"
        local status="⏳ PENDING"
        local timestamp=""

        if [[ -f "$gate_file" ]]; then
            status="✅ PASSED"
            timestamp=" ($(cat "$gate_file" 2>/dev/null))"
        fi

        local limit
        limit=$(get_parallel_limit "$phase")

        printf "%-6s %s (limit: %s agents)%s\n" "$phase" "$status" "$limit" "$timestamp"
    done

    echo
    echo "Current Phase: $(get_current_phase)"
}

# 主函数
main() {
    ensure_directories

    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        --current)
            show_current_phase
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        -v|--verbose)
            validate_gate "${2:-}" "${3:-0}" "1"
            ;;
        *)
            validate_gate "${1:-}" "${2:-0}" "0"
            ;;
    esac
}

# 如果是直接执行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi