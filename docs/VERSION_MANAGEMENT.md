# Version Management Guide

## 📖 Overview

Claude Enhancer uses a **Single Source of Truth** approach for version management. All version numbers are derived from the root `VERSION` file and automatically synchronized to all relevant files.

## 🎯 Core Principles

### 1. Single Source of Truth
- **VERSION File**: The **only** authoritative source for version numbers
- **Location**: `/VERSION` (root directory)
- **Format**: Semantic versioning `X.Y.Z` (e.g., `5.3.4`)

### 2. Automatic Synchronization
- All version-containing files are automatically synced from VERSION
- No manual editing of version numbers in individual files
- Consistency enforced by pre-commit hooks

### 3. Validation Before Commit
- Git hooks verify version consistency before every commit
- Prevents commits with inconsistent versions
- Provides fix commands if inconsistency detected

## 📁 Version-Containing Files

The following files contain version numbers and are automatically synchronized:

| File | Format | Path Expression | Tool |
|------|--------|-----------------|------|
| `VERSION` | Plain text | - | Source file |
| `.workflow/manifest.yml` | YAML | `.version` | yq/sed |
| `.claude/settings.json` | JSON | `.version` | jq |
| `CHANGELOG.md` | Markdown | First `## [X.Y.Z]` | sed |
| `README.md` | Markdown | `version-X.Y.Z-blue` | sed |
| `package.json` (if exists) | JSON | `.version` | jq |

## 🛠️ Version Management Scripts

### sync_version.sh
**Purpose**: Synchronize VERSION to all files

**Usage**:
```bash
./scripts/sync_version.sh
```

**Features**:
- Reads version from VERSION file
- Validates semver format (X.Y.Z)
- Syncs to all version-containing files
- Creates backup files (.backup.timestamp)
- Reports success/failure for each file
- Cleans old backups (>7 days)

**Example Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version Synchronization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source Version: 5.3.4

Syncing to configuration files...
✓ Synced (yq): .workflow/manifest.yml
✓ Synced (jq): .claude/settings.json

Syncing to documentation files...
✓ Synced (sed): README.md
✓ Synced (sed): CLAUDE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version:         5.3.4
Files Processed: 4
Success:         4
Failed:          0

✅ All files synced successfully!
```

### verify_version_consistency.sh
**Purpose**: Verify all files have consistent versions

**Usage**:
```bash
./scripts/verify_version_consistency.sh
```

**Features**:
- Reads expected version from VERSION file
- Checks all version-containing files
- Reports pass/fail for each file
- Provides fix command if inconsistency found
- Exit code 0 if consistent, 1 if inconsistent

**Example Output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version Consistency Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected Version: 5.3.4

Checking configuration files...
✓ Workflow Manifest: 5.3.4
✓ Claude Settings: 5.3.4

Checking documentation files...
✓ CHANGELOG (latest): 5.3.4
✓ README (badge): 5.3.4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Verification Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Expected:    5.3.4
Checks:      4
Passed:      4
Failed:      0

✅ All versions are consistent!
```

## 🔄 Version Update Workflow

### Step 1: Update VERSION File
```bash
# Update version number in VERSION file
echo "5.3.4" > VERSION
```

### Step 2: Sync to All Files
```bash
# Run synchronization script
./scripts/sync_version.sh
```

### Step 3: Verify Consistency
```bash
# Verify all files are consistent
./scripts/verify_version_consistency.sh
```

### Step 4: Update CHANGELOG
```bash
# Add new version entry to CHANGELOG.md
# The [X.Y.Z] header will be automatically synced
```

### Step 5: Commit Changes
```bash
# Git hook will verify consistency before commit
git add VERSION .workflow/manifest.yml .claude/settings.json CHANGELOG.md README.md
git commit -m "chore: bump version to 5.3.4"
```

## 🚫 Git Hook Integration

### Pre-commit Hook Enhancement

The pre-commit hook automatically verifies version consistency:

```bash
# In .git/hooks/pre-commit

# ====================================
# Version Consistency Check
# ====================================
if [[ -f "./scripts/verify_version_consistency.sh" ]]; then
    echo "🔍 Checking version consistency..."

    if ! ./scripts/verify_version_consistency.sh; then
        echo ""
        echo "❌ Version inconsistency detected!"
        echo ""
        echo "Fix command:"
        echo "  ./scripts/sync_version.sh"
        echo ""
        echo "Or force commit (not recommended):"
        echo "  git commit --no-verify"
        exit 1
    fi

    echo "✅ Version consistency verified"
fi
```

### Behavior
- **Blocking**: Commit is blocked if versions are inconsistent
- **Fix Command**: Provides exact command to fix (`sync_version.sh`)
- **Bypass**: Can use `--no-verify` to skip (not recommended)
- **Zero False Positives**: Only blocks on real inconsistencies

## 📋 Semantic Versioning Rules

Claude Enhancer follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     └─ Patch: Bug fixes, no API changes
  |     └─────── Minor: New features, backward compatible
  └───────────── Major: Breaking changes
```

### Version Increment Guidelines

#### Patch Version (X.Y.Z → X.Y.Z+1)
- Bug fixes
- Performance improvements
- Documentation updates
- Typo corrections
- Internal refactoring (no API changes)

**Example**: `5.3.3 → 5.3.4`
- Fixed version inconsistency bug
- Updated documentation
- No breaking changes

#### Minor Version (X.Y.Z → X.Y+1.0)
- New features (backward compatible)
- New capabilities
- New Phase additions
- New Agent types
- Deprecations (with warnings)

**Example**: `5.3.4 → 5.4.0`
- Added new P8 Phase
- New agent types
- Enhanced workflow features

#### Major Version (X.Y.Z → X+1.0.0)
- Breaking changes
- Removed deprecated features
- API changes requiring code updates
- Architecture redesign
- Incompatible workflow changes

**Example**: `5.3.4 → 6.0.0`
- Changed workflow structure
- Removed old APIs
- Requires migration

## 🔍 Troubleshooting

### Problem: Version Mismatch After Manual Edit

**Symptoms**:
```
❌ Workflow Manifest: expected 5.3.4, got 5.3.3
```

**Solution**:
```bash
# Run sync script to fix
./scripts/sync_version.sh

# Verify fix
./scripts/verify_version_consistency.sh
```

### Problem: Commit Blocked by Hook

**Symptoms**:
```
❌ Version inconsistency detected!
Fix command: ./scripts/sync_version.sh
```

**Solution**:
```bash
# Fix version inconsistency
./scripts/sync_version.sh

# Retry commit
git commit -m "your message"
```

**NOT Recommended**:
```bash
# Bypassing hook (dangerous!)
git commit --no-verify -m "your message"
```

### Problem: Missing VERSION File

**Symptoms**:
```
❌ VERSION file not found: /path/to/VERSION
```

**Solution**:
```bash
# Create VERSION file with current version
echo "5.3.4" > VERSION

# Sync to all files
./scripts/sync_version.sh
```

### Problem: Invalid Version Format

**Symptoms**:
```
❌ Invalid version format: 5.3.4-alpha
Expected format: X.Y.Z (e.g., 5.3.4)
```

**Solution**:
```bash
# Use semantic versioning (X.Y.Z)
echo "5.3.4" > VERSION

# For pre-release, use Git tags instead
git tag -a v5.3.4-alpha -m "Alpha release"
```

## 📊 Version Consistency Report

Run the following to generate a comprehensive version report:

```bash
# Generate report
{
    echo "=== VERSION CONSISTENCY REPORT ==="
    echo "Generated: $(date)"
    echo ""
    echo "Source Version: $(cat VERSION)"
    echo ""
    echo "File Versions:"

    echo -n "  manifest.yml:  "
    yq eval '.version' .workflow/manifest.yml 2>/dev/null || echo "N/A"

    echo -n "  settings.json: "
    jq -r '.version' .claude/settings.json 2>/dev/null || echo "N/A"

    echo -n "  CHANGELOG.md:  "
    grep -m 1 "^## \[" CHANGELOG.md | sed 's/.*\[\(.*\)\].*/\1/' || echo "N/A"

    echo -n "  README.md:     "
    grep -o "version-[0-9.]*-blue" README.md | head -1 | sed 's/version-\(.*\)-blue/\1/' || echo "N/A"

    echo ""
    ./scripts/verify_version_consistency.sh
} > version_report.txt

cat version_report.txt
```

## 🎯 Best Practices

### DO ✅

1. **Always update VERSION file first**
   ```bash
   echo "5.3.5" > VERSION
   ./scripts/sync_version.sh
   ```

2. **Run verification before commit**
   ```bash
   ./scripts/verify_version_consistency.sh
   git commit -m "chore: version bump"
   ```

3. **Use semantic versioning**
   ```
   5.3.4 → 5.3.5 (patch)
   5.3.5 → 5.4.0 (minor)
   5.4.0 → 6.0.0 (major)
   ```

4. **Document version changes in CHANGELOG**
   ```markdown
   ## [5.3.4] - 2025-10-09
   ### Fixed
   - Version inconsistency across files
   ```

### DON'T ❌

1. **Don't manually edit version in individual files**
   ```bash
   # ❌ Wrong
   vim .workflow/manifest.yml  # manually change version

   # ✅ Correct
   echo "5.3.4" > VERSION && ./scripts/sync_version.sh
   ```

2. **Don't commit with inconsistent versions**
   ```bash
   # ❌ Wrong
   git commit --no-verify  # bypassing hook

   # ✅ Correct
   ./scripts/sync_version.sh
   git commit
   ```

3. **Don't use non-semver formats**
   ```bash
   # ❌ Wrong
   echo "v5.3.4" > VERSION        # has 'v' prefix
   echo "5.3.4-alpha" > VERSION   # has pre-release tag

   # ✅ Correct
   echo "5.3.4" > VERSION         # clean semver
   git tag v5.3.4-alpha           # pre-release in Git tag
   ```

4. **Don't skip verification**
   ```bash
   # ❌ Wrong
   ./scripts/sync_version.sh  # assume it worked
   git commit

   # ✅ Correct
   ./scripts/sync_version.sh
   ./scripts/verify_version_consistency.sh  # verify!
   git commit
   ```

## 📚 Additional Resources

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [Claude Enhancer Workflow Guide](.claude/WORKFLOW.md)

## 🔄 Migration from Previous Versions

If you're upgrading from a version without centralized version management:

### Step 1: Determine Current Version
```bash
# Check all files and find the most recent version
grep -r "version" .workflow/manifest.yml .claude/settings.json CHANGELOG.md README.md | sort
```

### Step 2: Create VERSION File
```bash
# Use the highest version found
echo "5.3.4" > VERSION
```

### Step 3: Sync All Files
```bash
./scripts/sync_version.sh
```

### Step 4: Verify and Commit
```bash
./scripts/verify_version_consistency.sh
git add VERSION .workflow/manifest.yml .claude/settings.json
git commit -m "chore: establish VERSION as single source of truth"
```

## 🎓 Understanding the System

### Why Single Source of Truth?

**Problem Without It**:
```
manifest.yml:  version: "1.0.0"
settings.json: "version": "5.1.0"
CHANGELOG.md:  ## [5.3.3]
README.md:     version-5.1.1-blue
```
→ 4 different versions! Which is correct?

**Solution With VERSION File**:
```
VERSION:       5.3.4  ← Single source
↓ sync_version.sh
├→ manifest.yml:  5.3.4
├→ settings.json: 5.3.4
├→ CHANGELOG.md:  5.3.4
└→ README.md:     5.3.4
```
→ One version, automatically synced everywhere!

### How It Works

```
Developer          Scripts              Files
────────          ──────              ─────

Edit VERSION  →  sync_version.sh  →  manifest.yml
   5.3.4                                settings.json
                                       CHANGELOG.md
                                       README.md
                    ↓
              verify_version_consistency.sh
                    ↓
              pre-commit hook
                    ↓
              ✅ or ❌ commit
```

## 📝 Summary

- **VERSION file** is the single source of truth
- **sync_version.sh** synchronizes version to all files
- **verify_version_consistency.sh** verifies consistency
- **pre-commit hook** enforces consistency before commit
- **Semantic versioning** (X.Y.Z) is required
- **Never manually edit** version in individual files
- **Always verify** before committing

---

*Last Updated: 2025-10-09 (v5.3.4)*
*Maintained by: Claude Enhancer Team*
