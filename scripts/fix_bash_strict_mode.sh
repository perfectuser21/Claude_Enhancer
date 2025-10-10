#!/bin/bash
# Auto-fix bash scripts to add strict mode (set -euo pipefail)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔧 Auto-fixing bash scripts to add strict mode..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

fixed=0
skipped=0

while IFS= read -r script_file; do
    # Check if already has strict mode
    if head -n10 "$script_file" | grep -q "set -euo pipefail"; then
        echo "⏩ $script_file - already has strict mode"
        ((skipped++))
        continue
    fi

    # Check if has shebang
    if ! head -n1 "$script_file" | grep -q "^#!/"; then
        echo "⚠️  $script_file - no shebang, skipping"
        ((skipped++))
        continue
    fi

    # Add strict mode after shebang
    echo "🔧 $script_file - adding strict mode"

    # Create temp file
    temp_file=$(mktemp)

    # Copy shebang
    head -n1 "$script_file" > "$temp_file"

    # Add blank line and strict mode
    echo "" >> "$temp_file"
    echo "set -euo pipefail" >> "$temp_file"

    # Copy rest of file (skip first line)
    tail -n +2 "$script_file" >> "$temp_file"

    # Replace original
    mv "$temp_file" "$script_file"
    chmod +x "$script_file"

    ((fixed++))
done < <(git ls-files '*.sh' 2>/dev/null || find . -name "*.sh" -not -path "./.git/*")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fixed: $fixed"
echo "Skipped: $skipped"

if [ $fixed -gt 0 ]; then
    echo ""
    echo "✅ Auto-fix completed"
    echo "🔍 Run ./scripts/enforce_bash_strict_mode.sh to verify"
fi
