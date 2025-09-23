#!/bin/bash
# Claude Enhancer 智能Agent选择器 (4-6-8策略)
# 使用统一配置系统

set -e

# 配置文件路径
CONFIG_FILE="${PERFECT21_CONFIG:-$(dirname "$(dirname "$0")"/config/unified_main.yaml}"
CONFIG_LOADER="$(dirname "$(dirname "$0")"/scripts/load_config.sh"

# 加载配置
if [[ -f "$CONFIG_LOADER" ]]; then
    CONFIG_FILE="$($CONFIG_LOADER load 2>/dev/null || echo "$CONFIG_FILE")"
fi

# 读取输入
INPUT=$(cat)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
if [ -z "$TASK_DESC" ]; then
    TASK_DESC=$(echo "$INPUT" | grep -oP '"description"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
fi

# 转换为小写便于匹配
TASK_LOWER=$(echo "$TASK_DESC" | tr '[:upper:]' '[:lower:]')

# 判定任务复杂度
determine_complexity() {
    local desc="$1"

    # 复杂任务关键词 (8 agents)
    if echo "$desc" | grep -qE "architect|design system|integrate|migrate|refactor entire|complex|全栈|架构|重构整个|复杂"; then
        echo "complex"
        return
    fi

    # 简单任务关键词 (4 agents)
    if echo "$desc" | grep -qE "fix bug|typo|minor|quick|simple|small change|修复bug|小改动|简单|快速"; then
        echo "simple"
        return
    fi

    # 默认标准任务 (6 agents)
    echo "standard"
}

# 获取推荐的Agent组合
get_agent_combination() {
    local complexity="$1"
    local task="$2"
    local phase="$3"  # 添加phase参数

    case "$complexity" in
        simple)
            echo "4个Agent组合："
            echo "  1. backend-engineer - 实现修复"
            echo "  2. test-engineer - 验证测试"
            echo "  3. code-reviewer - 代码审查"
            echo "  4. technical-writer - 更新文档"
            if [ "$phase" = "5" ] || [ "$phase" = "7" ]; then
                echo "  + cleanup-specialist - 自动清理"
            fi
            ;;
        complex)
            echo "8个Agent组合："
            echo "  1. backend-architect - 系统架构"
            echo "  2. api-designer - API设计"
            echo "  3. database-specialist - 数据模型"
            echo "  4. backend-engineer - 核心实现"
            echo "  5. security-auditor - 安全审计"
            echo "  6. test-engineer - 全面测试"
            echo "  7. performance-engineer - 性能优化"
            echo "  8. technical-writer - 完整文档"
            if [ "$phase" = "5" ] || [ "$phase" = "7" ]; then
                echo "  + cleanup-specialist - 自动清理"
            fi
            ;;
        *)
            echo "6个Agent组合："
            echo "  1. backend-architect - 方案设计"
            echo "  2. backend-engineer - 功能实现"
            echo "  3. test-engineer - 质量保证"
            echo "  4. security-auditor - 安全检查"

            # 根据任务特点选择第5、6个Agent
            if echo "$task" | grep -qE "api|接口|endpoint"; then
                echo "  5. api-designer - API规范"
            elif echo "$task" | grep -qE "数据|database|sql"; then
                echo "  5. database-specialist - 数据设计"
            else
                echo "  5. code-reviewer - 代码质量"
            fi
            echo "  6. technical-writer - 文档编写"
            if [ "$phase" = "5" ] || [ "$phase" = "7" ]; then
                echo "  + cleanup-specialist - 自动清理"
            fi
            ;;
    esac
}

# 主逻辑
if [ -n "$TASK_DESC" ]; then
    # 判定复杂度
    COMPLEXITY=$(determine_complexity "$TASK_LOWER")

    # 输出分析结果
    echo "🤖 Claude Enhancer Agent智能选择 (4-6-8策略)" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "📝 任务: $(echo "$TASK_DESC" | head -c 80)..." >&2
    echo "" >&2

    # 复杂度判定
    case "$COMPLEXITY" in
        simple)
            echo "📊 复杂度: 🟢 简单任务" >&2
            echo "⚡ 执行模式: 快速模式 (4 Agents)" >&2
            echo "⏱️  预计时间: 5-10分钟" >&2
            ;;
        complex)
            echo "📊 复杂度: 🔴 复杂任务" >&2
            echo "💎 执行模式: 全面模式 (8 Agents)" >&2
            echo "⏱️  预计时间: 25-30分钟" >&2
            ;;
        *)
            echo "📊 复杂度: 🟡 标准任务" >&2
            echo "⚖️  执行模式: 平衡模式 (6 Agents)" >&2
            echo "⏱️  预计时间: 15-20分钟" >&2
            ;;
    esac

    echo "" >&2
    echo "👥 推荐Agent组合:" >&2
    get_agent_combination "$COMPLEXITY" "$TASK_LOWER" "$CURRENT_PHASE" | sed 's/^/  /' >&2
    echo "" >&2

    # 检查是否需要cleanup-specialist
    CURRENT_PHASE=$(echo "$INPUT" | grep -oP '"phase"\s*:\s*\d+' | grep -oP '\d+' || echo "")
    if [ "$CURRENT_PHASE" = "5" ] || [ "$CURRENT_PHASE" = "7" ]; then
        echo "🧹 清理专家: cleanup-specialist 已自动加入" >&2
        echo "" >&2
    fi

    # 工作流提醒
    echo "📋 工作流程 (8 Phases):" >&2
    echo "  Phase 0: Git分支 ✓" >&2
    echo "  Phase 1: 需求分析 ← 当前" >&2
    echo "  Phase 2: 设计规划" >&2
    echo "  Phase 3: 实现开发 (多Agent并行)" >&2
    echo "  Phase 4: 本地测试" >&2
    echo "  Phase 5: 代码提交 🧹" >&2
    echo "  Phase 6: 代码审查" >&2
    echo "  Phase 7: 合并部署 🧹" >&2
    echo "" >&2

    echo "💡 Max 20X: 质量优先，Token不限" >&2
    echo "═══════════════════════════════════════════" >&2

    # 记录到日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Complexity: $COMPLEXITY, Task: ${TASK_DESC:0:50}" >> /tmp/claude_agent_selection.log
fi

# 输出原始内容
echo "$INPUT"
exit 0