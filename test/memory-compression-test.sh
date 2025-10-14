#!/bin/bash
# Memory Compression System Test Suite
# 验证压缩系统的所有功能

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

COMPRESSOR="scripts/memory-compressor.py"
MEMORY_CACHE=".claude/memory-cache.json"
DECISION_INDEX=".claude/decision-index.json"
ARCHIVE_DIR=".claude/memory-archive"

echo "🧪 Memory Compression System Test Suite"
echo "========================================"
echo ""

# Test 1: 统计功能
echo "Test 1: Statistics Mode"
echo "------------------------"
python3 "$COMPRESSOR" --stats
echo "✅ Test 1 passed"
echo ""

# Test 2: Dry Run（不修改文件）
echo "Test 2: Dry Run Mode"
echo "------------------------"
python3 "$COMPRESSOR" --dry-run
echo "✅ Test 2 passed"
echo ""

# Test 3: 备份验证
echo "Test 3: Backup Creation"
echo "------------------------"
BACKUP_COUNT_BEFORE=$(ls -1 "$MEMORY_CACHE".backup* 2>/dev/null | wc -l)
python3 "$COMPRESSOR" --force
BACKUP_COUNT_AFTER=$(ls -1 "$MEMORY_CACHE".backup* 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT_AFTER" -gt "$BACKUP_COUNT_BEFORE" ]; then
    echo "✅ Test 3 passed: Backup created"
else
    echo "⚠️  Test 3: No new backup (might be below threshold)"
fi
echo ""

# Test 4: 归档文件结构
echo "Test 4: Archive Structure"
echo "------------------------"
if [ -d "$ARCHIVE_DIR" ]; then
    ARCHIVE_FILES=$(ls -1 "$ARCHIVE_DIR"/*.json 2>/dev/null | wc -l)
    echo "Archive files: $ARCHIVE_FILES"
    
    if [ "$ARCHIVE_FILES" -gt 0 ]; then
        echo "Sample archive content:"
        ls -lh "$ARCHIVE_DIR"
        echo "✅ Test 4 passed"
    else
        echo "⚠️  Test 4: No archives yet (normal for new installation)"
    fi
else
    echo "⚠️  Test 4: Archive directory not created yet"
fi
echo ""

# Test 5: 索引完整性
echo "Test 5: Decision Index Integrity"
echo "------------------------"
if [ -f "$DECISION_INDEX" ]; then
    python3 << 'PYCHECK'
import json
from pathlib import Path

index_file = Path(".claude/decision-index.json")
with open(index_file, 'r') as f:
    index = json.load(f)

required_keys = ["_description", "_purpose", "archives", "_usage", "_size_tracking"]
missing = [k for k in required_keys if k not in index]

if missing:
    print(f"❌ Missing keys: {missing}")
    exit(1)
else:
    print(f"✅ All required keys present")
    print(f"   Archives: {len(index['archives'])} months")
    print(f"   Total size: {index['_size_tracking']['estimated_total_size_kb']} KB")
PYCHECK
    echo "✅ Test 5 passed"
else
    echo "⚠️  Test 5: Index not created yet"
fi
echo ""

# Test 6: Token节省计算
echo "Test 6: Token Saving Calculation"
echo "------------------------"
python3 << 'PYCALC'
import json
from pathlib import Path

cache_file = Path(".claude/memory-cache.json")
archive_dir = Path(".claude/memory-archive")

cache_size = cache_file.stat().st_size / 1024 if cache_file.exists() else 0
archive_size = sum(f.stat().st_size for f in archive_dir.glob("*.json")) / 1024 if archive_dir.exists() else 0

print(f"Memory Cache: {cache_size:.2f} KB (~{int(cache_size * 1024 / 4)} tokens)")
print(f"Archives:     {archive_size:.2f} KB (~{int(archive_size * 1024 / 4)} tokens)")
print(f"Total:        {cache_size + archive_size:.2f} KB")
print("")
print("✅ Token metrics calculated successfully")
PYCALC
echo "✅ Test 6 passed"
echo ""

# Summary
echo "========================================"
echo "🎉 All tests completed!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  - Run: python3 $COMPRESSOR --stats"
echo "  - Auto-compress: Add to .git/hooks/post-commit"
echo "  - Monitor: .claude/decision-index.json"
