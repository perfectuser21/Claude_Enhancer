#!/bin/bash
# CI/CD Performance Benchmarking Tool
# Measures and reports on workflow and hook performance

set -euo pipefail

# Colors
_RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_DIR=".temp/analysis"
METRICS_DIR=".temp/metrics"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}⚡ CI/CD Performance Benchmark${NC}"
echo "================================"
echo ""

# Create directories
mkdir -p "$REPORT_DIR" "$METRICS_DIR"

# Function to measure execution time
measure_time() {
    local name="$1"
    local command="$2"

    echo -e "${YELLOW}📊 Measuring: $name${NC}"

    start=$(date +%s%N)
    eval "$command" >/dev/null 2>&1 || true
    end=$(date +%s%N)

    duration=$(( (end - start) / 1000000 ))
    echo "  Duration: ${duration}ms"
    echo "$duration" > "$METRICS_DIR/${name// /_}.txt"

    return 0
}

# 1. Git Hooks Performance
echo -e "${BLUE}🪝 Testing Git Hooks Performance${NC}"
echo "--------------------------------"

if [ ! -f ".git/hooks/pre-commit" ]; then
    echo "Installing hooks..."
    if [ -f ".claude/install.sh" ]; then
        bash .claude/install.sh >/dev/null 2>&1
    fi
fi

# Pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "test_$(date +%s)" > test_benchmark.txt
    git add test_benchmark.txt 2>/dev/null || true

    measure_time "Pre-commit Hook" "bash .git/hooks/pre-commit < /dev/null"

    rm -f test_benchmark.txt
else
    echo "⚠️ Pre-commit hook not found"
fi

# Pre-push hook
if [ -f ".git/hooks/pre-push" ]; then
    measure_time "Pre-push Hook" "bash .git/hooks/pre-push origin refs/heads/main < /dev/null"
else
    echo "⚠️ Pre-push hook not found"
fi

echo ""

# 2. Test Suite Performance
echo -e "${BLUE}🧪 Testing Test Suite Performance${NC}"
echo "--------------------------------"

if [ -f "package.json" ]; then
    # Ensure dependencies are installed
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm ci --prefer-offline --no-audit >/dev/null 2>&1
    fi

    measure_time "Test Suite" "npm test"
    measure_time "Test Coverage" "npm run test:coverage"
else
    echo "⚠️ package.json not found"
fi

echo ""

# 3. Linting Performance
echo -e "${BLUE}🔍 Testing Linting Performance${NC}"
echo "--------------------------------"

# Shellcheck
if command -v shellcheck &> /dev/null; then
    measure_time "Shellcheck" "find . -name '*.sh' -not -path './node_modules/*' -exec shellcheck {} + 2>&1"
else
    echo "⚠️ Shellcheck not installed"
fi

# Pylint
if command -v pylint &> /dev/null; then
    py_files=$(find . -name "*.py" -not -path "./node_modules/*" -not -path "./.git/*" | head -5)
    if [ -n "$py_files" ]; then
        measure_time "Pylint" "echo '$py_files' | xargs pylint --fail-under=7.0 2>&1"
    fi
fi

# ESLint
if [ -f "package.json" ] && command -v npx &> /dev/null; then
    measure_time "ESLint" "npx eslint '**/*.js' --ignore-pattern 'node_modules/' 2>&1"
fi

echo ""

# 4. Claude Hooks Performance
echo -e "${BLUE}🔧 Testing Claude Hooks Performance${NC}"
echo "--------------------------------"

if [ -d ".claude/hooks" ]; then
    hook_count=$(ls -1 .claude/hooks/*.sh 2>/dev/null | wc -l)
    echo "Found $hook_count Claude hooks"

    # Test parallel execution
    start=$(date +%s%N)
    find .claude/hooks -name "*.sh" -type f | head -27 | xargs -P27 -I {} timeout 1s bash {} 2>/dev/null || true
    end=$(date +%s%N)
    parallel_duration=$(( (end - start) / 1000000 ))

    echo "Parallel execution (27 hooks): ${parallel_duration}ms"
    echo "$parallel_duration" > "$METRICS_DIR/claude_hooks_parallel.txt"

    # Test sequential execution
    start=$(date +%s%N)
    find .claude/hooks -name "*.sh" -type f | head -5 | while read hook; do
        timeout 1s bash "$hook" < /dev/null 2>/dev/null || true
    done
    end=$(date +%s%N)
    sequential_duration=$(( (end - start) / 1000000 ))

    echo "Sequential execution (5 hooks): ${sequential_duration}ms"
    echo "$sequential_duration" > "$METRICS_DIR/claude_hooks_sequential.txt"
else
    echo "⚠️ .claude/hooks not found"
fi

echo ""

# 5. Workflow Validation Performance
echo -e "${BLUE}📋 Testing Workflow Validation Performance${NC}"
echo "--------------------------------"

if [ -d ".github/workflows" ]; then
    workflow_count=$(ls -1 .github/workflows/*.yml 2>/dev/null | wc -l)
    echo "Found $workflow_count workflow files"

    start=$(date +%s%N)
    for yaml in .github/workflows/*.yml; do
        python3 -c "import yaml; yaml.safe_load(open('$yaml'))" 2>/dev/null || true
    done
    end=$(date +%s%N)
    duration=$(( (end - start) / 1000000 ))

    echo "Workflow YAML validation: ${duration}ms"
    echo "$duration" > "$METRICS_DIR/workflow_validation.txt"
fi

echo ""

# 6. Generate Performance Report
echo -e "${BLUE}📊 Generating Performance Report${NC}"
echo "--------------------------------"

cat > "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md" <<EOF
# ⚡ CI/CD Performance Benchmark Report

**Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Benchmark ID**: ${TIMESTAMP}

## 📊 Performance Metrics

### Git Hooks
| Component | Duration | Threshold | Status |
|-----------|----------|-----------|--------|
EOF

# Add pre-commit results
if [ -f "$METRICS_DIR/Pre-commit_Hook.txt" ]; then
    duration=$(cat "$METRICS_DIR/Pre-commit_Hook.txt")
    status="✅"
    [ $duration -gt 500 ] && status="❌"
    [ $duration -gt 300 ] && [ $duration -le 500 ] && status="⚠️"
    echo "| Pre-commit Hook | ${duration}ms | <300ms | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
fi

# Add pre-push results
if [ -f "$METRICS_DIR/Pre-push_Hook.txt" ]; then
    duration=$(cat "$METRICS_DIR/Pre-push_Hook.txt")
    status="✅"
    [ $duration -gt 1000 ] && status="⚠️"
    echo "| Pre-push Hook | ${duration}ms | <1000ms | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
fi

cat >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md" <<EOF

### Test Suite
| Component | Duration | Threshold | Status |
|-----------|----------|-----------|--------|
EOF

# Add test suite results
if [ -f "$METRICS_DIR/Test_Suite.txt" ]; then
    duration=$(cat "$METRICS_DIR/Test_Suite.txt")
    status="✅"
    [ $duration -gt 30000 ] && status="❌"
    [ $duration -gt 10000 ] && [ $duration -le 30000 ] && status="⚠️"
    echo "| Test Execution | ${duration}ms | <10s | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
fi

if [ -f "$METRICS_DIR/Test_Coverage.txt" ]; then
    duration=$(cat "$METRICS_DIR/Test_Coverage.txt")
    status="✅"
    [ $duration -gt 40000 ] && status="⚠️"
    echo "| Coverage Report | ${duration}ms | <40s | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
fi

cat >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md" <<EOF

### Linting & Quality Checks
| Component | Duration | Threshold | Status |
|-----------|----------|-----------|--------|
EOF

# Add linting results
for tool in Shellcheck Pylint ESLint; do
    file="$METRICS_DIR/${tool}.txt"
    if [ -f "$file" ]; then
        duration=$(cat "$file")
        status="✅"
        [ $duration -gt 5000 ] && status="⚠️"
        echo "| $tool | ${duration}ms | <5s | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
    fi
done

cat >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md" <<EOF

### Claude Hooks
| Component | Duration | Threshold | Status |
|-----------|----------|-----------|--------|
EOF

# Add Claude hooks results
if [ -f "$METRICS_DIR/claude_hooks_parallel.txt" ]; then
    duration=$(cat "$METRICS_DIR/claude_hooks_parallel.txt")
    status="✅"
    [ $duration -gt 500 ] && status="❌"
    [ $duration -gt 250 ] && [ $duration -le 500 ] && status="⚠️"
    echo "| Parallel Execution (27 hooks) | ${duration}ms | <250ms | $status |" >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
fi

cat >> "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md" <<EOF

## 🎯 Performance Thresholds

- ✅ **Excellent**: Within target thresholds
- ⚠️ **Acceptable**: Slightly over threshold, consider optimization
- ❌ **Poor**: Significantly over threshold, optimization required

## 📈 Recommendations

1. **Developer Experience**: Keep total feedback loop under 15s
2. **Hook Performance**: Pre-commit should be <300ms
3. **Test Performance**: Unit tests should complete in <10s
4. **Parallel Execution**: Leverage parallelization where possible

## 🔄 Continuous Improvement

- Monitor trends over time
- Profile slow operations
- Optimize bottlenecks
- Review and update thresholds

---
*Generated by CI/CD Performance Benchmark Tool*
EOF

echo -e "${GREEN}✅ Report generated: $REPORT_DIR/performance_benchmark_${TIMESTAMP}.md${NC}"
cat "$REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"

echo ""
echo -e "${GREEN}🎉 Benchmark complete!${NC}"
echo ""
echo "Metrics stored in: $METRICS_DIR/"
echo "Full report: $REPORT_DIR/performance_benchmark_${TIMESTAMP}.md"
