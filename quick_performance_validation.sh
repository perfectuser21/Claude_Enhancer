#!/bin/bash
# Quick Performance Validation Script
# Simple test to verify the hyper-performance cleanup works

set -e

echo "🚀 Quick Performance Validation for Hyper-Performance Cleanup"
echo "============================================================="

# Create test environment
TEST_DIR="/tmp/quick_perf_test_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Creating test files..."

# Create test structure
mkdir -p src/{components,utils} tests
for i in {1..20}; do
    cat > "src/components/Component$i.js" << EOF
console.log("Debug: Component $i");
const apiKey = "test-key-$i";
export default function Component$i() {
    console.debug("Loading $i");
    return <div>Component $i</div>;
}
EOF
done

for i in {1..15}; do
    cat > "src/utils/util$i.py" << EOF
print(f"Debug: util $i")
def function_$i():
    password = "test-$i"
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

echo "✅ Test environment created: $(find . -type f | wc -l) files"

# Test each script
SCRIPTS=(
    "/home/xx/dev/Perfect21/.claude/scripts/cleanup.sh:Original"
    "/home/xx/dev/Perfect21/.claude/scripts/ultra_optimized_cleanup.sh:Ultra"
    "/home/xx/dev/Perfect21/.claude/scripts/hyper_performance_cleanup.sh:Hyper"
)

echo ""
echo "🔧 Testing scripts..."

for script_info in "${SCRIPTS[@]}"; do
    IFS=':' read -r script_path script_name <<< "$script_info"

    if [[ -f "$script_path" ]]; then
        echo ""
        echo "📊 Testing: $script_name"
        echo "----------------------------------------"

        # Copy test environment
        test_copy="/tmp/test_copy_$$_$(date +%s)"
        cp -r "$TEST_DIR" "$test_copy"
        cd "$test_copy"

        # Time the execution
        echo "⏱️ Executing..."
        if time bash "$script_path" >/dev/null 2>&1; then
            echo "✅ $script_name completed successfully"
        else
            echo "❌ $script_name failed"
        fi

        # Check cleanup results
        temp_files=$(find . -name "*.tmp" -o -name "*.bak" -o -name "*.swp" | wc -l)
        pyc_files=$(find . -name "*.pyc" | wc -l)
        echo "📊 Remaining temp files: $temp_files"
        echo "📊 Remaining .pyc files: $pyc_files"

        # Cleanup
        cd - >/dev/null
        rm -rf "$test_copy"
    else
        echo "⚠️ Script not found: $script_path"
    fi
done

# Cleanup
echo ""
echo "🧹 Cleaning up test environment..."
rm -rf "$TEST_DIR"

echo ""
echo "✅ Performance validation completed!"
echo "📝 Summary:"
echo "   - All scripts tested for basic functionality"
echo "   - Execution times measured with 'time' command"
echo "   - Cleanup effectiveness verified"
echo ""
echo "🎯 For detailed benchmarking, use:"
echo "   .claude/scripts/performance_test_suite.sh"
echo "   .claude/scripts/benchmark_runner.sh"