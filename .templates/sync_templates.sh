#!/bin/bash
# Claude Enhancer Template Sync Script
# Purpose: Regenerate CLAUDE.md from template + FEATURES.yml
# Usage: bash .templates/sync_templates.sh [--dry-run]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$SCRIPT_DIR/CLAUDE.template.md"
FEATURES="$SCRIPT_DIR/FEATURES.yml"
OUTPUT="$PROJECT_ROOT/CLAUDE.md"
VERSION_FILE="$PROJECT_ROOT/VERSION"

# Flags
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

# Logging
log_info() {
  echo -e "${GREEN}✅${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}⚠️${NC}  $1"
}

log_error() {
  echo -e "${RED}❌${NC} $1"
}

# Validation
validate_prerequisites() {
  log_info "Validating prerequisites..."

  if [[ ! -f "$TEMPLATE" ]]; then
    log_error "Template not found: $TEMPLATE"
    exit 1
  fi

  if [[ ! -f "$FEATURES" ]]; then
    log_error "Features config not found: $FEATURES"
    exit 1
  fi

  if [[ ! -f "$VERSION_FILE" ]]; then
    log_error "VERSION file not found: $VERSION_FILE"
    exit 1
  fi

  # Check for required tools
  if ! command -v python3 &> /dev/null; then
    log_error "python3 not found (required for YAML parsing)"
    exit 1
  fi
}

# Load version
load_version() {
  VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
  LAST_UPDATED=$(date +%Y-%m-%d)

  log_info "Version: $VERSION"
  log_info "Last Updated: $LAST_UPDATED"
}

# Parse FEATURES.yml and export as environment variables
parse_features() {
  log_info "Parsing feature flags..."

  # Simple Python YAML parser
  cat > /tmp/parse_features.py << 'PYTHON_SCRIPT'
import yaml
import sys

with open(sys.argv[1], 'r') as f:
    config = yaml.safe_load(f)

# Export basic variables
versions = config.get('versions', {})
print(f"export NEXT_VERSION='{versions.get('next_minor', '6.3.0')}'")

# Export feature flags
qa = config.get('quality_assurance', {})
for feature_name, feature_config in qa.items():
    enabled = feature_config.get('enabled', False)
    var_name = f"FEATURE_{feature_name.upper()}"
    print(f"export {var_name}='{str(enabled).lower()}'")

# Export advanced features
advanced = config.get('advanced', {})
for feature_name, feature_config in advanced.items():
    enabled = feature_config.get('enabled', False)
    var_name = f"FEATURE_{feature_name.upper()}"
    print(f"export {var_name}='{str(enabled).lower()}'")
PYTHON_SCRIPT

  # Check if PyYAML is installed
  if ! python3 -c "import yaml" 2>/dev/null; then
    log_warn "PyYAML not installed, installing..."
    pip3 install pyyaml --quiet || {
      log_error "Failed to install PyYAML"
      log_error "Install manually: pip3 install pyyaml"
      exit 1
    }
  fi

  # Execute and export
  eval "$(python3 /tmp/parse_features.py "$FEATURES")"
  rm -f /tmp/parse_features.py

  log_info "Feature flags loaded"
}

# Process conditional blocks in template
process_conditionals() {
  local input_file="$1"

  # Python script to handle {{FEATURE_X}} ... {{/FEATURE_X}} blocks
  cat > /tmp/process_template.py << 'PYTHON_SCRIPT'
import sys
import re
import os

def process_template(content):
    # Pattern: {{FEATURE_NAME}} ... {{/FEATURE_NAME}}
    pattern = r'\{\{FEATURE_(\w+)\}\}(.*?)\{\{/FEATURE_\1\}\}'

    def replace_feature(match):
        feature_name = match.group(1)
        feature_content = match.group(2)

        # Check environment variable
        var_name = f"FEATURE_{feature_name}"
        enabled = os.getenv(var_name, 'false').lower() == 'true'

        if enabled:
            # Keep content, remove markers
            return feature_content.strip()
        else:
            # Remove entire block
            return ''

    # Process all feature blocks (including nested)
    prev = None
    while prev != content:
        prev = content
        content = re.sub(pattern, replace_feature, content, flags=re.DOTALL)

    return content

# Read from stdin
content = sys.stdin.read()
processed = process_template(content)
print(processed)
PYTHON_SCRIPT

  python3 /tmp/process_template.py < "$input_file"
  rm -f /tmp/process_template.py
}

# Generate CLAUDE.md
generate_claude_md() {
  log_info "Generating CLAUDE.md..."

  # Step 1: Replace simple placeholders
  cat "$TEMPLATE" \
    | sed "s/{{VERSION}}/$VERSION/g" \
    | sed "s/{{NEXT_VERSION}}/$NEXT_VERSION/g" \
    | sed "s/{{LAST_UPDATED}}/$LAST_UPDATED/g" \
    > /tmp/claude_step1.md

  # Step 2: Process conditional blocks
  process_conditionals /tmp/claude_step1.md > /tmp/claude_step2.md

  # Step 3: Clean up extra blank lines
  cat /tmp/claude_step2.md \
    | sed '/^$/N;/^\n$/D' \
    > /tmp/claude_final.md

  rm -f /tmp/claude_step1.md /tmp/claude_step2.md

  # Validate line count
  LINES=$(wc -l < /tmp/claude_final.md)
  log_info "Generated $LINES lines"

  if [[ $LINES -gt 300 ]]; then
    log_warn "CLAUDE.md exceeds 300 lines ($LINES)"
    log_warn "Consider moving content to separate guides"
  fi

  # Write output
  if [[ "$DRY_RUN" == true ]]; then
    log_info "Dry run - would write to: $OUTPUT"
    log_info "Preview (first 20 lines):"
    head -20 /tmp/claude_final.md | sed 's/^/  /'
    rm -f /tmp/claude_final.md
  else
    mv /tmp/claude_final.md "$OUTPUT"
    log_info "Written to: $OUTPUT"
  fi
}

# Validate output
validate_output() {
  if [[ "$DRY_RUN" == true ]]; then
    return 0
  fi

  log_info "Validating output..."

  # Check version consistency
  if ! grep -q "$VERSION" "$OUTPUT"; then
    log_error "Version $VERSION not found in output"
    exit 1
  fi

  # Check for unprocessed placeholders
  UNPROCESSED=$(grep -E '\{\{[A-Z_]+\}\}' "$OUTPUT" || true)
  if [[ -n "$UNPROCESSED" ]]; then
    log_warn "Unprocessed placeholders found:"
    echo "$UNPROCESSED" | sed 's/^/  /'
  fi

  # Check forbidden terms
  FORBIDDEN=$(grep -E '(enterprise-grade|team management|production deployment)' "$OUTPUT" || true)
  if [[ -n "$FORBIDDEN" ]]; then
    log_warn "Forbidden terms found (check .templates/FEATURES.yml):"
    echo "$FORBIDDEN" | sed 's/^/  /'
  fi

  log_info "Validation complete"
}

# Update README.md version references (manual check only)
update_readme_version() {
  if [[ "$DRY_RUN" == true ]]; then
    return 0
  fi

  README="$PROJECT_ROOT/README.md"
  if [[ ! -f "$README" ]]; then
    log_warn "README.md not found, skipping version check"
    return 0
  fi

  # Check if README version matches
  if ! grep -q "# Claude Enhancer $VERSION" "$README"; then
    log_warn "README.md version mismatch"
    log_warn "Current: $(grep -m1 '# Claude Enhancer' "$README" || echo 'not found')"
    log_warn "Expected: # Claude Enhancer $VERSION"
    log_warn "Please update README.md manually or run: sed -i 's/# Claude Enhancer .*/# Claude Enhancer $VERSION/' README.md"
  else
    log_info "README.md version matches"
  fi
}

# Main
main() {
  echo "=================================="
  echo "Claude Enhancer Template Sync"
  echo "=================================="
  echo ""

  validate_prerequisites
  load_version
  parse_features
  generate_claude_md
  validate_output
  update_readme_version

  echo ""
  if [[ "$DRY_RUN" == true ]]; then
    log_info "Dry run complete (no files modified)"
  else
    log_info "Sync complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git diff CLAUDE.md"
    echo "  2. Verify consistency: bash scripts/validate_versions.sh"
    echo "  3. Commit: git add CLAUDE.md && git commit -m 'docs: sync template'"
  fi
}

main "$@"
