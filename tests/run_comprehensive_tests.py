#!/usr/bin/env python3
"""
Perfect21 综合测试执行器
统一执行所有测试并生成详细报告
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import xml.etree.ElementTree as ET

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """测试运行器"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.project_root = test_dir.parent
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'coverage': {},
            'performance': {},
            'security': {},
            'summary': {}
        }
    
    def run_all_tests(self, test_types: List[str] = None) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 Perfect21 综合测试开始")
        print(f"📅 开始时间: {self.results['start_time']}")
        print(f"📁 测试目录: {self.test_dir}")
        
        available_test_types = ['unit', 'integration', 'security', 'performance', 'e2e']
        
        if test_types is None:
            test_types = available_test_types
        
        # 检查pytest可用性
        if not self._check_pytest_available():
            print("❌ pytest不可用，请先安装: pip install -r tests/requirements.txt")
            return self.results
        
        for test_type in test_types:
            print(f"\n📋 正在运行 {test_type} 测试...")
            
            if test_type == 'unit':
                self.run_unit_tests()
            elif test_type == 'integration':
                self.run_integration_tests()
            elif test_type == 'security':
                self.run_security_tests()
            elif test_type == 'performance':
                self.run_performance_tests()
            elif test_type == 'e2e':
                self.run_e2e_tests()
        
        # 生成综合报告
        self.generate_final_report()
        
        return self.results
    
    def _check_pytest_available(self) -> bool:
        """检查pytest是否可用"""
        try:
            subprocess.run(['pytest', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_unit_tests(self):
        """运行单元测试"""
        cmd = [
            'python3', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'unit',
            '--cov=api', '--cov=config', '--cov=features', '--cov=main',
            '--cov-report=xml:coverage-unit.xml',
            '--cov-report=term-missing',
            '--junitxml=junit-unit.xml',
            '-v', '--tb=short'
        ]
        
        result = self._run_test_command(cmd, 'unit')
        self.results['test_suites']['unit'] = result
    
    def run_integration_tests(self):
        """运行集成测试"""
        cmd = [
            'python3', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'integration',
            '--junitxml=junit-integration.xml',
            '-v', '--tb=short'
        ]
        
        result = self._run_test_command(cmd, 'integration')
        self.results['test_suites']['integration'] = result
    
    def run_security_tests(self):
        """运行安全测试"""
        cmd = [
            'python3', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'security',
            '--junitxml=junit-security.xml',
            '-v', '--tb=short'
        ]
        
        result = self._run_test_command(cmd, 'security')
        self.results['test_suites']['security'] = result
        
        # 额外运行bandit安全扫描
        self._run_bandit_scan()
    
    def run_performance_tests(self):
        """运行性能测试"""
        cmd = [
            'python3', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'performance',
            '--benchmark-json=benchmark-results.json',
            '--junitxml=junit-performance.xml',
            '-v', '--tb=short'
        ]
        
        result = self._run_test_command(cmd, 'performance')
        self.results['test_suites']['performance'] = result
        
        # 运行负载测试
        self._run_load_tests()
    
    def run_e2e_tests(self):
        """运行E2E测试"""
        cmd = [
            'python3', '-m', 'pytest',
            str(self.test_dir),
            '-m', 'e2e',
            '--junitxml=junit-e2e.xml',
            '-v', '--tb=short'
        ]
        
        result = self._run_test_command(cmd, 'e2e')
        self.results['test_suites']['e2e'] = result
    
    def _run_test_command(self, cmd: List[str], test_type: str) -> Dict[str, Any]:
        """运行测试命令"""
        start_time = time.time()
        
        try:
            # 设置工作目录
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            duration = time.time() - start_time
            
            test_result = {
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            # 解析JUnit XML结果
            junit_file = f"junit-{test_type}.xml"
            if os.path.exists(junit_file):
                test_result['junit_stats'] = self._parse_junit_xml(junit_file)
            
            print(f"✅ {test_type} 测试完成 - {duration:.2f}s" if test_result['success'] else f"❌ {test_type} 测试失败")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            return {
                'command': ' '.join(cmd),
                'return_code': -1,
                'duration': time.time() - start_time,
                'error': 'Timeout',
                'success': False
            }
        except Exception as e:
            return {
                'command': ' '.join(cmd),
                'return_code': -1,
                'duration': time.time() - start_time,
                'error': str(e),
                'success': False
            }
    
    def _parse_junit_xml(self, junit_file: str) -> Dict[str, Any]:
        """解析JUnit XML文件"""
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            return {
                'tests': int(root.get('tests', 0)),
                'failures': int(root.get('failures', 0)),
                'errors': int(root.get('errors', 0)),
                'skipped': int(root.get('skipped', 0)),
                'time': float(root.get('time', 0.0))
            }
        except Exception as e:
            print(f"⚠️ 解析JUnit文件失败 {junit_file}: {e}")
            return {}
    
    def _run_bandit_scan(self):
        """运行Bandit安全扫描"""
        try:
            cmd = [
                'bandit', '-r', 'api', 'config', 'features', 'main',
                '-f', 'json', '-o', 'bandit-report.json'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            self.results['security']['bandit'] = {
                'return_code': result.returncode,
                'success': result.returncode == 0,
                'output_file': 'bandit-report.json'
            }
            
            print("✅ Bandit安全扫描完成")
            
        except FileNotFoundError:
            print("⚠️ Bandit未安装，跳过安全扫描")
    
    def _run_load_tests(self):
        """运行负载测试"""
        load_test_file = self.test_dir / 'load_test_auth_api.py'
        
        if not load_test_file.exists():
            print("⚠️ 负载测试文件不存在，跳过负载测试")
            return
        
        try:
            cmd = ['python', str(load_test_file)]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            self.results['performance']['load_test'] = {
                'return_code': result.returncode,
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print("✅ 负载测试完成" if result.returncode == 0 else "❌ 负载测试失败")
            
        except subprocess.TimeoutExpired:
            print("⚠️ 负载测试超时")
        except Exception as e:
            print(f"⚠️ 负载测试错误: {e}")
    
    def generate_final_report(self):
        """生成最终报告"""
        self.results['end_time'] = datetime.now().isoformat()
        
        # 计算统计信息
        summary = {
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'total_duration': 0,
            'success_rate': 0,
            'test_suites_run': 0
        }
        
        for suite_name, suite_result in self.results['test_suites'].items():
            if suite_result.get('success') and 'junit_stats' in suite_result:
                stats = suite_result['junit_stats']
                summary['total_tests'] += stats.get('tests', 0)
                summary['total_failed'] += stats.get('failures', 0) + stats.get('errors', 0)
                summary['total_skipped'] += stats.get('skipped', 0)
                summary['total_duration'] += suite_result.get('duration', 0)
                summary['test_suites_run'] += 1
        
        summary['total_passed'] = summary['total_tests'] - summary['total_failed'] - summary['total_skipped']
        
        if summary['total_tests'] > 0:
            summary['success_rate'] = (summary['total_passed'] / summary['total_tests']) * 100
        
        self.results['summary'] = summary
        
        # 保存结果到JSON文件
        self._save_results()
        
        # 生成Markdown报告
        self._generate_markdown_report()
        
        # 打印简要统计
        self._print_summary()
    
    def _save_results(self):
        """保存测试结果到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试结果已保存到: {filename}")
    
    def _generate_markdown_report(self):
        """生成Markdown报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_report_{timestamp}.md"
        
        summary = self.results['summary']
        
        report = f"""
# Perfect21 综合测试报告

## 测试摘要

- **开始时间**: {self.results['start_time']}
- **结束时间**: {self.results['end_time']}
- **总耗时**: {summary['total_duration']:.2f}秒
- **测试套件数**: {summary['test_suites_run']}

## 测试统计

- **总测试数**: {summary['total_tests']}
- **通过**: {summary['total_passed']} ✅
- **失败**: {summary['total_failed']} ❌
- **跳过**: {summary['total_skipped']} ⏭️
- **成功率**: {summary['success_rate']:.2f}%

## 测试套件结果

"""
        
        # 添加各个测试套件的结果
        for suite_name, suite_result in self.results['test_suites'].items():
            status = "✅ 通过" if suite_result.get('success') else "❌ 失败"
            duration = suite_result.get('duration', 0)
            
            report += f"### {suite_name.title()} 测试 {status}\n\n"
            report += f"- **执行时间**: {duration:.2f}秒\n"
            
            if 'junit_stats' in suite_result:
                stats = suite_result['junit_stats']
                report += f"- **测试数量**: {stats.get('tests', 0)}\n"
                report += f"- **通过**: {stats.get('tests', 0) - stats.get('failures', 0) - stats.get('errors', 0) - stats.get('skipped', 0)}\n"
                report += f"- **失败**: {stats.get('failures', 0)}\n"
                report += f"- **错误**: {stats.get('errors', 0)}\n"
                report += f"- **跳过**: {stats.get('skipped', 0)}\n"
            
            if not suite_result.get('success') and suite_result.get('stderr'):
                report += f"\n**错误输出**:\n```\n{suite_result['stderr'][:1000]}\n```\n"
            
            report += "\n"
        
        # 添加安全扫描结果
        if self.results.get('security'):
            report += "## 安全扫描\n\n"
            
            if 'bandit' in self.results['security']:
                bandit_result = self.results['security']['bandit']
                status = "✅ 通过" if bandit_result.get('success') else "❌ 失败"
                report += f"### Bandit 安全扫描 {status}\n\n"
                
                if bandit_result.get('output_file'):
                    report += f"- **报告文件**: {bandit_result['output_file']}\n"
        
        # 添加性能测试结果
        if self.results.get('performance'):
            report += "## 性能测试\n\n"
            
            if 'load_test' in self.results['performance']:
                load_result = self.results['performance']['load_test']
                status = "✅ 通过" if load_result.get('success') else "❌ 失败"
                report += f"### 负载测试 {status}\n\n"
        
        # 添加建议
        report += "\n## 建议\n\n"
        
        if summary['success_rate'] < 90:
            report += "- ❗ 测试成功率低于90%，建议检查失败的测试用例\n"
        
        if summary['total_failed'] > 0:
            report += "- ❗ 存在失败的测试，请查看详细错误信息\n"
        
        if summary['total_tests'] == 0:
            report += "- ⚠️ 未发现任何测试，请检查测试文件\n"
        
        if summary['success_rate'] >= 95 and summary['total_failed'] == 0:
            report += "- ✅ 所有测试都通过，代码质量良好\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Markdown报告已生成: {filename}")
    
    def _print_summary(self):
        """打印简要统计"""
        summary = self.results['summary']
        
        print("\n" + "="*60)
        print("🏁 Perfect21 测试综合报告")
        print("="*60)
        print(f"📈 总测试数: {summary['total_tests']}")
        print(f"✅ 通过: {summary['total_passed']}")
        print(f"❌ 失败: {summary['total_failed']}")
        print(f"⏭️ 跳过: {summary['total_skipped']}")
        print(f"📊 成功率: {summary['success_rate']:.2f}%")
        print(f"⏱️ 总耗时: {summary['total_duration']:.2f}秒")
        
        # 根据结果给出等级
        if summary['success_rate'] >= 95 and summary['total_failed'] == 0:
            print("🎆 等级: 优秀 - 所有测试通过！")
        elif summary['success_rate'] >= 85:
            print("🟡 等级: 良好 - 大部分测试通过")
        elif summary['success_rate'] >= 70:
            print("🟠 等级: 一般 - 需要改进")
        else:
            print("🔴 等级: 差 - 需要重点关注")
        
        print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Perfect21 综合测试执行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_comprehensive_tests.py                    # 运行所有测试
  python run_comprehensive_tests.py --types unit      # 只运行单元测试
  python run_comprehensive_tests.py --types unit integration security  # 运行多种测试
        """
    )
    
    parser.add_argument(
        '--types', 
        nargs='*',
        choices=['unit', 'integration', 'security', 'performance', 'e2e'],
        help='指定要运行的测试类型'
    )
    
    parser.add_argument(
        '--test-dir',
        type=Path,
        default=Path(__file__).parent,
        help='测试目录路径'
    )
    
    args = parser.parse_args()
    
    # 初始化测试运行器
    runner = TestRunner(args.test_dir)
    
    # 运行测试
    results = runner.run_all_tests(args.types)
    
    # 返回退出码
    summary = results.get('summary', {})
    if summary.get('total_failed', 0) > 0:
        sys.exit(1)  # 有失败的测试
    else:
        sys.exit(0)  # 所有测试通过


if __name__ == '__main__':
    main()
