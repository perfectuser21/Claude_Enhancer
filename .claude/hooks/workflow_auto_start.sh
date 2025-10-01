#!/bin/bash
# Claude Enhancer 工作流自动启动器
# 真正的Phase 0：自动分支创建和工作流启动

set -euo pipefail

# 设置UTF-8支持
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

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
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"

# 创建必要目录
mkdir -p "$PHASE_DIR" "$WORKFLOW_DIR/logs"

# ==================== 核心功能：执行触发检测 ====================
# 只检测明确的"开始执行"触发词

is_execution_trigger() {
    local prompt="${1:-}"

    # 明确的执行触发词（5个）
    local execution_triggers=(
        "现在开始实现"
        "现在开始执行"
        "开始工作流"
        "let's implement"
        "let's start"
    )

    # 标准化输入
    local normalized="${prompt//：/:}"
    normalized="${normalized//，/,}"
    normalized="${normalized//。/.}"
    normalized="${normalized,,}"  # 转小写

    # 检查触发词
    for trigger in "${execution_triggers[@]}"; do
        if [[ "$normalized" == *"${trigger,,}"* ]]; then
            echo "$(date +'%F %T') [workflow_auto_start] Execution triggered by: $trigger" >> "$WORKFLOW_DIR/logs/hooks.log"
            return 0
        fi
    done

    return 1
}

# ==================== 智能分支命名系统 ====================

# 从任务描述生成slug
generate_task_slug() {
    local description="$1"

    # 提取关键词（中英文）
    local slug=$(echo "$description" | \
        # 移除触发词
        sed -E 's/(现在开始实现|现在开始执行|开始工作流|let'\''s implement|let'\''s start)//gi' | \
        # 提取前5个有意义的词
        grep -oE '[a-zA-Z0-9\u4e00-\u9fa5]+' | head -5 | \
        # 转为小写并用-连接
        tr '[:upper:]' '[:lower:]' | tr '\n' '-' | sed 's/-$//')

    # 如果为空，使用默认值
    if [[ -z "$slug" ]]; then
        slug="task"
    fi

    echo "$slug"
}

# 检测任务类型（Phase）
detect_task_phase() {
    local description="$1"
    local normalized="${description,,}"

    # 规划类任务 → P1
    if [[ "$normalized" =~ (规划|计划|分析|设计文档|需求) ]]; then
        echo "P1"
        return
    fi

    # 骨架类任务 → P2
    if [[ "$normalized" =~ (架构|骨架|结构|框架设计) ]]; then
        echo "P2"
        return
    fi

    # 实现类任务 → P3（默认）
    if [[ "$normalized" =~ (实现|开发|编写|创建|修复|优化|重构) ]]; then
        echo "P3"
        return
    fi

    # 测试类任务 → P4
    if [[ "$normalized" =~ (测试|验证|检查) ]]; then
        echo "P4"
        return
    fi

    # 默认P3
    echo "P3"
}

# 自动创建分支
auto_create_branch() {
    local description="$1"

    # 检查是否已在feature分支
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        echo -e "${GREEN}✅ 已在分支: $current_branch${NC}"
        return 0
    fi

    # 生成分支名
    local phase=$(detect_task_phase "$description")
    local slug=$(generate_task_slug "$description")
    local date_str=$(date +%Y%m%d)
    local branch_name="${phase}/${date_str}-${slug}"

    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          🚀 Phase 0: 自动创建工作分支                    ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}📍 任务描述：${NC}${description:0:60}..."
    echo -e "${BLUE}🎯 检测Phase：${NC}${phase}"
    echo -e "${BLUE}🌿 分支名称：${NC}${branch_name}"
    echo

    # 创建并切换分支
    if git checkout -b "$branch_name" 2>/dev/null; then
        echo -e "${GREEN}✅ 成功创建分支：$branch_name${NC}"
        echo

        # 记录Phase（ACTIVE需要完整格式）
        echo "$phase" > "$PHASE_DIR/current"
        cat > "$WORKFLOW_DIR/ACTIVE" << EOF
phase: $phase
ticket: auto-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Auto created branch: $branch_name (Phase: $phase)" >> "$PHASE_DIR/history"

        return 0
    else
        echo -e "${RED}❌ 创建分支失败${NC}"
        return 1
    fi
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

    # ACTIVE需要完整格式
    cat > "$WORKFLOW_DIR/ACTIVE" << EOF
phase: $phase
ticket: manual-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

    echo "$(date '+%Y-%m-%d %H:%M:%S') - $phase" >> "$PHASE_DIR/history"
}

# ==================== 主函数：智能工作流启动 ====================

main() {
    local prompt="${1:-}"

    # 检查是否触发执行模式
    if is_execution_trigger "$prompt"; then
        echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║          🚀 Claude Enhancer 执行模式启动                 ║${NC}"
        echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
        echo

        # Phase 0: 自动创建分支
        if auto_create_branch "$prompt"; then
            local phase=$(get_current_phase)

            # 显示工作流概览
            echo -e "${BLUE}📋 8-Phase工作流：${NC}"
            echo "┌─────────────────────────────────────────────────────┐"
            echo "│ ✅ P0: 分支创建 - 已完成                            │"
            echo "│ P1: 规划 - 需求分析，生成PLAN.md                   │"
            echo "│ P2: 骨架 - 架构设计，创建目录结构                  │"
            echo "│ P3: 实现 - 编码开发（多Agent并行）                 │"
            echo "│ P4: 测试 - 单元/集成/性能/BDD测试                  │"
            echo "│ P5: 审查 - 代码审查，生成REVIEW.md                 │"
            echo "│ P6: 发布 - 文档更新，打tag，健康检查               │"
            echo "│ P7: 监控 - 生产监控，SLO跟踪                       │"
            echo "└─────────────────────────────────────────────────────┘"
            echo

            # 推荐Agent策略
            echo -e "${MAGENTA}🤖 Agent策略（4-6-8原则）：${NC}"
            local complexity="standard"
            if [[ "$prompt" =~ (简单|修复|bug) ]]; then
                complexity="simple"
            elif [[ "$prompt" =~ (系统|架构|复杂|完整) ]]; then
                complexity="complex"
            fi

            case "$complexity" in
                simple)
                    echo "  • 简单任务（4个Agent）："
                    echo "    - backend-architect, test-engineer"
                    echo "    - code-reviewer, documentation-writer"
                    ;;
                complex)
                    echo "  • 复杂任务（8个Agent）："
                    echo "    - backend-architect, database-specialist"
                    echo "    - security-auditor, performance-engineer"
                    echo "    - test-engineer, api-designer"
                    echo "    - code-reviewer, documentation-writer"
                    ;;
                *)
                    echo "  • 标准任务（6个Agent）："
                    echo "    - backend-architect, database-specialist"
                    echo "    - test-engineer, security-auditor"
                    echo "    - code-reviewer, documentation-writer"
                    ;;
            esac
            echo

            # 下一步提示
            echo -e "${GREEN}📝 下一步：${NC}"
            if [[ "$phase" == "P1" ]]; then
                echo "1. 创建 docs/PLAN.md（需求分析）"
                echo "2. 使用推荐的Agent组合并行执行"
            else
                echo "1. 当前Phase: $phase"
                echo "2. 使用推荐的Agent组合并行执行"
            fi
            echo

            return 0
        else
            echo -e "${RED}❌ 工作流启动失败${NC}"
            return 1
        fi
    else
        # 非执行触发词，保持讨论模式
        # 静默通过，不输出任何信息
        return 0
    fi
}

# 执行主函数
main "$@"