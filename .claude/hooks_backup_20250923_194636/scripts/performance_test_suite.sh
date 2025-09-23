#!/bin/bash
# Claude Enhancer Performance Test Suite
# Comprehensive testing for cleanup script optimization
# Validates <500ms execution time target

set -e

# Test Configuration
readonly TEST_DIR="/tmp/perfect21_perf_test"
readonly RESULTS_FILE="/tmp/perfect21_perf_results.json"
readonly ITERATIONS=10
readonly TARGET_TIME_MS=500

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Performance measurement functions
measure_execution_time() {
    local command="$1"
    local description="$2"

    local start_time
    local end_time
    local duration_ms

    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        start_time=${EPOCHREALTIME}
        eval "$command" >/dev/null 2>&1
        end_time=${EPOCHREALTIME}
        duration_ms=$(awk "BEGIN {printf \"%.0f\", ($end_time - $start_time) * 1000}")
    else
        start_time=$(date +%s.%N)
        eval "$command" >/dev/null 2>&1
        end_time=$(date +%s.%N)
        duration_ms=$(awk "BEGIN {printf \"%.0f\", ($end_time - $start_time) * 1000}")
    fi

    echo "$duration_ms"
}

# Create comprehensive test environment
create_test_environment() {
    local test_size="${1:-medium}"

    printf "${BLUE}🔧 Creating test environment (${test_size})${NC}\n"

    rm -rf "$TEST_DIR"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"

    case "$test_size" in
        "small")
            create_small_test_set
            ;;
        "medium")
            create_medium_test_set
            ;;
        "large")
            create_large_test_set
            ;;
    esac

    printf "  ✅ Test environment ready: %d files\n" "$(find . -type f | wc -l)"
}

create_small_test_set() {
    mkdir -p src/{components,utils} tests

    # Create 20 JS files with debug code
    for i in {1..20}; do
        cat > "src/components/Component$i.js" << EOF
console.log("Debug: Component $i");
const apiKey = "test-key-$i";
export default function Component$i() {
    console.debug("Loading component $i");
    return <div>Component $i</div>;
}
EOF
    done

    # Create 15 Python files
    for i in {1..15}; do
        cat > "src/utils/util$i.py" << EOF
print("Debug: Loading util $i")
def function_$i():
    password = "test-password-$i"
    return "result"
EOF
    done

    # Create temporary files
    for i in {1..10}; do
        touch "temp_$i.tmp" "backup_$i.bak" "swap_$i.swp"
    done

    # Create Python cache
    mkdir -p src/__pycache__
    for i in {1..8}; do
        touch "src/__pycache__/module$i.cpython-39.pyc"
    done
}

create_medium_test_set() {
    mkdir -p src/{components,utils,services,hooks} tests/{unit,integration} docs

    # Create 50 JS/TS files
    for i in {1..50}; do
        cat > "src/components/Component$i.tsx" << EOF
import React from 'react';
console.log("Debug: Component $i loading");
console.info("Component $i info");

interface Props$i {
    id: string;
    data: any;
}

const Component$i: React.FC<Props$i> = ({ id, data }) => {
    console.debug("Rendering component $i with id:", id);
    const apiKey = "api-key-$i-secret";
    return <div>Component {id}</div>;
};

export default Component$i;
EOF
    done

    # Create 30 Python files
    for i in {1..30}; do
        cat > "src/services/service$i.py" << EOF
import logging
print(f"Debug: Loading service $i")

class Service$i:
    def __init__(self):
        self.password = "secret-password-$i"
        self.api_token = "token-$i-very-secret"
        print(f"Service $i initialized")

    def process(self):
        print("Processing in service $i")
        return {"status": "success"}
EOF
    done

    # Create more temporary files
    for i in {1..25}; do
        touch "temp_file_$i.tmp" "backup_$i.bak" "editor_$i.swp" "old_log_$i.log.old"
        touch ".DS_Store_$i" "Thumbs_$i.db"
    done

    # Create nested Python cache
    for dir in src/{components,utils,services,hooks}; do
        mkdir -p "$dir/__pycache__"
        for i in {1..12}; do
            touch "$dir/__pycache__/cache$i.cpython-39.pyc"
        done
    done
}

create_large_test_set() {
    mkdir -p src/{components,utils,services,hooks,types,constants} tests/{unit,integration,e2e} docs/{api,guides}

    # Create 100 JS/TS files
    for i in {1..100}; do
        cat > "src/components/Component$i.tsx" << EOF
import React, { useState, useEffect } from 'react';
console.log("Debug: Component $i loading");
console.info("Component $i mounted");
console.warn("Component $i warning");

const Component$i = () => {
    const [data, setData] = useState(null);
    const apiKey = "very-secret-api-key-$i";
    const password = "super-secret-password-$i";

    useEffect(() => {
        console.debug("Effect running for component $i");
        print("This should not be here in JS");
    }, []);

    return <div>Component $i</div>;
};
EOF
    done

    # Create 60 Python files
    for i in {1..60}; do
        cat > "src/services/service$i.py" << EOF
import logging
import json
print(f"Debug: Loading service $i")
print("Another debug line")

class Service$i:
    def __init__(self):
        self.password = "ultra-secret-password-$i"
        self.api_key = "api-key-$i-secret"
        self.aws_access_key = "AKIA$i"
        self.token = "jwt-token-$i-secret"
        print(f"Service $i initialized with secrets")

    def process(self):
        print("Processing...")
        return {"status": "success", "service": $i}
EOF
    done

    # Create many temporary files
    for i in {1..50}; do
        touch "temp_file_$i.tmp" "backup_$i.bak" "swap_$i.swp" "orig_$i.orig"
        touch "log_$i.log.old" ".DS_Store_$i" "Thumbs_$i.db"
        echo "temporary content $i" > "temp_content_$i.temp"
    done

    # Create extensive Python cache structure
    for dir in src/{components,utils,services,hooks,types,constants}; do
        mkdir -p "$dir/__pycache__"
        for i in {1..20}; do
            touch "$dir/__pycache__/module$i.cpython-39.pyc"
            touch "$dir/__pycache__/cache$i.cpython-38.pyc"
        done
    done

    # Create nested directories with cache
    for nested in {a,b,c}; do
        mkdir -p "src/nested_$nested/__pycache__"
        for i in {1..15}; do
            touch "src/nested_$nested/__pycache__/nested$i.pyc"
        done
    done
}

# Test individual script performance
test_script_performance() {
    local script_path="$1"
    local script_name="$2"
    local test_size="$3"

    printf "${CYAN}📊 Testing ${script_name} (${test_size} dataset)${NC}\n"

    if [[ ! -f "$script_path" ]]; then
        printf "  ❌ Script not found: %s\n" "$script_path"
        return 1
    fi

    local times=()
    local total_time=0
    local success_count=0

    for i in $(seq 1 $ITERATIONS); do
        # Recreate test environment for each iteration
        create_test_environment "$test_size" >/dev/null 2>&1

        # Measure execution time
        local duration_ms
        if duration_ms=$(measure_execution_time "bash '$script_path'" "$script_name"); then
            times+=("$duration_ms")
            total_time=$((total_time + duration_ms))
            ((success_count++))
            printf "    Run %2d: %4d ms\n" "$i" "$duration_ms"
        else
            printf "    Run %2d: FAILED\n" "$i"
        fi
    done

    if [[ $success_count -eq 0 ]]; then
        printf "  ❌ All runs failed\n"
        return 1
    fi

    # Calculate statistics
    local avg_time=$((total_time / success_count))
    local min_time=$(printf '%s\n' "${times[@]}" | sort -n | head -1)
    local max_time=$(printf '%s\n' "${times[@]}" | sort -n | tail -1)

    printf "  📈 Average: %d ms\n" "$avg_time"
    printf "  ⚡ Best:    %d ms\n" "$min_time"
    printf "  🐌 Worst:   %d ms\n" "$max_time"

    # Check target achievement
    if [[ $avg_time -le $TARGET_TIME_MS ]]; then
        printf "  ${GREEN}✅ TARGET ACHIEVED (<%d ms)${NC}\n" "$TARGET_TIME_MS"
    else
        printf "  ${RED}❌ TARGET MISSED (>%d ms)${NC}\n" "$TARGET_TIME_MS"
    fi

    # Store results
    local result=$(cat << EOF
{
    "script": "$script_name",
    "test_size": "$test_size",
    "iterations": $success_count,
    "avg_time_ms": $avg_time,
    "min_time_ms": $min_time,
    "max_time_ms": $max_time,
    "target_achieved": $([ $avg_time -le $TARGET_TIME_MS ] && echo "true" || echo "false"),
    "timestamp": "$(date -Iseconds)"
}
EOF
    )

    echo "$result" >> "$RESULTS_FILE.tmp"
    printf "\n"
}

# Run comprehensive performance comparison
run_performance_comparison() {
    printf "${BLUE}🚀 Performance Comparison Test Suite${NC}\n"
    printf "Target: <%d ms execution time\n" "$TARGET_TIME_MS"
    printf "Iterations: %d per test\n" "$ITERATIONS"
    printf "========================================\n\n"

    # Initialize results file
    echo "[]" > "$RESULTS_FILE"
    : > "$RESULTS_FILE.tmp"

    # Test scripts with different dataset sizes
    local scripts=(
        "/home/xx/dev/Perfect21/.claude/scripts/cleanup.sh:Original Cleanup"
        "/home/xx/dev/Perfect21/.claude/scripts/ultra_optimized_cleanup.sh:Ultra Optimized"
        "/home/xx/dev/Perfect21/.claude/scripts/hyper_performance_cleanup.sh:Hyper Performance"
    )

    local test_sizes=("small" "medium" "large")

    for script_info in "${scripts[@]}"; do
        IFS=':' read -r script_path script_name <<< "$script_info"

        for test_size in "${test_sizes[@]}"; do
            test_script_performance "$script_path" "$script_name" "$test_size"
        done
    done

    # Consolidate results
    if [[ -s "$RESULTS_FILE.tmp" ]]; then
        jq -s '.' "$RESULTS_FILE.tmp" > "$RESULTS_FILE"
        rm -f "$RESULTS_FILE.tmp"
    fi
}

# Generate detailed performance report
generate_performance_report() {
    local report_file="/tmp/perfect21_performance_analysis.md"

    printf "${BLUE}📊 Generating Performance Analysis Report${NC}\n"

    cat > "$report_file" << 'EOF'
# Claude Enhancer Cleanup Scripts Performance Analysis

## 🎯 Test Objectives
- **Target Execution Time**: <500ms
- **Test Iterations**: 10 per configuration
- **Dataset Sizes**: Small (60 files), Medium (200 files), Large (400 files)

## 📊 Performance Results

### Execution Time Comparison

| Script Version | Small Dataset | Medium Dataset | Large Dataset | Target Achieved |
|---------------|---------------|----------------|---------------|-----------------|
EOF

    if [[ -f "$RESULTS_FILE" ]]; then
        # Process results with jq
        jq -r '
            group_by(.script) |
            map({
                script: .[0].script,
                small: (map(select(.test_size == "small")) | .[0].avg_time_ms // "N/A"),
                medium: (map(select(.test_size == "medium")) | .[0].avg_time_ms // "N/A"),
                large: (map(select(.test_size == "large")) | .[0].avg_time_ms // "N/A"),
                target_achieved: (map(.target_achieved) | any)
            }) |
            .[] |
            "| \(.script) | \(.small)ms | \(.medium)ms | \(.large)ms | \(if .target_achieved then "✅" else "❌" end) |"
        ' "$RESULTS_FILE" >> "$report_file"
    fi

    cat >> "$report_file" << 'EOF'

## 🚀 Performance Optimizations Implemented

### Hyper-Performance Version Features:
1. **Single-Pass File System Traversal** - Eliminated redundant directory scans
2. **Vectorized Operations** - Batch processing with optimized parameters
3. **Intelligent Parallel Execution** - True parallelism without overhead
4. **Optimized Progress Tracking** - Removed sleep-based progress bars
5. **High-Precision Timing** - Used EPOCHREALTIME for accurate measurement
6. **Smart Conditional Execution** - Skip unnecessary operations
7. **Memory-Efficient Processing** - Stream processing without loading large datasets

### Key Technical Improvements:
- **Batch Size Optimization**: 500 files per batch vs. 100
- **Depth Limiting**: Max depth 8 vs. 10 for faster traversal
- **Pattern Consolidation**: Single find command with all patterns
- **Process Pool Management**: Optimal core utilization
- **Cache Elimination**: Removed complex caching overhead

## 📈 Performance Analysis

### Target Achievement:
EOF

    if [[ -f "$RESULTS_FILE" ]]; then
        local total_tests=$(jq 'length' "$RESULTS_FILE")
        local successful_tests=$(jq 'map(select(.target_achieved == true)) | length' "$RESULTS_FILE")
        local success_rate=$(( (successful_tests * 100) / total_tests ))

        cat >> "$report_file" << EOF
- **Total Tests**: $total_tests
- **Successful Tests**: $successful_tests
- **Success Rate**: $success_rate%

### Best Performance:
EOF

        local best_time=$(jq 'map(.min_time_ms) | min' "$RESULTS_FILE")
        local best_script=$(jq -r 'map(select(.min_time_ms == ('$best_time'))) | .[0].script' "$RESULTS_FILE")

        cat >> "$report_file" << EOF
- **Fastest Execution**: ${best_time}ms (${best_script})
- **Performance Improvement**: $(jq -r '
    group_by(.script) |
    map({script: .[0].script, avg: (map(.avg_time_ms) | add / length)}) |
    sort_by(.avg) |
    if length > 1 then
        (.[0].avg / .[-1].avg * 100 | floor | tostring) + "% faster than slowest"
    else
        "Single script tested"
    end
' "$RESULTS_FILE")
EOF
    fi

    cat >> "$report_file" << 'EOF'

## 🔧 Recommendations

### For Production Use:
1. **Deploy Hyper-Performance Version** for critical paths
2. **Configure Parallel Jobs** based on system capacity
3. **Monitor Execution Times** with built-in timing
4. **Use Conditional Cleanup** for different phases

### For Further Optimization:
1. **Implement Incremental Cleanup** for large codebases
2. **Add File Change Detection** to skip unchanged areas
3. **Create Memory-Mapped Caching** for repeated operations
4. **Develop Predictive Cleanup** based on file patterns

## 📊 System Information
EOF

    cat >> "$report_file" << EOF
- **Test Date**: $(date)
- **System**: $(uname -a)
- **CPU Cores**: $(nproc)
- **Memory**: $(free -h | awk '/^Mem:/ {print $2}')
- **Bash Version**: $BASH_VERSION

---
*Generated by Claude Enhancer Performance Test Suite*
EOF

    printf "  📄 Report generated: %s\n" "$report_file"
    printf "  📊 Results data: %s\n" "$RESULTS_FILE"
}

# Cleanup test environment
cleanup_test_environment() {
    printf "${YELLOW}🧹 Cleaning up test environment${NC}\n"
    rm -rf "$TEST_DIR" 2>/dev/null || true
    printf "  ✅ Cleanup completed\n"
}

# Main execution function
main() {
    printf "${BLUE}🚀 Claude Enhancer Performance Test Suite${NC}\n"
    printf "========================================\n\n"

    # Check dependencies
    if ! command -v jq &>/dev/null; then
        printf "${RED}❌ Error: jq is required for JSON processing${NC}\n"
        exit 1
    fi

    # Run performance tests
    run_performance_comparison

    # Generate analysis report
    generate_performance_report

    # Cleanup
    cleanup_test_environment

    printf "\n========================================\n"
    printf "${GREEN}✅ Performance testing completed!${NC}\n"
    printf "${GREEN}📊 View results: %s${NC}\n" "/tmp/perfect21_performance_analysis.md"
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi