#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# 动态获取Claude Enhancer项目路径
CLAUDE_ENHANCER_HOME="${CLAUDE_ENHANCER_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export CLAUDE_ENHANCER_HOME

# Claude Enhancer Hooks Installer
# 安装和配置所有Claude Enhancer hooks

set -e

HOOKS_DIR="${CLAUDE_ENHANCER_HOME}/.claude/hooks"

echo "🚀 Claude Enhancer Hooks 安装程序"
echo "========================================="
echo ""

# 检查目录
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Hooks目录不存在: $HOOKS_DIR"
    exit 1
fi

cd "$HOOKS_DIR"

# 设置执行权限
echo "📝 设置Hook执行权限..."
chmod +x claude_enhancer_*.sh
chmod +x install.sh

# 备份原有hooks
if [ -f "check_agents.sh" ]; then
    echo "📦 备份原有hooks..."
    mv check_agents.sh check_agents.sh.bak.$(date +%Y%m%d) 2>/dev/null || true
    mv on-error.sh on-error.sh.bak.$(date +%Y%m%d) 2>/dev/null || true
    mv post-task.sh post-task.sh.bak.$(date +%Y%m%d) 2>/dev/null || true
    mv pre-edit.sh pre-edit.sh.bak.$(date +%Y%m%d) 2>/dev/null || true
fi

# 创建符号链接或包装器
echo "🔗 配置Hook链接..."

# 创建主hook包装器（如果Claude Code支持）
cat > pre-task.sh << 'EOF'
#!/bin/bash
# Claude Enhancer Pre-Task Hook Wrapper
# 在Task执行前运行所有Claude Enhancer验证

exec bash ${CLAUDE_ENHANCER_HOME}/.claude/hooks/claude_enhancer_master.sh
EOF

chmod +x pre-task.sh

# 验证安装
echo ""
echo "✅ 验证安装..."
echo ""
echo "已安装的Claude Enhancer Hooks:"
ls -la claude_enhancer_*.sh | awk '{print "  ✓", $9}'

echo ""
echo "📊 Hook功能说明:"
echo "  • claude_enhancer_task_analyzer.sh    - 智能识别任务类型"
echo "  • claude_enhancer_agent_validator.sh  - 验证Agent选择（最少3个）"
echo "  • claude_enhancer_parallel_checker.sh - 检查并行执行模式"
echo "  • claude_enhancer_quality_gates.sh    - 代码质量门检查"
echo "  • claude_enhancer_master.sh           - 主控制器（协调所有hooks）"

# 创建测试命令
echo ""
echo "📝 创建测试脚本..."
cat > test_hooks.sh << 'EOF'
#!/bin/bash
# 测试Claude Enhancer Hooks

echo "测试1: Agent数量不足（应该被阻止）"
echo '{"subagent_type": "backend-architect", "prompt": "设计登录系统"}' | bash claude_enhancer_agent_validator.sh

echo ""
echo "测试2: 正确的Agent组合"
echo '{"function_calls": [
  {"subagent_type": "backend-architect", "prompt": "设计登录系统"},
  {"subagent_type": "security-auditor", "prompt": "审查安全"},
  {"subagent_type": "test-engineer", "prompt": "编写测试"}
]}' | bash claude_enhancer_master.sh
EOF

chmod +x test_hooks.sh

# 显示使用说明
echo ""
echo "========================================="
echo "✨ Claude Enhancer Hooks 安装完成！"
echo ""
echo "📖 使用说明："
echo "  1. Hooks会自动在Claude Code操作时执行"
echo "  2. 查看日志: tail -f /tmp/claude_enhancer_*.log"
echo "  3. 测试hooks: ./test_hooks.sh"
echo "  4. 配置文件: claude_enhancer_config.yaml"
echo ""
echo "🎯 核心规则："
echo "  • 最少使用3个Agent"
echo "  • 优先并行执行"
echo "  • 自动任务类型识别"
echo "  • 质量门自动检查"
echo ""
echo "💡 提示：Hooks会提供智能建议但不会过度阻止你的工作"
echo "========================================="