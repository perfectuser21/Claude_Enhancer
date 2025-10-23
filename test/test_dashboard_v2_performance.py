#!/usr/bin/env python3
"""
Performance tests for Dashboard v2

Validates:
- API response time <500ms
- Parser performance <100ms
- Caching effectiveness

Version: 7.2.0
"""

import sys
import time
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from parsers import CapabilityParser, LearningSystemParser, FeatureParser, ProjectMonitor
from cache import SimpleCache


def measure_time(func, *args, **kwargs):
    """Measure function execution time"""
    start = time.time()
    result = func(*args, **kwargs)
    duration = (time.time() - start) * 1000  # Convert to ms
    return result, duration


def test_capability_parser_performance():
    """Test CapabilityParser performance"""
    project_root = Path(__file__).parent.parent
    parser = CapabilityParser(project_root / "docs" / "CAPABILITY_MATRIX.md")

    result, duration = measure_time(parser.parse)

    print(f"✓ CapabilityParser.parse(): {duration:.2f}ms", end="")

    if duration < 100:
        print(f" (PASS - target <100ms)")
        return True
    else:
        print(f" (FAIL - exceeded 100ms target)")
        return False


def test_learning_system_parser_performance():
    """Test LearningSystemParser performance"""
    project_root = Path(__file__).parent.parent
    parser = LearningSystemParser(project_root)

    # Test decisions parsing
    result1, duration1 = measure_time(parser.parse_decisions)
    print(f"✓ LearningSystemParser.parse_decisions(): {duration1:.2f}ms", end="")

    # Test memory cache parsing
    result2, duration2 = measure_time(parser.parse_memory_cache)
    print(f", parse_memory_cache(): {duration2:.2f}ms", end="")

    total = duration1 + duration2

    if total < 100:
        print(f" (PASS - total {total:.2f}ms < 100ms)")
        return True
    else:
        print(f" (FAIL - total {total:.2f}ms exceeded 100ms)")
        return False


def test_feature_parser_performance():
    """Test FeatureParser performance"""
    project_root = Path(__file__).parent.parent
    parser = FeatureParser(project_root / "tools" / "web" / "dashboard.html")

    result, duration = measure_time(parser.parse)

    print(f"✓ FeatureParser.parse(): {duration:.2f}ms", end="")

    if duration < 50:
        print(f" (PASS - target <50ms)")
        return True
    else:
        print(f" (FAIL - exceeded 50ms target)")
        return False


def test_project_monitor_performance():
    """Test ProjectMonitor performance"""
    project_root = Path(__file__).parent.parent
    monitor = ProjectMonitor(project_root)

    result, duration = measure_time(monitor.get_project_status)

    print(f"✓ ProjectMonitor.get_project_status(): {duration:.2f}ms", end="")

    if duration < 100:
        print(f" (PASS - target <100ms)")
        return True
    else:
        print(f" (FAIL - exceeded 100ms target)")
        return False


def test_cache_effectiveness():
    """Test caching improves performance"""
    cache = SimpleCache(ttl_seconds=60)

    expensive_call_count = 0

    def expensive_operation():
        nonlocal expensive_call_count
        expensive_call_count += 1
        time.sleep(0.05)  # Simulate 50ms operation
        return "result"

    # First call (cache miss)
    start1 = time.time()
    result1 = cache.get_or_compute('test_key', expensive_operation)
    duration1 = (time.time() - start1) * 1000

    # Second call (cache hit)
    start2 = time.time()
    result2 = cache.get_or_compute('test_key', expensive_operation)
    duration2 = (time.time() - start2) * 1000

    print(f"✓ Cache: first call {duration1:.2f}ms, second call {duration2:.2f}ms", end="")

    # Cache should be significantly faster
    if duration2 < duration1 / 5 and expensive_call_count == 1:
        print(f" (PASS - cache hit {(duration1/duration2):.1f}x faster)")
        return True
    else:
        print(f" (FAIL - cache not effective)")
        return False


def run_performance_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("Dashboard v2 Performance Tests")
    print("=" * 60)
    print()

    results = []

    print("Parser Performance Tests:")
    print("-" * 60)
    results.append(test_capability_parser_performance())
    results.append(test_learning_system_parser_performance())
    results.append(test_feature_parser_performance())
    results.append(test_project_monitor_performance())

    print()
    print("Caching Performance Tests:")
    print("-" * 60)
    results.append(test_cache_effectiveness())

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == '__main__':
    success = run_performance_tests()
    sys.exit(0 if success else 1)
