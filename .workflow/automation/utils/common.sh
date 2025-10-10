#!/usr/bin/env bash
# Common Utilities for Claude Enhancer Automation
# Purpose: Shared functions, logging, error handling
# Used by: All automation scripts

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_debug() {
    if [[ "${CE_DEBUG:-0}" == "1" ]]; then
        echo -e "[DEBUG] $*" >&2
    fi
}

# Error handling

die() {
    log_error "$@"
    exit 1
}

# Git utilities

get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

get_default_branch() {
    git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
}

is_main_branch() {
    local branch="${1:-$(get_current_branch)}"
    [[ "$branch" == "main" || "$branch" == "master" ]]
}

branch_exists() {
    local branch="$1"
    git rev-parse --verify --quiet "refs/heads/${branch}" > /dev/null
}

remote_branch_exists() {
    local branch="$1"
    git ls-remote --heads origin "${branch}" | grep -q "${branch}"
}

# File operations

ensure_directory() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        log_debug "Created directory: $dir"
    fi
}

file_age_minutes() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "999999"
        return
    fi
    local now=$(date +%s)
    local mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    echo $(( (now - mtime) / 60 ))
}

# Environment checks

check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        die "Required command not found: $cmd"
    fi
}

check_environment() {
    check_command git
    check_command gh  # GitHub CLI
}

# Phase detection

detect_phase() {
    local message="$1"
    if echo "$message" | grep -qE '\[P([0-7])\]'; then
        echo "$message" | sed -E 's/.*\[P([0-7])\].*/\1/'
    elif echo "$message" | grep -qE '\bP([0-7])\b'; then
        echo "$message" | sed -E 's/.*\bP([0-7])\b.*/\1/'
    else
        echo "unknown"
    fi
}

get_phase_name() {
    local phase="$1"
    case "$phase" in
        0) echo "探索" ;;
        1) echo "规划" ;;
        2) echo "骨架" ;;
        3) echo "实现" ;;
        4) echo "测试" ;;
        5) echo "审查" ;;
        6) echo "发布" ;;
        7) echo "监控" ;;
        *) echo "未知" ;;
    esac
}

# Validation helpers

validate_email() {
    local email="$1"
    [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

validate_url() {
    local url="$1"
    [[ "$url" =~ ^https?:// ]]
}

# Retry logic

retry_with_backoff() {
    local max_attempts="${1}"
    local delay="${2}"
    local max_delay="${3:-300}"
    shift 3
    local cmd=("$@")

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if "${cmd[@]}"; then
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            log_warning "Attempt $attempt failed. Retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))
            if [[ $delay -gt $max_delay ]]; then
                delay=$max_delay
            fi
        fi

        attempt=$((attempt + 1))
    done

    log_error "All $max_attempts attempts failed"
    return 1
}

# JSON handling

extract_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*: "\(.*\)"/\1/'
}

# Export functions
export -f log_info log_success log_warning log_error log_debug
export -f die
export -f get_current_branch get_default_branch is_main_branch
export -f branch_exists remote_branch_exists
export -f ensure_directory file_age_minutes
export -f check_command check_environment
export -f detect_phase get_phase_name
export -f validate_email validate_url
export -f retry_with_backoff
export -f extract_json_value
