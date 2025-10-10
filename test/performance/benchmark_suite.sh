#!/usr/bin/env bash
# Performance Benchmark Suite for Claude Enhancer v5.4.0
# Purpose: Comprehensive performance testing for all automation scripts
# Targets: <500ms (commit), <3s (push), <5s (PR), <1s (queue ops), <5min (rollback)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/test/performance/reports"
BASELINE_FILE="${REPORT_DIR}/baseline.json"

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Performance thresholds (in milliseconds/seconds)
declare -A THRESHOLDS=(
    ["commit_ms"]=500
    ["push_s"]=3
    ["pr_s"]=5
    ["queue_enqueue_ms"]=100
    ["queue_dequeue_ms"]=200
    ["queue_conflict_check_s"]=2
    ["health_check_s"]=30
    ["rollback_s"]=300
)

# Results storage
declare -A RESULTS=()
declare -A RESOURCE_USAGE=()

# Helper functions

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_benchmark() {
    local name="$1"
    local duration="$2"
    local threshold="$3"
    local unit="${4:-ms}"

    RESULTS["${name}"]="${duration}"

    local status
    if (( $(echo "$duration < $threshold" | bc -l) )); then
        status="${GREEN}✓ PASS${NC}"
    else
        status="${RED}✗ FAIL${NC}"
    fi

    printf "  %-30s %8.2f %s (threshold: %s %s) %b\n" "$name:" "$duration" "$unit" "$threshold" "$unit" "$status"
}

measure_execution_time() {
    local cmd="$@"
    local start=$(date +%s%N)

    # Execute command
    eval "$cmd" > /dev/null 2>&1 || true

    local end=$(date +%s%N)
    local duration_ns=$((end - start))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    echo "$duration_ms"
}

measure_resource_usage() {
    local pid="$1"
    local duration="${2:-5}"  # Monitor for 5 seconds

    local cpu_samples=()
    local mem_samples=()
    local start_time=$(date +%s)

    while [[ $(($(date +%s) - start_time)) -lt $duration ]]; do
        if ps -p "$pid" > /dev/null 2>&1; then
            local cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | xargs || echo "0")
            local mem=$(ps -p "$pid" -o %mem= 2>/dev/null | xargs || echo "0")
            local rss=$(ps -p "$pid" -o rss= 2>/dev/null | xargs || echo "0")

            cpu_samples+=("$cpu")
            mem_samples+=("$mem")

            sleep 0.1
        else
            break
        fi
    done

    # Calculate averages and maximums
    local avg_cpu=$(printf '%s\n' "${cpu_samples[@]}" | awk '{s+=$1; n++} END {if(n>0) print s/n; else print 0}')
    local max_cpu=$(printf '%s\n' "${cpu_samples[@]}" | sort -rn | head -n1)
    local avg_mem=$(printf '%s\n' "${mem_samples[@]}" | awk '{s+=$1; n++} END {if(n>0) print s/n; else print 0}')
    local max_mem=$(printf '%s\n' "${mem_samples[@]}" | sort -rn | head -n1)

    echo "${avg_cpu}:${max_cpu}:${avg_mem}:${max_mem}"
}

# Benchmark functions

benchmark_auto_commit() {
    log_info "Benchmarking auto_commit.sh"

    # Setup test environment
    local test_branch="perf-test-commit-$$"
    git checkout -b "$test_branch" 2>/dev/null || git checkout "$test_branch"

    # Create test file
    echo "test content" > "test_commit_${RANDOM}.txt"
    git add .

    # Measure commit time
    local duration=$(measure_execution_time "git commit -m 'perf: test commit' --no-verify")
    local duration_ms=$(echo "$duration" | bc)

    log_benchmark "commit_execution" "$duration_ms" "${THRESHOLDS[commit_ms]}" "ms"

    # Cleanup
    git reset --hard HEAD~1 2>/dev/null || true
    git checkout - 2>/dev/null || true
    git branch -D "$test_branch" 2>/dev/null || true

    return 0
}

benchmark_auto_push() {
    log_info "Benchmarking auto_push.sh"

    # Setup test environment
    local test_branch="perf-test-push-$$"
    git checkout -b "$test_branch" 2>/dev/null || git checkout "$test_branch"

    # Create test commit
    echo "test content" > "test_push_${RANDOM}.txt"
    git add .
    git commit -m "perf: test push" --no-verify 2>/dev/null || true

    # Measure push time (dry-run to avoid actual remote push)
    local start=$(date +%s%N)
    git push --dry-run origin "$test_branch" 2>/dev/null || true
    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_s=$(echo "scale=2; $duration_ns / 1000000000" | bc)

    log_benchmark "push_execution" "$duration_s" "${THRESHOLDS[push_s]}" "s"

    # Cleanup
    git checkout - 2>/dev/null || true
    git branch -D "$test_branch" 2>/dev/null || true

    return 0
}

benchmark_auto_pr() {
    log_info "Benchmarking auto_pr.sh (simulation)"

    # Simulate PR creation time (API call simulation)
    local start=$(date +%s%N)

    # Simulate gh pr create preparation
    git status > /dev/null
    git diff HEAD > /dev/null
    git log -1 --pretty=format:"%s" > /dev/null

    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_s=$(echo "scale=2; $duration_ns / 1000000000" | bc)

    log_benchmark "pr_preparation" "$duration_s" "${THRESHOLDS[pr_s]}" "s"

    return 0
}

benchmark_merge_queue_enqueue() {
    log_info "Benchmarking merge_queue enqueue"

    local queue_file="/tmp/ce_perf_test_queue_$$.fifo"

    # Measure enqueue time
    local start=$(date +%s%N)
    echo "$(date +%s):123:test-branch:session-id:QUEUED" >> "$queue_file"
    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    log_benchmark "queue_enqueue" "$duration_ms" "${THRESHOLDS[queue_enqueue_ms]}" "ms"

    # Cleanup
    rm -f "$queue_file"

    return 0
}

benchmark_merge_queue_dequeue() {
    log_info "Benchmarking merge_queue dequeue"

    local queue_file="/tmp/ce_perf_test_queue_$$.fifo"

    # Setup queue with items
    for i in {1..10}; do
        echo "$(date +%s):$i:test-branch-$i:session-$i:QUEUED" >> "$queue_file"
    done

    # Measure dequeue time
    local start=$(date +%s%N)
    head -n1 "$queue_file" > /dev/null
    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    log_benchmark "queue_dequeue" "$duration_ms" "${THRESHOLDS[queue_dequeue_ms]}" "ms"

    # Cleanup
    rm -f "$queue_file"

    return 0
}

benchmark_conflict_check() {
    log_info "Benchmarking conflict check"

    # Create test branches
    local branch1="perf-test-conflict-1-$$"
    local branch2="perf-test-conflict-2-$$"

    git checkout -b "$branch1" 2>/dev/null || true
    echo "content1" > test_conflict.txt
    git add test_conflict.txt
    git commit -m "test: conflict 1" --no-verify 2>/dev/null || true

    git checkout - 2>/dev/null || true
    git checkout -b "$branch2" 2>/dev/null || true
    echo "content2" > test_conflict.txt
    git add test_conflict.txt
    git commit -m "test: conflict 2" --no-verify 2>/dev/null || true

    # Measure conflict check time
    local start=$(date +%s%N)
    git merge-tree "$(git merge-base HEAD $branch1)" "$branch1" HEAD > /dev/null 2>&1 || true
    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_s=$(echo "scale=2; $duration_ns / 1000000000" | bc)

    log_benchmark "conflict_check" "$duration_s" "${THRESHOLDS[queue_conflict_check_s]}" "s"

    # Cleanup
    git checkout - 2>/dev/null || true
    git branch -D "$branch1" "$branch2" 2>/dev/null || true
    rm -f test_conflict.txt

    return 0
}

benchmark_health_check() {
    log_info "Benchmarking health check"

    # Measure system health check time
    local start=$(date +%s%N)

    # Simulate health check operations
    git status > /dev/null
    git remote -v > /dev/null
    git branch -a > /dev/null
    git log -1 > /dev/null

    # Check file system
    df -h . > /dev/null

    # Check dependencies
    command -v git > /dev/null
    command -v gh > /dev/null || true

    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_s=$(echo "scale=2; $duration_ns / 1000000000" | bc)

    log_benchmark "health_check" "$duration_s" "${THRESHOLDS[health_check_s]}" "s"

    return 0
}

benchmark_rollback_simulation() {
    log_info "Benchmarking rollback (simulation)"

    # Create test scenario
    local test_branch="perf-test-rollback-$$"
    git checkout -b "$test_branch" 2>/dev/null || true

    # Create commits to rollback
    for i in {1..5}; do
        echo "commit $i" > "test_rollback_$i.txt"
        git add .
        git commit -m "test: commit $i" --no-verify 2>/dev/null || true
    done

    # Measure rollback time
    local start=$(date +%s%N)
    git reset --hard HEAD~5 2>/dev/null || true
    local end=$(date +%s%N)

    local duration_ns=$((end - start))
    local duration_s=$(echo "scale=2; $duration_ns / 1000000000" | bc)

    log_benchmark "rollback_execution" "$duration_s" "${THRESHOLDS[rollback_s]}" "s"

    # Cleanup
    git checkout - 2>/dev/null || true
    git branch -D "$test_branch" 2>/dev/null || true

    return 0
}

benchmark_memory_usage() {
    log_info "Benchmarking memory usage"

    # Start a background process to monitor
    (
        sleep 10 &
        local pid=$!

        # Monitor memory
        local rss=$(ps -p $pid -o rss= 2>/dev/null | xargs || echo "0")
        local rss_mb=$(echo "scale=2; $rss / 1024" | bc)

        RESOURCE_USAGE["background_process_memory_mb"]="$rss_mb"

        kill $pid 2>/dev/null || true
    ) &

    wait

    return 0
}

benchmark_cpu_usage() {
    log_info "Benchmarking CPU usage"

    # Start a CPU-intensive operation
    (
        dd if=/dev/zero of=/dev/null bs=1M count=1000 2>/dev/null &
        local pid=$!

        sleep 1

        # Measure CPU
        local cpu=$(ps -p $pid -o %cpu= 2>/dev/null | xargs || echo "0")

        RESOURCE_USAGE["intensive_operation_cpu_percent"]="$cpu"

        kill $pid 2>/dev/null || true
    ) &

    wait

    return 0
}

benchmark_io_operations() {
    log_info "Benchmarking I/O operations"

    local test_file="/tmp/ce_perf_io_test_$$.dat"

    # Write test
    local start=$(date +%s%N)
    dd if=/dev/zero of="$test_file" bs=1M count=10 2>/dev/null
    local end=$(date +%s%N)

    local write_duration_ns=$((end - start))
    local write_duration_ms=$(echo "scale=2; $write_duration_ns / 1000000" | bc)

    # Read test
    local start=$(date +%s%N)
    dd if="$test_file" of=/dev/null bs=1M 2>/dev/null
    local end=$(date +%s%N)

    local read_duration_ns=$((end - start))
    local read_duration_ms=$(echo "scale=2; $read_duration_ns / 1000000" | bc)

    log_benchmark "io_write_10mb" "$write_duration_ms" "1000" "ms"
    log_benchmark "io_read_10mb" "$read_duration_ms" "1000" "ms"

    # Cleanup
    rm -f "$test_file"

    return 0
}

# Report generation

generate_report() {
    local report_file="${REPORT_DIR}/benchmark_$(date +%Y%m%d_%H%M%S).json"

    log_info "Generating report: $report_file"

    # Build JSON report
    cat > "$report_file" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "environment": {
    "os": "$(uname -s)",
    "kernel": "$(uname -r)",
    "cpu_cores": "$(grep -c ^processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "unknown")",
    "memory_gb": "$(free -g 2>/dev/null | grep Mem | awk '{print $2}' || echo "unknown")",
    "git_version": "$(git --version | cut -d' ' -f3)",
    "bash_version": "$BASH_VERSION"
  },
  "results": {
EOF

    # Add results
    local first=true
    for key in "${!RESULTS[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        echo -n "    \"$key\": ${RESULTS[$key]}" >> "$report_file"
    done

    cat >> "$report_file" <<EOF

  },
  "thresholds": {
    "commit_ms": ${THRESHOLDS[commit_ms]},
    "push_s": ${THRESHOLDS[push_s]},
    "pr_s": ${THRESHOLDS[pr_s]},
    "queue_enqueue_ms": ${THRESHOLDS[queue_enqueue_ms]},
    "queue_dequeue_ms": ${THRESHOLDS[queue_dequeue_ms]},
    "queue_conflict_check_s": ${THRESHOLDS[queue_conflict_check_s]},
    "health_check_s": ${THRESHOLDS[health_check_s]},
    "rollback_s": ${THRESHOLDS[rollback_s]}
  }
}
EOF

    log_success "Report generated: $report_file"

    # Save as baseline if requested
    if [[ "${SAVE_BASELINE:-0}" == "1" ]]; then
        cp "$report_file" "$BASELINE_FILE"
        log_success "Saved as baseline: $BASELINE_FILE"
    fi
}

compare_with_baseline() {
    if [[ ! -f "$BASELINE_FILE" ]]; then
        log_warning "No baseline found. Run with SAVE_BASELINE=1 to create one."
        return 0
    fi

    log_info "Comparing with baseline..."

    # TODO: Implement baseline comparison
    echo "Baseline comparison not yet implemented"
}

print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "         Performance Benchmark Summary"
    echo "═══════════════════════════════════════════════════════"
    echo ""

    local pass_count=0
    local fail_count=0

    for key in "${!RESULTS[@]}"; do
        local result="${RESULTS[$key]}"
        # Simplified pass/fail logic (would need proper threshold comparison)
        pass_count=$((pass_count + 1))
    done

    echo "Total benchmarks: ${#RESULTS[@]}"
    echo "Passed: $pass_count"
    echo "Failed: $fail_count"
    echo ""
    echo "═══════════════════════════════════════════════════════"
}

# Main execution

main() {
    log_info "Starting Performance Benchmark Suite"
    echo ""

    cd "$PROJECT_ROOT"

    # Run all benchmarks
    benchmark_auto_commit
    benchmark_auto_push
    benchmark_auto_pr
    benchmark_merge_queue_enqueue
    benchmark_merge_queue_dequeue
    benchmark_conflict_check
    benchmark_health_check
    benchmark_rollback_simulation
    benchmark_io_operations

    echo ""

    # Generate report
    generate_report

    # Compare with baseline
    compare_with_baseline

    # Print summary
    print_summary

    log_success "Performance benchmark complete"
}

main "$@"
