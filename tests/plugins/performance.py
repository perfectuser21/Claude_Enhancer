#!/usr/bin/env python3
"""
性能测试插件 - 用于性能测试和负载测试
提供性能监控、负载测试、压力测试功能
"""

import time
import psutil
import asyncio
import pytest
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from contextlib import contextmanager


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'requests_per_second': 0,
            'error_rate': 0
        }
        self.start_time = None
        self.end_time = None
    
    @contextmanager
    def monitor_performance(self):
        """性能监控上下文管理器"""
        self.start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield self
        finally:
            self.end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.metrics['memory_usage'].append(final_memory - initial_memory)
    
    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.metrics['response_times'].append(response_time)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        response_times = self.metrics['response_times']
        if not response_times:
            return {}
        
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        return {
            'total_requests': len(response_times),
            'avg_response_time': sum(response_times) / len(response_times) * 1000,  # ms
            'min_response_time': min(response_times) * 1000,
            'max_response_time': max(response_times) * 1000,
            'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] * 1000,
            'requests_per_second': len(response_times) / duration if duration > 0 else 0,
            'total_duration': duration,
            'memory_usage_mb': sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0
        }


class LoadTester:
    """负载测试器"""
    
    def __init__(self, target_function, max_workers: int = 100):
        self.target_function = target_function
        self.max_workers = max_workers
        self.results = []
        self.errors = []
    
    async def run_async_load_test(self, concurrent_requests: int, total_requests: int, **kwargs) -> Dict[str, Any]:
        """运行异步负载测试"""
        semaphore = asyncio.Semaphore(concurrent_requests)
        start_time = time.time()
        
        async def single_request():
            async with semaphore:
                request_start = time.time()
                try:
                    result = await self.target_function(**kwargs)
                    request_end = time.time()
                    return {
                        'success': True,
                        'response_time': request_end - request_start,
                        'result': result
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'response_time': time.time() - request_start
                    }
        
        # 并发执行请求
        tasks = [single_request() for _ in range(total_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 统计结果
        successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed_requests = total_requests - successful_requests
        response_times = [r['response_time'] for r in results if isinstance(r, dict) and 'response_time' in r]
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests * 100,
            'requests_per_second': total_requests / duration,
            'avg_response_time': sum(response_times) / len(response_times) * 1000 if response_times else 0,
            'min_response_time': min(response_times) * 1000 if response_times else 0,
            'max_response_time': max(response_times) * 1000 if response_times else 0,
            'duration': duration,
            'concurrent_requests': concurrent_requests
        }
    
    def run_sync_load_test(self, concurrent_requests: int, total_requests: int, **kwargs) -> Dict[str, Any]:
        """运行同步负载测试"""
        start_time = time.time()
        results = []
        
        def single_request():
            request_start = time.time()
            try:
                result = self.target_function(**kwargs)
                return {
                    'success': True,
                    'response_time': time.time() - request_start,
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'response_time': time.time() - request_start
                }
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=min(concurrent_requests, self.max_workers)) as executor:
            futures = [executor.submit(single_request) for _ in range(total_requests)]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'response_time': 0
                    })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 统计结果
        successful_requests = sum(1 for r in results if r.get('success'))
        failed_requests = len(results) - successful_requests
        response_times = [r['response_time'] for r in results if 'response_time' in r]
        
        return {
            'total_requests': len(results),
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / len(results) * 100 if results else 0,
            'requests_per_second': len(results) / duration if duration > 0 else 0,
            'avg_response_time': sum(response_times) / len(response_times) * 1000 if response_times else 0,
            'min_response_time': min(response_times) * 1000 if response_times else 0,
            'max_response_time': max(response_times) * 1000 if response_times else 0,
            'duration': duration,
            'concurrent_requests': concurrent_requests
        }


@pytest.fixture
def performance_monitor():
    """性能监控器夹具"""
    return PerformanceMonitor()

@pytest.fixture
def load_tester():
    """负载测试器工厂夹具"""
    def _create_load_tester(target_function, max_workers=100):
        return LoadTester(target_function, max_workers)
    return _create_load_tester

@pytest.mark.performance
class TestPerformanceHelpers:
    """性能测试辅助类"""
    
    @staticmethod
    def assert_response_time(response_time_ms: float, max_acceptable_ms: float):
        """断言响应时间"""
        assert response_time_ms <= max_acceptable_ms, f"Response time {response_time_ms}ms exceeds maximum {max_acceptable_ms}ms"
    
    @staticmethod
    def assert_throughput(requests_per_second: float, min_acceptable_rps: float):
        """断言吞吐量"""
        assert requests_per_second >= min_acceptable_rps, f"Throughput {requests_per_second} RPS below minimum {min_acceptable_rps} RPS"
    
    @staticmethod
    def assert_success_rate(success_rate: float, min_acceptable_rate: float):
        """断言成功率"""
        assert success_rate >= min_acceptable_rate, f"Success rate {success_rate}% below minimum {min_acceptable_rate}%"
    
    @staticmethod
    def assert_memory_usage(memory_mb: float, max_acceptable_mb: float):
        """断言内存使用"""
        assert memory_mb <= max_acceptable_mb, f"Memory usage {memory_mb}MB exceeds maximum {max_acceptable_mb}MB"


class StressTester:
    """压力测试器"""
    
    def __init__(self, target_function):
        self.target_function = target_function
        self.stress_results = []
    
    async def run_stress_test(self, 
                            start_concurrent: int = 1,
                            max_concurrent: int = 100,
                            step: int = 10,
                            requests_per_step: int = 50,
                            **kwargs) -> List[Dict[str, Any]]:
        """运行压力测试 - 逐步增加并发数"""
        
        results = []
        
        for concurrent in range(start_concurrent, max_concurrent + 1, step):
            print(f"\n正在运行压力测试: {concurrent} 并发请求...")
            
            load_tester = LoadTester(self.target_function)
            result = await load_tester.run_async_load_test(
                concurrent_requests=concurrent,
                total_requests=requests_per_step,
                **kwargs
            )
            
            result['concurrent_level'] = concurrent
            results.append(result)
            
            # 检查是否达到破坏点
            if result['success_rate'] < 95 or result['avg_response_time'] > 5000:  # 5秒
                print(f"达到破坏点: 成功率 {result['success_rate']:.1f}%, 平均响应时间 {result['avg_response_time']:.1f}ms")
                break
            
            # 等待一下面再次测试
            await asyncio.sleep(1)
        
        return results
    
    def find_breaking_point(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """查找破坏点"""
        for result in results:
            if result['success_rate'] < 95 or result['avg_response_time'] > 5000:
                return {
                    'breaking_point_concurrent': result['concurrent_level'],
                    'max_stable_concurrent': max(0, result['concurrent_level'] - 10),
                    'breaking_success_rate': result['success_rate'],
                    'breaking_response_time': result['avg_response_time']
                }
        
        # 未找到破坏点
        last_result = results[-1] if results else {}
        return {
            'breaking_point_concurrent': None,
            'max_stable_concurrent': last_result.get('concurrent_level', 0),
            'breaking_success_rate': None,
            'breaking_response_time': None
        }


@pytest.fixture
def stress_tester():
    """压力测试器夹具"""
    def _create_stress_tester(target_function):
        return StressTester(target_function)
    return _create_stress_tester


# Pytest 标记
def pytest_configure(config):
    """注册Pytest标记"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "load: mark test as load test"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as stress test"
    )
