#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Final Gate Check Library - 统一质量门禁规则
# 供 pre-push hook 和演练脚本共同使用
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# 颜色常量（带默认值防止未定义）
RED="${RED:-\033[0;31m}"
GREEN="${GREEN:-\033[0;32m}"
YELLOW="${YELLOW:-\033[1;33m}"
BLUE="${BLUE:-\033[0;34m}"
CYAN="${CYAN:-\033[0;36m}"
BOLD="${BOLD:-\033[1m}"
NC="${NC:-\033[0m}"

# 跨平台 mtime 函数
mtime() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        stat -f %m "$file" 2>/dev/null || echo "0"
    else
        stat -c %Y "$file" 2>/dev/null || echo "0"
    fi
}

final_gate_check() {
  local gate_fail=0

  # 确保PROJECT_ROOT已设置（CI兼容）
  PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
  BRANCH="${BRANCH:-${GITHUB_REF_NAME:-${CI_COMMIT_REF_NAME:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)}}}"

  # 加载配置阈值（从 gates.yml 或环境变量）
  local QUALITY_MIN="${QUALITY_MIN:-85}"
  local COVERAGE_MIN="${COVERAGE_MIN:-80}"
  local REQUIRED_SIGS="${REQUIRED_SIGS:-8}"

  if [[ -f "$PROJECT_ROOT/.workflow/gates.yml" ]] && command -v yq &> /dev/null; then
    QUALITY_MIN=$(yq '.quality.quality_min // 85' "$PROJECT_ROOT/.workflow/gates.yml" 2>/dev/null || echo "85")
    COVERAGE_MIN=$(yq '.quality.coverage_min // 80' "$PROJECT_ROOT/.workflow/gates.yml" 2>/dev/null || echo "80")
    REQUIRED_SIGS=$(yq '.quality.required_signatures // 8' "$PROJECT_ROOT/.workflow/gates.yml" 2>/dev/null || echo "8")
  fi

  echo -e "${CYAN}📊 Quality Thresholds: Score>=$QUALITY_MIN, Coverage>=$COVERAGE_MIN%, Sigs>=$REQUIRED_SIGS${NC}"

  # 1) 质量分：真实分数（MOCK 仅覆盖）
  local SCORE_FILE="$PROJECT_ROOT/.workflow/_reports/quality_score.txt"
  local REAL_SCORE="0"
  if [[ -f "$SCORE_FILE" ]]; then
    REAL_SCORE="$(tr -d '\n' < "$SCORE_FILE" 2>/dev/null || echo 0)"
  fi
  local SCORE="${MOCK_SCORE:-$REAL_SCORE}"

  # 去除小数部分进行比较
  if (( ${SCORE%%.*} < QUALITY_MIN )); then
    echo -e "${RED}❌ BLOCK: quality score $SCORE < $QUALITY_MIN (minimum required)${NC}"
    gate_fail=1
  else
    echo -e "${GREEN}✅ Quality score: $SCORE >= $QUALITY_MIN${NC}"
  fi

  # 2) 覆盖率：解析 coverage.xml 或 lcov.info（MOCK 仅覆盖）
  local COV="0"

  # 优先 coverage.xml (Cobertura/Jacoco)
  if [[ -f "$PROJECT_ROOT/coverage/coverage.xml" ]]; then
    if ! command -v python3 &> /dev/null; then
      echo -e "${RED}❌ FATAL: python3 not found, cannot parse coverage.xml${NC}"
      echo -e "${YELLOW}   Coverage check will BLOCK without python3${NC}"
      gate_fail=1
    else
      COV="$(cd "$PROJECT_ROOT" && python3 - <<'PY'
import xml.etree.ElementTree as ET, sys
try:
  t=ET.parse("coverage/coverage.xml")
  root=t.getroot()
  # Cobertura format
  if "line-rate" in root.attrib:
    print(int(float(root.attrib["line-rate"]) * 100))
  # Jacoco format
  else:
    c=root.find(".//counter[@type='LINE']")
    if c is not None:
      covered=int(c.get("covered",0))
      missed=int(c.get("missed",0))
      pct=100.0*covered/(covered+missed) if covered+missed>0 else 0.0
      print(f"{pct:.0f}")
    else:
      print("0")
except Exception:
  print("0")
PY
)"
    fi
  # 回退到 lcov.info
  elif [[ -f "$PROJECT_ROOT/coverage/lcov.info" ]]; then
    if ! command -v python3 &> /dev/null; then
      echo -e "${RED}❌ FATAL: python3 not found, cannot parse lcov.info${NC}"
      gate_fail=1
    else
      COV="$(cd "$PROJECT_ROOT" && python3 - <<'PY'
try:
  with open("coverage/lcov.info") as f:
    lf=lh=0
    for line in f:
      if line.startswith("LF:"): lf+=int(line.split(":")[1])
      elif line.startswith("LH:"): lh+=int(line.split(":")[1])
    print(int(lh*100/lf) if lf>0 else 0)
except:
  print("0")
PY
)"
    fi
  fi

  # 覆盖 MOCK 覆盖率
  if [[ -n "${MOCK_COVERAGE:-}" ]]; then
    COV="$MOCK_COVERAGE"
  fi

  # 简单整数比较 - Skip for RFC branches (documentation/kernel changes)
  if [[ "$BRANCH" =~ ^rfc/ ]]; then
    echo -e "${BLUE}ℹ️  Skipping coverage check for RFC branch (documentation/kernel changes)${NC}"
  elif (( ${COV%%.*} < COVERAGE_MIN )); then
    echo -e "${RED}❌ BLOCK: coverage ${COV}% < ${COVERAGE_MIN}% (minimum required)${NC}"
    gate_fail=1
  else
    echo -e "${GREEN}✅ Coverage: ${COV}% >= ${COVERAGE_MIN}%${NC}"
  fi

  # 3) Gate 签名（保护分支强制）
  if [[ "$BRANCH" =~ ^(main|master|production)$ ]]; then
    local SIG_COUNT
    SIG_COUNT=$(ls "$PROJECT_ROOT"/.gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')

    if [[ "${MOCK_SIG:-}" == "invalid" ]]; then
      echo -e "${CYAN}🎭 MOCK MODE: Simulating invalid signatures${NC}"
      echo -e "${RED}❌ BLOCK: gate signatures invalid (MOCK)${NC}"
      gate_fail=1
    elif (( SIG_COUNT < REQUIRED_SIGS )); then
      echo -e "${RED}❌ BLOCK: gate signatures incomplete ($SIG_COUNT/$REQUIRED_SIGS) for production branch${NC}"
      gate_fail=1
    else
      echo -e "${GREEN}✅ Gate signatures: $SIG_COUNT/$REQUIRED_SIGS${NC}"
    fi
  else
    echo -e "${BLUE}ℹ️  Skipping gate signature check (not a protected branch)${NC}"
  fi

  echo ""
  if (( gate_fail > 0 )); then
    echo -e "${BOLD}${RED}════════════════════════════════════════${NC}"
    echo -e "${BOLD}${RED}❌ FINAL GATE: BLOCKED${NC}"
    echo -e "${BOLD}${RED}════════════════════════════════════════${NC}"
    return 1
  else
    echo -e "${BOLD}${GREEN}════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}✅ FINAL GATE: PASSED${NC}"
    echo -e "${BOLD}${GREEN}════════════════════════════════════════${NC}"
    return 0
  fi
}
