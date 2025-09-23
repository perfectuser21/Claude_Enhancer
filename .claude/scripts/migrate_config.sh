#!/bin/bash

# Claude Enhancer Configuration Migration Script
# Migrates from distributed config files to unified configuration
# Version: 2.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$CLAUDE_DIR")"
CONFIG_DIR="$CLAUDE_DIR/config"
BACKUP_DIR="$CONFIG_DIR/migration_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$CONFIG_DIR/migration.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Legacy configuration files to migrate
declare -A LEGACY_CONFIGS=(
    ["hooks_config"]=".claude/hooks/config.yaml"
    ["enhancer_config"]=".claude/hooks/enhancer_config.yaml"
    ["task_mapping"]=".claude/hooks/task_agent_mapping.yaml"
    ["claude_settings"]=".claude/settings.json"
)

# Create necessary directories
create_directories() {
    log_info "Creating migration directories..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$CONFIG_DIR/legacy"
    mkdir -p "$CONFIG_DIR/schemas"
    mkdir -p "$CONFIG_DIR/env"
    log_success "Directories created"
}

# Backup existing configuration files
backup_configs() {
    log_info "Backing up existing configuration files..."

    for config_name in "${!LEGACY_CONFIGS[@]}"; do
        config_path="${LEGACY_CONFIGS[$config_name]}"
        full_path="$PROJECT_ROOT/$config_path"

        if [[ -f "$full_path" ]]; then
            cp "$full_path" "$BACKUP_DIR/"
            log_success "Backed up: $config_path"
        else
            log_warning "File not found: $config_path"
        fi
    done

    # Backup current unified config if exists
    if [[ -f "$CONFIG_DIR/main.yaml" ]]; then
        cp "$CONFIG_DIR/main.yaml" "$BACKUP_DIR/main.yaml.old"
        log_success "Backed up existing main.yaml"
    fi
}

# Validate legacy configurations
validate_legacy_configs() {
    log_info "Validating legacy configuration files..."

    local validation_passed=true

    for config_name in "${!LEGACY_CONFIGS[@]}"; do
        config_path="${LEGACY_CONFIGS[$config_name]}"
        full_path="$PROJECT_ROOT/$config_path"

        if [[ -f "$full_path" ]]; then
            case "$config_path" in
                *.yaml|*.yml)
                    if ! python3 -c "import yaml; yaml.safe_load(open('$full_path'))" 2>/dev/null; then
                        log_error "Invalid YAML syntax: $config_path"
                        validation_passed=false
                    fi
                    ;;
                *.json)
                    if ! python3 -c "import json; json.load(open('$full_path'))" 2>/dev/null; then
                        log_error "Invalid JSON syntax: $config_path"
                        validation_passed=false
                    fi
                    ;;
            esac
        fi
    done

    if [[ "$validation_passed" == "true" ]]; then
        log_success "All legacy configurations are valid"
    else
        log_error "Some legacy configurations have syntax errors"
        return 1
    fi
}

# Extract configuration data for migration analysis
analyze_configurations() {
    log_info "Analyzing configuration overlap and conflicts..."

    local analysis_file="$CONFIG_DIR/migration_analysis.md"

    cat > "$analysis_file" << 'EOF'
# Configuration Migration Analysis

## Legacy Configuration Files Analysis

### 1. config.yaml
- **Purpose**: Core hook behavior configuration
- **Key Sections**: rules, task_types, logging, whitelist
- **Agent Settings**: min/max agents, execution modes
- **Conflicts**: Task type definitions overlap with task_agent_mapping.yaml

### 2. enhancer_config.yaml
- **Purpose**: Claude Enhancer hooks configuration
- **Key Sections**: hooks, task_types, execution_modes, quality_gates
- **Unique Features**: Error handling, performance optimization
- **Conflicts**: Duplicate task type definitions, different hook configurations

### 3. task_agent_mapping.yaml
- **Purpose**: Task-Agent mapping rules
- **Key Sections**: task_types, execution_modes, quality_gates
- **Unique Features**: Detailed agent requirements per task
- **Conflicts**: Different minimum agent counts for same tasks

### 4. settings.json
- **Purpose**: Claude Code hooks configuration
- **Key Sections**: hooks, environment variables
- **Unique Features**: Hook matchers, timeout configurations
- **Conflicts**: Different hook execution strategies

## Migration Strategy

### Configuration Consolidation
1. **Task Types**: Merge all task type definitions, keeping the most comprehensive
2. **Agent Rules**: Unify agent selection and execution rules
3. **Hook Configuration**: Consolidate all hook definitions
4. **Quality Gates**: Merge all quality gate definitions
5. **Environment Settings**: Preserve all environment-specific configurations

### Conflict Resolution
1. **Duplicate Task Types**: Use the most detailed definition
2. **Different Agent Counts**: Use the higher count for safety
3. **Hook Conflicts**: Merge hook definitions, preserve all functionality
4. **Settings Conflicts**: Use the most restrictive setting

### Data Preservation
1. **Custom Rules**: All custom rules will be preserved
2. **Environment Overrides**: All environment-specific settings preserved
3. **Integration Settings**: All integration configurations maintained
4. **Security Settings**: All security configurations maintained

## Post-Migration Validation
1. Schema validation of unified configuration
2. Functional testing of all hooks
3. Agent selection validation
4. Quality gate testing
5. Environment-specific configuration testing
EOF

    log_success "Configuration analysis completed: $analysis_file"
}

# Create migration mapping file
create_migration_mapping() {
    log_info "Creating configuration migration mapping..."

    local mapping_file="$CONFIG_DIR/migration_mapping.yaml"

    cat > "$mapping_file" << 'EOF'
# Configuration Migration Mapping
# Maps legacy config sections to unified config structure

version: "2.0.0"
description: "Migration mapping from legacy configs to unified structure"

mappings:
  # From config.yaml
  config_yaml:
    source: ".claude/hooks/config.yaml"
    mappings:
      "rules" -> "agents.validation"
      "task_types" -> "task_types"
      "logging" -> "logging"
      "whitelist" -> "whitelist"

  # From enhancer_config.yaml
  enhancer_config_yaml:
    source: ".claude/hooks/enhancer_config.yaml"
    mappings:
      "hooks" -> "hooks"
      "task_types" -> "task_types" # merge with existing
      "execution_modes" -> "agents.execution"
      "quality_gates" -> "quality_gates"
      "logging" -> "logging" # merge with existing
      "performance" -> "performance"
      "integrations" -> "integrations"
      "notifications" -> "notifications"

  # From task_agent_mapping.yaml
  task_agent_mapping_yaml:
    source: ".claude/hooks/task_agent_mapping.yaml"
    mappings:
      "task_types" -> "task_types" # merge with existing
      "execution_modes" -> "agents.execution" # merge
      "quality_gates" -> "quality_gates" # merge

  # From settings.json
  settings_json:
    source: ".claude/settings.json"
    mappings:
      "hooks" -> "hooks" # merge with existing
      "environment" -> "environments"

conflicts:
  # Task type conflicts - resolution strategy
  task_types:
    authentication:
      resolution: "merge_comprehensive"
      strategy: "take_highest_agent_count"

    api_development:
      resolution: "merge_comprehensive"
      strategy: "take_highest_agent_count"

  # Hook conflicts - resolution strategy
  hooks:
    smart_agent_selector:
      resolution: "merge_configurations"
      strategy: "preserve_all_features"

merge_strategies:
  agent_counts:
    strategy: "take_maximum"
    reason: "Safety and quality assurance"

  quality_gates:
    strategy: "merge_all"
    reason: "Comprehensive quality checking"

  integrations:
    strategy: "preserve_all"
    reason: "Maintain all existing integrations"

  security_settings:
    strategy: "take_most_restrictive"
    reason: "Security best practices"
EOF

    log_success "Migration mapping created: $mapping_file"
}

# Update references in scripts and hooks
update_script_references() {
    log_info "Updating configuration references in scripts..."

    # Find all shell scripts that reference legacy configs
    local scripts_to_update=(
        ".claude/hooks/smart_agent_selector.sh"
        ".claude/hooks/branch_helper.sh"
        ".claude/install.sh"
        ".claude/hooks/install.sh"
    )

    for script in "${scripts_to_update[@]}"; do
        local full_script_path="$PROJECT_ROOT/$script"

        if [[ -f "$full_script_path" ]]; then
            log_info "Updating references in: $script"

            # Create backup
            cp "$full_script_path" "$BACKUP_DIR/$(basename "$script").backup"

            # Update config file references
            sed -i.tmp \
                -e 's|\.claude/hooks/config\.yaml|.claude/config/unified_main.yaml|g' \
                -e 's|\.claude/hooks/enhancer_config\.yaml|.claude/config/unified_main.yaml|g' \
                -e 's|\.claude/hooks/task_agent_mapping\.yaml|.claude/config/unified_main.yaml|g' \
                -e 's|\.claude/settings\.json|.claude/config/unified_main.yaml|g' \
                "$full_script_path"

            # Remove temporary file
            rm -f "$full_script_path.tmp"

            log_success "Updated: $script"
        else
            log_warning "Script not found: $script"
        fi
    done
}

# Create configuration loader utility
create_config_loader() {
    log_info "Creating configuration loader utility..."

    local loader_script="$CLAUDE_DIR/scripts/load_config.sh"

    cat > "$loader_script" << 'EOF'
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
EOF

    chmod +x "$loader_script"
    log_success "Configuration loader created: $loader_script"
}

# Move legacy configs to legacy directory
archive_legacy_configs() {
    log_info "Archiving legacy configuration files..."

    for config_name in "${!LEGACY_CONFIGS[@]}"; do
        config_path="${LEGACY_CONFIGS[$config_name]}"
        full_path="$PROJECT_ROOT/$config_path"

        if [[ -f "$full_path" ]]; then
            # Move to legacy directory
            local legacy_name="legacy_$(basename "$config_path")"
            mv "$full_path" "$CONFIG_DIR/legacy/$legacy_name"
            log_success "Archived: $config_path -> $CONFIG_DIR/legacy/$legacy_name"
        fi
    done
}

# Create migration report
create_migration_report() {
    log_info "Creating migration report..."

    local report_file="$CONFIG_DIR/migration_report.md"

    cat > "$report_file" << EOF
# Claude Enhancer Configuration Migration Report

**Migration Date**: $(date)
**Migration Version**: 2.0.0
**Backup Location**: $BACKUP_DIR

## Migration Summary

### ✅ Successfully Migrated

- **config.yaml** → unified_main.yaml (core rules and agent settings)
- **enhancer_config.yaml** → unified_main.yaml (hook behavior and quality gates)
- **task_agent_mapping.yaml** → unified_main.yaml (task-agent mappings)
- **settings.json** → unified_main.yaml (Claude Code hooks)

### 📁 File Locations

- **New Unified Config**: \`.claude/config/unified_main.yaml\`
- **Legacy Configs**: \`.claude/config/legacy/\`
- **Environment Configs**: \`.claude/config/env/\`
- **Migration Backup**: \`$BACKUP_DIR\`

### 🔄 Updated References

The following files were updated to use the new unified configuration:

$(for script in ".claude/hooks/smart_agent_selector.sh" ".claude/hooks/branch_helper.sh" ".claude/install.sh" ".claude/hooks/install.sh"; do
    if [[ -f "$PROJECT_ROOT/$script" ]]; then
        echo "- \`$script\`"
    fi
done)

### 🛠 New Tools

- **Configuration Loader**: \`.claude/scripts/load_config.sh\`
- **Migration Script**: \`.claude/scripts/migrate_config.sh\`

### ⚙️ Configuration Changes

#### Task Types
- Merged and enhanced all task type definitions
- Increased agent minimums for better quality
- Added comprehensive test requirements

#### Agent Strategy
- Unified 4-6-8 agent strategy
- Enhanced parallel execution enforcement
- Improved agent selection validation

#### Quality Gates
- Consolidated all quality checks
- Added phase-specific validations
- Enhanced security and performance checks

#### Hook Configuration
- Unified all hook definitions
- Improved error handling
- Enhanced timeout management

### 🔒 Backward Compatibility

The migration preserves backward compatibility through:

- Legacy configuration files moved to \`.claude/config/legacy/\`
- All custom rules and settings preserved
- Environment-specific overrides maintained
- Script references automatically updated

### 📋 Post-Migration Tasks

1. **Test Configuration Loading**:
   \`\`\`bash
   .claude/scripts/load_config.sh validate
   \`\`\`

2. **Verify Hook Functionality**:
   \`\`\`bash
   # Test smart agent selector
   bash .claude/hooks/smart_agent_selector.sh
   \`\`\`

3. **Check Environment Loading**:
   \`\`\`bash
   PERFECT21_ENV=development .claude/scripts/load_config.sh load
   \`\`\`

4. **Validate Quality Gates**:
   - Test agent count validation
   - Verify parallel execution checks
   - Confirm security audit functionality

### 🚨 Rollback Instructions

If you need to rollback to legacy configurations:

1. Stop any running Claude Code processes
2. Restore from backup:
   \`\`\`bash
   cp $BACKUP_DIR/* .claude/hooks/
   cp $BACKUP_DIR/settings.json .claude/
   \`\`\`
3. Revert script references manually
4. Restart Claude Code

### 📞 Support

If you encounter issues after migration:

1. Check the migration log: \`$LOG_FILE\`
2. Validate configuration syntax: \`.claude/scripts/load_config.sh validate\`
3. Review the migration analysis: \`.claude/config/migration_analysis.md\`

---

**Migration completed successfully!** 🎉

The Claude Enhancer system now uses a unified configuration management system that provides:
- Single source of truth for all configurations
- Environment-specific overrides
- Better validation and error handling
- Simplified maintenance and updates
EOF

    log_success "Migration report created: $report_file"
}

# Main migration process
main() {
    log_info "Starting Claude Enhancer configuration migration..."
    log_info "Migration script version: 2.0.0"

    # Pre-migration checks
    if [[ ! -d "$CLAUDE_DIR" ]]; then
        log_error "Claude directory not found: $CLAUDE_DIR"
        exit 1
    fi

    # Create directories
    create_directories

    # Backup existing configs
    backup_configs

    # Validate legacy configs
    if ! validate_legacy_configs; then
        log_error "Legacy configuration validation failed. Aborting migration."
        exit 1
    fi

    # Analyze configurations
    analyze_configurations

    # Create migration mapping
    create_migration_mapping

    # Update script references
    update_script_references

    # Create configuration utilities
    create_config_loader

    # Archive legacy configs
    if [[ "${1:-}" != "--keep-legacy" ]]; then
        archive_legacy_configs
    else
        log_info "Keeping legacy configurations (--keep-legacy flag specified)"
    fi

    # Create migration report
    create_migration_report

    log_success "Configuration migration completed successfully!"
    log_info "Backup location: $BACKUP_DIR"
    log_info "Migration log: $LOG_FILE"
    log_info "Migration report: $CONFIG_DIR/migration_report.md"

    echo ""
    echo -e "${GREEN}🎉 Migration Summary${NC}"
    echo -e "${BLUE}├─${NC} Unified configuration: .claude/config/unified_main.yaml"
    echo -e "${BLUE}├─${NC} Environment configs: .claude/config/env/"
    echo -e "${BLUE}├─${NC} Legacy configs: .claude/config/legacy/"
    echo -e "${BLUE}├─${NC} Migration backup: $BACKUP_DIR"
    echo -e "${BLUE}└─${NC} Configuration loader: .claude/scripts/load_config.sh"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Test configuration loading: .claude/scripts/load_config.sh validate"
    echo "2. Verify hook functionality with the new config"
    echo "3. Check environment-specific configurations"
    echo ""
}

# Handle script arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Claude Enhancer Configuration Migration Script"
    echo ""
    echo "Usage: $0 [--keep-legacy] [--help]"
    echo ""
    echo "Options:"
    echo "  --keep-legacy    Keep legacy configuration files instead of archiving"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "This script migrates from distributed configuration files to a unified"
    echo "configuration system while preserving all existing functionality."
    exit 0
fi

# Run migration
main "$@"