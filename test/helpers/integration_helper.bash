#!/bin/bash
# =============================================================================
# Integration Test Helpers
# Common functions for setting up and tearing down test environments
# =============================================================================

# Test repository management
create_test_repo() {
    local repo_name="${1:-test-repo}"
    local test_dir="${BATS_TEST_TMPDIR}/${repo_name}"

    mkdir -p "${test_dir}"
    cd "${test_dir}"

    git init -q
    git config user.email "test@example.com"
    git config user.name "Test User"

    # Create initial commit
    echo "# Test Repository" > README.md
    git add README.md
    git commit -q -m "Initial commit"

    # Setup Claude Enhancer structure
    mkdir -p .phase .gates .workflow docs src test
    echo "P1" > .phase/current

    # Copy essential files from main repo
    if [[ -f "${PROJECT_ROOT}/.workflow/executor.sh" ]]; then
        cp -r "${PROJECT_ROOT}/.workflow" .workflow/
    fi

    if [[ -f "${PROJECT_ROOT}/.workflow/gates.yml" ]]; then
        cp "${PROJECT_ROOT}/.workflow/gates.yml" .workflow/
    fi

    echo "${test_dir}"
}

cleanup_test_repo() {
    local test_dir="$1"
    if [[ -d "${test_dir}" ]]; then
        cd /
        rm -rf "${test_dir}"
    fi
}

# Phase management helpers
set_phase() {
    local phase="$1"
    echo "${phase}" > .phase/current

    # Also update .workflow/ACTIVE if it exists
    if [[ -f .workflow/ACTIVE ]]; then
        cat > .workflow/ACTIVE << EOF
phase: ${phase}
ticket: test-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
    fi
}

get_current_phase() {
    if [[ -f .phase/current ]]; then
        cat .phase/current | tr -d '\n\r'
    else
        echo "P1"
    fi
}

# Gate management helpers
create_gate() {
    local gate_num="$1"
    local phase="${2:-P${gate_num}}"

    mkdir -p .gates
    touch ".gates/${gate_num}.ok"
    echo "Gate ${gate_num} created for ${phase}" > ".gates/${gate_num}.ok"
}

check_gate_exists() {
    local gate_num="$1"
    [[ -f ".gates/${gate_num}.ok" ]]
}

# File creation helpers
create_plan_document() {
    cat > docs/PLAN.md << 'EOF'
# Feature Plan

## 任务清单
1. 实现用户认证模块
2. 创建登录接口
3. 添加JWT token验证
4. 实现密码加密
5. 编写单元测试

## 受影响文件清单
- src/auth/login.ts
- src/auth/auth.service.ts
- src/middleware/auth.middleware.ts
- test/auth/auth.test.ts

## 回滚方案
1. 删除新增的auth模块
2. 恢复原有的临时认证逻辑
3. 回滚数据库迁移
EOF
}

create_skeleton_notes() {
    cat > docs/SKELETON-NOTES.md << 'EOF'
# Skeleton Notes

## 架构设计
- 采用分层架构
- 使用依赖注入
- 遵循SOLID原则

## 接口定义
- IAuthService
- IUserRepository
- ITokenService
EOF
}

create_changelog() {
    cat > docs/CHANGELOG.md << 'EOF'
# Changelog

## Unreleased
- 添加用户认证功能
- 实现JWT token验证
- 增强安全性

## v1.0.0 - 2024-01-01
- 初始版本
EOF
}

create_test_report() {
    cat > docs/TEST-REPORT.md << 'EOF'
# Test Report

## 测试覆盖率
- 单元测试: 85%
- 集成测试: 70%
- E2E测试: 60%

## 测试结果
- 总测试数: 42
- 通过: 40
- 失败: 2
- 跳过: 0

## 边界测试
- 空输入测试: ✅
- 超长输入测试: ✅
- 并发测试: ✅
EOF
}

create_review_document() {
    cat > docs/REVIEW.md << 'EOF'
# Code Review

## 风格一致性
代码遵循项目规范，命名清晰，注释完整。

## 风险清单
1. JWT密钥管理需要加强
2. 密码复杂度验证待完善

## 回滚可行性
回滚方案清晰，已经过验证。

APPROVE
EOF
}

create_readme() {
    cat > docs/README.md << 'EOF'
# Project README

## 安装
npm install

## 使用
npm start

## 注意事项
确保Node.js版本 >= 18
EOF
}

# Git helpers
commit_file() {
    local file="$1"
    local message="${2:-Update file}"

    git add "${file}"
    git commit -q -m "${message}" 2>&1 || echo "Commit may have failed"
}

create_branch() {
    local branch_name="$1"
    git checkout -q -b "${branch_name}" 2>&1
}

merge_branch() {
    local branch_name="$1"
    local target="${2:-main}"

    git checkout -q "${target}" 2>&1
    git merge -q --no-ff "${branch_name}" -m "Merge ${branch_name}" 2>&1
}

# Validation helpers
assert_file_exists() {
    local file="$1"
    [[ -f "${file}" ]] || return 1
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    grep -q "${pattern}" "${file}" 2>/dev/null
}

assert_phase_is() {
    local expected="$1"
    local actual=$(get_current_phase)
    [[ "${actual}" == "${expected}" ]]
}

# Workflow executor helpers
run_executor() {
    local command="$1"
    shift

    if [[ -f .workflow/executor.sh ]]; then
        bash .workflow/executor.sh "${command}" "$@" 2>&1
    else
        echo "ERROR: executor.sh not found"
        return 1
    fi
}

validate_current_phase() {
    run_executor validate
}

progress_to_next_phase() {
    run_executor next
}

# Multi-terminal simulation helpers
export_terminal_env() {
    local terminal_id="$1"
    export CE_TERMINAL_ID="${terminal_id}"
    export CE_FEATURE_BRANCH="feature-${terminal_id}"
    export CE_SESSION_DIR=".workflow/sessions/${terminal_id}"
}

cleanup_terminal_env() {
    unset CE_TERMINAL_ID
    unset CE_FEATURE_BRANCH
    unset CE_SESSION_DIR
}

# Conflict detection helpers
create_conflicting_file() {
    local file="$1"
    local content="$2"

    mkdir -p "$(dirname "${file}")"
    echo "${content}" > "${file}"
}

simulate_multi_terminal_edit() {
    local file="$1"
    local terminal1_content="$2"
    local terminal2_content="$3"

    # Terminal 1 edits
    export_terminal_env "t1"
    create_branch "feature-t1"
    create_conflicting_file "${file}" "${terminal1_content}"
    commit_file "${file}" "Terminal 1 changes"
    cleanup_terminal_env

    # Terminal 2 edits
    export_terminal_env "t2"
    git checkout -q main 2>&1
    create_branch "feature-t2"
    create_conflicting_file "${file}" "${terminal2_content}"
    commit_file "${file}" "Terminal 2 changes"
    cleanup_terminal_env

    git checkout -q main 2>&1
}

# Performance helpers
measure_execution_time() {
    local start=$(date +%s%N)
    "$@"
    local end=$(date +%s%N)
    local duration=$(( (end - start) / 1000000 ))
    echo "${duration}"
}

# Output helpers
log_test_info() {
    echo "# $*" >&3
}

log_test_debug() {
    echo "# [DEBUG] $*" >&3
}

# Snapshot helpers
take_snapshot() {
    local snapshot_name="$1"
    local snapshot_dir=".snapshots/${snapshot_name}"

    mkdir -p "${snapshot_dir}"

    # Save current state
    cp -r .phase "${snapshot_dir}/"
    cp -r .gates "${snapshot_dir}/" 2>/dev/null || true
    cp -r docs "${snapshot_dir}/" 2>/dev/null || true

    git rev-parse HEAD > "${snapshot_dir}/commit.txt"
}

restore_snapshot() {
    local snapshot_name="$1"
    local snapshot_dir=".snapshots/${snapshot_name}"

    if [[ -d "${snapshot_dir}" ]]; then
        cp -r "${snapshot_dir}/.phase" .
        cp -r "${snapshot_dir}/.gates" . 2>/dev/null || true
        cp -r "${snapshot_dir}/docs" . 2>/dev/null || true

        if [[ -f "${snapshot_dir}/commit.txt" ]]; then
            local commit=$(cat "${snapshot_dir}/commit.txt")
            git reset --hard "${commit}" 2>&1 || true
        fi
    fi
}

# Export functions for BATS tests
export -f create_test_repo
export -f cleanup_test_repo
export -f set_phase
export -f get_current_phase
export -f create_gate
export -f check_gate_exists
export -f create_plan_document
export -f create_skeleton_notes
export -f create_changelog
export -f create_test_report
export -f create_review_document
export -f create_readme
export -f commit_file
export -f create_branch
export -f merge_branch
export -f assert_file_exists
export -f assert_file_contains
export -f assert_phase_is
export -f run_executor
export -f validate_current_phase
export -f progress_to_next_phase
export -f export_terminal_env
export -f cleanup_terminal_env
export -f create_conflicting_file
export -f simulate_multi_terminal_edit
export -f measure_execution_time
export -f log_test_info
export -f log_test_debug
export -f take_snapshot
export -f restore_snapshot
