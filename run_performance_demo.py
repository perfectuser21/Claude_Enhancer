#!/usr/bin/env python3
"""
Perfect21 Performance Optimization Demo
性能优化系统演示脚本
"""

import asyncio
import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """主演示函数"""
    print("🚀 Perfect21 Performance Optimization System Demo")
    print("=" * 60)

    try:
        # 导入性能优化模块
        from backend.core import quick_start, create_performance_tester

        # 1. 启动性能系统
        print("\n📋 Phase 1: 启动性能优化系统")
        performance_manager = await quick_start(
            service_name="perfect21-demo",
            config_file="performance.yaml"
        )

        # 2. 展示系统状态
        print("\n📊 Phase 2: 系统状态检查")
        health_status = await performance_manager.get_health_status()

        print("健康状态检查:")
        for component, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'健康' if status else '异常'}")

        # 3. 性能基准测试
        print("\n⚡ Phase 3: 性能基准测试")
        tester = create_performance_tester(performance_manager)

        # 缓存性能测试
        if performance_manager.cache_manager:
            print("正在进行缓存性能测试...")
            cache_results = await tester.benchmark_cache(500)
            print(f"缓存写入性能: {cache_results['write_ops_per_sec']:.0f} ops/sec")
            print(f"缓存读取性能: {cache_results['read_ops_per_sec']:.0f} ops/sec")

        # 数据库性能测试（如果配置了数据库）
        if performance_manager.database_optimizer:
            print("正在进行数据库性能测试...")
            try:
                db_results = await tester.benchmark_database(50)
                print(f"数据库查询性能: {db_results['queries_per_sec']:.0f} queries/sec")
            except Exception as e:
                print(f"数据库测试跳过: {e}")

        # 4. 模拟负载测试
        print("\n🔄 Phase 4: 模拟负载测试")
        await simulate_workload(performance_manager)

        # 5. 生成性能报告
        print("\n📈 Phase 5: 生成性能报告")
        report = await performance_manager.generate_performance_report()

        print(f"性能评分: {report.overall_score:.1f}/100")
        print(f"平均响应时间: {report.response_time_p95:.2f}ms")
        print(f"缓存命中率: {report.cache_hit_rate:.1f}%")
        print(f"系统健康状态: {report.system_health}")

        if report.bottlenecks:
            print("发现的瓶颈:")
            for bottleneck in report.bottlenecks:
                print(f"  - {bottleneck}")

        if report.recommendations:
            print("优化建议:")
            for recommendation in report.recommendations:
                print(f"  - {recommendation}")

        # 6. 仪表板信息
        print("\n🌐 Phase 6: 监控仪表板")
        if performance_manager.dashboard:
            print("性能监控仪表板已启动")
            print("访问地址: http://localhost:8000/")
            print("实时指标: http://localhost:8000/api/metrics")
            print("系统状态: http://localhost:8000/api/status")
            print("告警信息: http://localhost:8000/api/alerts")

        # 7. 等待用户交互
        print("\n⏱️  系统将运行60秒以收集指标数据...")
        print("按 Ctrl+C 提前停止")

        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\n用户中断，正在停止...")

        # 8. 最终报告
        print("\n📋 Final Report: 最终性能报告")
        final_report = await performance_manager.generate_performance_report()
        print(f"最终性能评分: {final_report.overall_score:.1f}/100")

        # 获取指标摘要
        if performance_manager.metrics_collector:
            metrics_summary = await performance_manager.metrics_collector.get_metrics_summary()
            print(f"指标收集统计: {metrics_summary}")

    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        return 1

    finally:
        # 清理资源
        print("\n🛑 正在关闭系统...")
        try:
            from backend.core import shutdown_performance_manager
            await shutdown_performance_manager()
            print("✅ 系统已安全关闭")
        except Exception as e:
            logger.error(f"关闭过程中发生错误: {e}")

    return 0

async def simulate_workload(performance_manager):
    """模拟工作负载"""
    print("模拟各种工作负载...")

    # 模拟HTTP请求
    tasks = []
    for i in range(100):
        task = asyncio.create_task(simulate_request(performance_manager, i))
        tasks.append(task)

    # 等待所有任务完成
    await asyncio.gather(*tasks, return_exceptions=True)

    print(f"完成 {len(tasks)} 个模拟请求")

async def simulate_request(performance_manager, request_id):
    """模拟单个请求"""
    async with performance_manager.performance_context("demo_request"):
        # 模拟缓存操作
        if performance_manager.cache_manager:
            await performance_manager.cache_manager.set(
                "demo",
                f"request_{request_id}",
                f"data_for_request_{request_id}"
            )

            await performance_manager.cache_manager.get("demo", f"request_{request_id}")

        # 模拟异步任务
        if performance_manager.async_processor:
            await performance_manager.async_processor.submit_custom_task(
                simulate_background_task,
                request_id,
                name=f"demo_task_{request_id}"
            )

        # 模拟处理时间
        await asyncio.sleep(0.01 + (request_id % 10) * 0.001)  # 10-20ms

async def simulate_background_task(request_id):
    """模拟后台任务"""
    await asyncio.sleep(0.05)  # 50ms processing time
    return f"Background task {request_id} completed"

def check_requirements():
    """检查运行要求"""
    required_files = [
        "backend/core/__init__.py",
        "performance.yaml"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False

    return True

if __name__ == "__main__":
    print("🔍 检查运行环境...")

    if not check_requirements():
        print("❌ 环境检查失败，请确保所有文件存在")
        exit(1)

    print("✅ 环境检查通过")

    # 运行演示
    exit_code = asyncio.run(main())