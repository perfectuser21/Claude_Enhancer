#!/bin/bash
# Auto Maintenance Script - 自动维护系统
# Purpose: 定期执行质量守护和清理任务
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly LOG_FILE="${PROJECT_ROOT}/.workflow/logs/maintenance.log"
readonly TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log function
log() {
    echo "[$TIMESTAMP] $*" | tee -a "$LOG_FILE"
}

# ═══════════════════════════════════════════════════════════════
# Daily Maintenance Tasks
# ═══════════════════════════════════════════════════════════════

daily_maintenance() {
    log "═══════════════════════════════════════════════════════════════"
    log "Starting Daily Maintenance"
    log "═══════════════════════════════════════════════════════════════"

    # 1. Run Quality Guardian
    log "Running Quality Guardian..."
    if bash "${PROJECT_ROOT}/.claude/tools/quality_guardian.sh" >> "$LOG_FILE" 2>&1; then
        log "✅ Quality Guardian completed"
    else
        log "⚠️ Quality Guardian reported issues"
    fi

    # 2. Clean old versions
    log "Cleaning old versions..."
    if bash "${PROJECT_ROOT}/.claude/tools/version_cleaner.sh" clean false >> "$LOG_FILE" 2>&1; then
        log "✅ Version cleanup completed"
    else
        log "⚠️ Version cleanup had issues"
    fi

    # 3. Clean temp files older than 7 days
    log "Cleaning old temp files..."
    find "${PROJECT_ROOT}/.temp" -type f -mtime +7 -delete 2>/dev/null || true
    log "✅ Temp cleanup completed"

    # 4. Clean old logs (keep 30 days)
    log "Rotating logs..."
    find "${PROJECT_ROOT}/.workflow/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    log "✅ Log rotation completed"

    # 5. Check for oversized scripts
    log "Checking for oversized scripts..."
    oversized_count=$(find "${PROJECT_ROOT}" -name "*.sh" -type f -exec wc -l {} \; | awk '$1 > 300' | wc -l)
    if [[ $oversized_count -gt 0 ]]; then
        log "⚠️ Found $oversized_count oversized scripts (>300 lines)"
        log "   Run: bash ${PROJECT_ROOT}/.claude/tools/quality_guardian.sh"
    else
        log "✅ No oversized scripts"
    fi

    # 6. Establish performance baseline (if monitor exists)
    if [[ -f "${PROJECT_ROOT}/.claude/tools/performance_monitor.sh" ]]; then
        log "Updating performance baseline..."
        bash "${PROJECT_ROOT}/.claude/tools/performance_monitor.sh" baseline >> "$LOG_FILE" 2>&1 || true
        log "✅ Performance baseline updated"
    fi

    log "═══════════════════════════════════════════════════════════════"
    log "Daily Maintenance Completed"
    log "═══════════════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════════════
# Weekly Maintenance Tasks
# ═══════════════════════════════════════════════════════════════

weekly_maintenance() {
    log "═══════════════════════════════════════════════════════════════"
    log "Starting Weekly Maintenance"
    log "═══════════════════════════════════════════════════════════════"

    # 1. Deep analysis
    log "Running deep quality analysis..."
    bash "${PROJECT_ROOT}/.claude/tools/quality_guardian.sh" --fix >> "$LOG_FILE" 2>&1 || true

    # 2. Archive old artifacts
    log "Archiving old artifacts..."
    if [[ -d "${PROJECT_ROOT}/.archive" ]]; then
        find "${PROJECT_ROOT}/.archive" -type f -mtime +90 -delete 2>/dev/null || true
    fi

    # 3. Shellcheck all scripts
    log "Running shellcheck on all scripts..."
    if command -v shellcheck >/dev/null 2>&1; then
        shellcheck_warnings=$(find "${PROJECT_ROOT}" -name "*.sh" -type f -exec shellcheck {} \; 2>&1 | grep "^In" | wc -l || echo 0)
        log "Shellcheck warnings: $shellcheck_warnings"
    fi

    log "═══════════════════════════════════════════════════════════════"
    log "Weekly Maintenance Completed"
    log "═══════════════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════════════
# Setup Cron Job
# ═══════════════════════════════════════════════════════════════

setup_cron() {
    local cron_entry="0 2 * * * cd $PROJECT_ROOT && bash scripts/auto_maintenance.sh daily"
    local weekly_entry="0 3 * * 0 cd $PROJECT_ROOT && bash scripts/auto_maintenance.sh weekly"

    # Check if cron entries exist
    if crontab -l 2>/dev/null | grep -q "auto_maintenance.sh"; then
        echo "Cron jobs already configured"
    else
        echo "Setting up cron jobs..."
        (crontab -l 2>/dev/null || true; echo "$cron_entry") | crontab -
        (crontab -l 2>/dev/null || true; echo "$weekly_entry") | crontab -
        echo "✅ Cron jobs configured:"
        echo "   Daily: 2 AM"
        echo "   Weekly: Sunday 3 AM"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════

main() {
    local command="${1:-help}"

    case "$command" in
        daily)
            daily_maintenance
            ;;
        weekly)
            weekly_maintenance
            ;;
        setup)
            setup_cron
            ;;
        help|*)
            cat <<EOF
Auto Maintenance System

Usage: $(basename "$0") [command]

Commands:
  daily    Run daily maintenance tasks
  weekly   Run weekly maintenance tasks
  setup    Setup cron jobs for automatic execution

Daily Tasks (2 AM):
  • Quality Guardian check
  • Version cleanup
  • Temp file cleanup
  • Log rotation
  • Script size check
  • Performance baseline

Weekly Tasks (Sunday 3 AM):
  • Deep quality analysis
  • Archive cleanup
  • Full shellcheck scan

Setup:
  $(basename "$0") setup

Manual Run:
  $(basename "$0") daily
  $(basename "$0") weekly
EOF
            ;;
    esac
}

# Execute main
main "$@"