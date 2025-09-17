#!/usr/bin/env python3
"""
Perfect21认证系统完整测试套件
整合所有认证相关测试，提供统一的测试入口和覆盖率报告
"""

import pytest
import os
import sys
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestSuiteRunner:
    """测试套件运行器"""

    def __init__(self):
        self.test_results = {
            'start_time': datetime.now(),
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'coverage_percentage': 0,
            'test_categories': {
                'unit_tests': {'passed': 0, 'failed': 0, 'time': 0},
                'integration_tests': {'passed': 0, 'failed': 0, 'time': 0},
                'security_tests': {'passed': 0, 'failed': 0, 'time': 0},
                'performance_tests': {'passed': 0, 'failed': 0, 'time': 0}
            },
            'detailed_results': []
        }

    def run_test_category(self, category_name, test_path):
        """运行特定类别的测试"""
        print(f"\n{'='*60}")
        print(f"运行 {category_name}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # 运行pytest并捕获结果
            result = subprocess.run([
                'python', '-m', 'pytest',
                test_path,
                '-v',
                '--tb=short',
                '--json-report',
                '--json-report-file=/tmp/pytest_report.json'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            end_time = time.time()
            execution_time = end_time - start_time

            # 解析测试结果
            try:
                with open('/tmp/pytest_report.json', 'r') as f:
                    test_report = json.load(f)

                passed = test_report['summary']['passed']
                failed = test_report['summary']['failed']
                total = test_report['summary']['total']

                self.test_results['test_categories'][category_name.lower().replace(' ', '_')] = {
                    'passed': passed,
                    'failed': failed,
                    'time': execution_time
                }

                print(f"测试结果: {passed} 通过, {failed} 失败, 耗时 {execution_time:.2f}s")

                # 如果有失败的测试，显示详细信息
                if failed > 0:
                    print("\n失败的测试:")
                    for test in test_report['tests']:
                        if test['outcome'] == 'failed':
                            print(f"  - {test['nodeid']}: {test.get('call', {}).get('longrepr', 'Unknown error')}")

            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"无法解析测试报告: {e}")
                print("Pytest输出:")
                print(result.stdout)
                if result.stderr:
                    print("Pytest错误:")
                    print(result.stderr)

        except Exception as e:
            print(f"运行测试时出错: {e}")

    def run_all_tests(self):
        """运行所有测试"""
        print("开始运行Perfect21认证系统完整测试套件")
        print(f"开始时间: {self.test_results['start_time']}")

        # 测试类别和路径
        test_categories = [
            ("单元测试", "unit/auth/"),
            ("集成测试", "integration/auth/"),
            ("安全测试", "security/auth/"),
            ("性能测试", "performance/auth/")
        ]

        for category_name, test_path in test_categories:
            if os.path.exists(test_path):
                self.run_test_category(category_name, test_path)
            else:
                print(f"跳过 {category_name}: 路径 {test_path} 不存在")

        self.test_results['end_time'] = datetime.now()
        self.generate_summary_report()

    def generate_coverage_report(self):
        """生成代码覆盖率报告"""
        print("\n生成代码覆盖率报告...")

        try:
            # 运行覆盖率测试
            result = subprocess.run([
                'python', '-m', 'pytest',
                '--cov=features.auth_system',
                '--cov=api.auth_api',
                '--cov-report=html:coverage_html',
                '--cov-report=xml:coverage.xml',
                '--cov-report=term-missing',
                'unit/auth/',
                'integration/auth/',
                'security/auth/'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            # 解析覆盖率
            coverage_output = result.stdout
            for line in coverage_output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    # 提取覆盖率百分比
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            try:
                                self.test_results['coverage_percentage'] = float(part.rstrip('%'))
                                break
                            except ValueError:
                                continue

            print("覆盖率报告生成完成")
            print(f"总体覆盖率: {self.test_results['coverage_percentage']:.1f}%")

        except Exception as e:
            print(f"生成覆盖率报告时出错: {e}")

    def generate_summary_report(self):
        """生成汇总报告"""
        print("\n" + "="*80)
        print("Perfect21认证系统测试套件汇总报告")
        print("="*80)

        # 计算总计
        total_passed = sum(cat['passed'] for cat in self.test_results['test_categories'].values())
        total_failed = sum(cat['failed'] for cat in self.test_results['test_categories'].values())
        total_time = sum(cat['time'] for cat in self.test_results['test_categories'].values())

        print(f"执行时间: {self.test_results['start_time']} - {self.test_results['end_time']}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"总测试数: {total_passed + total_failed}")
        print(f"通过: {total_passed}")
        print(f"失败: {total_failed}")
        print(f"成功率: {total_passed/(total_passed + total_failed)*100:.1f}%")

        print("\n分类结果:")
        for category, results in self.test_results['test_categories'].items():
            passed = results['passed']
            failed = results['failed']
            time_taken = results['time']
            total_cat = passed + failed

            if total_cat > 0:
                success_rate = passed / total_cat * 100
                print(f"  {category.replace('_', ' ').title()}: {passed}/{total_cat} "
                      f"({success_rate:.1f}%) - {time_taken:.2f}s")

        # 生成覆盖率报告
        self.generate_coverage_report()

        # 保存详细报告到文件
        self.save_report_to_file()

        # 测试质量评估
        self.assess_test_quality(total_passed, total_failed)

    def save_report_to_file(self):
        """保存报告到文件"""
        report_data = {
            'timestamp': self.test_results['start_time'].isoformat(),
            'total_passed': sum(cat['passed'] for cat in self.test_results['test_categories'].values()),
            'total_failed': sum(cat['failed'] for cat in self.test_results['test_categories'].values()),
            'coverage_percentage': self.test_results['coverage_percentage'],
            'categories': self.test_results['test_categories']
        }

        report_file = f"auth_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n详细报告已保存到: {report_file}")
        except Exception as e:
            print(f"保存报告文件时出错: {e}")

    def assess_test_quality(self, total_passed, total_failed):
        """评估测试质量"""
        print("\n测试质量评估:")
        print("-" * 40)

        total_tests = total_passed + total_failed
        success_rate = total_passed / total_tests * 100 if total_tests > 0 else 0
        coverage = self.test_results['coverage_percentage']

        # 成功率评估
        if success_rate >= 95:
            print("✅ 测试成功率: 优秀")
        elif success_rate >= 90:
            print("✅ 测试成功率: 良好")
        elif success_rate >= 80:
            print("⚠️  测试成功率: 需要改进")
        else:
            print("❌ 测试成功率: 不及格")

        # 覆盖率评估
        if coverage >= 90:
            print("✅ 代码覆盖率: 优秀")
        elif coverage >= 80:
            print("✅ 代码覆盖率: 良好")
        elif coverage >= 70:
            print("⚠️  代码覆盖率: 需要改进")
        else:
            print("❌ 代码覆盖率: 不及格")

        # 测试数量评估
        if total_tests >= 100:
            print("✅ 测试数量: 充足")
        elif total_tests >= 50:
            print("✅ 测试数量: 良好")
        elif total_tests >= 25:
            print("⚠️  测试数量: 基本")
        else:
            print("❌ 测试数量: 不足")

        # 综合评估
        print("\n综合评估:")
        if success_rate >= 90 and coverage >= 80 and total_tests >= 50:
            print("🏆 测试质量: 优秀 - 生产环境就绪")
        elif success_rate >= 80 and coverage >= 70 and total_tests >= 25:
            print("👍 测试质量: 良好 - 可以发布")
        elif success_rate >= 70 and coverage >= 60:
            print("⚠️  测试质量: 一般 - 需要改进")
        else:
            print("❌ 测试质量: 不足 - 不建议发布")

        # 改进建议
        print("\n改进建议:")
        if coverage < 90:
            print("- 增加代码覆盖率，特别关注边界条件和错误处理")
        if total_failed > 0:
            print(f"- 修复 {total_failed} 个失败的测试")
        if total_tests < 100:
            print("- 增加更多测试用例，特别是集成测试和性能测试")

        # 安全性检查建议
        security_passed = self.test_results['test_categories']['security_tests']['passed']
        security_failed = self.test_results['test_categories']['security_tests']['failed']
        if security_failed > 0 or security_passed < 20:
            print("- 加强安全测试，确保认证系统的安全性")

        # 性能测试建议
        perf_passed = self.test_results['test_categories']['performance_tests']['passed']
        perf_failed = self.test_results['test_categories']['performance_tests']['failed']
        if perf_failed > 0 or perf_passed < 10:
            print("- 增加性能测试，确保系统在高负载下的表现")


def main():
    """主函数"""
    # 检查必要的测试目录
    required_dirs = [
        'unit/auth',
        'integration/auth',
        'security/auth',
        'performance/auth'
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        print("创建缺失的测试目录:")
        for dir_path in missing_dirs:
            os.makedirs(dir_path, exist_ok=True)
            print(f"  创建: {dir_path}")

    # 运行测试套件
    runner = TestSuiteRunner()
    runner.run_all_tests()


if __name__ == "__main__":
    main()