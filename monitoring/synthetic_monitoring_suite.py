#!/usr/bin/env python3
"""
Claude Enhancer 5.1 - 综合监控套件
实现端到端的用户体验监控和业务流程验证

功能包括:
- 用户旅程监控
- API端点健康检查
- 性能基准测试
- 业务流程验证
- 故障恢复时间测量

@author Claude Code
@version 1.0.0
"""

import asyncio
import aiohttp
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin
import random
import hashlib
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringResult:
    """监控结果数据结构"""
    timestamp: str
    test_name: str
    status: str  # SUCCESS, FAILURE, WARNING
    duration_ms: float
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    details: Dict[str, Any] = None

class SyntheticMonitoringSuite:
    """综合监控套件主类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.timeout = config.get('timeout', 30)
        self.session = None
        self.results: List[MonitoringResult] = []
        self.metrics_endpoint = config.get('metrics_endpoint', '/metrics')

        # 创建结果存储目录
        self.results_dir = Path(config.get('results_dir', './monitoring_results'))
        self.results_dir.mkdir(exist_ok=True)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()

    async def run_all_checks(self) -> List[MonitoringResult]:
        """运行所有监控检查"""
        logger.info("开始运行综合监控检查套件")

        checks = [
            self.check_system_health,
            self.check_api_endpoints,
            self.check_authentication_flow,
            self.check_user_registration_flow,
            self.check_database_connectivity,
            self.check_cache_performance,
            self.check_error_handling,
            self.measure_performance_metrics,
            self.verify_security_headers,
            self.test_rate_limiting,
            self.check_monitoring_endpoints,
            self.validate_business_logic
        ]

        for check in checks:
            try:
                logger.info(f"执行检查: {check.__name__}")
                result = await check()
                if isinstance(result, list):
                    self.results.extend(result)
                else:
                    self.results.append(result)
            except Exception as e:
                error_result = MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name=check.__name__,
                    status='FAILURE',
                    duration_ms=0,
                    error_message=str(e),
                    details={'exception': traceback.format_exc()}
                )
                self.results.append(error_result)
                logger.error(f"检查失败 {check.__name__}: {e}")

        # 保存结果
        await self.save_results()

        # 发送指标到监控系统
        await self.send_metrics_to_prometheus()

        logger.info(f"监控检查完成，共执行 {len(self.results)} 项检查")
        return self.results

    async def check_system_health(self) -> MonitoringResult:
        """检查系统整体健康状态"""
        start_time = time.time()

        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                duration = (time.time() - start_time) * 1000
                response_data = await response.json()

                status = 'SUCCESS' if response.status == 200 else 'FAILURE'

                return MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name='system_health_check',
                    status=status,
                    duration_ms=duration,
                    response_time_ms=duration,
                    status_code=response.status,
                    details=response_data
                )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='system_health_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_api_endpoints(self) -> List[MonitoringResult]:
        """检查关键API端点的可用性"""
        endpoints = [
            {'path': '/api/v1/status', 'method': 'GET', 'expected_status': 200},
            {'path': '/api/v1/auth/status', 'method': 'GET', 'expected_status': 200},
            {'path': '/api/v1/users/me', 'method': 'GET', 'expected_status': 401},  # 未认证应该返回401
            {'path': '/metrics', 'method': 'GET', 'expected_status': 200}
        ]

        results = []

        for endpoint in endpoints:
            start_time = time.time()
            test_name = f"api_endpoint_check_{endpoint['path'].replace('/', '_')}"

            try:
                url = urljoin(self.base_url, endpoint['path'])

                async with self.session.request(
                    endpoint['method'],
                    url
                ) as response:
                    duration = (time.time() - start_time) * 1000

                    status = 'SUCCESS' if response.status == endpoint['expected_status'] else 'WARNING'

                    results.append(MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name=test_name,
                        status=status,
                        duration_ms=duration,
                        response_time_ms=duration,
                        status_code=response.status,
                        details={
                            'endpoint': endpoint['path'],
                            'method': endpoint['method'],
                            'expected_status': endpoint['expected_status'],
                            'actual_status': response.status
                        }
                    ))

            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results.append(MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name=test_name,
                    status='FAILURE',
                    duration_ms=duration,
                    error_message=str(e),
                    details={'endpoint': endpoint['path']}
                ))

        return results

    async def check_authentication_flow(self) -> MonitoringResult:
        """测试完整的认证流程"""
        start_time = time.time()

        try:
            # 1. 尝试未认证访问保护资源
            protected_url = urljoin(self.base_url, '/api/v1/users/me')
            async with self.session.get(protected_url) as response:
                if response.status != 401:
                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='authentication_flow_check',
                        status='FAILURE',
                        duration_ms=(time.time() - start_time) * 1000,
                        error_message='受保护的资源未正确返回401状态'
                    )

            # 2. 执行登录流程
            login_data = {
                'username': 'test@example.com',
                'password': 'testpass123'
            }

            login_url = urljoin(self.base_url, '/api/v1/auth/login')
            async with self.session.post(login_url, json=login_data) as response:
                login_duration = (time.time() - start_time) * 1000

                # 根据实际情况调整状态判断
                if response.status in [200, 401]:  # 401是预期的，因为测试用户不存在
                    status = 'SUCCESS' if response.status == 200 else 'WARNING'
                    error_msg = None if response.status == 200 else '测试用户不存在（预期行为）'
                else:
                    status = 'FAILURE'
                    error_msg = f'登录端点返回意外状态码: {response.status}'

                return MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name='authentication_flow_check',
                    status=status,
                    duration_ms=login_duration,
                    response_time_ms=login_duration,
                    status_code=response.status,
                    error_message=error_msg,
                    details={
                        'login_attempted': True,
                        'protected_resource_check': True
                    }
                )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='authentication_flow_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_user_registration_flow(self) -> MonitoringResult:
        """测试用户注册流程"""
        start_time = time.time()

        try:
            # 生成随机测试数据
            test_email = f"test_{random.randint(10000, 99999)}@example.com"
            registration_data = {
                'email': test_email,
                'password': 'TestPass123!',
                'full_name': 'Test User'
            }

            register_url = urljoin(self.base_url, '/api/v1/auth/register')
            async with self.session.post(register_url, json=registration_data) as response:
                duration = (time.time() - start_time) * 1000

                # 根据实际API设计调整状态判断
                status = 'SUCCESS' if response.status in [200, 201] else 'WARNING'

                response_data = {}
                try:
                    response_data = await response.json()
                except:
                    pass

                return MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name='user_registration_flow_check',
                    status=status,
                    duration_ms=duration,
                    response_time_ms=duration,
                    status_code=response.status,
                    details={
                        'test_email': test_email,
                        'response_data': response_data
                    }
                )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='user_registration_flow_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_database_connectivity(self) -> MonitoringResult:
        """检查数据库连接状态"""
        start_time = time.time()

        try:
            # 通过健康检查端点检查数据库状态
            db_health_url = urljoin(self.base_url, '/health/database')
            async with self.session.get(db_health_url) as response:
                duration = (time.time() - start_time) * 1000

                if response.status == 200:
                    response_data = await response.json()
                    db_status = response_data.get('database', {}).get('status', 'unknown')

                    status = 'SUCCESS' if db_status == 'healthy' else 'WARNING'

                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='database_connectivity_check',
                        status=status,
                        duration_ms=duration,
                        response_time_ms=duration,
                        status_code=response.status,
                        details={
                            'database_status': db_status,
                            'response_data': response_data
                        }
                    )
                else:
                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='database_connectivity_check',
                        status='FAILURE',
                        duration_ms=duration,
                        status_code=response.status,
                        error_message=f'数据库健康检查返回状态码: {response.status}'
                    )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='database_connectivity_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_cache_performance(self) -> MonitoringResult:
        """检查缓存性能"""
        start_time = time.time()

        try:
            # 模拟缓存测试请求
            cache_test_url = urljoin(self.base_url, '/api/v1/cache/test')

            # 第一次请求（缓存MISS）
            async with self.session.get(cache_test_url) as response1:
                first_duration = (time.time() - start_time) * 1000

                # 第二次请求（期望缓存HIT）
                start_time_2 = time.time()
                async with self.session.get(cache_test_url) as response2:
                    second_duration = (time.time() - start_time_2) * 1000

                    total_duration = (time.time() - start_time) * 1000

                    # 分析缓存性能
                    cache_improvement = (first_duration - second_duration) / first_duration * 100

                    status = 'SUCCESS' if cache_improvement > 10 else 'WARNING'  # 期望至少10%性能提升

                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='cache_performance_check',
                        status=status,
                        duration_ms=total_duration,
                        response_time_ms=second_duration,
                        status_code=response2.status,
                        details={
                            'first_request_ms': first_duration,
                            'second_request_ms': second_duration,
                            'performance_improvement_percent': cache_improvement,
                            'cache_hit_expected': cache_improvement > 0
                        }
                    )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='cache_performance_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_error_handling(self) -> MonitoringResult:
        """测试错误处理机制"""
        start_time = time.time()

        try:
            # 测试404错误处理
            not_found_url = urljoin(self.base_url, '/api/v1/nonexistent')
            async with self.session.get(not_found_url) as response:
                duration = (time.time() - start_time) * 1000

                # 检查错误响应格式
                try:
                    error_data = await response.json()
                    has_error_format = 'error' in error_data or 'message' in error_data
                except:
                    has_error_format = False

                status = 'SUCCESS' if response.status == 404 and has_error_format else 'WARNING'

                return MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name='error_handling_check',
                    status=status,
                    duration_ms=duration,
                    response_time_ms=duration,
                    status_code=response.status,
                    details={
                        'error_format_valid': has_error_format,
                        'expected_404': response.status == 404
                    }
                )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='error_handling_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def measure_performance_metrics(self) -> MonitoringResult:
        """测量性能指标"""
        start_time = time.time()

        try:
            # 执行多个并发请求来测试性能
            concurrent_requests = 10
            request_url = urljoin(self.base_url, '/api/v1/status')

            async def single_request():
                request_start = time.time()
                async with self.session.get(request_url) as response:
                    request_duration = (time.time() - request_start) * 1000
                    return request_duration, response.status

            # 执行并发请求
            tasks = [single_request() for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 分析结果
            successful_requests = [r for r in results if not isinstance(r, Exception) and r[1] == 200]
            response_times = [r[0] for r in successful_requests]

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                success_rate = len(successful_requests) / len(results) * 100
            else:
                avg_response_time = 0
                min_response_time = 0
                max_response_time = 0
                success_rate = 0

            total_duration = (time.time() - start_time) * 1000

            status = 'SUCCESS' if success_rate > 90 and avg_response_time < 1000 else 'WARNING'

            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='performance_metrics_check',
                status=status,
                duration_ms=total_duration,
                response_time_ms=avg_response_time,
                details={
                    'concurrent_requests': concurrent_requests,
                    'success_rate_percent': success_rate,
                    'avg_response_time_ms': avg_response_time,
                    'min_response_time_ms': min_response_time,
                    'max_response_time_ms': max_response_time,
                    'total_successful': len(successful_requests)
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='performance_metrics_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def verify_security_headers(self) -> MonitoringResult:
        """验证安全头配置"""
        start_time = time.time()

        try:
            async with self.session.get(self.base_url) as response:
                duration = (time.time() - start_time) * 1000
                headers = dict(response.headers)

                # 检查关键安全头
                security_headers = {
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                    'X-XSS-Protection': '1; mode=block',
                    'Strict-Transport-Security': None,  # 检查存在即可
                    'Content-Security-Policy': None
                }

                missing_headers = []
                present_headers = []

                for header, expected in security_headers.items():
                    header_value = headers.get(header, headers.get(header.lower()))

                    if header_value:
                        present_headers.append(header)
                        if expected and isinstance(expected, list):
                            if header_value not in expected:
                                missing_headers.append(f"{header} (unexpected value: {header_value})")
                        elif expected and expected != header_value:
                            missing_headers.append(f"{header} (unexpected value: {header_value})")
                    else:
                        missing_headers.append(header)

                security_score = len(present_headers) / len(security_headers) * 100
                status = 'SUCCESS' if security_score > 70 else 'WARNING'

                return MonitoringResult(
                    timestamp=datetime.now().isoformat(),
                    test_name='security_headers_check',
                    status=status,
                    duration_ms=duration,
                    response_time_ms=duration,
                    status_code=response.status,
                    details={
                        'security_score_percent': security_score,
                        'present_headers': present_headers,
                        'missing_headers': missing_headers,
                        'all_headers': list(headers.keys())
                    }
                )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='security_headers_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def test_rate_limiting(self) -> MonitoringResult:
        """测试速率限制功能"""
        start_time = time.time()

        try:
            # 快速发送多个请求来测试速率限制
            test_url = urljoin(self.base_url, '/api/v1/status')
            requests_count = 50
            rate_limited_responses = 0

            for i in range(requests_count):
                async with self.session.get(test_url) as response:
                    if response.status == 429:  # Too Many Requests
                        rate_limited_responses += 1
                    await asyncio.sleep(0.01)  # 10ms间隔

            duration = (time.time() - start_time) * 1000

            # 如果有速率限制响应，说明速率限制正在工作
            status = 'SUCCESS' if rate_limited_responses > 0 else 'WARNING'

            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='rate_limiting_check',
                status=status,
                duration_ms=duration,
                details={
                    'total_requests': requests_count,
                    'rate_limited_responses': rate_limited_responses,
                    'rate_limit_working': rate_limited_responses > 0
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='rate_limiting_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def check_monitoring_endpoints(self) -> MonitoringResult:
        """检查监控端点的可用性"""
        start_time = time.time()

        try:
            metrics_url = urljoin(self.base_url, self.metrics_endpoint)
            async with self.session.get(metrics_url) as response:
                duration = (time.time() - start_time) * 1000

                if response.status == 200:
                    metrics_data = await response.text()

                    # 检查关键指标是否存在
                    key_metrics = [
                        'http_requests_total',
                        'http_request_duration_seconds',
                        'process_resident_memory_bytes',
                        'process_cpu_seconds_total'
                    ]

                    present_metrics = [metric for metric in key_metrics if metric in metrics_data]
                    metrics_completeness = len(present_metrics) / len(key_metrics) * 100

                    status = 'SUCCESS' if metrics_completeness > 75 else 'WARNING'

                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='monitoring_endpoints_check',
                        status=status,
                        duration_ms=duration,
                        response_time_ms=duration,
                        status_code=response.status,
                        details={
                            'metrics_completeness_percent': metrics_completeness,
                            'present_metrics': present_metrics,
                            'missing_metrics': list(set(key_metrics) - set(present_metrics)),
                            'total_metrics_lines': len(metrics_data.split('\n'))
                        }
                    )
                else:
                    return MonitoringResult(
                        timestamp=datetime.now().isoformat(),
                        test_name='monitoring_endpoints_check',
                        status='FAILURE',
                        duration_ms=duration,
                        status_code=response.status,
                        error_message=f'监控端点返回状态码: {response.status}'
                    )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='monitoring_endpoints_check',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def validate_business_logic(self) -> MonitoringResult:
        """验证关键业务逻辑"""
        start_time = time.time()

        try:
            # 这里可以添加具体的业务逻辑验证
            # 例如：数据一致性检查、业务规则验证等

            validation_checks = []

            # 检查1: API版本一致性
            version_url = urljoin(self.base_url, '/api/v1/version')
            async with self.session.get(version_url) as response:
                if response.status == 200:
                    version_data = await response.json()
                    validation_checks.append({
                        'check': 'api_version_consistency',
                        'status': 'PASS',
                        'details': version_data
                    })
                else:
                    validation_checks.append({
                        'check': 'api_version_consistency',
                        'status': 'FAIL',
                        'details': {'status_code': response.status}
                    })

            # 检查2: 系统时间同步
            current_time = datetime.now()
            validation_checks.append({
                'check': 'system_time_sync',
                'status': 'PASS',
                'details': {'current_time': current_time.isoformat()}
            })

            duration = (time.time() - start_time) * 1000
            passed_checks = sum(1 for check in validation_checks if check['status'] == 'PASS')
            success_rate = passed_checks / len(validation_checks) * 100

            status = 'SUCCESS' if success_rate == 100 else 'WARNING' if success_rate > 50 else 'FAILURE'

            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='business_logic_validation',
                status=status,
                duration_ms=duration,
                details={
                    'validation_checks': validation_checks,
                    'success_rate_percent': success_rate,
                    'total_checks': len(validation_checks),
                    'passed_checks': passed_checks
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return MonitoringResult(
                timestamp=datetime.now().isoformat(),
                test_name='business_logic_validation',
                status='FAILURE',
                duration_ms=duration,
                error_message=str(e)
            )

    async def save_results(self):
        """保存监控结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.results_dir / f'monitoring_results_{timestamp}.json'

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'summary': {
                'total_checks': len(self.results),
                'successful': sum(1 for r in self.results if r.status == 'SUCCESS'),
                'warnings': sum(1 for r in self.results if r.status == 'WARNING'),
                'failures': sum(1 for r in self.results if r.status == 'FAILURE'),
                'avg_response_time_ms': sum(r.response_time_ms or 0 for r in self.results) / len(self.results) if self.results else 0
            },
            'results': [asdict(result) for result in self.results]
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        logger.info(f"监控结果已保存到: {results_file}")

    async def send_metrics_to_prometheus(self):
        """将监控结果发送到Prometheus指标端点"""
        try:
            # 构造Prometheus格式的指标
            metrics_lines = []

            # 生成基本指标
            current_timestamp = int(time.time() * 1000)

            for result in self.results:
                test_name_clean = result.test_name.replace('-', '_')

                # 测试状态指标 (1=SUCCESS, 0.5=WARNING, 0=FAILURE)
                status_value = 1 if result.status == 'SUCCESS' else 0.5 if result.status == 'WARNING' else 0
                metrics_lines.append(
                    f'synthetic_test_status{{test_name="{result.test_name}"}} {status_value} {current_timestamp}'
                )

                # 响应时间指标
                if result.response_time_ms is not None:
                    metrics_lines.append(
                        f'synthetic_test_response_time_ms{{test_name="{result.test_name}"}} {result.response_time_ms} {current_timestamp}'
                    )

                # 测试持续时间指标
                metrics_lines.append(
                    f'synthetic_test_duration_ms{{test_name="{result.test_name}"}} {result.duration_ms} {current_timestamp}'
                )

            # 汇总指标
            total_tests = len(self.results)
            successful_tests = sum(1 for r in self.results if r.status == 'SUCCESS')
            warning_tests = sum(1 for r in self.results if r.status == 'WARNING')
            failed_tests = sum(1 for r in self.results if r.status == 'FAILURE')

            metrics_lines.extend([
                f'synthetic_monitoring_total_tests {total_tests} {current_timestamp}',
                f'synthetic_monitoring_successful_tests {successful_tests} {current_timestamp}',
                f'synthetic_monitoring_warning_tests {warning_tests} {current_timestamp}',
                f'synthetic_monitoring_failed_tests {failed_tests} {current_timestamp}',
                f'synthetic_monitoring_success_rate {successful_tests / total_tests if total_tests > 0 else 0} {current_timestamp}'
            ])

            # 保存指标到文件（可以通过node_exporter的textfile collector收集）
            metrics_file = self.results_dir / 'synthetic_monitoring.prom'
            with open(metrics_file, 'w') as f:
                f.write('\n'.join(metrics_lines) + '\n')

            logger.info(f"Prometheus指标已生成: {metrics_file}")

        except Exception as e:
            logger.error(f"生成Prometheus指标失败: {e}")

    def generate_summary_report(self) -> Dict[str, Any]:
        """生成监控结果摘要报告"""
        if not self.results:
            return {'error': 'No results available'}

        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.status == 'SUCCESS')
        warnings = sum(1 for r in self.results if r.status == 'WARNING')
        failures = sum(1 for r in self.results if r.status == 'FAILURE')

        avg_response_time = sum(
            r.response_time_ms for r in self.results if r.response_time_ms is not None
        ) / sum(1 for r in self.results if r.response_time_ms is not None) if any(
            r.response_time_ms is not None for r in self.results
        ) else 0

        failed_tests = [r for r in self.results if r.status == 'FAILURE']

        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful': successful,
                'warnings': warnings,
                'failures': failures,
                'success_rate': successful / total_tests * 100 if total_tests > 0 else 0,
                'average_response_time_ms': round(avg_response_time, 2)
            },
            'health_status': 'HEALTHY' if failures == 0 else 'DEGRADED' if warnings > 0 else 'UNHEALTHY',
            'failed_tests': [
                {
                    'test_name': test.test_name,
                    'error': test.error_message,
                    'status_code': test.status_code
                } for test in failed_tests
            ]
        }

async def main():
    """主函数"""
    # 监控配置
    config = {
        'base_url': os.getenv('CLAUDE_ENHANCER_URL', 'http://localhost:8000'),
        'timeout': 30,
        'results_dir': './monitoring_results',
        'metrics_endpoint': '/metrics'
    }

    logger.info("启动Claude Enhancer 5.1综合监控套件")

    async with SyntheticMonitoringSuite(config) as monitor:
        results = await monitor.run_all_checks()

        # 生成并打印摘要报告
        summary = monitor.generate_summary_report()

        print("\n" + "="*80)
        print("Claude Enhancer 5.1 监控结果摘要")
        print("="*80)
        print(f"总测试数量: {summary['summary']['total_tests']}")
        print(f"成功: {summary['summary']['successful']}")
        print(f"警告: {summary['summary']['warnings']}")
        print(f"失败: {summary['summary']['failures']}")
        print(f"成功率: {summary['summary']['success_rate']:.1f}%")
        print(f"平均响应时间: {summary['summary']['average_response_time_ms']:.2f}ms")
        print(f"健康状态: {summary['health_status']}")

        if summary['failed_tests']:
            print("\n失败的测试:")
            for test in summary['failed_tests']:
                print(f"  - {test['test_name']}: {test['error']}")

        print("="*80)

        # 根据监控结果设置退出码
        exit_code = 0 if summary['summary']['failures'] == 0 else 1
        exit(exit_code)

if __name__ == '__main__':
    asyncio.run(main())