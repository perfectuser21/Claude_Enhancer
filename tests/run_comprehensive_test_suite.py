#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Perfect21
Orchestrates all test categories with detailed reporting
"""

import pytest
import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse


class TestSuiteRunner:
    """Comprehensive test suite runner"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_root = project_root / "tests"
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, coverage_target: float = 90.0) -> Dict[str, Any]:
        """Run all test categories"""
        print("🚀 Starting Perfect21 Comprehensive Test Suite")
        print("=" * 60)

        self.start_time = time.time()

        # Test categories in order of execution
        test_categories = [
            ("unit", "Unit Tests", True),
            ("integration", "Integration Tests", True),
            ("e2e", "End-to-End Tests", False),  # May require special setup
            ("performance", "Performance Tests", False),  # May be slow
            ("security", "Security Tests", True)
        ]

        overall_success = True

        for category, description, required in test_categories:
            print(f"\n📋 Running {description}")
            print("-" * 40)

            success = self.run_test_category(category)
            self.results[category] = success

            if required and not success:
                overall_success = False
                print(f"❌ {description} FAILED")
            elif success:
                print(f"✅ {description} PASSED")
            else:
                print(f"⚠️  {description} SKIPPED/PARTIAL")

        # Run coverage analysis
        coverage_result = self.analyze_coverage(coverage_target)
        self.results['coverage'] = coverage_result

        self.end_time = time.time()

        # Generate final report
        self.generate_final_report()

        return {
            'overall_success': overall_success,
            'results': self.results,
            'execution_time': self.end_time - self.start_time
        }

    def run_test_category(self, category: str) -> bool:
        """Run tests for a specific category"""
        category_path = self.test_root / category

        if not category_path.exists():
            print(f"⚠️  Category {category} not found at {category_path}")
            return False

        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(category_path),
            "-v",
            "--tb=short",
            f"--junitxml={self.test_root}/results_{category}.xml",
            f"--html={self.test_root}/report_{category}.html",
            "--self-contained-html"
        ]

        # Add coverage for unit tests
        if category == "unit":
            cmd.extend([
                "--cov=api",
                "--cov=main",
                "--cov=modules",
                "--cov=features",
                f"--cov-report=html:{self.test_root}/htmlcov_{category}",
                f"--cov-report=xml:{self.test_root}/coverage_{category}.xml",
                "--cov-report=term-missing"
            ])

        # Add markers for specific categories
        if category == "performance":
            cmd.extend(["-m", "performance"])
        elif category == "security":
            cmd.extend(["-m", "security"])

        try:
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per category
            )

            print(f"Return code: {result.returncode}")
            if result.stdout:
                print("STDOUT:", result.stdout[-1000:])  # Last 1000 chars
            if result.stderr:
                print("STDERR:", result.stderr[-1000:])  # Last 1000 chars

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"❌ {category} tests timed out")
            return False
        except Exception as e:
            print(f"❌ Error running {category} tests: {e}")
            return False

    def analyze_coverage(self, target: float) -> Dict[str, Any]:
        """Analyze test coverage"""
        print(f"\n📊 Analyzing Test Coverage (Target: {target}%)")
        print("-" * 40)

        coverage_file = self.test_root / "coverage_unit.xml"

        if not coverage_file.exists():
            print("⚠️  Coverage file not found")
            return {'success': False, 'coverage': 0.0}

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # Extract coverage percentage
            coverage_elem = root.find('.//coverage')
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get('line-rate', 0)) * 100
                branch_rate = float(coverage_elem.get('branch-rate', 0)) * 100

                print(f"Line Coverage: {line_rate:.1f}%")
                print(f"Branch Coverage: {branch_rate:.1f}%")

                success = line_rate >= target

                if success:
                    print(f"✅ Coverage target {target}% achieved!")
                else:
                    print(f"❌ Coverage {line_rate:.1f}% below target {target}%")

                return {
                    'success': success,
                    'line_coverage': line_rate,
                    'branch_coverage': branch_rate,
                    'target': target
                }

        except Exception as e:
            print(f"❌ Error analyzing coverage: {e}")

        return {'success': False, 'coverage': 0.0}

    def generate_final_report(self):
        """Generate final test report"""
        print(f"\n📈 Final Test Report")
        print("=" * 60)

        total_time = self.end_time - self.start_time

        print(f"⏱️  Total Execution Time: {total_time:.2f} seconds")
        print(f"📊 Test Results Summary:")

        for category, success in self.results.items():
            if category == 'coverage':
                coverage_data = success
                if isinstance(coverage_data, dict) and 'line_coverage' in coverage_data:
                    status = "✅" if coverage_data['success'] else "❌"
                    print(f"   {status} Coverage: {coverage_data['line_coverage']:.1f}%")
            else:
                status = "✅" if success else "❌"
                print(f"   {status} {category.title()} Tests")

        # Save detailed results
        results_file = self.test_root / "comprehensive_results.json"
        detailed_results = {
            'timestamp': time.time(),
            'execution_time': total_time,
            'results': self.results,
            'summary': {
                'total_categories': len([k for k in self.results.keys() if k != 'coverage']),
                'passed_categories': len([k for k, v in self.results.items() if k != 'coverage' and v]),
                'coverage_achieved': self.results.get('coverage', {}).get('success', False)
            }
        }

        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)

        print(f"📄 Detailed results saved to: {results_file}")

        # Generate HTML dashboard
        self.generate_html_dashboard()

    def generate_html_dashboard(self):
        """Generate HTML test dashboard"""
        dashboard_file = self.test_root / "test_dashboard_comprehensive.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Perfect21 Test Dashboard</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .card {{ background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; }}
                .success {{ border-left: 5px solid #28a745; }}
                .failure {{ border-left: 5px solid #dc3545; }}
                .warning {{ border-left: 5px solid #ffc107; }}
                .metric {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
                .links {{ margin: 20px 0; }}
                .links a {{ display: inline-block; margin-right: 15px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 3px; }}
                .links a:hover {{ background: #0056b3; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .status-pass {{ color: #28a745; font-weight: bold; }}
                .status-fail {{ color: #dc3545; font-weight: bold; }}
                .status-skip {{ color: #ffc107; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Perfect21 Comprehensive Test Dashboard</h1>
                <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="summary">
                <div class="card {'success' if self.results.get('unit', False) else 'failure'}">
                    <h3>Unit Tests</h3>
                    <div class="metric">{'✅' if self.results.get('unit', False) else '❌'}</div>
                    <p>Core component testing</p>
                </div>

                <div class="card {'success' if self.results.get('integration', False) else 'failure'}">
                    <h3>Integration Tests</h3>
                    <div class="metric">{'✅' if self.results.get('integration', False) else '❌'}</div>
                    <p>Component interaction testing</p>
                </div>

                <div class="card {'success' if self.results.get('e2e', False) else 'warning'}">
                    <h3>E2E Tests</h3>
                    <div class="metric">{'✅' if self.results.get('e2e', False) else '⚠️'}</div>
                    <p>End-to-end workflow testing</p>
                </div>

                <div class="card {'success' if self.results.get('performance', False) else 'warning'}">
                    <h3>Performance Tests</h3>
                    <div class="metric">{'✅' if self.results.get('performance', False) else '⚠️'}</div>
                    <p>Performance benchmarking</p>
                </div>

                <div class="card {'success' if self.results.get('security', False) else 'failure'}">
                    <h3>Security Tests</h3>
                    <div class="metric">{'✅' if self.results.get('security', False) else '❌'}</div>
                    <p>Security vulnerability testing</p>
                </div>

                <div class="card {'success' if self.results.get('coverage', {}).get('success', False) else 'failure'}">
                    <h3>Code Coverage</h3>
                    <div class="metric">{self.results.get('coverage', {}).get('line_coverage', 0):.1f}%</div>
                    <p>Target: {self.results.get('coverage', {}).get('target', 90)}%</p>
                </div>
            </div>

            <div class="links">
                <h3>📊 Detailed Reports</h3>
                <a href="report_unit.html">Unit Test Report</a>
                <a href="report_integration.html">Integration Test Report</a>
                <a href="report_e2e.html">E2E Test Report</a>
                <a href="report_performance.html">Performance Report</a>
                <a href="report_security.html">Security Report</a>
                <a href="htmlcov_unit/index.html">Coverage Report</a>
            </div>

            <h3>📋 Test Results Summary</h3>
            <table>
                <thead>
                    <tr>
                        <th>Test Category</th>
                        <th>Status</th>
                        <th>Description</th>
                        <th>Report</th>
                    </tr>
                </thead>
                <tbody>
        """

        test_categories = [
            ("unit", "Unit Tests", "Core component functionality", "report_unit.html"),
            ("integration", "Integration Tests", "Component interactions", "report_integration.html"),
            ("e2e", "End-to-End Tests", "Complete workflows", "report_e2e.html"),
            ("performance", "Performance Tests", "Performance benchmarks", "report_performance.html"),
            ("security", "Security Tests", "Security vulnerabilities", "report_security.html")
        ]

        for category, name, description, report_file in test_categories:
            success = self.results.get(category, False)
            status_class = "status-pass" if success else "status-fail"
            status_text = "PASS" if success else "FAIL"

            html_content += f"""
                    <tr>
                        <td>{name}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{description}</td>
                        <td><a href="{report_file}">View Report</a></td>
                    </tr>
            """

        html_content += f"""
                </tbody>
            </table>

            <h3>📈 Execution Summary</h3>
            <ul>
                <li><strong>Total Execution Time:</strong> {(self.end_time - self.start_time):.2f} seconds</li>
                <li><strong>Test Categories:</strong> {len([k for k in self.results.keys() if k != 'coverage'])}</li>
                <li><strong>Passed Categories:</strong> {len([k for k, v in self.results.items() if k != 'coverage' and v])}</li>
                <li><strong>Coverage Target:</strong> {self.results.get('coverage', {}).get('target', 90)}%</li>
                <li><strong>Coverage Achieved:</strong> {self.results.get('coverage', {}).get('line_coverage', 0):.1f}%</li>
            </ul>

            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Generated by Perfect21 Comprehensive Test Suite</p>
                <p>For more information, see the individual test reports linked above.</p>
            </footer>
        </body>
        </html>
        """

        with open(dashboard_file, 'w') as f:
            f.write(html_content)

        print(f"🎨 HTML dashboard generated: {dashboard_file}")

    def run_quick_tests(self) -> bool:
        """Run quick smoke tests"""
        print("🔥 Running Quick Smoke Tests")
        print("-" * 30)

        # Run a subset of fast unit tests
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_root / "unit"),
            "-v",
            "-x",  # Stop on first failure
            "--tb=short",
            "-k", "not slow"  # Skip slow tests
        ]

        try:
            result = subprocess.run(cmd, cwd=str(self.project_root), timeout=60)
            success = result.returncode == 0

            if success:
                print("✅ Quick tests passed!")
            else:
                print("❌ Quick tests failed!")

            return success

        except subprocess.TimeoutExpired:
            print("❌ Quick tests timed out")
            return False
        except Exception as e:
            print(f"❌ Error running quick tests: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Perfect21 Comprehensive Test Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    parser.add_argument("--coverage-target", type=float, default=90.0, help="Coverage target percentage")
    parser.add_argument("--category", choices=["unit", "integration", "e2e", "performance", "security"], help="Run specific test category only")

    args = parser.parse_args()

    # Find project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    runner = TestSuiteRunner(project_root)

    if args.quick:
        success = runner.run_quick_tests()
        sys.exit(0 if success else 1)

    elif args.category:
        success = runner.run_test_category(args.category)
        sys.exit(0 if success else 1)

    else:
        # Run full test suite
        result = runner.run_all_tests(args.coverage_target)

        print(f"\n🎯 Final Result: {'SUCCESS' if result['overall_success'] else 'FAILURE'}")
        print(f"⏱️  Total Time: {result['execution_time']:.2f} seconds")

        sys.exit(0 if result['overall_success'] else 1)


if __name__ == "__main__":
    main()