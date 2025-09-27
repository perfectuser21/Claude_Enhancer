#!/bin/bash
# =============================================================================
# Environment Variables Validation Script for Claude Enhancer 5.1
# Validates all required environment variables before deployment
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Validation counters
ERRORS=0
WARNINGS=0

# Function to check if variable is set and not empty
check_required() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -z "$var_value" ]]; then
        log_error "Required variable $var_name is not set or empty"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to check if variable meets minimum length requirement
check_min_length() {
    local var_name="$1"
    local min_length="$2"
    local var_value="${!var_name:-}"

    if [[ ${#var_value} -lt $min_length ]]; then
        log_error "Variable $var_name must be at least $min_length characters long"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to check if variable is a valid URL
check_url() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -n "$var_value" ]] && ! [[ "$var_value" =~ ^https?:// ]]; then
        log_error "Variable $var_name must be a valid URL starting with http:// or https://"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to check if variable is a valid email
check_email() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -n "$var_value" ]] && ! [[ "$var_value" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        log_error "Variable $var_name must be a valid email address"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to check if variable is a valid port number
check_port() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -n "$var_value" ]] && ! [[ "$var_value" =~ ^[0-9]+$ ]] || [[ "$var_value" -lt 1 ]] || [[ "$var_value" -gt 65535 ]]; then
        log_error "Variable $var_name must be a valid port number (1-65535)"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to warn about default values
warn_default() {
    local var_name="$1"
    local default_value="$2"
    local var_value="${!var_name:-}"

    if [[ "$var_value" == "$default_value" ]]; then
        log_warn "Variable $var_name is using default value. Consider changing for production."
        ((WARNINGS++))
    fi
}

# Function to check if secrets are strong enough
check_secret_strength() {
    local var_name="$1"
    local var_value="${!var_name:-}"

    if [[ -n "$var_value" ]]; then
        # Check for minimum length (32 characters)
        if [[ ${#var_value} -lt 32 ]]; then
            log_error "Secret $var_name should be at least 32 characters long for security"
            ((ERRORS++))
            return 1
        fi

        # Check for placeholder values
        if [[ "$var_value" =~ \<.*\> ]]; then
            log_error "Secret $var_name appears to contain placeholder value: $var_value"
            ((ERRORS++))
            return 1
        fi

        # Check if it's too simple (e.g., all same character)
        if [[ $(echo "$var_value" | grep -o . | sort -u | wc -l) -lt 5 ]]; then
            log_warn "Secret $var_name may be too simple (low character diversity)"
            ((WARNINGS++))
        fi
    fi
    return 0
}

# Main validation function
main() {
    log_info "Starting environment variables validation for Claude Enhancer 5.1"
    echo "=================================================================="

    # Load environment file if specified
    if [[ "${1:-}" ]]; then
        if [[ -f "$1" ]]; then
            log_info "Loading environment from file: $1"
            set -a
            source "$1"
            set +a
        else
            log_error "Environment file not found: $1"
            exit 1
        fi
    fi

    # Application Configuration
    log_info "Validating Application Configuration..."
    check_required "APP_NAME"
    check_required "APP_VERSION"
    check_required "CLAUDE_ENV"
    check_required "DOMAIN"
    check_url "API_BASE_URL"
    check_url "FRONTEND_URL"

    # Database Configuration
    log_info "Validating Database Configuration..."
    check_required "DB_NAME"
    check_required "DB_USER"
    check_required "DB_PASSWORD"
    check_required "DB_HOST"
    check_port "DB_PORT"
    check_min_length "DB_PASSWORD" 12
    warn_default "DB_PASSWORD" "password"
    warn_default "DB_USER" "postgres"

    # Redis Configuration
    log_info "Validating Redis Configuration..."
    check_required "REDIS_HOST"
    check_port "REDIS_PORT"
    check_required "REDIS_PASSWORD"
    check_min_length "REDIS_PASSWORD" 12
    warn_default "REDIS_PASSWORD" "password"

    # Security Configuration
    log_info "Validating Security Configuration..."
    check_required "JWT_ACCESS_SECRET"
    check_required "JWT_REFRESH_SECRET"
    check_required "SECRET_KEY"
    check_required "ENCRYPTION_KEY"

    check_secret_strength "JWT_ACCESS_SECRET"
    check_secret_strength "JWT_REFRESH_SECRET"
    check_secret_strength "SECRET_KEY"
    check_secret_strength "ENCRYPTION_KEY"

    # External Services
    log_info "Validating External Services..."
    if [[ -n "${SENTRY_DSN:-}" ]]; then
        check_url "SENTRY_DSN"
    fi

    if [[ -n "${SMTP_HOST:-}" ]]; then
        check_required "SMTP_USERNAME"
        check_required "SMTP_PASSWORD"
        check_port "SMTP_PORT"
        check_email "FROM_EMAIL"
    fi

    # Monitoring Configuration
    log_info "Validating Monitoring Configuration..."
    if [[ "${PROMETHEUS_ENABLED:-}" == "true" ]]; then
        check_port "PROMETHEUS_PORT"
    fi

    if [[ -n "${GRAFANA_ADMIN_PASSWORD:-}" ]]; then
        check_min_length "GRAFANA_ADMIN_PASSWORD" 8
        warn_default "GRAFANA_ADMIN_PASSWORD" "admin"
    fi

    # SSL Configuration
    log_info "Validating SSL Configuration..."
    if [[ -n "${SSL_CERT_PATH:-}" ]]; then
        check_required "SSL_KEY_PATH"
        if [[ ! -f "${SSL_CERT_PATH}" ]]; then
            log_error "SSL certificate file not found: ${SSL_CERT_PATH}"
            ((ERRORS++))
        fi
        if [[ ! -f "${SSL_KEY_PATH}" ]]; then
            log_error "SSL private key file not found: ${SSL_KEY_PATH}"
            ((ERRORS++))
        fi
    fi

    # Performance Configuration
    log_info "Validating Performance Configuration..."
    if [[ -n "${WORKERS:-}" ]] && ! [[ "${WORKERS}" =~ ^[0-9]+$ ]]; then
        log_error "WORKERS must be a positive integer"
        ((ERRORS++))
    fi

    if [[ -n "${MAX_WORKERS:-}" ]] && ! [[ "${MAX_WORKERS}" =~ ^[0-9]+$ ]]; then
        log_error "MAX_WORKERS must be a positive integer"
        ((ERRORS++))
    fi

    # Feature Flags Validation
    log_info "Validating Feature Flags..."
    for flag in ENABLE_METRICS ENABLE_TRACING ENABLE_RATE_LIMITING ENABLE_CSRF_PROTECTION; do
        if [[ -n "${!flag:-}" ]] && [[ "${!flag}" != "true" ]] && [[ "${!flag}" != "false" ]]; then
            log_error "Feature flag $flag must be 'true' or 'false'"
            ((ERRORS++))
        fi
    done

    # Production-specific checks
    if [[ "${CLAUDE_ENV:-}" == "production" ]]; then
        log_info "Performing production-specific validations..."

        # Debug must be disabled
        if [[ "${DEBUG:-}" == "true" ]]; then
            log_error "DEBUG must be 'false' in production"
            ((ERRORS++))
        fi

        # HTTPS requirement
        if [[ "${API_BASE_URL:-}" =~ ^http:// ]] || [[ "${FRONTEND_URL:-}" =~ ^http:// ]]; then
            log_error "HTTPS is required in production (http:// URLs detected)"
            ((ERRORS++))
        fi

        # Security features must be enabled
        for security_flag in ENABLE_CSRF_PROTECTION ENABLE_RATE_LIMITING; do
            if [[ "${!security_flag:-}" != "true" ]]; then
                log_error "Security feature $security_flag must be enabled in production"
                ((ERRORS++))
            fi
        done

        # Strong session security
        if [[ "${SESSION_COOKIE_SECURE:-}" != "true" ]]; then
            log_error "SESSION_COOKIE_SECURE must be 'true' in production"
            ((ERRORS++))
        fi
    fi

    # Summary
    echo "=================================================================="
    if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
        log_success "All environment variables are valid!"
        exit 0
    elif [[ $ERRORS -eq 0 ]]; then
        log_success "Environment validation passed with $WARNINGS warning(s)"
        exit 0
    else
        log_error "Environment validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
        echo
        log_error "Please fix the errors above before proceeding with deployment"
        exit 1
    fi
}

# Script help
show_help() {
    cat << EOF
Environment Variables Validation Script for Claude Enhancer 5.1

Usage: $0 [ENV_FILE]

Arguments:
  ENV_FILE    Optional path to environment file to validate

Examples:
  $0                                    # Validate current environment
  $0 .env.production                    # Validate specific env file
  $0 /path/to/production.env           # Validate env file with full path

The script validates:
  - Required variables are set
  - Secrets meet minimum security requirements
  - URLs and emails are properly formatted
  - Production-specific security settings
  - Port numbers are valid
  - File paths exist (for SSL certificates)

Exit codes:
  0 - All validations passed
  1 - Validation errors found
EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac