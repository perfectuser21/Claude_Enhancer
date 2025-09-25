#!/bin/bash
# Claude Enhancer 5.0 - Batch Rename Script
# Updates all references from Perfect21 to Claude Enhancer 5.0

echo "🔄 Starting batch rename to Claude Enhancer 5.0..."

# Update all markdown files
echo "📝 Updating documentation files..."
find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" -type f | while read -r file; do
    if grep -q "Perfect21\|perfect21" "$file" 2>/dev/null; then
        sed -i 's/Perfect21/Claude Enhancer 5.0/g' "$file"
        sed -i 's/perfect21/claude-enhancer/g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

# Update all JavaScript files
echo "🔧 Updating JavaScript files..."
find . -name "*.js" -not -path "./.git/*" -not -path "./node_modules/*" -type f | while read -r file; do
    if grep -q "Perfect21\|perfect21\|Claude Enhancer Plus\|v3.0\|v4.0" "$file" 2>/dev/null; then
        sed -i 's/Perfect21/Claude Enhancer 5.0/g' "$file"
        sed -i 's/perfect21/claude-enhancer/g' "$file"
        sed -i 's/Claude Enhancer Plus/Claude Enhancer 5.0/g' "$file"
        sed -i 's/v3\.0/5.0/g' "$file"
        sed -i 's/v4\.0/5.0/g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

# Update all Python files
echo "🐍 Updating Python files..."
find . -name "*.py" -not -path "./.git/*" -not -path "./node_modules/*" -type f | while read -r file; do
    if grep -q "Perfect21\|perfect21" "$file" 2>/dev/null; then
        sed -i 's/Perfect21/Claude Enhancer 5.0/g' "$file"
        sed -i 's/perfect21/claude-enhancer/g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

# Update all shell scripts
echo "🐚 Updating shell scripts..."
find . -name "*.sh" -not -path "./.git/*" -not -path "./node_modules/*" -not -name "rename_to_claude_enhancer_5.sh" -type f | while read -r file; do
    if grep -q "Perfect21\|perfect21\|v3.0\|v4.0" "$file" 2>/dev/null; then
        sed -i 's/Perfect21/Claude Enhancer 5.0/g' "$file"
        sed -i 's/perfect21/claude-enhancer/g' "$file"
        sed -i 's/v3\.0/5.0/g' "$file"
        sed -i 's/v4\.0/5.0/g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

# Update JSON files
echo "📦 Updating JSON configuration files..."
find . -name "*.json" -not -path "./.git/*" -not -path "./node_modules/*" -type f | while read -r file; do
    if grep -q "Perfect21\|perfect21" "$file" 2>/dev/null; then
        sed -i 's/"Perfect21"/"Claude Enhancer 5.0"/g' "$file"
        sed -i 's/"perfect21"/"claude-enhancer"/g' "$file"
        sed -i 's/perfect21\//claude-enhancer\//g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

# Update YAML files
echo "⚙️ Updating YAML configuration files..."
find . -name "*.yaml" -o -name "*.yml" -not -path "./.git/*" -not -path "./node_modules/*" -type f | while read -r file; do
    if [ -f "$file" ] && grep -q "Perfect21\|perfect21" "$file" 2>/dev/null; then
        sed -i 's/Perfect21/Claude Enhancer 5.0/g' "$file"
        sed -i 's/perfect21/claude-enhancer/g' "$file"
        echo "  ✓ Updated: $file"
    fi
done

echo ""
echo "✅ Batch rename completed!"
echo ""
echo "📊 Summary of changes:"
echo "  - All 'Perfect21' → 'Claude Enhancer 5.0'"
echo "  - All 'perfect21' → 'claude-enhancer'"
echo "  - All 'v3.0/v4.0' → '5.0'"
echo "  - All 'Claude Enhancer Plus' → 'Claude Enhancer 5.0'"
echo ""
echo "💡 Next steps:"
echo "  1. Review changes with: git diff"
echo "  2. Stage changes with: git add -A"
echo "  3. Commit with: git commit -m \"refactor: standardize naming to Claude Enhancer 5.0\""