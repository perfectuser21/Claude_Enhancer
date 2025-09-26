#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Professional Error Handler & Retry Mechanism
# =============================================================================
# Version: 5.0.0
# Author: Claude Code (AI Assistant)
# Date: 2025-09-26
#
# Features:
# - Comprehensive error capture for all workflow phases
# - Exponential backoff retry (1s, 2s, 4s, 8s, 16s)
# - Error classification: WARNING, ERROR, CRITICAL
# - Automatic error reporting and recovery suggestions
# - Integration with existing Claude Enhancer hooks
# - Max 20X quality - no shortcuts, full implementation
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly LOG_DIR="$PROJECT_ROOT/.claude/logs"
readonly ERROR_REPORTS_DIR="$PROJECT_ROOT/.claude/error_reports"
readonly CONFIG_FILE="$PROJECT_ROOT/.claude/error_handler_config.json"

# Create necessary directories
mkdir -p "$LOG_DIR" "$ERROR_REPORTS_DIR"

# Error severity levels
readonly SEVERITY_WARNING=1
readonly SEVERITY_ERROR=2
readonly SEVERITY_CRITICAL=3

# Retry configuration
readonly MAX_RETRIES=5
readonly BASE_RETRY_DELAY=1
readonly MAX_RETRY_DELAY=16

# Colors for output
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# =============================================================================
# CORE ERROR HANDLING CLASSES & FUNCTIONS
# =============================================================================

# Error context structure
declare -A error_context=(
    ["timestamp"]=""
    ["phase"]=""
    ["command"]=""
    ["exit_code"]=""
    ["error_message"]=""
    ["stack_trace"]=""
    ["system_state"]=""
    ["severity"]=""
    ["retry_count"]=""
    ["recovery_suggestions"]=""
)

# System state capture
capture_system_state() {
    local state_file="$LOG_DIR/system_state_$(date +%Y%m%d_%H%M%S).json"

    cat > "$state_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "system": {
        "hostname": "$(hostname)",
        "uptime": "$(uptime -p 2>/dev/null || echo 'N/A')",
        "load_average": "$(uptime | awk -F'load average:' '{print $2}' | xargs)",
        "memory": {
            "total": "$(free -h | awk '/^Mem:/ {print $2}')",
            "used": "$(free -h | awk '/^Mem:/ {print $3}')",
            "available": "$(free -h | awk '/^Mem:/ {print $7}')",
            "swap_used": "$(free -h | awk '/^Swap:/ {print $3}')"
        },
        "disk": {
            "usage": "$(df -h / | awk 'NR==2 {print $5}')",
            "available": "$(df -h / | awk 'NR==2 {print $4}')"
        }
    },
    "process": {
        "pid": "$$",
        "ppid": "$PPID",
        "user": "$(whoami)",
        "working_directory": "$PWD",
        "shell": "$SHELL",
        "path": "$PATH"
    },
    "git": {
        "branch": "$(git branch --show-current 2>/dev/null || echo 'N/A')",
        "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')",
        "status": "$(git status --porcelain 2>/dev/null | wc -l) files changed",
        "remote": "$(git remote -v 2>/dev/null | head -1 | awk '{print $2}' || echo 'N/A')"
    },
    "environment": {
        "node_version": "$(node --version 2>/dev/null || echo 'N/A')",
        "npm_version": "$(npm --version 2>/dev/null || echo 'N/A')",
        "python_version": "$(python3 --version 2>/dev/null || echo 'N/A')",
        "bash_version": "$BASH_VERSION"
    }
}
EOF

    echo "$state_file"
}

# Enhanced error classification
classify_error() {
    local exit_code="$1"
    local error_message="$2"
    local command="$3"

    # Critical errors that require immediate attention
    if [[ $exit_code -eq 137 ]]; then
        echo "$SEVERITY_CRITICAL:KILLED_BY_SIGNAL:Process was killed (likely out of memory)"
        return
    elif [[ $exit_code -eq 130 ]]; then
        echo "$SEVERITY_CRITICAL:INTERRUPTED:Process interrupted by user (Ctrl+C)"
        return
    elif [[ $exit_code -eq 124 ]]; then
        echo "$SEVERITY_ERROR:TIMEOUT:Command timed out"
        return
    fi

    # Error message pattern matching
    case "$error_message" in
        *"No such file or directory"*|*"not found"*)
            echo "$SEVERITY_ERROR:FILE_NOT_FOUND:Missing file or command"
            ;;
        *"Permission denied"*|*"Access denied"*)
            echo "$SEVERITY_ERROR:PERMISSION_DENIED:Insufficient permissions"
            ;;
        *"Connection refused"*|*"Network unreachable"*)
            echo "$SEVERITY_ERROR:NETWORK_ERROR:Network connectivity issue"
            ;;
        *"Out of memory"*|*"Cannot allocate memory"*)
            echo "$SEVERITY_CRITICAL:MEMORY_ERROR:System memory exhausted"
            ;;
        *"Disk full"*|*"No space left on device"*)
            echo "$SEVERITY_CRITICAL:DISK_FULL:Insufficient disk space"
            ;;
        *"syntax error"*|*"parse error"*)
            echo "$SEVERITY_ERROR:SYNTAX_ERROR:Code syntax issue"
            ;;
        *"undefined"*|*"not declared"*)
            echo "$SEVERITY_ERROR:UNDEFINED_REFERENCE:Missing variable or function"
            ;;
        *"timeout"*|*"timed out"*)
            echo "$SEVERITY_ERROR:TIMEOUT:Operation timeout"
            ;;
        *"lock"*|*"locked"*)
            echo "$SEVERITY_WARNING:RESOURCE_LOCKED:Resource temporarily unavailable"
            ;;
        *"deprecated"*|*"warning"*)
            echo "$SEVERITY_WARNING:DEPRECATION:Using deprecated feature"
            ;;
        *)
            if [[ $exit_code -gt 128 ]]; then
                echo "$SEVERITY_CRITICAL:SIGNAL_ERROR:Process terminated by signal"
            elif [[ $exit_code -eq 1 ]]; then
                echo "$SEVERITY_ERROR:GENERAL_ERROR:General command failure"
            elif [[ $exit_code -eq 2 ]]; then
                echo "$SEVERITY_ERROR:INVALID_USAGE:Invalid command usage"
            else
                echo "$SEVERITY_WARNING:UNKNOWN:Unknown error condition"
            fi
            ;;
    esac
}

# Advanced recovery suggestions generator
generate_recovery_suggestions() {
    local severity="$1"
    local error_type="$2"
    local error_description="$3"
    local command="$4"
    local phase="$5"

    local suggestions=()

    case "$error_type" in
        "FILE_NOT_FOUND")
            suggestions+=(
                "Check if the file path is correct and the file exists"
                "Verify current working directory with 'pwd'"
                "Use 'find' command to locate the missing file"
                "Check if the file was moved or renamed recently"
            )
            if [[ "$command" == *"npm"* ]] || [[ "$command" == *"node"* ]]; then
                suggestions+=("Run 'npm install' to install missing dependencies")
            fi
            ;;
        "PERMISSION_DENIED")
            suggestions+=(
                "Check file permissions with 'ls -la'"
                "Use 'chmod' to modify file permissions if needed"
                "Consider using 'sudo' for system-level operations"
                "Verify you have write access to the directory"
            )
            ;;
        "NETWORK_ERROR")
            suggestions+=(
                "Check internet connectivity with 'ping google.com'"
                "Verify firewall settings and proxy configuration"
                "Check if the target service is running and accessible"
                "Try using a different network or VPN"
            )
            ;;
        "MEMORY_ERROR")
            suggestions+=(
                "Close unnecessary applications to free memory"
                "Check memory usage with 'free -h'"
                "Consider increasing swap space"
                "Restart the system if memory leak is suspected"
            )
            ;;
        "DISK_FULL")
            suggestions+=(
                "Clean up temporary files and logs"
                "Use 'df -h' to check disk usage"
                "Remove unnecessary files or move them to external storage"
                "Empty trash/recycle bin"
            )
            ;;
        "SYNTAX_ERROR")
            suggestions+=(
                "Review the code for syntax errors"
                "Check for missing brackets, quotes, or semicolons"
                "Use a code linter or syntax checker"
                "Compare with working examples"
            )
            ;;
        "TIMEOUT")
            suggestions+=(
                "Increase timeout value in configuration"
                "Check system performance and resource usage"
                "Optimize the operation for better performance"
                "Try running during off-peak hours"
            )
            ;;
        "RESOURCE_LOCKED")
            suggestions+=(
                "Wait a few moments and retry the operation"
                "Check if another process is using the resource"
                "Restart related services if safe to do so"
                "Clear any stale lock files"
            )
            ;;
        *)
            suggestions+=(
                "Review the command and parameters for accuracy"
                "Check system logs for more detailed error information"
                "Try running the command with verbose output"
                "Search for similar issues in documentation or forums"
            )
            ;;
    esac

    # Phase-specific suggestions
    case "$phase" in
        "Phase 0"|"branch_creation")
            suggestions+=("Ensure Git is properly configured and repository is initialized")
            ;;
        "Phase 1"|"requirements")
            suggestions+=("Verify all project requirements and dependencies are documented")
            ;;
        "Phase 2"|"design")
            suggestions+=("Check if design specifications are complete and accessible")
            ;;
        "Phase 3"|"implementation")
            suggestions+=(
                "Ensure all required agents are available and functioning"
                "Check if the development environment is properly set up"
            )
            ;;
        "Phase 4"|"testing")
            suggestions+=(
                "Verify test environment configuration"
                "Check if all test dependencies are installed"
            )
            ;;
        "Phase 5"|"commit")
            suggestions+=(
                "Ensure all files are staged properly"
                "Check commit message format and requirements"
            )
            ;;
        "Phase 6"|"review")
            suggestions+=("Verify code review tools and permissions are set up correctly")
            ;;
        "Phase 7"|"deploy")
            suggestions+=(
                "Check deployment environment configuration"
                "Verify deployment permissions and credentials"
            )
            ;;
    esac

    printf "%s\n" "${suggestions[@]}"
}

# Exponential backoff retry mechanism
exponential_backoff() {
    local command="$1"
    local max_retries="${2:-$MAX_RETRIES}"
    local retry_count=0
    local delay="$BASE_RETRY_DELAY"
    local exit_code

    while [[ $retry_count -lt $max_retries ]]; do
        # Execute command and capture output and exit code
        local output
        local error_output

        echo -e "${BLUE}[RETRY $((retry_count + 1))/$max_retries]${NC} Executing: $command"

        if output=$(bash -c "$command" 2>&1); then
            echo -e "${GREEN}✅ Command succeeded after $((retry_count + 1)) attempt(s)${NC}"
            echo "$output"
            return 0
        else
            exit_code=$?
            error_output="$output"

            if [[ $retry_count -eq $((max_retries - 1)) ]]; then
                echo -e "${RED}❌ Command failed after $max_retries attempts${NC}"
                echo -e "${RED}Final error:${NC} $error_output"
                return $exit_code
            fi

            echo -e "${YELLOW}⚠️  Attempt $((retry_count + 1)) failed (exit code: $exit_code)${NC}"
            echo -e "${YELLOW}Error:${NC} $error_output"
            echo -e "${CYAN}⏳ Waiting ${delay}s before retry...${NC}"

            sleep "$delay"

            # Exponential backoff with jitter
            delay=$((delay * 2))
            if [[ $delay -gt $MAX_RETRY_DELAY ]]; then
                delay=$MAX_RETRY_DELAY
            fi

            # Add small random jitter (0-20% of delay)
            local jitter=$((delay * RANDOM / 32768 / 5))
            delay=$((delay + jitter))

            ((retry_count++))
        fi
    done
}

# Comprehensive error reporter
generate_error_report() {
    local timestamp="$1"
    local phase="$2"
    local command="$3"
    local exit_code="$4"
    local error_message="$5"
    local classification="$6"
    local system_state_file="$7"
    local retry_count="$8"

    local report_file="$ERROR_REPORTS_DIR/error_report_$(date +%Y%m%d_%H%M%S).md"
    local severity error_type error_description

    IFS=':' read -r severity error_type error_description <<< "$classification"

    local severity_name
    case "$severity" in
        "$SEVERITY_WARNING") severity_name="⚠️  WARNING" ;;
        "$SEVERITY_ERROR") severity_name="❌ ERROR" ;;
        "$SEVERITY_CRITICAL") severity_name="🔥 CRITICAL" ;;
        *) severity_name="❓ UNKNOWN" ;;
    esac

    # Generate recovery suggestions
    local recovery_suggestions
    recovery_suggestions=$(generate_recovery_suggestions "$severity" "$error_type" "$error_description" "$command" "$phase")

    cat > "$report_file" << EOF
# Claude Enhancer 5.0 - Error Report

## 📊 Error Summary

**Severity:** $severity_name
**Type:** $error_type
**Phase:** $phase
**Timestamp:** $timestamp
**Retry Attempts:** $retry_count

## 🔍 Error Details

### Command
\`\`\`bash
$command
\`\`\`

### Exit Code
$exit_code

### Error Message
\`\`\`
$error_message
\`\`\`

### Classification
- **Severity Level:** $severity ($severity_name)
- **Error Type:** $error_type
- **Description:** $error_description

## 🔧 Recovery Suggestions

EOF

    # Add numbered recovery suggestions
    local suggestion_number=1
    while IFS= read -r suggestion; do
        echo "$suggestion_number. $suggestion" >> "$report_file"
        ((suggestion_number++))
    done <<< "$recovery_suggestions"

    cat >> "$report_file" << EOF

## 🖥️  System State

System state captured in: \`$system_state_file\`

### Git Information
- **Branch:** $(git branch --show-current 2>/dev/null || echo 'N/A')
- **Commit:** $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')
- **Status:** $(git status --porcelain 2>/dev/null | wc -l) files changed

### Environment
- **Working Directory:** $PWD
- **User:** $(whoami)
- **Shell:** $SHELL
- **Node Version:** $(node --version 2>/dev/null || echo 'N/A')

## 📚 Troubleshooting Steps

1. **Review Error Context**
   - Check the command syntax and parameters
   - Verify file paths and permissions
   - Confirm required dependencies are installed

2. **Check System Resources**
   - Memory usage: \`free -h\`
   - Disk space: \`df -h\`
   - System load: \`uptime\`

3. **Examine Logs**
   - Application logs in \`$LOG_DIR\`
   - System logs: \`journalctl -n 50\`
   - Git logs: \`git log --oneline -10\`

4. **Environment Verification**
   - Path configuration: \`echo \$PATH\`
   - Environment variables: \`env | grep -E "(NODE|NPM|PYTHON)"\`
   - Service status: \`systemctl status [service-name]\`

## 🔄 Next Steps

Based on the error type and phase, consider:

1. **Immediate Actions**
   - Address the specific error cause identified above
   - Apply the most relevant recovery suggestion
   - Test the fix in a safe environment

2. **Prevention Measures**
   - Update documentation with this error scenario
   - Add error handling for similar cases
   - Consider adding automated checks

3. **Escalation Path**
   - If error persists, escalate to system administrator
   - Check for known issues in project documentation
   - Consider rolling back to last known good state

---
*Report generated by Claude Enhancer 5.0 Error Handler v5.0.0*
*Timestamp: $(date -Iseconds)*
EOF

    echo "$report_file"
}

# =============================================================================
# MAIN ERROR HANDLING INTERFACE
# =============================================================================

# Main error handling function
handle_error() {
    local phase="${1:-unknown}"
    local command="${2:-unknown}"
    local exit_code="${3:-1}"
    local error_message="${4:-No error message provided}"
    local enable_retry="${5:-true}"

    local timestamp
    timestamp=$(date -Iseconds)

    echo -e "\n${BOLD}${RED}🚨 ERROR DETECTED${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"

    # Capture system state
    local system_state_file
    system_state_file=$(capture_system_state)

    # Classify error
    local classification
    classification=$(classify_error "$exit_code" "$error_message" "$command")

    local severity error_type error_description
    IFS=':' read -r severity error_type error_description <<< "$classification"

    # Display immediate error information
    echo -e "${BOLD}Phase:${NC} $phase"
    echo -e "${BOLD}Command:${NC} $command"
    echo -e "${BOLD}Exit Code:${NC} $exit_code"
    echo -e "${BOLD}Classification:${NC} $error_description"

    # Generate and display recovery suggestions
    echo -e "\n${BOLD}${CYAN}🔧 RECOVERY SUGGESTIONS${NC}"
    echo -e "${BOLD}─────────────────────────────────────────────────${NC}"

    local suggestions
    suggestions=$(generate_recovery_suggestions "$severity" "$error_type" "$error_description" "$command" "$phase")

    local suggestion_number=1
    while IFS= read -r suggestion; do
        echo -e "${CYAN}$suggestion_number.${NC} $suggestion"
        ((suggestion_number++))
    done <<< "$suggestions"

    # Generate comprehensive error report
    local report_file
    report_file=$(generate_error_report "$timestamp" "$phase" "$command" "$exit_code" "$error_message" "$classification" "$system_state_file" "0")

    echo -e "\n${BOLD}${PURPLE}📋 DETAILED REPORT${NC}"
    echo -e "${BOLD}─────────────────────────────────────────────────${NC}"
    echo -e "Full error report: ${BOLD}$report_file${NC}"
    echo -e "System state: ${BOLD}$system_state_file${NC}"

    # Log error to main log file
    local log_entry="$timestamp | $phase | $exit_code | $error_type | $command"
    echo "$log_entry" >> "$LOG_DIR/error_history.log"

    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}\n"

    return "$exit_code"
}

# Retry wrapper function with error handling
retry_with_error_handling() {
    local phase="$1"
    local command="$2"
    local max_retries="${3:-$MAX_RETRIES}"

    local retry_count=0
    local delay="$BASE_RETRY_DELAY"

    echo -e "${BOLD}${BLUE}🔄 EXECUTING WITH RETRY MECHANISM${NC}"
    echo -e "${BOLD}Phase:${NC} $phase"
    echo -e "${BOLD}Command:${NC} $command"
    echo -e "${BOLD}Max Retries:${NC} $max_retries"
    echo -e "${BOLD}─────────────────────────────────────────────────${NC}"

    while [[ $retry_count -lt $max_retries ]]; do
        local output error_output exit_code

        echo -e "${BLUE}[ATTEMPT $((retry_count + 1))/$max_retries]${NC} $command"

        # Execute command with proper error capture
        if error_output=$(bash -c "$command" 2>&1); then
            echo -e "${GREEN}✅ SUCCESS after $((retry_count + 1)) attempt(s)${NC}"
            if [[ -n "$error_output" ]]; then
                echo -e "${BOLD}Output:${NC}\n$error_output"
            fi
            return 0
        else
            exit_code=$?

            if [[ $retry_count -eq $((max_retries - 1)) ]]; then
                # Final attempt failed - handle error comprehensively
                handle_error "$phase" "$command" "$exit_code" "$error_output" "false"
                return "$exit_code"
            fi

            echo -e "${YELLOW}⚠️  Attempt $((retry_count + 1)) failed (exit code: $exit_code)${NC}"
            echo -e "${YELLOW}Error:${NC} $error_output"

            # Quick error classification for retry decision
            local classification
            classification=$(classify_error "$exit_code" "$error_output" "$command")
            local severity error_type
            IFS=':' read -r severity error_type _ <<< "$classification"

            # Some errors shouldn't be retried
            case "$error_type" in
                "SYNTAX_ERROR"|"INVALID_USAGE"|"PERMISSION_DENIED")
                    echo -e "${RED}❌ Non-recoverable error detected. Stopping retries.${NC}"
                    handle_error "$phase" "$command" "$exit_code" "$error_output" "false"
                    return "$exit_code"
                    ;;
            esac

            echo -e "${CYAN}⏳ Waiting ${delay}s before retry...${NC}"
            sleep "$delay"

            # Exponential backoff with jitter
            delay=$((delay * 2))
            if [[ $delay -gt $MAX_RETRY_DELAY ]]; then
                delay=$MAX_RETRY_DELAY
            fi

            # Add random jitter (0-20% of delay)
            local jitter=$((delay * RANDOM / 32768 / 5))
            delay=$((delay + jitter))

            ((retry_count++))
        fi
    done
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Error handler configuration
configure_error_handler() {
    cat > "$CONFIG_FILE" << EOF
{
    "version": "5.0.0",
    "configuration": {
        "max_retries": $MAX_RETRIES,
        "base_retry_delay": $BASE_RETRY_DELAY,
        "max_retry_delay": $MAX_RETRY_DELAY,
        "log_directory": "$LOG_DIR",
        "reports_directory": "$ERROR_REPORTS_DIR",
        "capture_system_state": true,
        "detailed_reporting": true,
        "auto_recovery_suggestions": true
    },
    "error_patterns": {
        "file_not_found": ["No such file or directory", "not found"],
        "permission_denied": ["Permission denied", "Access denied"],
        "network_error": ["Connection refused", "Network unreachable"],
        "memory_error": ["Out of memory", "Cannot allocate memory"],
        "timeout": ["timeout", "timed out"]
    }
}
EOF
}

# Clean up old logs and reports (keep last 30 days)
cleanup_old_files() {
    local days="${1:-30}"

    echo "🧹 Cleaning up files older than $days days..."

    # Clean logs
    find "$LOG_DIR" -name "*.log" -type f -mtime +$days -delete 2>/dev/null || true
    find "$LOG_DIR" -name "system_state_*.json" -type f -mtime +$days -delete 2>/dev/null || true

    # Clean error reports
    find "$ERROR_REPORTS_DIR" -name "error_report_*.md" -type f -mtime +$days -delete 2>/dev/null || true

    echo "✅ Cleanup completed"
}

# Display error statistics
show_error_statistics() {
    local days="${1:-7}"

    if [[ ! -f "$LOG_DIR/error_history.log" ]]; then
        echo "No error history found."
        return
    fi

    echo -e "${BOLD}📊 ERROR STATISTICS (Last $days days)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"

    local since_date
    since_date=$(date -d "$days days ago" -Iseconds)

    # Count errors by type
    local total_errors
    total_errors=$(awk -v since="$since_date" -F'|' '$1 > since' "$LOG_DIR/error_history.log" | wc -l)

    echo -e "${BOLD}Total Errors:${NC} $total_errors"

    if [[ $total_errors -gt 0 ]]; then
        echo -e "\n${BOLD}By Phase:${NC}"
        awk -v since="$since_date" -F'|' '$1 > since {print $2}' "$LOG_DIR/error_history.log" | \
            sort | uniq -c | sort -nr | while read count phase; do
            echo "  $phase: $count"
        done

        echo -e "\n${BOLD}By Error Type:${NC}"
        awk -v since="$since_date" -F'|' '$1 > since {print $4}' "$LOG_DIR/error_history.log" | \
            sort | uniq -c | sort -nr | while read count type; do
            echo "  $type: $count"
        done
    fi

    echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

main() {
    local action="${1:-handle}"

    case "$action" in
        "handle")
            shift
            handle_error "$@"
            ;;
        "retry")
            shift
            retry_with_error_handling "$@"
            ;;
        "configure")
            configure_error_handler
            echo "✅ Error handler configured at $CONFIG_FILE"
            ;;
        "cleanup")
            cleanup_old_files "${2:-30}"
            ;;
        "stats")
            show_error_statistics "${2:-7}"
            ;;
        "test")
            echo "🧪 Testing error handler..."
            handle_error "test_phase" "false" "1" "Test error message for validation"
            ;;
        "--help"|"-h")
            cat << EOF
Claude Enhancer 5.0 - Error Handler & Retry Mechanism

USAGE:
    $0 <action> [arguments...]

ACTIONS:
    handle <phase> <command> <exit_code> <error_message>
        Handle a specific error with full analysis and reporting

    retry <phase> <command> [max_retries]
        Execute command with exponential backoff retry mechanism

    configure
        Set up error handler configuration file

    cleanup [days]
        Clean up log files older than specified days (default: 30)

    stats [days]
        Show error statistics for the last N days (default: 7)

    test
        Test the error handler functionality

    --help, -h
        Show this help message

EXAMPLES:
    $0 handle "Phase 3" "npm install" 1 "Package not found"
    $0 retry "Phase 4" "npm test" 3
    $0 stats 14
    $0 cleanup 7

For more information, see the Claude Enhancer 5.0 documentation.
EOF
            ;;
        *)
            echo -e "${RED}❌ Unknown action: $action${NC}"
            echo "Use '$0 --help' for usage information."
            exit 1
            ;;
    esac
}

# Initialize configuration if it doesn't exist
if [[ ! -f "$CONFIG_FILE" ]]; then
    configure_error_handler
fi

# Handle direct execution vs sourcing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# =============================================================================
# EXPORT FUNCTIONS FOR EXTERNAL USE
# =============================================================================

# Export main functions for use in other scripts
export -f handle_error
export -f retry_with_error_handling
export -f exponential_backoff
export -f classify_error
export -f generate_recovery_suggestions
export -f capture_system_state

echo -e "${GREEN}✅ Claude Enhancer 5.0 Error Handler loaded successfully${NC}"