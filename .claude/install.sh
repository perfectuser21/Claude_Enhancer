#!/bin/bash
# Claude Enhancer 安装脚本

echo "🚀 Claude Enhancer 安装"
echo "========================"

# 检查是否已有其他.claude配置
if [ -f ".claude/config/unified_main.yaml" ] && [ ! -f ".claude/WORKFLOW.md" ]; then
    echo "⚠️  检测到已存在其他.claude配置"
    echo "是否要备份现有配置？(y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        mv .claude .claude.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ 已备份到 .claude.backup.*"
    else
        echo "继续会覆盖现有配置，确定吗？(y/n)"
        read -r confirm
        if [[ "$confirm" != "y" ]]; then
            echo "❌ 安装取消"
            exit 1
        fi
    fi
fi

# 检查是否在git仓库
if [ ! -d .git ]; then
    echo "⚠️  警告：当前不是git仓库，Git Hooks将不会安装"
    echo "继续安装？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 0. 清理垃圾文件（可选）
echo "🧹 清理垃圾文件..."
if [ -f ".claude/scripts/cleanup.sh" ]; then
    bash .claude/scripts/cleanup.sh > /dev/null 2>&1
    echo "  ✅ 垃圾文件已清理"
else
    # 基础清理
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo "  ✅ 基础清理完成"
fi

# 1. 确保hooks有执行权限
echo "📝 设置执行权限..."
chmod +x .claude/hooks/*.sh 2>/dev/null
chmod +x .claude/scripts/*.sh 2>/dev/null

# 2. 安装Git Hooks（可选）
if [ -d .git ]; then
    echo "📌 安装Git Hooks..."

    # 备份现有hooks
    for hook in pre-commit commit-msg pre-push; do
        if [ -f .git/hooks/$hook ]; then
            cp .git/hooks/$hook .git/hooks/$hook.backup.$(date +%Y%m%d)
            echo "  备份: $hook → $hook.backup"
        fi
    done

    # 安装新hooks
    if [ -f .claude/git-hooks/pre-commit ]; then
        cp .claude/git-hooks/pre-commit .git/hooks/pre-commit
    fi
    if [ -f .claude/git-hooks/commit-msg ]; then
        cp .claude/git-hooks/commit-msg .git/hooks/commit-msg
    fi

    chmod +x .git/hooks/pre-commit 2>/dev/null
    chmod +x .git/hooks/commit-msg 2>/dev/null

    echo "  ✅ Git Hooks已安装"
fi

# 2.5 安装工作流硬闸（Workflow Guard）- 新增
echo "🛡️ 安装工作流硬闸..."
if [ -f setup_hooks.sh ]; then
    bash setup_hooks.sh > /dev/null 2>&1
    echo "  ✅ 工作流硬闸已激活"
    echo "  📝 使用: ce start \"任务\" 激活工作流"
fi

# 设置ce命令权限
if [ -f scripts/ce-start ] && [ -f scripts/ce-stop ]; then
    chmod +x scripts/ce-start scripts/ce-stop scripts/ce 2>/dev/null
    echo "  ✅ ce命令已就绪"
fi

# 3. 创建配置软链接（可选）
if [ ! -f .claude/config/unified_main.yaml ]; then
    echo "⚠️  未找到settings.json，跳过"
else
    echo "✅ Claude配置已就绪"
fi

# 4. 显示使用说明
echo ""
echo "✨ 安装完成！Claude Enhancer 5.3"
echo ""
echo "📋 核心功能："
echo "  1. 🤖 智能Agent选择（4-6-8策略）"
echo "  2. 🛡️ 工作流硬闸（强制执行标准流程）"
echo "  3. ✅ 三层质量保证（Workflow + Claude Hooks + Git Hooks）"
echo "  4. 📊 100/100保障力评分"
echo ""
echo "💡 快速开始："
echo "  1. ce start \"任务描述\" - 激活工作流"
echo "  2. 正常开发（git add/commit/push）"
echo "  3. ce stop - 完成后停用工作流"
echo ""
echo "🎯 8-Phase工作流（P0-P7）："
echo "  P0 探索 → P1 规划 → P2 骨架 → P3 实现"
echo "  P4 测试 → P5 审查 → P6 发布 → P7 监控"
echo ""
echo "📚 文档："
echo "  • 工作流硬闸: docs/WORKFLOW_GUARD.md"
echo "  • 系统架构: .claude/WORKFLOW.md"
echo "  • 项目说明: CLAUDE.md"
echo ""
echo "Happy coding with Claude Enhancer 5.3! 🚀"