#!/bin/bash
# Claude Enhancer 工作流自动启动器
# 确保所有编程任务自动进入6-Phase工作流

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PHASE_DIR="$PROJECT_ROOT/.phase"

# 创建Phase目录
mkdir -p "$PHASE_DIR"

# 检查是否是编程任务
is_programming_task() {
    local prompt="${1:-}"

    # 编程任务关键词（中英文）
    local programming_keywords=(
        "实现" "开发" "编写" "创建" "修复" "优化" "重构" "添加" "集成" "部署"
        "implement" "develop" "write" "create" "fix" "optimize" "refactor" "add" "integrate" "deploy"
        "代码" "功能" "组件" "模块" "系统" "架构" "API" "数据库" "测试" "文档"
        "code" "feature" "component" "module" "system" "architecture" "database" "test" "document"
        "hook" "agent" "workflow" "phase" "git" "docker" "CI" "CD"
    )

    for keyword in "${programming_keywords[@]}"; do
        if [[ "${prompt,,}" == *"${keyword,,}"* ]]; then
            return 0
        fi
    done

    return 1
}

# 获取当前Phase
get_current_phase() {
    if [[ -f "$PHASE_DIR/current" ]]; then
        cat "$PHASE_DIR/current"
    else
        echo "P0"
    fi
}

# 设置当前Phase
set_current_phase() {
    local phase="$1"
    echo "$phase" > "$PHASE_DIR/current"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $phase" >> "$PHASE_DIR/history"
}

# 自动启动工作流
auto_start_workflow() {
    local current_phase=$(get_current_phase)
    local task_description="${1:-编程任务}"

    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          🚀 Claude Enhancer 工作流自动启动               ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo

    # 如果当前没有在工作流中，自动启动
    if [[ "$current_phase" == "P0" ]] || [[ -z "$current_phase" ]]; then
        echo -e "${YELLOW}🔍 检测到编程任务：${NC}${task_description:0:50}..."
        echo
        echo -e "${GREEN}✅ 自动启动6-Phase工作流${NC}"
        echo

        # 显示工作流概览
        echo -e "${BLUE}📋 工作流概览：${NC}"
        echo "┌─────────────────────────────────────────────────────┐"
        echo "│ Phase 1: 需求分析 - 理解任务，生成PLAN.md          │"
        echo "│ Phase 2: 设计规划 - 架构设计，创建骨架             │"
        echo "│ Phase 3: 实现开发 - 编码实现（多Agent并行）        │"
        echo "│ Phase 4: 本地测试 - 单元/集成/性能测试             │"
        echo "│ Phase 5: 代码提交 - Git提交，触发质量检查          │"
        echo "│ Phase 6: 代码审查 - PR审查，合并部署               │"
        echo "└─────────────────────────────────────────────────────┘"
        echo

        # 设置为Phase 1
        set_current_phase "P1"

        # 创建任务文件
        echo "$task_description" > "$PHASE_DIR/task.txt"
        echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$PHASE_DIR/start_time.txt"

        # 推荐Agent组合
        echo -e "${MAGENTA}🤖 推荐Agent组合（基于任务复杂度）：${NC}"

        # 分析任务复杂度
        local complexity="standard"
        if [[ "$task_description" == *"简单"* ]] || [[ "$task_description" == *"修复"* ]]; then
            complexity="simple"
        elif [[ "$task_description" == *"系统"* ]] || [[ "$task_description" == *"架构"* ]]; then
            complexity="complex"
        fi

        case "$complexity" in
            simple)
                echo "  • 简单任务（4个Agent）："
                echo "    - backend-architect（架构指导）"
                echo "    - test-engineer（测试验证）"
                echo "    - code-reviewer（代码审查）"
                echo "    - documentation-writer（文档更新）"
                ;;
            complex)
                echo "  • 复杂任务（8个Agent）："
                echo "    - backend-architect（整体架构）"
                echo "    - database-specialist（数据设计）"
                echo "    - security-auditor（安全审查）"
                echo "    - performance-engineer（性能优化）"
                echo "    - test-engineer（测试策略）"
                echo "    - api-designer（接口设计）"
                echo "    - code-reviewer（代码质量）"
                echo "    - documentation-writer（完整文档）"
                ;;
            *)
                echo "  • 标准任务（6个Agent）："
                echo "    - backend-architect（架构设计）"
                echo "    - database-specialist（数据层）"
                echo "    - test-engineer（测试覆盖）"
                echo "    - security-auditor（安全检查）"
                echo "    - code-reviewer（代码审查）"
                echo "    - documentation-writer（文档同步）"
                ;;
        esac
        echo

        # 下一步提示
        echo -e "${GREEN}📝 下一步行动：${NC}"
        echo "1. 开始Phase 1：创建 docs/PLAN.md"
        echo "2. 分析需求，列出任务清单"
        echo "3. 使用推荐的Agent组合并行执行"
        echo

        # 创建初始PLAN.md模板
        mkdir -p "$PROJECT_ROOT/docs"
        if [[ ! -f "$PROJECT_ROOT/docs/PLAN.md" ]]; then
            cat > "$PROJECT_ROOT/docs/PLAN.md" << 'EOF'
# 任务计划

## 任务描述
[任务描述]

## 任务清单
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3
- [ ] 任务4
- [ ] 任务5

## 受影响文件
- 文件1
- 文件2
- 文件3

## 技术方案
[技术实现方案]

## 测试计划
[测试策略]

## 回滚方案
[如何回滚]

## 风险评估
[潜在风险]

---
*生成时间：$(date '+%Y-%m-%d %H:%M:%S')*
EOF
            echo -e "${GREEN}✅ 已创建PLAN.md模板${NC}"
        fi

        return 0

    else
        # 已在工作流中，显示当前状态
        echo -e "${BLUE}📍 当前Phase: ${current_phase}${NC}"

        case "$current_phase" in
            P1)
                echo -e "${YELLOW}⏳ Phase 1进行中：需求分析${NC}"
                echo "  请完成 docs/PLAN.md"
                ;;
            P2)
                echo -e "${YELLOW}⏳ Phase 2进行中：设计规划${NC}"
                echo "  请创建架构骨架"
                ;;
            P3)
                echo -e "${YELLOW}⏳ Phase 3进行中：实现开发${NC}"
                echo "  使用多Agent并行开发"
                ;;
            P4)
                echo -e "${YELLOW}⏳ Phase 4进行中：本地测试${NC}"
                echo "  运行测试套件"
                ;;
            P5)
                echo -e "${YELLOW}⏳ Phase 5进行中：代码提交${NC}"
                echo "  Git提交和质量检查"
                ;;
            P6)
                echo -e "${YELLOW}⏳ Phase 6进行中：代码审查${NC}"
                echo "  PR审查和合并"
                ;;
        esac

        return 0
    fi
}

# 主函数
main() {
    local prompt="${1:-}"

    # 检查是否是编程任务
    if is_programming_task "$prompt"; then
        auto_start_workflow "$prompt"
    else
        # 非编程任务，直接通过
        echo -e "${GREEN}✓ 非编程任务，无需工作流${NC}"
    fi
}

# 执行主函数
main "$@"