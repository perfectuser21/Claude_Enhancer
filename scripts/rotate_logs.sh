#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Log Rotation Script for Claude Enhancer
# ═══════════════════════════════════════════════════════════════
#
# Purpose: Rotate and compress old log files to prevent disk bloat
# Schedule: Run daily via cron or manually
#
# Configuration:
#   MAX_SIZE_MB: Maximum log file size before rotation (default: 10MB)
#   MAX_AGE_DAYS: Maximum age of uncompressed logs (default: 30 days)
#   ARCHIVE_DAYS: Days to keep compressed archives (default: 90 days)
#
# Usage:
#   bash scripts/rotate_logs.sh           # Default settings
#   MAX_SIZE_MB=20 bash scripts/rotate_logs.sh  # Custom size
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration (can be overridden by environment variables)
MAX_SIZE_MB="${MAX_SIZE_MB:-10}"
MAX_AGE_DAYS="${MAX_AGE_DAYS:-30}"
ARCHIVE_DAYS="${ARCHIVE_DAYS:-90}"

# Convert MB to bytes
MAX_SIZE_BYTES=$((MAX_SIZE_MB * 1024 * 1024))

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOG_DIR="$PROJECT_ROOT/.workflow/logs"
ARCHIVE_DIR="$LOG_DIR/archive"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Log Rotation for Claude Enhancer           ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$ARCHIVE_DIR"

echo -e "${CYAN}📋 Configuration:${NC}"
echo "   Log directory: $LOG_DIR"
echo "   Archive directory: $ARCHIVE_DIR"
echo "   Max file size: ${MAX_SIZE_MB}MB"
echo "   Max age (uncompressed): ${MAX_AGE_DAYS} days"
echo "   Archive retention: ${ARCHIVE_DAYS} days"
echo ""

# ═══════════════════════════════════════════════════════════════
# Step 1: Rotate large log files
# ═══════════════════════════════════════════════════════════════

echo -e "${CYAN}🔄 Step 1: Checking for large log files...${NC}"

ROTATED_COUNT=0

if [ -d "$LOG_DIR" ]; then
    while IFS= read -r log_file; do
        [ -z "$log_file" ] && continue
        [ ! -f "$log_file" ] && continue

        # Get file size
        if [[ "$OSTYPE" == "darwin"* ]]; then
            file_size=$(stat -f%z "$log_file" 2>/dev/null || echo "0")
        else
            file_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
        fi

        # Check if file exceeds size limit
        if [ "$file_size" -gt "$MAX_SIZE_BYTES" ]; then
            size_mb=$((file_size / 1024 / 1024))
            echo -e "   ${YELLOW}⚠️  Large file: $(basename "$log_file") (${size_mb}MB)${NC}"

            # Generate timestamp
            timestamp=$(date +%Y%m%d_%H%M%S)
            archive_name="${log_file%.log}_${timestamp}.log"

            # Move to archive directory
            mv "$log_file" "$archive_name"

            # Compress
            gzip "$archive_name"

            # Move compressed file to archive
            mv "${archive_name}.gz" "$ARCHIVE_DIR/"

            echo -e "   ${GREEN}✓ Rotated and compressed: $(basename "$archive_name").gz${NC}"
            ((ROTATED_COUNT++))

            # Create new empty log file
            touch "$log_file"
        fi
    done < <(find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f)
fi

if [ $ROTATED_COUNT -eq 0 ]; then
    echo -e "   ${GREEN}✓ No large files to rotate${NC}"
else
    echo -e "   ${GREEN}✓ Rotated $ROTATED_COUNT file(s)${NC}"
fi

# ═══════════════════════════════════════════════════════════════
# Step 2: Compress old uncompressed logs
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}🗜️  Step 2: Compressing old log files...${NC}"

COMPRESSED_COUNT=0

if [ -d "$LOG_DIR" ]; then
    # Find logs older than MAX_AGE_DAYS
    while IFS= read -r log_file; do
        [ -z "$log_file" ] && continue
        [ ! -f "$log_file" ] && continue

        # Skip active log files (hooks.log, etc.)
        if [[ "$(basename "$log_file")" =~ ^(hooks|permissions|quality|git)\.log$ ]]; then
            continue
        fi

        # Get file modification time
        if [[ "$OSTYPE" == "darwin"* ]]; then
            file_mtime=$(stat -f%m "$log_file" 2>/dev/null || echo "0")
        else
            file_mtime=$(stat -c%Y "$log_file" 2>/dev/null || echo "0")
        fi

        current_time=$(date +%s)
        file_age_days=$(( (current_time - file_mtime) / 86400 ))

        # Compress if older than MAX_AGE_DAYS
        if [ "$file_age_days" -gt "$MAX_AGE_DAYS" ]; then
            echo -e "   ${YELLOW}⚠️  Old file: $(basename "$log_file") (${file_age_days} days old)${NC}"

            # Compress in place
            gzip "$log_file"

            # Move to archive
            mv "${log_file}.gz" "$ARCHIVE_DIR/"

            echo -e "   ${GREEN}✓ Compressed and archived: $(basename "$log_file").gz${NC}"
            ((COMPRESSED_COUNT++))
        fi
    done < <(find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f -mtime "+$MAX_AGE_DAYS")
fi

if [ $COMPRESSED_COUNT -eq 0 ]; then
    echo -e "   ${GREEN}✓ No old files to compress${NC}"
else
    echo -e "   ${GREEN}✓ Compressed $COMPRESSED_COUNT file(s)${NC}"
fi

# ═══════════════════════════════════════════════════════════════
# Step 3: Delete very old archives
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}🗑️  Step 3: Cleaning up old archives...${NC}"

DELETED_COUNT=0

if [ -d "$ARCHIVE_DIR" ]; then
    while IFS= read -r archive_file; do
        [ -z "$archive_file" ] && continue
        [ ! -f "$archive_file" ] && continue

        # Get file modification time
        if [[ "$OSTYPE" == "darwin"* ]]; then
            file_mtime=$(stat -f%m "$archive_file" 2>/dev/null || echo "0")
        else
            file_mtime=$(stat -c%Y "$archive_file" 2>/dev/null || echo "0")
        fi

        current_time=$(date +%s)
        file_age_days=$(( (current_time - file_mtime) / 86400 ))

        # Delete if older than ARCHIVE_DAYS
        if [ "$file_age_days" -gt "$ARCHIVE_DAYS" ]; then
            echo -e "   ${YELLOW}⚠️  Expired archive: $(basename "$archive_file") (${file_age_days} days old)${NC}"
            rm -f "$archive_file"
            echo -e "   ${GREEN}✓ Deleted: $(basename "$archive_file")${NC}"
            ((DELETED_COUNT++))
        fi
    done < <(find "$ARCHIVE_DIR" -name "*.log.gz" -type f -mtime "+$ARCHIVE_DAYS")
fi

if [ $DELETED_COUNT -eq 0 ]; then
    echo -e "   ${GREEN}✓ No expired archives to delete${NC}"
else
    echo -e "   ${GREEN}✓ Deleted $DELETED_COUNT expired archive(s)${NC}"
fi

# ═══════════════════════════════════════════════════════════════
# Step 4: Generate summary
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}📊 Summary:${NC}"

# Count current log files
CURRENT_LOGS=$(find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f | wc -l)
CURRENT_ARCHIVES=$(find "$ARCHIVE_DIR" -name "*.log.gz" -type f 2>/dev/null | wc -l || echo "0")

# Calculate total disk usage
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | awk '{print $1}')
else
    LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
fi

echo "   Active logs: $CURRENT_LOGS"
echo "   Archived logs: $CURRENT_ARCHIVES"
echo "   Total disk usage: ${LOG_SIZE:-N/A}"
echo ""
echo "   Files rotated: $ROTATED_COUNT"
echo "   Files compressed: $COMPRESSED_COUNT"
echo "   Archives deleted: $DELETED_COUNT"

# ═══════════════════════════════════════════════════════════════
# Completion
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}✅ Log rotation completed successfully${NC}"
echo ""
echo -e "${CYAN}💡 Tip: Add to crontab for automatic rotation:${NC}"
echo "   # Daily log rotation at 2 AM"
echo "   0 2 * * * cd $PROJECT_ROOT && bash scripts/rotate_logs.sh >> .workflow/logs/rotation.log 2>&1"

exit 0
