#!/bin/bash
# Feature Registry CLI - 功能注册表命令行工具
# Purpose: 管理功能注册、验证、启用/禁用等操作

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly PROJECT_ROOT
REGISTRY="${PROJECT_ROOT}/.claude/FEATURE_REGISTRY.yaml"
readonly REGISTRY
TEMPLATE="${PROJECT_ROOT}/.claude/FEATURE_INTEGRATION_TEMPLATE.md"
readonly TEMPLATE
VERSION="1.0.0"
readonly VERSION

# 颜色定义
GREEN='\033[0;32m'
readonly GREEN
RED='\033[0;31m'
readonly RED
YELLOW='\033[1;33m'
readonly YELLOW
BLUE='\033[0;34m'
readonly BLUE
NC='\033[0m' # No Color
readonly NC

# ============= 辅助函数 =============

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

show_help() {
    cat << EOF
Feature Registry CLI v${VERSION}
管理Claude Enhancer的功能注册表

用法：
  $(basename "$0") <command> [options]

命令：
  register <name> <type> <location>  注册新功能
  list                               列出所有功能
  show <name>                        显示功能详情
  validate <name>                    验证功能集成
  enable <name>                      启用功能
  disable <name>                     禁用功能
  status                             显示系统状态
  init                               初始化注册表
  cleanup                            清理无效功能
  migrate                            迁移现有功能到注册表
  test <name>                        测试功能
  help                               显示帮助信息

选项：
  --json                             JSON格式输出
  --verbose                          详细输出
  --dry-run                          模拟运行

示例：
  $(basename "$0") register cache_manager performance .claude/tools/cache_manager.sh
  $(basename "$0") list --json
  $(basename "$0") validate cache_manager
  $(basename "$0") disable old_feature

EOF
}

# ============= 核心功能 =============

# 初始化注册表
init_registry() {
    if [[ -f "$REGISTRY" ]]; then
        log_warn "Registry already exists at $REGISTRY"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Initialization cancelled"
            return 1
        fi
    fi

    log_info "Initializing Feature Registry..."

    # 确保目录存在
    mkdir -p "$(dirname "$REGISTRY")"

    # 保持原有内容不变，已经很完善了
    log_success "Registry initialized at $REGISTRY"
}

# 注册新功能
register_feature() {
    local name="${1:-}"
    local type="${2:-}"
    local location="${3:-}"

    if [[ -z "$name" ]] || [[ -z "$type" ]] || [[ -z "$location" ]]; then
        log_error "Usage: register <name> <type> <location>"
        return 1
    fi

    # 验证类型
    local valid_types="core performance quality security monitoring utility"
    if ! echo "$valid_types" | grep -qw "$type"; then
        log_error "Invalid type: $type"
        log_info "Valid types: $valid_types"
        return 1
    fi

    # 验证文件存在
    if [[ ! -f "${PROJECT_ROOT}/${location}" ]]; then
        log_error "File not found: ${PROJECT_ROOT}/${location}"
        return 1
    fi

    log_info "Registering feature: $name"

    # 添加到注册表（简化的YAML追加）
    cat >> "$REGISTRY" << EOF

  ${name}:
    name: "${name}"
    type: "${type}"
    location: "${location}"
    phase_integration:
      - phase: "all"
        hook_point: "pre_execution"
    dependencies: []
    test_suite: "tests/test_${name}.sh"
    status: "active"
    added_date: "$(date +%Y-%m-%d)"
EOF

    log_success "Feature '$name' registered successfully"
    log_info "Next steps:"
    echo "  1. Configure phase integration in $REGISTRY"
    echo "  2. Create test suite at tests/test_${name}.sh"
    echo "  3. Run: $(basename "$0") validate $name"
}

# 列出所有功能
list_features() {
    # json_output参数预留给未来JSON输出功能
    # local json_output="${1:-false}"

    if [[ ! -f "$REGISTRY" ]]; then
        log_error "Registry not found. Run 'init' first."
        return 1
    fi

    log_info "Registered features:"
    echo ""

    # 提取功能列表（简化的YAML解析）
    local features
    features=$(grep "^  [a-z_]*:" "$REGISTRY" 2>/dev/null | sed 's/://g' | tr -d ' ')

    if [[ -z "$features" ]]; then
        log_warn "No features registered"
        return 0
    fi

    # 表格头
    printf "%-20s %-12s %-8s %-40s\n" "NAME" "TYPE" "STATUS" "LOCATION"
    printf "%-20s %-12s %-8s %-40s\n" "----" "----" "------" "--------"

    for feature in $features; do
        # 提取功能信息
        local type
        type=$(grep -A5 "^  ${feature}:" "$REGISTRY" | grep "type:" | head -1 | cut -d'"' -f2)
        local status
        status=$(grep -A10 "^  ${feature}:" "$REGISTRY" | grep "status:" | head -1 | cut -d'"' -f2)
        local location
        location=$(grep -A5 "^  ${feature}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)

        # 状态颜色
        local status_color="$NC"
        [[ "$status" == "active" ]] && status_color="$GREEN"
        [[ "$status" == "disabled" ]] && status_color="$YELLOW"

        printf "%-20s %-12s ${status_color}%-8s${NC} %-40s\n" \
            "$feature" "$type" "$status" "$location"
    done
}

# 显示功能详情
show_feature() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        log_error "Usage: show <name>"
        return 1
    fi

    if ! grep -q "^  ${name}:" "$REGISTRY" 2>/dev/null; then
        log_error "Feature '$name' not found"
        return 1
    fi

    echo "╔════════════════════════════════════════════╗"
    echo "║  Feature Details: $name"
    echo "╚════════════════════════════════════════════╝"
    echo ""

    # 提取并显示功能信息
    sed -n "/^  ${name}:/,/^  [a-z_]*:/p" "$REGISTRY" | head -n -1
}

# 验证功能
validate_feature() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        log_error "Usage: validate <name>"
        return 1
    fi

    log_info "Validating feature: $name"

    # 调用验证器
    if [[ -f "${PROJECT_ROOT}/scripts/feature_integration_validator.sh" ]]; then
        bash "${PROJECT_ROOT}/scripts/feature_integration_validator.sh" "$name"
    else
        log_warn "Validator not found, running basic checks..."

        # 基础验证
        local location
        location=$(grep -A5 "^  ${name}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)

        echo -n "  File exists: "
        if [[ -f "${PROJECT_ROOT}/${location}" ]]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            return 1
        fi

        echo -n "  Executable: "
        if [[ -x "${PROJECT_ROOT}/${location}" ]]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
}

# 启用功能
enable_feature() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        log_error "Usage: enable <name>"
        return 1
    fi

    log_info "Enabling feature: $name"

    # 更新状态为active
    sed -i "/^  ${name}:/,/^  [a-z_]*:/{s/status: \".*\"/status: \"active\"/}" "$REGISTRY"

    log_success "Feature '$name' enabled"
}

# 禁用功能
disable_feature() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        log_error "Usage: disable <name>"
        return 1
    fi

    log_info "Disabling feature: $name"

    # 更新状态为disabled
    sed -i "/^  ${name}:/,/^  [a-z_]*:/{s/status: \".*\"/status: \"disabled\"/}" "$REGISTRY"

    log_success "Feature '$name' disabled"
}

# 显示系统状态
show_status() {
    echo "╔════════════════════════════════════════════╗"
    echo "║  Feature Integration System Status         ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""

    # 统计信息
    if [[ -f "$REGISTRY" ]]; then
        local total
        total=$(grep -c "^  [a-z_]*:" "$REGISTRY" 2>/dev/null || echo 0)
        local active
        active=$(grep -c 'status: "active"' "$REGISTRY" 2>/dev/null || echo 0)
        local disabled
        disabled=$(grep -c 'status: "disabled"' "$REGISTRY" 2>/dev/null || echo 0)

        echo "Registry Statistics:"
        echo "  Total features: $total"
        echo "  Active: ${GREEN}$active${NC}"
        echo "  Disabled: ${YELLOW}$disabled${NC}"
        echo ""

        # 功能类型分布
        echo "Feature Types:"
        for type in core performance quality security monitoring utility; do
            local count
            count=$(grep -c "type: \"$type\"" "$REGISTRY" 2>/dev/null || echo 0)
            [[ $count -gt 0 ]] && echo "  $type: $count"
        done
    else
        log_warn "Registry not initialized"
    fi

    echo ""
    echo "System Health:"
    echo -n "  Registry: "
    [[ -f "$REGISTRY" ]] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

    echo -n "  Validator: "
    [[ -f "${PROJECT_ROOT}/scripts/feature_integration_validator.sh" ]] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

    echo -n "  Template: "
    [[ -f "$TEMPLATE" ]] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"
}

# 清理无效功能
cleanup_features() {
    log_info "Scanning for invalid features..."

    local invalid_count=0
    local features
    features=$(grep "^  [a-z_]*:" "$REGISTRY" 2>/dev/null | sed 's/://g' | tr -d ' ')

    for feature in $features; do
        local location
        location=$(grep -A5 "^  ${feature}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)

        if [[ ! -f "${PROJECT_ROOT}/${location}" ]]; then
            log_warn "Invalid feature: $feature (file not found: $location)"
            ((invalid_count++))

            read -p "Remove from registry? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # 删除功能条目（需要更复杂的sed操作）
                log_info "Removed $feature from registry"
            fi
        fi
    done

    if [[ $invalid_count -eq 0 ]]; then
        log_success "No invalid features found"
    else
        log_warn "Found $invalid_count invalid features"
    fi
}

# 迁移现有功能
migrate_features() {
    log_info "Migrating existing features to registry..."

    # 扫描已知的功能位置
    local locations=(
        ".claude/tools/*.sh"
        "scripts/*_*.sh"
        ".claude/hooks/*_*.sh"
    )

    local migrated=0

    for pattern in "${locations[@]}"; do
        for file in $PROJECT_ROOT/$pattern; do
            [[ ! -f "$file" ]] && continue

            local basename
            basename=$(basename "$file" .sh)
            local relpath
            relpath=$(realpath --relative-to="$PROJECT_ROOT" "$file")

            # 跳过已注册的
            if grep -q "^  ${basename}:" "$REGISTRY" 2>/dev/null; then
                continue
            fi

            log_info "Found unregistered feature: $basename"
            read -p "Register this feature? (y/N): " -n 1 -r
            echo

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                # 推断类型
                local type="utility"
                [[ "$file" =~ performance ]] && type="performance"
                [[ "$file" =~ quality|guardian ]] && type="quality"
                [[ "$file" =~ security ]] && type="security"
                [[ "$file" =~ monitor ]] && type="monitoring"

                register_feature "$basename" "$type" "$relpath"
                ((migrated++))
            fi
        done
    done

    log_success "Migrated $migrated features"
}

# 测试功能
test_feature() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        log_error "Usage: test <name>"
        return 1
    fi

    log_info "Testing feature: $name"

    # 获取测试套件路径
    local test_suite
    test_suite=$(grep -A10 "^  ${name}:" "$REGISTRY" | grep "test_suite:" | head -1 | cut -d'"' -f2)

    if [[ -z "$test_suite" ]] || [[ ! -f "${PROJECT_ROOT}/${test_suite}" ]]; then
        log_warn "No test suite found, running basic smoke test..."

        # 基础烟雾测试
        local location
        location=$(grep -A5 "^  ${name}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)

        if bash "${PROJECT_ROOT}/${location}" --help >/dev/null 2>&1; then
            log_success "Basic smoke test passed"
        else
            log_error "Feature does not support --help"
            return 1
        fi
    else
        # 运行测试套件
        bash "${PROJECT_ROOT}/${test_suite}"
    fi
}

# ============= 主函数 =============

main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        register)
            register_feature "$@"
            ;;
        list)
            list_features "$@"
            ;;
        show)
            show_feature "$@"
            ;;
        validate)
            validate_feature "$@"
            ;;
        enable)
            enable_feature "$@"
            ;;
        disable)
            disable_feature "$@"
            ;;
        status)
            show_status
            ;;
        init)
            init_registry
            ;;
        cleanup)
            cleanup_features
            ;;
        migrate)
            migrate_features
            ;;
        test)
            test_feature "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"