#!/usr/bin/env bash
# Enhanced Test Helper for BATS tests - Claude Enhancer v5.4.0
# Purpose: Comprehensive utilities and assertions for test suite
# Version: 2.0 - Enhanced with 20+ additional utilities

# Load bats support libraries
if [ -z "$BATS_SUPPORT_LOADED" ]; then
    load '/usr/local/lib/bats-support/load' 2>/dev/null || true
    load '/usr/lib/bats-support/load' 2>/dev/null || true
fi

if [ -z "$BATS_ASSERT_LOADED" ]; then
    load '/usr/local/lib/bats-assert/load' 2>/dev/null || true
    load '/usr/lib/bats-assert/load' 2>/dev/null || true
fi

# ============================================================================
# Custom Assertions
# ============================================================================

assert_file_exists() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "Expected file to exist: $file" >&2
        return 1
    fi
}

assert_file_not_exists() {
    local file="$1"
    if [[ -f "$file" ]]; then
        echo "Expected file to not exist: $file" >&2
        return 1
    fi
}

assert_directory_exists() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        echo "Expected directory to exist: $dir" >&2
        return 1
    fi
}

assert_directory_not_exists() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        echo "Expected directory to not exist: $dir" >&2
        return 1
    fi
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    if ! grep -q "$pattern" "$file"; then
        echo "Expected file to contain pattern: $pattern" >&2
        echo "File: $file" >&2
        return 1
    fi
}

assert_file_not_contains() {
    local file="$1"
    local pattern="$2"
    if grep -q "$pattern" "$file"; then
        echo "Expected file to NOT contain pattern: $pattern" >&2
        echo "File: $file" >&2
        return 1
    fi
}

assert_command_exists() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        echo "Expected command to exist: $cmd" >&2
        return 1
    fi
}

assert_git_clean() {
    if ! git diff-index --quiet HEAD --; then
        echo "Expected clean git working directory" >&2
        return 1
    fi
}

assert_git_dirty() {
    if git diff-index --quiet HEAD --; then
        echo "Expected dirty git working directory" >&2
        return 1
    fi
}

assert_branch_exists() {
    local branch="$1"
    if ! git rev-parse --verify --quiet "refs/heads/${branch}" > /dev/null; then
        echo "Expected branch to exist: $branch" >&2
        return 1
    fi
}

assert_tag_exists() {
    local tag="$1"
    if ! git rev-parse --verify --quiet "refs/tags/${tag}" > /dev/null; then
        echo "Expected tag to exist: $tag" >&2
        return 1
    fi
}

assert_file_executable() {
    local file="$1"
    if [[ ! -x "$file" ]]; then
        echo "Expected file to be executable: $file" >&2
        return 1
    fi
}

assert_file_not_executable() {
    local file="$1"
    if [[ -x "$file" ]]; then
        echo "Expected file to NOT be executable: $file" >&2
        return 1
    fi
}

assert_json_valid() {
    local json="$1"
    if ! echo "$json" | jq empty 2>/dev/null; then
        echo "Expected valid JSON" >&2
        return 1
    fi
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    if [[ "$actual" != "$expected" ]]; then
        echo "Expected exit code $expected, got $actual" >&2
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "Expected '$haystack' to contain '$needle'" >&2
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" == *"$needle"* ]]; then
        echo "Expected '$haystack' to NOT contain '$needle'" >&2
        return 1
    fi
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    if [[ "$expected" != "$actual" ]]; then
        echo "Expected '$expected', got '$actual'" >&2
        return 1
    fi
}

assert_greater_than() {
    local value="$1"
    local threshold="$2"
    if [[ ! "$value" -gt "$threshold" ]]; then
        echo "Expected $value > $threshold" >&2
        return 1
    fi
}

assert_less_than() {
    local value="$1"
    local threshold="$2"
    if [[ ! "$value" -lt "$threshold" ]]; then
        echo "Expected $value < $threshold" >&2
        return 1
    fi
}

# ============================================================================
# Test Fixtures
# ============================================================================

create_test_git_repo() {
    local repo_dir="${1:-$(mktemp -d)}"
    mkdir -p "$repo_dir"
    cd "$repo_dir"
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
    echo "$repo_dir"
}

create_test_file() {
    local file="$1"
    local content="${2:-test content}"
    mkdir -p "$(dirname "$file")"
    echo "$content" > "$file"
}

create_test_commit() {
    local message="${1:-test commit}"
    create_test_file "test_${RANDOM}.txt" "test content"
    git add .
    git commit -m "$message"
}

create_test_branch() {
    local branch="$1"
    git checkout -b "$branch"
}

create_test_tag() {
    local tag="$1"
    local message="${2:-test tag}"
    git tag -a "$tag" -m "$message"
}

create_remote_repo() {
    local remote_dir="$(mktemp -d)"
    cd "$remote_dir"
    git init --bare
    echo "$remote_dir"
}

setup_git_hooks() {
    mkdir -p .git/hooks
    cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
echo "pre-commit hook executed"
exit 0
EOF
    chmod +x .git/hooks/pre-commit
}

# ============================================================================
# Mocking Utilities
# ============================================================================

mock_command() {
    local cmd="$1"
    local output="$2"
    local exit_code="${3:-0}"

    eval "$cmd() { echo '$output'; return $exit_code; }"
    export -f "$cmd"
}

mock_command_with_script() {
    local cmd="$1"
    local script="$2"

    eval "$cmd() { $script; }"
    export -f "$cmd"
}

mock_git_command() {
    local subcommand="$1"
    local output="$2"
    local exit_code="${3:-0}"

    # Create a temporary git wrapper
    local mock_dir="/tmp/ce_test_mocks"
    mkdir -p "$mock_dir"

    cat > "$mock_dir/git" <<EOF
#!/bin/bash
if [[ "\$1" == "$subcommand" ]]; then
    echo "$output"
    exit $exit_code
else
    command git "\$@"
fi
EOF
    chmod +x "$mock_dir/git"
    export PATH="$mock_dir:$PATH"
}

mock_gh_command() {
    local output="$1"
    local exit_code="${2:-0}"

    local mock_dir="/tmp/ce_test_mocks"
    mkdir -p "$mock_dir"

    cat > "$mock_dir/gh" <<EOF
#!/bin/bash
echo "$output"
exit $exit_code
EOF
    chmod +x "$mock_dir/gh"
    export PATH="$mock_dir:$PATH"
}

restore_commands() {
    # Remove mock directory from PATH
    export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "/tmp/ce_test_mocks" | tr '\n' ':')
}

# ============================================================================
# Environment Setup
# ============================================================================

setup_test_environment() {
    export CE_DEBUG=0
    export CE_DRY_RUN=1
    export CE_SESSION_ID="test-session-$$"
    export CE_AUDIT_SECRET="test-secret-key-for-testing-only-$(openssl rand -hex 16)"
}

setup_automation_environment() {
    setup_test_environment
    export CE_AUTO_PUSH=1
    export CE_AUTO_MERGE=0
    export CE_FORCE_PUSH=0
    export CE_PR_DRAFT=0
}

cleanup_test_environment() {
    unset CE_DEBUG
    unset CE_DRY_RUN
    unset CE_SESSION_ID
    unset CE_AUDIT_SECRET
    unset CE_AUTO_PUSH
    unset CE_AUTO_MERGE
    unset CE_FORCE_PUSH
    unset CE_PR_DRAFT
}

# ============================================================================
# Cleanup Utilities
# ============================================================================

cleanup_test_files() {
    local pattern="$1"
    find /tmp -name "$pattern" -type f -mtime +1 -delete 2>/dev/null || true
}

cleanup_test_dirs() {
    local pattern="$1"
    find /tmp -name "$pattern" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null || true
}

cleanup_locks() {
    rm -rf /tmp/ce_locks 2>/dev/null || true
    rm -rf /tmp/ce_test_mocks 2>/dev/null || true
}

# ============================================================================
# Logging Utilities
# ============================================================================

test_log() {
    echo "# $*" >&3
}

test_debug() {
    if [[ "${TEST_DEBUG:-0}" == "1" ]]; then
        echo "# [DEBUG] $*" >&3
    fi
}

test_error() {
    echo "# [ERROR] $*" >&3
}

test_warning() {
    echo "# [WARNING] $*" >&3
}

# ============================================================================
# Time Utilities
# ============================================================================

get_timestamp() {
    date +%s
}

measure_execution_time() {
    local start=$SECONDS
    "$@"
    local duration=$((SECONDS - start))
    echo "$duration"
}

assert_execution_time_under() {
    local max_seconds="$1"
    shift
    local duration=$(measure_execution_time "$@")

    if [[ $duration -gt $max_seconds ]]; then
        echo "Execution took ${duration}s, expected < ${max_seconds}s" >&2
        return 1
    fi
}

# ============================================================================
# File Comparison Utilities
# ============================================================================

assert_files_equal() {
    local file1="$1"
    local file2="$2"

    if ! diff -q "$file1" "$file2" &>/dev/null; then
        echo "Files are not equal:" >&2
        echo "  $file1" >&2
        echo "  $file2" >&2
        diff "$file1" "$file2" >&2
        return 1
    fi
}

assert_json_equals() {
    local json1="$1"
    local json2="$2"

    local sorted1=$(echo "$json1" | jq -S .)
    local sorted2=$(echo "$json2" | jq -S .)

    if [[ "$sorted1" != "$sorted2" ]]; then
        echo "JSON values are not equal" >&2
        return 1
    fi
}

# ============================================================================
# Network Utilities
# ============================================================================

wait_for_port() {
    local port="$1"
    local timeout="${2:-30}"
    local start=$(date +%s)

    while ! nc -z localhost "$port" 2>/dev/null; do
        local elapsed=$(($(date +%s) - start))
        if [[ $elapsed -gt $timeout ]]; then
            echo "Port $port not available after ${timeout}s" >&2
            return 1
        fi
        sleep 1
    done
}

# ============================================================================
# Git Test Utilities
# ============================================================================

count_commits() {
    git rev-list --count HEAD
}

get_last_commit_message() {
    git log -1 --pretty=format:"%s"
}

get_commit_files() {
    git diff-tree --no-commit-id --name-only -r HEAD
}

is_git_repo() {
    git rev-parse --git-dir > /dev/null 2>&1
}

# ============================================================================
# Process Management
# ============================================================================

wait_for_process() {
    local pid="$1"
    local timeout="${2:-10}"

    local start=$(date +%s)
    while kill -0 "$pid" 2>/dev/null; do
        local elapsed=$(($(date +%s) - start))
        if [[ $elapsed -gt $timeout ]]; then
            kill -9 "$pid" 2>/dev/null || true
            return 1
        fi
        sleep 0.5
    done
}

# ============================================================================
# Security Test Utilities
# ============================================================================

generate_test_hmac() {
    local data="$1"
    local secret="${CE_AUDIT_SECRET:-test-secret}"
    echo -n "$data" | openssl dgst -sha256 -hmac "$secret" | awk '{print $2}'
}

create_audit_entry() {
    local event_type="$1"
    local action="$2"
    local resource="$3"
    local result="$4"

    cat <<EOF
{
  "audit_id": "test-$(date +%s)",
  "timestamp": "$(date --iso-8601=seconds)",
  "event_type": "$event_type",
  "action": "$action",
  "resource": "$resource",
  "result": "$result",
  "user": "test-user",
  "session_id": "test-session",
  "ip_address": "127.0.0.1"
}
EOF
}

# ============================================================================
# Export Functions
# ============================================================================

export -f assert_file_exists assert_file_not_exists
export -f assert_directory_exists assert_directory_not_exists
export -f assert_file_contains assert_file_not_contains
export -f assert_command_exists
export -f assert_git_clean assert_git_dirty
export -f assert_branch_exists assert_tag_exists
export -f assert_file_executable assert_file_not_executable
export -f assert_json_valid assert_exit_code
export -f assert_contains assert_not_contains assert_equals
export -f assert_greater_than assert_less_than
export -f create_test_git_repo create_test_file create_test_commit
export -f create_test_branch create_test_tag create_remote_repo
export -f setup_git_hooks
export -f mock_command mock_command_with_script
export -f mock_git_command mock_gh_command restore_commands
export -f setup_test_environment setup_automation_environment
export -f cleanup_test_environment cleanup_test_files cleanup_test_dirs
export -f cleanup_locks
export -f test_log test_debug test_error test_warning
export -f get_timestamp measure_execution_time assert_execution_time_under
export -f assert_files_equal assert_json_equals
export -f wait_for_port
export -f count_commits get_last_commit_message get_commit_files is_git_repo
export -f wait_for_process
export -f generate_test_hmac create_audit_entry
