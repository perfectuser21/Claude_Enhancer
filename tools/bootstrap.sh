#!/usr/bin/env bash
# ============================================================================
# Bootstrap Script - 一键初始化Claude Enhancer环境
# ============================================================================
# Version: 5.3.0
# Purpose: 设置git hooks、验证依赖、配置权限
# Compatibility: Linux, macOS, WSL
# ============================================================================

set -euo pipefail

# ============================================================================
# 颜色定义（兼容性处理）
# ============================================================================
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' BOLD='' RESET=''
fi

# ============================================================================
# 全局变量
# ============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LOG_FILE="${PROJECT_ROOT}/bootstrap.log"
readonly TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# 错误计数
WARNINGS=0
ERRORS=0

# ============================================================================
# 日志函数
# ============================================================================
log() {
    echo "[${TIMESTAMP}] $*" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}ℹ${RESET}  $*" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}✓${RESET}  $*" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}⚠${RESET}  $*" | tee -a "${LOG_FILE}"
    ((WARNINGS++)) || true
}

log_error() {
    echo -e "${RED}✗${RESET}  $*" | tee -a "${LOG_FILE}"
    ((ERRORS++)) || true
}

log_step() {
    echo -e "\n${CYAN}${BOLD}==> $*${RESET}" | tee -a "${LOG_FILE}"
}

# ============================================================================
# 平台检测
# ============================================================================
detect_platform() {
    local os_type
    os_type="$(uname -s)"

    case "${os_type}" in
        Linux*)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "WSL"
            else
                echo "Linux"
            fi
            ;;
        Darwin*)
            echo "macOS"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "Windows"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# ============================================================================
# 依赖检查
# ============================================================================
check_command() {
    local cmd=$1
    local install_hint=$2

    if command -v "${cmd}" >/dev/null 2>&1; then
        log_success "${cmd} is installed ($(command -v "${cmd}"))"
        return 0
    else
        log_warning "${cmd} is NOT installed. ${install_hint}"
        return 1
    fi
}

check_dependencies() {
    log_step "Checking Dependencies"

    local platform
    platform=$(detect_platform)
    log_info "Detected platform: ${platform}"

    # 必需工具
    local required_tools=(
        "git:Git is required. Install from https://git-scm.com/"
        "bash:Bash 4+ is required"
    )

    # 推荐工具
    local recommended_tools=(
        "jq:Install via 'apt install jq' (Linux) or 'brew install jq' (macOS)"
        "yq:Install via 'apt install yq' (Linux) or 'brew install yq' (macOS)"
        "shellcheck:Install via 'apt install shellcheck' (Linux) or 'brew install shellcheck' (macOS)"
        "node:Install from https://nodejs.org/ for BDD tests"
    )

    # 检查必需工具
    local has_all_required=true
    for tool_spec in "${required_tools[@]}"; do
        IFS=':' read -r cmd hint <<< "${tool_spec}"
        if ! check_command "${cmd}" "${hint}"; then
            has_all_required=false
        fi
    done

    if [[ "${has_all_required}" == "false" ]]; then
        log_error "Missing required dependencies. Please install them first."
        return 1
    fi

    # 检查推荐工具
    log_info "Checking recommended tools..."
    for tool_spec in "${recommended_tools[@]}"; do
        IFS=':' read -r cmd hint <<< "${tool_spec}"
        check_command "${cmd}" "${hint}" || true
    done

    # 检查Bash版本
    local bash_version
    bash_version=$(bash --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1)
    if (( $(echo "${bash_version} >= 4.0" | bc -l 2>/dev/null || echo 0) )); then
        log_success "Bash version ${bash_version} is supported"
    else
        log_warning "Bash version ${bash_version} detected. Version 4.0+ recommended."
    fi

    return 0
}

# ============================================================================
# Git配置
# ============================================================================
setup_git_hooks() {
    log_step "Setting up Git Hooks"

    # 检查是否在Git仓库中
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not a git repository. Please run 'git init' first."
        return 1
    fi

    local hooks_dir="${PROJECT_ROOT}/.git/hooks"

    # 创建hooks目录（如果不存在）
    if [[ ! -d "${hooks_dir}" ]]; then
        mkdir -p "${hooks_dir}"
        log_info "Created hooks directory: ${hooks_dir}"
    fi

    # 设置git hooks路径
    log_info "Configuring git core.hooksPath..."
    if git config core.hooksPath .git/hooks; then
        log_success "Git hooks path configured: .git/hooks"
    else
        log_error "Failed to configure git hooks path"
        return 1
    fi

    # 验证配置
    local configured_path
    configured_path=$(git config --get core.hooksPath || echo "")
    if [[ "${configured_path}" == ".git/hooks" ]]; then
        log_success "Verified hooks path: ${configured_path}"
    else
        log_warning "Hooks path verification failed. Expected '.git/hooks', got '${configured_path}'"
    fi

    return 0
}

# ============================================================================
# 权限设置
# ============================================================================
set_permissions() {
    log_step "Setting File Permissions"

    local chmod_errors=0

    # Git hooks权限
    if [[ -d "${PROJECT_ROOT}/.git/hooks" ]]; then
        log_info "Setting executable permissions for git hooks..."
        if chmod +x "${PROJECT_ROOT}/.git/hooks"/* 2>/dev/null; then
            log_success "Git hooks permissions updated"
        else
            log_warning "No hooks found or permission update skipped"
        fi
    fi

    # Workflow脚本权限
    if [[ -d "${PROJECT_ROOT}/.workflow" ]]; then
        log_info "Setting executable permissions for workflow scripts..."
        if find "${PROJECT_ROOT}/.workflow" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null; then
            local count
            count=$(find "${PROJECT_ROOT}/.workflow" -type f -name "*.sh" | wc -l)
            log_success "Updated ${count} workflow scripts"
        else
            log_warning "Workflow scripts not found or permission update skipped"
        fi
    fi

    # Tools脚本权限
    if [[ -d "${PROJECT_ROOT}/tools" ]]; then
        log_info "Setting executable permissions for tools..."
        if find "${PROJECT_ROOT}/tools" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null; then
            local count
            count=$(find "${PROJECT_ROOT}/tools" -type f -name "*.sh" | wc -l)
            log_success "Updated ${count} tool scripts"
        else
            log_warning "Tool scripts not found or permission update skipped"
        fi
    fi

    # Scripts目录权限
    if [[ -d "${PROJECT_ROOT}/scripts" ]]; then
        log_info "Setting executable permissions for scripts..."
        if find "${PROJECT_ROOT}/scripts" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null; then
            local count
            count=$(find "${PROJECT_ROOT}/scripts" -type f -name "*.sh" | wc -l)
            log_success "Updated ${count} scripts"
        else
            log_warning "Scripts not found or permission update skipped"
        fi
    fi

    # Test脚本权限
    if [[ -d "${PROJECT_ROOT}/test" ]]; then
        log_info "Setting executable permissions for test scripts..."
        if find "${PROJECT_ROOT}/test" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null; then
            local count
            count=$(find "${PROJECT_ROOT}/test" -type f -name "*.sh" | wc -l)
            log_success "Updated ${count} test scripts"
        else
            log_warning "Test scripts not found or permission update skipped"
        fi
    fi

    return 0
}

# ============================================================================
# 环境验证
# ============================================================================
verify_setup() {
    log_step "Verifying Setup"

    local verification_passed=true

    # 验证git config
    if git config --get core.hooksPath >/dev/null 2>&1; then
        log_success "Git hooks configuration is set"
    else
        log_error "Git hooks configuration is missing"
        verification_passed=false
    fi

    # 验证关键脚本可执行
    local key_scripts=(
        ".git/hooks/pre-commit"
        ".git/hooks/commit-msg"
        ".git/hooks/pre-push"
    )

    for script in "${key_scripts[@]}"; do
        local full_path="${PROJECT_ROOT}/${script}"
        if [[ -f "${full_path}" ]]; then
            if [[ -x "${full_path}" ]]; then
                log_success "${script} is executable"
            else
                log_warning "${script} exists but is not executable"
            fi
        fi
    done

    if [[ "${verification_passed}" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    echo -e "${MAGENTA}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║   Claude Enhancer 5.3 - Bootstrap Initialization    ║"
    echo "║   Production-Ready AI Programming Environment        ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${RESET}"

    log "Bootstrap started at ${TIMESTAMP}"
    log "Project root: ${PROJECT_ROOT}"

    # 执行初始化步骤
    local step_failed=false

    check_dependencies || step_failed=true

    if [[ "${step_failed}" == "false" ]]; then
        setup_git_hooks || step_failed=true
    fi

    if [[ "${step_failed}" == "false" ]]; then
        set_permissions || step_failed=true
    fi

    if [[ "${step_failed}" == "false" ]]; then
        verify_setup || step_failed=true
    fi

    # 生成报告
    log_step "Bootstrap Summary"

    if [[ "${step_failed}" == "true" ]] || [[ ${ERRORS} -gt 0 ]]; then
        echo -e "${RED}${BOLD}"
        echo "╔═══════════════════════════════════════════════════════╗"
        echo "║   Bootstrap FAILED - Please check errors above      ║"
        echo "╚═══════════════════════════════════════════════════════╝"
        echo -e "${RESET}"
        log_error "Bootstrap completed with ${ERRORS} error(s) and ${WARNINGS} warning(s)"
        log_info "Log file: ${LOG_FILE}"
        exit 1
    else
        echo -e "${GREEN}${BOLD}"
        echo "╔═══════════════════════════════════════════════════════╗"
        echo "║   Bootstrap SUCCESSFUL - Environment Ready           ║"
        echo "╚═══════════════════════════════════════════════════════╝"
        echo -e "${RESET}"

        if [[ ${WARNINGS} -gt 0 ]]; then
            log_warning "Bootstrap completed successfully with ${WARNINGS} warning(s)"
        else
            log_success "Bootstrap completed successfully with no warnings"
        fi

        log_info "Log file: ${LOG_FILE}"

        echo ""
        echo -e "${CYAN}Next Steps:${RESET}"
        echo "  1. Review the log file: ${LOG_FILE}"
        echo "  2. Install recommended tools if needed (jq, yq, shellcheck)"
        echo "  3. Run tests: npm run bdd"
        echo "  4. Start coding with Claude Enhancer workflow"
        echo ""

        exit 0
    fi
}

# ============================================================================
# 入口点
# ============================================================================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
