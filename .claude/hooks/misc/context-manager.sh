#!/bin/bash
# Context Manager - 防止上下文溢出

# 检查是否是多Agent调用
AGENT_COUNT=$(echo "$@" | grep -o "subagent_type" | wc -l)

# 根据Agent数量调整策略
if [ "$AGENT_COUNT" -ge 5 ]; then
    echo "⚠️  CONTEXT WARNING: 检测到${AGENT_COUNT}个Agent" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "建议优化策略防止上下文溢出：" >&2
    echo "" >&2
    echo "1. 分批执行：" >&2
    echo "   - 第一批: 核心设计Agent (2-3个)" >&2
    echo "   - 第二批: 实现Agent (2-3个)" >&2
    echo "   - 第三批: 测试和优化Agent (1-2个)" >&2
    echo "" >&2
    echo "2. 使用精简指令：" >&2
    echo "   - 每个Agent聚焦单一任务" >&2
    echo "   - 限制输出长度" >&2
    echo "   - 避免冗余信息" >&2
    echo "" >&2
    echo "3. 上下文管理技巧：" >&2
    echo "   - 使用 'summarize: true' 参数" >&2
    echo "   - 设置 'max_output: 2000' 限制" >&2
    echo "   - 完成后清理临时文件" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

    # 如果超过7个Agent，强制分批
    if [ "$AGENT_COUNT" -gt 7 ]; then
        echo "" >&2
        echo "❌ BLOCKED: ${AGENT_COUNT}个Agent太多，必须分批执行！" >&2
        echo "" >&2
        echo "强制要求：最多同时运行7个Agent" >&2
        echo "请分成2-3批执行以避免上下文溢出" >&2
        exit 2
    fi
fi

exit 0
