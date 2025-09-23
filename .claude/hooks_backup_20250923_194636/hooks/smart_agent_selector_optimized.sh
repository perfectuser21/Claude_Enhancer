#!/bin/bash
# 优化版Agent选择器 - 使用缓存减少重复计算

CACHE_FILE="/tmp/claude_agent_cache.json"
CACHE_TTL=300  # 5分钟缓存

# 检查缓存
if [ -f "$CACHE_FILE" ]; then
    CACHE_AGE=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ $CACHE_AGE -lt $CACHE_TTL ]; then
        # 使用缓存
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# 快速任务分析
TASK_TYPE="standard"
AGENT_COUNT=6

# 生成建议
SUGGESTION=$(cat <<JSON
{
  "type": "$TASK_TYPE",
  "agents": $AGENT_COUNT,
  "recommendation": "使用${AGENT_COUNT}个Agent并行执行"
}
JSON
)

# 保存到缓存
echo "$SUGGESTION" > "$CACHE_FILE"
echo "$SUGGESTION"
