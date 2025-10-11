#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 代码编写检查器
# 防止直接写代码，强制使用Task工具和多Agent

set -e

# 读取输入
INPUT=$(cat)

# 提取文件路径和内容特征
FILE_PATH=$(echo "$INPUT" | grep -oP '"file_path"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
CONTENT=$(echo "$INPUT" | grep -oP '"content"\s*:\s*"[^"]+' | head -c 200 || echo "")

# 检测是否在写复杂代码
COMPLEX_PATTERNS="stress_test|performance|benchmark|agent_test|optimization|refactor|新功能|测试套件|压力测试|性能优化"

if echo "$INPUT" | grep -qE "$COMPLEX_PATTERNS"; then
    echo "╔════════════════════════════════════════╗" >&2
    echo "║   🚨 Claude Enhancer 工作流违规警告 🚨      ║" >&2
    echo "╚════════════════════════════════════════╝" >&2
    echo "" >&2
    echo "❌ 检测到复杂任务，但你在直接写代码！" >&2
    echo "" >&2
    echo "📋 违规内容：" >&2
    echo "   文件: $FILE_PATH" >&2
    echo "   类型: 复杂开发任务" >&2
    echo "" >&2
    echo "✅ 正确做法：" >&2
    echo "   1. 使用Task工具调用专业Agent" >&2
    echo "   2. 至少需要以下Agent并行工作：" >&2
    echo "      • performance-engineer - 性能分析" >&2
    echo "      • test-engineer - 测试设计" >&2
    echo "      • backend-architect - 架构设计" >&2
    echo "      • monitoring-specialist - 监控方案" >&2
    echo "      • code-reviewer - 代码审查" >&2
    echo "      • technical-writer - 文档编写" >&2
    echo "" >&2
    echo "🔄 建议操作：" >&2
    echo "   停止直接编码，改用Task工具：" >&2
    echo '   Task(subagent_type="performance-engineer",...)' >&2
    echo "" >&2
    echo "⚠️  这不是建议，是Claude Enhancer的强制要求！" >&2
    echo "════════════════════════════════════════" >&2

    # 记录违规
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] VIOLATION: Direct coding instead of Task usage - $FILE_PATH" >> /tmp/claude-enhancer_violations.log
fi

# 检测是否应该先创建分支
if echo "$FILE_PATH" | grep -qE "test|feature|optimization"; then
    if ! git branch --show-current | grep -qE "feature/|fix/|test/"; then
        echo "⚠️  提醒：应该先创建feature分支 (Phase 0)" >&2
    fi
fi

# 始终输出原始内容（不阻塞，只警告）
echo "$INPUT"
exit 0