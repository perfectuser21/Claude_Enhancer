#!/usr/bin/env bats
# Example Unit Tests for Branch Manager
# 这是一个示例测试文件，展示如何为 ce 命令编写单元测试

# 加载测试辅助函数
load ../helpers/test_helpers

# ============================================================================
# Setup and Teardown
# ============================================================================

setup() {
  # 每个测试前执行
  setup_test_repo
  source "$BATS_TEST_DIRNAME/../../lib/branch_manager.sh" 2>/dev/null || true
}

teardown() {
  # 每个测试后执行
  cleanup_test_repo
}

# ============================================================================
# Branch Naming Tests
# ============================================================================

@test "branch_manager: generates correct P0 branch name" {
  # 模拟函数（实际实现时替换）
  generate_branch_name() {
    local phase="$1"
    local terminal="$2"
    local task="$3"
    echo "feature/${phase}-${terminal}-${task}"
  }

  result=$(generate_branch_name "P0" "t1" "login")

  assert_equals "feature/P0-t1-login" "$result"
}

@test "branch_manager: generates correct P3 branch name" {
  generate_branch_name() {
    local phase="$1"
    local terminal="$2"
    local task="$3"
    echo "feature/${phase}-${terminal}-${task}"
  }

  result=$(generate_branch_name "P3" "t2" "payment-api")

  assert_equals "feature/P3-t2-payment-api" "$result"
}

@test "branch_manager: sanitizes special characters in task name" {
  generate_branch_name() {
    local phase="$1"
    local terminal="$2"
    local task="$3"
    # 移除特殊字符，替换为 -
    task=$(echo "$task" | sed 's/[^a-zA-Z0-9-]/-/g' | sed 's/--*/-/g')
    echo "feature/${phase}-${terminal}-${task}"
  }

  result=$(generate_branch_name "P1" "t1" "fix: user@email.com")

  assert_equals "feature/P1-t1-fix-user-email-com" "$result"
}

@test "branch_manager: rejects invalid phase parameter" {
  validate_phase() {
    local phase="$1"
    if [[ ! "$phase" =~ ^P[0-7]$ ]]; then
      echo "Invalid phase: $phase (must be P0-P7)"
      return 1
    fi
  }

  run validate_phase "P8"
  [ "$status" -eq 1 ]
  assert_contains "$output" "Invalid phase"
}

@test "branch_manager: accepts all valid phases P0-P7" {
  validate_phase() {
    local phase="$1"
    if [[ ! "$phase" =~ ^P[0-7]$ ]]; then
      echo "Invalid phase: $phase (must be P0-P7)"
      return 1
    fi
    return 0
  }

  for phase in P0 P1 P2 P3 P4 P5 P6 P7; do
    run validate_phase "$phase"
    [ "$status" -eq 0 ]
  done
}

# ============================================================================
# Branch Creation Tests
# ============================================================================

@test "branch_manager: creates branch successfully from main" {
  # 确保在 main 分支
  git checkout main

  # 创建新分支
  git checkout -b "feature/P0-t1-test"

  # 验证当前分支
  current_branch=$(git rev-parse --abbrev-ref HEAD)
  assert_equals "feature/P0-t1-test" "$current_branch"
}

@test "branch_manager: detects existing branch conflict" {
  # 创建已存在的分支
  git checkout -b "feature/P0-t1-existing"
  git checkout main

  # 尝试再次创建同名分支
  create_branch() {
    local branch="$1"
    if git show-ref --verify --quiet "refs/heads/$branch"; then
      echo "Error: Branch $branch already exists"
      return 1
    fi
    git checkout -b "$branch"
  }

  run create_branch "feature/P0-t1-existing"
  [ "$status" -eq 1 ]
  assert_contains "$output" "already exists"
}

@test "branch_manager: requires starting from main branch" {
  # 创建并切换到非 main 分支
  git checkout -b "feature/other"

  # 验证分支检查函数
  is_on_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    [[ "$current_branch" =~ ^(main|master)$ ]]
  }

  run is_on_main_branch
  [ "$status" -eq 1 ]

  # 切换到 main
  git checkout main
  run is_on_main_branch
  [ "$status" -eq 0 ]
}

# ============================================================================
# Branch Validation Tests
# ============================================================================

@test "branch_manager: validates correct branch naming convention" {
  validate_branch_name() {
    local branch="$1"
    if [[ "$branch" =~ ^feature/P[0-7]-t[0-9]+-[a-z0-9-]+$ ]]; then
      return 0
    else
      echo "Invalid branch name format"
      return 1
    fi
  }

  run validate_branch_name "feature/P0-t1-login"
  [ "$status" -eq 0 ]

  run validate_branch_name "feature/P3-t2-payment-api"
  [ "$status" -eq 0 ]
}

@test "branch_manager: rejects invalid branch format" {
  validate_branch_name() {
    local branch="$1"
    if [[ "$branch" =~ ^feature/P[0-7]-t[0-9]+-[a-z0-9-]+$ ]]; then
      return 0
    else
      echo "Invalid branch name format"
      return 1
    fi
  }

  run validate_branch_name "my-random-branch"
  [ "$status" -eq 1 ]
  assert_contains "$output" "Invalid branch name format"
}

@test "branch_manager: rejects missing terminal ID" {
  validate_branch_name() {
    local branch="$1"
    if [[ "$branch" =~ ^feature/P[0-7]-t[0-9]+-[a-z0-9-]+$ ]]; then
      return 0
    else
      echo "Invalid branch name format"
      return 1
    fi
  }

  run validate_branch_name "feature/P0--login"
  [ "$status" -eq 1 ]
}

# ============================================================================
# Main Branch Detection Tests
# ============================================================================

@test "branch_manager: detects main branch correctly" {
  is_on_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    [[ "$current_branch" =~ ^(main|master)$ ]]
  }

  git checkout main
  run is_on_main_branch
  [ "$status" -eq 0 ]
}

@test "branch_manager: detects master branch as main" {
  # 创建 master 分支（老项目）
  git checkout -b master 2>/dev/null || git checkout master

  is_on_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    [[ "$current_branch" =~ ^(main|master)$ ]]
  }

  run is_on_main_branch
  [ "$status" -eq 0 ]
}

@test "branch_manager: detects non-main branch correctly" {
  is_on_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    [[ "$current_branch" =~ ^(main|master)$ ]]
  }

  git checkout -b "feature/test"
  run is_on_main_branch
  [ "$status" -eq 1 ]
}

# ============================================================================
# Branch Cleanup Tests
# ============================================================================

@test "branch_manager: cleans up fully merged branch" {
  # 创建并合并分支
  create_and_merge_branch "feature/P0-t1-test"

  # 删除已合并的分支
  cleanup_merged_branch() {
    local branch="$1"
    # 检查是否已合并
    if git branch --merged main | grep -q "$branch"; then
      git branch -d "$branch"
      echo "Branch $branch cleaned up"
      return 0
    else
      echo "Branch $branch is not fully merged"
      return 1
    fi
  }

  run cleanup_merged_branch "feature/P0-t1-test"
  [ "$status" -eq 0 ]
  assert_contains "$output" "cleaned up"

  # 验证分支已删除
  run git show-ref --verify --quiet "refs/heads/feature/P0-t1-test"
  [ "$status" -ne 0 ]
}

@test "branch_manager: protects unmerged branch from cleanup" {
  # 创建未合并的分支
  git checkout -b "feature/P0-t1-test"
  make_test_commit "test: unmerged commit"
  git checkout main

  cleanup_merged_branch() {
    local branch="$1"
    if git branch --merged main | grep -q "$branch"; then
      git branch -d "$branch"
      return 0
    else
      echo "Branch $branch is not fully merged"
      return 1
    fi
  }

  run cleanup_merged_branch "feature/P0-t1-test"
  [ "$status" -eq 1 ]
  assert_contains "$output" "not fully merged"

  # 验证分支仍存在
  run git show-ref --verify --quiet "refs/heads/feature/P0-t1-test"
  [ "$status" -eq 0 ]
}

@test "branch_manager: deletes both local and remote branch" {
  # 设置带远程的测试仓库
  setup_test_repo_with_remote

  # 创建并推送分支
  git checkout -b "feature/P0-t1-test"
  make_test_commit
  git push -u origin "feature/P0-t1-test"

  # 合并到 main
  git checkout main
  git merge --no-ff "feature/P0-t1-test" -m "Merge test"

  # 清理本地和远程分支
  cleanup_branch_full() {
    local branch="$1"
    git branch -d "$branch"
    git push origin --delete "$branch" 2>/dev/null || true
  }

  cleanup_branch_full "feature/P0-t1-test"

  # 验证本地分支已删除
  run git show-ref --verify --quiet "refs/heads/feature/P0-t1-test"
  [ "$status" -ne 0 ]
}

# ============================================================================
# Error Handling Tests
# ============================================================================

@test "branch_manager: handles git errors gracefully" {
  # 模拟 Git 错误
  git() {
    if [[ "$1" == "checkout" && "$2" == "-b" ]]; then
      echo "fatal: A branch named 'feature/P0-t1-test' already exists."
      return 128
    fi
    command git "$@"
  }

  run git checkout -b "feature/P0-t1-test"
  [ "$status" -eq 128 ]
  assert_contains "$output" "already exists"
}

@test "branch_manager: provides helpful error messages" {
  create_branch() {
    local branch="$1"
    if [[ ! "$branch" =~ ^feature/P[0-7]-t[0-9]+-[a-z0-9-]+$ ]]; then
      cat >&2 <<EOF
Error: Invalid branch name format

Expected format: feature/P<0-7>-t<terminal_id>-<task_name>
Example: feature/P0-t1-login

Your input: $branch
EOF
      return 1
    fi
  }

  run create_branch "invalid-branch"
  [ "$status" -eq 1 ]
  assert_contains "$output" "Invalid branch name format"
  assert_contains "$output" "Expected format"
  assert_contains "$output" "Example"
}

# ============================================================================
# Edge Cases Tests
# ============================================================================

@test "branch_manager: handles very long task names" {
  generate_branch_name() {
    local phase="$1"
    local terminal="$2"
    local task="$3"

    # 限制任务名长度
    if [ ${#task} -gt 50 ]; then
      task="${task:0:47}..."
    fi

    echo "feature/${phase}-${terminal}-${task}"
  }

  long_task="this-is-a-very-long-task-name-that-exceeds-the-maximum-allowed-length-for-a-branch-name"

  result=$(generate_branch_name "P0" "t1" "$long_task")

  # 验证长度被限制
  [ ${#result} -lt 100 ]
  assert_contains "$result" "..."
}

@test "branch_manager: handles empty task name" {
  create_branch() {
    local task="$1"
    if [[ -z "$task" ]]; then
      echo "Error: Task name cannot be empty"
      return 1
    fi
  }

  run create_branch ""
  [ "$status" -eq 1 ]
  assert_contains "$output" "cannot be empty"
}

@test "branch_manager: handles concurrent branch creation attempts" {
  # 模拟并发场景（简化版）
  create_branch_atomic() {
    local branch="$1"

    # 使用 Git 的原子性保证
    if git checkout -b "$branch" 2>&1; then
      echo "Branch created successfully"
      return 0
    else
      echo "Branch creation failed (may already exist)"
      return 1
    fi
  }

  # 第一次创建应该成功
  run create_branch_atomic "feature/P0-t1-concurrent"
  [ "$status" -eq 0 ]

  # 第二次创建应该失败
  git checkout main
  run create_branch_atomic "feature/P0-t1-concurrent"
  [ "$status" -eq 1 ]
}

# ============================================================================
# Performance Tests
# ============================================================================

@test "branch_manager: branch creation completes in < 1 second" {
  skip "Performance test - run manually"

  duration=$(benchmark_command "git checkout -b feature/P0-t1-perf-test")

  # 验证性能（1 秒 = 1.0）
  if (( $(echo "$duration > 1.0" | bc -l) )); then
    echo "Performance issue: branch creation took ${duration}s"
    return 1
  fi
}

# ============================================================================
# Integration with State Manager Tests
# ============================================================================

@test "branch_manager: updates state after branch creation" {
  # 模拟状态更新
  update_state_after_branch_creation() {
    local terminal="$1"
    local branch="$2"

    init_ce_state
    create_sample_state "$terminal" "$branch" "P0"
  }

  update_state_after_branch_creation "t1" "feature/P0-t1-test"

  # 验证状态文件创建
  assert_file_exists ".ce_state/terminal_t1.json"

  # 验证状态内容
  branch=$(jq -r '.branch' .ce_state/terminal_t1.json)
  assert_equals "feature/P0-t1-test" "$branch"
}
