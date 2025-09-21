#!/usr/bin/env python3
"""
测试运行器和统计分析器

这个脚本提供了一个统一的测试运行入口，支持不同类型的测试执行。
就像一个测试任务的指挥中心 - 可以灵活地运行各种测试组合。

功能特性：
- 支持单元测试、集成测试、性能测试
- 实时测试结果展示
- 详细的覆盖率报告
- 测试性能统计
- 失败测试的详细分析
"""

import os
import sys
import time
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET


# ========================================
# 测试结果数据结构 (Test Result Data Structures)
# ========================================

@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    file_path: str
    error_message: Optional[str] = None
    failure_message: Optional[str] = None


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage_percentage: float
    tests: List[TestResult]


@dataclass
class TestSessionResult:
    """整个测试会话结果"""
    start_time: datetime
    end_time: datetime
    duration: float
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    overall_coverage: float
    suites: List[TestSuiteResult]
    environment_info: Dict[str, Any]


# ========================================
# 测试运行器类 (Test Runner Class)
# ========================================

class TodoTestRunner:
    """
Todo API测试运行器 - 像一个智能的测试指挥官"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.test_dir = self.project_root / 'test'
        self.results_dir = self.project_root / 'test-results'
        self.coverage_dir = self.results_dir / 'coverage'
        
        # 创建结果目录
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        (self.results_dir / 'junit').mkdir(exist_ok=True)
        (self.coverage_dir / 'html').mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = True, coverage: bool = True) -> TestSuiteResult:
        """运行单元测试"""
        print("📝 开始运行单元测试...")
        
        cmd = [
            'python', '-m', 'pytest',
            str(self.test_dir / 'unit'),
            '-m', 'unit or not integration',
            '--tb=short',
        ]
        
        if verbose:
            cmd.extend(['-v', '--tb=short'])
        
        if coverage:
            cmd.extend([
                '--cov=.',
                '--cov-report=html:' + str(self.coverage_dir / 'html' / 'unit'),
                '--cov-report=xml:' + str(self.coverage_dir / 'unit_coverage.xml'),
                '--cov-report=term-missing',
                '--cov-fail-under=85'
            ])
        
        cmd.extend([
            '--junitxml=' + str(self.results_dir / 'junit' / 'unit_results.xml'),
            '--json-report',
            '--json-report-file=' + str(self.results_dir / 'unit_report.json')
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        print(f"⏱️  单元测试完成，耗时: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ 单元测试全部通过！")
        else:
            print("❌ 单元测试存在失败")
            if verbose:
                print("错误输出:")
                print(result.stdout)
                print(result.stderr)
        
        return self._parse_test_results('unit', duration)
    
    def run_integration_tests(self, verbose: bool = True) -> TestSuiteResult:
        """运行集成测试"""
        print("🔗 开始运行集成测试...")
        
        cmd = [
            'python', '-m', 'pytest',
            str(self.test_dir / 'integration'),
            '-m', 'integration',
            '--tb=short',
        ]
        
        if verbose:
            cmd.extend(['-v'])
        
        cmd.extend([
            '--junitxml=' + str(self.results_dir / 'junit' / 'integration_results.xml'),
            '--json-report',
            '--json-report-file=' + str(self.results_dir / 'integration_report.json')
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        print(f"⏱️  集成测试完成，耗时: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ 集成测试全部通过！")
        else:
            print("❌ 集成测试存在失败")
            if verbose:
                print("错误输出:")
                print(result.stdout)
                print(result.stderr)
        
        return self._parse_test_results('integration', duration)
    
    def run_performance_tests(self, verbose: bool = True) -> TestSuiteResult:
        """运行性能测试"""
        print("⚡ 开始运行性能测试...")
        
        cmd = [
            'python', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'performance',
            '--tb=short',
            '--benchmark-only',
            '--benchmark-json=' + str(self.results_dir / 'benchmark.json')
        ]
        
        if verbose:
            cmd.extend(['-v'])
        
        cmd.extend([
            '--junitxml=' + str(self.results_dir / 'junit' / 'performance_results.xml'),
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        print(f"⏱️  性能测试完成，耗时: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ 性能测试全部通过！")
        else:
            print("❌ 性能测试存在失败")
            if verbose:
                print("错误输出:")
                print(result.stdout)
                print(result.stderr)
        
        return self._parse_test_results('performance', duration)
    
    def run_security_tests(self, verbose: bool = True) -> TestSuiteResult:
        """运行安全测试"""
        print("🔒 开始运行安全测试...")
        
        cmd = [
            'python', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'security',
            '--tb=short',
        ]
        
        if verbose:
            cmd.extend(['-v'])
        
        cmd.extend([
            '--junitxml=' + str(self.results_dir / 'junit' / 'security_results.xml'),
        ])
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        duration = time.time() - start_time
        
        print(f"⏱️  安全测试完成，耗时: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ 安全测试全部通过！")
        else:
            print("❌ 安全测试存在失败")
            if verbose:
                print("错误输出:")
                print(result.stdout)
                print(result.stderr)
        
        return self._parse_test_results('security', duration)
    
    def run_all_tests(self, verbose: bool = True, coverage: bool = True, 
                     include_performance: bool = False, include_security: bool = False) -> TestSessionResult:
        """运行所有测试"""
        print("🚀 开始运行全部测试套件...")
        print("=" * 60)
        
        session_start = time.time()
        start_time = datetime.now()
        
        suites = []
        
        # 运行单元测试
        unit_result = self.run_unit_tests(verbose, coverage)
        suites.append(unit_result)
        print()
        
        # 运行集成测试
        integration_result = self.run_integration_tests(verbose)
        suites.append(integration_result)
        print()
        
        # 可选的性能测试
        if include_performance:
            performance_result = self.run_performance_tests(verbose)
            suites.append(performance_result)
            print()
        
        # 可选的安全测试
        if include_security:
            security_result = self.run_security_tests(verbose)
            suites.append(security_result)
            print()
        
        session_duration = time.time() - session_start
        end_time = datetime.now()
        
        # 计算总体统计
        total_tests = sum(suite.total_tests for suite in suites)
        total_passed = sum(suite.passed for suite in suites)
        total_failed = sum(suite.failed for suite in suites)
        total_skipped = sum(suite.skipped for suite in suites)
        total_errors = sum(suite.errors for suite in suites)
        
        # 计算总体覆盖率（以单元测试为主）
        overall_coverage = unit_result.coverage_percentage if coverage else 0.0
        
        session_result = TestSessionResult(
            start_time=start_time,
            end_time=end_time,
            duration=session_duration,
            total_tests=total_tests,
            passed=total_passed,
            failed=total_failed,
            skipped=total_skipped,
            errors=total_errors,
            overall_coverage=overall_coverage,
            suites=suites,
            environment_info=self._get_environment_info()
        )
        
        # 保存综合报告
        self._save_session_report(session_result)
        
        # 显示综合结果
        self._display_session_summary(session_result)
        
        return session_result
    
    def run_coverage_only(self) -> float:
        """仅运行覆盖率检查"""
        print("📈 开始计算代码覆盖率...")
        
        cmd = [
            'python', '-m', 'pytest',
            str(self.test_dir / 'unit'),
            '--cov=.',
            '--cov-report=html:' + str(self.coverage_dir / 'html'),
            '--cov-report=xml:' + str(self.coverage_dir / 'coverage.xml'),
            '--cov-report=term-missing',
            '--cov-report=json:' + str(self.coverage_dir / 'coverage.json'),
            '--quiet'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
        
        # 解析覆盖率
        coverage_percentage = self._parse_coverage_from_output(result.stdout)
        
        print(f"🎯 代码覆盖率: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 80:
            print("✅ 覆盖率达标！")
        else:
            print("⚠️  覆盖率低于80%，需要改进")
        
        return coverage_percentage
    
    def _parse_test_results(self, suite_name: str, duration: float) -> TestSuiteResult:
        """解析测试结果"""
        junit_file = self.results_dir / 'junit' / f'{suite_name}_results.xml'
        
        if not junit_file.exists():
            # 返回空结果
            return TestSuiteResult(
                name=suite_name,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=duration,
                coverage_percentage=0.0,
                tests=[]
            )
        
        # 解析JUnit XML
        tree = ET.parse(junit_file)
        root = tree.getroot()
        
        total_tests = int(root.get('tests', 0))
        failures = int(root.get('failures', 0))
        errors = int(root.get('errors', 0))
        skipped = int(root.get('skipped', 0))
        passed = total_tests - failures - errors - skipped
        
        tests = []
        for testcase in root.findall('.//testcase'):
            name = testcase.get('name')
            classname = testcase.get('classname')
            time_taken = float(testcase.get('time', 0))
            
            # 判断测试状态
            if testcase.find('failure') is not None:
                status = 'failed'
                failure_elem = testcase.find('failure')
                failure_message = failure_elem.text if failure_elem is not None else None
                error_message = None
            elif testcase.find('error') is not None:
                status = 'error'
                error_elem = testcase.find('error')
                error_message = error_elem.text if error_elem is not None else None
                failure_message = None
            elif testcase.find('skipped') is not None:
                status = 'skipped'
                error_message = None
                failure_message = None
            else:
                status = 'passed'
                error_message = None
                failure_message = None
            
            test_result = TestResult(
                name=name,
                status=status,
                duration=time_taken,
                file_path=classname,
                error_message=error_message,
                failure_message=failure_message
            )
            tests.append(test_result)
        
        # 获取覆盖率（仅对单元测试）
        coverage_percentage = 0.0
        if suite_name == 'unit':
            coverage_json_file = self.coverage_dir / 'coverage.json'
            if coverage_json_file.exists():
                try:
                    with open(coverage_json_file, 'r') as f:
                        coverage_data = json.load(f)
                        coverage_percentage = coverage_data.get('totals', {}).get('percent_covered', 0.0)
                except (json.JSONDecodeError, KeyError):
                    pass
        
        return TestSuiteResult(
            name=suite_name,
            total_tests=total_tests,
            passed=passed,
            failed=failures,
            skipped=skipped,
            errors=errors,
            duration=duration,
            coverage_percentage=coverage_percentage,
            tests=tests
        )
    
    def _parse_coverage_from_output(self, output: str) -> float:
        """从输出中解析覆盖率"""
        lines = output.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                # 查找百分数
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            return float(part[:-1])
                        except ValueError:
                            continue
        return 0.0
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        import platform
        import sys
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'hostname': platform.node(),
            'test_runner_version': '1.0.0',
            'working_directory': str(self.project_root),
        }
    
    def _save_session_report(self, session_result: TestSessionResult):
        """保存测试会话报告"""
        report_file = self.results_dir / 'test_session_report.json'
        
        # 转换为可序列化的格式
        report_data = asdict(session_result)
        report_data['start_time'] = session_result.start_time.isoformat()
        report_data['end_time'] = session_result.end_time.isoformat()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试报告已保存到: {report_file}")
    
    def _display_session_summary(self, session_result: TestSessionResult):
        """显示测试会话摘要"""
        print("=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        
        # 总体统计
        print(f"⏱️  总耗时: {session_result.duration:.2f}秒")
        print(f"📝 总测试数: {session_result.total_tests}")
        print(f"✅ 通过: {session_result.passed}")
        print(f"❌ 失败: {session_result.failed}")
        print(f"⏭️  跳过: {session_result.skipped}")
        print(f"⚠️  错误: {session_result.errors}")
        
        if session_result.overall_coverage > 0:
            print(f"🎯 代码覆盖率: {session_result.overall_coverage:.1f}%")
        
        # 成功率
        if session_result.total_tests > 0:
            success_rate = (session_result.passed / session_result.total_tests) * 100
            print(f"📈 成功率: {success_rate:.1f}%")
        
        print()
        
        # 各个测试套件的结果
        print("📋 各测试套件结果:")
        print("-" * 40)
        
        for suite in session_result.suites:
            status_icon = "✅" if suite.failed == 0 and suite.errors == 0 else "❌"
            print(f"{status_icon} {suite.name.title()}:")
            print(f"    测试数: {suite.total_tests}")
            print(f"    通过: {suite.passed}, 失败: {suite.failed}, 跳过: {suite.skipped}, 错误: {suite.errors}")
            print(f"    耗时: {suite.duration:.2f}秒")
            if suite.coverage_percentage > 0:
                print(f"    覆盖率: {suite.coverage_percentage:.1f}%")
            print()
        
        # 最终结论
        print("=" * 60)
        if session_result.failed == 0 and session_result.errors == 0:
            print("🎉 所有测试都通过了！系统运行良好。")
        else:
            print("⚠️  有测试失败，请检查上方的详细信息。")
        
        print(f"📁 详细报告可在以下目录查看: {self.results_dir}")
        print("=" * 60)
    
    def generate_html_report(self) -> Path:
        """生成HTML格式的综合报告"""
        print("📋 生成HTML报告...")
        
        # 这里可以集成更复杂的HTML报告生成逻辑
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Todo API 测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .suite { margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .passed { color: green; }
        .failed { color: red; }
        .skipped { color: orange; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Todo API 测试报告</h1>
        <p>生成时间: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>测试结果摘要</h2>
        <p>请查看具体的测试结果文件以获取详细信息。</p>
    </div>
</body>
</html>
        """
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        html_file = self.results_dir / 'comprehensive_report.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📝 HTML报告已生成: {html_file}")
        return html_file


# ========================================
# 命令行接口 (Command Line Interface)
# ========================================

def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description='Todo API 测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_tests.py --all              # 运行所有测试
  python run_tests.py --unit             # 仅运行单元测试
  python run_tests.py --integration      # 仅运行集成测试
  python run_tests.py --coverage-only    # 仅检查覆盖率
  python run_tests.py --performance      # 运行性能测试
        """
    )
    
    # 测试类型选项
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument('--all', action='store_true', help='运行所有测试')
    test_group.add_argument('--unit', action='store_true', help='仅运行单元测试')
    test_group.add_argument('--integration', action='store_true', help='仅运行集成测试')
    test_group.add_argument('--performance', action='store_true', help='仅运行性能测试')
    test_group.add_argument('--security', action='store_true', help='仅运行安全测试')
    test_group.add_argument('--coverage-only', action='store_true', help='仅检查代码覆盖率')
    
    # 其他选项
    parser.add_argument('--quiet', '-q', action='store_true', help='减少输出信息')
    parser.add_argument('--no-coverage', action='store_true', help='跳过覆盖率检查')
    parser.add_argument('--include-performance', action='store_true', help='在全部测试中包含性能测试')
    parser.add_argument('--include-security', action='store_true', help='在全部测试中包含安全测试')
    parser.add_argument('--html-report', action='store_true', help='生成HTML报告')
    parser.add_argument('--project-root', type=Path, help='项目根目录路径')
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = TodoTestRunner(args.project_root)
    
    try:
        # 根据选项执行相应的测试
        if args.coverage_only:
            coverage = runner.run_coverage_only()
            sys.exit(0 if coverage >= 80 else 1)
        
        elif args.unit:
            result = runner.run_unit_tests(verbose=not args.quiet, coverage=not args.no_coverage)
            success = result.failed == 0 and result.errors == 0
        
        elif args.integration:
            result = runner.run_integration_tests(verbose=not args.quiet)
            success = result.failed == 0 and result.errors == 0
        
        elif args.performance:
            result = runner.run_performance_tests(verbose=not args.quiet)
            success = result.failed == 0 and result.errors == 0
        
        elif args.security:
            result = runner.run_security_tests(verbose=not args.quiet)
            success = result.failed == 0 and result.errors == 0
        
        elif args.all:
            session_result = runner.run_all_tests(
                verbose=not args.quiet,
                coverage=not args.no_coverage,
                include_performance=args.include_performance,
                include_security=args.include_security
            )
            success = session_result.failed == 0 and session_result.errors == 0
        
        # 生成HTML报告
        if args.html_report:
            runner.generate_html_report()
        
        # 返回适当的退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ 测试运行器出现错误: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
