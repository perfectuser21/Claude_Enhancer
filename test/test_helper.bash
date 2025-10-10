#!/usr/bin/env bash
# Test Helper for BATS tests
# Purpose: Common utilities and assertions for tests

# Load bats support libraries
if [ -z "$BATS_SUPPORT_LOADED" ]; then
    load '/usr/local/lib/bats-support/load' 2>/dev/null || true
    load '/usr/lib/bats-support/load' 2>/dev/null || true
fi

if [ -z "$BATS_ASSERT_LOADED" ]; then
    load '/usr/local/lib/bats-assert/load' 2>/dev/null || true
    load '/usr/lib/bats-assert/load' 2>/dev/null || true
fi

# Custom assertions

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

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    if ! grep -q "$pattern" "$file"; then
        echo "Expected file to contain pattern: $pattern" >&2
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

# Test fixtures

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
    echo "$content" > "$file"
}

# Mocking utilities

mock_command() {
    local cmd="$1"
    local output="$2"
    local exit_code="${3:-0}"

    eval "$cmd() { echo '$output'; return $exit_code; }"
    export -f "$cmd"
}

# Environment setup

setup_test_environment() {
    export CE_DEBUG=0
    export CE_DRY_RUN=1
    export CE_SESSION_ID="test-session-$$"
}

# Cleanup utilities

cleanup_test_files() {
    local pattern="$1"
    find /tmp -name "$pattern" -type f -mtime +1 -delete 2>/dev/null || true
}

# Logging utilities

test_log() {
    echo "# $*" >&3
}

test_debug() {
    if [[ "${TEST_DEBUG:-0}" == "1" ]]; then
        echo "# [DEBUG] $*" >&3
    fi
}
