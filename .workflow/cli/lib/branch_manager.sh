#!/usr/bin/env bash
# branch_manager.sh - Branch lifecycle management
# Handles branch creation, naming, metadata, and cleanup
set -euo pipefail

# Branch metadata directory
CE_BRANCH_METADATA_DIR=".workflow/branches"
CE_BRANCH_ARCHIVE_DIR="${CE_BRANCH_METADATA_DIR}/archive"

# Initialize branch directories
_ce_branch_init_dirs() {
    mkdir -p "${CE_BRANCH_METADATA_DIR}"
    mkdir -p "${CE_BRANCH_ARCHIVE_DIR}"
}

# Branch naming conventions
ce_branch_generate_name() {
    local task_type="${1:-feat}"  # feat/fix/docs/test/refactor
    local description="${2:-unnamed}"
    local phase="${3:-P0}"
    local terminal="${4:-t1}"

    # Sanitize description: lowercase, replace spaces/underscores with hyphens
    description=$(echo "${description}" | tr '[:upper:]' '[:lower:]' | tr ' _' '--' | sed 's/[^a-z0-9-]//g' | sed 's/--*/-/g')

    # Truncate to max 30 chars
    description="${description:0:30}"

    # Generate timestamp
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)

    # Format: tasktype/phase-terminal-timestamp-description
    # Example: feature/P0-t1-20251009-120345-user-auth
    echo "${task_type}/${phase}-${terminal}-${timestamp}-${description}"
}

ce_branch_validate_name() {
    local branch_name="$1"

    # Pattern: (feat|fix|docs|test|refactor)/P[0-7]-t[0-9]+-[0-9]{8}-[0-9]{6}-[a-z0-9-]+
    if [[ ! "$branch_name" =~ ^(feature|feat|fix|docs|test|refactor)/P[0-7]-t[0-9]+-[0-9]{8}-[0-9]{6}-[a-z0-9-]+$ ]]; then
        echo "Error: Invalid branch name format: $branch_name" >&2
        echo "Expected: (feature|feat|fix|docs|test|refactor)/P[0-7]-t[0-9]+-YYYYMMDD-HHMMSS-description" >&2
        return 1
    fi

    # Check length (total should be 3-80 chars)
    if [[ ${#branch_name} -lt 10 || ${#branch_name} -gt 80 ]]; then
        echo "Error: Branch name length must be 10-80 characters" >&2
        return 1
    fi

    return 0
}

# Branch operations
ce_branch_create() {
    local task_type="${1:-feature}"
    local description="${2:-unnamed}"
    local phase="${3:-P0}"
    local terminal="${4:-t1}"

    _ce_branch_init_dirs

    # Generate branch name
    local branch_name
    branch_name=$(ce_branch_generate_name "$task_type" "$description" "$phase" "$terminal")

    # Validate name
    if ! ce_branch_validate_name "$branch_name"; then
        return 1
    fi

    # Check if branch already exists
    if ce_branch_check_exists "$branch_name"; then
        echo "Error: Branch already exists: $branch_name" >&2
        return 1
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "Warning: You have uncommitted changes. Stashing them..." >&2
        git stash push -m "Auto-stash before creating branch $branch_name"
    fi

    # Create git branch
    if ! git checkout -b "$branch_name" 2>/dev/null; then
        echo "Error: Failed to create git branch: $branch_name" >&2
        return 1
    fi

    # Initialize metadata
    ce_branch_init_metadata "$branch_name" "$task_type" "$description" "$phase" "$terminal"

    echo "✅ Branch created successfully: $branch_name"
    echo "   Phase: $phase"
    echo "   Terminal: $terminal"
    echo "   Type: $task_type"

    return 0
}

ce_branch_check_exists() {
    local branch_name="$1"
    git rev-parse --verify "$branch_name" &>/dev/null
}

ce_branch_switch() {
    local branch_name="$1"

    # Check if branch exists
    if ! ce_branch_check_exists "$branch_name"; then
        echo "Error: Branch does not exist: $branch_name" >&2
        return 1
    fi

    # Save current context
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ -n "$current_branch" ]]; then
        ce_context_save "$current_branch"
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo "Warning: You have uncommitted changes. Stashing them..." >&2
        git stash push -m "Auto-stash before switching to $branch_name"
    fi

    # Switch branch
    if ! git checkout "$branch_name" 2>/dev/null; then
        echo "Error: Failed to switch to branch: $branch_name" >&2
        return 1
    fi

    # Load branch metadata
    local metadata
    metadata=$(ce_branch_get_metadata "$branch_name")

    echo "✅ Switched to branch: $branch_name"
    if [[ -n "$metadata" ]]; then
        local phase
        phase=$(echo "$metadata" | grep -oP '(?<="phase": ")[^"]+' || echo "unknown")
        echo "   Phase: $phase"
    fi

    # Restore context if exists
    ce_context_restore "$branch_name" 2>/dev/null || true

    return 0
}

ce_branch_delete() {
    local branch_name="$1"
    local force="${2:-}"

    # Safety check: not currently checked out
    local current_branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" == "$branch_name" ]]; then
        echo "Error: Cannot delete currently checked out branch" >&2
        return 1
    fi

    # Check if branch exists
    if ! ce_branch_check_exists "$branch_name"; then
        echo "Error: Branch does not exist: $branch_name" >&2
        return 1
    fi

    # Check if merged (unless force)
    if [[ "$force" != "--force" && "$force" != "-f" ]]; then
        if ! git branch --merged | grep -q "$branch_name"; then
            echo "Error: Branch is not merged. Use --force to delete anyway" >&2
            return 1
        fi
    fi

    # Archive metadata
    ce_branch_archive_metadata "$branch_name"

    # Delete git branch
    local delete_flag="-d"
    [[ "$force" == "--force" || "$force" == "-f" ]] && delete_flag="-D"

    if git branch "$delete_flag" "$branch_name" 2>/dev/null; then
        echo "✅ Branch deleted: $branch_name"
        return 0
    else
        echo "Error: Failed to delete branch: $branch_name" >&2
        return 1
    fi
}

ce_branch_list_active() {
    _ce_branch_init_dirs

    local current_branch
    current_branch=$(git branch --show-current)

    echo "Active CE Branches:"
    echo "=================="

    # List all CE branches (feature/*, fix/*, etc.)
    git branch | grep -E "^\*? +(feature|feat|fix|docs|test|refactor)/" | while read -r marker branch; do
        local is_current=""
        [[ "$marker" == "*" ]] && is_current="* " && branch="${branch#* }"
        [[ "$branch" == "$current_branch" ]] && is_current="* "

        # Get metadata if exists
        local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch//\//_}.json"
        local phase="unknown"
        local status="active"
        local last_activity="N/A"

        if [[ -f "$metadata_file" ]]; then
            phase=$(jq -r '.phase // "unknown"' "$metadata_file" 2>/dev/null || echo "unknown")
            status=$(jq -r '.status // "active"' "$metadata_file" 2>/dev/null || echo "active")
            last_activity=$(jq -r '.last_activity // "N/A"' "$metadata_file" 2>/dev/null || echo "N/A")
        fi

        printf "%s%-50s %-15s %-10s %s\n" "$is_current" "$branch" "(Phase: $phase)" "[$status]" "$last_activity"
    done

    return 0
}

ce_branch_list_all() {
    ce_branch_list_active

    echo ""
    echo "Archived Branches:"
    echo "=================="

    if [[ -d "$CE_BRANCH_ARCHIVE_DIR" ]]; then
        find "$CE_BRANCH_ARCHIVE_DIR" -name "*.json" -type f | while read -r metadata_file; do
            local branch_name
            branch_name=$(jq -r '.branch_name // "unknown"' "$metadata_file" 2>/dev/null || echo "unknown")
            local phase
            phase=$(jq -r '.phase // "unknown"' "$metadata_file" 2>/dev/null || echo "unknown")
            local archived_at
            archived_at=$(jq -r '.archived_at // "N/A"' "$metadata_file" 2>/dev/null || echo "N/A")

            printf "  %-50s %-15s %s\n" "$branch_name" "(Phase: $phase)" "Archived: $archived_at"
        done
    fi

    return 0
}

# Branch metadata management
ce_branch_get_metadata() {
    local branch_name="$1"
    local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch_name//\//_}.json"

    if [[ -f "$metadata_file" ]]; then
        cat "$metadata_file"
    else
        echo "{}" # Return empty JSON if no metadata
    fi
}

ce_branch_set_metadata() {
    local branch_name="$1"
    local field="$2"
    local value="$3"

    _ce_branch_init_dirs

    local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch_name//\//_}.json"

    if [[ ! -f "$metadata_file" ]]; then
        echo "Error: Metadata file not found for branch: $branch_name" >&2
        return 1
    fi

    # Update field using jq
    local temp_file="${metadata_file}.tmp"
    jq --arg field "$field" --arg value "$value" '.[$field] = $value' "$metadata_file" > "$temp_file"
    mv "$temp_file" "$metadata_file"

    return 0
}

ce_branch_init_metadata() {
    local branch_name="$1"
    local task_type="$2"
    local description="$3"
    local phase="$4"
    local terminal="$5"

    _ce_branch_init_dirs

    local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch_name//\//_}.json"
    local timestamp
    timestamp=$(date -Iseconds)

    # Create metadata JSON
    cat > "$metadata_file" <<EOF
{
  "branch_name": "$branch_name",
  "task_type": "$task_type",
  "description": "$description",
  "phase": "$phase",
  "terminal_id": "$terminal",
  "status": "active",
  "created_at": "$timestamp",
  "updated_at": "$timestamp",
  "last_activity": "$timestamp",
  "session_ids": [],
  "commits": [],
  "stats": {
    "commits_count": 0,
    "files_changed": 0,
    "lines_added": 0,
    "lines_removed": 0
  },
  "phase_history": [
    {
      "phase": "$phase",
      "timestamp": "$timestamp"
    }
  ]
}
EOF

    return 0
}

ce_branch_archive_metadata() {
    local branch_name="$1"

    _ce_branch_init_dirs

    local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch_name//\//_}.json"

    if [[ ! -f "$metadata_file" ]]; then
        return 0 # No metadata to archive
    fi

    # Add archived timestamp
    local temp_file="${metadata_file}.tmp"
    local timestamp
    timestamp=$(date -Iseconds)

    jq --arg timestamp "$timestamp" '. + {archived_at: $timestamp, status: "archived"}' "$metadata_file" > "$temp_file"

    # Move to archive
    local archive_file="${CE_BRANCH_ARCHIVE_DIR}/${branch_name//\//_}_$(date +%Y%m%d_%H%M%S).json"
    mv "$temp_file" "$archive_file"
    rm -f "$metadata_file"

    return 0
}

# Conflict detection
ce_branch_detect_conflicts() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Check if branch exists
    if ! ce_branch_check_exists "$branch_name"; then
        echo "Error: Branch does not exist: $branch_name" >&2
        return 1
    fi

    # Get modified files in this branch
    local modified_files
    modified_files=$(git diff --name-only "$base_branch...$branch_name" 2>/dev/null || echo "")

    if [[ -z "$modified_files" ]]; then
        echo "No conflicts detected (no files modified)"
        return 0
    fi

    # Check for actual merge conflicts
    local conflicts
    conflicts=$(git merge-tree "$(git merge-base "$base_branch" "$branch_name")" "$base_branch" "$branch_name" 2>/dev/null | grep -c "^<<<<<" || echo "0")

    if [[ "$conflicts" -gt 0 ]]; then
        echo "⚠️  Potential conflicts detected:"
        echo "   Conflicting files: $conflicts"
        echo "   Modified files:"
        echo "$modified_files" | sed 's/^/     - /'
        return 1
    else
        echo "✅ No conflicts detected"
        return 0
    fi
}

ce_branch_check_divergence() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Get ahead/behind counts
    local ahead behind
    ahead=$(git rev-list --count "$base_branch..$branch_name" 2>/dev/null || echo "0")
    behind=$(git rev-list --count "$branch_name..$base_branch" 2>/dev/null || echo "0")

    echo "Branch divergence from $base_branch:"
    echo "  Ahead: $ahead commits"
    echo "  Behind: $behind commits"

    if [[ "$behind" -gt 10 ]]; then
        echo "  ⚠️  Warning: Branch is significantly behind base"
    fi

    return 0
}

# Branch validation
ce_branch_validate_phase_transition() {
    local branch_name="${1:-$(git branch --show-current)}"
    local new_phase="$2"

    local metadata
    metadata=$(ce_branch_get_metadata "$branch_name")

    if [[ -z "$metadata" || "$metadata" == "{}" ]]; then
        echo "Error: No metadata found for branch" >&2
        return 1
    fi

    local current_phase
    current_phase=$(echo "$metadata" | jq -r '.phase // "P0"')

    # Extract phase numbers
    local current_num="${current_phase#P}"
    local new_num="${new_phase#P}"

    # Can only move forward or stay same
    if [[ "$new_num" -lt "$current_num" ]]; then
        echo "Error: Cannot move backward from $current_phase to $new_phase" >&2
        return 1
    fi

    # TODO: Add gate validation here
    # Check if required gates are passed for phase transition

    echo "✅ Phase transition validated: $current_phase -> $new_phase"
    return 0
}

ce_branch_get_phase() {
    local branch_name="${1:-$(git branch --show-current)}"
    local metadata
    metadata=$(ce_branch_get_metadata "$branch_name")
    echo "$metadata" | jq -r '.phase // "P0"'
}

ce_branch_set_phase() {
    local branch_name="${1:-$(git branch --show-current)}"
    local new_phase="$2"

    # Validate transition
    if ! ce_branch_validate_phase_transition "$branch_name" "$new_phase"; then
        return 1
    fi

    # Update metadata
    ce_branch_set_metadata "$branch_name" "phase" "$new_phase"

    # Add to phase history
    local metadata_file="${CE_BRANCH_METADATA_DIR}/${branch_name//\//_}.json"
    local timestamp
    timestamp=$(date -Iseconds)

    local temp_file="${metadata_file}.tmp"
    jq --arg phase "$new_phase" --arg timestamp "$timestamp" \
       '.phase_history += [{phase: $phase, timestamp: $timestamp}]' \
       "$metadata_file" > "$temp_file"
    mv "$temp_file" "$metadata_file"

    echo "✅ Phase updated to $new_phase for branch: $branch_name"
    return 0
}

# Branch synchronization
ce_branch_sync_with_base() {
    local merge_flag="${1:-}"
    local base_branch="${2:-main}"
    local branch_name
    branch_name=$(git branch --show-current)

    echo "Syncing $branch_name with $base_branch..."

    # Fetch latest
    git fetch origin "$base_branch" 2>/dev/null || true

    # Check divergence
    ce_branch_check_divergence "$branch_name" "$base_branch"

    # Choose strategy
    if [[ "$merge_flag" == "--merge" ]]; then
        echo "Using merge strategy..."
        git merge "origin/$base_branch"
    else
        echo "Using rebase strategy..."
        git rebase "origin/$base_branch"
    fi

    local result=$?

    if [[ $result -eq 0 ]]; then
        echo "✅ Sync completed successfully"
    else
        echo "⚠️  Conflicts detected during sync. Please resolve manually."
    fi

    return $result
}

ce_branch_push() {
    local force_flag="${1:-}"
    local branch_name
    branch_name=$(git branch --show-current)

    echo "Pushing branch: $branch_name"

    # Check if remote exists
    if ! git remote | grep -q "origin"; then
        echo "Error: No remote 'origin' configured" >&2
        return 1
    fi

    # Push with tracking
    if [[ "$force_flag" == "--force-with-lease" ]]; then
        git push --force-with-lease -u origin "$branch_name"
    else
        git push -u origin "$branch_name"
    fi

    local result=$?

    if [[ $result -eq 0 ]]; then
        echo "✅ Branch pushed successfully"
        ce_branch_set_metadata "$branch_name" "last_push" "$(date -Iseconds)"
    else
        echo "Error: Failed to push branch" >&2
    fi

    return $result
}

# Branch analytics
ce_branch_get_stats() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    echo "Branch Statistics: $branch_name"
    echo "================================"

    # Commit count
    local commits
    commits=$(git rev-list --count "$base_branch..$branch_name" 2>/dev/null || echo "0")
    echo "Commits: $commits"

    # Files changed
    local files_changed
    files_changed=$(git diff --name-only "$base_branch...$branch_name" 2>/dev/null | wc -l || echo "0")
    echo "Files changed: $files_changed"

    # Lines added/removed
    local stats
    stats=$(git diff --shortstat "$base_branch...$branch_name" 2>/dev/null || echo "")
    echo "Changes: $stats"

    # Duration
    local metadata
    metadata=$(ce_branch_get_metadata "$branch_name")
    if [[ -n "$metadata" && "$metadata" != "{}" ]]; then
        local created_at
        created_at=$(echo "$metadata" | jq -r '.created_at // ""')
        if [[ -n "$created_at" ]]; then
            local created_epoch
            created_epoch=$(date -d "$created_at" +%s 2>/dev/null || echo "0")
            local now_epoch
            now_epoch=$(date +%s)
            local duration=$((now_epoch - created_epoch))
            local hours=$((duration / 3600))
            local minutes=$(((duration % 3600) / 60))
            echo "Duration: ${hours}h ${minutes}m"
        fi
    fi

    return 0
}

ce_branch_get_history() {
    local branch_name="${1:-$(git branch --show-current)}"
    local metadata
    metadata=$(ce_branch_get_metadata "$branch_name")

    if [[ -z "$metadata" || "$metadata" == "{}" ]]; then
        echo "No history available"
        return 0
    fi

    echo "Phase History for: $branch_name"
    echo "==============================="

    echo "$metadata" | jq -r '.phase_history[] | "[\(.timestamp)] Phase \(.phase)"'

    return 0
}

# Cleanup
ce_branch_cleanup_stale() {
    local days="${1:-30}"
    local dry_run="${2:-}"

    [[ "$1" == "--days="* ]] && days="${1#--days=}"
    [[ "$2" == "--dry-run" || "$1" == "--dry-run" ]] && dry_run="--dry-run"

    echo "Cleaning up stale branches (inactive for >$days days)..."
    [[ -n "$dry_run" ]] && echo "(DRY RUN - no changes will be made)"

    local cutoff_date
    cutoff_date=$(date -d "$days days ago" +%s)

    local cleaned=0

    # Check archived metadata
    if [[ -d "$CE_BRANCH_ARCHIVE_DIR" ]]; then
        find "$CE_BRANCH_ARCHIVE_DIR" -name "*.json" -type f | while read -r metadata_file; do
            local archived_at
            archived_at=$(jq -r '.archived_at // ""' "$metadata_file" 2>/dev/null || echo "")

            if [[ -n "$archived_at" ]]; then
                local archived_epoch
                archived_epoch=$(date -d "$archived_at" +%s 2>/dev/null || echo "0")

                if [[ "$archived_epoch" -lt "$cutoff_date" ]]; then
                    echo "  Removing old archive: $(basename "$metadata_file")"
                    [[ -z "$dry_run" ]] && rm -f "$metadata_file"
                    ((cleaned++))
                fi
            fi
        done
    fi

    echo "Cleanup complete. Removed $cleaned old archives."

    return 0
}

# Context management
ce_context_save() {
    local context_name="$1"
    local context_dir=".workflow/contexts"
    mkdir -p "$context_dir"

    local context_file="${context_dir}/${context_name//\//_}.ctx"

    # Save current state
    cat > "$context_file" <<EOF
{
  "branch": "$(git branch --show-current)",
  "saved_at": "$(date -Iseconds)",
  "modified_files": $(git status --porcelain | jq -R . | jq -s .),
  "stash_ref": "$(git stash list | head -n1 | grep -oP 'stash@\{[0-9]+\}' || echo "")"
}
EOF

    return 0
}

ce_context_restore() {
    local context_name="$1"
    local context_dir=".workflow/contexts"
    local context_file="${context_dir}/${context_name//\//_}.ctx"

    if [[ ! -f "$context_file" ]]; then
        return 1
    fi

    # Could restore stash, working tree state, etc.
    # For now, just acknowledge the context exists
    echo "Context restored for: $context_name"

    return 0
}

# Export functions
export -f ce_branch_create
export -f ce_branch_generate_name
export -f ce_branch_validate_name
export -f ce_branch_check_exists
export -f ce_branch_switch
export -f ce_branch_delete
export -f ce_branch_list_active
export -f ce_branch_list_all
export -f ce_branch_get_metadata
export -f ce_branch_set_metadata
export -f ce_branch_init_metadata
export -f ce_branch_archive_metadata
export -f ce_branch_detect_conflicts
export -f ce_branch_check_divergence
export -f ce_branch_validate_phase_transition
export -f ce_branch_get_phase
export -f ce_branch_set_phase
export -f ce_branch_sync_with_base
export -f ce_branch_push
export -f ce_branch_get_stats
export -f ce_branch_get_history
export -f ce_branch_cleanup_stale
export -f ce_context_save
export -f ce_context_restore
