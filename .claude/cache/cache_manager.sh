#!/bin/bash
CACHE_FILE=".claude/cache/workflow_status.cache"
CACHE_TTL=5  # 5秒缓存

if [ -f "$CACHE_FILE" ]; then
    CACHE_AGE=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ $CACHE_AGE -lt $CACHE_TTL ]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# 执行实际命令并缓存
./.workflow/executor.sh status > "$CACHE_FILE"
cat "$CACHE_FILE"
