# Lock System

This directory contains the **file integrity protection system** for core/ files.

## Purpose

Prevents accidental modification of core files by:
1. Maintaining SHA256 hash manifest
2. Validating file integrity on pre-commit
3. Requiring explicit approval for core changes

## Files

```
.locked/
├── manifest.json        # File inventory with SHA256 hashes
├── validator.sh         # Validation script (git hook integration)
└── README.md           # This file
```

## How It Works

### 1. Manifest Generation
```bash
./scripts/generate-lock-manifest.sh
```

This creates `manifest.json`:
```json
{
  "locked_files": [
    {
      "path": "core/workflow/engine.py",
      "sha256": "abc123...",
      "reason": "Core workflow engine",
      "locked_at": "2025-10-14T10:00:00Z"
    }
  ],
  "version": "2.0.0"
}
```

### 2. Pre-Commit Validation

When you try to commit changes to core/ files:

```bash
git add core/workflow/engine.py
git commit -m "Modify core file"

# Hook runs:
❌ Core file modified: core/workflow/engine.py
Expected: abc123...
Actual:   def456...

⚠️  This file is LOCKED. To modify:
1. Get approval (explain why change is needed)
2. Update lock manifest: ./scripts/generate-lock-manifest.sh
3. Commit with both changes
```

### 3. Bypass for Authorized Changes

If you have approval to modify core:

```bash
# 1. Make your changes
vim core/workflow/engine.py

# 2. Regenerate manifest
./scripts/generate-lock-manifest.sh

# 3. Commit both
git add core/workflow/engine.py .locked/manifest.json
git commit -m "fix(core): Update workflow engine

Reason: Fix critical bug in phase transition
Approved-By: User
SHA256-Update: Required"
```

## Protected Directories

- `core/workflow/` - Workflow engine (highest protection)
- `core/hooks/` - Hook system
- `core/agents/` - Agent selector
- `core/config/` - Configuration loader
- `core/api/` - Core APIs

## Security Guarantees

- **SHA256 collision resistance**: Cryptographically secure
- **Git hook enforcement**: Runs automatically on commit
- **Tamper detection**: Any byte change detected
- **Audit trail**: manifest.json tracks all changes

## Version: 2.0.0
