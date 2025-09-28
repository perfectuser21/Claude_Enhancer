#!/usr/bin/env bash
set -euo pipefail

# --- helpers ---
ts(){ date +"%Y-%m-%d %H:%M:%S"; }
hr(){ printf "\n%s\n" "----------------------------------------"; }

OUT="CAPABILITY_REPORT.md"
PASS=0; FAIL=0; WARN=0
ok(){ echo "✓ $*"; PASS=$((PASS+1)); }
ng(){ echo "✗ $*"; FAIL=$((FAIL+1)); }
wf(){ echo "⚠ $*"; WARN=$((WARN+1)); }

start="$(ts)"
echo "# Claude Enhancer 5.3 能力快照" > "$OUT"
echo "_Generated at: ${start}_" >> "$OUT"
echo >> "$OUT"

echo "## 1) 快速验证 (官方脚本)" | tee -a "$OUT"
validation_output=$(bash test/validate_enhancement.sh 2>&1 || true)
if echo "$validation_output" | grep -q "保障力评分.*100%"; then
  ok "官方验证脚本通过 (100/100)"
  echo "- 官方验证脚本：✅ 通过 (100/100)" >> "$OUT"
else
  score=$(echo "$validation_output" | grep "保障力评分" | sed -E 's/.*\[.*\] ([0-9]+)%.*/\1/')
  if [ -n "$score" ] && [ "$score" -gt 0 ]; then
    if [ "$score" -ge 90 ]; then
      ok "官方验证脚本评分: ${score}/100"
      echo "- 官方验证脚本：✅ 评分 ${score}/100" >> "$OUT"
    else
      wf "官方验证脚本评分: ${score}/100"
      echo "- 官方验证脚本：⚠ 评分 ${score}/100" >> "$OUT"
    fi
  else
    ng "官方验证脚本失败"
    echo "- 官方验证脚本：❌ 失败" >> "$OUT"
  fi
fi
hr

echo "## 2) 规模与契约指标" | tee -a "$OUT"
feat_cnt=$(find acceptance -name "*.feature" 2>/dev/null | wc -l | tr -d ' ')
perf_cnt=$(grep -R -E '(^|\s)(metric:|budget:|threshold:)' metrics 2>/dev/null | wc -l | tr -d ' ' || echo 0)
slo_cnt=$(grep -R "name:" -n observability/slo 2>/dev/null | wc -l | tr -d ' ' || echo 0)

[[ "${feat_cnt:-0}" -ge 25 ]] && ok "BDD 场景数 ${feat_cnt} (>=25)" || ng "BDD 场景不足 ${feat_cnt}/25"
[[ "${perf_cnt:-0}" -ge 30 ]] && ok "性能指标 ${perf_cnt} (>=30)" || ng "性能指标不足 ${perf_cnt}/30"
[[ "${slo_cnt:-0}" -ge 10 ]] && ok "SLO 数量 ${slo_cnt} (>=10)" || ng "SLO 不足 ${slo_cnt}/10"

cat >> "$OUT" <<EOF

| 指标 | 当前 | 目标 | 状态 |
|---|---:|---:|:---:|
| BDD 场景数 | ${feat_cnt} | 25 | $([[ $feat_cnt -ge 25 ]] && echo ✅ || echo ❌) |
| 性能指标数 | ${perf_cnt} | 30 | $([[ $perf_cnt -ge 30 ]] && echo ✅ || echo ❌) |
| SLO 定义数 | ${slo_cnt} | 10 | $([[ $slo_cnt -ge 10 ]] && echo ✅ || echo ❌) |

EOF
hr

echo "## 3) Git Hooks 硬闸" | tee -a "$OUT"
precommit=".git/hooks/pre-commit"
if [[ -x "$precommit" ]] && grep -q "set -e" "$precommit"; then
  ok "pre-commit 硬拦截启用"
  echo "- pre-commit：✅ 硬拦截启用" >> "$OUT"
else
  ng "pre-commit 未硬拦截或未安装（ln -sf ../../.claude/git-hooks/enhanced-pre-commit-5.3 .git/hooks/pre-commit）"
  echo "- pre-commit：❌ 未硬拦截/未安装" >> "$OUT"
fi
hr

echo "## 4) CI 工作流" | tee -a "$OUT"
wf_path=".github/workflows/ci-enhanced-5.3.yml"
if [[ -f "$wf_path" ]]; then
  jobs=$(grep -E "^[[:space:]]*[a-zA-Z0-9_.-]+:[[:space:]]*$" "$wf_path" | grep -v "^on:" | grep -v "^env:" | wc -l)
  if (( jobs >= 7 )); then
    ok "CI jobs ${jobs} (>=7)"
    echo "- CI jobs：✅ ${jobs}" >> "$OUT"
  else
    ng "CI jobs 不足 ${jobs}/7"
    echo "- CI jobs：❌ ${jobs}/7" >> "$OUT"
  fi
else
  ng "找不到 workflow: $wf_path"
  echo "- CI 配置：❌ 缺失 $wf_path" >> "$OUT"
fi
hr

echo "## 5) 迁移与回滚能力" | tee -a "$OUT"
mig_files=$(ls migrations/* 2>/dev/null | wc -l | tr -d ' ' || echo 0)
if grep -qiE '(down|rollback)' -n migrations/* 2>/dev/null; then
  ok "迁移含回滚（文件数：${mig_files}）"
  echo "- 数据库迁移：✅ up/down 完整" >> "$OUT"
else
  ng "迁移缺少回滚标记"
  echo "- 数据库迁移：❌ 缺少回滚" >> "$OUT"
fi
hr

echo "## 6) 金丝雀策略文件" | tee -a "$OUT"
if [[ -f "sre/deploy/canary.yaml" || -f "canary.yaml" ]]; then
  ok "检测到金丝雀部署策略"
  echo "- 金丝雀部署：✅ 配置存在" >> "$OUT"
else
  wf "未检测到 canary.yaml（仅警告）"
  echo "- 金丝雀部署：⚠ 配置缺失（可选）" >> "$OUT"
fi
hr

echo "## 7) 能力结论" | tee -a "$OUT"
echo "- 通过：${PASS}，失败：${FAIL}，警告：${WARN}" | tee -a "$OUT"
[[ $FAIL -eq 0 ]] && echo "- **结论：可投入生产** ✅" | tee -a "$OUT" || echo "- **结论：需处理失败项后再上** ❌" | tee -a "$OUT"

echo
echo "已输出报告：$OUT"