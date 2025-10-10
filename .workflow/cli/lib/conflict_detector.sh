#!/usr/bin/env bash
# conflict_detector.sh - Merge conflict detection and resolution
# Proactive conflict detection and intelligent resolution suggestions
set -euo pipefail

# Session state directory
CE_SESSION_DIR="${CE_SESSION_DIR:-.workflow/cli/state/sessions}"
CE_CONFLICT_REPORT_DIR=".workflow/reports/conflicts"

# Initialize directories
_ce_conflict_init_dirs() {
    mkdir -p "$CE_CONFLICT_REPORT_DIR"
    mkdir -p "$CE_SESSION_DIR"
}

# Conflict detection
ce_conflict_detect() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    _ce_conflict_init_dirs

    echo "Detecting conflicts for: $branch_name vs $base_branch"

    # Run all detection methods
    local file_conflicts
    file_conflicts=$(ce_conflict_detect_files "$branch_name" "$base_branch")

    local line_conflicts
    line_conflicts=$(ce_conflict_detect_lines "$branch_name" "$base_branch")

    local semantic_conflicts
    semantic_conflicts=$(ce_conflict_detect_semantic "$branch_name" "$base_branch")

    # Compile results
    local report_file="${CE_CONFLICT_REPORT_DIR}/conflict_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "branch": "$branch_name",
  "base": "$base_branch",
  "file_conflicts": $file_conflicts,
  "line_conflicts": $line_conflicts,
  "semantic_conflicts": $semantic_conflicts
}
EOF

    echo "Conflict report saved: $report_file"
    cat "$report_file" | jq '.'

    return 0
}

ce_conflict_detect_files() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Get files modified in both branches
    local branch_files base_files

    branch_files=$(git diff --name-only "$(git merge-base "$base_branch" "$branch_name")".."$branch_name" 2>/dev/null | sort)
    base_files=$(git diff --name-only "$(git merge-base "$base_branch" "$branch_name")".."$base_branch" 2>/dev/null | sort)

    # Find overlapping files
    local conflicting_files
    conflicting_files=$(comm -12 <(echo "$branch_files") <(echo "$base_files") 2>/dev/null || echo "")

    # Build JSON array
    local json_array="[]"
    if [[ -n "$conflicting_files" ]]; then
        json_array=$(echo "$conflicting_files" | jq -R . | jq -s .)
    fi

    echo "$json_array"
    return 0
}

ce_conflict_detect_lines() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Use git merge-tree to detect line-level conflicts
    local merge_base
    merge_base=$(git merge-base "$base_branch" "$branch_name" 2>/dev/null || echo "")

    if [[ -z "$merge_base" ]]; then
        echo "{}"
        return 0
    fi

    local merge_result
    merge_result=$(git merge-tree "$merge_base" "$base_branch" "$branch_name" 2>/dev/null || echo "")

    local conflict_count
    conflict_count=$(echo "$merge_result" | grep -c "^<<<<<" || echo "0")

    # Extract conflict markers
    local conflicts_json="{\"conflict_count\": $conflict_count}"

    echo "$conflicts_json"
    return 0
}

ce_conflict_detect_semantic() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Detect semantic conflicts in common file types
    local modified_files
    modified_files=$(git diff --name-only "$(git merge-base "$base_branch" "$branch_name")".."$branch_name" 2>/dev/null || echo "")

    local semantic_conflicts="[]"

    # Check for function/class name conflicts (simple pattern matching)
    # This is a basic implementation - can be enhanced with language parsers
    local conflict_patterns=(
        "^function "
        "^def "
        "^class "
        "^interface "
        "^export function"
        "^export class"
    )

    # TODO: Implement language-specific semantic analysis
    # For now, return empty array
    echo "$semantic_conflicts"
    return 0
}

# Conflict analysis
ce_conflict_analyze() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    echo "Analyzing conflicts between $branch_name and $base_branch..."

    # Detect conflicts first
    local conflicts
    conflicts=$(ce_conflict_detect "$branch_name" "$base_branch")

    # Calculate severity
    local severity
    severity=$(ce_conflict_calculate_severity "$branch_name" "$base_branch")

    # Categorize conflicts
    local categories
    categories=$(ce_conflict_categorize "$branch_name" "$base_branch")

    cat <<EOF
Conflict Analysis Report
========================
Branch: $branch_name
Base: $base_branch
Severity: $severity
Categories: $categories

Recommendation: $(ce_conflict_suggest_resolution "$branch_name")
EOF

    return 0
}

ce_conflict_calculate_severity() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Factors: number of files, number of lines, complexity
    local file_count
    file_count=$(ce_conflict_detect_files "$branch_name" "$base_branch" | jq 'length')

    local line_info
    line_info=$(ce_conflict_detect_lines "$branch_name" "$base_branch")
    local conflict_count
    conflict_count=$(echo "$line_info" | jq -r '.conflict_count // 0')

    # Calculate severity score (0-100)
    local score=0
    score=$((file_count * 10 + conflict_count * 5))

    # Cap at 100
    [[ $score -gt 100 ]] && score=100

    # Determine level
    local level="LOW"
    [[ $score -gt 30 ]] && level="MEDIUM"
    [[ $score -gt 70 ]] && level="HIGH"

    echo "$level (score: $score)"
    return 0
}

ce_conflict_categorize() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Categorize by file types and change patterns
    local conflicting_files
    conflicting_files=$(ce_conflict_detect_files "$branch_name" "$base_branch" | jq -r '.[]' 2>/dev/null || echo "")

    local trivial=0 simple=0 complex=0 breaking=0

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue

        # Check file extension and patterns
        case "$file" in
            *.md|*.txt|*.json)
                ((trivial++))
                ;;
            *.sh|*.py|*.js|*.ts)
                ((simple++))
                ;;
            **/api/*|**/interface/*)
                ((breaking++))
                ;;
            *)
                ((complex++))
                ;;
        esac
    done <<< "$conflicting_files"

    echo "Trivial: $trivial, Simple: $simple, Complex: $complex, Breaking: $breaking"
    return 0
}

# Conflict simulation
ce_conflict_simulate_merge() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    echo "Simulating merge: $branch_name -> $base_branch"

    # Create temporary worktree
    local temp_dir
    temp_dir=$(mktemp -d)
    local worktree_created=false

    trap "cd - > /dev/null 2>&1; [[ \$worktree_created == true ]] && git worktree remove --force '$temp_dir' 2>/dev/null; rm -rf '$temp_dir'" EXIT

    if git worktree add "$temp_dir" "$base_branch" 2>/dev/null; then
        worktree_created=true
        cd "$temp_dir"

        # Attempt merge
        if git merge --no-commit --no-ff "$branch_name" 2>/dev/null; then
            echo "✅ Simulation: Merge will succeed without conflicts"
            git merge --abort 2>/dev/null || true
            cd - > /dev/null
            return 0
        else
            echo "⚠️  Simulation: Merge will have conflicts"

            # Show conflicting files
            local conflicted
            conflicted=$(git diff --name-only --diff-filter=U 2>/dev/null || echo "")
            if [[ -n "$conflicted" ]]; then
                echo "Conflicting files:"
                echo "$conflicted" | sed 's/^/  - /'
            fi

            git merge --abort 2>/dev/null || true
            cd - > /dev/null
            return 1
        fi
    else
        echo "Error: Failed to create worktree for simulation"
        return 1
    fi
}

ce_conflict_dry_run() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Same as simulate_merge but with different output format
    ce_conflict_simulate_merge "$branch_name" "$base_branch"
    return $?
}

# Conflict resolution suggestions
ce_conflict_suggest_resolution() {
    local file="${1:-}"

    if [[ -z "$file" ]]; then
        # General suggestion
        echo "Suggested resolution strategies:"
        echo "  1. Rebase: For clean linear history (recommended for feature branches)"
        echo "  2. Merge: For preserving complete history (recommended for releases)"
        echo "  3. Squash: For combining commits (recommended for small features)"
        return 0
    fi

    # File-specific suggestion
    ce_conflict_suggest_for_file "$file"
}

ce_conflict_suggest_for_file() {
    local file="$1"

    echo "Resolution suggestion for: $file"

    # Analyze file type and suggest strategy
    case "$file" in
        *.md|*.txt)
            echo "  Strategy: MANUAL - Documentation conflicts require human review"
            echo "  Confidence: LOW"
            ;;
        *.json|*.yml|*.yaml)
            echo "  Strategy: STRUCTURAL - Use merge tool with structure awareness"
            echo "  Confidence: MEDIUM"
            ;;
        *.lock|package-lock.json|yarn.lock|Gemfile.lock)
            echo "  Strategy: REGENERATE - Delete and regenerate lock file"
            echo "  Confidence: HIGH"
            ;;
        *)
            echo "  Strategy: MANUAL - Review changes carefully"
            echo "  Confidence: MEDIUM"
            ;;
    esac

    return 0
}

ce_conflict_auto_resolve_trivial() {
    echo "Auto-resolving trivial conflicts..."

    local resolved=0

    # Get list of conflicted files
    local conflicted_files
    conflicted_files=$(git diff --name-only --diff-filter=U 2>/dev/null || echo "")

    if [[ -z "$conflicted_files" ]]; then
        echo "No conflicts to resolve"
        return 0
    fi

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue

        # Auto-resolve lock files
        if [[ "$file" == *.lock ]] || [[ "$file" == "package-lock.json" ]] || [[ "$file" == "yarn.lock" ]]; then
            echo "  Auto-resolving: $file (regenerating)"
            git checkout --theirs "$file" 2>/dev/null
            git add "$file" 2>/dev/null
            ((resolved++))
        fi

        # TODO: Add more auto-resolution patterns
        # - Whitespace-only conflicts
        # - Comment-only conflicts
        # - Import reordering

    done <<< "$conflicted_files"

    echo "Auto-resolved $resolved trivial conflicts"
    return 0
}

# Conflict resolution
ce_conflict_resolve_interactive() {
    echo "Starting interactive conflict resolution..."

    # Get conflicted files
    local conflicted_files
    conflicted_files=$(git diff --name-only --diff-filter=U 2>/dev/null || echo "")

    if [[ -z "$conflicted_files" ]]; then
        echo "No conflicts to resolve"
        return 0
    fi

    local file_count
    file_count=$(echo "$conflicted_files" | wc -l)

    echo "Found $file_count conflicted files"
    echo ""

    local index=1
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue

        echo "[$index/$file_count] Conflict in: $file"
        echo ""

        # Show conflict details
        ce_conflict_show "$file"
        echo ""

        # Present options
        echo "Resolution options:"
        echo "  1) Accept ours (keep current version)"
        echo "  2) Accept theirs (take incoming version)"
        echo "  3) Edit manually"
        echo "  4) Skip for now"
        echo "  q) Quit"
        echo ""

        read -rp "Choose resolution [1-4, q]: " choice

        case "$choice" in
            1)
                ce_conflict_resolve_with_ours "$file"
                ;;
            2)
                ce_conflict_resolve_with_theirs "$file"
                ;;
            3)
                ce_conflict_resolve_manual "$file"
                ;;
            4)
                echo "Skipped: $file"
                ;;
            q)
                echo "Exiting interactive resolution"
                return 0
                ;;
            *)
                echo "Invalid choice, skipping"
                ;;
        esac

        echo ""
        ((index++))
    done <<< "$conflicted_files"

    echo "Interactive resolution complete"
    return 0
}

ce_conflict_resolve_with_ours() {
    local file="$1"

    if git checkout --ours "$file" 2>/dev/null; then
        git add "$file" 2>/dev/null
        echo "✅ Resolved using 'ours': $file"
        return 0
    else
        echo "Error: Failed to resolve with 'ours': $file" >&2
        return 1
    fi
}

ce_conflict_resolve_with_theirs() {
    local file="$1"

    if git checkout --theirs "$file" 2>/dev/null; then
        git add "$file" 2>/dev/null
        echo "✅ Resolved using 'theirs': $file"
        return 0
    else
        echo "Error: Failed to resolve with 'theirs': $file" >&2
        return 1
    fi
}

ce_conflict_resolve_manual() {
    local file="$1"

    # Open in editor
    local editor="${EDITOR:-vim}"

    echo "Opening $file in $editor..."
    $editor "$file"

    # Ask if resolved
    read -rp "Mark as resolved? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git add "$file" 2>/dev/null
        echo "✅ Marked as resolved: $file"
        return 0
    else
        echo "Not marked as resolved: $file"
        return 1
    fi
}

# Conflict visualization
ce_conflict_show() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        echo "Error: File not found: $file" >&2
        return 1
    fi

    echo "Conflict details for: $file"
    echo "============================"
    echo ""

    # Show conflict sections with context
    grep -n -A5 -B5 "^<<<<<<< " "$file" 2>/dev/null || echo "No conflict markers found"

    return 0
}

ce_conflict_diff_three_way() {
    local file="$1"

    echo "Three-way diff for: $file"
    echo "========================"

    # Get merge base
    local merge_base
    merge_base=$(git merge-base HEAD MERGE_HEAD 2>/dev/null || echo "")

    if [[ -z "$merge_base" ]]; then
        echo "Error: Not in merge state" >&2
        return 1
    fi

    echo ""
    echo "=== BASE (common ancestor) ==="
    git show "$merge_base:$file" 2>/dev/null || echo "(file didn't exist)"

    echo ""
    echo "=== OURS (current branch) ==="
    git show "HEAD:$file" 2>/dev/null || echo "(file deleted)"

    echo ""
    echo "=== THEIRS (incoming branch) ==="
    git show "MERGE_HEAD:$file" 2>/dev/null || echo "(file deleted)"

    return 0
}

ce_conflict_visualize_tree() {
    echo "Conflict Tree Visualization"
    echo "==========================="

    # Get conflicted files grouped by directory
    local conflicted_files
    conflicted_files=$(git diff --name-only --diff-filter=U 2>/dev/null || echo "")

    if [[ -z "$conflicted_files" ]]; then
        echo "No conflicts"
        return 0
    fi

    # Build tree structure
    echo "$conflicted_files" | awk -F/ '{
        for (i=1; i<=NF; i++) {
            indent = ""
            for (j=1; j<i; j++) indent = indent "  "
            if (i == NF)
                print indent "⚠️  " $i
            else
                print indent "📁 " $i
        }
    }' | sort -u

    return 0
}

# Conflict prevention
ce_conflict_check_before_commit() {
    local base_branch="${1:-main}"
    local current_branch
    current_branch=$(git branch --show-current)

    echo "Checking for potential conflicts before commit..."

    # Check against base branch
    local conflicts
    conflicts=$(ce_conflict_detect_files "$current_branch" "$base_branch" | jq 'length')

    if [[ "$conflicts" -gt 0 ]]; then
        echo "⚠️  Warning: Potential conflicts detected with $base_branch"
        echo "   Conflicting files: $conflicts"
        echo "   Consider syncing with base before committing"
        return 1
    fi

    # Check against other active branches
    ce_conflict_compare_active_sessions

    echo "✅ No conflicts detected"
    return 0
}

ce_conflict_check_branch_divergence() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    echo "Checking branch divergence..."

    # Get commits ahead/behind
    local ahead behind
    ahead=$(git rev-list --count "$base_branch..$branch_name" 2>/dev/null || echo "0")
    behind=$(git rev-list --count "$branch_name..$base_branch" 2>/dev/null || echo "0")

    # Calculate divergence score
    local divergence_score=$((ahead + behind * 2)) # Behind is weighted more

    echo "Divergence Analysis:"
    echo "  Ahead: $ahead commits"
    echo "  Behind: $behind commits"
    echo "  Divergence Score: $divergence_score"

    # Time since last sync
    local last_sync
    last_sync=$(git log --format=%ct "$branch_name" -- 2>/dev/null | head -n1)
    local days_since_sync=0

    if [[ -n "$last_sync" ]]; then
        local now
        now=$(date +%s)
        days_since_sync=$(( (now - last_sync) / 86400 ))
        echo "  Days since last activity: $days_since_sync"
    fi

    return 0
}

ce_conflict_recommend_sync() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Get divergence info
    local behind
    behind=$(git rev-list --count "$branch_name..$base_branch" 2>/dev/null || echo "0")

    # Calculate urgency
    local urgency="LOW"
    [[ $behind -gt 5 ]] && urgency="MEDIUM"
    [[ $behind -gt 10 ]] && urgency="HIGH"
    [[ $behind -gt 20 ]] && urgency="CRITICAL"

    echo "Sync Recommendation"
    echo "==================="
    echo "Branch: $branch_name"
    echo "Base: $base_branch"
    echo "Commits behind: $behind"
    echo "Urgency: $urgency"

    if [[ "$urgency" != "LOW" ]]; then
        echo ""
        echo "💡 Recommendation: Sync with $base_branch soon"
        echo "   Command: git rebase $base_branch"
    fi

    return 0
}

# Cross-terminal conflict detection
ce_conflict_compare_active_sessions() {
    _ce_conflict_init_dirs

    echo "Checking conflicts across active terminal sessions..."

    # Read all session files
    local sessions=()
    if [[ -d "$CE_SESSION_DIR" ]]; then
        while IFS= read -r session_file; do
            sessions+=("$session_file")
        done < <(find "$CE_SESSION_DIR" -name "*.yml" -type f)
    fi

    if [[ ${#sessions[@]} -eq 0 ]]; then
        echo "No active sessions found"
        return 0
    fi

    echo "Found ${#sessions[@]} active session(s)"

    # Compare each session pair
    local conflicts_found=0
    for ((i=0; i<${#sessions[@]}; i++)); do
        for ((j=i+1; j<${#sessions[@]}; j++)); do
            local session1="${sessions[$i]}"
            local session2="${sessions[$j]}"

            # Extract terminal IDs and files
            local term1 term2
            term1=$(grep "^terminal_id:" "$session1" | cut -d'"' -f2 2>/dev/null || echo "unknown")
            term2=$(grep "^terminal_id:" "$session2" | cut -d'"' -f2 2>/dev/null || echo "unknown")

            # Get modified files
            local files1 files2
            files1=$(grep -A 100 "^files_modified:" "$session1" | tail -n +2 | grep "^  -" | sed 's/^  - //' 2>/dev/null || echo "")
            files2=$(grep -A 100 "^files_modified:" "$session2" | tail -n +2 | grep "^  -" | sed 's/^  - //' 2>/dev/null || echo "")

            # Check for overlap
            if [[ -n "$files1" && -n "$files2" ]]; then
                local overlap
                overlap=$(comm -12 <(echo "$files1" | sort) <(echo "$files2" | sort) 2>/dev/null || echo "")

                if [[ -n "$overlap" ]]; then
                    echo "⚠️  Conflict detected between terminals $term1 and $term2:"
                    echo "$overlap" | sed 's/^/     - /'
                    ((conflicts_found++))
                fi
            fi
        done
    done

    if [[ $conflicts_found -eq 0 ]]; then
        echo "✅ No cross-terminal conflicts detected"
    else
        echo ""
        echo "Total conflicts found: $conflicts_found"
    fi

    return $conflicts_found
}

ce_conflict_get_modified_files() {
    local terminal_id="${1:-t1}"
    local session_file="${CE_SESSION_DIR}/${terminal_id}.yml"

    if [[ ! -f "$session_file" ]]; then
        echo "[]"
        return 0
    fi

    # Extract modified files from YAML
    grep -A 100 "^files_modified:" "$session_file" | tail -n +2 | grep "^  -" | sed 's/^  - //' | jq -R . | jq -s . || echo "[]"

    return 0
}

ce_conflict_check_overlap() {
    local terminal1="$1"
    local terminal2="$2"

    local files1 files2
    files1=$(ce_conflict_get_modified_files "$terminal1" | jq -r '.[]' 2>/dev/null || echo "")
    files2=$(ce_conflict_get_modified_files "$terminal2" | jq -r '.[]' 2>/dev/null || echo "")

    if [[ -z "$files1" || -z "$files2" ]]; then
        echo "No overlap (one or both terminals have no modified files)"
        return 0
    fi

    local overlap
    overlap=$(comm -12 <(echo "$files1" | sort) <(echo "$files2" | sort) 2>/dev/null || echo "")

    if [[ -n "$overlap" ]]; then
        echo "Overlapping files between $terminal1 and $terminal2:"
        echo "$overlap" | sed 's/^/  - /'
        return 1
    else
        echo "No overlap between $terminal1 and $terminal2"
        return 0
    fi
}

# Conflict tracking
ce_conflict_get_history() {
    local history_dir="${CE_CONFLICT_REPORT_DIR}/history"
    mkdir -p "$history_dir"

    echo "Conflict Resolution History"
    echo "==========================="

    if [[ -d "$history_dir" ]]; then
        find "$history_dir" -name "*.json" -type f | sort | while read -r history_file; do
            echo ""
            jq -r '
                "[\(.timestamp)] " +
                "Branch: \(.branch) | " +
                "Strategy: \(.strategy) | " +
                "Outcome: \(.outcome)"
            ' "$history_file" 2>/dev/null || echo "Invalid history file"
        done
    else
        echo "No history available"
    fi

    return 0
}

ce_conflict_record_resolution() {
    local file="$1"
    local strategy="$2"
    local outcome="$3"

    local history_dir="${CE_CONFLICT_REPORT_DIR}/history"
    mkdir -p "$history_dir"

    local history_file="${history_dir}/resolution_$(date +%Y%m%d_%H%M%S).json"

    cat > "$history_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "file": "$file",
  "branch": "$(git branch --show-current)",
  "strategy": "$strategy",
  "outcome": "$outcome"
}
EOF

    return 0
}

# Conflict reporting
ce_conflict_generate_report() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    local report_file="${CE_CONFLICT_REPORT_DIR}/report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" <<EOF
# Conflict Analysis Report

**Generated:** $(date -Iseconds)
**Branch:** $branch_name
**Base:** $base_branch

## Summary

$(ce_conflict_show_summary)

## Detailed Analysis

### File-Level Conflicts

$(ce_conflict_detect_files "$branch_name" "$base_branch" | jq -r '.[] | "- " + .')

### Severity Assessment

$(ce_conflict_calculate_severity "$branch_name" "$base_branch")

### Conflict Categories

$(ce_conflict_categorize "$branch_name" "$base_branch")

## Resolution Recommendations

$(ce_conflict_suggest_resolution)

## Risk Assessment

- **Merge Risk:** $(ce_conflict_calculate_severity "$branch_name" "$base_branch" | cut -d'(' -f1)
- **Recommendation:** Consider manual review before merging

---
*Generated by Claude Enhancer Conflict Detector*
EOF

    echo "Report saved: $report_file"
    cat "$report_file"

    return 0
}

ce_conflict_show_summary() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    local file_conflicts line_conflicts
    file_conflicts=$(ce_conflict_detect_files "$branch_name" "$base_branch" | jq 'length')
    line_conflicts=$(ce_conflict_detect_lines "$branch_name" "$base_branch" | jq -r '.conflict_count // 0')

    # Categorize
    local categories
    categories=$(ce_conflict_categorize "$branch_name" "$base_branch")

    cat <<EOF
Conflict Summary
================
- Total conflicting files: $file_conflicts
- Line-level conflicts: $line_conflicts
- Categories: $categories
EOF

    return 0
}

ce_conflict_export_json() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    # Compile full conflict data
    cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "branch": "$branch_name",
  "base": "$base_branch",
  "files": $(ce_conflict_detect_files "$branch_name" "$base_branch"),
  "lines": $(ce_conflict_detect_lines "$branch_name" "$base_branch"),
  "severity": "$(ce_conflict_calculate_severity "$branch_name" "$base_branch")",
  "categories": "$(ce_conflict_categorize "$branch_name" "$base_branch")"
}
EOF

    return 0
}

# Branch comparison
ce_conflict_compare_branches() {
    local branch_a="$1"
    local branch_b="$2"

    echo "Comparing branches: $branch_a <-> $branch_b"
    echo "========================================="

    # Find common base
    local merge_base
    merge_base=$(ce_conflict_find_common_base "$branch_a" "$branch_b")
    echo "Common ancestor: $merge_base"
    echo ""

    # List divergent files
    ce_conflict_list_divergent_files "$branch_a" "$branch_b"

    return 0
}

ce_conflict_find_common_base() {
    local branch_a="$1"
    local branch_b="$2"

    git merge-base "$branch_a" "$branch_b" 2>/dev/null || echo "No common base found"
}

ce_conflict_list_divergent_files() {
    local branch_a="$1"
    local branch_b="$2"

    local merge_base
    merge_base=$(ce_conflict_find_common_base "$branch_a" "$branch_b")

    if [[ -z "$merge_base" || "$merge_base" == "No common base found" ]]; then
        echo "Cannot determine divergent files without common base"
        return 1
    fi

    echo "Divergent Files Analysis"
    echo "========================"
    echo ""

    # Files modified in both
    local files_a files_b
    files_a=$(git diff --name-only "$merge_base..$branch_a" 2>/dev/null | sort)
    files_b=$(git diff --name-only "$merge_base..$branch_b" 2>/dev/null | sort)

    echo "Modified in both (potential conflicts):"
    comm -12 <(echo "$files_a") <(echo "$files_b") | sed 's/^/  ⚠️  /'

    echo ""
    echo "Modified only in $branch_a:"
    comm -23 <(echo "$files_a") <(echo "$files_b") | sed 's/^/  ✓ /'

    echo ""
    echo "Modified only in $branch_b:"
    comm -13 <(echo "$files_a") <(echo "$files_b") | sed 's/^/  ✓ /'

    return 0
}

# Smart merge
ce_conflict_smart_merge() {
    local branch_name="${1:-}"
    local base_branch="${2:-main}"

    if [[ -z "$branch_name" ]]; then
        echo "Error: Branch name required" >&2
        return 1
    fi

    echo "Attempting smart merge: $branch_name -> $base_branch"

    # First, simulate
    if ce_conflict_simulate_merge "$branch_name" "$base_branch"; then
        echo "✅ Simulation successful - proceeding with merge"
        git merge --no-ff "$branch_name"
        return $?
    else
        echo "⚠️  Conflicts detected - attempting auto-resolution"

        # Start merge
        if ! git merge --no-commit --no-ff "$branch_name" 2>/dev/null; then
            # Try auto-resolve trivial conflicts
            ce_conflict_auto_resolve_trivial

            # Check if all resolved
            local remaining
            remaining=$(git diff --name-only --diff-filter=U 2>/dev/null | wc -l)

            if [[ $remaining -eq 0 ]]; then
                echo "✅ All conflicts auto-resolved"
                git commit -m "Merge $branch_name (auto-resolved)"
                return 0
            else
                echo "⚠️  $remaining conflicts require manual resolution"
                echo "Run: ce conflict resolve-interactive"
                return 1
            fi
        fi
    fi
}

ce_conflict_suggest_merge_strategy() {
    local branch_name="${1:-$(git branch --show-current)}"
    local base_branch="${2:-main}"

    echo "Merge Strategy Recommendation"
    echo "============================="
    echo ""

    # Analyze branch characteristics
    local commits_ahead
    commits_ahead=$(git rev-list --count "$base_branch..$branch_name" 2>/dev/null || echo "0")

    local files_changed
    files_changed=$(git diff --name-only "$base_branch...$branch_name" 2>/dev/null | wc -l)

    # Suggest strategy based on characteristics
    if [[ $commits_ahead -le 3 && $files_changed -le 5 ]]; then
        cat <<EOF
Recommended: SQUASH
- Small feature with few commits
- Clean single commit in history
- Command: git merge --squash $branch_name
EOF
    elif [[ $commits_ahead -le 10 ]]; then
        cat <<EOF
Recommended: REBASE
- Medium-sized feature
- Linear history preferred
- Command: git rebase $base_branch
EOF
    else
        cat <<EOF
Recommended: MERGE COMMIT
- Large feature with many commits
- Preserve complete history
- Command: git merge --no-ff $branch_name
EOF
    fi

    return 0
}

# Export functions
export -f ce_conflict_detect
export -f ce_conflict_detect_files
export -f ce_conflict_detect_lines
export -f ce_conflict_detect_semantic
export -f ce_conflict_analyze
export -f ce_conflict_calculate_severity
export -f ce_conflict_categorize
export -f ce_conflict_simulate_merge
export -f ce_conflict_dry_run
export -f ce_conflict_suggest_resolution
export -f ce_conflict_suggest_for_file
export -f ce_conflict_auto_resolve_trivial
export -f ce_conflict_resolve_interactive
export -f ce_conflict_resolve_with_ours
export -f ce_conflict_resolve_with_theirs
export -f ce_conflict_resolve_manual
export -f ce_conflict_show
export -f ce_conflict_diff_three_way
export -f ce_conflict_visualize_tree
export -f ce_conflict_check_before_commit
export -f ce_conflict_check_branch_divergence
export -f ce_conflict_recommend_sync
export -f ce_conflict_compare_active_sessions
export -f ce_conflict_get_modified_files
export -f ce_conflict_check_overlap
export -f ce_conflict_get_history
export -f ce_conflict_record_resolution
export -f ce_conflict_generate_report
export -f ce_conflict_show_summary
export -f ce_conflict_export_json
export -f ce_conflict_compare_branches
export -f ce_conflict_find_common_base
export -f ce_conflict_list_divergent_files
export -f ce_conflict_smart_merge
export -f ce_conflict_suggest_merge_strategy
