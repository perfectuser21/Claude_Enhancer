#!/usr/bin/env python3
"""
Perfect21 实际功能测试套件
专门测试已实现的核心功能
"""

import sys
import os
import traceback
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

class SimplifiedTestSuite:
    """简化的测试套件，专注于实际功能验证"""

    def __init__(self):
        self.results = []
        self.project_root = Path.cwd()

    def log_test(self, name: str, success: bool, message: str, details: Any = None):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'name': name,
            'success': success,
            'message': message,
            'details': str(details) if details else None  # 转换为字符串避免序列化问题
        }
        self.results.append(result)
        print(f"{status} {name}: {message}")
        return success

    def test_project_structure(self):
        """测试项目结构"""
        try:
            required_paths = [
                'features/capability_discovery',
                'features/version_manager',
                'features/git_workflow',
                'features/claude_md_manager',
                'modules/config.py',
                '__init__.py',
                'CLAUDE.md'
            ]

            missing = []
            for path in required_paths:
                if not (self.project_root / path).exists():
                    missing.append(path)

            if missing:
                return self.log_test("项目结构", False, f"缺失路径: {missing}")

            return self.log_test("项目结构", True, "项目结构完整")

        except Exception as e:
            return self.log_test("项目结构", False, f"检查异常: {e}")

    def test_capability_discovery(self):
        """测试capability_discovery模块"""
        try:
            # 测试基础导入
            from features.capability_discovery import bootstrap_capability_discovery
            from features.capability_discovery.scanner import CapabilityScanner

            # 测试bootstrap功能
            result = bootstrap_capability_discovery()
            if not result.get('success'):
                return self.log_test("Capability Discovery", False,
                                   f"Bootstrap失败: {result.get('message')}")

            # 测试扫描器
            scanner = CapabilityScanner()
            scan_result = scanner.scan_all_features()

            return self.log_test("Capability Discovery", True,
                               f"功能发现正常，扫描到 {len(scan_result)} 个模块",
                               f"Bootstrap: {result.get('message')}")

        except Exception as e:
            return self.log_test("Capability Discovery", False, f"测试异常: {e}")

    def test_version_manager(self):
        """测试version_manager模块"""
        try:
            # 直接导入核心类
            from features.version_manager.version_manager import VersionManager

            vm = VersionManager()

            # 测试基本功能
            current_version = vm.get_current_version()
            if not current_version:
                return self.log_test("Version Manager", False, "无法获取当前版本")

            # 测试版本一致性检查
            try:
                consistency = vm.check_version_consistency(exclude_venv=True)
                consistency_msg = f"一致性检查: {consistency.get('consistent', 'Unknown')}"
            except Exception as e:
                consistency_msg = f"一致性检查异常: {e}"

            return self.log_test("Version Manager", True,
                               f"版本管理正常，当前版本: {current_version}",
                               consistency_msg)

        except Exception as e:
            return self.log_test("Version Manager", False, f"测试异常: {e}")

    def test_claude_md_manager(self):
        """测试claude_md_manager模块"""
        try:
            from features.claude_md_manager import get_claude_md_manager
            from features.claude_md_manager.capability import get_capability_info

            # 测试capability信息
            info = get_capability_info()
            if not isinstance(info, dict) or not info.get('name'):
                return self.log_test("Claude MD Manager", False, "Capability信息无效")

            # 测试管理器获取
            manager = get_claude_md_manager()
            if not manager:
                return self.log_test("Claude MD Manager", False, "无法获取管理器实例")

            return self.log_test("Claude MD Manager", True,
                               f"模块正常，名称: {info['name']}, 版本: {info['version']}")

        except Exception as e:
            return self.log_test("Claude MD Manager", False, f"测试异常: {e}")

    def test_git_workflow(self):
        """测试git_workflow模块"""
        try:
            from features.git_workflow import GitHooks, WorkflowManager
            from features.git_workflow.capability import get_capability_info

            # 测试capability信息
            info = get_capability_info()
            if not isinstance(info, dict) or not info.get('name'):
                return self.log_test("Git Workflow", False, "Capability信息无效")

            # 测试核心类实例化
            hooks = GitHooks()
            workflow = WorkflowManager()

            # 基本功能测试
            installed_hooks = hooks.get_installed_hooks()

            return self.log_test("Git Workflow", True,
                               f"模块正常，名称: {info['name']}, 版本: {info['version']}",
                               f"已安装钩子: {len(installed_hooks)}")

        except Exception as e:
            return self.log_test("Git Workflow", False, f"测试异常: {e}")

    def test_configuration(self):
        """测试配置管理"""
        try:
            from modules.config import ConfigManager

            config = ConfigManager()

            # 测试基本配置
            version = config.get('perfect21.version')
            mode = config.get('perfect21.mode')

            if not version:
                return self.log_test("配置管理", False, "无法获取版本配置")

            return self.log_test("配置管理", True,
                               f"配置正常，版本: {version}, 模式: {mode}")

        except Exception as e:
            return self.log_test("配置管理", False, f"测试异常: {e}")

    def test_integration_status(self):
        """测试模块集成状态"""
        try:
            # 检查注册文件
            registration_file = self.project_root / 'core/claude-code-unified-agents/perfect21_capabilities.json'
            if registration_file.exists():
                import json
                with open(registration_file, 'r', encoding='utf-8') as f:
                    capabilities = json.load(f)

                registered_count = len(capabilities)
                registered_names = list(capabilities.keys())

                return self.log_test("集成状态", True,
                                   f"已注册 {registered_count} 个功能模块",
                                   f"模块: {registered_names}")
            else:
                return self.log_test("集成状态", False, "未找到功能注册文件")

        except Exception as e:
            return self.log_test("集成状态", False, f"测试异常: {e}")

    def test_system_status(self):
        """测试系统整体状态"""
        try:
            # 统计测试结果
            passed_tests = sum(1 for r in self.results if r['success'])
            total_tests = len(self.results)

            if total_tests == 0:
                return self.log_test("系统状态", False, "没有执行任何测试")

            success_rate = (passed_tests / total_tests) * 100

            status_msg = f"系统健康度: {success_rate:.1f}% ({passed_tests}/{total_tests})"

            if success_rate >= 80:
                return self.log_test("系统状态", True, f"系统状态良好 - {status_msg}")
            elif success_rate >= 60:
                return self.log_test("系统状态", True, f"系统状态一般 - {status_msg}")
            else:
                return self.log_test("系统状态", False, f"系统状态不佳 - {status_msg}")

        except Exception as e:
            return self.log_test("系统状态", False, f"状态检查异常: {e}")

    def run_all_tests(self):
        """运行所有测试"""
        print("🔍 Perfect21 实际功能验证测试")
        print("=" * 50)

        # 按顺序执行测试
        tests = [
            self.test_project_structure,
            self.test_configuration,
            self.test_capability_discovery,
            self.test_version_manager,
            self.test_claude_md_manager,
            self.test_git_workflow,
            self.test_integration_status,
            self.test_system_status,
        ]

        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_func.__name__, False, f"测试执行异常: {e}")
            print("-" * 30)

        # 生成总结报告
        return self.generate_summary()

    def generate_summary(self):
        """生成测试总结"""
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        failed = total - passed

        print("\n" + "=" * 50)
        print("📊 测试总结报告")
        print("=" * 50)

        summary = {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': failed,
            'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            'results': self.results
        }

        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {failed}")
        print(f"成功率: {summary['success_rate']}")

        if failed > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['message']}")

        if passed == total:
            print(f"\n🎉 所有测试通过！Perfect21项目状态优秀")
        elif passed >= total * 0.8:
            print(f"\n✅ 大部分测试通过，项目状态良好")
        else:
            print(f"\n⚠️  多个测试失败，建议检查和修复")

        return summary

def main():
    """主函数"""
    try:
        test_suite = SimplifiedTestSuite()
        summary = test_suite.run_all_tests()

        # 保存简化报告
        import json
        report_file = Path('test_functionality_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n📄 测试报告已保存到: {report_file}")

        # 根据结果设置退出码
        failed_count = summary['failed_tests']
        sys.exit(0 if failed_count == 0 else 1)

    except Exception as e:
        print(f"❌ 测试套件异常: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()