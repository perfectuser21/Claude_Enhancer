#!/usr/bin/env bash
# ============================================
# Claude Enhancer 完全自动化环境变量
# ============================================
# 用途: 启用 Claude Code Bypass Permissions Mode
# 使用: source .claude/env.sh
# 或添加到 ~/.bashrc / ~/.zshrc

# 🎯 完全自动化核心配置
export CE_AUTO_CONFIRM=true                      # 自动确认所有提示
export CLAUDE_CODE_BYPASS_PERMISSIONS=true       # Bypass权限检查
export CE_SILENT_MODE=false                      # 保持输出（用于调试）

# 📋 Claude Enhancer 工作流配置
export CE_WORKFLOW_ENABLED=true                  # 启用8-Phase工作流
export CE_AUTO_AGENT_SELECT=true                 # 自动Agent选择
export CE_PARALLEL_EXECUTION=true                # 并行执行优化

# 🔧 Git 和开发工具配置
export GIT_HOOKS_AUTO_MODE=true                  # Git hooks自动模式
export CE_COMPACT_OUTPUT=false                   # 详细输出模式

# 🎨 显示配置
export CE_COLOR_OUTPUT=true                      # 彩色输出
export CE_EMOJI_OUTPUT=true                      # Emoji显示

echo "✅ Claude Enhancer 完全自动化模式已启用"
echo "   - CE_AUTO_CONFIRM: $CE_AUTO_CONFIRM"
echo "   - CLAUDE_CODE_BYPASS_PERMISSIONS: $CLAUDE_CODE_BYPASS_PERMISSIONS"
echo "   - CE_WORKFLOW_ENABLED: $CE_WORKFLOW_ENABLED"
