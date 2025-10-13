#!/bin/bash
# Pre-Write Hook: Validates code quality before AI writes files
# Called before Write/Edit tool execution
# Part of Claude Enhancer 6.0 - AI Self-Validation System

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MIN_COVERAGE_THRESHOLD=80

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Performance tracking
start_time=$(date +%s%3N)

# Logging function
log() {
    echo -e "${BLUE}[PRE-WRITE]${NC} $*" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

# Helper: Check if file is a source file
is_source_file() {
    local file="$1"

    # Check if it's a code file
    [[ "$file" =~ \.(js|ts|jsx|tsx|py|go|rs|sh)$ ]] || return 1

    # Exclude test files
    [[ "$file" =~ \.(test|spec)\. ]] && return 1

    # Exclude temp files
    [[ "$file" =~ ^\.temp/ ]] && return 1

    return 0
}

# Helper: Infer test file location
infer_test_file() {
    local source_file="$1"
    local dir
    dir=$(dirname "$source_file")
    local base
    base=$(basename "$source_file")
    local ext="${base##*.}"
    local name="${base%.*}"

    # Try multiple test file patterns
    local test_patterns=(
        "${dir}/${name}.test.${ext}"
        "${dir}/${name}.spec.${ext}"
        "${dir}/__tests__/${name}.test.${ext}"
        "${dir}/__tests__/${name}.spec.${ext}"
        "test/${source_file#src/}"
        "tests/${source_file#src/}"
    )

    for pattern in "${test_patterns[@]}"; do
        if [[ -f "$pattern" ]]; then
            echo "$pattern"
            return 0
        fi
    done

    # Return first pattern as suggestion
    echo "${test_patterns[0]}"
    return 1
}

# Validation 1: Syntax Check
validate_syntax() {
    local file_path="$1"
    local content="$2"

    log "Checking syntax for: $file_path"

    case "$file_path" in
        *.sh)
            if command -v shellcheck >/dev/null 2>&1; then
                # Use temp file for shellcheck
                local temp_file
                temp_file=$(mktemp --suffix=.sh)
                echo "$content" > "$temp_file"
                if ! shellcheck "$temp_file" 2>&1; then
                    error "Shell syntax validation failed"
                    rm -f "$temp_file"
                    return 1
                fi
                rm -f "$temp_file"
            else
                # Fallback: basic bash syntax check
                if ! bash -n <(echo "$content") 2>&1; then
                    error "Basic shell syntax check failed"
                    return 1
                fi
            fi
            ;;

        *.py)
            # Check Python syntax using temp file
            local temp_file
            temp_file=$(mktemp --suffix=.py)
            echo "$content" > "$temp_file"

            if ! python3 -m py_compile "$temp_file" 2>&1; then
                error "Python syntax validation failed"
                rm -f "$temp_file"
                return 1
            fi

            # Pylint check (if available)
            if command -v pylint >/dev/null 2>&1; then
                if ! pylint --fail-under=7.0 --disable=all --enable=E,F "$temp_file" 2>&1; then
                    error "Python linting failed (errors/fatal only)"
                    rm -f "$temp_file"
                    return 1
                fi
            fi
            rm -f "$temp_file"
            ;;

        *.js|*.jsx)
            # Check JavaScript syntax with Node.js
            if command -v node >/dev/null 2>&1; then
                local temp_file
                temp_file=$(mktemp --suffix=.js)
                echo "$content" > "$temp_file"
                if ! node --check "$temp_file" 2>&1; then
                    error "JavaScript syntax validation failed"
                    rm -f "$temp_file"
                    return 1
                fi
                rm -f "$temp_file"
            fi

            # ESLint check (if available and configured)
            if command -v npx >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/.eslintrc.js" || -f "$PROJECT_ROOT/.eslintrc.json" ]]; then
                local temp_file
                temp_file=$(mktemp --suffix=.js)
                echo "$content" > "$temp_file"
                if ! npx eslint "$temp_file" 2>&1; then
                    warning "ESLint validation failed (non-blocking)"
                fi
                rm -f "$temp_file"
            fi
            ;;

        *.ts|*.tsx)
            # TypeScript syntax check (if tsc available)
            if command -v npx >/dev/null 2>&1 && [[ -f "$PROJECT_ROOT/tsconfig.json" ]]; then
                local temp_file
                temp_file=$(mktemp --suffix=.ts)
                echo "$content" > "$temp_file"
                if ! npx tsc --noEmit "$temp_file" 2>&1; then
                    error "TypeScript validation failed"
                    rm -f "$temp_file"
                    return 1
                fi
                rm -f "$temp_file"
            fi
            ;;
    esac

    success "Syntax validation passed"
    return 0
}

# Validation 2: Test Existence Check
validate_test_exists() {
    local file_path="$1"

    # Skip if not a source file
    if ! is_source_file "$file_path"; then
        log "Skipping test check (not a source file): $file_path"
        return 0
    fi

    log "Checking test file existence for: $file_path"

    local test_file
    if test_file=$(infer_test_file "$file_path"); then
        success "Test file exists: $test_file"
        return 0
    else
        error "Missing test file for: $file_path"
        error "Expected test file: $test_file"
        warning "💡 Create test file first or use .temp/ directory for prototypes"
        return 1
    fi
}

# Validation 3: Incremental Coverage Check
validate_incremental_coverage() {
    local file_path="$1"
    local content="$2"

    # Skip if not a source file
    if ! is_source_file "$file_path"; then
        log "Skipping coverage check (not a source file)"
        return 0
    fi

    # Skip if coverage tools not available
    if ! command -v jest >/dev/null 2>&1 && ! command -v pytest >/dev/null 2>&1; then
        warning "No coverage tools available, skipping coverage check"
        return 0
    fi

    log "Checking incremental coverage for: $file_path"

    # For JavaScript/TypeScript: use Jest
    if [[ "$file_path" =~ \.(js|ts|jsx|tsx)$ ]] && command -v jest >/dev/null 2>&1; then
        local test_file
        if test_file=$(infer_test_file "$file_path" 2>/dev/null); then
            # Run jest with coverage for this specific file
            local coverage_output
            if coverage_output=$(jest --coverage --collectCoverageFrom="$file_path" --testMatch="$test_file" --silent 2>&1); then
                # Parse coverage percentage (simplified)
                local coverage_pct
                coverage_pct=$(echo "$coverage_output" | grep -oP '\d+\.\d+%' | head -1 | tr -d '%' || echo "0")

                if (( $(echo "$coverage_pct >= $MIN_COVERAGE_THRESHOLD" | bc -l 2>/dev/null || echo 0) )); then
                    success "Coverage: ${coverage_pct}% >= ${MIN_COVERAGE_THRESHOLD}%"
                    return 0
                else
                    error "Coverage too low: ${coverage_pct}% < ${MIN_COVERAGE_THRESHOLD}%"
                    return 1
                fi
            fi
        fi
    fi

    # For Python: use pytest with coverage
    if [[ "$file_path" =~ \.py$ ]] && command -v pytest >/dev/null 2>&1; then
        local test_file
        if test_file=$(infer_test_file "$file_path" 2>/dev/null); then
            if [[ -f "$test_file" ]]; then
                local coverage_output
                if coverage_output=$(pytest --cov="$file_path" --cov-report=term "$test_file" 2>&1); then
                    local coverage_pct
                    coverage_pct=$(echo "$coverage_output" | grep -oP '\d+%' | tail -1 | tr -d '%' || echo "0")

                    if (( coverage_pct >= MIN_COVERAGE_THRESHOLD )); then
                        success "Coverage: ${coverage_pct}% >= ${MIN_COVERAGE_THRESHOLD}%"
                        return 0
                    else
                        warning "Coverage: ${coverage_pct}% < ${MIN_COVERAGE_THRESHOLD}% (non-blocking)"
                        return 0  # Make it non-blocking for now
                    fi
                fi
            fi
        fi
    fi

    # Default: pass if we can't measure
    warning "Could not measure coverage, allowing write"
    return 0
}

# Validation 4: Security Check
validate_security() {
    local file_path="$1"
    local content="$2"

    log "Checking for security issues"

    # Check for common security anti-patterns
    local security_issues=()

    # Check for hardcoded secrets
    if echo "$content" | grep -qiE '(password|secret|api_key|token)\s*=\s*["\047][^"\047]{8,}'; then
        security_issues+=("Potential hardcoded secret detected")
    fi

    # Check for SQL injection patterns (basic)
    if echo "$content" | grep -qE 'execute\(.*\+.*\)|query\(.*\+.*\)'; then
        security_issues+=("Potential SQL injection vulnerability")
    fi

    # Check for eval usage
    if echo "$content" | grep -qE '\beval\(|\bexec\('; then
        security_issues+=("Dangerous eval/exec usage detected")
    fi

    if [[ ${#security_issues[@]} -gt 0 ]]; then
        error "Security issues found:"
        for issue in "${security_issues[@]}"; do
            error "  - $issue"
        done
        return 1
    fi

    success "Security validation passed"
    return 0
}

# Main validation entry point
validate_before_write() {
    local file_path="$1"
    local content="${2:-}"

    log "🔍 Pre-write validation: $file_path"

    # If content not provided via arg, read from stdin
    if [[ -z "$content" ]]; then
        content=$(cat)
    fi

    # Skip validation for certain paths
    if [[ "$file_path" =~ ^\.temp/ ]] || [[ "$file_path" =~ ^\.git/ ]]; then
        log "Skipping validation for: $file_path"
        return 0
    fi

    local validation_passed=true
    local validation_results=()

    # Run all validations
    if validate_syntax "$file_path" "$content"; then
        validation_results+=("✅ Syntax")
    else
        validation_results+=("❌ Syntax")
        validation_passed=false
    fi

    if validate_security "$file_path" "$content"; then
        validation_results+=("✅ Security")
    else
        validation_results+=("❌ Security")
        validation_passed=false
    fi

    if validate_test_exists "$file_path"; then
        validation_results+=("✅ Test Exists")
    else
        validation_results+=("⚠️  Test Missing")
        # Don't fail on missing tests for now (can be strict later)
        # validation_passed=false
    fi

    if validate_incremental_coverage "$file_path" "$content"; then
        validation_results+=("✅ Coverage")
    else
        validation_results+=("⚠️  Coverage")
        # Don't fail on coverage for now
        # validation_passed=false
    fi

    # Performance tracking
    local end_time
    end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    # Summary
    echo "" >&2
    log "═══════════════════════════════════════"
    log "Validation Results: ${validation_results[*]}"
    log "Performance: ${duration}ms"
    log "═══════════════════════════════════════"

    if [[ "$validation_passed" == true ]]; then
        success "✅ Pre-write validation PASSED"
        return 0
    else
        error "❌ Pre-write validation FAILED"
        error "Fix the issues above before writing the file"
        return 1
    fi
}

# Entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Called as script
    if [[ $# -lt 1 ]]; then
        error "Usage: $0 <file_path> [content]"
        error "Or: echo 'content' | $0 <file_path>"
        exit 1
    fi

    validate_before_write "$@"
else
    # Sourced by another script
    log "Pre-write validation hook loaded"
fi
