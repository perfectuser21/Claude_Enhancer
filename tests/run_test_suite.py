#!/usr/bin/env python3
"""
Perfect21 Complete Test Suite Runner
运行完整的测试套件并生成报告
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

class TestSuiteRunner:
    """测试套件运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_unit_tests(self):
        """运行单元测试"""
        print("🧪 Running Unit Tests...")
        cmd = [
            'python3', '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--tb=short',
            '--cov=features',
            '--cov=main',
            '--cov=api',
            '--cov-report=term-missing',
            '--cov-report=json:coverage-unit.json',
            '--junitxml=junit-unit.xml'
        ]

        result = self._run_command(cmd)
        self.test_results['unit_tests'] = result
        return result

    def run_integration_tests(self):
        """运行集成测试"""
        print("🔗 Running Integration Tests...")
        cmd = [
            'python3', '-m', 'pytest',
            'tests/',
            '-k', 'integration or test_auth_api',
            '-v',
            '--tb=short',
            '--junitxml=junit-integration.xml'
        ]

        result = self._run_command(cmd)
        self.test_results['integration_tests'] = result
        return result

    def run_e2e_tests(self):
        """运行E2E测试"""
        print("🚀 Running E2E Tests...")
        cmd = [
            'python3', '-m', 'pytest',
            'tests/e2e/',
            '-v',
            '--tb=short',
            '--junitxml=junit-e2e.xml',
            '-m', 'e2e'
        ]

        result = self._run_command(cmd)
        self.test_results['e2e_tests'] = result
        return result

    def run_security_tests(self):
        """运行安全测试"""
        print("🔒 Running Security Tests...")
        cmd = [
            'python3', '-m', 'pytest',
            'tests/',
            '-k', 'security',
            '-v',
            '--tb=short',
            '--junitxml=junit-security.xml'
        ]

        result = self._run_command(cmd)
        self.test_results['security_tests'] = result
        return result

    def run_performance_tests(self):
        """运行性能测试"""
        print("⚡ Running Performance Tests...")
        cmd = [
            'python3', '-m', 'pytest',
            'tests/',
            '-k', 'performance',
            '-v',
            '--tb=short',
            '--junitxml=junit-performance.xml'
        ]

        result = self._run_command(cmd)
        self.test_results['performance_tests'] = result
        return result

    def _run_command(self, cmd):
        """运行命令并收集结果"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=600  # 10分钟超时
            )

            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': time.time()
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Test execution timed out (10 minutes)',
                'execution_time': time.time()
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': time.time()
            }

    def fix_common_issues(self):
        """修复常见测试问题"""
        print("🔧 Fixing common test issues...")

        # 1. 清理测试数据库
        self._cleanup_test_databases()

        # 2. 创建必要的目录
        self._create_test_directories()

        # 3. 修复权限问题
        self._fix_permissions()

        print("✅ Common issues fixed")

    def _cleanup_test_databases(self):
        """清理测试数据库"""
        test_db_patterns = [
            'data/test_*.db',
            'test_*.db',
            '*.db'
        ]

        import glob
        for pattern in test_db_patterns:
            for db_file in glob.glob(pattern):
                if 'test' in db_file.lower():
                    try:
                        os.remove(db_file)
                        print(f"  Removed: {db_file}")
                    except:
                        pass

    def _create_test_directories(self):
        """创建测试目录"""
        test_dirs = [
            'data',
            'tests/fixtures',
            'tests/temp',
            'tests/reports'
        ]

        for dir_path in test_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")

    def _fix_permissions(self):
        """修复权限问题"""
        # 确保测试文件可执行
        test_files = list(self.project_root.glob('tests/**/*.py'))
        for test_file in test_files:
            try:
                os.chmod(test_file, 0o755)
            except:
                pass

    def generate_report(self):
        """生成测试报告"""
        print("📊 Generating test report...")

        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for test_type, result in self.test_results.items():
            if result['success']:
                # 解析pytest输出获取测试数量
                stdout = result['stdout']
                if 'passed' in stdout:
                    lines = stdout.split('\n')
                    for line in lines:
                        if 'passed' in line and ('failed' in line or 'error' in line):
                            # 解析类似 "5 failed, 12 passed in 1.91s" 的输出
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'passed':
                                    passed_tests += int(parts[i-1])
                                elif part == 'failed':
                                    failed_tests += int(parts[i-1])

        total_tests = passed_tests + failed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'execution_time': self.end_time - self.start_time if self.end_time and self.start_time else 0,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': pass_rate
            },
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }

        # 保存报告
        report_file = self.project_root / 'test_suite_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # 生成HTML报告
        self._generate_html_report(report)

        print(f"📋 Test report saved to: {report_file}")
        return report

    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []

        for test_type, result in self.test_results.items():
            if not result['success']:
                if 'import' in result['stderr'].lower():
                    recommendations.append(f"Fix import issues in {test_type}")
                if 'timeout' in result['stderr'].lower():
                    recommendations.append(f"Optimize {test_type} execution time")
                if 'database' in result['stderr'].lower():
                    recommendations.append(f"Fix database setup in {test_type}")

        if not recommendations:
            recommendations.append("All tests passing! Consider adding more edge cases.")

        return recommendations

    def _generate_html_report(self, report):
        """生成HTML报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Perfect21 Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .success {{ background: #d4edda; }}
                .failure {{ background: #f8d7da; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Perfect21 Test Suite Report</h1>
                <p>Generated: {report['timestamp']}</p>
                <p>Execution Time: {report['execution_time']:.2f} seconds</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">Total Tests: {report['summary']['total_tests']}</div>
                <div class="metric">Passed: {report['summary']['passed_tests']}</div>
                <div class="metric">Failed: {report['summary']['failed_tests']}</div>
                <div class="metric">Pass Rate: {report['summary']['pass_rate']:.1f}%</div>
            </div>

            <h2>Test Results</h2>
        """

        for test_type, result in report['test_results'].items():
            status_class = 'success' if result['success'] else 'failure'
            status_text = 'PASSED' if result['success'] else 'FAILED'

            html_content += f"""
            <div class="test-section {status_class}">
                <h3>{test_type.replace('_', ' ').title()} - {status_text}</h3>
                <p>Return Code: {result['returncode']}</p>
                <details>
                    <summary>Output</summary>
                    <pre>{result['stdout'][:1000]}...</pre>
                </details>
                {f'<details><summary>Errors</summary><pre>{result["stderr"][:1000]}...</pre></details>' if result['stderr'] else ''}
            </div>
            """

        html_content += f"""
            <h2>Recommendations</h2>
            <ul>
        """

        for rec in report['recommendations']:
            html_content += f"<li>{rec}</li>"

        html_content += """
            </ul>
        </body>
        </html>
        """

        html_file = self.project_root / 'test_suite_report.html'
        with open(html_file, 'w') as f:
            f.write(html_content)

        print(f"🌐 HTML report saved to: {html_file}")

    def run_complete_suite(self):
        """运行完整的测试套件"""
        print("🚀 Starting Perfect21 Complete Test Suite")
        print("=" * 50)

        self.start_time = time.time()

        # 修复常见问题
        self.fix_common_issues()

        # 运行各类测试
        test_runners = [
            self.run_unit_tests,
            self.run_integration_tests,
            # self.run_e2e_tests,  # 暂时跳过E2E测试，因为需要更多setup
            self.run_security_tests,
            self.run_performance_tests
        ]

        for runner in test_runners:
            try:
                runner()
            except Exception as e:
                print(f"❌ Error running {runner.__name__}: {e}")

        self.end_time = time.time()

        # 生成报告
        report = self.generate_report()

        # 打印摘要
        print("\n" + "=" * 50)
        print("📊 Test Suite Summary")
        print("=" * 50)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")
        print(f"Execution Time: {report['execution_time']:.2f} seconds")

        if report['summary']['pass_rate'] >= 95:
            print("🎉 Excellent! Test suite is in great shape!")
        elif report['summary']['pass_rate'] >= 80:
            print("✅ Good! Some improvements needed.")
        else:
            print("⚠️  Needs attention! Many tests are failing.")

        return report

def main():
    """主函数"""
    runner = TestSuiteRunner()
    return runner.run_complete_suite()

if __name__ == '__main__':
    main()