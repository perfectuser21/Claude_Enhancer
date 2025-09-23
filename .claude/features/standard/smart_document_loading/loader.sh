#!/bin/bash

# Claude Enhancer智能文档加载器
# 根据任务内容智能决定加载哪些文档，避免上下文污染

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取输入参数
TASK_DESCRIPTION="${1:-}"
CURRENT_PHASE="${2:-3}"  # 默认Phase 3
MAX_TOKENS="${3:-20000}"

# Phase验证（修复Bug：限制范围0-7）
if ! [[ "$CURRENT_PHASE" =~ ^[0-7]$ ]]; then
    echo -e "${YELLOW}⚠️ 警告: Phase必须在0-7之间，使用默认值3${NC}" >&2
    CURRENT_PHASE=3
fi

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
ARCH_DIR="$CLAUDE_DIR/ARCHITECTURE"

# 初始化变量
DOCUMENTS_TO_LOAD=()
ESTIMATED_TOKENS=0
LOAD_REASON=""

# 辅助函数：添加文档到加载列表
add_document() {
    local doc="$1"
    local tokens="$2"
    local reason="$3"

    # 检查是否已经在列表中
    for loaded in "${DOCUMENTS_TO_LOAD[@]}"; do
        if [[ "$loaded" == "$doc" ]]; then
            return 0
        fi
    done

    # 检查Token预算
    local new_total=$((ESTIMATED_TOKENS + tokens))
    if [[ $new_total -le $MAX_TOKENS ]]; then
        DOCUMENTS_TO_LOAD+=("$doc")
        ESTIMATED_TOKENS=$new_total
        LOAD_REASON="${LOAD_REASON}\n  • $doc ($reason, ~${tokens} tokens)"
    else
        echo -e "${YELLOW}⚠️ Token预算不足，跳过: $doc${NC}" >&2
    fi
}

echo -e "${BLUE}🤖 Claude Enhancer智能文档加载器${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: 始终加载P0级核心文档
echo -e "\n${GREEN}Step 1: 加载核心文档 (P0级)${NC}"
add_document "CLAUDE.md" 2000 "核心配置"
add_document ".claude/settings.json" 500 "系统设置"

# Step 2: 分析任务描述，识别关键词
echo -e "\n${GREEN}Step 2: 分析任务内容${NC}"
echo "任务: $TASK_DESCRIPTION"
echo "当前Phase: $CURRENT_PHASE"

# 关键词检测
if [[ "$TASK_DESCRIPTION" =~ (新功能|new feature|添加|add|feature|功能) ]]; then
    echo "  ✓ 检测到: 新功能开发"
    add_document "$ARCH_DIR/GROWTH-STRATEGY.md" 6000 "新功能策略"
    add_document "$ARCH_DIR/NAMING-CONVENTIONS.md" 4000 "命名规范"
fi

if [[ "$TASK_DESCRIPTION" =~ (重构|refactor|架构|architecture|structure) ]]; then
    echo "  ✓ 检测到: 架构/重构"
    add_document "$ARCH_DIR/v2.0-FOUNDATION.md" 5000 "架构基础"
    add_document "$ARCH_DIR/LAYER-DEFINITION.md" 8000 "层级定义"
fi

if [[ "$TASK_DESCRIPTION" =~ (命名|naming|文件名|变量) ]]; then
    echo "  ✓ 检测到: 命名相关"
    add_document "$ARCH_DIR/NAMING-CONVENTIONS.md" 4000 "命名规范"
fi

if [[ "$TASK_DESCRIPTION" =~ (为什么|why|决策|decision) ]]; then
    echo "  ✓ 检测到: 决策查询"
    # 修复：正确处理decisions目录下的多个文件
    for decision in "$ARCH_DIR"/decisions/*.md; do
        if [ -f "$decision" ]; then
            add_document "$decision" 1000 "决策记录"
            break  # 暂时只加载第一个，避免Token过多
        fi
    done
fi

if [[ "$TASK_DESCRIPTION" =~ (agent|Agent|4-6-8) ]]; then
    echo "  ✓ 检测到: Agent策略"
    add_document "$CLAUDE_DIR/AGENT_STRATEGY.md" 3000 "Agent策略"
fi

if [[ "$TASK_DESCRIPTION" =~ (workflow|工作流|phase|阶段) ]]; then
    echo "  ✓ 检测到: 工作流"
    add_document "$CLAUDE_DIR/WORKFLOW.md" 4000 "工作流程"
fi

if [[ "$TASK_DESCRIPTION" =~ (哪层|layer|层级|放哪里|where) ]]; then
    echo "  ✓ 检测到: 层级查询"
    add_document "$ARCH_DIR/LAYER-DEFINITION.md" 8000 "层级定义"
fi

# Step 3: 根据Phase加载
echo -e "\n${GREEN}Step 3: Phase相关文档${NC}"
case $CURRENT_PHASE in
    0)
        echo "  Phase 0: 分支创建 (最小文档集)"
        ;;
    1|2)
        echo "  Phase 1-2: 分析设计"
        add_document "$ARCH_DIR/v2.0-FOUNDATION.md" 5000 "设计阶段"
        ;;
    3)
        echo "  Phase 3: 开发实现"
        if [[ ${#DOCUMENTS_TO_LOAD[@]} -lt 4 ]]; then
            add_document "$ARCH_DIR/GROWTH-STRATEGY.md" 6000 "开发指导"
        fi
        ;;
    4|5)
        echo "  Phase 4-5: 测试提交"
        add_document "$CLAUDE_DIR/WORKFLOW.md" 4000 "测试流程"
        ;;
    6|7)
        echo "  Phase 6-7: 审查部署 (最小文档集)"
        ;;
esac

# Step 4: 输出加载计划
echo -e "\n${GREEN}━━━ 文档加载计划 ━━━${NC}"
echo -e "${BLUE}将加载以下文档:${NC}"
echo -e "$LOAD_REASON"

echo -e "\n${BLUE}统计信息:${NC}"
echo "  • 文档数量: ${#DOCUMENTS_TO_LOAD[@]}"
echo "  • 预计Tokens: ${ESTIMATED_TOKENS}/${MAX_TOKENS}"
echo "  • 使用率: $(( ESTIMATED_TOKENS * 100 / MAX_TOKENS ))%"

# Step 5: 生成加载命令（供Claude Code使用）
echo -e "\n${GREEN}━━━ 建议的加载命令 ━━━${NC}"
echo "Claude Code应该按以下顺序读取文档:"
echo ""

for doc in "${DOCUMENTS_TO_LOAD[@]}"; do
    if [[ "$doc" == *.json ]]; then
        echo "Read: $doc"
    elif [[ "$doc" == *.md ]]; then
        # 对于Markdown文档，可以选择性读取
        if [[ $ESTIMATED_TOKENS -gt 15000 ]]; then
            echo "Read: $doc (limit: 100 lines)"
        else
            echo "Read: $doc"
        fi
    fi
done

# Step 6: 优化建议
if [[ $ESTIMATED_TOKENS -gt 25000 ]]; then
    echo -e "\n${YELLOW}⚠️ 警告: Token使用较高，建议:${NC}"
    echo "  1. 考虑分阶段加载文档"
    echo "  2. 使用摘要版本替代完整文档"
    echo "  3. 明确任务范围，减少不必要的文档"
elif [[ $ESTIMATED_TOKENS -lt 5000 ]]; then
    echo -e "\n${GREEN}✅ Token使用优化良好${NC}"
fi

# Step 7: 缓存提示
echo -e "\n${BLUE}💡 提示:${NC}"
echo "  • 已加载的文档会在会话中缓存"
echo "  • 如需强制重新评估，添加 --force 参数"
echo "  • 使用 --minimal 只加载P0级文档"

# 返回文档列表（用于脚本集成）
if [[ "$4" == "--json" ]]; then
    echo -e "\n{\"documents\": ["
    first=true
    for doc in "${DOCUMENTS_TO_LOAD[@]}"; do
        if [[ "$first" != true ]]; then echo -n ", "; fi
        echo -n "\"$doc\""
        first=false
    done
    echo "], \"tokens\": $ESTIMATED_TOKENS}"
fi

exit 0