#!/bin/bash
# Document Cleanup: Enforce lifecycle management
# Maintains clean project structure with automatic TTL-based cleanup

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Document Cleanup Starting...${NC}\n"

# 1. Clean .temp/ directory (7 days TTL)
echo -e "${YELLOW}🗑️  Cleaning temporary files (7+ days old)...${NC}"
if [ -d ".temp" ]; then
    # Find and delete files older than 7 days
    find .temp -type f -mtime +7 -delete 2>/dev/null || true
    # Remove empty directories
    find .temp -type d -empty -delete 2>/dev/null || true

    temp_count=$(find .temp -type f 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} Temp files remaining: $temp_count"
else
    echo -e "  ${YELLOW}⚠${NC}  .temp directory not found"
fi

# 2. Archive evidence/ directory (30 days TTL)
echo -e "\n${YELLOW}📦 Archiving evidence files (30+ days old)...${NC}"
if [ -d "evidence" ]; then
    archive_month=$(date -d "30 days ago" +%Y-%m 2>/dev/null || date -v-30d +%Y-%m 2>/dev/null || echo "archive")
    archive_dir="archive/$archive_month"
    mkdir -p "$archive_dir"

    # Move old evidence files to archive
    old_files=$(find evidence -type f -mtime +30 2>/dev/null | wc -l)
    if [ "$old_files" -gt 0 ]; then
        find evidence -type f -mtime +30 -exec mv {} "$archive_dir/" \; 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} Archived $old_files files to $archive_dir"
    else
        echo -e "  ${GREEN}✓${NC} No old evidence files to archive"
    fi

    evidence_count=$(find evidence -type f 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} Evidence files remaining: $evidence_count"
else
    echo -e "  ${YELLOW}⚠${NC}  evidence directory not found"
fi

# 3. Check and quarantine unauthorized root documents
echo -e "\n${YELLOW}🔍 Checking root directory documents...${NC}"

# Core documentation whitelist (authorized files)
authorized_docs=(
    "README.md"
    "CLAUDE.md"
    "INSTALLATION.md"
    "ARCHITECTURE.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
    "LICENSE.md"
    "PLAN.md"
)

unauthorized=()

# Check each .md file in root
while IFS= read -r file; do
    filename=$(basename "$file")
    authorized=false

    # Check if file is in whitelist
    for allowed in "${authorized_docs[@]}"; do
        if [[ "$filename" == "$allowed" ]]; then
            authorized=true
            break
        fi
    done

    # Add to unauthorized list if not in whitelist
    if [[ "$authorized" == "false" ]]; then
        unauthorized+=("$file")
    fi
done < <(find . -maxdepth 1 -name "*.md" -type f 2>/dev/null)

# Quarantine unauthorized documents
if [ ${#unauthorized[@]} -gt 0 ]; then
    echo -e "  ${RED}⚠${NC}  Found ${#unauthorized[@]} unauthorized documents:"

    quarantine_dir=".temp/quarantine_$(date +%Y%m%d)"
    mkdir -p "$quarantine_dir"

    for file in "${unauthorized[@]}"; do
        filename=$(basename "$file")
        echo -e "    ${YELLOW}→${NC} Moving: $filename → $quarantine_dir/"
        mv "$file" "$quarantine_dir/"
    done

    echo -e "  ${GREEN}✓${NC} Quarantined to: $quarantine_dir"
else
    echo -e "  ${GREEN}✓${NC} All root documents are authorized"
fi

# 4. Generate cleanup report
echo -e "\n${BLUE}📊 Cleanup Complete${NC}\n"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

core_docs=$(find . -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l)
temp_docs=$(find .temp -name "*.md" 2>/dev/null | wc -l || echo "0")
evidence_docs=$(find evidence -type f 2>/dev/null | wc -l || echo "0")
total_docs=$(find . -name "*.md" -type f 2>/dev/null | wc -l)

echo "Document Statistics:"
echo "  Core documents (root):    $core_docs (target: ≤7)"
echo "  Temporary files (.temp):  $temp_docs"
echo "  Evidence files:           $evidence_docs"
echo "  Total markdown files:     $total_docs"
echo ""

# Health check
if [ "$core_docs" -le 7 ]; then
    echo -e "${GREEN}✅ Document count healthy${NC}"
    exit_code=0
else
    echo -e "${RED}⚠️  Core documents exceed limit (found: $core_docs, limit: 7)${NC}"
    exit_code=1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# List current core documents
if [ "$core_docs" -gt 0 ]; then
    echo -e "\n${BLUE}Current Core Documents:${NC}"
    find . -maxdepth 1 -name "*.md" -type f -exec basename {} \; 2>/dev/null | sort | sed 's/^/  • /'
fi

exit $exit_code
