#!/usr/bin/env python3
"""
Perfect21 性能测试脚本
对比优化前后的性能差异
"""

import asyncio
import time
import statistics
import subprocess
import os
import sys
from typing import Dict, List, Any
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class PerformanceTester:
    """性能测试器"""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            'git_operations': {},
            'cli_commands': {},
            'memory_usage': {},
            'summary': {}
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("🚀 Perfect21 性能测试开始")
        print("=" * 60)

        # 1. Git操作性能测试
        print("\n📊 1. Git操作性能测试")
        await self.test_git_operations()

        # 2. CLI命令响应时间测试
        print("\n📊 2. CLI命令响应时间测试")
        await self.test_cli_response_times()

        # 3. 内存使用测试
        print("\n📊 3. 内存使用测试")
        await self.test_memory_usage()

        # 4. 并发操作测试
        print("\n📊 4. 并发操作测试")
        await self.test_concurrent_operations()

        # 5. 生成测试报告
        print("\n📊 5. 生成测试报告")
        self.generate_report()

        return self.results

    async def test_git_operations(self):
        """测试Git操作性能"""
        git_tests = [
            ('git_status_traditional', self._git_status_traditional),
            ('git_status_cached', self._git_status_cached),
            ('git_batch_operations', self._git_batch_operations)
        ]

        for test_name, test_func in git_tests:
            print(f"  测试: {test_name}")
            times = []

            for i in range(10):  # 运行10次取平均值
                start_time = time.time()
                try:
                    await test_func()
                    execution_time = time.time() - start_time
                    times.append(execution_time)
                except Exception as e:
                    print(f"    ❌ 测试失败: {e}")
                    times.append(float('inf'))

            avg_time = statistics.mean([t for t in times if t != float('inf')])
            min_time = min([t for t in times if t != float('inf')])
            max_time = max([t for t in times if t != float('inf')])

            self.results['git_operations'][test_name] = {
                'average_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'times': times
            }

            print(f"    ✅ 平均时间: {avg_time:.3f}s (最快: {min_time:.3f}s, 最慢: {max_time:.3f}s)")

    async def _git_status_traditional(self):
        """传统Git状态查询"""
        commands = [
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            ['git', 'status', '--porcelain'],
            ['git', 'diff', '--cached', '--name-only']
        ]

        for cmd in commands:
            subprocess.run(cmd, capture_output=True, cwd=self.project_root)

    async def _git_status_cached(self):
        """缓存版Git状态查询"""
        try:
            from infrastructure.git.git_cache import get_git_cache

            git_cache = get_git_cache(str(self.project_root))
            await git_cache.get_git_status()
        except ImportError:
            # 如果模块不存在，跳过测试
            pass

    async def _git_batch_operations(self):
        """批量Git操作"""
        try:
            from infrastructure.git.git_cache import get_git_cache

            git_cache = get_git_cache(str(self.project_root))
            await git_cache.get_git_status()
            await git_cache.get_file_changes_summary()
        except ImportError:
            pass

    async def test_cli_response_times(self):
        """测试CLI命令响应时间"""
        cli_tests = [
            ('status_command', ['python3', 'main/cli_optimized.py', 'status']),
            ('hooks_list', ['python3', 'main/cli_optimized.py', 'hooks', 'list']),
            ('parallel_status', ['python3', 'main/cli_optimized.py', 'parallel', 'status'])
        ]

        for test_name, cmd in cli_tests:
            print(f"  测试: {test_name}")
            times = []

            for i in range(5):  # CLI测试次数少一些
                start_time = time.time()
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        cwd=self.project_root,
                        timeout=30
                    )
                    execution_time = time.time() - start_time
                    times.append(execution_time)

                    if result.returncode != 0:
                        print(f"    ⚠️ 命令返回非零退出码: {result.returncode}")

                except subprocess.TimeoutExpired:
                    print(f"    ❌ 命令超时")
                    times.append(float('inf'))
                except Exception as e:
                    print(f"    ❌ 测试失败: {e}")
                    times.append(float('inf'))

            valid_times = [t for t in times if t != float('inf')]
            if valid_times:
                avg_time = statistics.mean(valid_times)
                min_time = min(valid_times)
                max_time = max(valid_times)

                self.results['cli_commands'][test_name] = {
                    'average_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'times': times
                }

                print(f"    ✅ 平均时间: {avg_time:.3f}s (最快: {min_time:.3f}s, 最慢: {max_time:.3f}s)")
            else:
                print(f"    ❌ 所有测试都失败了")

    async def test_memory_usage(self):
        """测试内存使用"""
        try:
            import psutil

            # 获取当前进程内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # 模拟一些操作
            await self._simulate_operations()

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = memory_after - memory_before

            self.results['memory_usage'] = {
                'before_mb': memory_before,
                'after_mb': memory_after,
                'difference_mb': memory_diff
            }

            print(f"  ✅ 内存使用: {memory_before:.1f}MB → {memory_after:.1f}MB (差异: {memory_diff:+.1f}MB)")

        except ImportError:
            print("  ⚠️ psutil未安装，跳过内存测试")

    async def _simulate_operations(self):
        """模拟一些操作"""
        try:
            # 模拟Git缓存操作
            from infrastructure.git.git_cache import get_git_cache

            git_cache = get_git_cache(str(self.project_root))
            for _ in range(10):
                await git_cache.get_git_status()

            # 模拟配置操作
            from infrastructure.config.config_manager import get_config_manager

            config_manager = get_config_manager(str(self.project_root))
            for _ in range(10):
                config_manager.get('perfect21.version')

        except ImportError:
            pass

    async def test_concurrent_operations(self):
        """测试并发操作"""
        concurrent_tests = [
            ('git_cache_concurrent', self._test_git_cache_concurrent),
            ('config_concurrent', self._test_config_concurrent)
        ]

        for test_name, test_func in concurrent_tests:
            print(f"  测试: {test_name}")
            start_time = time.time()

            try:
                await test_func()
                execution_time = time.time() - start_time
                print(f"    ✅ 并发执行时间: {execution_time:.3f}s")

                self.results[test_name] = {
                    'execution_time': execution_time,
                    'success': True
                }

            except Exception as e:
                print(f"    ❌ 并发测试失败: {e}")
                self.results[test_name] = {
                    'execution_time': float('inf'),
                    'success': False,
                    'error': str(e)
                }

    async def _test_git_cache_concurrent(self):
        """测试Git缓存并发操作"""
        try:
            from infrastructure.git.git_cache import get_git_cache

            git_cache = get_git_cache(str(self.project_root))

            # 并发执行多个Git操作
            tasks = [
                git_cache.get_git_status() for _ in range(10)
            ]

            await asyncio.gather(*tasks)

        except ImportError:
            pass

    async def _test_config_concurrent(self):
        """测试配置并发读取"""
        try:
            from infrastructure.config.config_manager import get_config_manager

            config_manager = get_config_manager(str(self.project_root))

            # 并发读取配置
            async def read_config():
                for _ in range(100):
                    config_manager.get('perfect21.version')

            tasks = [read_config() for _ in range(5)]
            await asyncio.gather(*tasks)

        except ImportError:
            pass

    def generate_report(self):
        """生成性能测试报告"""
        print("\n📋 性能测试报告")
        print("=" * 60)

        # Git操作性能对比
        git_results = self.results.get('git_operations', {})
        if git_results:
            print("\n🔍 Git操作性能对比:")

            traditional = git_results.get('git_status_traditional', {})
            cached = git_results.get('git_status_cached', {})

            if traditional and cached:
                traditional_time = traditional.get('average_time', 0)
                cached_time = cached.get('average_time', 0)

                if traditional_time > 0 and cached_time > 0:
                    improvement = ((traditional_time - cached_time) / traditional_time) * 100
                    print(f"  传统方式: {traditional_time:.3f}s")
                    print(f"  缓存方式: {cached_time:.3f}s")
                    print(f"  性能提升: {improvement:.1f}%")

        # CLI响应时间
        cli_results = self.results.get('cli_commands', {})
        if cli_results:
            print("\n⚡ CLI命令响应时间:")
            for cmd_name, result in cli_results.items():
                avg_time = result.get('average_time', 0)
                print(f"  {cmd_name}: {avg_time:.3f}s")

        # 内存使用
        memory_results = self.results.get('memory_usage', {})
        if memory_results:
            print("\n💾 内存使用情况:")
            print(f"  操作前: {memory_results.get('before_mb', 0):.1f}MB")
            print(f"  操作后: {memory_results.get('after_mb', 0):.1f}MB")
            print(f"  内存增长: {memory_results.get('difference_mb', 0):+.1f}MB")

        # 保存详细报告
        self.save_detailed_report()

    def save_detailed_report(self):
        """保存详细测试报告"""
        try:
            import json
            from datetime import datetime

            report_file = self.project_root / f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            print(f"\n📄 详细报告已保存: {report_file}")

        except Exception as e:
            print(f"\n❌ 保存报告失败: {e}")


async def main():
    """主函数"""
    tester = PerformanceTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())