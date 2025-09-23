#!/bin/bash

# Claude Enhancer Unified Configuration
# Centralized configuration for all Claude Enhancer components

# Core paths
export PERFECT21_ROOT="/home/xx/dev/Claude Enhancer"
export CLAUDE_DIR="$PERFECT21_ROOT/.claude"
export SCRIPTS_DIR="$CLAUDE_DIR/scripts"
export AGENTS_DIR="$CLAUDE_DIR/agents"
export HOOKS_DIR="$CLAUDE_DIR/hooks"

# Git paths
export GIT_HOOKS_DIR="$PERFECT21_ROOT/.git/hooks"

# Log configuration
export LOG_DIR="$CLAUDE_DIR/logs"
export LOG_FILE="$LOG_DIR/perfect21.log"

# Performance settings
export MAX_PARALLEL_AGENTS=8
export DEFAULT_TIMEOUT=300
export CLEANUP_BATCH_SIZE=100

# Phase configuration
export PHASE_STATE_FILE="$CLAUDE_DIR/phase_state.json"
export CURRENT_PHASE_FILE="$CLAUDE_DIR/current_phase"

# Agent strategy settings
export SIMPLE_TASK_AGENTS=4
export STANDARD_TASK_AGENTS=6
export COMPLEX_TASK_AGENTS=8

# Color definitions for consistent output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export WHITE='\033[1;37m'
export NC='\033[0m' # No Color

# Print functions for consistent output
print_header() {
    echo -e "\n${CYAN}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_debug() {
    if [ "${DEBUG:-false}" = "true" ]; then
        echo -e "${PURPLE}🔍 DEBUG: $1${NC}"
    fi
}

# Utility functions
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_debug "Created directory: $dir"
    fi
}

check_file_exists() {
    local file="$1"
    if [ ! -f "$file" ]; then
        print_error "Required file not found: $file"
        return 1
    fi
    return 0
}

get_current_phase() {
    if [ -f "$PHASE_STATE_FILE" ]; then
        jq -r '.current_phase // "0"' "$PHASE_STATE_FILE" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

update_phase() {
    local new_phase="$1"
    local description="$2"

    ensure_dir "$(dirname "$PHASE_STATE_FILE")"

    cat > "$PHASE_STATE_FILE" << EOF
{
  "current_phase": "$new_phase",
  "description": "$description",
  "timestamp": "$(date -Iseconds)",
  "last_updated_by": "Claude Enhancer"
}
EOF

    print_info "Phase updated to: $new_phase - $description"
}

# Initialize logging
init_logging() {
    ensure_dir "$LOG_DIR"

    # Clean old logs (keep last 10)
    if [ -f "$LOG_FILE" ]; then
        tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

# Performance monitoring
log_performance() {
    local operation="$1"
    local start_time="$2"
    local end_time="${3:-$(date +%s%N)}"
    local duration=$(( (end_time - start_time) / 1000000 ))

    echo "[$(date -Iseconds)] PERF: $operation took ${duration}ms" >> "$LOG_FILE"
}

# Validate configuration
validate_config() {
    local errors=0

    # Check critical directories
    for dir in "$PERFECT21_ROOT" "$CLAUDE_DIR" "$AGENTS_DIR"; do
        if [ ! -d "$dir" ]; then
            print_error "Critical directory missing: $dir"
            errors=$((errors + 1))
        fi
    done

    # Check agent count
    local agent_count
    agent_count=$(find "$AGENTS_DIR" -name "*.md" 2>/dev/null | wc -l)
    if [ "$agent_count" -lt 50 ]; then
        print_warning "Low agent count: $agent_count (expected: 56+)"
    fi

    return $errors
}

# Auto-initialize on source
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    # Being sourced, not executed
    init_logging

    # Validate critical paths
    if ! validate_config >/dev/null 2>&1; then
        print_warning "Configuration validation found issues"
    fi
fi