#!/usr/bin/env python3
"""
Perfect21 用户登录API负载测试套件
使用K6和locust进行性能和负载测试
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from typing import Dict, Any, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class LoadTestConfig:
    """负载测试配置"""
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    test_duration: int = 60  # 秒
    ramp_up_time: int = 10  # 秒
    think_time: float = 1.0  # 秒
    target_rps: int = 100  # 每秒请求数

@dataclass 
class LoadTestResult:
    """负载测试结果"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    test_duration: float
    concurrent_users: int
    
class AuthAPILoadTester:
    """认证API负载测试器"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = []
        self.errors = []
        self.response_times = []
        
    async def run_load_test(self) -> LoadTestResult:
        """运行负载测试"""
        print(f"🚀 开始负载测试: {self.config.concurrent_users} 并发用户, {self.config.test_duration} 秒")
        
        start_time = time.time()
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.config.concurrent_users)
        
        # 创建任务列表
        tasks = []
        
        # 计算总请求数
        total_requests = self.config.target_rps * self.config.test_duration
        
        # 创建请求任务
        for i in range(total_requests):
            task = asyncio.create_task(self._simulate_user_session(semaphore, i))
            tasks.append(task)
            
            # 控制请求速率
            if i > 0 and i % self.config.target_rps == 0:
                await asyncio.sleep(1)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        return self._calculate_results(test_duration)
    
    async def _simulate_user_session(self, semaphore: asyncio.Semaphore, user_id: int):
        """模拟用户会话"""
        async with semaphore:
            try:
                async with aiohttp.ClientSession() as session:
                    # 模拟登录操作
                    await self._perform_login(session, user_id)
                    
                    # 模拟思考时间
                    await asyncio.sleep(self.config.think_time)
                    
                    # 模拟其他API调用
                    await self._perform_api_calls(session)
                    
            except Exception as e:
                self.errors.append({
                    'user_id': user_id,
                    'error': str(e),
                    'timestamp': time.time()
                })
    
    async def _perform_login(self, session: aiohttp.ClientSession, user_id: int):
        """执行登录操作"""
        login_url = f"{self.config.base_url}/api/auth/login"
        login_data = {
            "email": f"testuser{user_id % 100}@example.com",
            "password": "testpassword"
        }
        
        start_time = time.time()
        
        try:
            async with session.post(login_url, json=login_data) as response:
                response_time = time.time() - start_time
                self.response_times.append(response_time * 1000)  # 转换为毫秒
                
                result = {
                    'url': login_url,
                    'method': 'POST',
                    'status_code': response.status,
                    'response_time': response_time,
                    'user_id': user_id,
                    'timestamp': time.time()
                }
                
                if response.status == 200:
                    response_data = await response.json()
                    result['response_data'] = response_data
                    result['success'] = response_data.get('success', False)
                else:
                    result['success'] = False
                    result['error'] = f"HTTP {response.status}"
                
                self.results.append(result)
                
        except Exception as e:
            self.errors.append({
                'url': login_url,
                'method': 'POST',
                'user_id': user_id,
                'error': str(e),
                'timestamp': time.time()
            })
    
    async def _perform_api_calls(self, session: aiohttp.ClientSession):
        """执行其他API调用"""
        # 模拟其他常用API调用
        api_calls = [
            {'method': 'GET', 'url': f"{self.config.base_url}/health"},
            {'method': 'GET', 'url': f"{self.config.base_url}/status"},
            {'method': 'GET', 'url': f"{self.config.base_url}/"},
        ]
        
        for api_call in api_calls:
            start_time = time.time()
            
            try:
                if api_call['method'] == 'GET':
                    async with session.get(api_call['url']) as response:
                        response_time = time.time() - start_time
                        self.response_times.append(response_time * 1000)
                        
                        self.results.append({
                            'url': api_call['url'],
                            'method': api_call['method'],
                            'status_code': response.status,
                            'response_time': response_time,
                            'success': response.status == 200,
                            'timestamp': time.time()
                        })
                        
            except Exception as e:
                self.errors.append({
                    'url': api_call['url'],
                    'method': api_call['method'],
                    'error': str(e),
                    'timestamp': time.time()
                })
    
    def _calculate_results(self, test_duration: float) -> LoadTestResult:
        """计算测试结果"""
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.get('success', False))
        failed_requests = total_requests - successful_requests + len(self.errors)
        
        if self.response_times:
            avg_response_time = statistics.mean(self.response_times)
            min_response_time = min(self.response_times)
            max_response_time = max(self.response_times)
            
            sorted_times = sorted(self.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
            p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = (failed_requests / (total_requests + len(self.errors))) * 100 if (total_requests + len(self.errors)) > 0 else 0
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            test_duration=test_duration,
            concurrent_users=self.config.concurrent_users
        )
    
    def generate_load_test_report(self, result: LoadTestResult) -> str:
        """生成负载测试报告"""
        report = f"""
# Perfect21 登录API负载测试报告

## 测试配置
- **并发用户数**: {result.concurrent_users}
- **测试时长**: {result.test_duration:.2f}秒
- **目标RPS**: {self.config.target_rps}
- **思考时间**: {self.config.think_time}s

## 性能指标
- **总请求数**: {result.total_requests}
- **成功请求**: {result.successful_requests}
- **失败请求**: {result.failed_requests}
- **成功率**: {((result.successful_requests / result.total_requests) * 100):.2f}%
- **错误率**: {result.error_rate:.2f}%

## 响应时间（毫秒）
- **平均响应时间**: {result.avg_response_time:.2f}ms
- **最小响应时间**: {result.min_response_time:.2f}ms
- **最大响应时间**: {result.max_response_time:.2f}ms
- **95%分位数**: {result.p95_response_time:.2f}ms
- **99%分位数**: {result.p99_response_time:.2f}ms

## 吞吐量
- **实际RPS**: {result.requests_per_second:.2f}
- **目标RPS**: {self.config.target_rps}
- **RPS达成率**: {(result.requests_per_second / self.config.target_rps * 100):.2f}%

## 性能评估
{self._generate_performance_assessment(result)}

## 错误统计
{self._generate_error_summary()}
        """
        
        return report
    
    def _generate_performance_assessment(self, result: LoadTestResult) -> str:
        """生成性能评估"""
        assessment = []
        
        # 响应时间评估
        if result.avg_response_time <= 100:
            assessment.append("✅ 平均响应时间优秀 (<=100ms)")
        elif result.avg_response_time <= 200:
            assessment.append("🟡 平均响应时间良好 (<=200ms)")
        else:
            assessment.append("❌ 平均响应时间需要优化 (>200ms)")
        
        # 成功率评估
        success_rate = (result.successful_requests / result.total_requests) * 100
        if success_rate >= 99.9:
            assessment.append("✅ 成功率优秀 (>=99.9%)")
        elif success_rate >= 99:
            assessment.append("🟡 成功率良好 (>=99%)")
        else:
            assessment.append("❌ 成功率需要改进 (<99%)")
        
        # 吞吐量评估
        rps_achievement = (result.requests_per_second / self.config.target_rps) * 100
        if rps_achievement >= 95:
            assessment.append("✅ 吞吐量达标 (>=95%)")
        elif rps_achievement >= 80:
            assessment.append("🟡 吞吐量还可以 (>=80%)")
        else:
            assessment.append("❌ 吞吐量不足 (<80%)")
        
        return "\n".join([f"- {item}" for item in assessment])
    
    def _generate_error_summary(self) -> str:
        """生成错误统计"""
        if not self.errors:
            return "- ✅ 无错误发生"
        
        error_summary = []
        error_types = {}
        
        for error in self.errors:
            error_type = type(error.get('error', 'Unknown')).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for error_type, count in error_types.items():
            error_summary.append(f"- {error_type}: {count} 次")
        
        return "\n".join(error_summary)

class StressTester:
    """压力测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.stress_results = []
    
    async def run_stress_test(self, 
                            start_users: int = 1,
                            max_users: int = 100,
                            step: int = 10,
                            duration_per_step: int = 30) -> List[LoadTestResult]:
        """运行压力测试"""
        print(f"🔥 开始压力测试: {start_users} -> {max_users} 用户, 每步 {step} 用户")
        
        results = []
        
        for users in range(start_users, max_users + 1, step):
            print(f"\n正在测试 {users} 并发用户...")
            
            config = LoadTestConfig(
                base_url=self.base_url,
                concurrent_users=users,
                test_duration=duration_per_step,
                target_rps=users * 2  # 每个用户平均2RPS
            )
            
            load_tester = AuthAPILoadTester(config)
            result = await load_tester.run_load_test()
            results.append(result)
            
            # 输出实时结果
            success_rate = (result.successful_requests / result.total_requests) * 100 if result.total_requests > 0 else 0
            print(f"用户: {users}, RPS: {result.requests_per_second:.2f}, 平均响应: {result.avg_response_time:.2f}ms, 成功率: {success_rate:.2f}%")
            
            # 检查是否达到破坏点
            if success_rate < 95 or result.avg_response_time > 2000:  # 2秒
                print(f"\n❗ 达到破坏点: 成功率 {success_rate:.1f}%, 平均响应 {result.avg_response_time:.1f}ms")
                break
            
            # 等待一段时间再进行下一步
            await asyncio.sleep(5)
        
        return results
    
    def find_breaking_point(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """查找破坏点"""
        for result in results:
            success_rate = (result.successful_requests / result.total_requests) * 100
            
            if success_rate < 95 or result.avg_response_time > 2000:
                return {
                    'breaking_point_users': result.concurrent_users,
                    'max_stable_users': max(1, result.concurrent_users - 10),
                    'breaking_success_rate': success_rate,
                    'breaking_response_time': result.avg_response_time,
                    'breaking_rps': result.requests_per_second
                }
        
        # 未找到破坏点
        last_result = results[-1] if results else None
        if last_result:
            success_rate = (last_result.successful_requests / last_result.total_requests) * 100
            return {
                'breaking_point_users': None,
                'max_stable_users': last_result.concurrent_users,
                'breaking_success_rate': success_rate,
                'breaking_response_time': last_result.avg_response_time,
                'breaking_rps': last_result.requests_per_second
            }
        
        return {}


async def main():
    """主函数 - 运行负载测试"""
    print("🚀 Perfect21 登录API负载测试套件")
    
    # 配置测试参数
    config = LoadTestConfig(
        base_url="http://localhost:8000",
        concurrent_users=50,
        test_duration=120,
        target_rps=100
    )
    
    # 运行负载测试
    load_tester = AuthAPILoadTester(config)
    result = await load_tester.run_load_test()
    
    # 生成报告
    report = load_tester.generate_load_test_report(result)
    print(report)
    
    # 保存报告到文件
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"load_test_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存到: {report_file}")
    
    # 运行压力测试
    print("\n\n🔥 开始压力测试...")
    stress_tester = StressTester(config.base_url)
    stress_results = await stress_tester.run_stress_test(
        start_users=10,
        max_users=200,
        step=20,
        duration_per_step=60
    )
    
    # 查找破坏点
    breaking_point = stress_tester.find_breaking_point(stress_results)
    
    print("\n\n📈 压力测试结果:")
    if breaking_point.get('breaking_point_users'):
        print(f"- 破坏点: {breaking_point['breaking_point_users']} 并发用户")
        print(f"- 最大稳定用户数: {breaking_point['max_stable_users']}")
        print(f"- 破坏时成功率: {breaking_point['breaking_success_rate']:.2f}%")
        print(f"- 破坏时响应时间: {breaking_point['breaking_response_time']:.2f}ms")
    else:
        print(f"- 未找到破坏点, 最大测试到 {breaking_point.get('max_stable_users', 0)} 用户")


if __name__ == "__main__":
    asyncio.run(main())
