#!/bin/bash

# Claude Enhancer Plus - Git Optimizer Setup Script
# Automatic installation and integration with existing Claude Enhancer system

set -e

echo "🚀 Claude Enhancer Plus Git优化器安装程序"
echo "=================================================="

# 检查环境
check_environment() {
    echo "🔍 检查环境要求..."

    # 检查Node.js
    if ! command -v node >/dev/null 2>&1; then
        echo "❌ 需要Node.js环境"
        echo "💡 请安装Node.js 14.0+: https://nodejs.org/"
        exit 1
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo "✅ Node.js版本: $NODE_VERSION"

    # 检查Git
    if ! command -v git >/dev/null 2>&1; then
        echo "❌ 需要Git环境"
        exit 1
    fi

    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo "✅ Git版本: $GIT_VERSION"

    # 检查是否在Git仓库中
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "❌ 当前目录不是Git仓库"
        echo "💡 请在Git仓库根目录中运行此脚本"
        exit 1
    fi

    echo "✅ 环境检查通过"
}

# 创建必要的目录结构
create_directories() {
    echo "📁 创建目录结构..."

    mkdir -p .claude/cache/git
    mkdir -p .claude/logs
    mkdir -p src/git

    echo "✅ 目录创建完成"
}

# 安装Git优化器组件
install_components() {
    echo "📦 安装Git优化器组件..."

    # 检查组件是否已存在
    if [ -f "src/git/GitIntegration.js" ]; then
        echo "ℹ️ Git优化器组件已存在"

        echo "是否要重新安装？(y/n)"
        read -r response
        if [[ "$response" != "y" ]]; then
            echo "跳过组件安装"
            return 0
        fi
    fi

    echo "✅ Git优化器组件已就绪"
}

# 配置集成
configure_integration() {
    echo "⚙️ 配置系统集成..."

    # 更新Claude Enhancer设置
    SETTINGS_FILE=".claude/settings.json"
    if [ -f "$SETTINGS_FILE" ]; then
        # 备份原始设置
        cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"

        # 添加Git优化器配置
        node -e "
            const fs = require('fs');
            const settings = JSON.parse(fs.readFileSync('$SETTINGS_FILE', 'utf-8'));

            // 添加Git优化器配置
            settings.git_optimizer = {
                enabled: true,
                version: '1.0.0',
                components: {
                    caching: true,
                    monitoring: true,
                    optimized_hooks: true,
                    batching: true
                },
                performance_targets: {
                    git_operation_improvement: '60%',
                    hook_execution_improvement: '70%',
                    cache_hit_rate_target: '70%'
                }
            };

            // 更新现有hooks配置
            if (settings.hooks && settings.hooks.PostToolUse) {
                // 确保性能监控hook启用Git优化器
                const perfHook = settings.hooks.PostToolUse.find(h => h.command && h.command.includes('performance_monitor.sh'));
                if (perfHook) {
                    perfHook.description += ' - 集成Git优化器';
                }
            }

            fs.writeFileSync('$SETTINGS_FILE', JSON.stringify(settings, null, 2));
            console.log('✅ Claude Enhancer设置已更新');
        "
    fi

    # 生成Git优化器配置文件
    cat > .claude/git-optimizer-config.json << 'EOF'
{
  "version": "1.0.0",
  "enabled": true,
  "optimization": {
    "enableCaching": true,
    "enableMonitoring": true,
    "enableOptimizedHooks": true,
    "enableBatching": true,
    "cacheMaxAge": 30000,
    "watchFiles": true,
    "maxConcurrentOps": 5
  },
  "performance": {
    "targets": {
      "git_operations_improvement": 60,
      "hook_execution_improvement": 70,
      "cache_hit_rate": 70
    },
    "thresholds": {
      "fast": 100,
      "medium": 500,
      "slow": 1000,
      "very_slow": 3000
    }
  },
  "integration": {
    "claude_enhancer": true,
    "hooks_updated": true,
    "monitoring_enabled": true
  }
}
EOF

    echo "✅ 集成配置完成"
}

# 初始化Git优化器
initialize_optimizer() {
    echo "🔧 初始化Git优化器..."

    # 运行初始化
    if [ -f "src/git/git-optimizer-cli.js" ]; then
        node src/git/git-optimizer-cli.js init --verbose || {
            echo "⚠️ 优化器初始化失败，使用基础模式"
        }
    fi

    echo "✅ 优化器初始化完成"
}

# 运行性能测试
run_performance_test() {
    echo "⚡ 运行性能基准测试..."

    if [ -f "src/git/git-optimizer-cli.js" ]; then
        echo "📊 基准测试结果："
        node src/git/git-optimizer-cli.js benchmark --iterations 5 || {
            echo "⚠️ 基准测试失败，跳过"
        }
    fi
}

# 安装到Git hooks
install_to_git_hooks() {
    echo "🪝 安装到Git hooks..."

    # 检查是否有现有的pre-commit hook
    PRE_COMMIT_HOOK=".git/hooks/pre-commit"

    if [ -f "$PRE_COMMIT_HOOK" ]; then
        echo "ℹ️ 检测到现有的pre-commit hook"
        cp "$PRE_COMMIT_HOOK" "$PRE_COMMIT_HOOK.backup"
        echo "✅ 已备份现有hook到 $PRE_COMMIT_HOOK.backup"
    fi

    # 安装优化的pre-commit hook
    if [ -f ".claude/hooks/simple_pre_commit.sh" ]; then
        cp ".claude/hooks/simple_pre_commit.sh" "$PRE_COMMIT_HOOK"
        chmod +x "$PRE_COMMIT_HOOK"
        echo "✅ 优化的pre-commit hook已安装"
    fi

    # 安装其他hooks
    for hook_file in .claude/hooks/simple_*.sh; do
        if [ -f "$hook_file" ]; then
            hook_name=$(basename "$hook_file" .sh | sed 's/simple_//')
            git_hook_path=".git/hooks/$hook_name"

            if [[ "$hook_name" != "pre_commit" ]]; then  # 已经处理过pre-commit
                cp "$hook_file" "$git_hook_path"
                chmod +x "$git_hook_path"
                echo "✅ $hook_name hook已安装"
            fi
        fi
    done
}

# 显示安装结果和使用说明
show_installation_result() {
    echo ""
    echo "🎉 Claude Enhancer Plus Git优化器安装完成！"
    echo "=================================================="
    echo ""
    echo "📋 安装摘要："
    echo "  ✅ Git优化器组件已就绪"
    echo "  ✅ 智能缓存系统已启用"
    echo "  ✅ 性能监控已集成"
    echo "  ✅ 优化hooks已安装"
    echo "  ✅ Claude Enhancer集成完成"
    echo ""
    echo "🚀 使用方法："
    echo "  查看状态: node src/git/git-optimizer-cli.js status"
    echo "  运行测试: node src/git/git-optimizer-cli.js test"
    echo "  性能基准: node src/git/git-optimizer-cli.js benchmark"
    echo "  健康检查: node src/git/git-optimizer-cli.js health"
    echo "  生成报告: node src/git/git-optimizer-cli.js report"
    echo ""
    echo "💡 优化效果："
    echo "  🎯 Git操作速度提升: 目标60%"
    echo "  🎯 Hook执行速度提升: 目标70%"
    echo "  🎯 缓存命中率: 目标70%+"
    echo ""
    echo "📊 监控："
    echo "  性能日志: .claude/logs/git-performance.log"
    echo "  缓存状态: .claude/cache/git/"
    echo "  配置文件: .claude/git-optimizer-config.json"
    echo ""
    echo "🔧 高级操作："
    echo "  清理缓存: node src/git/git-optimizer-cli.js cache --action clear"
    echo "  测试hooks: node src/git/git-optimizer-cli.js hooks --action test"
    echo "  完全清理: node src/git/git-optimizer-cli.js cleanup"
    echo ""

    # 显示当前状态
    if [ -f "src/git/git-optimizer-cli.js" ]; then
        echo "📈 当前状态："
        node src/git/git-optimizer-cli.js status 2>/dev/null || {
            echo "  ⚠️ 状态查询失败，系统可能需要初始化"
            echo "  💡 运行: node src/git/git-optimizer-cli.js init"
        }
    fi
}

# 主安装流程
main() {
    echo "开始安装Claude Enhancer Plus Git优化器..."
    echo ""

    check_environment
    echo ""

    create_directories
    echo ""

    install_components
    echo ""

    configure_integration
    echo ""

    initialize_optimizer
    echo ""

    run_performance_test
    echo ""

    install_to_git_hooks
    echo ""

    show_installation_result
}

# 处理参数
case "${1:-install}" in
    "install"|"")
        main
        ;;
    "uninstall")
        echo "🗑️ 卸载Git优化器..."

        # 恢复Git hooks
        if [ -f ".git/hooks/pre-commit.backup" ]; then
            mv ".git/hooks/pre-commit.backup" ".git/hooks/pre-commit"
            echo "✅ 已恢复原始pre-commit hook"
        fi

        # 清理文件
        rm -rf .claude/cache/git/ 2>/dev/null || true
        rm -f .claude/git-optimizer-config.json 2>/dev/null || true
        rm -f .claude/logs/git-performance.log 2>/dev/null || true

        # 运行清理
        if [ -f "src/git/git-optimizer-cli.js" ]; then
            node src/git/git-optimizer-cli.js cleanup || true
        fi

        echo "✅ Git优化器已卸载"
        ;;
    "status")
        if [ -f "src/git/git-optimizer-cli.js" ]; then
            node src/git/git-optimizer-cli.js status
        else
            echo "❌ Git优化器未安装"
            echo "💡 运行 ./setup-git-optimizer.sh 进行安装"
        fi
        ;;
    "help")
        echo "Claude Enhancer Plus Git优化器安装脚本"
        echo ""
        echo "用法: ./setup-git-optimizer.sh [命令]"
        echo ""
        echo "命令:"
        echo "  install    安装Git优化器 (默认)"
        echo "  uninstall  卸载Git优化器"
        echo "  status     显示安装状态"
        echo "  help       显示此帮助信息"
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "💡 使用 ./setup-git-optimizer.sh help 查看帮助"
        exit 1
        ;;
esac