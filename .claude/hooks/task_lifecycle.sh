#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 任务生命周期管理器
# Claude Enhancer v6.5.0 - Task-Branch Binding System
# ═══════════════════════════════════════════════════════════════
# 功能：管理任务的启动、完成、查询、取消
# 作者：Claude Code
# 创建时间：2025-10-15
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK_MAP="$PROJECT_ROOT/.workflow/task_branch_map.json"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/task_lifecycle.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 确保目录存在
mkdir -p "$(dirname "$TASK_MAP")"
mkdir -p "$(dirname "$LOG_FILE")"

# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') $*" >> "$LOG_FILE"
}

generate_task_id() {
    local desc="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local hash=$(echo "$desc" | md5sum | cut -c1-8)
    echo "TASK_${timestamp}_${hash}"
}

validate_json() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        return 1
    fi

    if command -v jq >/dev/null 2>&1; then
        jq empty "$file" 2>/dev/null
    else
        # 降级验证：至少检查是否是有效JSON
        python3 -c "import json; json.load(open('$file'))" 2>/dev/null
    fi
}

# ═══════════════════════════════════════════════════════════════
# 核心功能
# ═══════════════════════════════════════════════════════════════

task_start() {
    local description="$1"
    local branch="$2"

    # 参数验证
    if [[ -z "$description" || -z "$branch" ]]; then
        echo -e "${RED}❌ 错误：缺少必需参数${NC}" >&2
        echo "用法: task_start <描述> <分支名>" >&2
        return 1
    fi

    # 检查是否已有活动任务
    if [[ -f "$TASK_MAP" ]] && validate_json "$TASK_MAP"; then
        local active=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")
        if [[ -n "$active" ]]; then
            echo -e "${YELLOW}⚠️  警告：已存在活动任务${NC}" >&2
            echo "$(echo "$active" | jq -r '.description // "未知任务"')" >&2
            echo "" >&2
            echo "请先完成或取消当前任务：" >&2
            echo "  task_complete  # 完成任务" >&2
            echo "  task_cancel    # 取消任务" >&2
            return 1
        fi
    fi

    # 生成任务ID
    local task_id=$(generate_task_id "$description")

    # 创建任务记录
    cat > "$TASK_MAP" <<EOF
{
  "active_task": {
    "id": "$task_id",
    "description": "$description",
    "branch": "$branch",
    "start_time": "$(date -Iseconds)",
    "status": "in_progress",
    "commits": []
  },
  "task_history": []
}
EOF

    log "TASK_START: $task_id | $description | $branch"

    # 显示成功信息
    echo -e "${GREEN}✅ 任务已启动${NC}"
    echo ""
    echo -e "${BOLD}任务信息：${NC}"
    echo -e "  ${CYAN}ID:${NC}       $task_id"
    echo -e "  ${CYAN}描述:${NC}     $description"
    echo -e "  ${CYAN}绑定分支:${NC} $branch"
    echo -e "  ${CYAN}状态:${NC}     进行中"
    echo ""
    echo -e "${YELLOW}提醒：${NC}此任务期间请勿切换分支，否则操作将被阻止"
}

task_complete() {
    # 验证是否有活动任务
    if [[ ! -f "$TASK_MAP" ]] || ! validate_json "$TASK_MAP"; then
        echo -e "${YELLOW}⚠️  无活动任务${NC}" >&2
        return 0
    fi

    local active=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")
    if [[ -z "$active" ]]; then
        echo -e "${YELLOW}⚠️  无活动任务${NC}" >&2
        return 0
    fi

    # 提取任务信息
    local task_id=$(echo "$active" | jq -r '.id')
    local description=$(echo "$active" | jq -r '.description')
    local branch=$(echo "$active" | jq -r '.branch')
    local start_time=$(echo "$active" | jq -r '.start_time')

    # 归档到历史
    if [[ -f "$TASK_MAP" ]]; then
        local history=$(jq -r '.task_history // []' "$TASK_MAP")
        local completed_task=$(echo "$active" | jq ". + {\"end_time\": \"$(date -Iseconds)\", \"status\": \"completed\"}")

        jq --argjson task "$completed_task" '.task_history += [$task] | .active_task = null' "$TASK_MAP" > "$TASK_MAP.tmp"
        mv "$TASK_MAP.tmp" "$TASK_MAP"
    else
        echo '{"active_task": null, "task_history": []}' > "$TASK_MAP"
    fi

    log "TASK_COMPLETE: $task_id | $description | $branch"

    # 显示成功信息
    echo -e "${GREEN}✅ 任务已完成${NC}"
    echo ""
    echo -e "${BOLD}完成信息：${NC}"
    echo -e "  ${CYAN}ID:${NC}       $task_id"
    echo -e "  ${CYAN}描述:${NC}     $description"
    echo -e "  ${CYAN}分支:${NC}     $branch"
    echo -e "  ${CYAN}开始时间:${NC} $start_time"
    echo -e "  ${CYAN}完成时间:${NC} $(date -Iseconds)"
    echo ""
    echo -e "${GREEN}分支绑定已解除，可以开始新任务${NC}"
}

task_status() {
    # 验证文件
    if [[ ! -f "$TASK_MAP" ]] || ! validate_json "$TASK_MAP"; then
        echo -e "${YELLOW}⚠️  无任务记录${NC}"
        return 0
    fi

    local active=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")

    if [[ -z "$active" ]]; then
        echo -e "${CYAN}当前状态：${NC}无活动任务"
        echo ""
        echo "您可以开始新任务："
        echo "  task_start <描述> <分支名>"
    else
        echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BOLD}  当前活动任务${NC}"
        echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${CYAN}ID:${NC}         $(echo "$active" | jq -r '.id')"
        echo -e "${CYAN}描述:${NC}       $(echo "$active" | jq -r '.description')"
        echo -e "${CYAN}绑定分支:${NC}   $(echo "$active" | jq -r '.branch')"
        echo -e "${CYAN}开始时间:${NC}   $(echo "$active" | jq -r '.start_time')"
        echo -e "${CYAN}状态:${NC}       $(echo "$active" | jq -r '.status')"
        echo ""

        local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "未知")
        local bound_branch=$(echo "$active" | jq -r '.branch')

        if [[ "$current_branch" == "$bound_branch" ]]; then
            echo -e "${GREEN}✅ 当前分支正确：$current_branch${NC}"
        else
            echo -e "${RED}❌ 分支不匹配！${NC}"
            echo -e "   期望：$bound_branch"
            echo -e "   实际：$current_branch"
            echo ""
            echo -e "${YELLOW}建议操作：${NC}"
            echo "   git checkout $bound_branch"
        fi
        echo ""
        echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    fi
}

task_cancel() {
    # 验证是否有活动任务
    if [[ ! -f "$TASK_MAP" ]] || ! validate_json "$TASK_MAP"; then
        echo -e "${YELLOW}⚠️  无活动任务${NC}" >&2
        return 0
    fi

    local active=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")
    if [[ -z "$active" ]]; then
        echo -e "${YELLOW}⚠️  无活动任务${NC}" >&2
        return 0
    fi

    # 提取任务信息
    local task_id=$(echo "$active" | jq -r '.id')
    local description=$(echo "$active" | jq -r '.description')

    # 归档为取消状态
    if [[ -f "$TASK_MAP" ]]; then
        local cancelled_task=$(echo "$active" | jq ". + {\"end_time\": \"$(date -Iseconds)\", \"status\": \"cancelled\"}")
        jq --argjson task "$cancelled_task" '.task_history += [$task] | .active_task = null' "$TASK_MAP" > "$TASK_MAP.tmp"
        mv "$TASK_MAP.tmp" "$TASK_MAP"
    else
        echo '{"active_task": null, "task_history": []}' > "$TASK_MAP"
    fi

    log "TASK_CANCEL: $task_id | $description"

    # 显示警告信息
    echo -e "${YELLOW}⚠️  任务已取消${NC}"
    echo ""
    echo -e "${BOLD}取消信息：${NC}"
    echo -e "  ${CYAN}ID:${NC}   $task_id"
    echo -e "  ${CYAN}描述:${NC} $description"
    echo ""
    echo -e "${YELLOW}分支绑定已强制解除${NC}"
    echo -e "${RED}注意：${NC}这是紧急绕过机制，请确认操作必要性"
}

task_history() {
    # 验证文件
    if [[ ! -f "$TASK_MAP" ]] || ! validate_json "$TASK_MAP"; then
        echo -e "${YELLOW}⚠️  无历史记录${NC}"
        return 0
    fi

    local history=$(jq -r '.task_history // []' "$TASK_MAP")
    local count=$(echo "$history" | jq 'length')

    if [[ $count -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  无历史记录${NC}"
        return 0
    fi

    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  任务历史（最近10条）${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    echo "$history" | jq -r '.[-10:] | reverse | .[] |
        "ID:       \(.id)\n" +
        "描述:     \(.description)\n" +
        "分支:     \(.branch)\n" +
        "开始:     \(.start_time)\n" +
        "结束:     \(.end_time // "未完成")\n" +
        "状态:     \(.status)\n" +
        "---"'
}

# ═══════════════════════════════════════════════════════════════
# 命令行接口
# ═══════════════════════════════════════════════════════════════

show_usage() {
    cat <<'EOF'
任务生命周期管理器 - Task Lifecycle Manager

用法:
  task_lifecycle.sh start <描述> <分支名>  # 启动新任务
  task_lifecycle.sh complete                # 完成当前任务
  task_lifecycle.sh status                  # 查询任务状态
  task_lifecycle.sh cancel                  # 取消当前任务（紧急）
  task_lifecycle.sh history                 # 查看任务历史

示例:
  # 启动任务
  bash .claude/hooks/task_lifecycle.sh start "实现登录功能" "feature/login"

  # 查询状态
  bash .claude/hooks/task_lifecycle.sh status

  # 完成任务
  bash .claude/hooks/task_lifecycle.sh complete

说明:
  - 启动任务后，分支将被绑定，切换分支会被阻止
  - 完成任务后，绑定自动解除
  - 取消任务是紧急绕过机制，请谨慎使用
EOF
}

main() {
    local command="${1:-}"

    case "$command" in
        start)
            if [[ $# -lt 3 ]]; then
                echo -e "${RED}❌ 错误：参数不足${NC}" >&2
                echo "用法: task_lifecycle.sh start <描述> <分支名>" >&2
                exit 1
            fi
            task_start "$2" "$3"
            ;;
        complete)
            task_complete
            ;;
        status)
            task_status
            ;;
        cancel)
            task_cancel
            ;;
        history)
            task_history
            ;;
        ""|help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}❌ 错误：未知命令 '$command'${NC}" >&2
            echo "" >&2
            show_usage >&2
            exit 1
            ;;
    esac
}

# 如果直接执行（不是source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
