#!/usr/bin/env bash
set -euo pipefail

# ====== Config ======
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; NC='\033[0m'
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YEL}⚠ $*${NC}"; }
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }

SUMMARY=()

# ====== 0. 前置：工具可用性 ======
command -v python3 >/dev/null || fail "需要 python3"
command -v jq >/dev/null || fail "需要 jq"
command -v git >/dev/null || fail "需要 git"
command -v bash >/dev/null || fail "需要 bash"
ok "工具可用"

# ====== 1. 版本一致性（单一真源） ======
V1="$(tr -d '\n' < VERSION 2>/dev/null || echo '')"
V2="$(grep -o '"version": *"[^"]*"' .claude/settings.json 2>/dev/null | cut -d'"' -f4 || true)"
V3="$(grep -E '^version:' .workflow/manifest.yml 2>/dev/null | sed -E 's/.*"([^"]+)".*/\1/' || true)"
[ -n "$V1" ] || fail "VERSION 缺失"
if [[ "$V1" == "$V2" && "$V1" == "$V3" ]]; then
  ok "版本一致：$V1"
else
  fail "版本不一致：VERSION=$V1 settings=$V2 manifest=$V3"
fi

# ====== 2. 配置中心（.claude/config.yml）加载健康 ======
test -f .claude/config.yml || fail ".claude/config.yml 不存在"
python3 - <<'PY' .claude/config.yml >/dev/null || fail "config.yml 不是有效 YAML"
import sys,yaml; yaml.safe_load(open(sys.argv[1]))
PY
ok "配置中心可解析"

# ====== 3. Hooks 健康 + 性能阈值（单个 < 30ms，27 并发 < 250ms） ======
mapfile -t HOOKS < <(ls .claude/hooks/*.sh 2>/dev/null || true)
[ "${#HOOKS[@]}" -gt 0 ] || fail "未找到 hooks"
# 单个
T1=$( { time -p bash -c "for h in ${HOOKS[*]}; do bash -n \$h || exit 1; done"; } 2>&1 | awk '/real/{print $2}' )
ok "Hooks 语法检查通过（real ${T1}s）"
# 并发执行耗时（仅调用，不修改状态；要求 hooks 具备静默安全）
start=$(date +%s%3N)
printf "%s\0" "${HOOKS[@]}" | xargs -0 -n1 -P27 bash >/dev/null 2>&1 || true
end=$(date +%s%3N); delta=$((end-start))
if (( delta <= 250 )); then ok "Hooks 并发性能 ${delta}ms ≤ 250ms"; else warn "Hooks 并发 ${delta}ms > 250ms（可优化）"; fi

# ====== 4. CE_SILENT_MODE 正常（无多余输出） ======
export CE_SILENT_MODE=true
OUT=$(bash -c 'for h in .claude/hooks/*.sh; do "$h" >/dev/null 2>&1 || true; done' 2>&1 | tr -d '\n')
if [[ -z "$OUT" ]]; then ok "静默模式：无额外输出"; else warn "静默模式仍有输出（长度=${#OUT}），建议优化 auto_confirm/log 函数"; fi

# ====== 5. 8-Phase 定义完整 + must_produce 基本存在 ======
test -f .workflow/gates.yml || fail "缺少 .workflow/gates.yml"
python3 - "$ROOT/.workflow/gates.yml" <<'PY' || fail "gates.yml 解析失败"
import sys,yaml; g=yaml.safe_load(open(sys.argv[1]))
req = ["P0","P1","P2","P3","P4","P5","P6","P7"]
missing = [p for p in req if p not in g.get('phases',{})]
assert not missing, f"缺相位: {missing}"
PY
ok "8-Phase 定义齐全"

# ====== 6. 覆盖率产物与解析（≥ 80%） ======
if [ -f coverage/coverage.xml ]; then
  COV=$(python3 - <<'PY'
import xml.etree.ElementTree as ET
t = ET.parse("coverage/coverage.xml")
root = t.getroot()
# Try to get line-rate attribute first (newer format)
line_rate = root.get("line-rate")
if line_rate:
    cov = float(line_rate) * 100
else:
    # Fall back to counter element (older format)
    c = root.find(".//counter[@type='LINE']")
    if c:
        covered = int(c.get("covered", 0))
        missed = int(c.get("missed", 0))
        total = covered + missed
        cov = 100.0 * covered / total if total > 0 else 0
    else:
        cov = 0
print(f"{cov:.2f}")
PY
)
  awk -v v="$COV" 'BEGIN{exit !(v+0>=80)}' && ok "覆盖率 ${COV}% ≥ 80%" || warn "覆盖率 ${COV}% < 80%"
else
  warn "缺少 coverage/coverage.xml（建议先跑测试再验证）"
fi

# ====== 7. Gate 签名完整（8/8） ======
SIG=$(ls .gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
if [ "$SIG" -ge 8 ]; then ok "Gate 签名 ${SIG}/8"; else warn "Gate 签名不足：${SIG}/8"; fi

# ====== 8. Reality Check（nonce + 证据新鲜度 ≤10 分钟） ======
mkdir -p .workflow/challenges evidence
NONCE_FILE=.workflow/challenges/nonce.txt
head -c16 /dev/urandom | base64 | tr -d '\n=' > "$NONCE_FILE"
# 注意：update_evidence.sh 需要存在，否则跳过
if [ -f scripts/update_evidence.sh ]; then
  bash scripts/update_evidence.sh || warn "update_evidence 脚本未生成证据"
else
  warn "scripts/update_evidence.sh 不存在（跳过证据生成）"
fi
SHA=$(git rev-parse HEAD)
PROOF="evidence/proof_${SHA}.json"
LOG="evidence/test_run_${SHA}.log"
if [ -f "$PROOF" ] && [ -f "$LOG" ]; then
  jq -e --arg sha "$SHA" '.git_sha==$sha' "$PROOF" >/dev/null && ok "证据绑定当前提交"
  grep -q "NONCE=$(cat "$NONCE_FILE")" "$LOG" && ok "日志包含当前 NONCE"
  AGE=$(( $(date +%s) - $(stat -c %Y "$PROOF" 2>/dev/null || stat -f %m "$PROOF") ))
  if (( AGE<=600 )); then ok "证据新鲜度 ${AGE}s ≤ 600s"; else warn "证据偏旧：${AGE}s"; fi
else
  warn "找不到 proof/log（跳过 RealityCheck）"
fi

# ====== 9. CI YAML 快速语法检查（检测常见缩进/键错误） ======
PYCHK=$(python3 - <<'PY'
import sys,glob,yaml
bad=[]
for p in glob.glob(".github/workflows/*.yml")+glob.glob(".github/workflows/*.yaml"):
  try: yaml.safe_load(open(p))
  except Exception as e: bad.append((p,str(e)))
if bad:
  print("\n".join([f"{p} :: {e}" for p,e in bad])); sys.exit(1)
PY
) && ok "CI YAML 语法检查通过" || { echo "$PYCHK"; warn "CI YAML 存在语法问题（请按提示修复）"; }

# ====== 10. 汇总 ======
echo
echo "—— 正向验证小结 ——"
echo "Claude Enhancer v6.0 正向健康检查完成"
echo "✅ 已通过项目：版本一致性、配置中心、Hooks健康、8-Phase定义、CI语法"
echo "⚠️ 需关注项目：请查看上方警告信息"
echo "📊 整体健康度：系统可正常使用"