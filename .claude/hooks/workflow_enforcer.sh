#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 工作流强制执行器
# 确保所有编程任务按照8-Phase工作流执行

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [workflow_enforcer.sh] triggered by ${USER:-claude} args: $*" >> "$LOG_FILE"

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 获取当前Phase
get_current_phase() {
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        cat "$PROJECT_ROOT/.phase/current"
    else
        echo "P0"
    fi
}

# 检查是否是编程任务
is_programming_task() {
    local prompt="$1"

    # 编程任务关键词
    local programming_keywords=(
        "实现" "开发" "编写" "创建" "修复" "优化" "重构"
        "implement" "develop" "write" "create" "fix" "optimize" "refactor"
        "代码" "功能" "组件" "模块" "系统" "架构"
        "code" "feature" "component" "module" "system" "architecture"
    )

    for keyword in "${programming_keywords[@]}"; do
        if [[ "$prompt" == *"$keyword"* ]]; then
            return 0
        fi
    done

    return 1
}

# 强制执行工作流
enforce_workflow() {
    local current_phase=$(get_current_phase)

    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║            🛑 工作流强制执行 - 阻塞模式                   ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo

    echo -e "${YELLOW}⚠️  检测到编程任务，但未按工作流执行！${NC}"
    echo
    echo -e "${BLUE}📍 当前Phase: ${current_phase}${NC}"
    echo

    case "$current_phase" in
        "P0"|"")
            echo -e "${RED}❌ 错误：必须先创建分支（Phase 0）${NC}"
            echo -e "${GREEN}✅ 请执行：git checkout -b feature/your-feature${NC}"
            echo
            echo -e "${YELLOW}工作流要求：${NC}"
            echo "  1. Phase 0: 创建feature分支"
            echo "  2. Phase 1: 创建计划文档 (docs/PLAN.md)"
            echo "  3. Phase 2: 设计架构骨架"
            echo "  4. Phase 3: 实现功能（4-6-8 Agent策略）"
            echo "  5. Phase 4: 本地测试"
            echo "  6. Phase 5: 代码提交"
            echo "  7. Phase 6: 代码审查"
            echo
            echo -e "${RED}🚫 操作已阻塞！请按工作流执行。${NC}"
            exit 1
            ;;

        "P1")
            if [[ ! -f "$PROJECT_ROOT/docs/PLAN.md" ]]; then
                echo -e "${RED}❌ 错误：Phase 1需要创建计划文档${NC}"
                echo -e "${GREEN}✅ 请先创建：docs/PLAN.md${NC}"
                echo
                echo "计划文档必须包含："
                echo "  - ## 任务清单（至少5项）"
                echo "  - ## 受影响文件清单"
                echo "  - ## 回滚方案"
                echo
                echo -e "${RED}🚫 操作已阻塞！${NC}"
                exit 1
            fi
            ;;

        "P2")
            echo -e "${YELLOW}📐 Phase 2: 请先完成架构设计${NC}"
            echo "  - 创建必要的目录结构"
            echo "  - 定义接口和数据结构"
            echo "  - 记录设计决策"
            ;;

        "P3")
            echo -e "${GREEN}✅ Phase 3: 可以开始实现${NC}"
            echo "  - 使用4-6-8 Agent策略"
            echo "  - 简单任务：4个Agent"
            echo "  - 标准任务：6个Agent"
            echo "  - 复杂任务：8个Agent"
            ;;

        *)
            echo -e "${BLUE}ℹ️  当前在Phase ${current_phase}${NC}"
            ;;
    esac

    # 显示正确的执行命令
    echo
    echo -e "${MAGENTA}📋 推荐执行步骤：${NC}"
    echo "  1. 查看当前状态："
    echo "     ${GREEN}./.workflow/executor.sh status${NC}"
    echo
    echo "  2. 验证当前Phase："
    echo "     ${GREEN}./.workflow/executor.sh validate${NC}"
    echo
    echo "  3. 进入下一Phase："
    echo "     ${GREEN}./.workflow/executor.sh next${NC}"
    echo

    # 返回阻塞信号
    return 1
}

# 主函数
main() {
    local user_prompt="${1:-}"

    # 检查是否是编程任务
    if is_programming_task "$user_prompt"; then
        # 检查是否已在正确的Phase
        local current_phase=$(get_current_phase)

        # 如果不在P3或更高Phase，强制执行工作流
        if [[ "$current_phase" != "P3" && "$current_phase" != "P4" && \
              "$current_phase" != "P5" && "$current_phase" != "P6" ]]; then
            enforce_workflow
        fi
    fi

    # 如果一切正常，返回成功
    return 0
}

# 执行主函数
main "$@"
