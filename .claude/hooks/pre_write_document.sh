#!/bin/bash
# Pre-Write Document Hook: Block unauthorized document creation
# Prevents documentation chaos by enforcing strict file creation rules

validate_document_creation() {
    local file_path="$1"
    local filename
    filename=$(basename "$file_path")
    local dirname
    dirname=$(dirname "$file_path")

    # Allow non-markdown files
    if [[ "$filename" != *.md ]]; then
        return 0
    fi

    # Normalize path
    if [[ "$dirname" == "." ]]; then
        dirname=""
    fi

    # Allow files not in root (subdirectories are OK)
    if [[ -n "$dirname" ]] && [[ "$dirname" != "." ]]; then
        # Special directories with rules
        case "$dirname" in
            .temp*|temp*)
                return 0  # Allow .temp/ (temporary storage)
                ;;
            evidence*|archive*)
                return 0  # Allow evidence/ and archive/
                ;;
            docs*)
                return 0  # Allow docs/ (structured documentation)
                ;;
            *)
                return 0  # Allow other subdirectories
                ;;
        esac
    fi

    # Core document whitelist (only these allowed in root)
    case "$filename" in
        README.md|CLAUDE.md|INSTALLATION.md|ARCHITECTURE.md|CONTRIBUTING.md|CHANGELOG.md|LICENSE.md|PLAN.md)
            return 0  # Authorized core documents
            ;;
    esac

    # Block with helpful message
    cat <<'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ DOCUMENT CREATION BLOCKED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: %FILE_PATH%
Reason: Not in core documentation whitelist

✅ ALLOWED Actions:
  • Update core documents (8 files):
    - README.md, CLAUDE.md, PLAN.md
    - INSTALLATION.md, ARCHITECTURE.md, CONTRIBUTING.md
    - CHANGELOG.md, LICENSE.md

  • Write to approved directories:
    - .temp/          → Temporary analysis (no approval needed)
    - evidence/       → Work evidence and logs
    - docs/           → Structured permanent documentation
    - archive/        → Historical archives

❌ FORBIDDEN Actions:
  • Create new root .md files
  • Create *_REPORT.md in root
  • Create *_ANALYSIS.md in root

💡 Recommended Solutions:

  1. Temporary Analysis:
     → .temp/analysis/${filename}

  2. Work Evidence:
     → evidence/${filename}

  3. Permanent Documentation:
     → ASK USER FIRST, then docs/

  4. Development Reports:
     → .temp/reports/${filename}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Document Lifecycle Policy:

  .temp/      → 7 days TTL (auto-cleanup)
  evidence/   → 30 days TTL (auto-archive)
  docs/       → Permanent (version controlled)
  root/       → 8 core docs only (strictly enforced)

Run: scripts/cleanup_documents.sh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

    # Replace placeholder with actual file path
    sed -i.bak "s|%FILE_PATH%|$file_path|g" /dev/stderr 2>/dev/null || true

    return 1
}

# Execute validation
validate_document_creation "$@"
