#!/usr/bin/env python3
"""
Authentication System Test Runner
================================

统一的测试运行器，用于执行认证系统的所有单元测试
包含测试报告生成、覆盖率统计、性能测试等功能

作者: Claude Code AI Testing Team
版本: 1.0.0
创建时间: 2025-09-22
"""

import pytest
import sys
import os
from pathlib import Path
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class AuthTestRunner:
    """
    认证系统测试运行器
    
    功能：
    - 运行所有认证相关的单元测试
    - 生成测试报告
    - 统计代码覆盖率
    - 性能基准测试
    - 安全测试
    """
    
    def __init__(self, test_dir: str = None):
        self.test_dir = test_dir or str(Path(__file__).parent)
        self.project_root = project_root
        self.reports_dir = Path(self.test_dir) / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 测试模块列表
        self.test_modules = [
            "test_jwt_service.py",
            "test_password_encryption.py", 
            "test_user_registration_login.py",
            "test_mfa_functionality.py",
            "test_session_management.py"
        ]
    
    def run_all_tests(self, verbose: bool = True, coverage: bool = True,
                     generate_report: bool = True) -> Dict[str, Any]:
        """
        运行所有认证系统测试
        
        Args:
            verbose: 是否显示详细输出
            coverage: 是否统计代码覆盖率
            generate_report: 是否生成测试报告
            
        Returns:
            测试结果字典
        """
    # print("🚀 开始执行认证系统测试套件...")
    # print(f"📂 测试目录: {self.test_dir}")
    # print(f"📊 项目根目录: {self.project_root}")
    # print("="*60)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "test_results": {},
            "coverage_report": None,
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            }
        }
        
        # 运行各个测试模块
        for module in self.test_modules:
    # print(f"\n🧪 运行测试模块: {module}")
            module_result = self._run_single_test(module, verbose)
            results["test_results"][module] = module_result
            
            # 更新总计
            if module_result:
                results["summary"]["total_tests"] += module_result.get("total", 0)
                results["summary"]["passed"] += module_result.get("passed", 0)
                results["summary"]["failed"] += module_result.get("failed", 0)
                results["summary"]["skipped"] += module_result.get("skipped", 0)
                results["summary"]["errors"] += module_result.get("errors", 0)
        
        # 运行覆盖率测试
        if coverage:
    # print("\n📊 生成代码覆盖率报告...")
            results["coverage_report"] = self._run_coverage_test()
        
        # 生成测试报告
        if generate_report:
    # print("\n📝 生成测试报告...")
            self._generate_test_report(results)
        
        results["end_time"] = datetime.now().isoformat()
        
        # 显示总结
        self._print_summary(results["summary"])
        
        return results
    
    def _run_single_test(self, module: str, verbose: bool = True) -> Dict[str, Any]:
        """
        运行单个测试模块
        
        Args:
            module: 测试模块文件名
            verbose: 是否显示详细输出
            
        Returns:
            测试结果字典
        """
        test_file = Path(self.test_dir) / module
        
        if not test_file.exists():
    # print(f"⚠️  测试文件不存在: {test_file}")
            return None
        
        # 构建 pytest 命令
        cmd = [
            "python", "-m", "pytest",
            str(test_file),
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ]
        
        if verbose:
            cmd.append("-v")
        
        # 添加 JSON 报告
        json_report_file = self.reports_dir / f"{module.replace('.py', '')}_report.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report_file}"])
        
        try:
            # 运行测试
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 解析结果
            test_result = {
                "module": module,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0
            }
            
            # 尝试解析 JSON 报告
            if json_report_file.exists():
                try:
                    with open(json_report_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        summary = json_data.get("summary", {})
                        test_result.update({
                            "total": summary.get("total", 0),
                            "passed": summary.get("passed", 0),
                            "failed": summary.get("failed", 0),
                            "skipped": summary.get("skipped", 0),
                            "errors": summary.get("error", 0),
                            "duration": json_data.get("duration", 0)
                        })
                except Exception as e:
    # print(f"⚠️  解析JSON报告失败: {e}")
            
            # 显示结果
            if result.returncode == 0:
                print(f"✅ {module}: 测试通过 ({test_result['passed']} passed)")
            else:
                print(f"❌ {module}: 测试失败 ({test_result['failed']} failed, {test_result['errors']} errors)")
                if verbose and result.stderr:
                    print(f"错误信息: {result.stderr[:500]}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
    # print(f"⏰ {module}: 测试超时")
            return {
                "module": module,
                "exit_code": -1,
                "error": "timeout",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 1
            }
        except Exception as e:
    # print(f"💥 {module}: 运行异常 - {e}")
            return {
                "module": module,
                "exit_code": -1,
                "error": str(e),
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 1
            }
    
    def _run_coverage_test(self) -> Dict[str, Any]:
        """
        运行代码覆盖率测试
        
        Returns:
            覆盖率报告字典
        """
        try:
            # 运行带覆盖率的测试
            cmd = [
                "python", "-m", "pytest",
                self.test_dir,
                "--cov=backend",
                "--cov-report=term-missing",
                "--cov-report=html:reports/coverage_html",
                "--cov-report=json:reports/coverage.json",
                "--disable-warnings"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            coverage_data = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # 尝试解析覆盖率 JSON 报告
            coverage_json = self.reports_dir / "coverage.json"
            if coverage_json.exists():
                try:
                    with open(coverage_json, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        coverage_data["summary"] = json_data.get("totals", {})
                        coverage_data["files"] = json_data.get("files", {})
                except Exception as e:
    # print(f"⚠️  解析覆盖率JSON失败: {e}")
            
            return coverage_data
            
        except Exception as e:
    # print(f"💥 覆盖率测试异常: {e}")
            return {"error": str(e)}
    
    def _generate_test_report(self, results: Dict[str, Any]) -> None:
        """
        生成HTML测试报告
        
        Args:
            results: 测试结果数据
        """
        try:
            report_file = self.reports_dir / "test_report.html"
            
            html_content = self._build_html_report(results)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
    # print(f"📄 测试报告已生成: {report_file}")
            
            # 同时生成 JSON 报告
            json_file = self.reports_dir / "test_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
    # print(f"📄 JSON报告已生成: {json_file}")
            
        except Exception as e:
    # print(f"💥 生成报告异常: {e}")
    
    def _build_html_report(self, results: Dict[str, Any]) -> str:
        """
        构建HTML测试报告
        
        Args:
            results: 测试结果数据
            
        Returns:
            HTML内容字符串
        """
        summary = results["summary"]
        
        # 计算成功率
        total = summary["total_tests"]
        passed = summary["passed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>认证系统测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric h3 {{ margin: 0; font-size: 24px; }}
        .metric p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .success {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); }}
        .warning {{ background: linear-gradient(135deg, #ff9800 0%, #e68900 100%); }}
        .error {{ background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); }}
        .modules {{ margin-top: 30px; }}
        .module {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
        .module-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .module-content {{ padding: 15px; }}
        .status-pass {{ color: #4CAF50; font-weight: bold; }}
        .status-fail {{ color: #f44336; font-weight: bold; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); transition: width 0.3s ease; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Claude Enhancer 认证系统测试报告</h1>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="metric success">
                <h3>{total}</h3>
                <p>总测试数</p>
            </div>
            <div class="metric success">
                <h3>{passed}</h3>
                <p>通过测试</p>
            </div>
            <div class="metric {('error' if summary['failed'] > 0 else 'success')}">
                <h3>{summary['failed']}</h3>
                <p>失败测试</p>
            </div>
            <div class="metric {('warning' if summary['skipped'] > 0 else 'success')}">
                <h3>{summary['skipped']}</h3>
                <p>跳过测试</p>
            </div>
            <div class="metric">
                <h3>{success_rate:.1f}%</h3>
                <p>成功率</p>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {success_rate}%"></div>
        </div>
        
        <div class="modules">
            <h2>📋 测试模块详情</h2>
"""
        
        # 添加各个模块的详情
        for module, result in results["test_results"].items():
            if not result:
                continue
                
            status_class = "status-pass" if result["exit_code"] == 0 else "status-fail"
            status_text = "✅ 通过" if result["exit_code"] == 0 else "❌ 失败"
            
            module_success_rate = 0
            if result["total"] > 0:
                module_success_rate = (result["passed"] / result["total"]) * 100
            
            html += f"""
            <div class="module">
                <div class="module-header">
                    <h3>{module} <span class="{status_class}">{status_text}</span></h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {module_success_rate:.1f}%"></div>
                    </div>
                </div>
                <div class="module-content">
                    <p><strong>总计:</strong> {result['total']} | 
                       <strong>通过:</strong> {result['passed']} | 
                       <strong>失败:</strong> {result['failed']} | 
                       <strong>跳过:</strong> {result['skipped']} | 
                       <strong>错误:</strong> {result['errors']}</p>
                    <p><strong>执行时间:</strong> {result.get('duration', 0):.2f}秒</p>
                    <p><strong>成功率:</strong> {module_success_rate:.1f}%</p>
                </div>
            </div>
"""
        
        # 添加覆盖率信息
        coverage = results.get("coverage_report")
        if coverage and "summary" in coverage:
            cov_summary = coverage["summary"]
            coverage_percent = cov_summary.get("percent_covered", 0)
            
            html += f"""
            <div class="module">
                <div class="module-header">
                    <h3>📊 代码覆盖率报告</h3>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {coverage_percent}%"></div>
                    </div>
                </div>
                <div class="module-content">
                    <p><strong>覆盖率:</strong> {coverage_percent:.1f}%</p>
                    <p><strong>总行数:</strong> {cov_summary.get('num_statements', 0)}</p>
                    <p><strong>覆盖行数:</strong> {cov_summary.get('covered_lines', 0)}</p>
                    <p><strong>缺失行数:</strong> {cov_summary.get('missing_lines', 0)}</p>
                </div>
            </div>
"""
        
        html += """
        </div>
        
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
            <p>🤖 由 Claude Code AI Testing Team 自动生成</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """
        打印测试总结
        
        Args:
            summary: 测试总结数据
        """
    # print("\n" + "="*60)
    # print("🎯 测试执行总结")
    # print("="*60)
        
        total = summary["total_tests"]
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        errors = summary["errors"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
    # print(f"📊 总测试数:     {total}")
    # print(f"✅ 通过测试:     {passed}")
    # print(f"❌ 失败测试:     {failed}")
    # print(f"⚠️  跳过测试:     {skipped}")
    # print(f"💥 错误测试:     {errors}")
    # print(f"🎯 成功率:       {success_rate:.1f}%")
        
        if failed == 0 and errors == 0:
    # print("\n🎉 所有测试通过！认证系统质量良好。")
        elif failed > 0 or errors > 0:
    # print("\n⚠️  发现测试失败，请检查并修复问题。")
        
    # print("="*60)
    
    def run_specific_test(self, test_name: str, verbose: bool = True) -> Dict[str, Any]:
        """
        运行特定的测试模块
        
        Args:
            test_name: 测试模块名称
            verbose: 是否显示详细输出
            
        Returns:
            测试结果字典
        """
        if test_name not in self.test_modules:
    # print(f"❌ 未找到测试模块: {test_name}")
    # print(f"可用模块: {', '.join(self.test_modules)}")
            return None
        
    # print(f"🧪 运行特定测试: {test_name}")
        return self._run_single_test(test_name, verbose)
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """
        运行性能基准测试
        
        Returns:
            性能测试结果
        """
    # print("🚀 运行性能基准测试...")
        
        # 这里可以添加专门的性能测试
        performance_tests = [
            "test_jwt_service.py::TestJWTTokenManager::test_token_timing_attacks_resistance",
            "test_password_encryption.py::TestPasswordManager::test_password_hashing_performance",
            "test_session_management.py::TestSessionManagerIntegration::test_concurrent_session_operations"
        ]
        
        results = {}
        
        for test in performance_tests:
            try:
                cmd = [
                    "python", "-m", "pytest",
                    test,
                    "--benchmark-only",
                    "-v"
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                results[test] = {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            except Exception as e:
                results[test] = {"error": str(e)}
        
        return results


def main():
    """
    主函数 - 命令行入口
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Enhancer 认证系统测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_runner.py                    # 运行所有测试
  python test_runner.py --module jwt       # 运行JWT测试
  python test_runner.py --no-coverage      # 跳过覆盖率测试
  python test_runner.py --performance      # 运行性能测试
        """
    )
    
    parser.add_argument(
        "--module", "-m",
        help="运行特定测试模块 (jwt, password, user, mfa, session)"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="跳过代码覆盖率测试"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="跳过测试报告生成"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="运行性能基准测试"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，减少输出"
    )
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = AuthTestRunner()
    
    # 模块名称映射
    module_map = {
        "jwt": "test_jwt_service.py",
        "password": "test_password_encryption.py",
        "user": "test_user_registration_login.py",
        "mfa": "test_mfa_functionality.py",
        "session": "test_session_management.py"
    }
    
    try:
        if args.performance:
            # 运行性能测试
            results = runner.run_performance_tests()
    # print("\n🏁 性能测试完成")
            
        elif args.module:
            # 运行特定模块
            if args.module in module_map:
                test_file = module_map[args.module]
                results = runner.run_specific_test(test_file, not args.quiet)
            else:
    # print(f"❌ 未知模块: {args.module}")
    # print(f"可用模块: {', '.join(module_map.keys())}")
                sys.exit(1)
                
        else:
            # 运行所有测试
            results = runner.run_all_tests(
                verbose=not args.quiet,
                coverage=not args.no_coverage,
                generate_report=not args.no_report
            )
        
        # 根据测试结果设置退出码
        if results and isinstance(results, dict):
            if "summary" in results:
                summary = results["summary"]
                if summary["failed"] > 0 or summary["errors"] > 0:
                    sys.exit(1)
            elif "exit_code" in results:
                sys.exit(results["exit_code"])
        
    except KeyboardInterrupt:
    # print("\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
    # print(f"💥 测试运行器异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
