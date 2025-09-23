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
    for hook in pre-commit commit-msg; do
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

# 3. 创建配置软链接（可选）
if [ ! -f .claude/config/unified_main.yaml ]; then
    echo "⚠️  未找到settings.json，跳过"
else
    echo "✅ Claude配置已就绪"
fi

# 4. 显示使用说明
echo ""
echo "✨ 安装完成！"
echo ""
echo "📋 使用方法："
echo "  1. Claude会自动分析任务并选择4-6-8个Agent"
echo "  2. Git提交时会自动检查代码质量"
echo "  3. 查看 .claude/README.md 了解详情"
echo ""
echo "💡 工作流程："
echo "  Phase 0-2: 需求分析和设计"
echo "  Phase 3: Agent并行开发"
echo "  Phase 4-7: 测试、提交、审查、部署"
echo ""
echo "🎯 Agent策略："
echo "  简单任务：4个Agent"
echo "  标准任务：6个Agent"
echo "  复杂任务：8个Agent"
echo ""
echo "Happy coding with Claude Enhancer! 🚀"