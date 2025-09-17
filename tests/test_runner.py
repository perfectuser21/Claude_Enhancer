#!/usr/bin/env python3
"""
Perfect21 测试运行器
统一运行所有测试并生成完整的测试报告
"""

import os
import sys
import pytest
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class Perfect21TestRunner:
    """Perfect21 测试运行器"""

    def __init__(self, project_root=None):
        self.project_root = Path(project_root or os.path.dirname(__file__)).parent
        self.test_dir = self.project_root / "tests"
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_unit_tests(self, verbose=False):
        """运行单元测试"""
        print("🧪 运行单元测试...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "unit"),
            "--tb=short",
            "--junit-xml=junit-unit.xml",
            "--cov=features",
            "--cov-report=xml:coverage-unit.xml",
            "--cov-report=term-missing"
        ]

        if verbose:
            cmd.append("-v")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))

        self.results['unit_tests'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }

        print(f"✅ 单元测试完成 (返回码: {result.returncode})")
        return result.returncode == 0

    def run_integration_tests(self, verbose=False):
        """运行集成测试"""
        print("🔗 运行集成测试...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "integration"),
            "--tb=short",
            "--junit-xml=junit-integration.xml"
        ]

        if verbose:
            cmd.append("-v")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))

        self.results['integration_tests'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }

        print(f"✅ 集成测试完成 (返回码: {result.returncode})")
        return result.returncode == 0

    def run_performance_tests(self, verbose=False):
        """运行性能测试"""
        print("⚡ 运行性能测试...")

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "performance"),
            "--tb=short",
            "--junit-xml=junit-performance.xml",
            "-m", "not slow"  # 跳过耗时测试
        ]

        if verbose:
            cmd.append("-v")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))

        self.results['performance_tests'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }

        print(f"✅ 性能测试完成 (返回码: {result.returncode})")
        return result.returncode == 0

    def run_security_tests(self, verbose=False):
        """运行安全测试"""
        print("🔒 运行安全测试...")

        # 运行质量门安全检查
        from features.preventive_quality.quality_gate import QualityGate

        quality_gate = QualityGate(str(self.project_root))
        security_results = quality_gate.run_checks(categories=['security'])

        security_passed = all(r.status.value != 'failed' for r in security_results)

        self.results['security_tests'] = {
            'returncode': 0 if security_passed else 1,
            'results': [
                {
                    'check_name': r.check_name,
                    'status': r.status.value,
                    'severity': r.severity.value,
                    'message': r.message,
                    'suggestions': r.suggestions
                }
                for r in security_results
            ],
            'success': security_passed
        }

        print(f"✅ 安全测试完成 ({'通过' if security_passed else '失败'})")
        return security_passed

    def run_quality_checks(self):
        """运行质量检查"""
        print("🎯 运行质量检查...")

        from features.preventive_quality.quality_gate import QualityGate

        quality_gate = QualityGate(str(self.project_root))
        all_results = quality_gate.run_checks()
        summary = quality_gate.get_check_summary(all_results)

        # 计算质量分数
        total_checks = summary['总检查数']
        passed_checks = summary['通过']
        quality_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        self.results['quality_checks'] = {
            'summary': summary,
            'quality_score': quality_score,
            'detailed_results': [
                {
                    'check_name': r.check_name,
                    'status': r.status.value,
                    'severity': r.severity.value,
                    'message': r.message,
                    'execution_time': r.execution_time,
                    'suggestions': r.suggestions
                }
                for r in all_results
            ],
            'success': quality_score >= 80  # 80%以上算通过
        }

        print(f"✅ 质量检查完成 (质量分数: {quality_score:.1f}%)")
        return quality_score >= 80

    def calculate_coverage(self):
        """计算测试覆盖率"""
        coverage_file = self.project_root / "coverage-unit.xml"
        if not coverage_file.exists():
            return {"error": "Coverage file not found"}

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # 解析覆盖率数据
            coverage_data = {}
            for package in root.findall(".//package"):
                package_name = package.get("name")
                line_rate = float(package.get("line-rate", 0)) * 100
                branch_rate = float(package.get("branch-rate", 0)) * 100

                coverage_data[package_name] = {
                    "line_coverage": line_rate,
                    "branch_coverage": branch_rate
                }

            # 计算总体覆盖率
            overall_line_rate = float(root.get("line-rate", 0)) * 100
            overall_branch_rate = float(root.get("branch-rate", 0)) * 100

            return {
                "overall_line_coverage": overall_line_rate,
                "overall_branch_coverage": overall_branch_rate,
                "package_coverage": coverage_data,
                "target_coverage": 90.0,
                "meets_target": overall_line_coverage >= 90.0
            }

        except Exception as e:
            return {"error": f"Failed to parse coverage: {str(e)}"}

    def generate_report(self):
        """生成测试报告"""
        coverage_info = self.calculate_coverage()

        report = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds() if (self.start_time and self.end_time) else None,
                "project_root": str(self.project_root)
            },
            "test_results": self.results,
            "coverage": coverage_info,
            "summary": self._generate_summary()
        }

        return report

    def _generate_summary(self):
        """生成测试摘要"""
        total_success = 0
        total_tests = 0

        test_categories = ['unit_tests', 'integration_tests', 'performance_tests', 'security_tests', 'quality_checks']

        for category in test_categories:
            if category in self.results:
                total_tests += 1
                if self.results[category].get('success', False):
                    total_success += 1

        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0

        return {
            "total_test_categories": total_tests,
            "successful_categories": total_success,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate >= 80 else "FAIL",
            "quality_gate_status": "PASS" if self.results.get('quality_checks', {}).get('success', False) else "FAIL"
        }

    def save_report(self, filename=None):
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"perfect21_test_report_{timestamp}.json"

        report = self.generate_report()

        report_path = self.project_root / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 测试报告已保存: {report_path}")
        return str(report_path)

    def print_summary(self):
        """打印测试摘要"""
        summary = self._generate_summary()

        print("\n" + "="*60)
        print("🎯 Perfect21 测试摘要")
        print("="*60)

        print(f"📊 总体状态: {summary['overall_status']}")
        print(f"✅ 测试类别: {summary['successful_categories']}/{summary['total_test_categories']}")
        print(f"📈 成功率: {summary['success_rate']:.1f}%")
        print(f"🛡️  质量门: {summary['quality_gate_status']}")

        if 'quality_checks' in self.results:
            quality_score = self.results['quality_checks'].get('quality_score', 0)
            print(f"🎯 质量分数: {quality_score:.1f}%")

        # 覆盖率信息
        coverage_info = self.calculate_coverage()
        if 'overall_line_coverage' in coverage_info:
            line_coverage = coverage_info['overall_line_coverage']
            print(f"📋 代码覆盖率: {line_coverage:.1f}%")

            if coverage_info.get('meets_target', False):
                print("✅ 达到覆盖率目标 (90%)")
            else:
                print("❌ 未达到覆盖率目标 (90%)")

        print("\n📋 详细结果:")
        for category, result in self.results.items():
            status = "✅ 通过" if result.get('success', False) else "❌ 失败"
            print(f"  {category}: {status}")

        print("="*60)

    def run_all_tests(self, verbose=False, skip_slow=True):
        """运行所有测试"""
        print("🚀 开始 Perfect21 完整测试套件")
        print("="*60)

        self.start_time = datetime.now()

        try:
            # 运行各类测试
            unit_success = self.run_unit_tests(verbose)
            integration_success = self.run_integration_tests(verbose)

            if not skip_slow:
                performance_success = self.run_performance_tests(verbose)
            else:
                print("⏩ 跳过性能测试 (使用 --include-slow 来运行)")
                performance_success = True

            security_success = self.run_security_tests(verbose)
            quality_success = self.run_quality_checks()

            self.end_time = datetime.now()

            # 生成并保存报告
            report_path = self.save_report()

            # 打印摘要
            self.print_summary()

            # 总体成功判断
            overall_success = all([
                unit_success,
                integration_success,
                performance_success,
                security_success,
                quality_success
            ])

            if overall_success:
                print("\n🎉 所有测试通过！Perfect21 系统状态良好。")
            else:
                print("\n⚠️  部分测试失败，请检查详细报告。")

            return overall_success

        except Exception as e:
            self.end_time = datetime.now()
            print(f"\n❌ 测试运行过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Perfect21 测试运行器")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--include-slow", action="store_true", help="包含耗时测试")
    parser.add_argument("--unit-only", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration-only", action="store_true", help="只运行集成测试")
    parser.add_argument("--performance-only", action="store_true", help="只运行性能测试")
    parser.add_argument("--quality-only", action="store_true", help="只运行质量检查")
    parser.add_argument("--project-root", help="项目根目录路径")

    args = parser.parse_args()

    runner = Perfect21TestRunner(args.project_root)

    try:
        if args.unit_only:
            success = runner.run_unit_tests(args.verbose)
        elif args.integration_only:
            success = runner.run_integration_tests(args.verbose)
        elif args.performance_only:
            success = runner.run_performance_tests(args.verbose)
        elif args.quality_only:
            success = runner.run_quality_checks()
        else:
            success = runner.run_all_tests(args.verbose, not args.include_slow)

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()