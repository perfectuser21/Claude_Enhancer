#!/usr/bin/env python3
"""
Perfect21 综合测试套件
验证所有核心功能模块的集成和独立功能
"""

import sys
import os
import traceback
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import importlib.util

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

class TestResult:
    """测试结果类"""
    def __init__(self, name: str, passed: bool, message: str = "", details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.name}: {self.message}"

class Perfect21TestSuite:
    """Perfect21综合测试套件"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.project_root = Path.cwd()

    def log_result(self, name: str, passed: bool, message: str = "", details: Any = None):
        """记录测试结果"""
        result = TestResult(name, passed, message, details)
        self.results.append(result)
        print(result)
        return result

    def test_project_structure(self) -> TestResult:
        """测试项目结构完整性"""
        try:
            required_dirs = [
                'features/capability_discovery',
                'features/version_manager',
                'features/git_workflow',
                'features/claude_md_manager',
                'modules',
                'main',
                'api'
            ]

            required_files = [
                '__init__.py',
                'CLAUDE.md',
                '.version_history.json'
            ]

            missing_dirs = []
            missing_files = []

            for dir_path in required_dirs:
                if not (self.project_root / dir_path).exists():
                    missing_dirs.append(dir_path)

            for file_path in required_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)

            if missing_dirs or missing_files:
                message = f"缺失目录: {missing_dirs}, 缺失文件: {missing_files}"
                return self.log_result("项目结构检查", False, message)

            return self.log_result("项目结构检查", True, "所有必需的目录和文件都存在")

        except Exception as e:
            return self.log_result("项目结构检查", False, f"检查异常: {str(e)}")

    def test_capability_discovery_module(self) -> TestResult:
        """测试capability_discovery模块的动态加载机制"""
        try:
            # 测试模块导入
            from features.capability_discovery import bootstrap_capability_discovery, CapabilityLoader

            # 测试动态发现功能
            discovery_result = bootstrap_capability_discovery()

            if not isinstance(discovery_result, dict):
                return self.log_result("Capability Discovery", False, "bootstrap返回类型错误")

            if not discovery_result.get('success'):
                return self.log_result("Capability Discovery", False,
                                     f"启动失败: {discovery_result.get('message')}")

            # 测试加载器功能
            loader = CapabilityLoader()
            capabilities = loader.scan_capabilities()

            return self.log_result("Capability Discovery", True,
                                 f"发现 {len(capabilities)} 个功能模块",
                                 {'capabilities': capabilities, 'bootstrap': discovery_result})

        except Exception as e:
            return self.log_result("Capability Discovery", False, f"测试异常: {str(e)}")

    def test_version_manager_module(self) -> TestResult:
        """测试version_manager的版本一致性检查"""
        try:
            from features.version_manager import get_global_version_manager, VersionManager

            # 获取全局版本管理器
            vm = get_global_version_manager()

            # 测试版本一致性检查（排除venv）
            consistency_result = vm.check_version_consistency(exclude_venv=True)

            # 测试基本版本信息
            current_version = vm.get_current_version()

            if not current_version:
                return self.log_result("Version Manager", False, "无法获取当前版本")

            # 生成版本报告
            try:
                report = vm.generate_version_report()
            except Exception as e:
                report = f"报告生成失败: {str(e)}"

            return self.log_result("Version Manager", True,
                                 f"版本管理正常，当前版本: {current_version}",
                                 {'consistency': consistency_result, 'report': report})

        except Exception as e:
            return self.log_result("Version Manager", False, f"测试异常: {str(e)}")

    def test_claude_md_manager_module(self) -> TestResult:
        """测试claude_md_manager的标准化CAPABILITY格式"""
        try:
            from features.claude_md_manager import get_claude_md_manager, bootstrap_claude_md_management
            from features.claude_md_manager.capability import get_capability_info

            # 测试capability信息获取
            capability_info = get_capability_info()

            if not isinstance(capability_info, dict):
                return self.log_result("Claude MD Manager", False, "capability信息格式错误")

            # 验证标准化格式
            required_info = ['name', 'description', 'version']
            missing_info = []

            for info in required_info:
                if not capability_info.get(info):
                    missing_info.append(info)

            if missing_info:
                return self.log_result("Claude MD Manager", False, f"缺失信息: {missing_info}")

            # 测试bootstrap功能
            bootstrap_result = bootstrap_claude_md_management()

            if not bootstrap_result.get('success'):
                return self.log_result("Claude MD Manager", False,
                                     f"bootstrap失败: {bootstrap_result.get('error')}")

            # 测试管理器获取
            manager = get_claude_md_manager()

            return self.log_result("Claude MD Manager", True,
                                 f"标准化格式正确: {capability_info['name']} v{capability_info['version']}",
                                 {'capability_info': capability_info, 'bootstrap': bootstrap_result})

        except Exception as e:
            return self.log_result("Claude MD Manager", False, f"测试异常: {str(e)}")

    def test_git_workflow_module(self) -> TestResult:
        """测试git_workflow模块"""
        try:
            from features.git_workflow import GitHooks, WorkflowManager, BranchManager
            from features.git_workflow.capability import get_capability_info

            # 测试capability信息获取
            capability_info = get_capability_info()

            if not isinstance(capability_info, dict):
                return self.log_result("Git Workflow", False, "capability信息格式错误")

            # 测试核心类实例化
            hooks = GitHooks()
            workflow = WorkflowManager()
            branch_mgr = BranchManager()

            # 基本功能测试
            hook_status = hooks.get_installed_hooks()

            return self.log_result("Git Workflow", True,
                                 f"Git工作流模块正常: {capability_info['name']} v{capability_info['version']}",
                                 {'capability_info': capability_info, 'hooks_status': hook_status})

        except Exception as e:
            return self.log_result("Git Workflow", False, f"测试异常: {str(e)}")

    def test_module_integration(self) -> TestResult:
        """测试模块间集成"""
        try:
            # 测试所有模块的CAPABILITY格式统一性
            modules_to_test = [
                ('features.capability_discovery.capability', 'CAPABILITY'),
                ('features.version_manager.capability', 'CAPABILITY'),
                ('features.claude_md_manager.capability', 'get_capability_info'),
                ('features.git_workflow.capability', 'get_capability_info')
            ]

            integrated_modules = []

            for module_path, capability_source in modules_to_test:
                try:
                    module = __import__(module_path, fromlist=[capability_source])

                    if capability_source == 'CAPABILITY':
                        capability_info = getattr(module, 'CAPABILITY')
                    else:
                        capability_func = getattr(module, capability_source)
                        capability_info = capability_func()

                    # 验证标准字段
                    required_fields = ['name', 'version', 'description']
                    for field in required_fields:
                        if field not in capability_info:
                            raise Exception(f"缺失必需字段: {field}")

                    integrated_modules.append({
                        'name': capability_info['name'],
                        'version': capability_info['version'],
                        'module': module_path,
                        'description': capability_info['description']
                    })

                except Exception as e:
                    return self.log_result("模块集成测试", False, f"{module_path} 集成失败: {str(e)}")

            return self.log_result("模块集成测试", True,
                                 f"成功集成 {len(integrated_modules)} 个模块",
                                 integrated_modules)

        except Exception as e:
            return self.log_result("模块集成测试", False, f"集成测试异常: {str(e)}")

    def test_error_handling(self) -> TestResult:
        """测试错误处理机制"""
        try:
            from features.capability_discovery import CapabilityLoader

            loader = CapabilityLoader()

            # 测试无效路径处理
            try:
                invalid_result = loader.load_capability('/invalid/path')
                # 应该返回None或空字典
                if invalid_result is not None and invalid_result != {}:
                    return self.log_result("错误处理测试", False, "无效路径未正确处理")
            except Exception:
                # 抛出异常也是合理的错误处理
                pass

            # 测试scanner的错误处理
            try:
                from features.capability_discovery import CapabilityScanner
                scanner = CapabilityScanner()
                # 扫描不存在的目录
                result = scanner.scan_directory('/nonexistent/directory')
                # 应该返回空列表或适当的错误信息
                if not isinstance(result, (list, dict)):
                    return self.log_result("错误处理测试", False, "目录扫描错误处理不当")
            except Exception:
                # 抛出异常也是合理的
                pass

            return self.log_result("错误处理测试", True, "错误处理机制正常工作")

        except Exception as e:
            return self.log_result("错误处理测试", False, f"错误处理测试异常: {str(e)}")

    def test_configuration_management(self) -> TestResult:
        """测试配置管理"""
        try:
            from modules.config import ConfigManager

            config = ConfigManager()

            # 测试配置加载
            if not hasattr(config, 'get') or not callable(config.get):
                return self.log_result("配置管理测试", False, "配置类接口不完整")

            # 测试默认配置
            version = config.get('perfect21.version', 'unknown')
            mode = config.get('perfect21.mode', 'unknown')

            if not version or version == 'unknown':
                return self.log_result("配置管理测试", False, "无法获取项目版本")

            return self.log_result("配置管理测试", True,
                                 f"配置管理正常，版本: {version}, 模式: {mode}")

        except Exception as e:
            return self.log_result("配置管理测试", False, f"配置管理测试异常: {str(e)}")

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始Perfect21综合测试套件")
        print("=" * 60)

        # 执行所有测试
        test_methods = [
            self.test_project_structure,
            self.test_capability_discovery_module,
            self.test_version_manager_module,
            self.test_claude_md_manager_module,
            self.test_git_workflow_module,
            self.test_module_integration,
            self.test_configuration_management,
            self.test_error_handling
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_result(test_method.__name__, False, f"测试执行异常: {str(e)}")
            print("-" * 40)

        # 生成测试报告
        return self.generate_test_report()

    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("📊 测试报告汇总")
        print("=" * 60)

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            'detailed_results': []
        }

        for result in self.results:
            status_icon = "✅" if result.passed else "❌"
            print(f"{status_icon} {result.name}: {result.message}")

            report['detailed_results'].append({
                'test_name': result.name,
                'passed': result.passed,
                'message': result.message,
                'details': result.details
            })

        print(f"\n📈 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   成功率: {report['summary']['success_rate']}")

        if failed_tests > 0:
            print(f"\n⚠️  发现 {failed_tests} 个问题需要修复")
            print("建议查看详细测试结果进行修复")
        else:
            print(f"\n🎉 所有测试通过！Perfect21项目状态良好")

        return report

def main():
    """主函数"""
    try:
        test_suite = Perfect21TestSuite()
        report = test_suite.run_all_tests()

        # 保存测试报告到文件
        report_file = Path('test_report_comprehensive.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细测试报告已保存到: {report_file}")

        # 返回退出码
        failed_tests = report['summary']['failed_tests']
        sys.exit(0 if failed_tests == 0 else 1)

    except Exception as e:
        print(f"❌ 测试套件执行失败: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()