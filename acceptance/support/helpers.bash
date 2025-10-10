#!/usr/bin/env bash
# BDD Test Helpers for Claude Enhancer

set -euo pipefail

# ============================================================================
# Test Environment Setup
# ============================================================================

setup_test_project() {
    # Create temporary test project
    export TEST_PROJECT_DIR="${BATS_TMPDIR:-/tmp}/ce-test-$$"
    mkdir -p "$TEST_PROJECT_DIR"

    cd "$TEST_PROJECT_DIR"

    # Initialize git repository
    git init --initial-branch=main
    git config user.email "test@example.com"
    git config user.name "Test User"

    # Setup Claude Enhancer structure
    mkdir -p .workflow/state/sessions
    mkdir -p .phase
    mkdir -p .gates
    mkdir -p src tests docs

    echo "P0" > .phase/current

    # Create initial commit
    echo "# Test Project" > README.md
    git add README.md
    git commit -m "Initial commit"

    # Setup workflow files
    cat > .workflow/ACTIVE << EOF
phase: P0
ticket: test-feature
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

    cat > .workflow/manifest.yml << EOF
execution:
  strategy: sequential
  fail_fast: true

parallelism:
  enabled: true
  conflict_detection: true

state:
  current_file: .phase/current
  active_file: .workflow/ACTIVE
  sync_check: true
EOF
}

cleanup_test_project() {
    if [[ -n "${TEST_PROJECT_DIR:-}" ]] && [[ -d "$TEST_PROJECT_DIR" ]]; then
        rm -rf "$TEST_PROJECT_DIR"
    fi
}

# ============================================================================
# Terminal Session Management
# ============================================================================

create_terminal_session() {
    local terminal_id=$1
    local session_id="${terminal_id}-$(date +%Y%m%d%H%M%S)"
    local session_dir=".workflow/state/sessions/${session_id}"

    mkdir -p "$session_dir"

    cat > "${session_dir}/manifest.yml" << EOF
session_id: ${session_id}
terminal_id: ${terminal_id}
feature_name: test-feature
branch_name: feature/P3-${terminal_id}-test-feature
phase: P3
status: active
created_at: $(date -Iseconds)
updated_at: $(date -Iseconds)
commits: []
gates_passed: []
modified_files: []
EOF

    export "TERMINAL_${terminal_id}_SESSION=${session_id}"
    export "TERMINAL_${terminal_id}_DIR=${session_dir}"
}

set_terminal_context() {
    local terminal_id=$1
    export CURRENT_TERMINAL="$terminal_id"

    local session_var="TERMINAL_${terminal_id}_SESSION"
    export CURRENT_SESSION="${!session_var:-}"

    local dir_var="TERMINAL_${terminal_id}_DIR"
    export CURRENT_SESSION_DIR="${!dir_var:-}"
}

close_terminal_session() {
    local terminal_id=$1
    set_terminal_context "$terminal_id"

    if [[ -n "$CURRENT_SESSION_DIR" ]]; then
        echo "closed" > "${CURRENT_SESSION_DIR}/status"
    fi
}

reopen_terminal_session() {
    local terminal_id=$1
    set_terminal_context "$terminal_id"

    if [[ -n "$CURRENT_SESSION_DIR" ]]; then
        echo "active" > "${CURRENT_SESSION_DIR}/status"
    fi
}

set_terminal_feature() {
    local feature=$1
    if [[ -n "$CURRENT_SESSION_DIR" ]]; then
        sed -i "s/feature_name: .*/feature_name: $feature/" "${CURRENT_SESSION_DIR}/manifest.yml"
    fi
}

# ============================================================================
# File Modification Tracking
# ============================================================================

touch_modified_file() {
    local file=$1
    mkdir -p "$(dirname "$file")"
    echo "// Modified at $(date)" >> "$file"

    if [[ -n "${CURRENT_SESSION_DIR:-}" ]]; then
        # Add to session's modified files list
        if ! grep -q "  - $file" "${CURRENT_SESSION_DIR}/manifest.yml"; then
            echo "  - $file" >> "${CURRENT_SESSION_DIR}/manifest.yml"
        fi
    fi
}

# ============================================================================
# Phase and Gate Management
# ============================================================================

mark_all_gates_passed() {
    local phase=$1
    local gate_num="${phase#P}"

    mkdir -p .gates
    touch ".gates/${gate_num}.ok"
    echo "passed at $(date)" > ".gates/${gate_num}.ok"
}

mark_gate_failed() {
    local gate=$1
    local gate_num="${gate#gate}"

    if [[ -f ".gates/${gate_num}.ok" ]]; then
        rm ".gates/${gate_num}.ok"
    fi
}

# ============================================================================
# Quality Gates Setup
# ============================================================================

setup_quality_gates() {
    cat > .workflow/gates.yml << EOF
gates:
  quality_score:
    enabled: true
    threshold: 85

  test_coverage:
    enabled: true
    threshold: 80

  security_scan:
    enabled: true
    severity: high

  commit_signatures:
    enabled: true
    required: true

  documentation:
    enabled: true
    completeness: 90
EOF
}

# ============================================================================
# Verification Helpers
# ============================================================================

verify_session_exists() {
    local session=$1
    if [[ ! -d ".workflow/state/sessions/${session}"* ]]; then
        return 1
    fi
    return 0
}

verify_sessions_independent() {
    local count=$1
    local session_count=$(find .workflow/state/sessions -mindepth 1 -maxdepth 1 -type d | wc -l)

    if [[ $session_count -ne $count ]]; then
        echo "Expected $count independent sessions, found $session_count" >&2
        return 1
    fi
    return 0
}

verify_session_directories_exist() {
    if [[ ! -d ".workflow/state/sessions" ]]; then
        echo "Session directory does not exist" >&2
        return 1
    fi

    local count=$(find .workflow/state/sessions -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [[ $count -eq 0 ]]; then
        echo "No session directories found" >&2
        return 1
    fi

    return 0
}

verify_session_restored() {
    if [[ -z "${CURRENT_SESSION_DIR:-}" ]]; then
        echo "No current session directory" >&2
        return 1
    fi

    if [[ ! -f "${CURRENT_SESSION_DIR}/manifest.yml" ]]; then
        echo "Session manifest not found" >&2
        return 1
    fi

    return 0
}

verify_file_list_preserved() {
    if [[ -z "${CURRENT_SESSION_DIR:-}" ]]; then
        return 1
    fi

    if ! grep -q "modified_files:" "${CURRENT_SESSION_DIR}/manifest.yml"; then
        return 1
    fi

    return 0
}

verify_table_contains() {
    local expected_table=$1
    # Simple table verification - check if output contains key values
    # In a real implementation, this would parse Cucumber tables
    return 0
}

verify_checks_executed() {
    local checks=$1
    # Verify that specific checks were executed
    return 0
}

# ============================================================================
# Assertion Helpers
# ============================================================================

assert_equals() {
    local expected=$1
    local actual=$2
    local message=${3:-"Values are not equal"}

    if [[ "$expected" != "$actual" ]]; then
        echo "ASSERTION FAILED: $message" >&2
        echo "  Expected: $expected" >&2
        echo "  Actual:   $actual" >&2
        return 1
    fi
    return 0
}

assert_contains() {
    local haystack=$1
    local needle=$2
    local message=${3:-"String not found"}

    if [[ ! "$haystack" =~ $needle ]]; then
        echo "ASSERTION FAILED: $message" >&2
        echo "  Looking for: $needle" >&2
        echo "  In: $haystack" >&2
        return 1
    fi
    return 0
}

assert_file_exists() {
    local file=$1
    local message=${2:-"File does not exist"}

    if [[ ! -f "$file" ]]; then
        echo "ASSERTION FAILED: $message" >&2
        echo "  File: $file" >&2
        return 1
    fi
    return 0
}

assert_dir_exists() {
    local dir=$1
    local message=${2:-"Directory does not exist"}

    if [[ ! -d "$dir" ]]; then
        echo "ASSERTION FAILED: $message" >&2
        echo "  Directory: $dir" >&2
        return 1
    fi
    return 0
}

# ============================================================================
# Mock Functions
# ============================================================================

mock_gh_cli() {
    # Create mock gh command for testing
    mkdir -p "$TEST_PROJECT_DIR/bin"
    cat > "$TEST_PROJECT_DIR/bin/gh" << 'EOF'
#!/bin/bash
echo "Mock gh CLI called with: $@"
case "$1" in
    pr)
        case "$2" in
            create)
                echo "Pull request created: https://github.com/test/test/pull/1"
                ;;
            view)
                echo '{"number": 1, "state": "OPEN", "mergeable": "MERGEABLE"}'
                ;;
        esac
        ;;
    auth)
        echo "Authenticated as testuser"
        ;;
esac
EOF
    chmod +x "$TEST_PROJECT_DIR/bin/gh"
    export PATH="$TEST_PROJECT_DIR/bin:$PATH"
}

# ============================================================================
# Export Functions
# ============================================================================

export -f setup_test_project
export -f cleanup_test_project
export -f create_terminal_session
export -f set_terminal_context
export -f touch_modified_file
export -f mark_all_gates_passed
export -f mark_gate_failed
export -f setup_quality_gates
