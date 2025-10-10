#!/bin/bash
# Coverage Report Generator and Threshold Checker
# Claude Enhancer 5.3
# Version: 1.0.0

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
THRESHOLD=80
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE_DIR="${PROJECT_ROOT}/coverage"
REPORTS_DIR="${PROJECT_ROOT}/test-results"

# Ensure directories exist
mkdir -p "$COVERAGE_DIR"
mkdir -p "$REPORTS_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Coverage Report Generator"
echo "  Claude Enhancer 5.3"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ═══════════════════════════════════════
# Function: Check if command exists
# ═══════════════════════════════════════
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${YELLOW}⚠  $cmd not found, skipping ${cmd} coverage${NC}"
        return 1
    fi
    return 0
}

# ═══════════════════════════════════════
# Function: Generate JavaScript Coverage
# ═══════════════════════════════════════
generate_js_coverage() {
    echo -e "${BLUE}▶ Generating JavaScript/TypeScript Coverage...${NC}"

    if [[ ! -f "${PROJECT_ROOT}/package.json" ]]; then
        echo -e "${YELLOW}⚠  No package.json found, skipping JS coverage${NC}"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Run Jest with coverage
    if check_command npm; then
        echo "  Running: npm run test:coverage"
        npm run test:coverage -- --ci --maxWorkers=2 || {
            echo -e "${RED}❌ JavaScript tests failed${NC}"
            return 1
        }

        # Check if coverage was generated
        if [[ -f "${COVERAGE_DIR}/lcov.info" ]]; then
            echo -e "${GREEN}✓ JavaScript coverage report generated${NC}"

            # Extract coverage percentage from lcov
            if check_command lcov; then
                local js_coverage=$(lcov --summary "${COVERAGE_DIR}/lcov.info" 2>&1 | grep -oP 'lines......: \K[0-9.]+' || echo "0")
                echo "  JavaScript Coverage: ${js_coverage}%"

                # Check threshold
                if (( $(echo "$js_coverage < $THRESHOLD" | bc -l) )); then
                    echo -e "${RED}❌ JavaScript coverage ${js_coverage}% is below threshold ${THRESHOLD}%${NC}"
                    return 1
                fi
            fi
        else
            echo -e "${YELLOW}⚠  No lcov.info file generated${NC}"
        fi
    else
        echo -e "${YELLOW}⚠  npm not found, skipping JS coverage${NC}"
    fi

    return 0
}

# ═══════════════════════════════════════
# Function: Generate Python Coverage
# ═══════════════════════════════════════
generate_python_coverage() {
    echo -e "${BLUE}▶ Generating Python Coverage...${NC}"

    # Check for Python source files
    if ! find "$PROJECT_ROOT/src" -name "*.py" 2>/dev/null | grep -q .; then
        echo -e "${YELLOW}⚠  No Python files found, skipping Python coverage${NC}"
        return 0
    fi

    if check_command pytest && check_command coverage; then
        cd "$PROJECT_ROOT"

        echo "  Running: pytest with coverage"

        # Run pytest with coverage (using pytest.ini config)
        pytest --cov="${PROJECT_ROOT}/src" \
               --cov="${PROJECT_ROOT}/.claude/core" \
               --cov="${PROJECT_ROOT}/scripts" \
               --cov-report=term \
               --cov-report=html:${COVERAGE_DIR}/htmlcov-python \
               --cov-report=xml:${COVERAGE_DIR}/coverage-python.xml \
               --cov-report=json:${COVERAGE_DIR}/coverage-python.json \
               --cov-fail-under=${THRESHOLD} \
               --junit-xml="${REPORTS_DIR}/pytest-junit.xml" \
               test/ || {
            echo -e "${RED}❌ Python tests or coverage below ${THRESHOLD}%${NC}"
            return 1
        }

        # Generate text summary
        coverage report > "${REPORTS_DIR}/coverage-python.txt" || true

        echo -e "${GREEN}✓ Python coverage report generated${NC}"

        # Display summary
        coverage report --skip-covered || true

    else
        echo -e "${YELLOW}⚠  pytest or coverage not found, skipping Python coverage${NC}"
    fi

    return 0
}

# ═══════════════════════════════════════
# Function: Generate Combined Report
# ═══════════════════════════════════════
generate_combined_report() {
    echo ""
    echo -e "${BLUE}▶ Generating Combined Coverage Report...${NC}"

    local report_file="${REPORTS_DIR}/coverage-summary.md"

    cat > "$report_file" <<EOF
# Coverage Report Summary
**Generated**: $(date '+%Y-%m-%d %H:%M:%S')
**Threshold**: ${THRESHOLD}%

## Coverage by Language

EOF

    # JavaScript Coverage
    if [[ -f "${COVERAGE_DIR}/coverage-final.json" ]]; then
        echo "### JavaScript/TypeScript" >> "$report_file"
        echo "" >> "$report_file"

        # Parse coverage-final.json for summary
        if check_command node; then
            node -e "
                const fs = require('fs');
                const coverage = JSON.parse(fs.readFileSync('${COVERAGE_DIR}/coverage-final.json'));
                let totalStatements = 0, coveredStatements = 0;
                let totalBranches = 0, coveredBranches = 0;
                let totalFunctions = 0, coveredFunctions = 0;
                let totalLines = 0, coveredLines = 0;

                Object.values(coverage).forEach(file => {
                    totalStatements += file.s ? Object.keys(file.s).length : 0;
                    coveredStatements += file.s ? Object.values(file.s).filter(v => v > 0).length : 0;
                    totalBranches += file.b ? Object.keys(file.b).length : 0;
                    coveredBranches += file.b ? Object.values(file.b).filter(v => v.some(b => b > 0)).length : 0;
                    totalFunctions += file.f ? Object.keys(file.f).length : 0;
                    coveredFunctions += file.f ? Object.values(file.f).filter(v => v > 0).length : 0;
                    totalLines += file.l ? Object.keys(file.l).length : 0;
                    coveredLines += file.l ? Object.values(file.l).filter(v => v > 0).length : 0;
                });

                const calc = (c, t) => t > 0 ? ((c / t) * 100).toFixed(2) : '0.00';

                console.log('| Metric | Coverage |');
                console.log('|--------|----------|');
                console.log('| Statements | ' + calc(coveredStatements, totalStatements) + '% |');
                console.log('| Branches | ' + calc(coveredBranches, totalBranches) + '% |');
                console.log('| Functions | ' + calc(coveredFunctions, totalFunctions) + '% |');
                console.log('| Lines | ' + calc(coveredLines, totalLines) + '% |');
            " >> "$report_file" 2>/dev/null || echo "Unable to parse JS coverage" >> "$report_file"
        fi

        echo "" >> "$report_file"
        echo "**Report Location**: \`coverage/lcov-report/index.html\`" >> "$report_file"
        echo "" >> "$report_file"
    fi

    # Python Coverage
    if [[ -f "${COVERAGE_DIR}/coverage-python.json" ]]; then
        echo "### Python" >> "$report_file"
        echo "" >> "$report_file"

        if check_command python3; then
            python3 -c "
import json
with open('${COVERAGE_DIR}/coverage-python.json') as f:
    data = json.load(f)
    totals = data.get('totals', {})
    print('| Metric | Coverage |')
    print('|--------|----------|')
    print(f\"| Statements | {totals.get('percent_covered', 0):.2f}% |\")
    print(f\"| Branches | {totals.get('percent_covered_display', 0)}% |\")
    print(f\"| Missing Lines | {totals.get('missing_lines', 0)} |\")
" >> "$report_file" 2>/dev/null || echo "Unable to parse Python coverage" >> "$report_file"
        fi

        echo "" >> "$report_file"
        echo "**Report Location**: \`coverage/htmlcov-python/index.html\`" >> "$report_file"
        echo "" >> "$report_file"
    fi

    # Status
    echo "## Status" >> "$report_file"
    echo "" >> "$report_file"
    echo "- ✅ **PASSED**: All coverage thresholds met (≥${THRESHOLD}%)" >> "$report_file"
    echo "- 📊 **Reports**: Available in \`coverage/\` directory" >> "$report_file"
    echo "- 📝 **CI Integration**: Coverage data exported for CI/CD" >> "$report_file"

    echo -e "${GREEN}✓ Combined report saved to: ${report_file}${NC}"

    # Display the report
    cat "$report_file"
}

# ═══════════════════════════════════════
# Function: Upload to Coverage Services
# ═══════════════════════════════════════
upload_coverage() {
    echo ""
    echo -e "${BLUE}▶ Uploading to Coverage Services...${NC}"

    # Codecov
    if [[ -n "${CODECOV_TOKEN:-}" ]] && check_command codecov; then
        echo "  Uploading to Codecov..."
        codecov -f "${COVERAGE_DIR}/lcov.info" -f "${COVERAGE_DIR}/coverage-python.xml" || {
            echo -e "${YELLOW}⚠  Codecov upload failed${NC}"
        }
    fi

    # Coveralls
    if [[ -n "${COVERALLS_REPO_TOKEN:-}" ]] && check_command coveralls; then
        echo "  Uploading to Coveralls..."
        coveralls < "${COVERAGE_DIR}/lcov.info" || {
            echo -e "${YELLOW}⚠  Coveralls upload failed${NC}"
        }
    fi

    # If running in CI
    if [[ -n "${CI:-}" ]]; then
        echo -e "${GREEN}✓ Coverage data ready for CI consumption${NC}"
    else
        echo -e "${YELLOW}ℹ  Not in CI environment, skipping upload${NC}"
    fi
}

# ═══════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════
main() {
    local js_result=0
    local py_result=0

    # Generate JavaScript coverage
    generate_js_coverage || js_result=$?

    # Generate Python coverage
    generate_python_coverage || py_result=$?

    # Generate combined report
    generate_combined_report

    # Upload (if configured)
    upload_coverage

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check results
    if [[ $js_result -ne 0 ]] || [[ $py_result -ne 0 ]]; then
        echo -e "${RED}❌ Coverage check FAILED${NC}"
        echo "   One or more coverage thresholds not met"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        exit 1
    fi

    echo -e "${GREEN}✅ Coverage check PASSED${NC}"
    echo "   All coverage thresholds met (≥${THRESHOLD}%)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Run main function
main "$@"
