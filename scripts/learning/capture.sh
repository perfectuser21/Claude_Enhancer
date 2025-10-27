#!/usr/bin/env bash
# Learning Item捕获脚本
# 用途：捕获开发过程中的学习经验（错误、优化、架构决策等）
# 用法：bash scripts/learning/capture.sh --category error_pattern --description "..." --phase Phase2
# 日期：2025-10-27

set -euo pipefail

# CE_HOME检测（优先环境变量，fallback自动检测）
CE_HOME="${CE_HOME:-}"
if [[ -z "$CE_HOME" ]]; then
  # 方法1: 从当前脚本位置推断（最可靠）
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CANDIDATE_CE_HOME="$(cd "$SCRIPT_DIR/../.." && pwd)"
  if [[ -f "$CANDIDATE_CE_HOME/.workflow/SPEC.yaml" ]]; then
    CE_HOME="$CANDIDATE_CE_HOME"
  else
    # 方法2: 搜索home目录（使用-print0和read -d ''处理空格）
    while IFS= read -r -d '' spec_file; do
      CE_HOME="$(dirname "$(dirname "$spec_file")")"
      break
    done < <(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" -print0 2>/dev/null)
  fi
fi

if [[ -z "${CE_HOME:-}" ]] || [[ ! -f "$CE_HOME/.workflow/SPEC.yaml" ]]; then
  echo "❌ 错误: 无法找到Claude Enhancer目录" >&2
  echo "   请设置CE_HOME环境变量或确保.workflow/SPEC.yaml存在" >&2
  echo "   示例: export CE_HOME=\"/home/xx/dev/Claude Enhancer\"" >&2
  exit 1
fi

# 默认值
CATEGORY=""
DESCRIPTION=""
PHASE=""
PROJECT=""
FILE=""
LINE=0
TYPE=""
TECHNICAL_DETAILS=""
CODE_SNIPPET=""
ROOT_CAUSE=""
SOLUTION=""
PREVENTION=""
CONFIDENCE=0.5
TODO_CANDIDATE="false"
PRIORITY="medium"
EFFORT=""
AUTO_FIX_ELIGIBLE="false"
AUTO_FIX_TIER=""
TAGS=""

# 参数解析
show_help() {
  cat <<'EOF'
Learning Item捕获脚本

用法:
  capture.sh --category <类别> --description <描述> --phase <Phase> [选项]

必填参数:
  --category CATEGORY       Learning类别（5选1）:
                             - error_pattern    (错误模式)
                             - performance      (性能优化)
                             - architecture     (架构决策)
                             - code_quality     (代码质量)
                             - success_pattern  (成功模式)

  --description DESC        简短描述（中文，用户友好）

  --phase PHASE             发生的Phase（Phase1-Phase7）

可选参数:
  --project PROJECT         项目名（默认自动检测）
  --file FILE               相关文件路径
  --line LINE               相关行号（默认0）
  --type TYPE               观察类型: error|optimization|insight
  --technical-details TEXT  技术细节（英文）
  --code-snippet CODE       相关代码片段
  --root-cause CAUSE        根本原因
  --solution SOL            解决方案
  --prevention PREV         预防措施
  --confidence NUM          信心分数 0-1（默认0.5）
  --todo                    标记为TODO候选
  --priority PRI            优先级: high|medium|low（默认medium）
  --effort EFFORT           预估工作量（如"2h", "1d"）
  --auto-fix-tier TIER      Auto-fix级别: tier1_auto|tier2_try_then_ask|tier3_must_confirm
  --tags "tag1,tag2"        标签（逗号分隔）

示例:
  # 捕获错误模式
  capture.sh \
    --category error_pattern \
    --description "导入bcrypt模块失败" \
    --phase Phase2 \
    --solution "pip install bcrypt" \
    --confidence 0.95 \
    --auto-fix-tier tier1_auto

  # 捕获性能优化
  capture.sh \
    --category performance \
    --description "使用缓存优化查询速度" \
    --phase Phase2 \
    --technical-details "Redis cache reduced query time from 500ms to 50ms" \
    --confidence 0.85

  # 捕获架构决策
  capture.sh \
    --category architecture \
    --description "选择JWT而非Session进行认证" \
    --phase Phase1 \
    --root-cause "需要支持分布式部署" \
    --todo \
    --priority high
EOF
}

# 参数解析循环
while [[ $# -gt 0 ]]; do
  case $1 in
    --help|-h) show_help; exit 0 ;;
    --category) CATEGORY="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --file) FILE="$2"; shift 2 ;;
    --line) LINE="$2"; shift 2 ;;
    --type) TYPE="$2"; shift 2 ;;
    --technical-details) TECHNICAL_DETAILS="$2"; shift 2 ;;
    --code-snippet) CODE_SNIPPET="$2"; shift 2 ;;
    --root-cause) ROOT_CAUSE="$2"; shift 2 ;;
    --solution) SOLUTION="$2"; shift 2 ;;
    --prevention) PREVENTION="$2"; shift 2 ;;
    --confidence) CONFIDENCE="$2"; shift 2 ;;
    --todo) TODO_CANDIDATE="true"; shift ;;
    --priority) PRIORITY="$2"; shift 2 ;;
    --effort) EFFORT="$2"; shift 2 ;;
    --auto-fix-tier) AUTO_FIX_TIER="$2"; AUTO_FIX_ELIGIBLE="true"; shift 2 ;;
    --tags) TAGS="$2"; shift 2 ;;
    *) echo "❌ 未知参数: $1" >&2; echo "   运行 --help 查看用法" >&2; exit 1 ;;
  esac
done

# 参数验证
if [[ -z "$CATEGORY" || -z "$DESCRIPTION" || -z "$PHASE" ]]; then
  echo "❌ 错误: --category, --description, --phase 为必填参数" >&2
  echo "   运行 --help 查看用法" >&2
  exit 1
fi

# 验证category
case "$CATEGORY" in
  error_pattern|performance|architecture|code_quality|success_pattern) ;;
  *) echo "❌ 错误: category必须是5个类别之一" >&2; exit 1 ;;
esac

# 验证phase
case "$PHASE" in
  Phase1|Phase2|Phase3|Phase4|Phase5|Phase6|Phase7) ;;
  *) echo "❌ 错误: phase必须是Phase1-Phase7" >&2; exit 1 ;;
esac

# 自动检测项目名
if [[ -z "$PROJECT" ]]; then
  PWD_BASE="$(basename "$PWD")"
  if [[ "$PWD" == "$CE_HOME" ]] || [[ "$PWD_BASE" == "Claude Enhancer" ]] || [[ "$PWD" == *"Claude Enhancer"* ]]; then
    PROJECT="claude-enhancer"
  else
    PROJECT="$PWD_BASE"
  fi
fi

# 生成Learning Item
TIMESTAMP=$(date -u +%FT%TZ)
TIMESTAMP_SHORT=$(date +%Y-%m-%d)

# 计算序号（当天第几个）
SEQ=$(find "$CE_HOME/.learning/items/" -name "${TIMESTAMP_SHORT}_*" 2>/dev/null | wc -l)
SEQ=$((SEQ + 1))

ITEM_ID="learning-${TIMESTAMP_SHORT}-$(printf "%03d" $SEQ)"
FILENAME="${TIMESTAMP_SHORT}_$(printf "%03d" $SEQ)_${CATEGORY}_${PROJECT}.yml"
FILEPATH="$CE_HOME/.learning/items/$FILENAME"

# 获取Git信息
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# 处理tags（转换为YAML数组）
if [[ -n "$TAGS" ]]; then
  TAGS_YAML=$(echo "$TAGS" | awk -F',' '{for(i=1;i<=NF;i++) printf "  - \"%s\"\n", $i}')
else
  TAGS_YAML="  []"
fi

# 写入YAML
cat > "$FILEPATH" <<EOF
---
id: "$ITEM_ID"
timestamp: "$TIMESTAMP"
project: "$PROJECT"
category: "$CATEGORY"
phase: "$PHASE"

context:
  working_directory: "$PWD"
  file: "$FILE"
  line: $LINE
  git_branch: "$GIT_BRANCH"
  git_commit: "$GIT_COMMIT"

observation:
  type: "$TYPE"
  description: "$DESCRIPTION"
  technical_details: "$TECHNICAL_DETAILS"
  code_snippet: |
$(if [[ -n "$CODE_SNIPPET" ]]; then echo "$CODE_SNIPPET" | sed 's/^/    /'; else echo "    "; fi)

learning:
  root_cause: "$ROOT_CAUSE"
  solution: "$SOLUTION"
  prevention: "$PREVENTION"
  confidence: $CONFIDENCE

actionable:
  todo_candidate: $TODO_CANDIDATE
  priority: "$PRIORITY"
  estimated_effort: "$EFFORT"
  auto_fix_eligible: $AUTO_FIX_ELIGIBLE
  auto_fix_tier: "$AUTO_FIX_TIER"

metadata:
  decay_factor: 1.0
  last_validated: null
  validation_count: 0
  notion_synced: false
  notion_page_id: null
  tags:
$TAGS_YAML
EOF

# 创建符号链接（by_category）
ln -sf "../../items/$FILENAME" "$CE_HOME/.learning/by_category/$CATEGORY/$FILENAME" 2>/dev/null || true

# 创建符号链接（by_project）
mkdir -p "$CE_HOME/.learning/by_project/$PROJECT"
ln -sf "../../items/$FILENAME" "$CE_HOME/.learning/by_project/$PROJECT/$FILENAME" 2>/dev/null || true

# 更新stats.json
if command -v jq >/dev/null 2>&1; then
  STATS_FILE="$CE_HOME/.learning/stats.json"
  TMP_STATS=$(mktemp)

  jq --arg cat "$CATEGORY" --arg proj "$PROJECT" --arg phase "$PHASE" '
    .by_category[$cat] += 1 |
    .by_project[$proj] = ((.by_project[$proj] // 0) + 1) |
    .by_phase[$phase] += 1
  ' "$STATS_FILE" > "$TMP_STATS"

  mv "$TMP_STATS" "$STATS_FILE"
fi

# 输出成功信息
echo "✅ Learning Item已捕获"
echo "   ID:       $ITEM_ID"
echo "   项目:     $PROJECT"
echo "   类别:     $CATEGORY"
echo "   Phase:    $PHASE"
echo "   文件:     $FILEPATH"
echo ""

if [[ "$TODO_CANDIDATE" == "true" ]]; then
  echo "   🔖 已标记为TODO候选（优先级: $PRIORITY）"
fi

if [[ "$AUTO_FIX_ELIGIBLE" == "true" ]]; then
  echo "   🔧 Auto-fix级别: $AUTO_FIX_TIER"
fi

echo ""
echo "查看Learning Item:"
echo "   cat $FILEPATH"
echo ""
echo "查看所有Learning Items:"
echo "   ls -lh $CE_HOME/.learning/items/"
echo ""
