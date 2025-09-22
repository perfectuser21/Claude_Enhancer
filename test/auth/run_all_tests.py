#!/usr/bin/env python3
"""
🎯 Authentication Test Suite Runner
===================================

Master test runner for the complete authentication test suite
Orchestrates all test categories with reporting and CI/CD integration

Author: Test Suite Runner Agent
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSuiteRunner:
    """Comprehensive test suite runner"""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_test_suite(self,
                      categories: List[str] = None,
                      verbose: bool = True,
                      parallel: bool = False,
                      coverage: bool = False,
                      output_format: str = "console") -> Dict[str, Any]:
        """
        Run the complete authentication test suite

        Args:
            categories: List of test categories to run (unit, integration, security, performance, e2e)
            verbose: Enable verbose output
            parallel: Run tests in parallel
            coverage: Generate coverage report
            output_format: Output format (console, json, html)

        Returns:
            Test results summary
        """
        self.start_time = datetime.utcnow()

    # print("🚀 Starting Authentication Test Suite")
    # print("=" * 60)
    # print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    # print(f"Test directory: {self.test_dir}")
    # print("=" * 60)

        # Default categories if not specified
        if not categories:
            categories = ["unit", "integration", "security", "performance", "e2e", "comprehensive"]

        # Run each test category
        for category in categories:
    # print(f"\n📋 Running {category.upper()} tests...")
            self.results[category] = self._run_test_category(category, verbose, parallel, coverage)

        self.end_time = datetime.utcnow()

        # Generate final report
        summary = self._generate_summary()
        self._output_results(summary, output_format)

        return summary

    def _run_test_category(self, category: str, verbose: bool, parallel: bool, coverage: bool) -> Dict[str, Any]:
        """Run tests for a specific category"""

        # Map categories to test files
        test_files = {
            "unit": ["unit_tests.py"],
            "integration": ["integration_tests.py"],
            "security": ["security_tests.py", "test_security_penetration.py"],
            "performance": ["performance_tests.py", "test_load_performance.py"],
            "e2e": ["test_end_to_end.py"],
            "fixtures": ["test_fixtures.py"],
            "comprehensive": ["test_comprehensive_suite.py"]
        }

        if category not in test_files:
            return {"status": "SKIPPED", "reason": f"Unknown category: {category}"}

        # Build pytest command
        cmd = ["python", "-m", "pytest"]

        # Add test files
        for test_file in test_files[category]:
            test_path = self.test_dir / test_file
            if test_path.exists():
                cmd.append(str(test_path))

        # Add pytest options
        cmd.extend([
            "-v" if verbose else "-q",
            "--tb=short",
            "--asyncio-mode=auto",
            "--durations=10"
        ])

        if parallel and category in ["unit", "integration"]:
            cmd.extend(["-n", "auto"])  # pytest-xdist for parallel execution

        if coverage:
            cmd.extend([
                "--cov=backend",
                "--cov-report=term-missing",
                f"--cov-report=html:test_coverage_{category}"
            ])

        # Add category-specific markers
        if category == "performance":
            cmd.extend(["-m", "not slow"])  # Skip slow tests by default
        elif category == "security":
            cmd.extend(["--tb=line"])  # Shorter traceback for security tests

        # Execute tests
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "duration_seconds": duration,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "duration_seconds": 1800,
                "error": "Test execution timed out after 30 minutes"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "command": " ".join(cmd)
            }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test execution summary"""
        total_duration = (self.end_time - self.start_time).total_seconds()

        # Count results by status
        status_counts = {"PASSED": 0, "FAILED": 0, "SKIPPED": 0, "ERROR": 0, "TIMEOUT": 0}
        category_details = {}

        for category, result in self.results.items():
            status = result.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

            category_details[category] = {
                "status": status,
                "duration": result.get("duration_seconds", 0),
                "exit_code": result.get("exit_code"),
                "has_errors": bool(result.get("stderr")),
                "has_output": bool(result.get("stdout"))
            }

        # Calculate overall success
        total_categories = len(self.results)
        successful_categories = status_counts["PASSED"]
        success_rate = (successful_categories / total_categories * 100) if total_categories > 0 else 0

        return {
            "execution_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "categories_executed": list(self.results.keys())
            },
            "summary": {
                "total_categories": total_categories,
                "successful_categories": successful_categories,
                "success_rate_percent": round(success_rate, 2),
                "status_breakdown": status_counts
            },
            "category_details": category_details,
            "recommendations": self._generate_recommendations(),
            "raw_results": self.results
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_categories = [cat for cat, result in self.results.items()
                           if result.get("status") == "FAILED"]

        if failed_categories:
            recommendations.append(f"Review and fix issues in failed categories: {', '.join(failed_categories)}")

        security_failed = any(cat in failed_categories for cat in ["security"])
        if security_failed:
            recommendations.append("URGENT: Address security test failures immediately")

        performance_failed = any(cat in failed_categories for cat in ["performance"])
        if performance_failed:
            recommendations.append("Investigate performance issues and optimize accordingly")

        timeout_categories = [cat for cat, result in self.results.items()
                            if result.get("status") == "TIMEOUT"]
        if timeout_categories:
            recommendations.append(f"Optimize test execution time for: {', '.join(timeout_categories)}")

        if not recommendations:
            recommendations.append("All tests passed successfully! Maintain current quality standards.")

        return recommendations

    def _output_results(self, summary: Dict[str, Any], format_type: str):
        """Output test results in specified format"""

        if format_type == "console":
            self._print_console_summary(summary)
        elif format_type == "json":
            self._save_json_report(summary)
        elif format_type == "html":
            self._generate_html_report(summary)
        else:
    # print(f"⚠️ Unknown output format: {format_type}, defaulting to console")
            self._print_console_summary(summary)

    def _print_console_summary(self, summary: Dict[str, Any]):
        """Print summary to console"""
    # print(f"\n📊 TEST SUITE EXECUTION SUMMARY")
    # print("=" * 60)

        exec_info = summary["execution_info"]
        summary_stats = summary["summary"]

    # print(f"Execution Time: {exec_info['total_duration_seconds']:.1f} seconds")
    # print(f"Categories Executed: {len(exec_info['categories_executed'])}")
    # print(f"Success Rate: {summary_stats['success_rate_percent']}%")
    # print()

    # print("STATUS BREAKDOWN:")
        for status, count in summary_stats["status_breakdown"].items():
            if count > 0:
    # print(f"  {status}: {count}")
    # print()

    # print("CATEGORY DETAILS:")
        for category, details in summary["category_details"].items():
            status = details["status"]
            duration = details["duration"]
            emoji = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⚠️"
    # print(f"  {emoji} {category.upper()}: {status} ({duration:.1f}s)")
    # print()

        if summary["recommendations"]:
    # print("RECOMMENDATIONS:")
            for i, rec in enumerate(summary["recommendations"], 1):
    # print(f"  {i}. {rec}")
    # print()

        # Overall result
        if summary_stats["success_rate_percent"] == 100:
    # print("🎉 ALL TESTS PASSED! Authentication system is ready for production.")
        elif summary_stats["success_rate_percent"] >= 80:
    # print("⚠️ Most tests passed, but some issues need attention.")
        else:
    # print("❌ Multiple test failures detected. System needs significant work.")

    # print("=" * 60)

    def _save_json_report(self, summary: Dict[str, Any]):
        """Save results as JSON report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"auth_test_results_{timestamp}.json"
        filepath = self.test_dir / filename

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

    # print(f"\n📄 JSON report saved: {filepath}")

    def _generate_html_report(self, summary: Dict[str, Any]):
        """Generate HTML report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"auth_test_report_{timestamp}.html"
        filepath = self.test_dir / filename

        html_content = self._create_html_content(summary)

        with open(filepath, 'w') as f:
            f.write(html_content)

    # print(f"\n📄 HTML report saved: {filepath}")

    def _create_html_content(self, summary: Dict[str, Any]) -> str:
        """Create HTML report content"""
        exec_info = summary["execution_info"]
        summary_stats = summary["summary"]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Test Suite Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .category {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Authentication Test Suite Report</h1>
        <p>Generated: {exec_info['start_time']}</p>
        <p>Duration: {exec_info['total_duration_seconds']:.1f} seconds</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Success Rate</h3>
            <h2 class="{'passed' if summary_stats['success_rate_percent'] == 100 else 'failed'}">{summary_stats['success_rate_percent']}%</h2>
        </div>
        <div class="metric">
            <h3>Categories</h3>
            <h2>{summary_stats['successful_categories']}/{summary_stats['total_categories']}</h2>
        </div>
    </div>

    <h2>Category Results</h2>
"""

        for category, details in summary["category_details"].items():
            status_class = "passed" if details["status"] == "PASSED" else "failed"
            html += f"""
    <div class="category">
        <h3>{category.upper()}</h3>
        <p>Status: <span class="{status_class}">{details['status']}</span></p>
        <p>Duration: {details['duration']:.1f} seconds</p>
    </div>
"""

        if summary["recommendations"]:
            html += """
    <div class="recommendations">
        <h2>📋 Recommendations</h2>
        <ul>
"""
            for rec in summary["recommendations"]:
                html += f"            <li>{rec}</li>\n"

            html += """
        </ul>
    </div>
"""

        html += """
</body>
</html>
"""
        return html


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run authentication test suite")

    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Test categories to run (unit, integration, security, performance, e2e, comprehensive)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (where supported)"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate code coverage report"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json", "html"],
        default="console",
        help="Output format for results"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only essential tests (unit + integration)"
    )

    args = parser.parse_args()

    # Quick mode - only essential tests
    if args.quick:
        args.categories = ["unit", "integration"]

    # Run test suite
    runner = TestSuiteRunner()
    summary = runner.run_test_suite(
        categories=args.categories,
        verbose=args.verbose,
        parallel=args.parallel,
        coverage=args.coverage,
        output_format=args.output
    )

    # Exit with appropriate code
    success_rate = summary["summary"]["success_rate_percent"]
    if success_rate == 100:
        sys.exit(0)  # All tests passed
    elif success_rate >= 80:
        sys.exit(1)  # Some failures, but mostly working
    else:
        sys.exit(2)  # Significant failures


if __name__ == "__main__":
    main()