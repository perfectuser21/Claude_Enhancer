#!/usr/bin/env python3
"""测试Agent输出汇总器"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 安全导入模块而不是使用exec
import importlib.util
spec = importlib.util.spec_from_file_location("summarizer", "agent-output-summarizer.py")
if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

# 模拟多个agent的输出
test_agents = [
    {
        "tool": "Task",
        "subagent_type": "fullstack-engineer",
        "description": "Implement modularization",
        "output": """
## ✅ Modularization Complete!

Successfully refactored phase-controller.js into 7 modules:
- Created src/core/PhaseManager.js (357 lines)
- Created src/validators/ValidationEngine.js (416 lines)
- Created src/utils/FileOperations.js (348 lines)
- Created src/cache/CacheManager.js (285 lines)

Total: 1406 lines of code
Performance improvement: 60% faster validation

✅ All tests passing
✅ 100% backward compatibility maintained
        """,
    },
    {
        "tool": "Task",
        "subagent_type": "backend-architect",
        "description": "Implement caching system",
        "output": """
## Cache System Implementation

Implemented LRU cache with:
- In-memory caching for hot paths
- File system cache for persistent data
- TTL-based expiration
- 80% cache hit rate achieved

Created 5 files:
- src/cache/CacheManager.js
- src/cache/LRUCache.js
- src/cache/FileCache.js
- tests/cache.test.js
- docs/cache-architecture.md

Performance improvement: 75% reduction in validation time
        """,
    },
    {
        "tool": "Task",
        "subagent_type": "test-engineer",
        "description": "Optimize test suite",
        "output": """
## Test Suite Optimization Results

✅ Test execution time: 0.98s (target <10s)
✅ Coverage: 85.7% (target 80%)
✅ All 47 tests passing

Created test files:
- test/optimized_test_suite.py
- test/performance_benchmark.py
- test/modular_architecture.test.js

Added 500 lines of test code
Performance: 10x improvement in test speed
        """,
    },
    {
        "tool": "Task",
        "subagent_type": "performance-engineer",
        "description": "Implement lazy loading",
        "output": """
## Lazy Loading Implementation

Achieved 98.8% startup time reduction:
- Before: ~50ms
- After: 0.6ms

Implementation:
- Dynamic imports for all heavy components
- On-demand loading of phases
- Smart caching with LRU eviction
- Created .claude/core/lazy_engine.py
- Created .claude/core/lazy_orchestrator.py

Memory usage: 0.026MB per instance
Cache hit rate: 40-80%
        """,
    },
]


def test_summarizer():
    """测试汇总器功能"""
    print("🧪 Testing Agent Output Summarizer...")

    summarizer = AgentOutputSummarizer()

    # 处理每个agent的输出
    for agent_data in test_agents:
        print(f"  Processing {agent_data['subagent_type']}...")
        summarizer.process_agent_output(agent_data)

    # 生成报告
    report = summarizer.generate_summary_report()
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # 保存报告
    report_file = summarizer.save_summary()
    print(f"\n✅ Report saved to: {report_file}")
    print(f"✅ Latest report: .claude/LATEST_AGENT_SUMMARY.md")


if __name__ == "__main__":
    test_summarizer()
