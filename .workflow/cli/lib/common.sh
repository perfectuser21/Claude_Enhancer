#!/usr/bin/env bash
# common.sh - Common utilities for CE CLI
# Provides logging, color output, and shared utility functions
set -euo pipefail

# Color codes
CE_COLOR_RED='\033[0;31m'
CE_COLOR_GREEN='\033[0;32m'
CE_COLOR_YELLOW='\033[1;33m'
CE_COLOR_BLUE='\033[0;34m'
CE_COLOR_MAGENTA='\033[0;35m'
CE_COLOR_CYAN='\033[0;36m'
CE_COLOR_RESET='\033[0m'

# Logging levels
CE_LOG_LEVEL_DEBUG=0
CE_LOG_LEVEL_INFO=1
CE_LOG_LEVEL_WARN=2
CE_LOG_LEVEL_ERROR=3

# Current log level (default: INFO)
CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL:-${CE_LOG_LEVEL_INFO}}

# Temporary file tracking for cleanup
CE_TEMP_FILES=()
CE_TEMP_DIRS=()

# Cleanup handler - removes temporary files/dirs on exit
_ce_cleanup_handler() {
    local exit_code=$?

    # Remove temporary files
    for temp_file in "${CE_TEMP_FILES[@]+"${CE_TEMP_FILES[@]}"}"; do
        [[ -f "${temp_file}" ]] && rm -f "${temp_file}" 2>/dev/null || true
    done

    # Remove temporary directories
    for temp_dir in "${CE_TEMP_DIRS[@]+"${CE_TEMP_DIRS[@]}"}"; do
        [[ -d "${temp_dir}" ]] && rm -rf "${temp_dir}" 2>/dev/null || true
    done

    exit "${exit_code}"
}

# Set up cleanup trap
trap _ce_cleanup_handler EXIT INT TERM

# ============================================================================
# Security: Source Input Validator
# ============================================================================

# Get the directory where this script is located
COMMON_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source input validation library
# shellcheck source=./input_validator.sh
if [[ -f "${COMMON_SCRIPT_DIR}/input_validator.sh" ]]; then
    source "${COMMON_SCRIPT_DIR}/input_validator.sh"
fi

# ============================================================================
# Security: Secure File Operations
# ============================================================================

ce_create_secure_file() {
    # Create file with secure permissions (600 by default)
    # Security: Prevents information disclosure via file permissions
    # Usage: ce_create_secure_file "/path/to/file" "content" 600
    # Returns: 0 on success, 1 on failure
    local file_path="${1:?File path required}"
    local content="${2:-}"
    local perms="${3:-600}"
    
    # Validate permissions format
    if [[ ! "$perms" =~ ^[0-7]{3}$ ]]; then
        ce_log_error "Invalid permission format: $perms (must be octal like 600)"
        return 1
    fi
    
    # Create file with secure umask
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
        rm -f "$file_path"  # Clean up on failure
        return 1
    }
    
    # Verify permissions were set correctly
    local actual_perms
    actual_perms=$(stat -c '%a' "$file_path" 2>/dev/null || stat -f '%Lp' "$file_path" 2>/dev/null)
    
    if [[ "$actual_perms" != "$perms" ]]; then
        ce_log_error "Permission verification failed for $file_path"
        ce_log_error "Expected: $perms, Got: $actual_perms"
        rm -f "$file_path"  # Clean up on verification failure
        return 1
    fi
    
    ce_log_debug "Created secure file: $file_path (permissions: $perms)"
    return 0
}

ce_create_secure_dir() {
    # Create directory with secure permissions (700 by default)
    # Security: Prevents unauthorized access to sensitive directories
    # Usage: ce_create_secure_dir "/path/to/dir" 700
    # Returns: 0 on success, 1 on failure
    local dir_path="${1:?Directory path required}"
    local perms="${2:-700}"
    
    # Validate permissions format
    if [[ ! "$perms" =~ ^[0-7]{3}$ ]]; then
        ce_log_error "Invalid permission format: $perms (must be octal like 700)"
        return 1
    fi
    
    # Create directory
    mkdir -p "$dir_path" || {
        ce_log_error "Failed to create directory: $dir_path"
        return 1
    }
    
    # Set permissions
    chmod "$perms" "$dir_path" || {
        ce_log_error "Failed to set directory permissions: $dir_path"
        return 1
    }
    
    # Verify permissions
    local actual_perms
    actual_perms=$(stat -c '%a' "$dir_path" 2>/dev/null || stat -f '%Lp' "$dir_path" 2>/dev/null)
    
    if [[ "$actual_perms" != "$perms" ]]; then
        ce_log_warn "Directory permission verification failed for $dir_path"
        ce_log_warn "Expected: $perms, Got: $actual_perms"
        # Don't fail for directories, just warn
    fi
    
    ce_log_debug "Created secure directory: $dir_path (permissions: $perms)"
    return 0
}

ce_log_sanitize() {
    # Sanitize sensitive data before logging
    # Security: Prevents credential leakage in logs
    # Usage: sanitized=$(ce_log_sanitize "$message")
    # Returns: Sanitized message
    local message="$1"
    
    # Redact common sensitive patterns
    # Password/token patterns
    message=$(echo "$message" | sed -E 's/(password|passwd|pwd|token|secret|key|apikey|api_key|auth)=[^ ]*/\1=***REDACTED***/gi')
    
    # Bearer tokens
    message=$(echo "$message" | sed -E 's/Bearer\s+[A-Za-z0-9._-]+/Bearer ***REDACTED***/gi')
    
    # GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_)
    message=$(echo "$message" | sed -E 's/(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}/***GITHUB_TOKEN***/g')
    
    # SSH keys
    message=$(echo "$message" | sed -E 's/ssh-rsa\s+[A-Za-z0-9+\/=]+/ssh-rsa ***REDACTED***/g')
    message=$(echo "$message" | sed -E 's/ssh-ed25519\s+[A-Za-z0-9+\/=]+/ssh-ed25519 ***REDACTED***/g')
    
    # AWS credentials
    message=$(echo "$message" | sed -E 's/(AKIA|ASIA)[A-Z0-9]{16}/***AWS_KEY***/g')
    
    # Basic auth in URLs
    message=$(echo "$message" | sed -E 's|://[^:@]+:[^:@]+@|://***:***@|g')
    
    echo "$message"
}


# ============================================================================
# Logging Functions
# ============================================================================

ce_log_debug() {
    # Log debug message (only if debug enabled)
    # Usage: ce_log_debug "message"
    local message="${1:-}"

    if [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_DEBUG} ]]; then
        echo -e "${CE_COLOR_CYAN}[DEBUG $(date +'%Y-%m-%d %H:%M:%S')]${CE_COLOR_RESET} ${message}" >&2
    fi
}

ce_log_info() {
    # Log informational message with timestamp
    # Usage: ce_log_info "message"
    local message="${1:-}"

    if [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_INFO} ]]; then
        echo -e "${CE_COLOR_BLUE}[INFO $(date +'%Y-%m-%d %H:%M:%S')]${CE_COLOR_RESET} ${message}"
    fi
}

ce_log_warn() {
    # Log warning message in yellow
    # Usage: ce_log_warn "message"
    local message="${1:-}"

    if [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_WARN} ]]; then
        echo -e "${CE_COLOR_YELLOW}[WARN $(date +'%Y-%m-%d %H:%M:%S')]${CE_COLOR_RESET} ${message}" >&2
    fi
}

ce_log_error() {
    # Log error message in red to stderr
    # Usage: ce_log_error "message"
    local message="${1:-}"

    if [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_ERROR} ]]; then
        echo -e "${CE_COLOR_RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${CE_COLOR_RESET} ${message}" >&2
    fi
}

ce_log_success() {
    # Log success message in green
    # Usage: ce_log_success "message"
    local message="${1:-}"

    echo -e "${CE_COLOR_GREEN}[SUCCESS]${CE_COLOR_RESET} ${message}"
}

# ============================================================================
# Color Output Functions
# ============================================================================

ce_color_text() {
    # Output text in specified color
    # Usage: ce_color_text "color_code" "message"
    local color="${1:-${CE_COLOR_RESET}}"
    local message="${2:-}"

    echo -e "${color}${message}${CE_COLOR_RESET}"
}

ce_color_red() {
    # Output text in red
    # Usage: ce_color_red "message"
    local message="${1:-}"
    ce_color_text "${CE_COLOR_RED}" "${message}"
}

ce_color_green() {
    # Output text in green
    # Usage: ce_color_green "message"
    local message="${1:-}"
    ce_color_text "${CE_COLOR_GREEN}" "${message}"
}

ce_color_yellow() {
    # Output text in yellow
    # Usage: ce_color_yellow "message"
    local message="${1:-}"
    ce_color_text "${CE_COLOR_YELLOW}" "${message}"
}

ce_color_blue() {
    # Output text in blue
    # Usage: ce_color_blue "message"
    local message="${1:-}"
    ce_color_text "${CE_COLOR_BLUE}" "${message}"
}

# ============================================================================
# Utility Functions
# ============================================================================

ce_require_command() {
    # Check if required command exists, exit if not
    # Usage: ce_require_command "git" "Please install git"
    local command="${1:?Command name required}"
    local error_message="${2:-Command '${command}' is required but not found}"

    if ! command -v "${command}" &>/dev/null; then
        ce_log_error "${error_message}"
        exit 1
    fi
}

ce_require_file() {
    # Check if required file exists, exit if not
    # Usage: ce_require_file "config.yml" "Config not found"
    local file_path="${1:?File path required}"
    local error_message="${2:-Required file '${file_path}' not found}"

    if [[ ! -f "${file_path}" ]]; then
        ce_log_error "${error_message}"
        exit 1
    fi
}

ce_get_project_root() {
    # Find and return project root directory
    # Looks for: .git directory, .workflow directory
    # Returns: Absolute path to project root
    local current_dir="${PWD}"

    # Traverse up the directory tree
    while [[ "${current_dir}" != "/" ]]; do
        # Check for .git directory (primary indicator)
        if [[ -d "${current_dir}/.git" ]]; then
            echo "${current_dir}"
            return 0
        fi

        # Check for .workflow directory (CE project)
        if [[ -d "${current_dir}/.workflow" ]]; then
            echo "${current_dir}"
            return 0
        fi

        # Move up one directory
        current_dir="$(dirname "${current_dir}")"
    done

    # Not found
    ce_log_error "Project root not found. Not a git or CE project?"
    return 1
}

ce_get_current_branch() {
    # Get current git branch name
    # Returns: Branch name or empty string
    if ! git rev-parse --git-dir &>/dev/null; then
        return 1
    fi

    local branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
    echo "${branch}"
}

ce_get_timestamp() {
    # Get current timestamp in ISO 8601 format
    # Returns: YYYY-MM-DDTHH:MM:SS
    date -u +'%Y-%m-%dT%H:%M:%S'
}

ce_confirm() {
    # Prompt user for yes/no confirmation
    # Usage: ce_confirm "Are you sure?" && do_something
    # Returns: 0 for yes, 1 for no
    local prompt="${1:-Are you sure?}"
    local response

    read -r -p "${prompt} [y/N] " response

    case "${response}" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

ce_prompt() {
    # Prompt user for input with default value
    # Usage: result=$(ce_prompt "Enter name" "default")
    # Returns: User input or default
    local prompt="${1:-Enter value}"
    local default="${2:-}"
    local response

    if [[ -n "${default}" ]]; then
        read -r -p "${prompt} [${default}]: " response
        echo "${response:-${default}}"
    else
        read -r -p "${prompt}: " response
        echo "${response}"
    fi
}

ce_spinner() {
    # Show spinner while command runs
    # Usage: ce_spinner "Loading..." long_running_command
    local message="${1:-Processing}"
    shift
    local command=("$@")

    # Start spinner in background
    {
        local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        local i=0
        while true; do
            i=$(( (i+1) %10 ))
            printf "\r${CE_COLOR_CYAN}${spin:$i:1}${CE_COLOR_RESET} %s" "${message}"
            sleep 0.1
        done
    } &
    local spinner_pid=$!

    # Run the command
    "${command[@]}" &>/dev/null
    local result=$?

    # Stop spinner
    kill "${spinner_pid}" 2>/dev/null
    wait "${spinner_pid}" 2>/dev/null
    printf "\r\033[K"  # Clear line

    return ${result}
}

ce_progress_bar() {
    # Display progress bar
    # Usage: ce_progress_bar 75 100 "Processing"
    local current="${1:-0}"
    local total="${2:-100}"
    local message="${3:-}"

    # Calculate percentage
    local percent=$((current * 100 / total))

    # Calculate filled vs empty blocks (50 char width)
    local filled=$((percent / 2))
    local empty=$((50 - filled))

    # Build progress bar
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done

    # Print progress bar
    printf "\r[%s] %3d%% %s" "${bar}" "${percent}" "${message}"

    # Add newline if complete
    [[ ${current} -ge ${total} ]] && echo
}

ce_trim() {
    # Trim whitespace from string
    # Usage: trimmed=$(ce_trim "  text  ")
    local var="${1:-}"

    # Remove leading whitespace
    var="${var#"${var%%[![:space:]]*}"}"

    # Remove trailing whitespace
    var="${var%"${var##*[![:space:]]}"}"

    echo "${var}"
}

ce_join() {
    # Join array elements with delimiter
    # Usage: ce_join "," "${array[@]}"
    local delimiter="${1:-}"
    shift
    local items=("$@")

    local result=""
    local first=true

    for item in "${items[@]}"; do
        if [[ "${first}" == true ]]; then
            result="${item}"
            first=false
        else
            result="${result}${delimiter}${item}"
        fi
    done

    echo "${result}"
}

ce_is_git_repo() {
    # Check if current directory is a git repository
    # Returns: 0 if git repo, 1 otherwise
    git rev-parse --git-dir &>/dev/null
}

ce_is_ce_project() {
    # Check if current directory is a CE project
    # Looks for: .workflow directory, ce.sh
    # Returns: 0 if CE project, 1 otherwise
    [[ -d ".workflow" ]] && [[ -f "ce.sh" || -f ".workflow/ce" ]]
}

ce_get_ce_version() {
    # Get Claude Enhancer version
    # Returns: Version string (e.g., "5.3.0")
    local version_file

    # Try to find version file
    if [[ -f ".workflow/VERSION" ]]; then
        version_file=".workflow/VERSION"
    elif [[ -f "VERSION" ]]; then
        version_file="VERSION"
    else
        echo "unknown"
        return 1
    fi

    cat "${version_file}" | ce_trim
}

ce_format_duration() {
    # Format seconds into human-readable duration
    # Usage: ce_format_duration 3665
    # Returns: "1h 1m 5s"
    local total_seconds="${1:-0}"

    local hours=$((total_seconds / 3600))
    local minutes=$(( (total_seconds % 3600) / 60 ))
    local seconds=$((total_seconds % 60))

    local result=""

    [[ ${hours} -gt 0 ]] && result="${hours}h "
    [[ ${minutes} -gt 0 ]] && result="${result}${minutes}m "
    [[ ${seconds} -gt 0 || -z "${result}" ]] && result="${result}${seconds}s"

    echo "${result}" | ce_trim
}

ce_format_bytes() {
    # Format bytes into human-readable size
    # Usage: ce_format_bytes 1024000
    # Returns: "1.0 MB"
    local bytes="${1:-0}"

    local units=("B" "KB" "MB" "GB" "TB")
    local unit_index=0
    local size="${bytes}"

    # Convert to float and divide by 1024 until < 1024
    while (( $(echo "${size} >= 1024" | bc -l) )) && [[ ${unit_index} -lt 4 ]]; do
        size=$(echo "scale=1; ${size} / 1024" | bc)
        ((unit_index++))
    done

    echo "${size} ${units[${unit_index}]}"
}

ce_create_temp_file() {
    # Create temporary file and return path
    # Ensures cleanup on exit
    # Returns: Path to temp file
    local temp_file
    temp_file=$(mktemp)

    # Track for cleanup
    CE_TEMP_FILES+=("${temp_file}")

    echo "${temp_file}"
}

ce_create_temp_dir() {
    # Create temporary directory and return path
    # Ensures cleanup on exit
    # Returns: Path to temp directory
    local temp_dir
    temp_dir=$(mktemp -d)

    # Track for cleanup
    CE_TEMP_DIRS+=("${temp_dir}")

    echo "${temp_dir}"
}

ce_die() {
    # Print error and exit with code
    # Usage: ce_die "Fatal error occurred" 1
    local message="${1:-Unknown error}"
    local exit_code="${2:-1}"

    ce_log_error "${message}"
    exit "${exit_code}"
}

ce_debug_mode() {
    # Check if debug mode is enabled
    # Returns: 0 if enabled, 1 otherwise
    [[ ${CE_CURRENT_LOG_LEVEL} -le ${CE_LOG_LEVEL_DEBUG} ]]
}

ce_enable_debug() {
    # Enable debug logging
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_DEBUG}
    ce_log_debug "Debug mode enabled"
}

ce_disable_debug() {
    # Disable debug logging
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_INFO}
}

# ============================================================================
# Export Functions
# ============================================================================

# Export all functions for use in subshells
export -f ce_log_debug
export -f ce_log_info
export -f ce_log_warn
export -f ce_log_error
export -f ce_log_success
export -f ce_color_text
export -f ce_color_red
export -f ce_color_green
export -f ce_color_yellow
export -f ce_color_blue
export -f ce_require_command
export -f ce_require_file
export -f ce_get_project_root
export -f ce_get_current_branch
export -f ce_get_timestamp
export -f ce_confirm
export -f ce_prompt
export -f ce_spinner
export -f ce_progress_bar
export -f ce_trim
export -f ce_join
export -f ce_is_git_repo
export -f ce_is_ce_project
export -f ce_get_ce_version
export -f ce_format_duration
export -f ce_format_bytes
export -f ce_create_temp_file
export -f ce_create_temp_dir
export -f ce_die
export -f ce_debug_mode
export -f ce_enable_debug
export -f ce_disable_debug
export -f ce_create_secure_file
export -f ce_create_secure_dir
export -f ce_log_sanitize
