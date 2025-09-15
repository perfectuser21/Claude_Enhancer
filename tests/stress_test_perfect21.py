#!/usr/bin/env python3
"""
Perfect21 系统压力测试脚本
全面测试Perfect21的所有核心功能和性能
"""

import os
import sys
import time
import json
import subprocess
import concurrent.futures
from typing import Dict, Any, List, Tuple
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Perfect21组件
from features.git_workflow.hooks_manager import GitHooksManager
from features.version_manager import get_global_version_manager, get_global_version_advisor
from features.git_workflow.plugins.plugin_manager import PluginManager

class Perfect21StressTest:
    """Perfect21系统压力测试器"""

    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_results = {
            "start_time": time.time(),
            "tests": {},
            "summary": {},
            "errors": []
        }

        print("🚀 Perfect21 系统压力测试启动")
        print("=" * 60)

    def run_command_test(self, description: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """运行命令测试"""
        print(f"🧪 {description}")
        start_time = time.time()

        try:
            result = subprocess.run(
                command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time
            success = result.returncode == 0

            test_result = {
                "success": success,
                "execution_time": execution_time,
                "returncode": result.returncode,
                "stdout": result.stdout[:500],  # 限制输出长度
                "stderr": result.stderr[:500] if result.stderr else "",
                "timeout": timeout
            }

            status = "✅" if success else "❌"
            print(f"   {status} 耗时: {execution_time:.2f}s | 状态: {result.returncode}")

            return test_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"   ⏰ 超时: {timeout}s")
            return {
                "success": False,
                "execution_time": execution_time,
                "timeout": True,
                "error": f"Command timeout after {timeout}s"
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   💥 异常: {str(e)}")
            return {
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }

    def test_perfect21_commands(self):
        """测试Perfect21主命令"""
        print("\n📋 测试Perfect21主命令")
        print("-" * 40)

        commands = [
            ("Perfect21帮助信息", "./perfect21 --help"),
            ("Perfect21系统状态", "./perfect21 --status"),
            ("Git Hooks状态", "python3 main/cli.py hooks status"),
            ("工作流状态", "python3 main/cli.py workflow list"),
            ("分支状态", "python3 main/cli.py branch status"),
        ]

        results = {}
        for description, command in commands:
            results[description] = self.run_command_test(description, command)

        self.test_results["tests"]["perfect21_commands"] = results

    def test_hooks_system(self):
        """测试Git Hooks系统"""
        print("\n🔧 测试Git Hooks系统")
        print("-" * 40)

        try:
            # 测试GitHooksManager初始化
            print("🧪 GitHooksManager初始化测试")
            start_time = time.time()

            hm = GitHooksManager()
            init_time = time.time() - start_time

            print(f"   ✅ 初始化成功: {init_time:.2f}s")

            # 测试配置加载
            print("🧪 配置系统测试")
            config_summary = hm.get_config_summary()
            print(f"   ✅ 配置加载成功: {len(config_summary)} 字符")

            # 测试插件系统
            print("🧪 插件系统测试")
            plugin_status = hm.get_plugin_status()
            plugin_count = plugin_status['total_plugins']
            enabled_count = len(plugin_status['enabled_plugins'])

            print(f"   ✅ 插件系统: {enabled_count}/{plugin_count} 插件启用")

            # 测试Hook状态
            print("🧪 Hook状态测试")
            hook_status = hm.get_hook_status()
            total_hooks = hook_status['summary']['total_hooks']
            installed_hooks = hook_status['summary']['installed_hooks']

            print(f"   ✅ Hook状态: {installed_hooks}/{total_hooks} 钩子安装")

            self.test_results["tests"]["hooks_system"] = {
                "success": True,
                "init_time": init_time,
                "total_plugins": plugin_count,
                "enabled_plugins": enabled_count,
                "total_hooks": total_hooks,
                "installed_hooks": installed_hooks,
                "config_size": len(config_summary)
            }

        except Exception as e:
            print(f"   💥 Hooks系统测试失败: {e}")
            self.test_results["tests"]["hooks_system"] = {
                "success": False,
                "error": str(e)
            }
            self.test_results["errors"].append(f"Hooks system: {e}")

    def test_version_manager(self):
        """测试版本管理系统"""
        print("\n📊 测试版本管理系统")
        print("-" * 40)

        try:
            # 测试版本管理器
            print("🧪 版本管理器初始化测试")
            start_time = time.time()

            vm = get_global_version_manager()
            va = get_global_version_advisor()

            init_time = time.time() - start_time
            print(f"   ✅ 版本管理器初始化: {init_time:.2f}s")

            # 测试版本获取
            print("🧪 版本信息测试")
            current_version = vm.get_current_version()
            version_info = vm.get_version_info()

            print(f"   ✅ 当前版本: {current_version}")
            print(f"   ✅ 版本信息: {len(json.dumps(version_info))} 字符")

            # 测试版本建议
            print("🧪 版本决策测试")
            suggestion = va.suggest_version_bump(current_version)

            print(f"   ✅ 版本建议: {suggestion.get('suggested_version', 'N/A')}")

            self.test_results["tests"]["version_manager"] = {
                "success": True,
                "init_time": init_time,
                "current_version": current_version,
                "version_info_size": len(json.dumps(version_info)),
                "suggestion": suggestion
            }

        except Exception as e:
            print(f"   💥 版本管理测试失败: {e}")
            self.test_results["tests"]["version_manager"] = {
                "success": False,
                "error": str(e)
            }
            self.test_results["errors"].append(f"Version manager: {e}")

    def test_plugin_performance(self):
        """测试插件系统性能"""
        print("\n⚡ 测试插件系统性能")
        print("-" * 40)

        try:
            # 创建插件管理器
            plugins_dir = os.path.join(self.project_root, 'features/git_workflow/plugins')
            pm = PluginManager(plugins_dir=plugins_dir)

            # 测试插件加载性能
            print("🧪 插件加载性能测试")
            load_times = []

            for i in range(5):  # 重复5次测试
                start_time = time.time()
                results = pm.load_all_plugins()
                load_time = time.time() - start_time
                load_times.append(load_time)

                # 清理插件以便下次测试
                pm.cleanup()

            avg_load_time = sum(load_times) / len(load_times)
            min_load_time = min(load_times)
            max_load_time = max(load_times)

            print(f"   ✅ 平均加载时间: {avg_load_time:.3f}s")
            print(f"   ✅ 最快加载时间: {min_load_time:.3f}s")
            print(f"   ✅ 最慢加载时间: {max_load_time:.3f}s")

            # 重新加载插件用于执行测试
            pm.load_all_plugins()

            # 测试插件执行性能
            print("🧪 插件执行性能测试")
            context = {
                'hook_name': 'performance_test',
                'project_root': self.project_root,
                'staged_files': ['test_file.py'],
                'dry_run': True
            }

            execution_times = {}
            for plugin_name in pm.get_enabled_plugins():
                start_time = time.time()
                result = pm.execute_plugin(plugin_name, context)
                exec_time = time.time() - start_time
                execution_times[plugin_name] = {
                    'time': exec_time,
                    'status': result.status.value,
                    'success': result.status.value in ['success', 'skipped']
                }

                print(f"   ✅ {plugin_name}: {exec_time:.3f}s ({result.status.value})")

            pm.cleanup()

            self.test_results["tests"]["plugin_performance"] = {
                "success": True,
                "load_times": {
                    "average": avg_load_time,
                    "min": min_load_time,
                    "max": max_load_time,
                    "all_times": load_times
                },
                "execution_times": execution_times
            }

        except Exception as e:
            print(f"   💥 插件性能测试失败: {e}")
            self.test_results["tests"]["plugin_performance"] = {
                "success": False,
                "error": str(e)
            }
            self.test_results["errors"].append(f"Plugin performance: {e}")

    def test_concurrent_operations(self):
        """测试并发操作"""
        print("\n🚀 测试并发操作")
        print("-" * 40)

        try:
            # 并发执行多个Perfect21操作
            commands = [
                "./perfect21 --status",
                "python3 main/cli.py hooks status",
                "python3 main/cli.py workflow list",
                "python3 main/cli.py branch status"
            ]

            print(f"🧪 并发执行 {len(commands)} 个操作")
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(
                        self.run_command_test,
                        f"并发任务{i+1}",
                        cmd,
                        30
                    )
                    for i, cmd in enumerate(commands)
                ]

                results = []
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())

            total_time = time.time() - start_time
            success_count = sum(1 for r in results if r['success'])

            print(f"   ✅ 并发执行完成: {total_time:.2f}s")
            print(f"   ✅ 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

            self.test_results["tests"]["concurrent_operations"] = {
                "success": success_count == len(results),
                "total_time": total_time,
                "success_count": success_count,
                "total_count": len(results),
                "success_rate": success_count / len(results) * 100,
                "individual_results": results
            }

        except Exception as e:
            print(f"   💥 并发操作测试失败: {e}")
            self.test_results["tests"]["concurrent_operations"] = {
                "success": False,
                "error": str(e)
            }
            self.test_results["errors"].append(f"Concurrent operations: {e}")

    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n💾 测试内存使用情况")
        print("-" * 40)

        try:
            import psutil
            import gc

            # 获取初始内存
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            print("🧪 创建多个Perfect21组件测试内存")

            # 创建多个组件实例
            components = []
            memory_snapshots = [initial_memory]

            for i in range(10):
                hm = GitHooksManager()
                components.append(hm)

                current_memory = process.memory_info().rss / 1024 / 1024
                memory_snapshots.append(current_memory)

                if i % 2 == 0:  # 每两次显示一次
                    print(f"   📊 创建 {i+1} 个组件: {current_memory:.1f}MB (+{current_memory-initial_memory:.1f}MB)")

            peak_memory = max(memory_snapshots)

            # 清理组件
            components.clear()
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024
            memory_freed = peak_memory - final_memory

            print(f"   ✅ 初始内存: {initial_memory:.1f}MB")
            print(f"   ✅ 峰值内存: {peak_memory:.1f}MB")
            print(f"   ✅ 最终内存: {final_memory:.1f}MB")
            print(f"   ✅ 释放内存: {memory_freed:.1f}MB")

            self.test_results["tests"]["memory_usage"] = {
                "success": True,
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_freed_mb": memory_freed,
                "memory_snapshots": memory_snapshots
            }

        except ImportError:
            print("   ⚠️  psutil未安装，跳过内存测试")
            self.test_results["tests"]["memory_usage"] = {
                "success": False,
                "error": "psutil not available"
            }
        except Exception as e:
            print(f"   💥 内存测试失败: {e}")
            self.test_results["tests"]["memory_usage"] = {
                "success": False,
                "error": str(e)
            }
            self.test_results["errors"].append(f"Memory usage: {e}")

    def generate_report(self):
        """生成测试报告"""
        print("\n📊 生成压力测试报告")
        print("=" * 60)

        end_time = time.time()
        total_time = end_time - self.test_results["start_time"]

        # 统计结果
        total_tests = len(self.test_results["tests"])
        successful_tests = sum(
            1 for test_data in self.test_results["tests"].values()
            if test_data.get("success", False)
        )

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # 更新摘要
        self.test_results["summary"] = {
            "total_time": total_time,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate,
            "end_time": end_time
        }

        # 打印报告
        print(f"🕒 总测试时间: {total_time:.2f}秒")
        print(f"📋 测试项目: {total_tests}")
        print(f"✅ 成功: {successful_tests}")
        print(f"❌ 失败: {total_tests - successful_tests}")
        print(f"📊 成功率: {success_rate:.1f}%")

        if self.test_results["errors"]:
            print(f"\n🚨 错误详情:")
            for error in self.test_results["errors"]:
                print(f"   • {error}")

        # 保存详细报告
        report_file = os.path.join(self.project_root, "tests/stress_test_report.json")
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存: {report_file}")

        # 性能评级
        if success_rate >= 95:
            grade = "🏆 优秀"
        elif success_rate >= 85:
            grade = "🥉 良好"
        elif success_rate >= 70:
            grade = "⚠️  需要改进"
        else:
            grade = "🚨 严重问题"

        print(f"\n🎯 Perfect21系统评级: {grade} ({success_rate:.1f}%)")

    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.test_perfect21_commands()
            self.test_hooks_system()
            self.test_version_manager()
            self.test_plugin_performance()
            self.test_concurrent_operations()
            self.test_memory_usage()
        finally:
            self.generate_report()


if __name__ == "__main__":
    print("🔥 Perfect21系统自我压力测试")
    print("Testing all components: Commands, Hooks, Plugins, Version Manager, Performance")
    print()

    tester = Perfect21StressTest()
    tester.run_all_tests()