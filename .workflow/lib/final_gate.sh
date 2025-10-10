#!/usr/bin/env bash
# Final Gate Check - 最后闸门检查（Trust-but-Verify）
# 用途：pre-push和演练脚本共用的质量闸门
# 调用：source .workflow/lib/final_gate.sh && final_gate_check

set -euo pipefail

final_gate_check() {
  local gate_fail=0

  # 确保PROJECT_ROOT已设置
  PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
  BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)}"

  # 1) 质量分：真实分数（MOCK 仅覆盖）
  local SCORE_FILE="$PROJECT_ROOT/.workflow/_reports/quality_score.txt"
  local REAL_SCORE="0"
  if [[ -f "$SCORE_FILE" ]]; then
    REAL_SCORE="$(tr -d '\n' < "$SCORE_FILE" 2>/dev/null || echo 0)"
  fi
  local SCORE="${MOCK_SCORE:-$REAL_SCORE}"

  # 去除小数部分进行比较
  if (( ${SCORE%%.*} < 85 )); then
    echo "❌ BLOCK: quality score $SCORE < 85 (minimum required)"
    gate_fail=1
  fi

  # 2) 覆盖率：解析 coverage.xml（MOCK 仅覆盖）
  local COV="0"
  if [[ -f "$PROJECT_ROOT/coverage/coverage.xml" ]]; then
    COV="$(python3 - <<'PY'
import xml.etree.ElementTree as ET, sys
try:
  t=ET.parse("coverage/coverage.xml")
  c=t.getroot().find(".//counter[@type='LINE']")
  if c is not None:
    covered=int(c.get("covered",0))
    missed=int(c.get("missed",0))
    pct=100.0*covered/(covered+missed) if covered+missed>0 else 0.0
    print(f"{pct:.2f}")
  else:
    print("0")
except Exception as e:
  print("0")
  sys.exit(0)
PY
)"
  fi

  # 覆盖 MOCK 覆盖率
  if [[ -n "${MOCK_COVERAGE:-}" ]]; then
    COV="$MOCK_COVERAGE"
  fi

  # 简单浮点比较（避免 bc 依赖）
  if ! awk -v v="$COV" 'BEGIN{ if (v+0 >= 80) { exit 0 } else { exit 1 } }'; then
    echo "❌ BLOCK: coverage ${COV}% < 80% (minimum required)"
    gate_fail=1
  fi

  # 3) Gate 签名（保护分支强制）
  if [[ "$BRANCH" =~ ^(main|master|production)$ ]]; then
    local SIG_COUNT
    SIG_COUNT=$(ls "$PROJECT_ROOT"/.gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
    if [[ "${MOCK_SIG:-}" == "invalid" || "$SIG_COUNT" -lt 8 ]]; then
      echo "❌ BLOCK: gate signatures incomplete ($SIG_COUNT/8) for production branch"
      gate_fail=1
    fi
  fi

  return $gate_fail
}
