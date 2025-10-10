#!/bin/bash
# Enforce bash strict mode (set -euo pipefail) across all shell scripts
# Trust-but-Verify: Scan all .sh files for strict mode compliance

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Scanning all shell scripts for strict mode compliance..."
echo "Required: set -euo pipefail"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

fails=0
total=0

while IFS= read -r script_file; do
    ((total++))

    # Check if file has strict mode in first 10 lines
    if ! head -n10 "$script_file" | grep -q "set -euo pipefail"; then
        echo "❌ $script_file - MISSING strict mode"
        ((fails++))
    else
        echo "✅ $script_file"
    fi
done < <(git ls-files '*.sh' 2>/dev/null || find . -name "*.sh" -not -path "./.git/*")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total scripts: $total"
echo "Compliant: $((total - fails))"
echo "Non-compliant: $fails"

if [ $fails -gt 0 ]; then
    echo ""
    echo "❌ Strict mode enforcement FAILED"
    echo "🔧 To auto-fix, run: ./scripts/fix_bash_strict_mode.sh"
    exit 1
else
    echo ""
    echo "✅ All scripts are compliant with strict mode"
    exit 0
fi
