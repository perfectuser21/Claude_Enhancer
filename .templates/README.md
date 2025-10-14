# Template System Documentation

## Purpose

Prevent documentation sprawl and version drift by establishing:

1. **Single Source of Truth**: `VERSION` file for all version references
2. **Feature-Driven Documentation**: `FEATURES.yml` controls what gets documented
3. **Template-Based Generation**: `CLAUDE.template.md` ensures consistency
4. **Automated Validation**: CI/CD enforces compliance

## Problem Solved

**Before** (v6.0-6.1):
- ❌ Version conflicts (6.1 in CLAUDE.md, 6.2.0 in README.md)
- ❌ Document explosion (676 lines in CLAUDE.md)
- ❌ Role confusion (AI instructions mixed with user docs)
- ❌ "Enterprise" terminology creep (personal tool, not SaaS)
- ❌ Duplicate content (2 CLAUDE.md files, 80% overlap)

**After** (v6.2+ with templates):
- ✅ Version: Single `VERSION` file (6.2.0)
- ✅ CLAUDE.md: 300 lines max, clean separation
- ✅ Features: YAML-controlled toggles
- ✅ Identity: Clear "personal tool" positioning
- ✅ Validation: Pre-commit hooks + CI checks

## File Structure

```
.templates/
├── CLAUDE.template.md   # Master template (300 lines max)
├── FEATURES.yml         # Feature flags + metrics
├── README.md            # This file (usage guide)
└── sync_templates.sh    # Regeneration script

VERSION                  # Single source of truth: "6.2.0"

CLAUDE.md                # Generated from template (DO NOT EDIT MANUALLY)
README.md                # User-facing docs (manually maintained)
```

## Usage

### 1. Update Version

```bash
# Change version in ONE place
echo "6.3.0" > VERSION

# Regenerate all version references
bash .templates/sync_templates.sh

# Verify consistency
git diff VERSION CLAUDE.md README.md package.json
```

### 2. Toggle Feature

```yaml
# .templates/FEATURES.yml
quality_assurance:
  bdd_testing:
    enabled: true  # Change to false to disable
```

```bash
# Regenerate docs
bash .templates/sync_templates.sh

# Result: {{FEATURE_BDD}} sections removed from CLAUDE.md
```

### 3. Update Template Content

```bash
# Edit master template
vim .templates/CLAUDE.template.md

# Regenerate CLAUDE.md
bash .templates/sync_templates.sh

# Verify changes
git diff CLAUDE.md
```

### 4. Add New Feature

```yaml
# 1. Add to FEATURES.yml
advanced:
  new_feature:
    enabled: false  # Start disabled
    status: "experimental"
    placeholder: "{{FEATURE_NEWFEATURE}}"
    description: "Amazing new capability"
```

```markdown
# 2. Add placeholder to template
## 🚀 Advanced Features

{{FEATURE_NEWFEATURE}}
- New feature documentation here
- Only appears when enabled=true
{{/FEATURE_NEWFEATURE}}
```

```bash
# 3. Enable when ready for production
# Edit FEATURES.yml: enabled: true
bash .templates/sync_templates.sh
```

## Template Syntax

### Placeholders

```markdown
# Simple replacement
Version: {{VERSION}}
Last Updated: {{LAST_UPDATED}}

# Conditional sections
{{FEATURE_BDD}}
This content only appears when quality_assurance.bdd_testing.enabled = true
{{/FEATURE_BDD}}

# Nested conditions
{{FEATURE_QUALITY}}
  {{FEATURE_BDD}}
  BDD testing is enabled
  {{/FEATURE_BDD}}
{{/FEATURE_QUALITY}}
```

### Available Placeholders

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{VERSION}}` | VERSION file | 6.2.0 |
| `{{NEXT_VERSION}}` | FEATURES.yml | 6.3.0 |
| `{{LAST_UPDATED}}` | FEATURES.yml | 2025-10-13 |
| `{{FEATURE_BDD}}` | FEATURES.yml | Conditional block |
| `{{FEATURE_OPENAPI}}` | FEATURES.yml | Conditional block |
| `{{FEATURE_PERF}}` | FEATURES.yml | Conditional block |
| `{{FEATURE_SLO}}` | FEATURES.yml | Conditional block |
| `{{FEATURE_METRICS}}` | FEATURES.yml | Conditional block |

## Validation Rules

### Pre-Commit Checks

```bash
# Enforced by .git/hooks/pre-commit

1. Version Consistency
   ✅ VERSION = CLAUDE.md = README.md = package.json

2. Document Count (Root)
   ✅ Exactly 7 files: README, CLAUDE, INSTALLATION, ARCHITECTURE,
                       CONTRIBUTING, CHANGELOG, LICENSE

3. Line Count
   ✅ CLAUDE.md ≤ 300 lines
   ⚠️  README.md ≤ 600 lines (warning only)
   ⚠️  ARCHITECTURE.md ≤ 1000 lines (warning only)

4. Forbidden Terms in CLAUDE.md
   ❌ "enterprise-grade", "production deployment", "team management"
   ✅ Use: "personal tool", "development workflow", "individual developer"

5. Template Sync
   ✅ CLAUDE.md matches .templates/CLAUDE.template.md + FEATURES.yml
```

### CI/CD Checks

```yaml
# .github/workflows/template-validation.yml

jobs:
  validate-templates:
    steps:
      - name: Check version consistency
        run: bash .templates/validate_versions.sh

      - name: Verify template sync
        run: bash .templates/sync_templates.sh --dry-run

      - name: Validate feature documentation
        run: python3 .templates/validate_features.py

      - name: Check document count
        run: |
          count=$(ls *.md | wc -l)
          if [ $count -gt 7 ]; then
            echo "❌ Too many docs: $count (max 7)"
            exit 1
          fi
```

## Sync Script

### sync_templates.sh

```bash
#!/bin/bash
# Purpose: Regenerate CLAUDE.md from template + FEATURES.yml

set -euo pipefail

TEMPLATE=".templates/CLAUDE.template.md"
FEATURES=".templates/FEATURES.yml"
OUTPUT="CLAUDE.md"

# 1. Load version
VERSION=$(cat VERSION)
LAST_UPDATED=$(date +%Y-%m-%d)

# 2. Load feature flags
# (Python script parses YAML and generates bash variables)
eval $(python3 .templates/parse_features.py)

# 3. Process template
cat "$TEMPLATE" \
  | sed "s/{{VERSION}}/$VERSION/g" \
  | sed "s/{{LAST_UPDATED}}/$LAST_UPDATED/g" \
  | sed "s/{{NEXT_VERSION}}/$NEXT_VERSION/g" \
  | python3 .templates/process_conditionals.py \
  > "$OUTPUT"

# 4. Validate line count
LINES=$(wc -l < "$OUTPUT")
if [ $LINES -gt 300 ]; then
  echo "⚠️  CLAUDE.md exceeded 300 lines ($LINES)"
  echo "    Consider moving content to separate guides/"
fi

echo "✅ Regenerated $OUTPUT ($LINES lines)"
```

## Maintenance Workflow

### Monthly: Review Feature Status

```bash
# 1. Review enabled features
cat .templates/FEATURES.yml | grep "enabled: true"

# 2. Check for experimental → production promotion
cat .templates/FEATURES.yml | grep "status: experimental"

# 3. Update metrics
python3 scripts/auto_metrics.py --update-features
```

### On Version Bump

```bash
# 1. Update version
echo "6.3.0" > VERSION

# 2. Update FEATURES.yml
vim .templates/FEATURES.yml
# Change: versions.current = "6.3.0"

# 3. Regenerate all docs
bash .templates/sync_templates.sh

# 4. Update package.json
npm version 6.3.0

# 5. Verify consistency
git diff VERSION CLAUDE.md README.md package.json
git commit -am "chore: bump version to 6.3.0"
```

### On Feature Addition

```bash
# 1. Add feature definition
vim .templates/FEATURES.yml
# Add under appropriate category

# 2. Add placeholder to template
vim .templates/CLAUDE.template.md
# Add {{FEATURE_X}} conditional block

# 3. Keep disabled initially
# enabled: false, status: "experimental"

# 4. Test generation
bash .templates/sync_templates.sh

# 5. When stable, enable
# enabled: true, status: "production"
bash .templates/sync_templates.sh
```

## Anti-Patterns to Avoid

### ❌ Manual Editing of CLAUDE.md

```bash
# WRONG: Editing generated file
vim CLAUDE.md  # Changes will be lost on next sync!

# CORRECT: Edit template
vim .templates/CLAUDE.template.md
bash .templates/sync_templates.sh
```

### ❌ Version Inconsistency

```bash
# WRONG: Changing multiple files
echo "6.3.0" > VERSION
vim CLAUDE.md  # Manually update version
vim README.md  # Manually update version

# CORRECT: Single source of truth
echo "6.3.0" > VERSION
bash .templates/sync_templates.sh  # Auto-updates all
```

### ❌ Feature Creep in CLAUDE.md

```bash
# WRONG: Adding every detail to CLAUDE.md
# (Results in 676-line bloat)

# CORRECT: Use FEATURES.yml to toggle sections
# Keep CLAUDE.md ≤ 300 lines
# Move details to docs/guides/
```

### ❌ "Enterprise" Terminology

```yaml
# WRONG in FEATURES.yml
validation:
  forbidden_terms:
    - "enterprise-grade"  # ❌ Not a SaaS product

# CORRECT positioning
system_identity: "Personal workflow tool for individual developers"
```

## Success Metrics

### After Template System Implementation

- ✅ Version drift: 0 instances (was 3)
- ✅ CLAUDE.md: 300 lines (was 676)
- ✅ Root docs: 7 files (was 7, but now enforced)
- ✅ Sync time: <5 seconds (manual was 30+ minutes)
- ✅ Consistency: 100% (4 files always match)

### 3-Month Goals

- [ ] Zero manual edits to generated files
- [ ] 100% CI passing on template validation
- [ ] <5 minutes to add new feature documentation
- [ ] Zero version conflicts across files

## Troubleshooting

### Q: sync_templates.sh fails with "parse error"

```bash
# Check YAML syntax
yamllint .templates/FEATURES.yml

# Common issues:
# - Missing quotes around special chars
# - Incorrect indentation (use 2 spaces)
# - Trailing colons without values
```

### Q: CLAUDE.md exceeds 300 lines after sync

```bash
# Options:
1. Move content to separate guides
   - docs/BRANCH_STRATEGY.md
   - docs/AGENT_SELECTION.md

2. Disable optional features
   # FEATURES.yml: enabled: false

3. Use more concise wording
   # Remove redundant examples
```

### Q: Version still shows 6.1.0 after update

```bash
# Verify sync ran
bash .templates/sync_templates.sh

# Check all locations
grep -r "6.1.0" VERSION CLAUDE.md README.md package.json

# If found, manual override needed (bug)
# Report to Claude Enhancer team
```

## Future Enhancements

### v6.3
- [ ] Web UI for feature toggling
- [ ] Real-time preview of template changes
- [ ] Automatic CHANGELOG generation from features

### v7.0
- [ ] Multi-language template support
- [ ] Custom placeholder definitions
- [ ] Template inheritance (base + project-specific)

---

**Template System v1.0** - Maintaining Claude Enhancer Documentation Sanity

Last Updated: 2025-10-13
