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

    # 根据静默模式决定是否输出
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║            🛑 工作流强制执行 - 阻塞模式                   ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
        echo

        echo -e "${YELLOW}⚠️  检测到编程任务，但未按工作流执行！${NC}"
        echo
        echo -e "${BLUE}📍 当前Phase: ${current_phase}${NC}"
        echo
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        # 紧凑模式输出
        echo "[Workflow] ⚠️ 未按工作流执行 (Phase: ${current_phase})"
    fi

    case "$current_phase" in
        "P0"|"")
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
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
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Workflow] ❌ 需要创建分支 (Phase 0)"
            fi
            exit 1
            ;;

        "P1")
            if [[ ! -f "$PROJECT_ROOT/docs/PLAN.md" ]]; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${RED}❌ 错误：Phase 1需要创建计划文档${NC}"
                    echo -e "${GREEN}✅ 请先创建：docs/PLAN.md${NC}"
                    echo
                    echo "计划文档必须包含："
                    echo "  - ## 任务清单（至少5项）"
                    echo "  - ## 受影响文件清单"
                    echo "  - ## 回滚方案"
                    echo
                    echo -e "${RED}🚫 操作已阻塞！${NC}"
                elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                    echo "[Workflow] ❌ 需要计划文档 docs/PLAN.md"
                fi
                exit 1
            fi
            ;;

        "P2")
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${YELLOW}📐 Phase 2: 请先完成架构设计${NC}"
                echo "  - 创建必要的目录结构"
                echo "  - 定义接口和数据结构"
                echo "  - 记录设计决策"
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Workflow] 📐 Phase 2: 架构设计"
            fi
            ;;

        "P3")
            # P3 Implementation Phase Validation
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${BLUE}🔍 Validating P3 (Implementation) phase...${NC}"
            fi

            # Check 1: Agent count (minimum 3 for implementation)
            AGENT_COUNT=0
            if [[ -f ".gates/agents_invocation.json" ]]; then
                AGENT_COUNT=$(jq '.agents | length' .gates/agents_invocation.json 2>/dev/null || echo "0")
            fi

            if [ "$AGENT_COUNT" -lt 3 ]; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${RED}❌ P3 requires ≥3 agents for implementation (found: $AGENT_COUNT)${NC}"
                    echo -e "${YELLOW}💡 Use: backend-architect, test-engineer, devops-engineer${NC}"
                fi
                exit 1
            fi

            # Check 2: Code changes present
            if ! git diff --cached --name-only | grep -qE '\.(py|sh|js|ts|yml)$'; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${YELLOW}⚠️ P3 should have code changes${NC}"
                fi
            fi

            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${GREEN}✅ P3 validation passed${NC}"
            fi
            ;;

        "P4")
            # P4 Testing Phase Validation
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${BLUE}🧪 Validating P4 (Testing) phase...${NC}"
            fi

            # Check 1: Test files exist
            TEST_FILES=$(git diff --cached --name-only | grep -E 'test_|_test\.|\.test\.' | wc -l)
            if [ "$TEST_FILES" -eq 0 ]; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${RED}❌ P4 requires test files${NC}"
                    echo -e "${YELLOW}💡 Add tests in test/ directory${NC}"
                fi
                exit 1
            fi

            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${GREEN}✅ P4 validation passed ($TEST_FILES test files)${NC}"
            fi
            ;;

        "P5")
            # P5 Review Phase Validation
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${BLUE}👀 Validating P5 (Review) phase...${NC}"
            fi

            # Check 1: REVIEW.md exists
            if [[ ! -f "docs/REVIEW.md" ]] && ! git diff --cached --name-only | grep -q "docs/REVIEW.md"; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${RED}❌ P5 requires REVIEW.md${NC}"
                    echo -e "${YELLOW}💡 Generate code review report: docs/REVIEW.md${NC}"
                fi
                exit 1
            fi

            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${GREEN}✅ P5 validation passed${NC}"
            fi
            ;;

        "P6")
            # P6 Release Phase Validation
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${BLUE}🚀 Validating P6 (Release) phase...${NC}"
            fi

            # Check 1: CHANGELOG.md updated
            if ! git diff --cached --name-only | grep -q "CHANGELOG.md"; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${RED}❌ P6 requires CHANGELOG.md update${NC}"
                    echo -e "${YELLOW}💡 Add release notes to CHANGELOG.md${NC}"
                fi
                exit 1
            fi

            # Check 2: Documentation updated
            DOC_FILES=$(git diff --cached --name-only | grep -E '\.md$|docs/' | wc -l)
            if [ "$DOC_FILES" -eq 0 ]; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo -e "${YELLOW}⚠️ No documentation updates in release${NC}"
                fi
            fi

            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${GREEN}✅ P6 validation passed${NC}"
            fi
            ;;

        "P7")
            # P7 Monitoring Phase - usually no commit restrictions
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${GREEN}✅ P7 Monitoring phase - no commit restrictions${NC}"
            fi
            ;;

        *)
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo -e "${BLUE}ℹ️  当前在Phase ${current_phase}${NC}"
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Workflow] Phase: ${current_phase}"
            fi
            ;;
    esac

    # 显示正确的执行命令
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
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
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        echo "[Workflow] 使用 ./.workflow/executor.sh 管理流程"
    fi

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

        # Enforce workflow for all phases (no bypass)
        # All phases now have proper validation in enforce_workflow()
        enforce_workflow
    fi

    # 如果一切正常，返回成功
    return 0
}

# 执行主函数
main "$@"
