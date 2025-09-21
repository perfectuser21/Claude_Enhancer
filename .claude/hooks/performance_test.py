#!/usr/bin/env python3
"""
Performance Test Suite for Claude Enhancer Optimizations
Tests all performance improvements and generates benchmarks
"""

import os
import sys
import time
import json
import subprocess
import threading
from typing import Dict, List, Tuple, Any
import statistics
from pathlib import Path

class PerformanceTestSuite:
    """Comprehensive performance testing for Claude Enhancer"""

    def __init__(self):
        self.results = {}
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, str]:
        """Generate test data for performance testing"""
        return {
            'simple_task': '''
            {
                "tool": "Task",
                "params": {
                    "subagent_type": "backend-architect",
                    "prompt": "Design a simple API"
                }
            }
            ''',
            'auth_task': '''
            {
                "function_calls": [
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "backend-architect",
                            "prompt": "实现用户认证系统"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "security-auditor",
                            "prompt": "审查认证安全"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "test-engineer",
                            "prompt": "设计认证测试"
                        }
                    }
                ]
            }
            ''',
            'complex_task': '''
            {
                "function_calls": [
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "backend-architect",
                            "prompt": "设计完整的微服务架构"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "database-specialist",
                            "prompt": "设计数据库架构"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "security-auditor",
                            "prompt": "全面安全审计"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "api-designer",
                            "prompt": "设计API规范"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "test-engineer",
                            "prompt": "完整测试策略"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "devops-engineer",
                            "prompt": "CI/CD部署方案"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "performance-engineer",
                            "prompt": "性能优化方案"
                        }
                    },
                    {
                        "name": "Task",
                        "parameters": {
                            "subagent_type": "monitoring-specialist",
                            "prompt": "监控告警系统"
                        }
                    }
                ]
            }
            '''
        }

    def test_hook_latency(self) -> Dict[str, float]:
        """Test hook execution latency"""
        print("🔬 Testing Hook Latency...")

        latency_results = {}

        # Test original validator
        original_times = []
        optimized_times = []

        test_input = self.test_data['auth_task']

        # Test original validator (if exists)
        original_validator = "/home/xx/dev/Perfect21/.claude/hooks/agent_validator.sh"
        if os.path.exists(original_validator):
            for _ in range(5):  # Reduced for faster testing
                start_time = time.time()
                try:
                    subprocess.run(
                        ['bash', original_validator],
                        input=test_input,
                        text=True,
                        capture_output=True,
                        timeout=5
                    )
                except:
                    pass
                original_times.append(time.time() - start_time)

        # Test optimized validator
        optimized_validator = "/home/xx/dev/Perfect21/.claude/hooks/fast_agent_validator.sh"
        for _ in range(5):  # Reduced for faster testing
            start_time = time.time()
            try:
                subprocess.run(
                    ['bash', optimized_validator],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            optimized_times.append(time.time() - start_time)

        if original_times:
            latency_results['original_avg'] = sum(original_times) / len(original_times)
            latency_results['original_p95'] = sorted(original_times)[int(len(original_times) * 0.95)]

        latency_results['optimized_avg'] = sum(optimized_times) / len(optimized_times)
        latency_results['optimized_p95'] = sorted(optimized_times)[int(len(optimized_times) * 0.95)]

        if original_times:
            improvement = (latency_results['original_avg'] - latency_results['optimized_avg']) / latency_results['original_avg'] * 100
            latency_results['improvement_percent'] = improvement

        return latency_results

    def test_cache_performance(self) -> Dict[str, Any]:
        """Test caching performance improvements"""
        print("💾 Testing Cache Performance...")

        dispatcher_path = "/home/xx/dev/Perfect21/.claude/hooks/performance_optimized_dispatcher.py"

        cache_results = {
            'first_run_times': [],
            'cached_run_times': [],
            'cache_hit_rate': 0
        }

        test_input = self.test_data['auth_task']

        # First run (cache miss)
        for _ in range(3):  # Reduced for faster testing
            start_time = time.time()
            try:
                subprocess.run(
                    ['python3', dispatcher_path],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            cache_results['first_run_times'].append(time.time() - start_time)

        # Subsequent runs (should hit cache)
        for _ in range(3):  # Reduced for faster testing
            start_time = time.time()
            try:
                subprocess.run(
                    ['python3', dispatcher_path],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            cache_results['cached_run_times'].append(time.time() - start_time)

        # Get cache statistics
        try:
            result = subprocess.run(
                ['python3', dispatcher_path, 'stats'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout:
                stats = json.loads(result.stdout)
                cache_hit_rate = stats.get('cache_hit_rate', '0%')
                if isinstance(cache_hit_rate, str):
                    cache_results['cache_hit_rate'] = float(cache_hit_rate.rstrip('%'))
                else:
                    cache_results['cache_hit_rate'] = cache_hit_rate
        except:
            pass

        cache_results['avg_first_run'] = sum(cache_results['first_run_times']) / len(cache_results['first_run_times'])
        cache_results['avg_cached_run'] = sum(cache_results['cached_run_times']) / len(cache_results['cached_run_times'])

        if cache_results['avg_first_run'] > 0:
            cache_improvement = (cache_results['avg_first_run'] - cache_results['avg_cached_run']) / cache_results['avg_first_run'] * 100
            cache_results['cache_improvement_percent'] = cache_improvement

        return cache_results

    def test_resource_usage(self) -> Dict[str, Any]:
        """Test resource usage optimization"""
        print("📊 Testing Resource Usage...")

        monitor_path = "/home/xx/dev/Perfect21/.claude/hooks/resource_monitor.py"

        # Get baseline resource usage
        try:
            result = subprocess.run(
                ['python3', monitor_path, 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            baseline = json.loads(result.stdout) if result.stdout else {}
        except:
            baseline = {}

        # Run stress test
        stress_results = self._run_stress_test()

        return {
            'baseline': baseline,
            'stress_test_results': stress_results
        }

    def _run_stress_test(self) -> Dict[str, Any]:
        """Run stress test on the system"""
        stress_results = {
            'concurrent_validations': 0,
            'total_time': 0,
            'success_rate': 0
        }

        # Run multiple validations concurrently
        def run_validation():
            validator_path = "/home/xx/dev/Perfect21/.claude/hooks/fast_agent_validator.sh"
            test_input = self.test_data['auth_task']  # Use simpler task for stress test

            try:
                result = subprocess.run(
                    ['bash', validator_path],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
            except:
                return False

        # Run 10 concurrent validations (reduced for testing)
        start_time = time.time()
        threads = []
        results = []

        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(run_validation()))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        stress_results['concurrent_validations'] = len(threads)
        stress_results['total_time'] = end_time - start_time
        stress_results['success_rate'] = (sum(results) / len(results) * 100) if results else 0

        return stress_results

    def run_quick_test(self) -> Dict[str, Any]:
        """Run quick performance test"""
        print("🚀 Running Quick Performance Test")
        print("=" * 50)

        start_time = time.time()

        results = {
            'timestamp': time.time(),
            'test_duration': 0,
            'hook_latency': {},
            'cache_performance': {},
            'resource_usage': {},
            'overall_score': 0
        }

        try:
            # Test 1: Hook Latency
            results['hook_latency'] = self.test_hook_latency()

            # Test 2: Cache Performance
            results['cache_performance'] = self.test_cache_performance()

            # Test 3: Resource Usage
            results['resource_usage'] = self.test_resource_usage()

            # Calculate overall performance score
            results['overall_score'] = self._calculate_performance_score(results)

        except Exception as e:
            results['error'] = str(e)

        results['test_duration'] = time.time() - start_time

        return results

    def _calculate_performance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        score = 0

        # Hook latency score (40 points for quick test)
        if 'improvement_percent' in results['hook_latency']:
            improvement = results['hook_latency']['improvement_percent']
            score += min(40, improvement / 2.5)  # Up to 40 points

        # Cache performance score (35 points)
        if 'cache_improvement_percent' in results['cache_performance']:
            cache_improvement = results['cache_performance']['cache_improvement_percent']
            score += min(35, cache_improvement / 2.86)  # Up to 35 points

        # Resource efficiency score (25 points)
        stress_test = results['resource_usage'].get('stress_test_results', {})
        if stress_test.get('success_rate', 0) > 80:
            score += 25

        return min(100, score)

    def generate_quick_report(self, results: Dict[str, Any]) -> str:
        """Generate quick performance report"""
        report = []
        report.append("📊 Claude Enhancer Quick Performance Test Results")
        report.append("=" * 55)
        report.append(f"Test Duration: {results['test_duration']:.2f} seconds")
        report.append(f"Performance Score: {results['overall_score']:.1f}/100")
        report.append("")

        # Hook Latency Results
        report.append("🔬 Hook Latency:")
        hook_results = results['hook_latency']
        if 'improvement_percent' in hook_results:
            report.append(f"  • Improvement: {hook_results['improvement_percent']:.1f}%")
            report.append(f"  • Original: {hook_results['original_avg']:.3f}s")
        report.append(f"  • Optimized: {hook_results['optimized_avg']:.3f}s")
        report.append("")

        # Cache Performance Results
        report.append("💾 Cache Performance:")
        cache_results = results['cache_performance']
        if 'cache_improvement_percent' in cache_results:
            report.append(f"  • Speed Improvement: {cache_results['cache_improvement_percent']:.1f}%")
        report.append(f"  • Hit Rate: {cache_results['cache_hit_rate']:.1f}%")
        report.append("")

        # Resource Usage Results
        report.append("📊 Resource Usage:")
        stress_test = results['resource_usage'].get('stress_test_results', {})
        if stress_test:
            report.append(f"  • Stress Test Success: {stress_test['success_rate']:.1f}%")
            report.append(f"  • Concurrent Tests: {stress_test['concurrent_validations']}")
        report.append("")

        # Overall Assessment
        if results['overall_score'] >= 80:
            report.append("✅ Excellent performance! Optimizations working well.")
        elif results['overall_score'] >= 60:
            report.append("✅ Good performance with noticeable improvements.")
        elif results['overall_score'] >= 40:
            report.append("⚠️ Moderate performance. Some optimizations effective.")
        else:
            report.append("❌ Performance needs attention. Check system resources.")

        return "\n".join(report)

def main():
    """Main performance test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test mode
        test_suite = PerformanceTestSuite()
        results = test_suite.run_quick_test()

        # Generate and display report
        report = test_suite.generate_quick_report(results)
        print(report)

        # Also output JSON for programmatic use
        print("\n" + "="*55)
        print("JSON Results:")
        print(json.dumps(results, indent=2))

    else:
        print("Usage: python3 performance_test.py quick")
        print("Full test suite not implemented in this version")

if __name__ == "__main__":
    main()