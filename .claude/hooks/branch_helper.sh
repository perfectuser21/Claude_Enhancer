#!/bin/bash
# Claude Enhancer - Branch Helper (Delegator)
# Version: 5.0 - Unified System
# Updated: 2025-10-25 - Delegates to unified_branch_protector.sh

# Load unified branch protector
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/unified_branch_protector.sh
source "${SCRIPT_DIR}/unified_branch_protector.sh"

# Delegate to unified system
cached_branch_check "branch_helper" "write"
exit $?
