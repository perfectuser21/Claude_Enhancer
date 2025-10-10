#!/usr/bin/env bash
# Test Helper Functions for CE Commands
# 用于所有测试文件的通用辅助函数

# ============================================================================
# Setup and Teardown Helpers
# ============================================================================

setup_test_repo() {
  # 创建临时测试仓库
  export TEST_REPO_DIR=$(mktemp -d /tmp/ce-test-XXXXXX)
  cd "$TEST_REPO_DIR"

  git init
  git config user.name "CE Test User"
  git config user.email "test@ce.example.com"
  git config init.defaultBranch main

  # 创建初始提交
  echo "# Test Repository" > README.md
  git add README.md
  git commit -m "chore: initial commit"

  # 确保在 main 分支
  git checkout -b main 2>/dev/null || git checkout main

  echo "$TEST_REPO_DIR"
}

setup_clean_repo() {
  # 设置干净的测试仓库（别名）
  setup_test_repo
}

cleanup_test_repo() {
  # 清理测试仓库
  if [[ -n "${TEST_REPO_DIR:-}" && -d "$TEST_REPO_DIR" ]]; then
    cd /
    rm -rf "$TEST_REPO_DIR"
    unset TEST_REPO_DIR
  fi
}

setup_test_repo_with_remote() {
  # 创建带远程仓库的测试环境
  setup_test_repo

  # 创建模拟远程仓库
  export TEST_REMOTE_DIR=$(mktemp -d /tmp/ce-test-remote-XXXXXX)
  git init --bare "$TEST_REMOTE_DIR"

  # 添加远程仓库
  git remote add origin "$TEST_REMOTE_DIR"
  git push -u origin main
}

setup_test_repo_with_commits() {
  # 创建包含多个提交的测试仓库
  setup_test_repo

  echo "feature 1" > feature1.txt
  git add feature1.txt
  git commit -m "feat: add feature 1"

  echo "feature 2" > feature2.txt
  git add feature2.txt
  git commit -m "feat: add feature 2"

  echo "fix issue" > fix.txt
  git add fix.txt
  git commit -m "fix: handle edge case"
}

# ============================================================================
# State Management Helpers
# ============================================================================

init_ce_state() {
  # 初始化 CE 状态目录
  mkdir -p .ce_state
  echo "*" > .ce_state/.gitignore
}

create_sample_state() {
  local terminal_id="$1"
  local branch="${2:-feature/P0-${terminal_id}-sample}"
  local phase="${3:-P0}"

  init_ce_state

  cat > ".ce_state/terminal_${terminal_id}.json" <<EOF
{
  "terminal_id": "${terminal_id}",
  "branch": "${branch}",
  "phase": "${phase}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "active"
}
EOF
}

create_corrupted_state() {
  local terminal_id="$1"

  init_ce_state
  echo "invalid json{" > ".ce_state/terminal_${terminal_id}.json"
}

create_old_state() {
  local terminal_id="$1"
  local days_ago="${2:-7}"

  init_ce_state

  local old_timestamp=$(date -u -d "$days_ago days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
                        date -u -v-${days_ago}d +%Y-%m-%dT%H:%M:%SZ)

  cat > ".ce_state/terminal_${terminal_id}.json" <<EOF
{
  "terminal_id": "${terminal_id}",
  "branch": "feature/P0-${terminal_id}-old",
  "phase": "P0",
  "timestamp": "${old_timestamp}",
  "status": "active"
}
EOF
}

# ============================================================================
# Git Helpers
# ============================================================================

create_and_checkout_branch() {
  local branch_name="$1"
  git checkout -b "$branch_name"
}

create_and_merge_branch() {
  local branch_name="$1"
  local commit_msg="${2:-Test commit}"

  git checkout -b "$branch_name"
  echo "test content" > test.txt
  git add test.txt
  git commit -m "$commit_msg"

  git checkout main
  git merge --no-ff "$branch_name" -m "Merge ${branch_name}"
}

make_test_commit() {
  local msg="${1:-test: sample commit}"
  local filename="${2:-test_$(date +%s).txt}"

  echo "test content" > "$filename"
  git add "$filename"
  git commit -m "$msg"
}

# ============================================================================
# Mock Helpers
# ============================================================================

mock_git_push_failure() {
  # Mock git push 失败（网络错误）
  git() {
    if [[ "$1" == "push" ]]; then
      echo "fatal: unable to access remote: Network error" >&2
      return 1
    else
      command git "$@"
    fi
  }
  export -f git
}

mock_git_push_success() {
  # Mock git push 成功
  git() {
    if [[ "$1" == "push" ]]; then
      echo "To remote"
      echo "   abc123..def456  main -> main"
      return 0
    else
      command git "$@"
    fi
  }
  export -f git
}

unmock_git() {
  # 恢复真实的 git 命令
  unset -f git
}

mock_quality_gate_pass() {
  export MOCK_SCORE=90
  export MOCK_COVERAGE=85
}

mock_quality_gate_fail_score() {
  export MOCK_SCORE=75  # < 85
  export MOCK_COVERAGE=85
}

mock_quality_gate_fail_coverage() {
  export MOCK_SCORE=90
  export MOCK_COVERAGE=70  # < 80
}

unmock_quality_gate() {
  unset MOCK_SCORE
  unset MOCK_COVERAGE
  unset MOCK_SIG
}

# ============================================================================
# Assertion Helpers
# ============================================================================

assert_file_exists() {
  local file="$1"
  local msg="${2:-File should exist: $file}"

  if [[ ! -f "$file" ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    return 1
  fi
}

assert_file_not_exists() {
  local file="$1"
  local msg="${2:-File should not exist: $file}"

  if [[ -f "$file" ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    return 1
  fi
}

assert_dir_exists() {
  local dir="$1"
  local msg="${2:-Directory should exist: $dir}"

  if [[ ! -d "$dir" ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    return 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-String should contain: $needle}"

  if [[ ! "$haystack" =~ $needle ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    echo "Expected to find: $needle" >&2
    echo "In: $haystack" >&2
    return 1
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-String should not contain: $needle}"

  if [[ "$haystack" =~ $needle ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    echo "Did not expect to find: $needle" >&2
    echo "In: $haystack" >&2
    return 1
  fi
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local msg="${3:-Values should be equal}"

  if [[ "$expected" != "$actual" ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    echo "Expected: $expected" >&2
    echo "Actual:   $actual" >&2
    return 1
  fi
}

assert_exit_code() {
  local expected="$1"
  local actual="$2"
  local msg="${3:-Exit code should be $expected}"

  if [[ "$expected" -ne "$actual" ]]; then
    echo "ASSERTION FAILED: $msg" >&2
    echo "Expected exit code: $expected" >&2
    echo "Actual exit code:   $actual" >&2
    return 1
  fi
}

# ============================================================================
# GitHub Helpers
# ============================================================================

setup_github_https_remote() {
  local owner="${1:-testuser}"
  local repo="${2:-testrepo}"

  git remote add origin "https://github.com/${owner}/${repo}.git"
}

setup_github_ssh_remote() {
  local owner="${1:-testuser}"
  local repo="${2:-testrepo}"

  git remote add origin "git@github.com:${owner}/${repo}.git"
}

# ============================================================================
# Evidence Helpers
# ============================================================================

setup_evidence_dir() {
  mkdir -p evidence
  echo "# Test Evidence" > evidence/.gitkeep
}

count_evidence_files() {
  local pattern="${1:-gate_*.log}"
  ls evidence/$pattern 2>/dev/null | wc -l | tr -d ' '
}

get_latest_evidence() {
  local pattern="${1:-gate_*.log}"
  ls -t evidence/$pattern 2>/dev/null | head -1
}

# ============================================================================
# Time Helpers
# ============================================================================

get_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

benchmark_command() {
  local cmd="$1"

  local start_time=$(date +%s.%N)
  eval "$cmd" > /dev/null 2>&1
  local end_time=$(date +%s.%N)

  echo "$end_time - $start_time" | bc
}

# ============================================================================
# JSON Helpers
# ============================================================================

json_get_field() {
  local json="$1"
  local field="$2"

  echo "$json" | jq -r ".$field"
}

json_validate() {
  local json="$1"

  if echo "$json" | jq . > /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# ============================================================================
# Output Helpers
# ============================================================================

log_test() {
  echo "[TEST] $*" >&2
}

log_debug() {
  if [[ "${DEBUG:-0}" == "1" ]]; then
    echo "[DEBUG] $*" >&2
  fi
}

log_error() {
  echo "[ERROR] $*" >&2
}

# ============================================================================
# Cleanup Hooks
# ============================================================================

# 自动注册清理函数（如果在 bats 环境中）
if [[ -n "${BATS_TEST_NAME:-}" ]]; then
  # bats 环境：使用 teardown
  teardown() {
    cleanup_test_repo
    unmock_git
    unmock_quality_gate
  }
fi

# ============================================================================
# Export Functions (for use in subshells)
# ============================================================================

export -f setup_test_repo
export -f setup_clean_repo
export -f cleanup_test_repo
export -f setup_test_repo_with_remote
export -f setup_test_repo_with_commits
export -f init_ce_state
export -f create_sample_state
export -f create_corrupted_state
export -f create_old_state
export -f create_and_checkout_branch
export -f create_and_merge_branch
export -f make_test_commit
export -f mock_git_push_failure
export -f mock_git_push_success
export -f unmock_git
export -f mock_quality_gate_pass
export -f mock_quality_gate_fail_score
export -f mock_quality_gate_fail_coverage
export -f unmock_quality_gate
export -f assert_file_exists
export -f assert_file_not_exists
export -f assert_dir_exists
export -f assert_contains
export -f assert_not_contains
export -f assert_equals
export -f assert_exit_code
export -f setup_github_https_remote
export -f setup_github_ssh_remote
export -f setup_evidence_dir
export -f count_evidence_files
export -f get_latest_evidence
export -f get_timestamp
export -f benchmark_command
export -f json_get_field
export -f json_validate
export -f log_test
export -f log_debug
export -f log_error
