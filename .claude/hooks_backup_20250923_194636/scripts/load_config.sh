#!/bin/bash

# Claude Enhancer Configuration Loader
# Loads unified configuration with environment overrides

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$CLAUDE_DIR/config"

# Default configuration file
DEFAULT_CONFIG="$CONFIG_DIR/unified_main.yaml"

# Environment detection
detect_environment() {
    if [[ -n "${PERFECT21_ENV:-}" ]]; then
        echo "$PERFECT21_ENV"
    elif [[ -f ".env" ]]; then
        grep "PERFECT21_ENV" .env | cut -d'=' -f2 | tr -d '"'
    else
        echo "development"
    fi
}

# Load configuration
load_config() {
    local env="${1:-$(detect_environment)}"
    local config_file="$DEFAULT_CONFIG"
    local env_config="$CONFIG_DIR/env/${env}.yaml"

    echo "Loading configuration for environment: $env" >&2

    if [[ -f "$env_config" ]]; then
        echo "Environment override: $env_config" >&2
        echo "$env_config"
    else
        echo "Using default config: $config_file" >&2
        echo "$config_file"
    fi
}

# Validate configuration
validate_config() {
    local config_file="$1"

    if [[ ! -f "$config_file" ]]; then
        echo "Error: Configuration file not found: $config_file" >&2
        return 1
    fi

    # Validate YAML syntax
    if command -v python3 >/dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$config_file'))" 2>/dev/null || {
            echo "Error: Invalid YAML syntax in: $config_file" >&2
            return 1
        }
    fi

    echo "Configuration validated: $config_file" >&2
}

# Main function
main() {
    local command="${1:-load}"

    case "$command" in
        "load")
            local config_file
            config_file="$(load_config "${2:-}")"
            validate_config "$config_file"
            echo "$config_file"
            ;;
        "validate")
            validate_config "${2:-$DEFAULT_CONFIG}"
            ;;
        "env")
            detect_environment
            ;;
        *)
            echo "Usage: $0 {load|validate|env} [environment]" >&2
            exit 1
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
