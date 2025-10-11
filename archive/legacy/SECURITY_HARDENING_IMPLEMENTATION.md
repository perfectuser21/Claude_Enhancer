# Security Hardening Implementation Guide
**Claude Enhancer 5.0 - P3 Implementation Phase**

**Date:** 2025-10-09  
**Status:** Implementation Required  
**Priority:** Critical (P0/P1 fixes)

---

## Overview

This document provides actionable steps to harden the Claude Enhancer 5.0 CLI system based on the security audit findings. Follow these steps in priority order.

---

## Phase 1: Critical Fixes (P0 - Block Deployment)

### Fix 1: Implement Input Sanitization (CRIT-001)

**Priority:** P0  
**Files:** All command and library files accepting user input

#### Implementation:

Create `/home/xx/dev/Claude Enhancer 5.0/.workflow/cli/lib/input_validator.sh`:

```bash
#!/usr/bin/env bash
# input_validator.sh - Input validation and sanitization
set -euo pipefail

# Sanitize alphanumeric input with hyphens
ce_sanitize_alphanum() {
    local input="$1"
    local max_length="${2:-256}"
    
    # Remove all non-alphanumeric characters except hyphens
    local sanitized="${input//[^a-zA-Z0-9-]/}"
    
    # Truncate to max length
    sanitized="${sanitized:0:$max_length}"
    
    echo "$sanitized"
}

# Validate feature name
ce_validate_feature_name() {
    local feature_name="$1"
    
    # Length check
    local len=${#feature_name}
    if [[ $len -lt 2 || $len -gt 50 ]]; then
        echo "Error: Feature name must be 2-50 characters" >&2
        return 1
    fi
    
    # Pattern check: lowercase alphanumeric and hyphens only
    if [[ ! "$feature_name" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
        echo "Error: Feature name must contain only lowercase letters, numbers, and hyphens" >&2
        echo "Error: Must start and end with alphanumeric character" >&2
        return 1
    fi
    
    # No consecutive hyphens
    if [[ "$feature_name" =~ -- ]]; then
        echo "Error: Feature name cannot contain consecutive hyphens" >&2
        return 1
    fi
    
    return 0
}

# Validate terminal ID
ce_validate_terminal_id() {
    local terminal_id="$1"
    
    # Pattern: t[0-9]+
    if [[ ! "$terminal_id" =~ ^t[0-9]+$ ]]; then
        echo "Error: Terminal ID must match pattern 't[0-9]+' (e.g., t1, t2, t123)" >&2
        return 1
    fi
    
    # Length check (reasonable limit)
    if [[ ${#terminal_id} -gt 20 ]]; then
        echo "Error: Terminal ID too long" >&2
        return 1
    fi
    
    # Path traversal prevention
    if [[ "$terminal_id" == *".."* ]] || [[ "$terminal_id" == *"/"* ]]; then
        echo "Error: Terminal ID contains invalid characters" >&2
        return 1
    fi
    
    return 0
}

# Validate and canonicalize path (prevent traversal)
ce_validate_path() {
    local input_path="$1"
    local allowed_prefix="$2"
    
    # Resolve to absolute path
    local canonical_path
    canonical_path=$(realpath -m "$input_path" 2>/dev/null) || {
        echo "Error: Invalid path" >&2
        return 1
    }
    
    # Check if path is within allowed prefix
    local canonical_prefix
    canonical_prefix=$(realpath -m "$allowed_prefix" 2>/dev/null) || {
        echo "Error: Invalid allowed prefix" >&2
        return 1
    }
    
    if [[ "$canonical_path" != "$canonical_prefix"* ]]; then
        echo "Error: Path traversal detected" >&2
        return 1
    fi
    
    echo "$canonical_path"
}

# Validate phase name
ce_validate_phase() {
    local phase="$1"
    
    if [[ ! "$phase" =~ ^P[0-7]$ ]]; then
        echo "Error: Invalid phase. Must be P0-P7" >&2
        return 1
    fi
    
    return 0
}

# Validate branch name
ce_validate_branch_name() {
    local branch_name="$1"
    
    # Allow common branch patterns
    local valid_pattern='^(feature|feat|fix|docs|test|refactor|chore)\/[a-zA-Z0-9][a-zA-Z0-9\/_-]*$'
    
    if [[ ! "$branch_name" =~ $valid_pattern ]]; then
        echo "Error: Invalid branch name format" >&2
        return 1
    fi
    
    # Length check
    if [[ ${#branch_name} -lt 3 || ${#branch_name} -gt 80 ]]; then
        echo "Error: Branch name must be 3-80 characters" >&2
        return 1
    fi
    
    # No path traversal patterns
    if [[ "$branch_name" == *".."* ]]; then
        echo "Error: Branch name contains invalid patterns" >&2
        return 1
    fi
    
    return 0
}

# Sanitize for use in filenames
ce_sanitize_filename() {
    local input="$1"
    
    # Replace slashes with underscores for safety
    local sanitized="${input//\//_}"
    
    # Remove any remaining dangerous characters
    sanitized="${sanitized//[^a-zA-Z0-9_.-]/}"
    
    echo "$sanitized"
}

# Export functions
export -f ce_sanitize_alphanum
export -f ce_validate_feature_name
export -f ce_validate_terminal_id
export -f ce_validate_path
export -f ce_validate_phase
export -f ce_validate_branch_name
export -f ce_sanitize_filename
```

#### Integration:

1. Source in `common.sh`:
```bash
source "${SCRIPT_DIR}/input_validator.sh"
```

2. Use in `start.sh` command:
```bash
# Replace existing validation with:
cmd_start_validate() {
    # Validate feature name with new function
    if ! ce_validate_feature_name "$FEATURE_NAME"; then
        return 1
    fi
    
    # Validate phase
    if ! ce_validate_phase "$PHASE"; then
        return 1
    fi
    
    # Validate terminal ID with path traversal prevention
    if ! ce_validate_terminal_id "$TERMINAL_ID"; then
        return 1
    fi
    
    # Additional validation: prevent path traversal in session path
    local session_path
    session_path=$(ce_validate_path \
        ".workflow/state/sessions/${TERMINAL_ID}" \
        ".workflow/state/sessions") || return 1
    
    return 0
}
```

---

### Fix 2: Fix Variable Quoting (CRIT-002)

**Priority:** P0  
**Files:** All library files

#### Automated Fix Script:

Create `/home/xx/dev/Claude Enhancer 5.0/scripts/fix_variable_quoting.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Fixing unquoted variable expansions..."

# Find all bash files
find .workflow/cli -name "*.sh" -type f | while read -r file; do
    echo "Checking: $file"
    
    # Run shellcheck and capture unquoted variable warnings
    shellcheck -f json "$file" 2>/dev/null | jq -r '.[] | select(.code == "SC2086") | .message' || true
done

echo ""
echo "Run shellcheck manually to identify all instances:"
echo "  shellcheck .workflow/cli/**/*.sh"
```

#### Manual Fix Examples:

```bash
# BEFORE (vulnerable):
CE_STATE_FILE="${CE_STATE_DIR}/current.json"
cat $CE_STATE_FILE

# AFTER (secure):
CE_STATE_FILE="${CE_STATE_DIR}/current.json"
cat "$CE_STATE_FILE"

# BEFORE (vulnerable):
for file in ${CE_SESSION_DIR}/*.json; do

# AFTER (secure):
for file in "${CE_SESSION_DIR}"/*.json; do

# BEFORE (vulnerable - array):
files=(${CE_SESSION_DIR}/*.json)

# AFTER (secure - array):
files=("${CE_SESSION_DIR}"/*.json)
```

---

## Phase 2: High Priority Fixes (P1)

### Fix 3: File Permission Management (HIGH-001)

**Priority:** P1

#### Implementation:

Add to `common.sh`:

```bash
# Create secure file with proper permissions
ce_create_secure_file() {
    local file_path="$1"
    local content="${2:-}"
    local perms="${3:-600}"
    
    # Create with secure umask
    (
        umask 077
        echo "$content" > "$file_path"
    ) || {
        ce_log_error "Failed to create secure file: $file_path"
        return 1
    }
    
    # Set explicit permissions
    chmod "$perms" "$file_path" || {
        ce_log_error "Failed to set permissions on $file_path"
        return 1
    }
    
    # Verify permissions
    local actual_perms
    actual_perms=$(stat -c '%a' "$file_path" 2>/dev/null || stat -f '%Lp' "$file_path" 2>/dev/null)
    
    if [[ "$actual_perms" != "$perms" ]]; then
        ce_log_error "Permission verification failed for $file_path"
        ce_log_error "Expected: $perms, Got: $actual_perms"
        return 1
    fi
    
    return 0
}

# Create secure directory
ce_create_secure_dir() {
    local dir_path="$1"
    local perms="${2:-700}"
    
    mkdir -p "$dir_path" || {
        ce_log_error "Failed to create directory: $dir_path"
        return 1
    }
    
    chmod "$perms" "$dir_path" || {
        ce_log_error "Failed to set directory permissions: $dir_path"
        return 1
    }
    
    return 0
}
```

#### Fix Permissions Script:

```bash
#!/usr/bin/env bash
# fix_permissions.sh - Standardize file permissions
set -euo pipefail

echo "Fixing file permissions..."

# Executable scripts: 755
find .workflow/cli/commands -name "*.sh" -type f -exec chmod 755 {} \;
find .workflow/cli -maxdepth 1 -name "*.sh" -type f -exec chmod 755 {} \;
chmod 755 ce.sh

# Library files (sourced): 644
find .workflow/cli/lib -name "*.sh" -type f -exec chmod 644 {} \;

# State files (if exist): 600
if [[ -d ".workflow/cli/state" ]]; then
    find .workflow/cli/state -name "*.yml" -o -name "*.json" -o -name "*.state" | \
        xargs chmod 600 2>/dev/null || true
fi

# Directories: 755 (or 700 for sensitive)
find .workflow/cli -type d -exec chmod 755 {} \;
chmod 700 .workflow/cli/state 2>/dev/null || true

echo "✅ Permissions fixed"
```

---

### Fix 4: Implement File Locking (HIGH-002, HIGH-003)

**Priority:** P1  
**File:** `.workflow/cli/lib/state_manager.sh`

**NOTE:** This was already implemented in the enhanced `state_manager.sh`. Verify it's being used:

```bash
# Check if lock functions are being called
grep -r "ce_state_acquire_lock" .workflow/cli/

# Verify lock implementation
# Should see lock directory creation and PID tracking
```

---

### Fix 5: Terminal ID Validation (HIGH-004)

**Priority:** P1

Already addressed in Fix 1 (Input Sanitization). Verify implementation:

```bash
# Test terminal ID validation
bash -c 'source .workflow/cli/lib/input_validator.sh; ce_validate_terminal_id "../../../etc/passwd"'
# Should fail with error

bash -c 'source .workflow/cli/lib/input_validator.sh; ce_validate_terminal_id "t1"'
# Should succeed
```

---

### Fix 6: Ensure Strict Mode (HIGH-005)

**Priority:** P1

#### Verification Script:

```bash
#!/usr/bin/env bash
# verify_strict_mode.sh
set -euo pipefail

echo "Checking for strict mode in all scripts..."

missing_count=0

find .workflow/cli -name "*.sh" -type f | while read -r script; do
    if ! head -10 "$script" | grep -q "set -euo pipefail"; then
        echo "❌ MISSING: $script"
        ((missing_count++)) || true
    fi
done

if [[ $missing_count -eq 0 ]]; then
    echo "✅ All scripts have strict mode"
    exit 0
else
    echo "❌ Found $missing_count scripts missing strict mode"
    exit 1
fi
```

#### Auto-fix Script:

```bash
#!/usr/bin/env bash
# add_strict_mode.sh
set -euo pipefail

echo "Adding strict mode to scripts..."

find .workflow/cli -name "*.sh" -type f | while read -r script; do
    if ! head -10 "$script" | grep -q "set -euo pipefail"; then
        echo "Fixing: $script"
        
        # Create temp file with strict mode added
        {
            head -1 "$script"  # Keep shebang
            echo "set -euo pipefail"
            echo ""
            tail -n +2 "$script"  # Rest of file
        } > "${script}.tmp"
        
        mv "${script}.tmp" "$script"
        chmod --reference="$script" "${script}"
    fi
done

echo "✅ Strict mode added to all scripts"
```

---

## Phase 3: Medium Priority Fixes (P2)

### Fix 7: Implement Log Sanitization (MED-002)

Add to `common.sh`:

```bash
# Sanitize sensitive data in logs
ce_log_sanitize() {
    local message="$1"
    
    # Redact common sensitive patterns
    message=$(echo "$message" | sed -E 's/(password|passwd|pwd|token|secret|key|apikey|api_key)=S[^ ]*/\1=***REDACTED***/gi')
    message=$(echo "$message" | sed -E 's/Bearer\s+[A-Za-z0-9._-]+/Bearer ***REDACTED***/gi')
    message=$(echo "$message" | sed -E 's/(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}/***GITHUB_TOKEN***/g')
    message=$(echo "$message" | sed -E 's/ssh-rsa\s+[A-Za-z0-9+\/=]+/ssh-rsa ***REDACTED***/g')
    
    echo "$message"
}

# Update logging functions to use sanitization
ce_log_info() {
    local message="${1:-}"
    message=$(ce_log_sanitize "$message")
    
    if [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_INFO} ]]; then
        echo -e "${CE_COLOR_BLUE}[INFO $(date +'%Y-%m-%d %H:%M:%S')]${CE_COLOR_RESET} ${message}"
    fi
}

# Similar for ce_log_warn, ce_log_error, ce_log_debug
```

---

### Fix 8: Implement Length Limits (MED-003)

Already covered in input validation (Fix 1). Ensure all inputs are validated:

```bash
# Checklist:
# - Feature names: 2-50 chars
# - Branch names: 3-80 chars
# - Terminal IDs: 1-20 chars
# - Descriptions: 0-256 chars
# - Commit messages: 1-500 chars (if applicable)
```

---

### Fix 9: Secure Temporary Files (MED-006)

Already implemented in `common.sh`. Verify usage:

```bash
# Good usage example:
temp_file=$(ce_create_temp_file)
echo "data" > "$temp_file"
# File automatically cleaned up on exit

# Verify cleanup trap is registered:
grep "_ce_cleanup_handler" .workflow/cli/lib/common.sh
```

---

## Phase 4: Testing & Validation

### Security Test Suite

Create `/home/xx/dev/Claude Enhancer 5.0/test/security_validation.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Running Security Validation Suite..."
echo "===================================="

# Test 1: Input Sanitization
echo ""
echo "[Test 1] Input Sanitization"
source .workflow/cli/lib/input_validator.sh

# Should fail
if ce_validate_feature_name "../etc/passwd" 2>/dev/null; then
    echo "❌ FAIL: Path traversal not detected"
    exit 1
else
    echo "✅ PASS: Path traversal blocked"
fi

# Should succeed
if ce_validate_feature_name "user-auth"; then
    echo "✅ PASS: Valid feature name accepted"
else
    echo "❌ FAIL: Valid feature name rejected"
    exit 1
fi

# Test 2: Terminal ID Validation
echo ""
echo "[Test 2] Terminal ID Validation"

# Should fail
if ce_validate_terminal_id "../../../etc" 2>/dev/null; then
    echo "❌ FAIL: Path traversal in terminal ID not detected"
    exit 1
else
    echo "✅ PASS: Path traversal in terminal ID blocked"
fi

# Test 3: File Permissions
echo ""
echo "[Test 3] File Permissions"
source .workflow/cli/lib/common.sh

temp_file=$(mktemp)
if ce_create_secure_file "$temp_file" "test content" 600; then
    perms=$(stat -c '%a' "$temp_file")
    if [[ "$perms" == "600" ]]; then
        echo "✅ PASS: Secure file created with correct permissions"
    else
        echo "❌ FAIL: Incorrect permissions: $perms"
        exit 1
    fi
    rm -f "$temp_file"
else
    echo "❌ FAIL: Failed to create secure file"
    exit 1
fi

# Test 4: Lock Mechanism
echo ""
echo "[Test 4] Lock Mechanism"
source .workflow/cli/lib/state_manager.sh

if ce_state_acquire_lock "test_lock" 5; then
    echo "✅ PASS: Lock acquired"
    
    # Verify lock exists
    if [[ -d ".workflow/cli/state/locks/test_lock.lock" ]]; then
        echo "✅ PASS: Lock file created"
    else
        echo "❌ FAIL: Lock file not found"
        exit 1
    fi
    
    ce_state_release_lock "test_lock"
    
    # Verify lock released
    if [[ ! -d ".workflow/cli/state/locks/test_lock.lock" ]]; then
        echo "✅ PASS: Lock released"
    else
        echo "❌ FAIL: Lock not released"
        exit 1
    fi
else
    echo "❌ FAIL: Failed to acquire lock"
    exit 1
fi

# Test 5: Strict Mode
echo ""
echo "[Test 5] Strict Mode Verification"
missing=0
find .workflow/cli -name "*.sh" -type f | while read -r script; do
    if ! head -10 "$script" | grep -q "set -euo pipefail"; then
        echo "❌ Missing strict mode: $script"
        ((missing++)) || true
    fi
done

if [[ $missing -eq 0 ]]; then
    echo "✅ PASS: All scripts have strict mode"
else
    echo "❌ FAIL: $missing scripts missing strict mode"
    exit 1
fi

echo ""
echo "===================================="
echo "✅ All Security Tests Passed"
```

---

## Implementation Checklist

Use this checklist to track implementation progress:

### Phase 1: Critical (P0)
- [ ] Create `input_validator.sh` library
- [ ] Integrate input validation in `start.sh`
- [ ] Fix all unquoted variable expansions
- [ ] Run shellcheck on all files
- [ ] Verify fixes with test suite

### Phase 2: High Priority (P1)
- [ ] Implement secure file/directory creation
- [ ] Fix all file permissions (run fix script)
- [ ] Verify lock mechanism implementation
- [ ] Add strict mode to all scripts
- [ ] Validate terminal ID path traversal prevention

### Phase 3: Medium Priority (P2)
- [ ] Implement log sanitization
- [ ] Add length limit validation
- [ ] Verify secure temporary file handling
- [ ] Test all input validation functions

### Phase 4: Testing
- [ ] Run security validation test suite
- [ ] Perform manual penetration testing
- [ ] Run shellcheck on entire codebase
- [ ] Document security measures

### Phase 5: Documentation
- [ ] Update security documentation
- [ ] Add security section to README
- [ ] Create security best practices guide
- [ ] Document incident response procedures

---

## Deployment Gates

Before deploying to production, ensure ALL of these pass:

1. ✅ All Critical (P0) issues resolved
2. ✅ All High (P1) issues resolved
3. ✅ Security test suite passes 100%
4. ✅ Shellcheck reports 0 errors on all files
5. ✅ Manual security review completed
6. ✅ Documentation updated
7. ✅ Security training completed for team

---

## Post-Implementation Verification

After implementing all fixes, run:

```bash
# 1. Security test suite
bash test/security_validation.sh

# 2. Shellcheck
find .workflow/cli -name "*.sh" -exec shellcheck {} \;

# 3. Permission audit
bash scripts/fix_permissions.sh --verify

# 4. Integration test
bash test/P4_CAPABILITY_ENHANCEMENT_TEST.sh

# 5. Manual verification
ce start test-feature
ce status
ce validate
```

---

## Maintenance

### Regular Security Tasks

**Weekly:**
- Run security test suite
- Check for new shellcheck warnings
- Review logs for suspicious activity

**Monthly:**
- Update dependencies
- Review and rotate credentials
- Audit file permissions
- Review access logs

**Quarterly:**
- Full security audit
- Penetration testing
- Update security documentation
- Security training refresh

---

## References

- OWASP Shell Security Guidelines
- Bash Security Pitfalls: https://mywiki.wooledge.org/BashPitfalls
- ShellCheck Wiki: https://www.shellcheck.net/wiki/
- CIS Bash Scripting Security Benchmarks

---

**Last Updated:** 2025-10-09  
**Next Review:** After P0/P1 fixes implemented
