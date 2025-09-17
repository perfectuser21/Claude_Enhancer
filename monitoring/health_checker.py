#!/usr/bin/env python3
"""
Health Checker - Perfect21 Health Check Service
完整的健康检查系统，支持深度健康检查和依赖监控
"""

import time
import threading
import asyncio
import psutil
import os
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import socket

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    duration_ms: float = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class HealthCheck:
    """健康检查基类"""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout
            )
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            return result
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                duration_ms=duration_ms
            )

    async def _perform_check(self) -> HealthCheckResult:
        """子类需要实现的检查逻辑"""
        raise NotImplementedError

class SystemHealthCheck(HealthCheck):
    """系统资源健康检查"""

    def __init__(self, cpu_threshold: float = 90.0, memory_threshold: float = 90.0):
        super().__init__("system_resources")
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    async def _perform_check(self) -> HealthCheckResult:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        # 负载均衡
        load_avg = os.getloadavg()

        details = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'load_average': {
                '1min': load_avg[0],
                '5min': load_avg[1],
                '15min': load_avg[2]
            },
            'memory_available_gb': memory.available / (1024**3),
            'disk_free_gb': disk.free / (1024**3)
        }

        # 判断健康状态
        if cpu_percent > self.cpu_threshold or memory_percent > self.memory_threshold:
            status = HealthStatus.UNHEALTHY
            message = f"High resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%"
        elif cpu_percent > self.cpu_threshold * 0.8 or memory_percent > self.memory_threshold * 0.8:
            status = HealthStatus.DEGRADED
            message = f"Elevated resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"System resources normal - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%"

        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            details=details
        )

class DatabaseHealthCheck(HealthCheck):
    """数据库健康检查"""

    def __init__(self, db_path: str = None):
        super().__init__("database")
        self.db_path = db_path or "data/perfect21.db"

    async def _perform_check(self) -> HealthCheckResult:
        try:
            import sqlite3

            # 检查数据库文件是否存在
            if not os.path.exists(self.db_path):
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="Database file does not exist",
                    details={'db_path': self.db_path}
                )

            # 测试数据库连接
            conn = sqlite3.connect(self.db_path, timeout=2.0)
            cursor = conn.cursor()

            # 执行简单查询
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # 检查数据库大小
            db_size = os.path.getsize(self.db_path)

            conn.close()

            details = {
                'db_path': self.db_path,
                'db_size_mb': db_size / (1024 * 1024),
                'connection_test': 'passed'
            }

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {e}",
                details={'error': str(e)}
            )

class GitHealthCheck(HealthCheck):
    """Git仓库健康检查"""

    def __init__(self, repo_path: str = "."):
        super().__init__("git_repository")
        self.repo_path = repo_path

    async def _perform_check(self) -> HealthCheckResult:
        try:
            # 检查是否是Git仓库
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="Not a git repository",
                    details={'repo_path': self.repo_path}
                )

            # 获取Git状态
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            # 获取当前分支
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            # 获取最后提交
            commit_result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%s|%an|%ad'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            # 解析状态
            modified_files = len([line for line in status_result.stdout.strip().split('\n') if line])
            current_branch = branch_result.stdout.strip()

            commit_info = {}
            if commit_result.stdout:
                parts = commit_result.stdout.split('|')
                if len(parts) >= 4:
                    commit_info = {
                        'hash': parts[0][:8],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    }

            details = {
                'repo_path': self.repo_path,
                'current_branch': current_branch,
                'modified_files': modified_files,
                'last_commit': commit_info
            }

            if modified_files > 50:
                status = HealthStatus.DEGRADED
                message = f"Many modified files ({modified_files}) in repository"
            else:
                status = HealthStatus.HEALTHY
                message = f"Git repository healthy on branch '{current_branch}'"

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )

        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Git command timed out"
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Git check failed: {e}",
                details={'error': str(e)}
            )

class ServiceHealthCheck(HealthCheck):
    """服务健康检查"""

    def __init__(self, name: str, host: str, port: int):
        super().__init__(f"service_{name}")
        self.host = host
        self.port = port
        self.service_name = name

    async def _perform_check(self) -> HealthCheckResult:
        try:
            # 测试TCP连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            start_time = time.time()
            result = sock.connect_ex((self.host, self.port))
            connection_time = (time.time() - start_time) * 1000

            sock.close()

            details = {
                'host': self.host,
                'port': self.port,
                'connection_time_ms': connection_time
            }

            if result == 0:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"Service {self.service_name} is reachable",
                    details=details
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Cannot connect to {self.service_name}",
                    details=details
                )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Service check failed: {e}",
                details={'error': str(e)}
            )

class Perfect21ComponentHealthCheck(HealthCheck):
    """Perfect21组件健康检查"""

    def __init__(self):
        super().__init__("perfect21_components")

    async def _perform_check(self) -> HealthCheckResult:
        try:
            # 检查核心目录
            core_path = "core/claude-code-unified-agents"
            features_path = "features"
            main_path = "main"

            components = {
                'core_agents': os.path.exists(core_path),
                'features': os.path.exists(features_path),
                'main_module': os.path.exists(main_path),
                'config': os.path.exists("config"),
                'logs': os.path.exists("logs")
            }

            # 检查重要文件
            important_files = {
                'claude_md': os.path.exists("CLAUDE.md"),
                'requirements': os.path.exists("requirements.txt"),
                'cli': os.path.exists("main/cli.py"),
                'perfect21_main': os.path.exists("main/perfect21.py")
            }

            # 检查功能模块
            feature_modules = {}
            if os.path.exists(features_path):
                for item in os.listdir(features_path):
                    module_path = os.path.join(features_path, item)
                    if os.path.isdir(module_path):
                        feature_modules[item] = True

            all_components_ok = all(components.values()) and all(important_files.values())

            details = {
                'components': components,
                'important_files': important_files,
                'feature_modules': feature_modules,
                'total_features': len(feature_modules)
            }

            if all_components_ok:
                status = HealthStatus.HEALTHY
                message = f"All Perfect21 components available ({len(feature_modules)} features)"
            else:
                missing_components = [k for k, v in components.items() if not v]
                missing_files = [k for k, v in important_files.items() if not v]
                status = HealthStatus.DEGRADED
                message = f"Missing components: {missing_components + missing_files}"

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Component check failed: {e}",
                details={'error': str(e)}
            )

class Perfect21HealthChecker:
    """Perfect21健康检查管理器"""

    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, HealthCheckResult] = {}
        self._setup_default_checks()

    def _setup_default_checks(self):
        """设置默认健康检查"""
        self.add_check(SystemHealthCheck())
        self.add_check(DatabaseHealthCheck())
        self.add_check(GitHealthCheck())
        self.add_check(Perfect21ComponentHealthCheck())

    def add_check(self, check: HealthCheck):
        """添加健康检查"""
        self.checks.append(check)

    def add_service_check(self, name: str, host: str, port: int):
        """添加服务检查"""
        self.add_check(ServiceHealthCheck(name, host, port))

    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        start_time = time.time()
        results = []

        # 并行执行所有检查
        tasks = [check.check() for check in self.checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        overall_status = HealthStatus.HEALTHY
        total_checks = len(self.checks)
        passed_checks = 0

        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                # 处理异常
                check_name = self.checks[i].name
                result = HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed with exception: {result}"
                )

            results.append(result.to_dict())
            self.last_results[result.name] = result

            # 更新整体状态
            if result.status == HealthStatus.HEALTHY:
                passed_checks += 1
            elif result.status == HealthStatus.DEGRADED:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            else:  # UNHEALTHY
                overall_status = HealthStatus.UNHEALTHY

        total_duration = time.time() - start_time

        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': total_duration,
            'summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': total_checks - passed_checks,
                'success_rate': (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            },
            'checks': results
        }

    async def run_check(self, check_name: str) -> Optional[Dict[str, Any]]:
        """运行单个健康检查"""
        for check in self.checks:
            if check.name == check_name:
                result = await check.check()
                self.last_results[result.name] = result
                return result.to_dict()
        return None

    def get_last_results(self) -> Dict[str, Any]:
        """获取最后的检查结果"""
        if not self.last_results:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': 'No health checks have been run yet',
                'checks': []
            }

        results = [result.to_dict() for result in self.last_results.values()]
        overall_status = HealthStatus.HEALTHY

        for result in self.last_results.values():
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif result.status == HealthStatus.DEGRADED:
                overall_status = HealthStatus.DEGRADED

        return {
            'status': overall_status.value,
            'timestamp': max(result.timestamp for result in self.last_results.values()).isoformat(),
            'checks': results
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        if not self.last_results:
            return {'status': 'unknown', 'message': 'No health data available'}

        status_counts = {}
        for result in self.last_results.values():
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        overall_status = HealthStatus.HEALTHY
        if status_counts.get('unhealthy', 0) > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts.get('degraded', 0) > 0:
            overall_status = HealthStatus.DEGRADED

        return {
            'status': overall_status.value,
            'total_checks': len(self.last_results),
            'status_breakdown': status_counts,
            'last_check': max(result.timestamp for result in self.last_results.values()).isoformat()
        }

# 全局健康检查器实例
health_checker = Perfect21HealthChecker()

# 便捷函数
async def run_health_checks() -> Dict[str, Any]:
    """运行所有健康检查"""
    return await health_checker.run_all_checks()

async def run_health_check(check_name: str) -> Optional[Dict[str, Any]]:
    """运行单个健康检查"""
    return await health_checker.run_check(check_name)

def get_health_status() -> Dict[str, Any]:
    """获取当前健康状态"""
    return health_checker.get_last_results()

def get_health_summary() -> Dict[str, Any]:
    """获取健康状态摘要"""
    return health_checker.get_health_summary()

def add_service_health_check(name: str, host: str, port: int):
    """添加服务健康检查"""
    health_checker.add_service_check(name, host, port)

class HealthCheckScheduler:
    """健康检查调度器"""

    def __init__(self, checker: Perfect21HealthChecker, interval: int = 60):
        self.checker = checker
        self.interval = interval
        self._running = False
        self._task = None

    def start(self):
        """启动定期健康检查"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        print(f"Health check scheduler started (interval: {self.interval}s)")

    def stop(self):
        """停止定期健康检查"""
        self._running = False
        if self._task:
            self._task.cancel()

    async def _check_loop(self):
        """检查循环"""
        while self._running:
            try:
                await self.checker.run_all_checks()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health check loop: {e}")
                await asyncio.sleep(self.interval)

# 全局调度器
health_scheduler = HealthCheckScheduler(health_checker)

def start_health_monitoring(interval: int = 60):
    """启动健康监控"""
    health_scheduler.start()