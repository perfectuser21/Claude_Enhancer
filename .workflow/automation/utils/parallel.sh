#!/usr/bin/env bash
# Parallel Execution Utilities for Claude Enhancer v5.4.0
# Purpose: Execute independent operations in parallel for better performance
# Used by: All automation scripts that can benefit from parallelization

set -euo pipefail

# Configuration
MAX_PARALLEL_JOBS="${CE_MAX_PARALLEL:-4}"
JOB_TIMEOUT="${CE_JOB_TIMEOUT:-300}"  # 5 minutes

# Job tracking
declare -A PARALLEL_JOBS=()
declare -A JOB_RESULTS=()
declare -A JOB_EXIT_CODES=()

# Temporary directory for job outputs
JOB_OUTPUT_DIR="/tmp/ce_parallel_$$"
mkdir -p "$JOB_OUTPUT_DIR"

# Cleanup on exit
trap 'rm -rf "$JOB_OUTPUT_DIR"' EXIT

# ============================================================================
# Core Parallel Functions
# ============================================================================

parallel_run() {
    local job_id="$1"
    shift
    local cmd=("$@")

    # Check if we've reached max parallel jobs
    while [[ ${#PARALLEL_JOBS[@]} -ge $MAX_PARALLEL_JOBS ]]; do
        parallel_wait_any
        sleep 0.1
    done

    # Create output file for this job
    local output_file="${JOB_OUTPUT_DIR}/${job_id}.out"
    local error_file="${JOB_OUTPUT_DIR}/${job_id}.err"
    local exit_code_file="${JOB_OUTPUT_DIR}/${job_id}.exit"

    # Execute job in background
    (
        {
            "${cmd[@]}"
            echo $? > "$exit_code_file"
        } > "$output_file" 2> "$error_file"
    ) &

    local pid=$!
    PARALLEL_JOBS["$job_id"]=$pid

    echo "$job_id: Started (PID: $pid)"
}

parallel_wait_any() {
    # Wait for any job to complete
    for job_id in "${!PARALLEL_JOBS[@]}"; do
        local pid="${PARALLEL_JOBS[$job_id]}"

        if ! kill -0 "$pid" 2>/dev/null; then
            # Job completed
            wait "$pid" 2>/dev/null || true

            # Read exit code
            local exit_code_file="${JOB_OUTPUT_DIR}/${job_id}.exit"
            local exit_code=0
            if [[ -f "$exit_code_file" ]]; then
                exit_code=$(cat "$exit_code_file")
            fi

            JOB_EXIT_CODES["$job_id"]=$exit_code

            # Read output
            local output_file="${JOB_OUTPUT_DIR}/${job_id}.out"
            if [[ -f "$output_file" ]]; then
                JOB_RESULTS["$job_id"]=$(cat "$output_file")
            fi

            # Remove from active jobs
            unset PARALLEL_JOBS["$job_id"]

            echo "$job_id: Completed (exit code: $exit_code)"
            return 0
        fi
    done

    return 1
}

parallel_wait_all() {
    echo "Waiting for ${#PARALLEL_JOBS[@]} jobs to complete..."

    while [[ ${#PARALLEL_JOBS[@]} -gt 0 ]]; do
        parallel_wait_any
        sleep 0.1
    done

    echo "All jobs completed"
}

parallel_wait_job() {
    local job_id="$1"

    if [[ -z "${PARALLEL_JOBS[$job_id]:-}" ]]; then
        echo "Job $job_id not found or already completed"
        return 1
    fi

    local pid="${PARALLEL_JOBS[$job_id]}"

    echo "Waiting for job $job_id (PID: $pid)..."

    wait "$pid" 2>/dev/null || true

    # Read exit code
    local exit_code_file="${JOB_OUTPUT_DIR}/${job_id}.exit"
    local exit_code=0
    if [[ -f "$exit_code_file" ]]; then
        exit_code=$(cat "$exit_code_file")
    fi

    JOB_EXIT_CODES["$job_id"]=$exit_code

    # Read output
    local output_file="${JOB_OUTPUT_DIR}/${job_id}.out"
    if [[ -f "$output_file" ]]; then
        JOB_RESULTS["$job_id"]=$(cat "$output_file")
    fi

    # Remove from active jobs
    unset PARALLEL_JOBS["$job_id"]

    echo "$job_id: Completed (exit code: $exit_code)"
    return $exit_code
}

# ============================================================================
# Job Status and Results
# ============================================================================

get_job_status() {
    local job_id="$1"

    if [[ -n "${PARALLEL_JOBS[$job_id]:-}" ]]; then
        echo "running"
    elif [[ -n "${JOB_EXIT_CODES[$job_id]:-}" ]]; then
        echo "completed"
    else
        echo "unknown"
    fi
}

get_job_result() {
    local job_id="$1"

    if [[ -n "${JOB_RESULTS[$job_id]:-}" ]]; then
        echo "${JOB_RESULTS[$job_id]}"
        return 0
    fi

    return 1
}

get_job_exit_code() {
    local job_id="$1"

    if [[ -n "${JOB_EXIT_CODES[$job_id]:-}" ]]; then
        echo "${JOB_EXIT_CODES[$job_id]}"
        return 0
    fi

    echo "255"  # Unknown
    return 1
}

list_active_jobs() {
    echo "Active jobs: ${#PARALLEL_JOBS[@]}"

    for job_id in "${!PARALLEL_JOBS[@]}"; do
        local pid="${PARALLEL_JOBS[$job_id]}"
        echo "  $job_id: PID $pid"
    done
}

list_completed_jobs() {
    echo "Completed jobs: ${#JOB_EXIT_CODES[@]}"

    for job_id in "${!JOB_EXIT_CODES[@]}"; do
        local exit_code="${JOB_EXIT_CODES[$job_id]}"
        echo "  $job_id: exit code $exit_code"
    done
}

# ============================================================================
# Batch Operations
# ============================================================================

parallel_foreach() {
    local items=("$@")
    local func_name="${items[0]}"
    unset items[0]

    local job_index=0

    for item in "${items[@]}"; do
        local job_id="foreach_${job_index}"
        parallel_run "$job_id" "$func_name" "$item"
        job_index=$((job_index + 1))
    done

    parallel_wait_all

    # Check results
    local failed=0
    for job_id in "${!JOB_EXIT_CODES[@]}"; do
        if [[ "${JOB_EXIT_CODES[$job_id]}" != "0" ]]; then
            failed=$((failed + 1))
        fi
    done

    if [[ $failed -gt 0 ]]; then
        echo "Warning: $failed jobs failed"
        return 1
    fi

    return 0
}

parallel_map() {
    local func_name="$1"
    shift
    local items=("$@")

    local results=()
    local job_index=0

    # Start all jobs
    for item in "${items[@]}"; do
        local job_id="map_${job_index}"
        parallel_run "$job_id" "$func_name" "$item"
        job_index=$((job_index + 1))
    done

    # Wait for all jobs
    parallel_wait_all

    # Collect results
    for i in $(seq 0 $((job_index - 1))); do
        local job_id="map_${i}"
        results+=("${JOB_RESULTS[$job_id]:-}")
    done

    # Output results
    printf '%s\n' "${results[@]}"
}

# ============================================================================
# Pipeline Support
# ============================================================================

parallel_pipeline() {
    local stages=("$@")
    local input=""

    for stage in "${stages[@]}"; do
        local job_id="pipeline_${RANDOM}"

        if [[ -z "$input" ]]; then
            # First stage
            parallel_run "$job_id" bash -c "$stage"
        else
            # Subsequent stages
            parallel_run "$job_id" bash -c "echo '$input' | $stage"
        fi

        parallel_wait_job "$job_id"
        input="${JOB_RESULTS[$job_id]}"
    done

    echo "$input"
}

# ============================================================================
# Timeout Support
# ============================================================================

parallel_run_with_timeout() {
    local timeout="$1"
    local job_id="$2"
    shift 2
    local cmd=("$@")

    # Start job
    parallel_run "$job_id" "${cmd[@]}"

    local pid="${PARALLEL_JOBS[$job_id]}"
    local start_time=$(date +%s)

    # Monitor for timeout
    (
        while kill -0 "$pid" 2>/dev/null; do
            local elapsed=$(($(date +%s) - start_time))

            if [[ $elapsed -gt $timeout ]]; then
                echo "Job $job_id timed out after ${timeout}s, killing..."
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                kill -KILL "$pid" 2>/dev/null || true

                echo "255" > "${JOB_OUTPUT_DIR}/${job_id}.exit"
                echo "TIMEOUT" > "${JOB_OUTPUT_DIR}/${job_id}.err"
                return 1
            fi

            sleep 1
        done
    ) &
}

# ============================================================================
# Error Handling
# ============================================================================

parallel_stop_all() {
    echo "Stopping all parallel jobs..."

    for job_id in "${!PARALLEL_JOBS[@]}"; do
        local pid="${PARALLEL_JOBS[$job_id]}"

        echo "Stopping job $job_id (PID: $pid)"
        kill -TERM "$pid" 2>/dev/null || true
    done

    sleep 2

    # Force kill if still running
    for job_id in "${!PARALLEL_JOBS[@]}"; do
        local pid="${PARALLEL_JOBS[$job_id]}"

        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing job $job_id (PID: $pid)"
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done

    PARALLEL_JOBS=()
}

get_failed_jobs() {
    local failed=()

    for job_id in "${!JOB_EXIT_CODES[@]}"; do
        if [[ "${JOB_EXIT_CODES[$job_id]}" != "0" ]]; then
            failed+=("$job_id")
        fi
    done

    printf '%s\n' "${failed[@]}"
}

# ============================================================================
# Specialized Parallel Operations
# ============================================================================

parallel_git_fetch() {
    local remotes=("$@")

    if [[ ${#remotes[@]} -eq 0 ]]; then
        remotes=($(git remote))
    fi

    for remote in "${remotes[@]}"; do
        parallel_run "fetch_${remote}" git fetch "$remote"
    done

    parallel_wait_all

    # Check results
    local failed=$(get_failed_jobs)
    if [[ -n "$failed" ]]; then
        echo "Failed to fetch from: $failed"
        return 1
    fi

    return 0
}

parallel_file_check() {
    local files=("$@")
    local results=()

    for file in "${files[@]}"; do
        parallel_run "check_${file//\//_}" bash -c "[[ -f '$file' ]] && echo 'exists' || echo 'missing'"
    done

    parallel_wait_all

    # Collect results
    for file in "${files[@]}"; do
        local job_id="check_${file//\//_}"
        local result="${JOB_RESULTS[$job_id]:-missing}"
        results+=("$file: $result")
    done

    printf '%s\n' "${results[@]}"
}

parallel_command_check() {
    local commands=("$@")
    local results=()

    for cmd in "${commands[@]}"; do
        parallel_run "cmd_${cmd}" bash -c "command -v '$cmd' >/dev/null && echo 'installed' || echo 'missing'"
    done

    parallel_wait_all

    # Collect results
    for cmd in "${commands[@]}"; do
        local job_id="cmd_${cmd}"
        local result="${JOB_RESULTS[$job_id]:-missing}"
        results+=("$cmd: $result")
    done

    printf '%s\n' "${results[@]}"
}

# ============================================================================
# Performance Monitoring
# ============================================================================

get_parallel_stats() {
    cat <<EOF
Parallel Execution Statistics:
  Active Jobs:    ${#PARALLEL_JOBS[@]}
  Completed Jobs: ${#JOB_EXIT_CODES[@]}
  Max Parallel:   $MAX_PARALLEL_JOBS
  Job Timeout:    ${JOB_TIMEOUT}s
EOF
}

# ============================================================================
# Export Functions
# ============================================================================

export -f parallel_run
export -f parallel_wait_any
export -f parallel_wait_all
export -f parallel_wait_job
export -f get_job_status
export -f get_job_result
export -f get_job_exit_code
export -f parallel_foreach
export -f parallel_map
export -f parallel_stop_all
export -f parallel_git_fetch
export -f parallel_file_check
export -f parallel_command_check
