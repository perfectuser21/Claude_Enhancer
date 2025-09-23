#!/bin/bash
# 优化后的性能基准测试

echo "🏃 Running optimized performance benchmark..."

# 测试Hook性能
echo -e "\n📊 Hook Performance:"
for hook in smart_agent_selector_optimized performance_monitor_optimized; do
    if [ -f ".claude/hooks/${hook}.sh" ]; then
        START=$(date +%s%N)
        bash ".claude/hooks/${hook}.sh" > /dev/null 2>&1
        END=$(date +%s%N)
        ELAPSED=$((($END - $START) / 1000000))
        echo "  $hook: ${ELAPSED}ms"
    fi
done

# 测试Git Hook性能
echo -e "\n📊 Git Hook Performance:"
if [ -f ".git/hooks/pre-commit-optimized" ]; then
    START=$(date +%s%N)
    bash .git/hooks/pre-commit-optimized > /dev/null 2>&1
    END=$(date +%s%N)
    ELAPSED=$((($END - $START) / 1000000))
    echo "  pre-commit-optimized: ${ELAPSED}ms"
fi

# 测试配置验证
echo -e "\n📊 Config Validation:"
START=$(date +%s%N)
python3 .claude/config/config_validator_fixed.py validate > /dev/null 2>&1
END=$(date +%s%N)
ELAPSED=$((($END - $START) / 1000000))
echo "  config validation: ${ELAPSED}ms"

echo -e "\n✅ Benchmark complete"
