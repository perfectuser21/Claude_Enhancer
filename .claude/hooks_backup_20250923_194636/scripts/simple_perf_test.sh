#!/bin/bash
# Simple Performance Test Script

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Simple Performance Test${NC}"

# Setup test environment
mkdir -p simple_test_env/{src,temp}
cd simple_test_env

# Create test files
for i in {1..50}; do
    echo "console.log('test $i');" > "src/test$i.js"
    touch "temp/file$i.tmp"
    touch "temp/backup$i.bak"
done

echo "Created test files:"
echo "  JS files with debug: $(find src -name "*.js" | wc -l)"
echo "  Temp files: $(find temp -name "*.tmp" -o -name "*.bak" | wc -l)"

# Test original script
echo -e "\n${YELLOW}Testing Original Script:${NC}"
time bash $(ls /home/xx/dev/Claude Enhancer/.claude/scripts/cleanup.sh.backup.* | head -1) 5 > /dev/null 2>&1

# Reset environment
for i in {1..50}; do
    echo "console.log('test $i');" > "src/test$i.js"
    touch "temp/file$i.tmp"
    touch "temp/backup$i.bak"
done

# Test ultra script
echo -e "\n${YELLOW}Testing Ultra Script:${NC}"
time bash /home/xx/dev/Claude Enhancer/.claude/scripts/cleanup.sh 5 > /dev/null 2>&1

cd ..
rm -rf simple_test_env

echo -e "\n${GREEN}✅ Performance test completed${NC}"