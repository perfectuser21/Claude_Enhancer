#!/usr/bin/env python3
"""
Perfect21认证系统测试运行器
统一执行所有认证相关测试并生成详细报告
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path


class AuthTestRunner:
    """认证测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'test_categories': {},
            'coverage': {},
            'summary': {}
        }

    def setup_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")

        # 设置环境变量
        os.environ.update({
            'JWT_SECRET_KEY': 'test_secret_key_for_testing_only_do_not_use_in_production',
            'TESTING': 'true',
            'LOG_LEVEL': 'INFO',
            'DATABASE_URL': 'sqlite:///test_auth.db'
        })

        # 清理旧的测试数据库
        test_dbs = [
            'data/test_auth.db',
            'data/test_auth_integration.db',
            'data/test_auth_security.db',
            'data/test_auth_performance.db',
            'data/test_auth_concurrent.db',
            'data/test_auth_load.db',
            'data/test_auth_crypto.db',
            'data/test_auth_session.db',
            'data/test_auth_user.db',
            'data/test_auth_brute_force.db'
        ]

        for db_path in test_dbs:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    print(f"  ✅ 清理测试数据库: {db_path}")
                except Exception as e:
                    print(f"  ⚠️  无法删除 {db_path}: {e}")

        # 确保数据目录存在
        os.makedirs('data', exist_ok=True)

        print("  ✅ 环境设置完成")

    def run_test_suite(self, name, test_path, markers=None):
        """运行测试套件"""
        print(f"\n📋 运行 {name}...")
        print(f"   路径: {test_path}")

        start_time = time.time()

        # 构建pytest命令
        cmd = [
            sys.executable, '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short',
            '--color=yes',
            '--durations=5'
        ]

        if markers:
            cmd.extend(['-m', markers])

        # 添加覆盖率选项（仅对单元测试和集成测试）
        if 'unit' in name.lower() or 'integration' in name.lower():
            cmd.extend([
                '--cov=features.auth_system',
                '--cov=api.auth_api',
                '--cov-append'
            ])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5分钟超时
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # 解析结果
            output = result.stdout
            error_output = result.stderr

            # 统计测试结果
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            skipped = output.count(' SKIPPED')
            errors = output.count(' ERROR')

            self.test_results['test_categories'][name] = {
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'errors': errors,
                'execution_time': execution_time,
                'return_code': result.returncode
            }

            # 显示结果
            total = passed + failed + skipped + errors
            if total > 0:
                success_rate = (passed / total) * 100
                print(f"  📊 结果: {passed} 通过, {failed} 失败, {skipped} 跳过, {errors} 错误")
                print(f"  ⏱️  耗时: {execution_time:.2f}s")
                print(f"  📈 成功率: {success_rate:.1f}%")

                if failed > 0 or errors > 0:
                    print(f"  ❌ 有测试失败，检查详细输出")
                    # 显示失败的测试
                    lines = output.split('\n')
                    for line in lines:
                        if 'FAILED' in line or 'ERROR' in line:
                            print(f"    {line}")
                else:
                    print(f"  ✅ 所有测试通过")
            else:
                print(f"  ⚠️  未找到测试或测试未执行")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"  ⏰ 测试超时（5分钟）")
            return False
        except Exception as e:
            print(f"  ❌ 运行测试时出错: {e}")
            return False

    def run_coverage_report(self):
        """生成覆盖率报告"""
        print(f"\n📊 生成代码覆盖率报告...")

        try:
            # 生成覆盖率报告
            cmd = [
                sys.executable, '-m', 'coverage',
                'report',
                '--include=features/auth_system/*,api/auth_api.py',
                '--show-missing'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )

            if result.returncode == 0:
                output = result.stdout
                print("覆盖率详情:")
                print(output)

                # 提取总体覆盖率
                for line in output.split('\n'):
                    if 'TOTAL' in line:
                        parts = line.split()
                        for part in parts:
                            if '%' in part:
                                try:
                                    coverage_pct = float(part.rstrip('%'))
                                    self.test_results['coverage']['percentage'] = coverage_pct
                                    break
                                except ValueError:
                                    continue

                # 生成HTML报告
                html_cmd = [
                    sys.executable, '-m', 'coverage',
                    'html',
                    '--include=features/auth_system/*,api/auth_api.py',
                    '-d', 'htmlcov'
                ]

                subprocess.run(html_cmd, cwd=str(self.project_root))
                print(f"  ✅ HTML覆盖率报告生成完成: htmlcov/index.html")

            else:
                print(f"  ⚠️  覆盖率报告生成失败")

        except Exception as e:
            print(f"  ❌ 生成覆盖率报告时出错: {e}")

    def run_all_tests(self):
        """运行所有认证测试"""
        print("🚀 Perfect21认证系统测试套件")
        print("=" * 60)

        self.setup_environment()

        # 测试套件配置
        test_suites = [
            {
                'name': '单元测试',
                'path': 'tests/unit/auth/',
                'required': True,
                'description': '测试密码加密、JWT生成验证等核心功能'
            },
            {
                'name': '集成测试',
                'path': 'tests/integration/auth/',
                'required': True,
                'description': '测试登录流程、令牌刷新等完整业务流程'
            },
            {
                'name': '安全测试',
                'path': 'tests/security/auth/',
                'required': True,
                'description': '测试SQL注入、暴力破解防护等安全特性'
            },
            {
                'name': '性能测试',
                'path': 'tests/performance/auth/',
                'required': False,
                'description': '测试并发登录、响应时间等性能指标'
            }
        ]

        successful_suites = 0
        total_suites = len(test_suites)

        for suite in test_suites:
            if os.path.exists(suite['path']):
                success = self.run_test_suite(suite['name'], suite['path'])
                if success:
                    successful_suites += 1
            else:
                print(f"\n⚠️  跳过 {suite['name']}: 路径 {suite['path']} 不存在")
                if suite['required']:
                    print(f"   这是必需的测试套件，建议创建相关测试")

        # 生成覆盖率报告
        self.run_coverage_report()

        # 生成汇总报告
        self.generate_summary()

        return successful_suites == total_suites

    def generate_summary(self):
        """生成测试汇总"""
        print(f"\n📋 测试汇总报告")
        print("=" * 60)

        # 计算总计
        total_passed = sum(suite.get('passed', 0) for suite in self.test_results['test_categories'].values())
        total_failed = sum(suite.get('failed', 0) for suite in self.test_results['test_categories'].values())
        total_skipped = sum(suite.get('skipped', 0) for suite in self.test_results['test_categories'].values())
        total_errors = sum(suite.get('errors', 0) for suite in self.test_results['test_categories'].values())
        total_tests = total_passed + total_failed + total_skipped + total_errors
        total_time = sum(suite.get('execution_time', 0) for suite in self.test_results['test_categories'].values())

        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'skipped': total_skipped,
            'errors': total_errors,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time
        }

        print(f"总测试数: {total_tests}")
        print(f"通过: {total_passed}")
        print(f"失败: {total_failed}")
        print(f"跳过: {total_skipped}")
        print(f"错误: {total_errors}")
        print(f"成功率: {self.test_results['summary']['success_rate']:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")

        if 'percentage' in self.test_results['coverage']:
            coverage_pct = self.test_results['coverage']['percentage']
            print(f"代码覆盖率: {coverage_pct:.1f}%")

        # 分类详情
        print(f"\n📊 分类详情:")
        for suite_name, results in self.test_results['test_categories'].items():
            passed = results.get('passed', 0)
            failed = results.get('failed', 0)
            skipped = results.get('skipped', 0)
            errors = results.get('errors', 0)
            time_taken = results.get('execution_time', 0)
            total_suite = passed + failed + skipped + errors

            if total_suite > 0:
                success_rate = passed / total_suite * 100
                status = "✅" if failed == 0 and errors == 0 else "❌"
                print(f"  {status} {suite_name}: {passed}/{total_suite} "
                      f"({success_rate:.1f}%) - {time_taken:.2f}s")

        # 质量评估
        self.assess_quality()

        # 保存报告
        self.save_report()

    def assess_quality(self):
        """评估测试质量"""
        print(f"\n🎯 质量评估:")

        summary = self.test_results['summary']
        coverage_pct = self.test_results['coverage'].get('percentage', 0)

        # 成功率评估
        success_rate = summary['success_rate']
        if success_rate >= 95:
            print("✅ 测试成功率: 优秀 (≥95%)")
        elif success_rate >= 90:
            print("🟡 测试成功率: 良好 (≥90%)")
        elif success_rate >= 80:
            print("🟠 测试成功率: 一般 (≥80%)")
        else:
            print("🔴 测试成功率: 需要改进 (<80%)")

        # 覆盖率评估
        if coverage_pct >= 90:
            print("✅ 代码覆盖率: 优秀 (≥90%)")
        elif coverage_pct >= 80:
            print("🟡 代码覆盖率: 良好 (≥80%)")
        elif coverage_pct >= 70:
            print("🟠 代码覆盖率: 一般 (≥70%)")
        else:
            print("🔴 代码覆盖率: 需要改进 (<70%)")

        # 测试数量评估
        total_tests = summary['total_tests']
        if total_tests >= 100:
            print("✅ 测试数量: 充足 (≥100)")
        elif total_tests >= 50:
            print("🟡 测试数量: 良好 (≥50)")
        elif total_tests >= 25:
            print("🟠 测试数量: 基本 (≥25)")
        else:
            print("🔴 测试数量: 不足 (<25)")

        # 综合评估
        if success_rate >= 90 and coverage_pct >= 80 and total_tests >= 50:
            print("🏆 综合评估: 优秀 - 生产环境就绪")
        elif success_rate >= 80 and coverage_pct >= 70 and total_tests >= 25:
            print("👍 综合评估: 良好 - 可以发布")
        else:
            print("⚠️  综合评估: 需要改进")

        # 建议
        print(f"\n💡 改进建议:")
        if summary['failed'] > 0:
            print(f"  - 修复 {summary['failed']} 个失败的测试")
        if summary['errors'] > 0:
            print(f"  - 修复 {summary['errors']} 个错误的测试")
        if coverage_pct < 90:
            print(f"  - 提高代码覆盖率至90%以上（当前{coverage_pct:.1f}%）")
        if total_tests < 100:
            print(f"  - 增加更多测试用例（当前{total_tests}个）")

        # 性能建议
        perf_results = self.test_results['test_categories'].get('性能测试', {})
        if perf_results.get('failed', 0) > 0:
            print(f"  - 优化性能，确保在高负载下的表现")

        # 安全建议
        security_results = self.test_results['test_categories'].get('安全测试', {})
        if security_results.get('failed', 0) > 0:
            print(f"  - 修复安全漏洞，加强防护措施")

    def save_report(self):
        """保存测试报告"""
        self.test_results['end_time'] = datetime.now().isoformat()

        report_file = f"auth_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"⚠️  保存报告时出错: {e}")


def main():
    """主函数"""
    runner = AuthTestRunner()

    print("Perfect21认证系统测试套件")
    print("包含：单元测试、集成测试、安全测试、性能测试")
    print("目标：>90%代码覆盖率")
    print()

    success = runner.run_all_tests()

    if success:
        print("\n🎉 所有测试套件运行完成！")
        exit(0)
    else:
        print("\n❌ 部分测试套件失败")
        exit(1)


if __name__ == "__main__":
    main()