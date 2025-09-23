#!/usr/bin/env python3
"""
Quick Hook Validation Test
Tests the fixes for Claude Enhancer hook failures
"""

import subprocess
import time
import json
import concurrent.futures
from pathlib import Path


def test_hook_execution(
    hook_path, test_input='{"tool": "test", "prompt": "validation test"}'
):
    """Test a single hook execution"""
    try:
        start_time = time.time()
        result = subprocess.run(
            ["bash", str(hook_path)],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=10,
        )
        duration = (time.time() - start_time) * 1000

        return {
            "hook": hook_path.name,
            "success": result.returncode == 0,
            "duration_ms": duration,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr),
            "error": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "hook": hook_path.name,
            "success": False,
            "duration_ms": 10000,
            "error": "Timeout after 10s",
        }
    except Exception as e:
        return {
            "hook": hook_path.name,
            "success": False,
            "duration_ms": 0,
            "error": str(e),
        }


def test_concurrent_execution(hook_path, concurrency=10):
    """Test concurrent hook execution"""
    test_input = '{"tool": "concurrent_test", "prompt": "concurrent validation test"}'

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(test_hook_execution, hook_path, test_input)
            for _ in range(concurrency)
        ]

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=15)
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        "hook": hook_path.name,
                        "success": False,
                        "error": f"Future failed: {e}",
                    }
                )

    total_time = (time.time() - start_time) * 1000
    success_count = sum(1 for r in results if r["success"])

    return {
        "hook": hook_path.name,
        "concurrency": concurrency,
        "total_time_ms": total_time,
        "success_rate": success_count / len(results) if results else 0,
        "successful_operations": success_count,
        "total_operations": len(results),
        "avg_duration_ms": sum(r.get("duration_ms", 0) for r in results) / len(results)
        if results
        else 0,
    }


def main():
    """Run validation tests"""
    print("🔧 Claude Enhancer Hook Validation Test")
    print("=" * 50)

    hook_dir = Path(".claude/hooks")

    # Test individual hook execution
    print("\n📝 Testing Individual Hook Execution...")
    hook_results = []

    test_hooks = [
        "smart_agent_selector.sh",
        "performance_monitor.sh",
        "error_handler.sh",
        "quality_gate.sh",
        "task_type_detector.sh",
    ]

    for hook_name in test_hooks:
        hook_path = hook_dir / hook_name
        if hook_path.exists():
            result = test_hook_execution(hook_path)
            hook_results.append(result)

            status = "✅" if result["success"] else "❌"
            print(f"  {status} {hook_name}: {result['duration_ms']:.1f}ms")
            if not result["success"]:
                print(f"     Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ⚠️  {hook_name}: Not found")

    # Test concurrent execution
    print("\n🔀 Testing Concurrent Hook Execution...")
    concurrent_results = []

    for hook_name in ["smart_agent_selector.sh", "performance_monitor.sh"]:
        hook_path = hook_dir / hook_name
        if hook_path.exists():
            result = test_concurrent_execution(hook_path, concurrency=5)
            concurrent_results.append(result)

            print(f"  {hook_name}:")
            print(f"    Success Rate: {result['success_rate']*100:.1f}%")
            print(f"    Avg Duration: {result['avg_duration_ms']:.1f}ms")

    # Summary
    print("\n📊 Validation Summary:")
    print("-" * 30)

    total_hooks = len(hook_results)
    successful_hooks = sum(1 for r in hook_results if r["success"])

    print(f"Individual Tests: {successful_hooks}/{total_hooks} passed")

    if concurrent_results:
        avg_concurrent_success = sum(
            r["success_rate"] for r in concurrent_results
        ) / len(concurrent_results)
        print(f"Concurrent Tests: {avg_concurrent_success*100:.1f}% success rate")

    # Check for critical issues
    critical_issues = [r for r in hook_results if not r["success"]]
    if critical_issues:
        print(f"\n🔴 Critical Issues Found: {len(critical_issues)}")
        for issue in critical_issues:
            print(f"  - {issue['hook']}: {issue.get('error', 'Failed')}")
        return 1

    # Check for performance issues
    slow_hooks = [r for r in hook_results if r.get("duration_ms", 0) > 1000]
    if slow_hooks:
        print(f"\n🟡 Performance Issues: {len(slow_hooks)} hooks > 1000ms")
        for hook in slow_hooks:
            print(f"  - {hook['hook']}: {hook['duration_ms']:.1f}ms")

    if successful_hooks == total_hooks and (
        not concurrent_results or avg_concurrent_success > 0.9
    ):
        print("\n🎉 All validation tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed - see details above")
        return 1


if __name__ == "__main__":
    exit(main())
