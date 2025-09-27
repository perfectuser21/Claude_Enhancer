#!/bin/bash
# Git自动标签策略脚本
# 在每个关键阶段自动创建恢复点

set -euo pipefail

# 配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly TAG_PREFIX="checkpoint"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 日志函数
log_info() { echo "[INFO] $(date '+%H:%M:%S') $*"; }
log_error() { echo "[ERROR] $(date '+%H:%M:%S') $*" >&2; }
log_success() { echo "[SUCCESS] $(date '+%H:%M:%S') $*"; }

# 检查Git状态
check_git_status() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "不在Git仓库中"
        return 1
    fi

    if [[ -n $(git status --porcelain) ]]; then
        log_error "工作目录有未提交的更改"
        return 1
    fi

    return 0
}

# 获取当前Phase
get_current_phase() {
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        cat "$PROJECT_ROOT/.phase/current"
    else
        echo "unknown"
    fi
}

# 创建阶段标签
create_phase_tag() {
    local phase=$1
    local task_id=${2:-"auto"}
    local tag_name="${TAG_PREFIX}-${phase}-${task_id}-${TIMESTAMP}"
    local tag_message="Phase ${phase} checkpoint - Task ${task_id}"

    if git tag -a "$tag_name" -m "$tag_message"; then
        log_success "创建标签: $tag_name"
        return 0
    else
        log_error "创建标签失败: $tag_name"
        return 1
    fi
}

# 创建回滚点
create_rollback_point() {
    local reason=${1:-"manual"}
    local tag_name="rollback-${reason}-${TIMESTAMP}"
    local tag_message="Rollback point: ${reason}"

    # 获取当前状态信息
    local current_commit=$(git rev-parse HEAD)
    local current_branch=$(git branch --show-current)
    local current_phase=$(get_current_phase)

    # 创建详细的标签信息
    cat > "/tmp/rollback_info_${TIMESTAMP}.txt" << EOF
Rollback Point Information
==========================
Timestamp: $(date)
Commit: ${current_commit}
Branch: ${current_branch}
Phase: ${current_phase}
Reason: ${reason}

System Status:
- Working directory: clean
- Last commit: $(git log -1 --oneline)
- Modified files: $(git diff --name-only HEAD~1 | wc -l)

Phase Gates Status:
$(find "$PROJECT_ROOT/.gates" -name "*.ok" 2>/dev/null | sort || echo "No gates found")

Active Limits:
$(find "$PROJECT_ROOT/.limits" -name "max" -exec head -1 {} \; 2>/dev/null | paste - <(find "$PROJECT_ROOT/.limits" -name "max") || echo "No limits found")
EOF

    # 创建标签
    if git tag -a "$tag_name" -F "/tmp/rollback_info_${TIMESTAMP}.txt"; then
        log_success "创建回滚点: $tag_name"

        # 保存回滚信息到本地
        mkdir -p "$PROJECT_ROOT/.rollback/points"
        cp "/tmp/rollback_info_${TIMESTAMP}.txt" "$PROJECT_ROOT/.rollback/points/${tag_name}.info"

        # 清理临时文件
        rm "/tmp/rollback_info_${TIMESTAMP}.txt"

        return 0
    else
        log_error "创建回滚点失败: $tag_name"
        return 1
    fi
}

# 列出可用的回滚点
list_rollback_points() {
    log_info "可用的回滚点:"
    git tag -l "rollback-*" --sort=-version:refname | head -10 | while read -r tag; do
        local commit_date=$(git log -1 --format=%ci "$tag" 2>/dev/null || echo "unknown")
        local commit_msg=$(git log -1 --format=%s "$tag" 2>/dev/null || echo "unknown")
        echo "  $tag ($commit_date) - $commit_msg"
    done
}

# 自动阶段标签（在Phase转换时调用）
auto_phase_tag() {
    local phase=$1
    local task_id=$2

    log_info "为Phase $phase 创建自动标签..."

    if ! check_git_status; then
        log_error "Git状态检查失败，跳过标签创建"
        return 1
    fi

    create_phase_tag "$phase" "$task_id"
}

# 手动回滚点创建
manual_rollback_point() {
    local reason=${1:-"manual-checkpoint"}

    log_info "创建手动回滚点: $reason"

    if ! check_git_status; then
        log_error "Git状态检查失败，无法创建回滚点"
        return 1
    fi

    create_rollback_point "$reason"
}

# 清理旧标签
cleanup_old_tags() {
    local keep_count=${1:-20}

    log_info "清理旧标签，保留最新 $keep_count 个..."

    # 清理旧的checkpoint标签
    git tag -l "${TAG_PREFIX}-*" --sort=-version:refname | tail -n +$((keep_count + 1)) | while read -r tag; do
        if git tag -d "$tag"; then
            log_info "删除旧标签: $tag"
        fi
    done

    # 清理旧的rollback标签
    git tag -l "rollback-*" --sort=-version:refname | tail -n +$((keep_count + 1)) | while read -r tag; do
        if git tag -d "$tag"; then
            log_info "删除旧回滚标签: $tag"
        fi
    done
}

# 显示使用帮助
show_usage() {
    cat << EOF
Git标签策略工具

用法:
    $0 phase <phase> [task-id]     - 创建阶段标签
    $0 rollback [reason]           - 创建回滚点
    $0 list                        - 列出回滚点
    $0 cleanup [keep-count]        - 清理旧标签
    $0 help                        - 显示帮助

示例:
    $0 phase P3 task-123          - 为P3阶段创建标签
    $0 rollback "before-hotfix"   - 创建回滚点
    $0 list                       - 查看回滚点
    $0 cleanup 15                 - 保留最新15个标签
EOF
}

# 主函数
main() {
    case "${1:-help}" in
        "phase")
            if [[ $# -lt 2 ]]; then
                log_error "缺少phase参数"
                show_usage
                exit 1
            fi
            auto_phase_tag "$2" "${3:-auto}"
            ;;
        "rollback")
            manual_rollback_point "${2:-manual-checkpoint}"
            ;;
        "list")
            list_rollback_points
            ;;
        "cleanup")
            cleanup_old_tags "${2:-20}"
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi