#!/usr/bin/env python3
"""
Perfect21 性能测试执行器
自动启动模拟服务器并执行完整的性能测试套件
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
import logging
from pathlib import Path
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestRunner:
    """性能测试运行器"""

    def __init__(self):
        self.server_process = None
        self.server_ready = False

    async def check_dependencies(self):
        """检查依赖"""
        logger.info("🔍 检查测试依赖...")

        required_packages = [
            'aiohttp',
            'aiohttp-cors',
            'psutil',
            'matplotlib',
            'pandas'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.error(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
            logger.info("请运行: pip install " + " ".join(missing_packages))
            return False

        logger.info("✅ 依赖检查通过")
        return True

    async def start_mock_server(self):
        """启动模拟服务器"""
        logger.info("🚀 启动模拟性能测试服务器...")

        try:
            # 启动模拟服务器
            self.server_process = subprocess.Popen(
                [sys.executable, "mock_performance_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            # 等待服务器启动
            max_wait = 30  # 最大等待30秒
            wait_time = 0

            while wait_time < max_wait:
                try:
                    # 检查服务器是否响应
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://localhost:8080/health', timeout=aiohttp.ClientTimeout(total=2)) as response:
                            if response.status == 200:
                                self.server_ready = True
                                logger.info("✅ 模拟服务器启动成功")
                                return True
                except Exception:
                    pass

                await asyncio.sleep(1)
                wait_time += 1

            logger.error("❌ 模拟服务器启动超时")
            return False

        except Exception as e:
            logger.error(f"❌ 启动模拟服务器失败: {e}")
            return False

    async def stop_mock_server(self):
        """停止模拟服务器"""
        if self.server_process:
            logger.info("🛑 停止模拟服务器...")
            try:
                # 发送终止信号
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                else:
                    self.server_process.terminate()

                # 等待进程结束
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制终止
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                    else:
                        self.server_process.kill()

                logger.info("✅ 模拟服务器已停止")
            except Exception as e:
                logger.error(f"❌ 停止模拟服务器失败: {e}")

    async def run_performance_tests(self):
        """运行性能测试"""
        logger.info("⚡ 开始执行综合性能测试...")

        try:
            # 导入测试模块
            from comprehensive_performance_test import ComprehensivePerformanceTester

            # 创建测试器
            tester = ComprehensivePerformanceTester("http://localhost:8080")

            # 初始化测试器
            await tester.initialize()

            # 运行测试
            report = await tester.run_comprehensive_tests()

            # 保存报告
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            report_filename = f"performance_report_{timestamp}.json"
            await tester.save_report_to_file(report, report_filename)

            # 生成测试摘要
            await self.generate_test_summary(report, report_filename)

            return report

        except Exception as e:
            logger.error(f"❌ 性能测试执行失败: {e}")
            raise

    async def generate_test_summary(self, report, report_filename):
        """生成测试摘要"""
        logger.info("📋 生成测试摘要...")

        # 创建摘要数据
        summary = {
            "测试概述": {
                "整体评分": f"{report.overall_score:.1f}/100",
                "测试时间": report.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "测试项目数": len(report.test_results),
                "系统信息": report.system_info
            },
            "关键指标": {},
            "性能瓶颈": report.bottlenecks,
            "优化建议": report.recommendations
        }

        # 提取关键指标
        for result in report.test_results:
            summary["关键指标"][result.test_name] = {
                "吞吐量(RPS)": f"{result.requests_per_second:.1f}",
                "平均响应时间(ms)": f"{result.avg_response_time_ms:.1f}",
                "P95响应时间(ms)": f"{result.p95_response_time_ms:.1f}",
                "错误率(%)": f"{result.error_rate_percent:.2f}",
                "CPU使用率(%)": f"{result.cpu_usage_percent:.1f}",
                "内存使用(MB)": f"{result.memory_usage_mb:.1f}"
            }

            if result.cache_hit_rate_percent > 0:
                summary["关键指标"][result.test_name]["缓存命中率(%)"] = f"{result.cache_hit_rate_percent:.1f}"

        # 保存摘要
        summary_filename = f"performance_summary_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # 打印控制台摘要
        self.print_console_summary(report)

        logger.info(f"📄 详细报告: {report_filename}")
        logger.info(f"📊 测试摘要: {summary_filename}")

    def print_console_summary(self, report):
        """打印控制台摘要"""
    # print("\n" + "="*80)
    # print("🎯 PERFECT21 性能测试报告")
    # print("="*80)

        # 整体评分
        score_color = "🟢" if report.overall_score >= 80 else "🟡" if report.overall_score >= 60 else "🔴"
    # print(f"{score_color} 整体性能评分: {report.overall_score:.1f}/100")

        # 测试结果概览
    # print(f"\n📊 测试结果概览:")
    # print(f"  测试时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    # print(f"  测试项目: {len(report.test_results)}个")
    # print(f"  系统信息: {report.system_info['cpu_count']}核CPU, {report.system_info['total_memory_gb']:.1f}GB内存")

        # 详细测试结果
    # print(f"\n📈 详细测试结果:")
    # print("-" * 80)
    # print(f"{'测试项目':<25} {'RPS':<8} {'响应时间':<12} {'P95':<10} {'错误率':<8} {'CPU':<6} {'内存':<8}")
    # print("-" * 80)

        for result in report.test_results:
            test_name = result.test_name[:24]
            rps = f"{result.requests_per_second:.1f}"
            avg_time = f"{result.avg_response_time_ms:.1f}ms"
            p95_time = f"{result.p95_response_time_ms:.1f}ms"
            error_rate = f"{result.error_rate_percent:.2f}%"
            cpu = f"{result.cpu_usage_percent:.1f}%"
            memory = f"{result.memory_usage_mb:.0f}MB"

    # print(f"{test_name:<25} {rps:<8} {avg_time:<12} {p95_time:<10} {error_rate:<8} {cpu:<6} {memory:<8}")

        # 性能瓶颈
        if report.bottlenecks:
    # print(f"\n⚠️ 发现的性能瓶颈 ({len(report.bottlenecks)}个):")
            for i, bottleneck in enumerate(report.bottlenecks, 1):
    # print(f"  {i}. {bottleneck}")

        # 优化建议
        if report.recommendations:
    # print(f"\n💡 优化建议 ({len(report.recommendations)}个):")
            for i, recommendation in enumerate(report.recommendations, 1):
    # print(f"  {i}. {recommendation}")

        # 图表信息
        charts_dir = Path("performance_charts")
        if charts_dir.exists():
            charts = list(charts_dir.glob("*.png"))
            if charts:
    # print(f"\n📈 生成的图表文件 ({len(charts)}个):")
                for chart in charts:
    # print(f"  📊 {chart.name}")

    # print("\n" + "="*80)

async def main():
    """主函数"""
    # print("🚀 Perfect21 性能测试执行器")
    # print("=" * 50)

    runner = PerformanceTestRunner()

    try:
        # 1. 检查依赖
        if not await runner.check_dependencies():
            return 1

        # 2. 启动模拟服务器
        if not await runner.start_mock_server():
            return 1

        # 3. 等待用户确认或自动开始
    # print("\n🔄 模拟服务器已就绪，准备开始性能测试...")
    # print("测试将包括:")
    # print("  ⚡ 负载测试 (1000并发用户)")
    # print("  ⏱️ 响应时间测试")
    # print("  💾 内存使用测试")
    # print("  🗄️ 数据库查询优化测试")
    # print("  🗂️ 缓存命中率测试")
    # print("  💥 压力测试 (极限负载)")

    # print("\n按 Enter 键开始测试 (或等待10秒自动开始)...")

        # 等待用户输入或超时
        try:
            await asyncio.wait_for(asyncio.to_thread(input), timeout=10.0)
        except asyncio.TimeoutError:
    # print("⏰ 超时，自动开始测试...")

        # 4. 运行性能测试
        report = await runner.run_performance_tests()

    # print("\n✅ 性能测试完成！")
        return 0

    except KeyboardInterrupt:
    # print("\n❌ 用户中断测试")
        return 1

    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        return 1

    finally:
        # 清理
        await runner.stop_mock_server()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)