#!/bin/bash
# Local Coverage Verification Script
# Quick check before pushing to CI
# Version: 1.0.0

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THRESHOLD=80

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Local Coverage Verification"
echo "  Quick check before CI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$PROJECT_ROOT"

# ═══════════════════════════════════════
# Step 1: JavaScript Coverage
# ═══════════════════════════════════════
echo -e "${BLUE}Step 1: Checking JavaScript Coverage...${NC}"

if [[ -f package.json ]]; then
    echo "  Running Jest with coverage..."
    npm run test:coverage -- --silent --ci || {
        echo -e "${RED}❌ JavaScript tests failed${NC}"
        exit 1
    }

    # Quick check
    if [[ -f coverage/lcov.info ]]; then
        # Count lines
        TOTAL_LINES=$(grep -c "^DA:" coverage/lcov.info || echo "0")
        COVERED_LINES=$(grep "^DA:" coverage/lcov.info | grep -v ",0$" | wc -l || echo "0")

        if [[ $TOTAL_LINES -gt 0 ]]; then
            JS_COVERAGE=$(awk "BEGIN {printf \"%.2f\", ($COVERED_LINES / $TOTAL_LINES) * 100}")
            echo -e "  JavaScript Coverage: ${JS_COVERAGE}%"

            if (( $(echo "$JS_COVERAGE < $THRESHOLD" | bc -l) )); then
                echo -e "${RED}  ❌ Below threshold ${THRESHOLD}%${NC}"
                exit 1
            else
                echo -e "${GREEN}  ✓ Above threshold ${THRESHOLD}%${NC}"
            fi
        fi
    fi
else
    echo -e "${YELLOW}  ⚠  No package.json, skipping JS coverage${NC}"
fi

echo ""

# ═══════════════════════════════════════
# Step 2: Python Coverage
# ═══════════════════════════════════════
echo -e "${BLUE}Step 2: Checking Python Coverage...${NC}"

if command -v pytest &> /dev/null && command -v coverage &> /dev/null; then
    # Check for Python files
    if find src -name "*.py" 2>/dev/null | grep -q .; then
        echo "  Running pytest with coverage..."

        pytest \
            --cov=src \
            --cov-report=term-missing \
            --cov-fail-under=$THRESHOLD \
            --quiet \
            test/ || {
            echo -e "${RED}❌ Python tests failed or coverage below ${THRESHOLD}%${NC}"
            exit 1
        }

        echo -e "${GREEN}  ✓ Python coverage above ${THRESHOLD}%${NC}"
    else
        echo -e "${YELLOW}  ⚠  No Python files found${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠  pytest or coverage not installed${NC}"
fi

echo ""

# ═══════════════════════════════════════
# Step 3: Summary
# ═══════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Coverage Verification PASSED${NC}"
echo ""
echo "Next steps:"
echo "  1. Review HTML reports:"
echo "     - JavaScript: coverage/lcov-report/index.html"
echo "     - Python: coverage/htmlcov-python/index.html"
echo ""
echo "  2. If satisfied, commit and push"
echo "     CI will run the same checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
