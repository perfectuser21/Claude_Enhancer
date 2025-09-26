#!/usr/bin/env python3
"""
Optimized Test Runner for Claude Enhancer Plus P3 Phase
Parallel execution, sub-10s target, 80%+ coverage
"""

import pytest
import asyncio
import time
import json
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import multiprocessing as mp
from dataclasses import dataclass
import psutil


@dataclass
class TestExecutionConfig:
    """Optimized test execution configuration"""

    max_execution_time: float = 10.0
    target_coverage: float = 0.8
    parallel_workers: int = min(mp.cpu_count(), 6)
    memory_limit_mb: float = 1000.0
    fail_fast: bool = True
    verbose: bool = True
    run_performance_tests: bool = True
    generate_coverage_report: bool = True


class OptimizedTestRunner:
    """High-performance test runner with intelligent parallelization"""

    def __init__(self, config: TestExecutionConfig = None):
        self.config = config or TestExecutionConfig()
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.start_time = None
        self.results = {}

    def _discover_test_modules(self) -> Dict[str, List[str]]:
        """Discover and categorize test modules for optimal execution"""
        test_categories = {
            "unit_fast": [],
            "integration": [],
            "performance": [],
            "async": [],
        }

        # Define test modules by category for optimal scheduling
        test_modules = {
            "unit_fast": [
                "test_modular_architecture.py::TestPhaseManager::test_phase_initialization",
                "test_modular_architecture.py::TestPhaseManager::test_phase_transitions",
                "test_modular_architecture.py::TestValidationEngine::test_agent_count_validation",
                "test_modular_architecture.py::TestValidationEngine::test_parallel_execution_validation",
                "test_modular_architecture.py::TestFileOperations::test_config_file_operations",
                "test_modular_architecture.py::TestFileOperations::test_path_validation",
                "test_modular_architecture.py::TestCacheManager::test_cache_basic_operations",
            ],
            "integration": [
                "test_modular_architecture.py::TestIntegrationScenarios::test_end_to_end_workflow_simulation",
                "test_modular_architecture.py::TestCacheManager::test_cache_memory_efficiency",
            ],
            "performance": [
                "test_modular_architecture.py::TestPhaseManager::test_phase_manager_performance",
                "test_modular_architecture.py::TestCacheManager::test_cache_performance_optimization",
                "test_modular_architecture.py::TestIntegrationScenarios::test_system_performance_under_load",
                "test_modular_architecture.py::TestPerformanceRegression",
            ],
            "async": [
                "test_modular_architecture.py::TestIntegrationScenarios::test_parallel_agent_execution"
            ],
        }

        return test_modules

    def run_unit_tests_parallel(self) -> Dict[str, Any]:
        """Run unit tests with maximum parallelization"""
        print("⚡ Running Unit Tests (Parallel)")
        start_time = time.perf_counter()

        # Pytest command for fast unit tests
        cmd = [
            "python",
            "-m",
            "pytest",
            str(self.test_dir / "test_modular_architecture.py"),
            "-v",
            "--tb=short",
            "--maxfail=5" if not self.config.fail_fast else "--maxfail=1",
            "-x" if self.config.fail_fast else "",
            f"-n {self.config.parallel_workers}",  # Parallel execution
            "--dist=loadscope",
            "-m",
            "unit or fast",  # Only unit/fast tests
            "--durations=10",
            "--disable-warnings",
        ]

        # Remove empty strings
        cmd = [arg for arg in cmd if arg]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5.0,  # Fast timeout for unit tests
                cwd=self.test_dir,
            )

            duration = time.perf_counter() - start_time
            success = result.returncode == 0

            return {
                "category": "unit_tests",
                "success": success,
                "duration": duration,
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "category": "unit_tests",
                "success": False,
                "duration": 5.0,
                "error": "Unit tests timed out (>5s)",
                "return_code": 1,
            }
        except Exception as e:
            return {
                "category": "unit_tests",
                "success": False,
                "duration": time.perf_counter() - start_time,
                "error": str(e),
                "return_code": 1,
            }

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests with moderate parallelization"""
        print("🔄 Running Integration Tests")
        start_time = time.perf_counter()

        cmd = [
            "python",
            "-m",
            "pytest",
            str(self.test_dir / "test_modular_architecture.py"),
            "-v",
            "--tb=short",
            "--maxfail=3",
            "-n 2",  # Reduced parallelization for integration tests
            "-m",
            "integration",
            "--durations=5",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3.0, cwd=self.test_dir
            )

            duration = time.perf_counter() - start_time
            success = result.returncode == 0

            return {
                "category": "integration_tests",
                "success": success,
                "duration": duration,
                "output": result.stdout,
                "errors": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "category": "integration_tests",
                "success": False,
                "duration": 3.0,
                "error": "Integration tests timed out",
                "return_code": 1,
            }
        except Exception as e:
            return {
                "category": "integration_tests",
                "success": False,
                "duration": time.perf_counter() - start_time,
                "error": str(e),
                "return_code": 1,
            }

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests and benchmarks"""
        print("🚀 Running Performance Tests")
        start_time = time.perf_counter()

        if not self.config.run_performance_tests:
            return {
                "category": "performance_tests",
                "success": True,
                "duration": 0.0,
                "message": "Skipped (disabled in config)",
                "return_code": 0,
            }

        # Run optimized test suite
        try:
            from optimized_test_suite import OptimizedTestSuite, TestConfig
            from performance_benchmark_suite import PerformanceBenchmarkSuite

            # Run optimized test suite
            test_config = TestConfig(
                max_execution_time=3.0,  # Strict limit for performance tests
                target_coverage=0.8,
                parallel_workers=self.config.parallel_workers,
            )

            suite = OptimizedTestSuite(test_config)
            suite_results = suite.run_optimized_suite()

            # Run benchmark suite
            benchmark_suite = PerformanceBenchmarkSuite()
            benchmark_results = asyncio.run(
                asyncio.wait_for(benchmark_suite.run_benchmark_suite(), timeout=4.0)
            )

            duration = time.perf_counter() - start_time

            return {
                "category": "performance_tests",
                "success": suite_results["performance_target_met"]
                and benchmark_results["target_met"],
                "duration": duration,
                "suite_results": suite_results,
                "benchmark_results": benchmark_results,
                "return_code": 0 if suite_results["performance_target_met"] else 1,
            }

        except asyncio.TimeoutError:
            return {
                "category": "performance_tests",
                "success": False,
                "duration": 4.0,
                "error": "Performance tests timed out",
                "return_code": 1,
            }
        except Exception as e:
            return {
                "category": "performance_tests",
                "success": False,
                "duration": time.perf_counter() - start_time,
                "error": str(e),
                "return_code": 1,
            }

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate coverage report if enabled"""
        if not self.config.generate_coverage_report:
            return {"success": True, "message": "Coverage reporting disabled"}

        print("📊 Generating Coverage Report")
        start_time = time.perf_counter()

        try:
            # Run pytest with coverage
            cmd = [
                "python",
                "-m",
                "pytest",
                str(self.test_dir),
                "--cov=../src",
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-fail-under=80",
                "--quiet",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=2.0, cwd=self.test_dir
            )

            duration = time.perf_counter() - start_time

            # Parse coverage results
            coverage_file = self.test_dir / "coverage.json"
            coverage_data = {}
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)

            return {
                "success": result.returncode == 0,
                "duration": duration,
                "coverage_percent": total_coverage,
                "target_met": total_coverage >= (self.config.target_coverage * 100),
                "coverage_data": coverage_data,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": 2.0,
                "error": "Coverage generation timed out",
                "return_code": 1,
            }
        except Exception as e:
            return {
                "success": False,
                "duration": time.perf_counter() - start_time,
                "error": str(e),
                "return_code": 1,
            }

    def run_parallel_test_execution(self) -> Dict[str, Any]:
        """Execute all test categories in parallel where possible"""
        print("🔀 Starting Parallel Test Execution")
        self.start_time = time.perf_counter()

        # Execute tests in optimal order with parallelization
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit test categories
            futures = {
                "unit": executor.submit(self.run_unit_tests_parallel),
                "integration": executor.submit(self.run_integration_tests),
                "performance": executor.submit(self.run_performance_tests),
            }

            # Collect results as they complete
            results = {}
            for category, future in futures.items():
                try:
                    result = future.result(timeout=8.0)  # Individual timeout
                    results[category] = result
                    status = "✅" if result["success"] else "❌"
                    print(f"  {status} {category}: {result['duration']:.3f}s")
                except Exception as e:
                    results[category] = {
                        "success": False,
                        "error": str(e),
                        "duration": 0.0,
                        "return_code": 1,
                    }
                    print(f"  ❌ {category}: Failed - {e}")

        return results

    def run_optimized_test_suite(self) -> Dict[str, Any]:
        """Run the complete optimized test suite"""
        print("🚀 Claude Enhancer Plus - Optimized Test Suite P3")
        print("Target: <10s execution, 80%+ coverage, parallel execution")
        print("=" * 70)

        suite_start_time = time.perf_counter()

        # Run parallel test execution
        test_results = self.run_parallel_test_execution()

        # Generate coverage report
        coverage_result = self.generate_coverage_report()
        test_results["coverage"] = coverage_result

        total_duration = time.perf_counter() - suite_start_time

        # Calculate summary metrics
        successful_categories = sum(
            1 for r in test_results.values() if r.get("success", False)
        )
        total_categories = len([k for k in test_results.keys() if k != "coverage"])
        success_rate = (
            successful_categories / total_categories if total_categories > 0 else 0
        )

        # Performance analysis
        performance_target_met = total_duration < self.config.max_execution_time
        coverage_target_met = coverage_result.get("target_met", False)

        # Overall success criteria
        overall_success = (
            success_rate >= 0.8 and performance_target_met and coverage_target_met
        )

        summary = {
            "timestamp": time.time(),
            "total_duration": total_duration,
            "performance_target_met": performance_target_met,
            "coverage_target_met": coverage_target_met,
            "success_rate": success_rate,
            "overall_success": overall_success,
            "successful_categories": successful_categories,
            "total_categories": total_categories,
            "test_results": test_results,
            "configuration": {
                "max_execution_time": self.config.max_execution_time,
                "target_coverage": self.config.target_coverage,
                "parallel_workers": self.config.parallel_workers,
                "memory_limit_mb": self.config.memory_limit_mb,
            },
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_gb": psutil.virtual_memory().total / (1024**3),
            },
        }

        # Print final results
        print("\n" + "=" * 70)
        print("📊 Optimized Test Suite Results - P3 Phase")
        print("=" * 70)
        print(
            f"⏱️  Total Duration: {total_duration:.3f}s (target: <{self.config.max_execution_time}s)"
        )
        print(
            f"📈 Success Rate: {success_rate:.1%} ({successful_categories}/{total_categories})"
        )
        print(f"🎯 Performance Target: {'✅' if performance_target_met else '❌'}")
        print(
            f"📊 Coverage Target: {'✅' if coverage_target_met else '❌'} ({coverage_result.get('coverage_percent', 0):.1f}%)"
        )
        print(f"✅ Overall Success: {'Yes' if overall_success else 'No'}")

        # Category breakdown
        print(f"\n📋 Category Results:")
        for category, result in test_results.items():
            if category == "coverage":
                continue
            status = "✅" if result.get("success", False) else "❌"
            duration = result.get("duration", 0)
            print(f"  {status} {category}: {duration:.3f}s")

        # Recommendations
        if not overall_success:
            print(f"\n⚠️  Optimization Recommendations:")
            if not performance_target_met:
                print("  - Reduce test execution time through better mocking")
                print("  - Increase parallel worker count")
            if not coverage_target_met:
                print("  - Add tests for uncovered code paths")
                print("  - Review test effectiveness")
            if success_rate < 0.8:
                print("  - Fix failing test categories")
                print("  - Review test reliability")

        print("=" * 70)

        return summary

    def save_test_report(
        self, results: Dict[str, Any], filename: str = "optimized_test_report.json"
    ) -> Path:
        """Save comprehensive test report"""
        report_path = self.test_dir / filename

        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📄 Test report saved to: {report_path}")
        return report_path


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimized Test Runner for Claude Enhancer Plus"
    )
    parser.add_argument(
        "--max-time", type=float, default=10.0, help="Maximum execution time (seconds)"
    )
    parser.add_argument(
        "--target-coverage", type=float, default=0.8, help="Target coverage percentage"
    )
    parser.add_argument(
        "--workers", type=int, default=min(mp.cpu_count(), 6), help="Parallel workers"
    )
    parser.add_argument(
        "--no-performance", action="store_true", help="Skip performance tests"
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Skip coverage report"
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )

    args = parser.parse_args()

    # Create configuration
    config = TestExecutionConfig(
        max_execution_time=args.max_time,
        target_coverage=args.target_coverage,
        parallel_workers=args.workers,
        run_performance_tests=not args.no_performance,
        generate_coverage_report=not args.no_coverage,
        fail_fast=args.fail_fast,
    )

    # Run test suite
    runner = OptimizedTestRunner(config)
    results = runner.run_optimized_test_suite()

    # Save report
    runner.save_test_report(results)

    # Exit with appropriate code
    return results["overall_success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
