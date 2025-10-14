#!/bin/bash
# Claude Enhancer v2.0 - Enhanced Workflow Enforcer
# 5层检测机制，修复"继续"关键词绕过漏洞
# Version: 2.0.0
# Author: Backend Architect + Security Auditor

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly WORKFLOW_DIR="${PROJECT_ROOT}/.workflow"
readonly LOG_DIR="${PROJECT_ROOT}/.claude/logs"

# 创建必要目录
mkdir -p "${LOG_DIR}"

# 日志配置
readonly ENFORCER_LOG="${LOG_DIR}/enforcer_v2.log"
readonly DEBUG_MODE="${DEBUG_ENFORCER:-0}"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ============================================================
# 日志函数
# ============================================================
log_debug() {
    if [[ "${DEBUG_MODE}" == "1" ]]; then
        echo "[DEBUG] $*" | tee -a "${ENFORCER_LOG}" >&2
    fi
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${ENFORCER_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${ENFORCER_LOG}" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${ENFORCER_LOG}" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "${ENFORCER_LOG}" >&2
}

log_block() {
    echo -e "${RED}[✗ BLOCKED]${NC} $*" | tee -a "${ENFORCER_LOG}" >&2
}

# ============================================================
# 层1: Phase检测（Phase Detection Layer）
# ============================================================
# 目的: 防止跳过Phase或在错误的Phase执行操作
# 检测: Phase跳过关键词、Phase状态一致性
# ============================================================
detect_phase_violation() {
    local input="$1"
    local current_phase=""
    local violations=0

    log_debug "Layer 1: Phase Detection - Start"

    # 读取当前Phase
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        current_phase=$(cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]')
        log_debug "Current phase: ${current_phase}"
    else
        log_warn "Phase状态文件不存在: ${WORKFLOW_DIR}/current"
        return 0  # 如果没有Phase文件，跳过此检查（讨论模式）
    fi

    # 定义Phase列表
    local phases=("P0" "P1" "P2" "P3" "P4" "P5" "P6" "P7")

    # 检测跳过关键词
    local skip_keywords=(
        "跳过"
        "skip"
        "bypass"
        "ignore"
        "省略"
        "忽略"
    )

    for keyword in "${skip_keywords[@]}"; do
        for phase in "${phases[@]}"; do
            # 检查是否提到跳过某个Phase
            if echo "$input" | grep -iqE "${keyword}[[:space:]]*${phase}"; then
                log_block "检测到尝试跳过Phase: ${keyword} ${phase}"
                log_error "  输入片段: $(echo "$input" | grep -iE "${keyword}[[:space:]]*${phase}" | head -1)"
                ((violations++))
            fi
        done
    done

    # 检测直接跳到后续Phase的企图
    if [[ -n "$current_phase" ]]; then
        local current_phase_num="${current_phase#P}"
        for phase in "${phases[@]}"; do
            local phase_num="${phase#P}"

            # 如果提到未来的Phase，检查是否合理
            if [[ $phase_num -gt $((current_phase_num + 1)) ]]; then
                if echo "$input" | grep -iqE "直接.*${phase}|directly.*${phase}"; then
                    log_block "检测到尝试跳过中间Phase，直接到 ${phase}"
                    log_error "  当前Phase: ${current_phase}"
                    log_error "  目标Phase: ${phase}"
                    log_error "  跳过了: P$((current_phase_num + 1)) 到 P$((phase_num - 1))"
                    ((violations++))
                fi
            fi
        done
    fi

    log_debug "Layer 1: Phase Detection - Found ${violations} violations"
    return $violations
}

# ============================================================
# 层2: 分支检测（Branch Detection Layer）
# ============================================================
# 目的: 防止在保护分支（main/master）上直接编码
# 检测: 当前分支状态、编码关键词
# ============================================================
detect_branch_violation() {
    local input="$1"
    local current_branch
    local violations=0

    log_debug "Layer 2: Branch Detection - Start"

    # 获取当前分支
    if git rev-parse --git-dir > /dev/null 2>&1; then
        current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        log_debug "Current branch: ${current_branch}"
    else
        log_debug "Not a git repository, skipping branch detection"
        return 0
    fi

    # 检查是否在保护分支
    if [[ "$current_branch" =~ ^(main|master|production|release)$ ]]; then
        log_debug "On protected branch: ${current_branch}"

        # 定义编码操作关键词
        local coding_keywords=(
            "编码"
            "写代码"
            "实现"
            "implement"
            "code"
            "develop"
            "写.*function"
            "创建.*class"
            "修改.*文件"
            "create.*file"
            "modify.*code"
            "add.*feature"
            "写入.*文件"
            "更新.*代码"
        )

        for keyword in "${coding_keywords[@]}"; do
            if echo "$input" | grep -iqE "${keyword}"; then
                log_block "在保护分支 ${current_branch} 上检测到编码操作"
                log_error "  关键词: ${keyword}"
                log_error "  输入片段: $(echo "$input" | grep -iE "${keyword}" | head -1)"
                log_warn "  建议: 请创建新分支"
                log_warn "    git checkout -b feature/your-feature-name"
                ((violations++))
                break  # 只报告一次
            fi
        done
    fi

    log_debug "Layer 2: Branch Detection - Found ${violations} violations"
    return $violations
}

# ============================================================
# 层3: "继续"关键词检测（Continue Bypass Detection Layer）
# ============================================================
# 目的: 防止使用"继续"关键词绕过工作流检查
# 检测: "继续" + 编程操作的组合模式
# 这是最关键的一层，修复了v1.x的主要漏洞
# ============================================================
detect_continue_bypass() {
    local input="$1"
    local violations=0

    log_debug "Layer 3: Continue Bypass Detection - Start"

    # 定义"继续"类关键词（扩展列表）
    local continue_patterns=(
        "继续"
        "continue"
        "接着"
        "然后"
        "下一步"
        "proceed"
        "next"
        "move on"
        "carry on"
        "接下来"
        "之后"
        "following"
        "subsequently"
    )

    # 定义编程操作关键词（精确匹配）
    local programming_keywords=(
        "写代码"
        "编码"
        "实现"
        "implement"
        "code"
        "develop"
        "create function"
        "add feature"
        "修改"
        "modify"
        "update code"
        "写.*function"
        "创建.*class"
        "定义.*method"
        "编写.*逻辑"
        "构建.*API"
    )

    # 检测"继续 + 编程操作"组合
    for continue_word in "${continue_patterns[@]}"; do
        for prog_word in "${programming_keywords[@]}"; do
            # 正向检查: 继续...编程
            if echo "$input" | grep -iqE "${continue_word}[[:space:][:punct:]]{0,20}${prog_word}"; then
                log_block "检测到'继续'绕过模式"
                log_error "  模式: '${continue_word}' → '${prog_word}'"
                log_error "  输入片段: $(echo "$input" | grep -iE "${continue_word}[[:space:][:punct:]]{0,20}${prog_word}" | head -1)"
                log_warn "  说明: 这种模式可能绕过工作流验证"
                log_warn "  建议: 明确说明在哪个Phase执行操作"
                ((violations++))
                break 2  # 退出两层循环
            fi

            # 反向检查: 编程...继续
            if echo "$input" | grep -iqE "${prog_word}[[:space:][:punct:]]{0,20}${continue_word}"; then
                log_block "检测到编程操作+继续模式"
                log_error "  模式: '${prog_word}' → '${continue_word}'"
                log_error "  输入片段: $(echo "$input" | grep -iE "${prog_word}[[:space:][:punct:]]{0,20}${continue_word}" | head -1)"
                ((violations++))
                break 2
            fi
        done
    done

    # 额外检测: "继续上次的"、"继续之前的"等隐式绕过
    local implicit_continue_patterns=(
        "继续上次"
        "继续之前"
        "继续刚才"
        "continue where.*left"
        "continue from.*last"
        "resume.*previous"
    )

    for pattern in "${implicit_continue_patterns[@]}"; do
        if echo "$input" | grep -iqE "${pattern}"; then
            log_block "检测到隐式'继续'模式"
            log_error "  模式: ${pattern}"
            log_warn "  请明确当前工作流状态和Phase"
            ((violations++))
        fi
    done

    log_debug "Layer 3: Continue Bypass Detection - Found ${violations} violations"
    return $violations
}

# ============================================================
# 层4: 编程关键词检测（Programming Keyword Detection Layer）
# ============================================================
# 目的: 防止在工作流未激活时进行编程操作
# 检测: 工作流激活状态、编程语言语法
# ============================================================
detect_programming_without_workflow() {
    local input="$1"
    local workflow_active="no"
    local violations=0

    log_debug "Layer 4: Programming Keyword Detection - Start"

    # 检查工作流是否激活
    if [[ -f "${WORKFLOW_DIR}/ACTIVE" ]]; then
        workflow_active="yes"
        log_debug "Workflow is active"
    else
        log_debug "Workflow is NOT active"
    fi

    # 如果工作流未激活，检测编程操作
    if [[ "$workflow_active" == "no" ]]; then
        # 定义编程语法模式（语言无关）
        local programming_patterns=(
            "function[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\("
            "class[[:space:]]+[A-Z][a-zA-Z0-9_]*"
            "def[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\("
            "import[[:space:]]+[a-zA-Z_]"
            "from[[:space:]]+[a-zA-Z_].*import"
            "async[[:space:]]+def"
            "const[[:space:]]+[a-zA-Z_]"
            "let[[:space:]]+[a-zA-Z_]"
            "var[[:space:]]+[a-zA-Z_]"
            "interface[[:space:]]+[A-Z]"
            "type[[:space:]]+[A-Z].*="
            "@[a-zA-Z_]+.*\("
            "public[[:space:]]+class"
            "private[[:space:]]+[a-zA-Z_]"
            "protected[[:space:]]+[a-zA-Z_]"
        )

        for pattern in "${programming_patterns[@]}"; do
            if echo "$input" | grep -qE "$pattern"; then
                log_block "检测到编程代码，但工作流未激活"
                log_error "  检测到的模式: ${pattern}"
                log_error "  输入片段: $(echo "$input" | grep -E "$pattern" | head -1)"
                log_warn "  建议: 请先启动工作流"
                log_warn "    方式1: 明确说明'启动工作流'"
                log_warn "    方式2: 明确说明当前Phase（如'在P3阶段...'）"
                ((violations++))
                break  # 只报告一次
            fi
        done
    fi

    log_debug "Layer 4: Programming Keyword Detection - Found ${violations} violations"
    return $violations
}

# ============================================================
# 层5: 工作流状态检测（Workflow State Detection Layer）
# ============================================================
# 目的: 确保在正确的Phase执行相应操作
# 检测: 当前Phase状态、操作类型匹配
# ============================================================
detect_workflow_state_violation() {
    local input="$1"
    local current_phase=""
    local violations=0

    log_debug "Layer 5: Workflow State Detection - Start"

    # 读取当前Phase
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        current_phase=$(cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]')
        log_debug "Current phase: ${current_phase}"
    else
        log_debug "No phase file found, skipping state detection"
        return 0  # 讨论模式，跳过检查
    fi

    # 定义Phase允许的操作
    declare -A phase_allowed_operations
    phase_allowed_operations["P0"]="探索|research|spike|prototype|feasibility"
    phase_allowed_operations["P1"]="规划|plan|analyze|requirement|design"
    phase_allowed_operations["P2"]="骨架|skeleton|structure|architecture|setup"
    phase_allowed_operations["P3"]="实现|implement|code|develop|feature"
    phase_allowed_operations["P4"]="测试|test|验证|verify|coverage"
    phase_allowed_operations["P5"]="审查|review|inspect|quality|refactor"
    phase_allowed_operations["P6"]="发布|release|deploy|document|publish"
    phase_allowed_operations["P7"]="监控|monitor|observe|track|alert"

    # 定义编码操作关键词
    local coding_keywords=(
        "写代码"
        "编码"
        "实现.*function"
        "创建.*class"
        "implement.*method"
        "code.*logic"
        "develop.*feature"
    )

    # 检查编码操作是否在允许的Phase
    local allows_coding=0
    case "$current_phase" in
        P3|P4)
            allows_coding=1
            log_debug "Current phase allows coding: ${current_phase}"
            ;;
        *)
            allows_coding=0
            log_debug "Current phase does NOT allow coding: ${current_phase}"
            ;;
    esac

    # 如果当前Phase不允许编码，检测编码操作
    if [[ $allows_coding -eq 0 ]]; then
        for keyword in "${coding_keywords[@]}"; do
            if echo "$input" | grep -iqE "${keyword}"; then
                log_block "当前Phase ${current_phase} 不允许编码操作"
                log_error "  检测到的关键词: ${keyword}"
                log_error "  输入片段: $(echo "$input" | grep -iE "${keyword}" | head -1)"
                log_warn "  建议: 编码操作应在P3（实现）或P4（测试）阶段进行"

                # 根据当前Phase给出具体建议
                case "$current_phase" in
                    P0)
                        log_warn "  P0阶段应专注于: 技术探索、可行性验证、原型测试"
                        ;;
                    P1)
                        log_warn "  P1阶段应专注于: 需求分析、规划设计、生成PLAN.md"
                        ;;
                    P2)
                        log_warn "  P2阶段应专注于: 搭建骨架、配置环境、建立结构"
                        ;;
                    P5)
                        log_warn "  P5阶段应专注于: 代码审查、质量检查、生成REVIEW.md"
                        ;;
                    P6)
                        log_warn "  P6阶段应专注于: 文档完善、发布准备、部署配置"
                        ;;
                    P7)
                        log_warn "  P7阶段应专注于: 生产监控、SLO跟踪、性能分析"
                        ;;
                esac

                ((violations++))
                break  # 只报告一次
            fi
        done
    fi

    log_debug "Layer 5: Workflow State Detection - Found ${violations} violations"
    return $violations
}

# ============================================================
# 综合检测引擎（Integrated Detection Engine）
# ============================================================
run_all_detections() {
    local input="$1"
    local total_violations=0
    local layer_results=()

    log_info "========================================"
    log_info "Claude Enhancer v2.0 - 5层检测系统"
    log_info "========================================"
    echo ""

    # 层1: Phase检测
    log_info "[1/5] Phase检测 (Phase Detection)..."
    if detect_phase_violation "$input"; then
        layer_results+=("1:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("1:PASS")
        log_success "通过"
    fi
    echo ""

    # 层2: 分支检测
    log_info "[2/5] 分支检测 (Branch Detection)..."
    if detect_branch_violation "$input"; then
        layer_results+=("2:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("2:PASS")
        log_success "通过"
    fi
    echo ""

    # 层3: "继续"关键词检测
    log_info "[3/5] '继续'绕过检测 (Continue Bypass Detection)..."
    if detect_continue_bypass "$input"; then
        layer_results+=("3:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("3:PASS")
        log_success "通过"
    fi
    echo ""

    # 层4: 编程关键词检测
    log_info "[4/5] 编程关键词检测 (Programming Keyword Detection)..."
    if detect_programming_without_workflow "$input"; then
        layer_results+=("4:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("4:PASS")
        log_success "通过"
    fi
    echo ""

    # 层5: 工作流状态检测
    log_info "[5/5] 工作流状态检测 (Workflow State Detection)..."
    if detect_workflow_state_violation "$input"; then
        layer_results+=("5:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("5:PASS")
        log_success "通过"
    fi
    echo ""

    # 总结报告
    log_info "========================================"
    log_info "检测总结"
    log_info "========================================"

    local passed=0
    local failed=0

    for result in "${layer_results[@]}"; do
        local layer="${result%%:*}"
        local status="${result##*:}"

        if [[ "$status" == "PASS" ]]; then
            echo -e "  层${layer}: ${GREEN}✓ 通过${NC}"
            ((passed++))
        else
            echo -e "  层${layer}: ${RED}✗ 失败${NC}"
            ((failed++))
        fi
    done

    echo ""
    log_info "通过: ${passed}/5"
    log_info "失败: ${failed}/5"
    log_info "总违规: ${total_violations}"
    log_info "========================================"

    # 最终判定
    if [[ $total_violations -gt 0 ]]; then
        echo ""
        log_error "❌ 强制执行器阻止操作"
        echo ""
        log_warn "修复建议:"
        log_warn "1. 检查当前Phase状态: cat .workflow/current"
        log_warn "2. 确认分支状态: git branch --show-current"
        log_warn "3. 确保工作流已激活: ls .workflow/ACTIVE"
        log_warn "4. 遵循8-Phase工作流规范"
        log_warn "5. 避免使用'继续'等模糊词汇，明确说明Phase"
        echo ""

        # 写入违规日志
        {
            echo "=========================================="
            echo "Violation Report"
            echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "Total Violations: ${total_violations}"
            echo "Input: ${input}"
            echo "=========================================="
        } >> "${LOG_DIR}/violations.log"

        return 1
    fi

    echo ""
    log_success "✅ 所有检测通过，允许继续"
    return 0
}

# ============================================================
# 主入口
# ============================================================
show_help() {
    cat << 'EOF'
Claude Enhancer v2.0 - Enhanced Workflow Enforcer

用法:
  enforcer_v2.sh <input_text>
  enforcer_v2.sh --test
  enforcer_v2.sh --help

选项:
  --test          运行内置测试用例
  --help          显示帮助信息
  --debug         启用调试模式

环境变量:
  DEBUG_ENFORCER=1    启用调试输出

示例:
  enforcer_v2.sh "在P3阶段实现用户登录功能"
  enforcer_v2.sh "继续写代码"  # 应该被阻止
  DEBUG_ENFORCER=1 enforcer_v2.sh "测试输入"

5层检测机制:
  1. Phase检测 - 防止跳过Phase
  2. 分支检测 - 防止在保护分支编码
  3. 继续检测 - 防止"继续"绕过工作流
  4. 编程检测 - 防止无工作流编码
  5. 状态检测 - 确保Phase操作匹配

EOF
}

run_tests() {
    log_info "运行内置测试用例..."
    echo ""

    local test_cases=(
        "继续写代码:FAIL:应阻止'继续'绕过"
        "在P3阶段实现登录功能:PASS:合法的P3操作"
        "跳过P1直接编码:FAIL:应阻止跳过Phase"
        "def hello(): pass:FAIL:无工作流编码"
    )

    local passed=0
    local failed=0

    for test_case in "${test_cases[@]}"; do
        IFS=':' read -r input expected_result description <<< "$test_case"

        log_info "测试: ${description}"
        log_debug "  输入: ${input}"
        log_debug "  期望: ${expected_result}"

        if run_all_detections "$input" > /dev/null 2>&1; then
            actual_result="PASS"
        else
            actual_result="FAIL"
        fi

        if [[ "$actual_result" == "$expected_result" ]]; then
            log_success "通过: ${description}"
            ((passed++))
        else
            log_error "失败: ${description} (期望: ${expected_result}, 实际: ${actual_result})"
            ((failed++))
        fi
        echo ""
    done

    log_info "测试总结: ${passed} 通过, ${failed} 失败"

    if [[ $failed -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

main() {
    # 解析参数
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --test)
            run_tests
            exit $?
            ;;
        --debug)
            export DEBUG_ENFORCER=1
            shift
            ;;
        "")
            log_error "错误: 缺少输入参数"
            echo ""
            show_help
            exit 1
            ;;
    esac

    local input_text="$*"

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行检测
    if run_all_detections "$input_text"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_debug "Execution time: ${duration}s"
        exit 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_debug "Execution time: ${duration}s"
        exit 1
    fi
}

# 执行主函数
main "$@"
