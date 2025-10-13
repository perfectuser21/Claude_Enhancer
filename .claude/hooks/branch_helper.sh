#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - Branch强制检查（规则0：Phase -1）
# 版本：2.0 - 升级为强制执行模式

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [branch_helper.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# 如果不在git仓库，直接退出
if [[ -z "$current_branch" ]]; then
    echo "ℹ️  不在Git仓库中，跳过分支检查" >&2
    exit 0
fi

# 检查是否在执行模式
# 执行模式通过以下方式判断：
# 1. 环境变量 CE_EXECUTION_MODE=true
# 2. 正在使用Write/Edit工具（通过TOOL_NAME判断）
# 3. .workflow/ACTIVE 文件存在
EXECUTION_MODE=false

if [[ "$CE_EXECUTION_MODE" == "true" ]] || \
   [[ "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]] || \
   [[ -f "$PROJECT_ROOT/.workflow/ACTIVE" ]]; then
    EXECUTION_MODE=true
fi

# 定义分支检查函数
check_branch_suitable() {
    local branch="$1"

    # 主分支检查
    if [[ "$branch" == "main" ]] || [[ "$branch" == "master" ]]; then
        return 1  # 不适合
    fi

    # 可以添加更多检查逻辑
    # 例如：检查分支名是否符合规范等

    return 0  # 适合
}

# 显示友好提示
show_branch_guidance() {
    echo "🌿 Claude Enhancer 分支指导" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "📍 当前分支: $current_branch" >&2
    echo "" >&2
    echo "💡 建议创建feature分支开发：" >&2
    echo "  git checkout -b feature/your-feature" >&2
    echo "" >&2
    echo "📝 分支命名规范：" >&2
    echo "  • feature/xxx - 新功能开发" >&2
    echo "  • bugfix/xxx - Bug修复" >&2
    echo "  • perf/xxx - 性能优化" >&2
    echo "  • docs/xxx - 文档更新" >&2
    echo "  • experiment/xxx - 实验性改动" >&2
    echo "" >&2
    echo "🚀 Claude Enhancer工作流（Phase -1 → P7）：" >&2
    echo "  Phase -1: 分支准备 ← 你在这里" >&2
    echo "  Phase  0: 探索发现" >&2
    echo "  Phase  1: 需求规划" >&2
    echo "  Phase  2: 架构设计" >&2
    echo "  Phase  3: 编码实现" >&2
    echo "  Phase  4: 测试验证" >&2
    echo "  Phase  5: 代码审查" >&2
    echo "  Phase  6: 发布部署" >&2
    echo "  Phase  7: 监控运维" >&2
    echo "" >&2
}

# 主逻辑
if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    if [[ "$EXECUTION_MODE" == "true" ]]; then
        # 检查是否启用自动创建分支
        if [[ "${CE_AUTO_CREATE_BRANCH:-false}" == "true" ]]; then
            # 自动创建分支模式
            # FIX: Remove 'local' outside functions (SC2168)
            date_str=$(date +%Y%m%d-%H%M%S)
            new_branch="feature/auto-${date_str}"

            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "" >&2
                echo "🌿 Claude Enhancer - 自动创建分支" >&2
                echo "═══════════════════════════════════════════" >&2
                echo "" >&2
                echo "📍 检测到在 $current_branch 分支" >&2
                echo "🚀 自动创建新分支: $new_branch" >&2
                echo "" >&2
            fi

            # 创建并切换到新分支
            if git checkout -b "$new_branch" 2>/dev/null; then
                if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                    echo "✅ 成功创建并切换到: $new_branch" >&2
                    echo "" >&2
                fi
                echo "$(date +'%F %T') [branch_helper.sh] AUTO-CREATED: $new_branch from $current_branch" >> "$LOG_FILE"
                # 成功创建，继续执行
                exit 0
            else
                echo "❌ 自动创建分支失败，请手动创建" >&2
                exit 1
            fi
        else
            # 执行模式：硬阻止
            echo "" >&2
            echo "🚨 Claude Enhancer - 分支检查失败" >&2
            echo "═══════════════════════════════════════════" >&2
            echo "" >&2
            echo "❌ 错误：不能在 $current_branch 分支上直接修改文件" >&2
            echo "" >&2
            echo "📋 规则0：新任务 = 新分支（强制执行）" >&2
            echo "" >&2
            echo "🔧 解决方案：" >&2
            echo "  1. 创建新的feature分支：" >&2
            echo "     git checkout -b feature/任务描述" >&2
            echo "" >&2
            echo "  2. 或启用自动创建：export CE_AUTO_CREATE_BRANCH=true" >&2
            echo "" >&2
            echo "📝 分支命名示例：" >&2
            echo "  • feature/add-user-auth" >&2
            echo "  • feature/multi-terminal-workflow" >&2
            echo "  • bugfix/fix-login-error" >&2
            echo "" >&2
            echo "═══════════════════════════════════════════" >&2
            echo "" >&2

            # 记录阻止日志
            echo "$(date +'%F %T') [branch_helper.sh] BLOCKED: attempt to modify on $current_branch" >> "$LOG_FILE"

            # 硬阻止
            exit 1
        fi
    else
        # 非执行模式：友好提示
        show_branch_guidance
        echo "ℹ️  这是提示信息，不会阻止操作" >&2
        echo "═══════════════════════════════════════════" >&2
    fi
else
    # 在feature分支上
    if [[ "$EXECUTION_MODE" == "true" ]]; then
        echo "✅ 分支检查通过: $current_branch" >&2
        echo "$(date +'%F %T') [branch_helper.sh] PASSED: on branch $current_branch" >> "$LOG_FILE"
    else
        echo "🌿 当前分支: $current_branch" >&2
        echo "✅ 可以开始开发" >&2
    fi
fi

exit 0
