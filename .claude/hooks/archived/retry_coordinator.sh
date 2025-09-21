#!/bin/bash
# Claude Enhancer Retry Coordinator - 协调重试流程
# 生成正确的Agent调用格式供Claude Code使用

set -e

INPUT=$(cat)

# 解析输入中的违规信息
if echo "$INPUT" | grep -q "CLAUDE_ENHANCER_MANDATORY_RETRY"; then
    # 提取需要的agents
    REQUIRED_AGENTS=$(echo "$INPUT" | grep "REQUIRED_AGENTS:" | cut -d: -f2- | xargs)
    TASK_TYPE=$(echo "$INPUT" | grep "TASK_TYPE:" | cut -d: -f2 | xargs)

    # 输出清晰的重试指导
    cat >&2 << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 CLAUDE_ENHANCER RETRY COORDINATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task Type Detected: $TASK_TYPE

Required Agents:
EOF

    # 列出每个agent及其作用
    for agent in $REQUIRED_AGENTS; do
        case "$agent" in
            backend-architect)
                echo "  • backend-architect - 设计系统架构" >&2
                ;;
            security-auditor)
                echo "  • security-auditor - 审查安全措施" >&2
                ;;
            api-designer)
                echo "  • api-designer - 设计API接口" >&2
                ;;
            database-specialist)
                echo "  • database-specialist - 设计数据模型" >&2
                ;;
            test-engineer)
                echo "  • test-engineer - 编写测试策略" >&2
                ;;
            frontend-specialist)
                echo "  • frontend-specialist - 设计前端架构" >&2
                ;;
            technical-writer)
                echo "  • technical-writer - 编写技术文档" >&2
                ;;
            performance-engineer)
                echo "  • performance-engineer - 优化性能" >&2
                ;;
            *)
                echo "  • $agent" >&2
                ;;
        esac
    done

    cat >&2 << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY ACTION FOR CLAUDE CODE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST now retry with ALL the following agents in
ONE function_calls block. This is not optional.

Copy and execute this EXACT format:

<function_calls>
EOF

    # 生成每个agent的调用
    for agent in $REQUIRED_AGENTS; do
        cat >&2 << EOF
  <invoke name="Task">
    <parameter name="description">[task for $agent]</parameter>
    <parameter name="prompt">[specific prompt for $agent]</parameter>
    <parameter name="subagent_type">$agent</parameter>
  </invoke>
EOF
    done

    cat >&2 << EOF
</function_calls>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Remember: All agents MUST be in ONE function_calls block!
This ensures parallel execution as required by Claude Enhancer.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

else
    # 没有违规，输出成功信息
    cat >&2 << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CLAUDE_ENHANCER COMPLIANCE CONFIRMED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All requirements met. Proceeding with execution.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi

exit 0