#!/bin/bash

# Fix Claude Enhancer Branding - Remove Claude Enhancer References
# Replace all "Claude Enhancer" with "Claude Enhancer" in documentation files

echo "🔧 Fixing Claude Enhancer branding consistency..."

# Find and replace in .md files
find /home/xx/dev/Claude Enhancer -name "*.md" -type f -exec sed -i 's/Claude Enhancer/Claude Enhancer/g' {} +

# Find and replace in .json files
find /home/xx/dev/Claude Enhancer -name "*.json" -type f -exec sed -i 's/Claude Enhancer/Claude Enhancer/g' {} +

# Find and replace in .sh files (comments only)
find /home/xx/dev/Claude Enhancer -name "*.sh" -type f -exec sed -i 's/# Claude Enhancer/# Claude Enhancer/g' {} +
find /home/xx/dev/Claude Enhancer -name "*.sh" -type f -exec sed -i 's/Claude Enhancer/Claude Enhancer/g' {} +

echo "✅ Branding fix completed"

# Count remaining references
remaining=$(find /home/xx/dev/Claude Enhancer -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" \) -exec grep -l "Claude Enhancer" {} \; 2>/dev/null | wc -l)

echo "📊 Remaining 'Claude Enhancer' references: $remaining files"

if [ "$remaining" -gt 0 ]; then
    echo "📋 Files with remaining references:"
    find /home/xx/dev/Claude Enhancer -type f \( -name "*.md" -o -name "*.json" -o -name "*.sh" \) -exec grep -l "Claude Enhancer" {} \; 2>/dev/null
fi