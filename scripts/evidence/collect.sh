#!/usr/bin/env bash
# Evidence Collection Script (v1.1 - ChatGPT Reviewed & Patched)
# Collects evidence for acceptance checklist items
#
# Fixes Applied:
# - P0-1: ISO week format (%GW%V instead of %YW%U)
# - P0-1: Correct sequence search (within week directory)
# - P0-2: Python environment properly exported
# - P0-2: Timestamp generated in Python (not shell variable)
# - P0-5: ISO week format unified across system
# - P1-8: Cross-platform sha256 support (macOS + Linux)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Usage
usage() {
  cat << EOF
Usage: bash scripts/evidence/collect.sh \\
  --type <test_result|code_review|command_output|artifact> \\
  --checklist-item <1.1> \\
  --description "Description of evidence" \\
  --file <path/to/file> OR --command "command to run"

Options:
  --type              Type of evidence (required)
  --checklist-item    Checklist item number like 1.1 (required)
  --description       Human-readable description (required)
  --file              Path to file artifact (optional)
  --command           Command to execute (optional)

Example:
  bash scripts/evidence/collect.sh \\
    --type test_result \\
    --checklist-item 1.1 \\
    --description "Unit tests for Learning System" \\
    --command "pytest tests/test_learning.py -v"

  bash scripts/evidence/collect.sh \\
    --type code_review \\
    --checklist-item 2.3 \\
    --description "Manual code review notes" \\
    --file docs/review_notes.md
EOF
  exit 1
}

# Cross-platform sha256 function (P1-8 fix)
sha256_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    echo -e "${RED}ERROR: Neither sha256sum nor shasum available${NC}" >&2
    echo "Please install one of: coreutils (sha256sum) or perl (shasum)" >&2
    return 1
  fi
}

# Parse arguments
TYPE=""
CHECKLIST_ITEM=""
DESCRIPTION=""
FILE_PATH=""
COMMAND=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --type) TYPE="$2"; shift 2 ;;
    --checklist-item) CHECKLIST_ITEM="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    --file) FILE_PATH="$2"; shift 2 ;;
    --command) COMMAND="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; usage ;;
  esac
done

# Validate required parameters
if [[ -z "$TYPE" || -z "$CHECKLIST_ITEM" || -z "$DESCRIPTION" ]]; then
  echo -e "${RED}Error: Missing required parameters${NC}"
  usage
fi

# Validate type
if [[ ! "$TYPE" =~ ^(test_result|code_review|command_output|artifact)$ ]]; then
  echo -e "${RED}Error: Invalid type '$TYPE'${NC}"
  echo "Must be one of: test_result, code_review, command_output, artifact"
  exit 1
fi

# Validate checklist item format
if [[ ! "$CHECKLIST_ITEM" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo -e "${RED}Error: Invalid checklist item format '$CHECKLIST_ITEM'${NC}"
  echo "Must be in format: X.Y (e.g., 1.1, 2.3)"
  exit 1
fi

if [[ -z "$FILE_PATH" && -z "$COMMAND" ]]; then
  echo -e "${RED}Error: Must provide either --file or --command${NC}"
  usage
fi

# Detect CE_HOME
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

EVIDENCE_DIR="$CE_HOME/.evidence"
mkdir -p "$EVIDENCE_DIR"

# Generate Evidence ID using ISO week format (P0-1, P0-5 fix)
# Format: EVID-2025W44-NNN (ISO week, not US week)
YEAR_WEEK="$(date -u +%GW%V)"
EVIDENCE_WEEK_DIR="$EVIDENCE_DIR/$YEAR_WEEK"
mkdir -p "$EVIDENCE_WEEK_DIR"

# Find latest sequence number WITHIN the week directory (P0-1 fix)
# Previously searched in wrong directory, always returned 001
LATEST_SEQ=$(ls "$EVIDENCE_WEEK_DIR"/EVID-"$YEAR_WEEK"-*.yml 2>/dev/null \
  | sed -E 's/.*-([0-9]{3})\.yml/\1/' | sort -n | tail -1)
LATEST_SEQ=${LATEST_SEQ:-0}

# Safely handle leading zeros (avoid octal interpretation)
NEW_SEQ=$(printf "%03d" $((10#$LATEST_SEQ + 1)))

EVIDENCE_ID="EVID-$YEAR_WEEK-$NEW_SEQ"
EVIDENCE_FILE="$EVIDENCE_WEEK_DIR/$EVIDENCE_ID.yml"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Evidence Collection - Anti-Hollow Gate                  ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Collecting Evidence: $EVIDENCE_ID${NC}"
echo -e "  Type: $TYPE"
echo -e "  Checklist Item: $CHECKLIST_ITEM"
echo -e "  Description: $DESCRIPTION"
echo ""

# Collect artifacts
ARTIFACTS_DIR="$EVIDENCE_WEEK_DIR/artifacts"
mkdir -p "$ARTIFACTS_DIR"

ARTIFACT_INFO=""

# Handle file artifact
if [[ -n "$FILE_PATH" ]]; then
  if [[ ! -f "$FILE_PATH" ]]; then
    echo -e "${RED}Error: File not found: $FILE_PATH${NC}"
    exit 1
  fi

  echo -e "  📄 Collecting file artifact: $FILE_PATH"

  # Calculate hash (cross-platform)
  FILE_HASH=$(sha256_file "$FILE_PATH")
  ARTIFACT_NAME="$(basename "$FILE_PATH")_${NEW_SEQ}"
  cp "$FILE_PATH" "$ARTIFACTS_DIR/$ARTIFACT_NAME"

  ARTIFACT_INFO="
  files:
    - path: $FILE_PATH
      hash: $FILE_HASH
      stored_as: artifacts/$ARTIFACT_NAME"

  echo -e "  ✅ File stored: artifacts/$ARTIFACT_NAME"
  echo -e "  🔒 SHA256: $FILE_HASH"
fi

# Handle command artifact
if [[ -n "$COMMAND" ]]; then
  echo -e "  🔧 Executing command: $COMMAND"

  OUTPUT_FILE="$ARTIFACTS_DIR/command_output_${NEW_SEQ}.log"
  echo "$ $COMMAND" > "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"

  if eval "$COMMAND" >> "$OUTPUT_FILE" 2>&1; then
    EXIT_CODE=0
    echo -e "  ✅ Command succeeded (exit code: 0)"
  else
    EXIT_CODE=$?
    echo -e "  ⚠️  Command failed (exit code: $EXIT_CODE)"
  fi

  ARTIFACT_INFO="
  commands:
    - command: $COMMAND
      exit_code: $EXIT_CODE
      output: artifacts/command_output_${NEW_SEQ}.log"

  echo -e "  📝 Output stored: artifacts/command_output_${NEW_SEQ}.log"
fi

# Get Git context
echo ""
echo -e "  🔍 Collecting Git context..."
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_DIFF_STAT=$(git diff --stat 2>/dev/null | tail -1 || echo "no changes")

echo -e "  📍 Branch: $GIT_BRANCH"
echo -e "  📍 Commit: ${GIT_COMMIT:0:7}"

# Write evidence file
cat > "$EVIDENCE_FILE" << EOF
---
id: "$EVIDENCE_ID"
type: "$TYPE"
checklist_item: "$CHECKLIST_ITEM"
description: "$DESCRIPTION"
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

artifacts:$ARTIFACT_INFO

git_context:
  commit: "$GIT_COMMIT"
  branch: "$GIT_BRANCH"
  diff_stat: "$GIT_DIFF_STAT"

retention_days: 90
EOF

echo ""
echo -e "${GREEN}✅ Evidence collected successfully${NC}"
echo -e "   Evidence ID: ${CYAN}$EVIDENCE_ID${NC}"
echo -e "   File: $EVIDENCE_FILE"
echo ""

# Update index (P0-2 fix: proper environment export + Python timestamp)
export EVIDENCE_DIR EVIDENCE_ID TYPE CHECKLIST_ITEM EVIDENCE_FILE
python3 - << 'PYEOF'
import json
import os
from pathlib import Path
from datetime import datetime

evidence_dir = Path(os.environ['EVIDENCE_DIR'])
index_file = evidence_dir / 'index.json'

# Generate timestamp in Python (not from shell variable) - P0-2 fix
ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

# Load existing index
index = {"evidence": []}
if index_file.exists():
    try:
        with open(index_file, 'r') as f:
            index = json.load(f)
    except Exception as e:
        print(f"Warning: Could not read index, starting fresh: {e}")
        pass

# Append new entry
entry = {
    "id": os.environ['EVIDENCE_ID'],
    "type": os.environ['TYPE'],
    "checklist_item": os.environ['CHECKLIST_ITEM'],
    "timestamp": ts,
    "file": os.environ['EVIDENCE_FILE']
}
index["evidence"].append(entry)

# Write index (TODO P2: add flock for concurrent safety)
with open(index_file, 'w') as f:
    json.dump(index, indent=2, fp=f)

print(f"✅ Evidence indexed: {entry['id']}")
PYEOF

echo ""
echo -e "${CYAN}Next step: Add evidence reference to checklist:${NC}"
echo -e "${YELLOW}<!-- evidence: $EVIDENCE_ID -->${NC}"
echo ""
echo -e "Example:"
echo -e "  - [x] $CHECKLIST_ITEM Your task description"
echo -e "  <!-- evidence: $EVIDENCE_ID -->"
echo ""
