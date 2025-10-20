#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - Branch强制检查（规则0：Phase 1 - Branch Check）
# 版本：3.0 - 100%强制执行模式（无条件硬阻止）
# 修复日期：2025-10-15
# 修复原因：之前的EXECUTION_MODE检测不可靠，导致50%违规率

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [branch_helper.sh v3.0] triggered by ${USER:-claude}" >> "$LOG_FILE"

# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# 如果不在git仓库，直接退出
if [[ -z "$current_branch" ]]; then
    echo "ℹ️  不在Git仓库中，跳过分支检查" >&2
    exit 0
fi

# ============================================
# 版本3.0重大改变：无条件硬阻止main/master分支
# 删除不可靠的EXECUTION_MODE检测逻辑
# 任何对main/master分支的Write/Edit操作都被阻止
# ============================================

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
    echo "🚀 Claude Enhancer工作流（Phase 1 → P7）：" >&2
    echo "  Phase  1: 分支准备 ← 你在这里" >&2
    echo "  Phase  2: 探索发现" >&2
    echo "  Phase  3: 需求规划+架构设计" >&2
    echo "  Phase  4: 编码实现" >&2
    echo "  Phase  5: 测试验证（质量门禁1）" >&2
    echo "  Phase  6: 代码审查（质量门禁2）" >&2
    echo "  Phase  7: 发布部署+监控运维" >&2
    echo "" >&2
}

# ============================================
# 主逻辑 - 版本3.0: 无条件硬阻止
# ============================================

if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    # 检测到main/master分支 - 无条件处理（不依赖EXECUTION_MODE）

    # 优先级1: 自动创建分支（如果启用）
    if [[ "${CE_AUTO_CREATE_BRANCH:-true}" == "true" ]]; then
        # 默认启用自动创建！（改为true）
        date_str=$(date +%Y%m%d-%H%M%S)
        new_branch="feature/auto-${date_str}"

        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "" >&2
            echo "🤖 Claude Enhancer - 自动创建分支（v3.0）" >&2
            echo "═══════════════════════════════════════════" >&2
            echo "" >&2
            echo "📍 检测到在 $current_branch 分支" >&2
            echo "🚀 自动创建新分支: $new_branch" >&2
            echo "💡 规则0: 新任务 = 新分支 (100%强制)" >&2
            echo "" >&2
        fi

        # 创建并切换到新分支
        if git checkout -b "$new_branch" 2>/dev/null; then
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "✅ 成功创建并切换到: $new_branch" >&2
                echo "✅ 现在可以安全开始Phase 2-7工作流" >&2
                echo "" >&2
            fi
            echo "$(date +'%F %T') [branch_helper.sh v3.0] AUTO-CREATED: $new_branch from $current_branch" >> "$LOG_FILE"
            # 成功创建，继续执行
            exit 0
        else
            echo "❌ 自动创建分支失败" >&2
            # 继续执行到硬阻止逻辑
        fi
    fi

    # 优先级2: 硬阻止（自动创建失败或被禁用）
    echo "" >&2
    echo "🚨 Claude Enhancer - 分支检查失败（v3.0）" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "❌ 错误：禁止在 $current_branch 分支上修改文件" >&2
    echo "" >&2
    echo "📋 规则0：新任务 = 新分支（100%强制执行）" >&2
    echo "" >&2
    echo "🔧 解决方案：" >&2
    echo "  1. AI必须先创建feature分支：" >&2
    echo "     git checkout -b feature/任务描述" >&2
    echo "" >&2
    echo "  2. 或启用自动创建（默认已启用）：" >&2
    echo "     export CE_AUTO_CREATE_BRANCH=true" >&2
    echo "" >&2
    echo "📝 分支命名示例：" >&2
    echo "  • feature/release-automation" >&2
    echo "  • feature/add-user-auth" >&2
    echo "  • bugfix/fix-tag-issue" >&2
    echo "" >&2
    echo "💡 这是100%强制规则，不是建议！" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2

    # 记录阻止日志
    echo "$(date +'%F %T') [branch_helper.sh v3.0] HARD-BLOCKED: attempt to modify on $current_branch" >> "$LOG_FILE"

    # 硬阻止 - exit 1
    exit 1
else
    # 在feature分支上 - 允许操作
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "✅ 分支检查通过: $current_branch" >&2
    fi
    echo "$(date +'%F %T') [branch_helper.sh v3.0] PASSED: on branch $current_branch" >> "$LOG_FILE"
fi

exit 0
