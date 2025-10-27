#!/usr/bin/env bash
# Learning Items转换为TODO
# 用途：将符合条件的Learning Items自动转换为TODO队列
# 用法：bash scripts/learning/convert_to_todo.sh
# 日期：2025-10-27

set -euo pipefail

CE_HOME="${CE_HOME:-}"
if [[ -z "$CE_HOME" ]]; then
  SPEC_PATH=$(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" 2>/dev/null | head -1)
  if [[ -n "$SPEC_PATH" ]]; then
    CE_HOME="$(dirname "$(dirname "$SPEC_PATH")")"
  fi
fi

if [[ -z "${CE_HOME:-}" ]] || [[ ! -f "$CE_HOME/.workflow/SPEC.yaml" ]]; then
  echo "❌ 错误: 无法找到Claude Enhancer目录" >&2
  exit 1
fi

echo "🔄 扫描Learning Items并转换为TODO..."
echo "   CE_HOME: $CE_HOME"
echo ""

CONVERTED=0
SKIPPED=0
ALREADY_CONVERTED=0

# 创建已转换记录文件（避免重复转换）
CONVERTED_LOG="$CE_HOME/.todos/.converted_items.log"
touch "$CONVERTED_LOG"

# 遍历所有Learning Items
for item_file in "$CE_HOME/.learning/items/"*.yml; do
  [[ ! -f "$item_file" ]] && continue

  ITEM_ID=$(grep "^id:" "$item_file" | head -1 | awk '{print $2}' | tr -d '"')

  # 检查是否已转换
  if grep -q "^$ITEM_ID$" "$CONVERTED_LOG" 2>/dev/null; then
    ((ALREADY_CONVERTED++))
    continue
  fi

  # 读取Learning Item字段（使用grep避免依赖yq）
  TODO_CANDIDATE=$(grep "todo_candidate:" "$item_file" | awk '{print $2}')
  CONFIDENCE=$(grep "confidence:" "$item_file" | awk '{print $2}')
  PRIORITY=$(grep "priority:" "$item_file" | awk '{print $2}' | tr -d '"')

  # 转换规则: todo_candidate=true && confidence>=0.80 && priority in [high,medium]
  if [[ "$TODO_CANDIDATE" == "true" ]]; then
    # 使用bc进行浮点数比较（如果可用）
    CONF_OK=false
    if command -v bc >/dev/null 2>&1; then
      if (( $(echo "$CONFIDENCE >= 0.80" | bc -l) )); then
        CONF_OK=true
      fi
    else
      # Fallback: 简单字符串比较（不精确但够用）
      if [[ "$CONFIDENCE" =~ ^0\.[89] ]] || [[ "$CONFIDENCE" =~ ^1\.0 ]]; then
        CONF_OK=true
      fi
    fi

    if [[ "$CONF_OK" == "true" ]]; then
      if [[ "$PRIORITY" == "high" || "$PRIORITY" == "medium" ]]; then
        # 提取信息
        DESCRIPTION=$(grep "description:" "$item_file" | head -1 | cut -d'"' -f2)
        SOLUTION=$(grep "solution:" "$item_file" | head -1 | cut -d'"' -f2)
        EFFORT=$(grep "estimated_effort:" "$item_file" | head -1 | cut -d'"' -f2)
        PROJECT=$(grep "^project:" "$item_file" | awk '{print $2}' | tr -d '"')
        CATEGORY=$(grep "^category:" "$item_file" | awk '{print $2}' | tr -d '"')

        # 生成TODO
        TODO_ID="todo-$(date +%Y%m%d)-$(printf "%03d" $((CONVERTED + 1)))"
        TODO_FILE="$CE_HOME/.todos/pending/${TODO_ID}.json"

        cat > "$TODO_FILE" <<EOF
{
  "id": "$TODO_ID",
  "title": "$DESCRIPTION",
  "description": "**来源**: Learning Item \`$ITEM_ID\`\\n**项目**: $PROJECT\\n**类别**: $CATEGORY\\n\\n**建议方案**:\\n$SOLUTION",
  "priority": "$PRIORITY",
  "estimated_effort": "$EFFORT",
  "status": "pending",
  "source_learning_id": "$ITEM_ID",
  "created_at": "$(date -u +%FT%TZ)",
  "tags": ["learning", "$CATEGORY", "$PROJECT"]
}
EOF

        # 记录已转换
        echo "$ITEM_ID" >> "$CONVERTED_LOG"

        echo "  ✅ 已转换: $TODO_ID"
        echo "     来源: $ITEM_ID"
        echo "     标题: $DESCRIPTION"
        echo "     优先级: $PRIORITY"
        echo ""

        ((CONVERTED++))
      else
        ((SKIPPED++))
      fi
    else
      ((SKIPPED++))
    fi
  else
    ((SKIPPED++))
  fi
done

# 更新queue.json
if command -v jq >/dev/null 2>&1 && [[ $CONVERTED -gt 0 ]]; then
  QUEUE_FILE="$CE_HOME/.todos/queue.json"
  TMP_QUEUE=$(mktemp)

  # 更新元数据
  jq --arg count "$CONVERTED" '
    .meta.total_todos = (.meta.total_todos + ($count | tonumber)) |
    .meta.last_updated = (now | todate)
  ' "$QUEUE_FILE" > "$TMP_QUEUE"

  mv "$TMP_QUEUE" "$QUEUE_FILE"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  📊 TODO转换完成                                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "统计："
echo "  ✅ 新转换: $CONVERTED个TODO"
echo "  ⊘ 跳过: $SKIPPED个Learning Item"
echo "  📝 已转换: $ALREADY_CONVERTED个（之前已转换）"
echo ""

if [[ $CONVERTED -gt 0 ]]; then
  echo "查看TODO队列："
  echo "  ls -lh $CE_HOME/.todos/pending/"
  echo ""
  echo "或使用ce命令："
  echo "  ce todo list"
fi
