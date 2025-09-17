#!/usr/bin/env python3
"""
Perfect21 性能质量门
===================

检查性能指标，防止性能回归
"""

import asyncio
import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics

from .models import GateResult, GateStatus, GateSeverity


class PerformanceGate:
    """性能质量门"""

    def __init__(self, project_root: str, config):
        self.project_root = Path(project_root)
        self.config = config

    async def check(self, context: str = "commit") -> GateResult:
        """执行性能检查"""
        start_time = datetime.now()
        violations = []
        details = {}
        suggestions = []

        try:
            # 1. API性能测试
            if context in ["merge", "release", "performance_test", "all"]:
                api_performance = await self._test_api_performance()
                details["api_performance"] = api_performance

                # 检查响应时间
                p95_response_time = api_performance.get("p95_response_time", 0)
                if p95_response_time > self.config.max_response_time_p95:
                    violations.append({
                        "type": "slow_api_response",
                        "message": f"API响应时间过慢: P95 {p95_response_time:.1f}ms > {self.config.max_response_time_p95}ms",
                        "severity": "high",
                        "current": p95_response_time,
                        "threshold": self.config.max_response_time_p95
                    })
                    suggestions.append("优化API响应时间")

                # 检查吞吐量
                throughput = api_performance.get("throughput", 0)
                if throughput < self.config.min_throughput:
                    violations.append({
                        "type": "low_throughput",
                        "message": f"API吞吐量过低: {throughput:.1f} req/s < {self.config.min_throughput} req/s",
                        "severity": "medium",
                        "current": throughput,
                        "threshold": self.config.min_throughput
                    })
                    suggestions.append("提高API处理能力")

            # 2. 内存使用检查
            memory_usage = await self._check_memory_usage()
            details["memory_usage"] = memory_usage

            max_memory_mb = memory_usage.get("max_memory_mb", 0)
            if max_memory_mb > self.config.max_memory_usage:
                violations.append({
                    "type": "high_memory_usage",
                    "message": f"内存使用过高: {max_memory_mb:.1f}MB > {self.config.max_memory_usage}MB",
                    "severity": "medium",
                    "current": max_memory_mb,
                    "threshold": self.config.max_memory_usage
                })
                suggestions.append("优化内存使用")

            # 3. 启动时间检查
            startup_performance = await self._check_startup_performance()
            details["startup_performance"] = startup_performance

            startup_time = startup_performance.get("startup_time", 0)
            if startup_time > 10:  # 启动时间超过10秒
                violations.append({
                    "type": "slow_startup",
                    "message": f"启动时间过长: {startup_time:.1f}s",
                    "severity": "low",
                    "current": startup_time
                })
                suggestions.append("优化启动时间")

            # 4. 代码性能分析
            code_performance = await self._analyze_code_performance()
            details["code_performance"] = code_performance

            if code_performance.get("slow_functions"):
                violations.append({
                    "type": "slow_functions",
                    "message": f"发现 {len(code_performance['slow_functions'])} 个慢函数",
                    "severity": "medium",
                    "functions": code_performance["slow_functions"]
                })
                suggestions.append("优化耗时函数")

            # 5. 数据库性能检查（如果有）
            if context in ["merge", "release", "all"]:
                db_performance = await self._check_database_performance()
                details["database_performance"] = db_performance

                slow_queries = db_performance.get("slow_queries", [])
                if slow_queries:
                    violations.append({
                        "type": "slow_database_queries",
                        "message": f"发现 {len(slow_queries)} 个慢查询",
                        "severity": "medium",
                        "queries": slow_queries
                    })
                    suggestions.append("优化数据库查询")

            # 计算性能分数
            score = self._calculate_performance_score(details, violations)

            # 确定状态
            high_severity_count = len([v for v in violations if v.get("severity") == "high"])
            medium_severity_count = len([v for v in violations if v.get("severity") == "medium"])

            if high_severity_count > 0:
                status = GateStatus.FAILED
                severity = GateSeverity.HIGH
                message = f"性能问题严重: {high_severity_count} 个高危问题"
            elif medium_severity_count > 3:
                status = GateStatus.FAILED
                severity = GateSeverity.MEDIUM
                message = f"性能问题较多: {medium_severity_count} 个中等问题"
            elif violations:
                status = GateStatus.WARNING
                severity = GateSeverity.LOW
                message = f"发现 {len(violations)} 个性能问题"
            else:
                status = GateStatus.PASSED
                severity = GateSeverity.INFO
                message = "性能检查通过"

            # 添加性能优化建议
            if violations:
                suggestions.extend([
                    "使用性能分析工具定位瓶颈",
                    "考虑启用缓存机制",
                    "优化数据库查询",
                    "评估异步处理方案"
                ])

            execution_time = (datetime.now() - start_time).total_seconds()

            return GateResult(
                gate_name="performance",
                status=status,
                severity=severity,
                score=score,
                message=message,
                details=details,
                violations=violations,
                suggestions=list(set(suggestions)),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name="performance",
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"性能检查失败: {str(e)}",
                details={"error": str(e)},
                violations=[{"type": "check_error", "message": str(e), "severity": "high"}],
                suggestions=["检查性能测试环境"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    async def _test_api_performance(self) -> Dict[str, Any]:
        """测试API性能"""
        try:
            # 检查是否有API服务器运行
            api_running = await self._check_api_server()
            if not api_running:
                return {
                    "api_available": False,
                    "message": "API服务器未运行",
                    "p95_response_time": 0,
                    "throughput": 0
                }

            # 简单的API性能测试
            response_times = []
            successful_requests = 0
            total_requests = 10

            start_time = time.time()

            for i in range(total_requests):
                try:
                    request_start = time.time()

                    # 这里可以添加实际的API调用
                    # 目前使用简单的健康检查
                    result = subprocess.run([
                        'curl', '-s', '-w', '%{time_total}',
                        'http://localhost:8000/health'
                    ], capture_output=True, text=True, timeout=5)

                    if result.returncode == 0:
                        response_time = float(result.stdout.strip()) * 1000  # 转换为毫秒
                        response_times.append(response_time)
                        successful_requests += 1

                except Exception:
                    continue

            total_time = time.time() - start_time

            if response_times:
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # P95
                throughput = successful_requests / total_time
            else:
                p95_response_time = 0
                throughput = 0

            return {
                "api_available": True,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "p95_response_time": p95_response_time,
                "average_response_time": statistics.mean(response_times) if response_times else 0,
                "throughput": throughput,
                "success_rate": (successful_requests / total_requests) * 100
            }

        except Exception as e:
            return {
                "api_available": False,
                "error": str(e),
                "p95_response_time": 0,
                "throughput": 0
            }

    async def _check_api_server(self) -> bool:
        """检查API服务器是否运行"""
        try:
            result = subprocess.run([
                'curl', '-s', '--connect-timeout', '2',
                'http://localhost:8000/health'
            ], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用情况"""
        try:
            # 运行一个简单的Perfect21操作来测试内存使用
            process = subprocess.Popen([
                'python3', '-c',
                'import sys; sys.path.append("."); '
                'from main.perfect21 import Perfect21CLI; '
                'cli = Perfect21CLI(); '
                'print("Memory test completed")'
            ], cwd=str(self.project_root))

            # 监控进程内存使用
            memory_usage = []
            max_memory = 0

            for _ in range(10):  # 监控1秒
                try:
                    ps_process = psutil.Process(process.pid)
                    memory_info = ps_process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB

                    memory_usage.append(memory_mb)
                    max_memory = max(max_memory, memory_mb)

                    await asyncio.sleep(0.1)
                except psutil.NoSuchProcess:
                    break

            process.wait(timeout=10)

            return {
                "max_memory_mb": max_memory,
                "average_memory_mb": statistics.mean(memory_usage) if memory_usage else 0,
                "memory_samples": len(memory_usage)
            }

        except Exception as e:
            return {
                "max_memory_mb": 0,
                "error": str(e)
            }

    async def _check_startup_performance(self) -> Dict[str, Any]:
        """检查启动性能"""
        try:
            start_time = time.time()

            # 测试Perfect21启动时间
            result = subprocess.run([
                'python3', '-c',
                'import sys; sys.path.append("."); '
                'from main.perfect21 import Perfect21CLI; '
                'cli = Perfect21CLI(); '
                'print("Startup completed")'
            ], cwd=str(self.project_root), capture_output=True, text=True, timeout=30)

            startup_time = time.time() - start_time

            return {
                "startup_time": startup_time,
                "startup_successful": result.returncode == 0,
                "startup_output": result.stdout if result.returncode == 0 else result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "startup_time": 30,
                "startup_successful": False,
                "error": "启动超时"
            }
        except Exception as e:
            return {
                "startup_time": 0,
                "startup_successful": False,
                "error": str(e)
            }

    async def _analyze_code_performance(self) -> Dict[str, Any]:
        """分析代码性能"""
        try:
            # 查找可能的性能问题模式
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents', 'tests'])]

            slow_functions = []
            performance_issues = []

            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    file_rel_path = str(py_file.relative_to(self.project_root))

                    # 检查潜在的性能问题
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        line_lower = line.lower().strip()

                        # 检查嵌套循环
                        if 'for ' in line and content.count('for ', content.find(line)) >= 2:
                            performance_issues.append({
                                "type": "nested_loops",
                                "file": file_rel_path,
                                "line": i,
                                "message": "潜在的嵌套循环性能问题"
                            })

                        # 检查大文件读取
                        if '.read()' in line and 'open(' in line:
                            performance_issues.append({
                                "type": "large_file_read",
                                "file": file_rel_path,
                                "line": i,
                                "message": "可能的大文件读取操作"
                            })

                        # 检查数据库查询在循环中
                        if any(db_op in line_lower for db_op in ['select', 'insert', 'update', 'delete']) and \
                           any(loop_word in content[:content.find(line)].split('\n')[-5:] for loop_word in ['for ', 'while ']):
                            performance_issues.append({
                                "type": "query_in_loop",
                                "file": file_rel_path,
                                "line": i,
                                "message": "循环中的数据库查询"
                            })

                        # 检查同步操作
                        if any(sync_op in line_lower for sync_op in ['time.sleep', 'requests.get', 'subprocess.run']):
                            performance_issues.append({
                                "type": "blocking_operation",
                                "file": file_rel_path,
                                "line": i,
                                "message": "潜在的阻塞操作"
                            })

                except Exception:
                    continue

            # 统计可能的慢函数（基于代码模式）
            if performance_issues:
                slow_functions = list(set([issue["file"] for issue in performance_issues]))

            return {
                "slow_functions": slow_functions,
                "performance_issues": performance_issues,
                "files_analyzed": len(python_files)
            }

        except Exception as e:
            return {
                "slow_functions": [],
                "performance_issues": [],
                "error": str(e)
            }

    async def _check_database_performance(self) -> Dict[str, Any]:
        """检查数据库性能"""
        try:
            # 这里可以添加实际的数据库性能检查
            # 目前返回模拟数据
            return {
                "slow_queries": [],
                "connection_pool_usage": 0,
                "query_cache_hit_rate": 100,
                "average_query_time": 0
            }

        except Exception as e:
            return {
                "slow_queries": [],
                "error": str(e)
            }

    def _calculate_performance_score(self, details: Dict[str, Any], violations: List[Dict[str, Any]]) -> float:
        """计算性能分数"""
        base_score = 100.0

        # API性能扣分
        api_perf = details.get("api_performance", {})
        p95_time = api_perf.get("p95_response_time", 0)
        if p95_time > self.config.max_response_time_p95:
            excess_ratio = p95_time / self.config.max_response_time_p95
            base_score -= min(excess_ratio * 30, 40)

        throughput = api_perf.get("throughput", 0)
        if throughput < self.config.min_throughput and throughput > 0:
            deficit_ratio = self.config.min_throughput / throughput
            base_score -= min(deficit_ratio * 20, 30)

        # 内存使用扣分
        memory_usage = details.get("memory_usage", {})
        max_memory = memory_usage.get("max_memory_mb", 0)
        if max_memory > self.config.max_memory_usage:
            excess_ratio = max_memory / self.config.max_memory_usage
            base_score -= min(excess_ratio * 20, 25)

        # 启动时间扣分
        startup_perf = details.get("startup_performance", {})
        startup_time = startup_perf.get("startup_time", 0)
        if startup_time > 5:  # 超过5秒
            base_score -= min((startup_time - 5) * 3, 15)

        # 代码性能问题扣分
        code_perf = details.get("code_performance", {})
        issues_count = len(code_perf.get("performance_issues", []))
        base_score -= min(issues_count * 2, 20)

        # 根据违规严重程度额外扣分
        for violation in violations:
            severity = violation.get("severity", "medium")
            if severity == "high":
                base_score -= 15
            elif severity == "medium":
                base_score -= 8
            else:
                base_score -= 3

        # 确保分数在0-100范围内
        return max(0.0, min(100.0, base_score))