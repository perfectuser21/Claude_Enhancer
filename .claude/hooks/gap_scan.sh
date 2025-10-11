#!/usr/bin/env bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [gap_scan.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

set -euo pipefail

# 根据静默模式决定输出函数
if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "== CE-5.3 Gap Scan =="
fi
pass=0; fail=0; warn=0

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    section(){ printf "\n-- %s --\n" "$1"; }
    ok(){ echo "✓ $*"; pass=$((pass+1)); }
    ng(){ echo "✗ $*"; fail=$((fail+1)); }
    wf(){ echo "⚠ $*"; warn=$((warn+1)); }
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    section(){ :; }  # 紧凑模式不输出section
    ok(){ pass=$((pass+1)); }
    ng(){ echo "[Gap] ✗ $*"; fail=$((fail+1)); }
    wf(){ warn=$((warn+1)); }
else
    # 完全静默模式
    section(){ :; }
    ok(){ pass=$((pass+1)); }
    ng(){ fail=$((fail+1)); }
    wf(){ warn=$((warn+1)); }
fi

# 目标：场景≥25、SLO≥10、性能指标≥30、CI jobs≥7、hooks硬拦截
section "Counts & Contracts"
feat_cnt=$(find acceptance -name "*.feature" 2>/dev/null | wc -l | tr -d ' ')
(( feat_cnt >= 25 )) && ok "BDD features >=25 ($feat_cnt)" || ng "BDD features不足：$feat_cnt/25"

slo_cnt=$(grep -R "name:" -n observability/slo 2>/dev/null | wc -l | tr -d ' ')
(( slo_cnt >= 10 )) && ok "SLO >=10 ($slo_cnt)" || ng "SLO不足：$slo_cnt/10"

perf_cnt=$(grep -R -E '(^|\s)(metric:|budget:|threshold:)' metrics 2>/dev/null | wc -l | tr -d ' ')
(( perf_cnt >= 30 )) && ok "性能指标 >=30 ($perf_cnt)" || ng "性能指标不足：$perf_cnt/30"

section "CI Workflow"
wf_path=".github/workflows/ci-enhanced-5.3.yml"
if [[ -f "$wf_path" ]]; then
  jobs=$(awk '
    BEGIN{in=0; c=0}
    /^[[:space:]]*jobs:[[:space:]]*$/ {in=1; next}
    in==1 && /^[[:space:]]*[a-zA-Z0-9_.-]+:[[:space:]]*$/ {c++}
    in==1 && /^[^[:space:]]/ {in=0}
    END{print c}' "$wf_path")
  (( jobs >= 7 )) && ok "CI jobs >=7 ($jobs)" || ng "CI jobs不足：$jobs/7"
else
  ng "缺少 workflow: $wf_path"
fi

section "Hooks (hard fail)"
precommit=".git/hooks/pre-commit"
[[ -x "$precommit" ]] || wf "pre-commit 不在 .git/hooks/，请安装或软链"
grep -q "set -e" "${precommit:-/dev/null}" && ok "pre-commit 硬失败开启" || ng "pre-commit 未设置硬失败 set -e"

section "Migrations"
mig=$(ls migrations/* 2>/dev/null | wc -l | tr -d ' ')
grep -qiE '(down|rollback)' -n migrations/* 2>/dev/null \
  && ok "迁移含回滚 (files:$mig)" || ng "迁移缺少回滚标记"

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo -e "\n== Summary ==\nPASS:$pass  FAIL:$fail  WARN:$warn"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Gap] PASS:$pass FAIL:$fail WARN:$warn"
fi
(( fail == 0 )) || exit 1
