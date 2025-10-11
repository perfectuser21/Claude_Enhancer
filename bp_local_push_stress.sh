#!/usr/bin/env bash
set -euo pipefail

# ====== 配色 & 工具 ======
GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; NC='\033[0m'
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
bad(){ echo -e "${RED}✗ $*${NC}"; }
warn(){ echo -e "${YEL}⚠ $*${NC}"; }
die(){ bad "$*"; exit 1; }

# ====== 前置检查 ======
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "请在 Git 仓库根目录运行。"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
LOGDIR="$ROOT/stress-logs"
mkdir -p "$LOGDIR"

HOOK="$ROOT/.git/hooks/pre-push"
test -f "$HOOK" || die "未找到 .git/hooks/pre-push"
test -x "$HOOK" || warn "pre-push 当前不可执行（脚本会覆盖多场景测试）"

CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
MAIN_BRANCH="${MAIN_BRANCH:-main}"

# 创建一个干净的"空提交"以触发钩子（不影响代码）
git commit --allow-empty -m "bp-stress: synthetic test commit $(date -Is)" >/dev/null 2>&1 || true

# 建立一个可用的 feature 分支用于"应当允许"的对照
if git show-ref --quiet "refs/heads/feature/bp-stress"; then
  git checkout -q "feature/bp-stress"
else
  git checkout -q -B "feature/bp-stress"
fi

# ====== 测试矩阵定义 ======
# 每个用例：name | command | expect (BLOCK/ALLOW) | ref (main/feature)
CASES=()
add_case(){ CASES+=("$1|$2|$3|$4"); }

# 基线：应允许（feature 分支）
add_case "ALLOW_feature_normal" \
  "git push --dry-run origin HEAD:refs/heads/feature/bp-stress" \
  "ALLOW" "feature"

# 1. 直推 main（标准）
add_case "BLOCK_main_plain" \
  "git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 2. --no-verify 绕过
add_case "BLOCK_main_noverify" \
  "git push --dry-run --no-verify origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 3. 取消钩子执行权限
add_case "BLOCK_main_nonexec_hook" \
  "chmod -x .git/hooks/pre-push; git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}; chmod +x .git/hooks/pre-push" \
  "BLOCK" "main"

# 4. 更改 hooksPath 指向空目录
add_case "BLOCK_main_hooksPath_null" \
  "git -c core.hooksPath=/dev/null push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 5. 临时替换 hooksPath 到一个只有空脚本的目录
add_case "BLOCK_main_hooksPath_dummy" \
  "mkdir -p .git/hooks-empty; printf '#!/usr/bin/env bash\nexit 0\n' > .git/hooks-empty/pre-push; chmod +x .git/hooks-empty/pre-push; git -c core.hooksPath=.git/hooks-empty push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 6. 用环境变量干扰（如果你的钩子读取 CE_*）
add_case "BLOCK_main_env_bypass" \
  "CE_DISABLE_PREPUSH=1 git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 7. 改 remote 名（仍应阻止 main 引用）
add_case "BLOCK_main_alt_remote" \
  "git remote rename origin origin-bp 2>/dev/null || true; git push --dry-run origin-bp HEAD:refs/heads/${MAIN_BRANCH}; git remote rename origin-bp origin 2>/dev/null || true" \
  "BLOCK" "main"

# 8. 使用 GIT_DIR/GIT_WORK_TREE 改变布局（应仍阻止）
add_case "BLOCK_main_alt_tree" \
  "GIT_DIR=$(git rev-parse --git-dir) GIT_WORK_TREE=$(pwd) git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 9. 空仓或浅克隆情境（在本地同仓模拟：--porcelain 也应被拦）
add_case "BLOCK_main_porcelain" \
  "git push --porcelain --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}" \
  "BLOCK" "main"

# 10. 工作树/子工作树情境（worktree）
add_case "BLOCK_main_worktree" \
  "git worktree add -f .wt-bp-stress >/dev/null 2>&1 || true; (cd .wt-bp-stress && git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}); rm -rf .wt-bp-stress" \
  "BLOCK" "main"

# 11. 大量重试/并发（10 次并发，不应有一次放行）
add_case "BLOCK_main_concurrent" \
  "seq 1 10 | xargs -I{} -P10 bash -c 'git push --dry-run origin HEAD:refs/heads/${MAIN_BRANCH}'" \
  "BLOCK" "main"

# 12. 对照再测（feature 仍应允许）
add_case "ALLOW_feature_again" \
  "git push --dry-run origin HEAD:refs/heads/feature/bp-stress" \
  "ALLOW" "feature"

# ====== 执行函数 ======
run_case(){
  local name="$1" cmd="$2" expect="$3" ref="$4"
  local logfile="$LOGDIR/${name}.log"
  local rc

  # 切到目标 ref
  if [[ "$ref" == "main" ]]; then
    git checkout -q "$MAIN_BRANCH" || die "切换到 ${MAIN_BRANCH} 失败，请确认为本地存在。"
  else
    git checkout -q "feature/bp-stress"
  fi

  echo "===== $name =====" | tee "$logfile"
  echo "\$ $cmd" | tee -a "$logfile"

  set +e
  eval "$cmd" >>"$logfile" 2>&1
  rc=$?
  set -e

  # 根据 expect 判断
  if [[ "$expect" == "BLOCK" ]]; then
    if [[ $rc -ne 0 ]] && grep -Eiq '(Direct push .* disabled|禁止直接推送|BLOCK|pre-push|hook refused|protected branch)' "$logfile"; then
      ok "$name -> 正确阻止（rc=$rc）"
      return 0
    else
      bad "$name -> 未阻止或提示缺失（rc=$rc），详见 $logfile"
      return 1
    fi
  else # ALLOW
    if [[ $rc -eq 0 ]]; then
      ok "$name -> 正确允许（rc=0）"
      return 0
    else
      bad "$name -> 误阻止（rc=$rc），详见 $logfile"
      return 1
    fi
  fi
}

# ====== 逐一执行 ======
failcnt=0
for c in "${CASES[@]}"; do
  IFS='|' read -r name cmd expect ref <<<"$c"
  run_case "$name" "$cmd" "$expect" "$ref" || failcnt=$((failcnt+1))
done

# 回到原分支
git checkout -q "$CUR_BRANCH" || true

echo
if [[ $failcnt -eq 0 ]]; then
  ok "本地禁止推送压力测试：全部通过 ✅"
  echo "日志位置：$LOGDIR"
  exit 0
else
  bad "本地禁止推送压力测试：有 $failcnt 个用例失败 ❌"
  echo "请检查对应日志文件（$LOGDIR/*.log）定位钩子规则缺口。"
  exit 1
fi