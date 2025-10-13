#!/usr/bin/env python3
"""
🚀 Claude Enhancer Comprehensive Performance Test Suite
==========================================

执行完整的性能测试套件，包括：
1. 负载测试（1000并发用户）
2. 响应时间测试
3. 内存使用测试
4. 数据库查询优化
5. 缓存命中率测试

生成详细的性能测试报告
"""

import asyncio
import time
import json
import logging
import statistics
import psutil
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceTestResult:
    """性能测试结果"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    error_rate_percent: float
    cpu_usage_percent: float
    memory_usage_mb: float
    peak_memory_mb: float
    cache_hit_rate_percent: float = 0.0
    database_query_time_ms: float = 0.0
    additional_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_metrics is None:
            self.additional_metrics = {}

@dataclass
class PerformanceReport:
    """完整性能报告"""
    timestamp: datetime
    overall_score: float
    test_results: List[PerformanceTestResult]
    system_info: Dict[str, Any]
    bottlenecks: List[str]
    recommendations: List[str]
    charts_generated: List[str]

class ComprehensivePerformanceTester:
    """综合性能测试器"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_results = []
        self.session = None

        # 监控数据
        self.cpu_samples = []
        self.memory_samples = []
        self.response_times = []

        # 测试配置
        self.test_configs = {
            'load_test': {
                'concurrent_users': 1000,
                'duration_seconds': 300,  # 5分钟
                'ramp_up_seconds': 60     # 1分钟加压
            },
            'stress_test': {
                'concurrent_users': 2000,
                'duration_seconds': 180,  # 3分钟
                'ramp_up_seconds': 30     # 30秒加压
            },
            'spike_test': {
                'concurrent_users': 5000,
                'duration_seconds': 60,   # 1分钟
                'ramp_up_seconds': 10     # 10秒加压
            }
        }

    async def initialize(self):
        """初始化测试环境"""
        logger.info("🔧 初始化性能测试环境...")

        # 创建HTTP会话
        connector = aiohttp.TCPConnector(
            limit=2000,  # 总连接池大小
            limit_per_host=500,  # 每个主机的连接数
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        # 检查目标服务可用性
        await self._check_service_availability()

        logger.info("✅ 测试环境初始化完成")

    async def _check_service_availability(self):
        """检查服务可用性"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ 目标服务可用")
                else:
                    logger.warning(f"⚠️ 服务返回状态码: {response.status}")
        except Exception as e:
            logger.error(f"❌ 无法连接到目标服务: {e}")
            raise

    async def run_comprehensive_tests(self) -> PerformanceReport:
        """运行综合性能测试"""
        logger.info("🚀 开始综合性能测试")
        start_time = datetime.now()

        try:
            pass  # Auto-fixed empty block
            # 1. 基准性能测试
            logger.info("📊 Phase 1: 基准性能测试")
            baseline_result = await self._baseline_performance_test()
            self.test_results.append(baseline_result)

            # 2. 负载测试 (1000并发用户)
            logger.info("⚡ Phase 2: 负载测试 (1000并发用户)")
            load_result = await self._load_test()
            self.test_results.append(load_result)

            # 3. 响应时间测试
            logger.info("⏱️ Phase 3: 响应时间测试")
            response_time_result = await self._response_time_test()
            self.test_results.append(response_time_result)

            # 4. 内存压力测试
            logger.info("💾 Phase 4: 内存压力测试")
            memory_result = await self._memory_stress_test()
            self.test_results.append(memory_result)

            # 5. 数据库查询性能测试
            logger.info("🗄️ Phase 5: 数据库查询性能测试")
            db_result = await self._database_performance_test()
            self.test_results.append(db_result)

            # 6. 缓存命中率测试
            logger.info("🗂️ Phase 6: 缓存命中率测试")
            cache_result = await self._cache_performance_test()
            self.test_results.append(cache_result)

            # 7. 压力测试 (极限负载)
            logger.info("💥 Phase 7: 压力测试 (极限负载)")
            stress_result = await self._stress_test()
            self.test_results.append(stress_result)

            # 8. 生成报告
            logger.info("📋 Phase 8: 生成性能报告")
            report = await self._generate_comprehensive_report()

            # 9. 生成图表
            logger.info("📈 Phase 9: 生成性能图表")
            await self._generate_performance_charts()

            logger.info("✅ 综合性能测试完成")
            return report

        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()

    async def _baseline_performance_test(self) -> PerformanceTestResult:
        """基准性能测试"""
        logger.info("执行基准性能测试...")

        start_time = datetime.now()
        response_times = []
        successful_requests = 0
        failed_requests = 0

        # 监控开始
        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 执行100个顺序请求作为基准
            for i in range(100):
                request_start = time.time()

                try:
                    async with self.session.get(f"{self.base_url}/api/status") as response:
                        if response.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1

                        duration_ms = (time.time() - request_start) * 1000
                        response_times.append(duration_ms)

                except Exception as e:
                    failed_requests += 1
                    duration_ms = (time.time() - request_start) * 1000
                    response_times.append(duration_ms)

                await asyncio.sleep(0.1)  # 100ms间隔

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return PerformanceTestResult(
            test_name="Baseline Performance Test",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=len(response_times),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=len(response_times) / duration if duration > 0 else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=self._percentile(response_times, 50),
            p95_response_time_ms=self._percentile(response_times, 95),
            p99_response_time_ms=self._percentile(response_times, 99),
            max_response_time_ms=max(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            error_rate_percent=(failed_requests / len(response_times) * 100) if response_times else 0,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0
        )

    async def _load_test(self) -> PerformanceTestResult:
        """负载测试 - 1000并发用户"""
        logger.info("执行负载测试 (1000并发用户)...")

        config = self.test_configs['load_test']
        start_time = datetime.now()

        # 清理之前的监控数据
        self.cpu_samples.clear()
        self.memory_samples.clear()

        # 启动系统监控
        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 执行负载测试
            results = await self._execute_concurrent_test(
                concurrent_users=config['concurrent_users'],
                duration_seconds=config['duration_seconds'],
                ramp_up_seconds=config['ramp_up_seconds']
            )

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return PerformanceTestResult(
            test_name=f"Load Test ({config['concurrent_users']} users)",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            **results,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0
        )

    async def _response_time_test(self) -> PerformanceTestResult:
        """响应时间测试"""
        logger.info("执行响应时间测试...")

        start_time = datetime.now()
        response_times = []
        successful_requests = 0
        failed_requests = 0

        # 测试不同类型的端点
        endpoints = [
            "/api/health",
            "/api/status",
            "/api/metrics",
            "/api/users",
            "/api/auth/login"
        ]

        # 清理监控数据
        self.cpu_samples.clear()
        self.memory_samples.clear()

        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 对每个端点执行多次请求
            for endpoint in endpoints:
                for _ in range(50):  # 每个端点50次请求
                    request_start = time.time()

                    try:
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            duration_ms = (time.time() - request_start) * 1000
                            response_times.append(duration_ms)

                            if response.status in [200, 201, 202]:
                                successful_requests += 1
                            else:
                                failed_requests += 1

                    except Exception as e:
                        duration_ms = (time.time() - request_start) * 1000
                        response_times.append(duration_ms)
                        failed_requests += 1

                    await asyncio.sleep(0.02)  # 20ms间隔

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return PerformanceTestResult(
            test_name="Response Time Test",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=len(response_times),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=len(response_times) / duration if duration > 0 else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=self._percentile(response_times, 50),
            p95_response_time_ms=self._percentile(response_times, 95),
            p99_response_time_ms=self._percentile(response_times, 99),
            max_response_time_ms=max(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            error_rate_percent=(failed_requests / len(response_times) * 100) if response_times else 0,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0
        )

    async def _memory_stress_test(self) -> PerformanceTestResult:
        """内存压力测试"""
        logger.info("执行内存压力测试...")

        start_time = datetime.now()

        # 清理监控数据
        self.cpu_samples.clear()
        self.memory_samples.clear()

        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 创建内存压力 - 大量并发连接
            results = await self._execute_concurrent_test(
                concurrent_users=500,
                duration_seconds=120,  # 2分钟
                ramp_up_seconds=20,
                endpoint="/api/data/large"  # 假设有大数据端点
            )

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return PerformanceTestResult(
            test_name="Memory Stress Test",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            **results,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0
        )

    async def _database_performance_test(self) -> PerformanceTestResult:
        """数据库查询性能测试"""
        logger.info("执行数据库查询性能测试...")

        start_time = datetime.now()
        response_times = []
        successful_requests = 0
        failed_requests = 0

        # 数据库相关端点
        db_endpoints = [
            "/api/users",
            "/api/users/search",
            "/api/analytics",
            "/api/reports"
        ]

        self.cpu_samples.clear()
        self.memory_samples.clear()

        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 测试数据库密集型操作
            for endpoint in db_endpoints:
                for _ in range(25):  # 每个端点25次请求
                    request_start = time.time()

                    try:
                        pass  # Auto-fixed empty block
                        # 添加查询参数以触发数据库操作
                        params = {"limit": 100, "sort": "created_at", "filter": "active"}
                        async with self.session.get(f"{self.base_url}{endpoint}", params=params) as response:
                            duration_ms = (time.time() - request_start) * 1000
                            response_times.append(duration_ms)

                            if response.status in [200, 201]:
                                successful_requests += 1
                            else:
                                failed_requests += 1

                    except Exception as e:
                        duration_ms = (time.time() - request_start) * 1000
                        response_times.append(duration_ms)
                        failed_requests += 1

                    await asyncio.sleep(0.05)  # 50ms间隔

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 计算数据库查询时间 (假设响应时间主要来自数据库)
        avg_db_time_ms = statistics.mean(response_times) if response_times else 0

        return PerformanceTestResult(
            test_name="Database Performance Test",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=len(response_times),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=len(response_times) / duration if duration > 0 else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=self._percentile(response_times, 50),
            p95_response_time_ms=self._percentile(response_times, 95),
            p99_response_time_ms=self._percentile(response_times, 99),
            max_response_time_ms=max(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            error_rate_percent=(failed_requests / len(response_times) * 100) if response_times else 0,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0,
            database_query_time_ms=avg_db_time_ms
        )

    async def _cache_performance_test(self) -> PerformanceTestResult:
        """缓存性能测试"""
        logger.info("执行缓存性能测试...")

        start_time = datetime.now()
        response_times = []
        successful_requests = 0
        failed_requests = 0
        cache_hits = 0
        cache_misses = 0

        self.cpu_samples.clear()
        self.memory_samples.clear()

        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            pass  # Auto-fixed empty block
            # 第一轮：预热缓存
            warmup_endpoints = ["/api/users/1", "/api/users/2", "/api/users/3", "/api/config"]

            for endpoint in warmup_endpoints:
                for _ in range(5):  # 预热5次
                    try:
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            if response.status == 200:
                                cache_misses += 1
                    except:
                        pass
                    await asyncio.sleep(0.01)

            # 第二轮：测试缓存命中
            for endpoint in warmup_endpoints:
                for _ in range(20):  # 每个端点20次请求
                    request_start = time.time()

                    try:
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            duration_ms = (time.time() - request_start) * 1000
                            response_times.append(duration_ms)

                            if response.status == 200:
                                successful_requests += 1
                                # 假设响应时间<50ms为缓存命中
                                if duration_ms < 50:
                                    cache_hits += 1
                                else:
                                    cache_misses += 1
                            else:
                                failed_requests += 1

                    except Exception as e:
                        duration_ms = (time.time() - request_start) * 1000
                        response_times.append(duration_ms)
                        failed_requests += 1
                        cache_misses += 1

                    await asyncio.sleep(0.01)  # 10ms间隔

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0

        return PerformanceTestResult(
            test_name="Cache Performance Test",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            total_requests=len(response_times),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=len(response_times) / duration if duration > 0 else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=self._percentile(response_times, 50),
            p95_response_time_ms=self._percentile(response_times, 95),
            p99_response_time_ms=self._percentile(response_times, 99),
            max_response_time_ms=max(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            error_rate_percent=(failed_requests / len(response_times) * 100) if response_times else 0,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0,
            cache_hit_rate_percent=cache_hit_rate,
            additional_metrics={
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "total_cache_requests": total_cache_requests
            }
        )

    async def _stress_test(self) -> PerformanceTestResult:
        """压力测试 - 极限负载"""
        logger.info("执行压力测试 (极限负载)...")

        config = self.test_configs['stress_test']
        start_time = datetime.now()

        self.cpu_samples.clear()
        self.memory_samples.clear()

        monitor_task = asyncio.create_task(self._monitor_system_resources())

        try:
            results = await self._execute_concurrent_test(
                concurrent_users=config['concurrent_users'],
                duration_seconds=config['duration_seconds'],
                ramp_up_seconds=config['ramp_up_seconds']
            )

        finally:
            monitor_task.cancel()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return PerformanceTestResult(
            test_name=f"Stress Test ({config['concurrent_users']} users)",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            **results,
            cpu_usage_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            memory_usage_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            peak_memory_mb=max(self.memory_samples) if self.memory_samples else 0
        )

    async def _execute_concurrent_test(self, concurrent_users: int, duration_seconds: int,
                                     ramp_up_seconds: int, endpoint: str = "/api/health") -> Dict[str, Any]:
        """执行并发测试"""
        logger.info(f"执行并发测试: {concurrent_users}用户, 持续{duration_seconds}秒")

        response_times = []
        successful_requests = 0
        failed_requests = 0

        # 计算每秒启动的用户数
        users_per_second = concurrent_users / ramp_up_seconds if ramp_up_seconds > 0 else concurrent_users

        async def user_session(user_id: int, start_delay: float):
            """单个用户会话"""
            await asyncio.sleep(start_delay)

            session_start = time.time()
            session_end = session_start + duration_seconds

            nonlocal successful_requests, failed_requests, response_times

            while time.time() < session_end:
                request_start = time.time()

                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        duration_ms = (time.time() - request_start) * 1000
                        response_times.append(duration_ms)

                        if response.status in [200, 201, 202]:
                            successful_requests += 1
                        else:
                            failed_requests += 1

                except Exception as e:
                    duration_ms = (time.time() - request_start) * 1000
                    response_times.append(duration_ms)
                    failed_requests += 1

                # 随机等待时间，模拟真实用户行为
                await asyncio.sleep(random.uniform(0.1, 1.0))

        # 创建并启动用户会话
        tasks = []
        for user_id in range(concurrent_users):
            start_delay = (user_id / users_per_second) if users_per_second > 0 else 0
            task = asyncio.create_task(user_session(user_id, start_delay))
            tasks.append(task)

        # 等待所有用户会话完成
        await asyncio.gather(*tasks, return_exceptions=True)

        total_requests = len(response_times)

        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'requests_per_second': total_requests / duration_seconds if duration_seconds > 0 else 0,
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'p50_response_time_ms': self._percentile(response_times, 50),
            'p95_response_time_ms': self._percentile(response_times, 95),
            'p99_response_time_ms': self._percentile(response_times, 99),
            'max_response_time_ms': max(response_times) if response_times else 0,
            'min_response_time_ms': min(response_times) if response_times else 0,
            'error_rate_percent': (failed_requests / total_requests * 100) if total_requests > 0 else 0
        }

    async def _monitor_system_resources(self):
        """监控系统资源"""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                memory_mb = memory_info.used / 1024 / 1024

                self.cpu_samples.append(cpu_percent)
                self.memory_samples.append(memory_mb)

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控系统资源失败: {e}")
                await asyncio.sleep(1)

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def _generate_comprehensive_report(self) -> PerformanceReport:
        """生成综合性能报告"""
        logger.info("生成综合性能报告...")

        # 计算整体评分
        overall_score = self._calculate_overall_score()

        # 识别瓶颈
        bottlenecks = self._identify_bottlenecks()

        # 生成建议
        recommendations = self._generate_recommendations(bottlenecks)

        # 收集系统信息
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "platform": psutil.platform.platform(),
            "python_version": psutil.sys.version,
            "test_duration_minutes": sum(r.duration_seconds for r in self.test_results) / 60
        }

        return PerformanceReport(
            timestamp=datetime.now(),
            overall_score=overall_score,
            test_results=self.test_results,
            system_info=system_info,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            charts_generated=[]
        )

    def _calculate_overall_score(self) -> float:
        """计算整体性能评分 (0-100)"""
        if not self.test_results:
            return 0.0

        scores = []

        for result in self.test_results:
            score = 100.0

            # 响应时间评分 (30%)
            if result.p95_response_time_ms > 2000:
                score -= 30
            elif result.p95_response_time_ms > 1000:
                score -= 20
            elif result.p95_response_time_ms > 500:
                score -= 10

            # 错误率评分 (25%)
            if result.error_rate_percent > 5:
                score -= 25
            elif result.error_rate_percent > 1:
                score -= 10
            elif result.error_rate_percent > 0.1:
                score -= 5

            # 吞吐量评分 (20%)
            if result.requests_per_second < 10:
                score -= 20
            elif result.requests_per_second < 50:
                score -= 10
            elif result.requests_per_second < 100:
                score -= 5

            # 系统资源评分 (25%)
            if result.cpu_usage_percent > 90:
                score -= 15
            elif result.cpu_usage_percent > 80:
                score -= 10

            if result.memory_usage_mb > 2048:  # 2GB
                score -= 10
            elif result.memory_usage_mb > 1024:  # 1GB
                score -= 5

            scores.append(max(0, score))

        return statistics.mean(scores)

    def _identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        for result in self.test_results:
            pass  # Auto-fixed empty block
            # 响应时间瓶颈
            if result.p95_response_time_ms > 1000:
                bottlenecks.append(f"{result.test_name}: P95响应时间过高 ({result.p95_response_time_ms:.1f}ms)")

            # 错误率瓶颈
            if result.error_rate_percent > 1:
                bottlenecks.append(f"{result.test_name}: 错误率过高 ({result.error_rate_percent:.1f}%)")

            # 吞吐量瓶颈
            if result.requests_per_second < 50:
                bottlenecks.append(f"{result.test_name}: 吞吐量过低 ({result.requests_per_second:.1f} RPS)")

            # CPU瓶颈
            if result.cpu_usage_percent > 80:
                bottlenecks.append(f"{result.test_name}: CPU使用率过高 ({result.cpu_usage_percent:.1f}%)")

            # 内存瓶颈
            if result.memory_usage_mb > 1024:
                bottlenecks.append(f"{result.test_name}: 内存使用过高 ({result.memory_usage_mb:.1f}MB)")

            # 缓存瓶颈
            if result.cache_hit_rate_percent > 0 and result.cache_hit_rate_percent < 80:
                bottlenecks.append(f"{result.test_name}: 缓存命中率低 ({result.cache_hit_rate_percent:.1f}%)")

            # 数据库瓶颈
            if result.database_query_time_ms > 500:
                bottlenecks.append(f"{result.test_name}: 数据库查询时间过长 ({result.database_query_time_ms:.1f}ms)")

        return list(set(bottlenecks))  # 去重

    def _generate_recommendations(self, bottlenecks: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        for bottleneck in bottlenecks:
            if "响应时间过高" in bottleneck:
                recommendations.append("建议优化应用逻辑，添加缓存层，或优化数据库查询")
            elif "错误率过高" in bottleneck:
                recommendations.append("检查应用日志，修复错误处理逻辑，增强系统稳定性")
            elif "吞吐量过低" in bottleneck:
                recommendations.append("考虑水平扩展，优化资源配置，或使用负载均衡")
            elif "CPU使用率过高" in bottleneck:
                recommendations.append("优化CPU密集型操作，考虑垂直扩展或分布式处理")
            elif "内存使用过高" in bottleneck:
                recommendations.append("优化内存使用，检查内存泄漏，考虑增加内存或优化算法")
            elif "缓存命中率低" in bottleneck:
                recommendations.append("优化缓存策略，增加缓存预热，调整缓存TTL")
            elif "数据库查询时间过长" in bottleneck:
                recommendations.append("优化数据库索引，重构查询语句，考虑数据库连接池优化")

        # 添加通用建议
        if not recommendations:
            recommendations.append("系统性能良好，建议定期监控并持续优化")

        return list(set(recommendations))  # 去重

    async def _generate_performance_charts(self):
        """生成性能图表"""
        logger.info("生成性能图表...")

        # 确保输出目录存在
        charts_dir = Path("performance_charts")
        charts_dir.mkdir(exist_ok=True)

        # 1. 响应时间对比图
        self._create_response_time_chart(charts_dir)

        # 2. 吞吐量对比图
        self._create_throughput_chart(charts_dir)

        # 3. 系统资源使用图
        self._create_resource_usage_chart(charts_dir)

        # 4. 错误率图
        self._create_error_rate_chart(charts_dir)

        logger.info(f"图表已生成到 {charts_dir} 目录")

    def _create_response_time_chart(self, charts_dir: Path):
        """创建响应时间对比图"""
        try:
            test_names = [r.test_name for r in self.test_results]
            avg_times = [r.avg_response_time_ms for r in self.test_results]
            p95_times = [r.p95_response_time_ms for r in self.test_results]
            p99_times = [r.p99_response_time_ms for r in self.test_results]

            plt.figure(figsize=(12, 6))
            x = range(len(test_names))

            plt.bar([i - 0.25 for i in x], avg_times, 0.25, label='Average', alpha=0.8)
            plt.bar(x, p95_times, 0.25, label='P95', alpha=0.8)
            plt.bar([i + 0.25 for i in x], p99_times, 0.25, label='P99', alpha=0.8)

            plt.xlabel('Test Cases')
            plt.ylabel('Response Time (ms)')
            plt.title('Response Time Comparison')
            plt.xticks(x, test_names, rotation=45, ha='right')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plt.savefig(charts_dir / "response_time_comparison.png", dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"创建响应时间图表失败: {e}")

    def _create_throughput_chart(self, charts_dir: Path):
        """创建吞吐量对比图"""
        try:
            test_names = [r.test_name for r in self.test_results]
            throughputs = [r.requests_per_second for r in self.test_results]

            plt.figure(figsize=(10, 6))
            bars = plt.bar(test_names, throughputs, alpha=0.7, color='skyblue')

            # 添加数值标签
            for bar, value in zip(bars, throughputs):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}', ha='center', va='bottom')

            plt.xlabel('Test Cases')
            plt.ylabel('Requests per Second')
            plt.title('Throughput Comparison')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()

            plt.savefig(charts_dir / "throughput_comparison.png", dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"创建吞吐量图表失败: {e}")

    def _create_resource_usage_chart(self, charts_dir: Path):
        """创建系统资源使用图"""
        try:
            test_names = [r.test_name for r in self.test_results]
            cpu_usage = [r.cpu_usage_percent for r in self.test_results]
            memory_usage = [r.memory_usage_mb for r in self.test_results]

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # CPU使用率
            ax1.bar(test_names, cpu_usage, alpha=0.7, color='orange')
            ax1.set_ylabel('CPU Usage (%)')
            ax1.set_title('CPU Usage by Test')
            ax1.set_xticklabels(test_names, rotation=45, ha='right')
            ax1.grid(True, alpha=0.3)

            # 内存使用量
            ax2.bar(test_names, memory_usage, alpha=0.7, color='green')
            ax2.set_ylabel('Memory Usage (MB)')
            ax2.set_title('Memory Usage by Test')
            ax2.set_xticklabels(test_names, rotation=45, ha='right')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(charts_dir / "resource_usage.png", dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"创建资源使用图表失败: {e}")

    def _create_error_rate_chart(self, charts_dir: Path):
        """创建错误率图"""
        try:
            test_names = [r.test_name for r in self.test_results]
            error_rates = [r.error_rate_percent for r in self.test_results]

            plt.figure(figsize=(10, 6))
            colors = ['red' if rate > 1 else 'yellow' if rate > 0.1 else 'green' for rate in error_rates]
            bars = plt.bar(test_names, error_rates, alpha=0.7, color=colors)

            # 添加数值标签
            for bar, value in zip(bars, error_rates):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{value:.2f}%', ha='center', va='bottom')

            plt.xlabel('Test Cases')
            plt.ylabel('Error Rate (%)')
            plt.title('Error Rate by Test')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()

            plt.savefig(charts_dir / "error_rate.png", dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            logger.error(f"创建错误率图表失败: {e}")

    async def save_report_to_file(self, report: PerformanceReport, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 转换为可序列化的格式
        report_data = {
            "timestamp": report.timestamp.isoformat(),
            "overall_score": report.overall_score,
            "system_info": report.system_info,
            "bottlenecks": report.bottlenecks,
            "recommendations": report.recommendations,
            "charts_generated": report.charts_generated,
            "test_results": [asdict(result) for result in report.test_results]
        }

        # 处理datetime字段
        for test_result in report_data["test_results"]:
            test_result["start_time"] = test_result["start_time"].isoformat()
            test_result["end_time"] = test_result["end_time"].isoformat()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"性能报告已保存到: {filename}")

async def main():
    """主函数"""
    logger.info("🚀 启动Claude Enhancer综合性能测试")

    # 配置测试目标 - 可以根据实际情况修改
    target_url = "http://localhost:8080"  # 默认测试本地服务

    # 检查是否有性能演示服务运行
    try:
        import subprocess
        import sys

        # 启动性能演示服务
        logger.info("启动性能演示服务...")
        demo_process = subprocess.Popen([
            sys.executable, "run_performance_demo.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 等待服务启动
        await asyncio.sleep(10)

    except Exception as e:
        logger.warning(f"无法启动演示服务: {e}")
        logger.info("将测试模拟端点...")

    try:
        pass  # Auto-fixed empty block
        # 创建测试器
        tester = ComprehensivePerformanceTester(target_url)

        # 初始化
        await tester.initialize()

        # 运行测试
        report = await tester.run_comprehensive_tests()

        # 保存报告
        await tester.save_report_to_file(report)

        # 打印摘要
    print("\n" + "="*80)
    print("🎯 PERFECT21 性能测试报告摘要")
    print("="*80)
    print(f"整体性能评分: {report.overall_score:.1f}/100")
    print(f"测试时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试项目数: {len(report.test_results)}")

        if report.bottlenecks:
        print(f"\n⚠️ 发现的瓶颈 ({len(report.bottlenecks)}个):")
            for bottleneck in report.bottlenecks:
                print(f"  - {bottleneck}")

        if report.recommendations:
        print(f"\n💡 优化建议 ({len(report.recommendations)}个):")
            for recommendation in report.recommendations:
            print(f"  - {recommendation}")

    print("\n📊 详细测试结果:")
        for result in report.test_results:
            print(f"\n{result.test_name}:")
            print(f"  RPS: {result.requests_per_second:.1f}")
            print(f"  平均响应时间: {result.avg_response_time_ms:.1f}ms")
            print(f"  P95响应时间: {result.p95_response_time_ms:.1f}ms")
            print(f"  错误率: {result.error_rate_percent:.2f}%")
            print(f"  CPU使用: {result.cpu_usage_percent:.1f}%")
            print(f"  内存使用: {result.memory_usage_mb:.1f}MB")
            if result.cache_hit_rate_percent > 0:
                print(f"  缓存命中率: {result.cache_hit_rate_percent:.1f}%")

    print(f"\n📁 报告文件: performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print("📈 图表文件: performance_charts/ 目录")
    # print("="*80)

        return 0

    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        return 1

    finally:
        pass  # Auto-fixed empty block
        # 清理
        try:
            if 'demo_process' in locals():
                demo_process.terminate()
        except:
            pass

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)