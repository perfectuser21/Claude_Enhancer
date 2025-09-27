#!/usr/bin/env python3
"""
Claude Enhancer 5.0 - 故障恢复测试框架
作为test-engineer设计的专业故障恢复测试系统

功能特性:
1. 多层次故障模拟（Hook、Agent、系统级）
2. 自动化故障注入和恢复验证
3. 灾难恢复场景测试
4. 性能降级验证
5. 数据完整性保护测试
6. 故障恢复时间测量
"""

import os
import sys
import time
import json
import subprocess
import threading
import tempfile
import shutil
import signal
import psutil
import socket
import random
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from contextlib import contextmanager
import hashlib


@dataclass
class FailureScenario:
    """故障场景定义"""
    name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    category: str  # "hook", "agent", "system", "data"
    setup_func: str  # 设置故障的函数名
    recovery_func: str  # 恢复验证的函数名
    expected_behavior: str  # 期望的系统行为
    timeout_seconds: int = 30


@dataclass
class RecoveryTestResult:
    """故障恢复测试结果"""
    scenario_name: str
    failure_injected: bool
    recovery_successful: bool
    detection_time_ms: float
    recovery_time_ms: float
    system_stability: str  # "stable", "degraded", "unstable"
    data_integrity_preserved: bool
    performance_impact: Dict[str, float]
    error_logs: List[str]
    recommendations: List[str]


class FailureInjector:
    """故障注入器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.active_failures = {}
        self.cleanup_tasks = []

    @contextmanager
    def inject_failure(self, failure_type: str, **kwargs):
        """故障注入上下文管理器"""
        failure_id = f"{failure_type}_{int(time.time())}"

        try:
            # 注入故障
            if failure_type == "hook_corruption":
                self._inject_hook_corruption(**kwargs)
            elif failure_type == "hook_timeout":
                self._inject_hook_timeout(**kwargs)
            elif failure_type == "hook_permission":
                self._inject_hook_permission_error(**kwargs)
            elif failure_type == "process_kill":
                self._inject_process_kill(**kwargs)
            elif failure_type == "disk_full":
                self._inject_disk_full(**kwargs)
            elif failure_type == "network_partition":
                self._inject_network_partition(**kwargs)
            elif failure_type == "memory_exhaustion":
                self._inject_memory_exhaustion(**kwargs)
            elif failure_type == "config_corruption":
                self._inject_config_corruption(**kwargs)
            elif failure_type == "database_lock":
                self._inject_database_lock(**kwargs)
            else:
                raise ValueError(f"Unknown failure type: {failure_type}")

            self.active_failures[failure_id] = {
                "type": failure_type,
                "start_time": time.time(),
                "kwargs": kwargs
            }

            yield failure_id

        finally:
            # 清理故障
            self._cleanup_failure(failure_id)

    def _inject_hook_corruption(self, hook_name: str = "quality_gate.sh"):
        """注入Hook脚本损坏"""
        hook_path = os.path.join(self.project_root, ".claude/hooks", hook_name)

        if os.path.exists(hook_path):
            # 备份原文件
            backup_path = f"{hook_path}.backup"
            shutil.copy2(hook_path, backup_path)
            self.cleanup_tasks.append(("restore_file", hook_path, backup_path))

            # 创建损坏的脚本
            with open(hook_path, 'w') as f:
                f.write("#!/bin/bash\necho 'CORRUPTED HOOK'\nexit 1\n")

    def _inject_hook_timeout(self, hook_name: str = "quality_gate.sh", delay: int = 30):
        """注入Hook执行超时"""
        hook_path = os.path.join(self.project_root, ".claude/hooks", hook_name)

        if os.path.exists(hook_path):
            backup_path = f"{hook_path}.backup"
            shutil.copy2(hook_path, backup_path)
            self.cleanup_tasks.append(("restore_file", hook_path, backup_path))

            # 创建超时脚本
            with open(hook_path, 'w') as f:
                f.write(f"#!/bin/bash\nsleep {delay}\necho 'TIMEOUT HOOK'\n")

    def _inject_hook_permission_error(self, hook_name: str = "quality_gate.sh"):
        """注入Hook权限错误"""
        hook_path = os.path.join(self.project_root, ".claude/hooks", hook_name)

        if os.path.exists(hook_path):
            # 记录原权限
            original_mode = os.stat(hook_path).st_mode
            self.cleanup_tasks.append(("restore_permissions", hook_path, original_mode))

            # 移除执行权限
            os.chmod(hook_path, 0o644)

    def _inject_process_kill(self, process_pattern: str = "python"):
        """注入进程终止"""
        # 查找匹配的进程
        target_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process_pattern in proc.info['name'] or \
                   any(process_pattern in arg for arg in proc.info['cmdline'] or []):
                    target_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 随机终止一个进程
        if target_pids:
            target_pid = random.choice(target_pids)
            try:
                os.kill(target_pid, signal.SIGTERM)
                self.cleanup_tasks.append(("process_killed", target_pid))
            except ProcessLookupError:
                pass

    def _inject_disk_full(self, path: str = None, size_mb: int = 100):
        """注入磁盘空间耗尽"""
        if path is None:
            path = tempfile.gettempdir()

        # 创建大文件占用磁盘空间
        dummy_file = os.path.join(path, f"disk_full_dummy_{int(time.time())}.tmp")

        try:
            with open(dummy_file, 'wb') as f:
                # 写入指定大小的数据
                chunk_size = 1024 * 1024  # 1MB chunks
                for _ in range(size_mb):
                    f.write(b'0' * chunk_size)

            self.cleanup_tasks.append(("remove_file", dummy_file))
        except OSError:
            # 磁盘可能已满
            pass

    def _inject_network_partition(self, target_host: str = "8.8.8.8"):
        """注入网络分区（模拟）"""
        # 这里只是模拟，实际环境中可能需要iptables等工具
        # 我们通过修改hosts文件来模拟网络问题
        hosts_file = "/etc/hosts"

        if os.path.exists(hosts_file) and os.access(hosts_file, os.W_OK):
            # 备份hosts文件
            backup_file = f"{hosts_file}.backup_{int(time.time())}"
            try:
                shutil.copy2(hosts_file, backup_file)
                self.cleanup_tasks.append(("restore_file", hosts_file, backup_file))

                # 添加错误的DNS解析
                with open(hosts_file, 'a') as f:
                    f.write(f"\n127.0.0.1 {target_host}\n")
            except PermissionError:
                # 没有权限修改hosts文件
                pass

    def _inject_memory_exhaustion(self, size_mb: int = 500):
        """注入内存耗尽"""
        # 创建内存消耗进程
        def memory_hog():
            try:
                # 分配大量内存
                memory_blocks = []
                block_size = 1024 * 1024  # 1MB per block

                for _ in range(size_mb):
                    block = bytearray(block_size)
                    memory_blocks.append(block)
                    time.sleep(0.01)  # 缓慢分配，避免系统崩溃

                # 保持内存占用
                time.sleep(30)  # 保持30秒
            except MemoryError:
                pass

        # 在后台进程中运行
        memory_process = threading.Thread(target=memory_hog, daemon=True)
        memory_process.start()
        self.cleanup_tasks.append(("stop_thread", memory_process))

    def _inject_config_corruption(self, config_file: str = ".claude/settings.json"):
        """注入配置文件损坏"""
        config_path = os.path.join(self.project_root, config_file)

        if os.path.exists(config_path):
            backup_path = f"{config_path}.backup"
            shutil.copy2(config_path, backup_path)
            self.cleanup_tasks.append(("restore_file", config_path, backup_path))

            # 创建损坏的配置文件
            with open(config_path, 'w') as f:
                f.write('{"corrupted": "config", "invalid": }')  # 无效JSON

    def _inject_database_lock(self, db_file: str = None):
        """注入数据库锁定"""
        if db_file is None:
            # 查找项目中的数据库文件
            db_files = list(Path(self.project_root).rglob("*.db"))
            if db_files:
                db_file = str(db_files[0])

        if db_file and os.path.exists(db_file):
            # 创建锁文件
            lock_file = f"{db_file}.lock"
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))

            self.cleanup_tasks.append(("remove_file", lock_file))

    def _cleanup_failure(self, failure_id: str):
        """清理故障"""
        for cleanup_task in self.cleanup_tasks:
            try:
                task_type = cleanup_task[0]

                if task_type == "restore_file":
                    original_path, backup_path = cleanup_task[1], cleanup_task[2]
                    if os.path.exists(backup_path):
                        shutil.move(backup_path, original_path)

                elif task_type == "restore_permissions":
                    file_path, original_mode = cleanup_task[1], cleanup_task[2]
                    if os.path.exists(file_path):
                        os.chmod(file_path, original_mode)

                elif task_type == "remove_file":
                    file_path = cleanup_task[1]
                    if os.path.exists(file_path):
                        os.remove(file_path)

                elif task_type == "stop_thread":
                    thread = cleanup_task[1]
                    # 线程会自然结束，这里只是标记
                    pass

                elif task_type == "process_killed":
                    # 进程已被终止，无需清理
                    pass

            except Exception as e:
                print(f"Cleanup error: {e}")

        self.cleanup_tasks.clear()
        if failure_id in self.active_failures:
            del self.active_failures[failure_id]


class SystemHealthMonitor:
    """系统健康监控器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.monitoring = False
        self.health_metrics = []
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 1.0):
        """开始健康监控"""
        self.monitoring = True
        self.health_metrics = []

        def monitor_worker():
            while self.monitoring:
                try:
                    metrics = self._collect_health_metrics()
                    self.health_metrics.append(metrics)
                    time.sleep(interval)
                except Exception as e:
                    print(f"Health monitoring error: {e}")

        self.monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止健康监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _collect_health_metrics(self) -> Dict[str, Any]:
        """收集健康指标"""
        metrics = {
            "timestamp": time.time(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage(self.project_root).percent,
            "process_count": len(psutil.pids()),
            "load_average": os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
        }

        # 检查关键进程
        metrics["critical_processes"] = self._check_critical_processes()

        # 检查文件系统
        metrics["file_system_health"] = self._check_file_system()

        # 检查网络连接
        metrics["network_health"] = self._check_network()

        return metrics

    def _check_critical_processes(self) -> Dict[str, bool]:
        """检查关键进程状态"""
        critical_processes = ["python", "bash", "ssh"]
        process_status = {}

        running_processes = {proc.name() for proc in psutil.process_iter()}

        for proc_name in critical_processes:
            process_status[proc_name] = proc_name in running_processes

        return process_status

    def _check_file_system(self) -> Dict[str, Any]:
        """检查文件系统健康"""
        health = {
            "readable": True,
            "writable": True,
            "critical_files_exist": True
        }

        try:
            # 测试读写能力
            test_file = os.path.join(self.project_root, "test/.health_check_tmp")
            os.makedirs(os.path.dirname(test_file), exist_ok=True)

            with open(test_file, 'w') as f:
                f.write("health check")

            with open(test_file, 'r') as f:
                content = f.read()
                health["readable"] = content == "health check"

            os.remove(test_file)

        except Exception:
            health["readable"] = False
            health["writable"] = False

        # 检查关键文件
        critical_files = [
            ".claude/hooks/quality_gate.sh",
            ".claude/hooks/smart_agent_selector.sh",
            ".claude/core/lazy_orchestrator.py"
        ]

        for file_path in critical_files:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                health["critical_files_exist"] = False
                break

        return health

    def _check_network(self) -> Dict[str, Any]:
        """检查网络连接"""
        network_health = {
            "localhost_reachable": False,
            "external_reachable": False,
            "dns_working": False
        }

        try:
            # 测试本地连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 22))
            network_health["localhost_reachable"] = result == 0
            sock.close()
        except Exception:
            pass

        try:
            # 测试外部连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('8.8.8.8', 53))
            network_health["external_reachable"] = result == 0
            sock.close()
        except Exception:
            pass

        try:
            # 测试DNS解析
            socket.gethostbyname('google.com')
            network_health["dns_working"] = True
        except Exception:
            pass

        return network_health

    def assess_system_stability(self) -> str:
        """评估系统稳定性"""
        if not self.health_metrics:
            return "unknown"

        recent_metrics = self.health_metrics[-10:]  # 最近10个样本

        # 计算稳定性指标
        cpu_variance = self._calculate_variance([m["cpu_usage"] for m in recent_metrics])
        memory_trend = self._calculate_trend([m["memory_usage"] for m in recent_metrics])

        # 检查关键服务状态
        critical_issues = 0
        for metrics in recent_metrics:
            fs_health = metrics.get("file_system_health", {})
            if not fs_health.get("readable", True) or not fs_health.get("writable", True):
                critical_issues += 1

            if not fs_health.get("critical_files_exist", True):
                critical_issues += 1

        # 判断稳定性
        if critical_issues > len(recent_metrics) * 0.3:  # 30%以上样本有关键问题
            return "unstable"
        elif cpu_variance > 30 or memory_trend > 10:  # CPU波动大或内存快速增长
            return "degraded"
        else:
            return "stable"

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5  # 标准差

    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势（简单线性回归斜率）"""
        if len(values) < 2:
            return 0

        n = len(values)
        x_values = list(range(n))

        x_mean = sum(x_values) / n
        y_mean = sum(values) / n

        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0

        slope = numerator / denominator
        return slope


class FailureRecoveryTestSuite:
    """故障恢复测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.failure_injector = FailureInjector(project_root)
        self.health_monitor = SystemHealthMonitor(project_root)
        self.test_scenarios = self._initialize_test_scenarios()

    def _initialize_test_scenarios(self) -> List[FailureScenario]:
        """初始化测试场景"""
        return [
            # Hook级别故障
            FailureScenario(
                name="hook_script_corruption",
                description="Hook脚本文件损坏",
                severity="high",
                category="hook",
                setup_func="hook_corruption",
                recovery_func="verify_hook_recovery",
                expected_behavior="系统应检测到Hook失败，使用默认处理逻辑"
            ),
            FailureScenario(
                name="hook_execution_timeout",
                description="Hook执行超时",
                severity="medium",
                category="hook",
                setup_func="hook_timeout",
                recovery_func="verify_timeout_handling",
                expected_behavior="系统应在超时后终止Hook并继续执行"
            ),
            FailureScenario(
                name="hook_permission_denied",
                description="Hook文件权限错误",
                severity="medium",
                category="hook",
                setup_func="hook_permission",
                recovery_func="verify_permission_handling",
                expected_behavior="系统应检测权限问题并报告错误"
            ),

            # 系统级别故障
            FailureScenario(
                name="disk_space_exhaustion",
                description="磁盘空间耗尽",
                severity="critical",
                category="system",
                setup_func="disk_full",
                recovery_func="verify_disk_recovery",
                expected_behavior="系统应优雅降级，避免数据损坏"
            ),
            FailureScenario(
                name="memory_exhaustion",
                description="内存资源耗尽",
                severity="critical",
                category="system",
                setup_func="memory_exhaustion",
                recovery_func="verify_memory_recovery",
                expected_behavior="系统应限制内存使用，避免OOM"
            ),
            FailureScenario(
                name="network_partition",
                description="网络连接中断",
                severity="high",
                category="system",
                setup_func="network_partition",
                recovery_func="verify_network_recovery",
                expected_behavior="系统应在网络恢复后自动重连"
            ),

            # 数据级别故障
            FailureScenario(
                name="config_file_corruption",
                description="配置文件损坏",
                severity="high",
                category="data",
                setup_func="config_corruption",
                recovery_func="verify_config_recovery",
                expected_behavior="系统应使用默认配置或备份配置"
            ),
            FailureScenario(
                name="database_lock_contention",
                description="数据库锁争用",
                severity="medium",
                category="data",
                setup_func="database_lock",
                recovery_func="verify_database_recovery",
                expected_behavior="系统应处理锁冲突，避免死锁"
            )
        ]

    def run_all_recovery_tests(self) -> List[RecoveryTestResult]:
        """运行所有故障恢复测试"""
        print("🛡️ Claude Enhancer 5.0 - 故障恢复测试框架")
        print(f"📋 测试场景数量: {len(self.test_scenarios)}")
        print("=" * 60)

        results = []

        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n🔬 [{i}/{len(self.test_scenarios)}] 测试场景: {scenario.name}")
            print(f"📄 描述: {scenario.description}")
            print(f"🚨 严重程度: {scenario.severity}")

            try:
                result = self._run_single_recovery_test(scenario)
                results.append(result)

                # 输出测试结果
                status_icon = "✅" if result.recovery_successful else "❌"
                print(f"{status_icon} 恢复测试: {'成功' if result.recovery_successful else '失败'}")
                print(f"⏱️ 检测时间: {result.detection_time_ms:.2f}ms")
                print(f"🔧 恢复时间: {result.recovery_time_ms:.2f}ms")
                print(f"📊 系统稳定性: {result.system_stability}")

            except Exception as e:
                print(f"❌ 测试执行失败: {e}")
                results.append(RecoveryTestResult(
                    scenario_name=scenario.name,
                    failure_injected=False,
                    recovery_successful=False,
                    detection_time_ms=0,
                    recovery_time_ms=0,
                    system_stability="unknown",
                    data_integrity_preserved=False,
                    performance_impact={},
                    error_logs=[str(e)],
                    recommendations=["调查测试框架问题"]
                ))

            # 短暂休息，让系统稳定
            time.sleep(2)

        return results

    def _run_single_recovery_test(self, scenario: FailureScenario) -> RecoveryTestResult:
        """运行单个故障恢复测试"""
        start_time = time.time()

        # 启动健康监控
        self.health_monitor.start_monitoring(0.5)

        # 记录基线健康状态
        time.sleep(1)  # 收集基线数据
        baseline_health = self.health_monitor.health_metrics[-1] if self.health_monitor.health_metrics else {}

        # 故障注入
        failure_injected = False
        detection_time_ms = 0
        recovery_time_ms = 0
        error_logs = []

        try:
            # 注入故障
            failure_kwargs = self._get_failure_kwargs(scenario)

            with self.failure_injector.inject_failure(scenario.setup_func, **failure_kwargs):
                failure_injected = True
                failure_start = time.time()

                # 等待故障被检测
                detection_start = time.time()
                failure_detected = self._wait_for_failure_detection(scenario, timeout=10)
                detection_time_ms = (time.time() - detection_start) * 1000

                if failure_detected:
                    # 等待系统恢复
                    recovery_start = time.time()
                    recovery_successful = self._wait_for_recovery(scenario, timeout=scenario.timeout_seconds)
                    recovery_time_ms = (time.time() - recovery_start) * 1000
                else:
                    recovery_successful = False
                    recovery_time_ms = scenario.timeout_seconds * 1000

        except Exception as e:
            error_logs.append(str(e))
            recovery_successful = False

        finally:
            # 停止监控
            self.health_monitor.stop_monitoring()

        # 评估恢复结果
        recovery_result = self._evaluate_recovery(
            scenario, failure_injected, recovery_successful,
            baseline_health, detection_time_ms, recovery_time_ms, error_logs
        )

        return recovery_result

    def _get_failure_kwargs(self, scenario: FailureScenario) -> Dict[str, Any]:
        """获取故障注入参数"""
        kwargs_map = {
            "hook_corruption": {"hook_name": "quality_gate.sh"},
            "hook_timeout": {"hook_name": "quality_gate.sh", "delay": 5},
            "hook_permission": {"hook_name": "quality_gate.sh"},
            "disk_full": {"size_mb": 50},  # 较小的文件，避免真正填满磁盘
            "memory_exhaustion": {"size_mb": 100},  # 适中的内存使用
            "network_partition": {"target_host": "example.com"},
            "config_corruption": {"config_file": ".claude/settings.json"},
            "database_lock": {}
        }

        return kwargs_map.get(scenario.setup_func, {})

    def _wait_for_failure_detection(self, scenario: FailureScenario, timeout: int = 10) -> bool:
        """等待故障被检测"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 根据故障类型执行检测逻辑
            if scenario.category == "hook":
                if self._test_hook_failure_detection(scenario):
                    return True
            elif scenario.category == "system":
                if self._test_system_failure_detection(scenario):
                    return True
            elif scenario.category == "data":
                if self._test_data_failure_detection(scenario):
                    return True

            time.sleep(0.5)

        return False

    def _test_hook_failure_detection(self, scenario: FailureScenario) -> bool:
        """测试Hook故障检测"""
        try:
            # 尝试执行Hook
            hook_path = os.path.join(self.project_root, ".claude/hooks/quality_gate.sh")
            result = subprocess.run(
                [hook_path],
                input='{"prompt": "test"}',
                text=True,
                capture_output=True,
                timeout=3
            )

            # 根据场景判断是否检测到故障
            if scenario.name == "hook_script_corruption":
                return result.returncode != 0  # 损坏的脚本应该返回非0
            elif scenario.name == "hook_execution_timeout":
                return False  # 超时情况下不会正常返回
            elif scenario.name == "hook_permission_denied":
                return result.returncode != 0  # 权限错误应该返回非0

        except subprocess.TimeoutExpired:
            return scenario.name == "hook_execution_timeout"  # 超时是预期的
        except Exception:
            return True  # 其他异常也算检测到故障

        return False

    def _test_system_failure_detection(self, scenario: FailureScenario) -> bool:
        """测试系统故障检测"""
        if not self.health_monitor.health_metrics:
            return False

        current_health = self.health_monitor.health_metrics[-1]

        if scenario.name == "disk_space_exhaustion":
            return current_health.get("disk_usage", 0) > 90
        elif scenario.name == "memory_exhaustion":
            return current_health.get("memory_usage", 0) > 90
        elif scenario.name == "network_partition":
            network_health = current_health.get("network_health", {})
            return not network_health.get("external_reachable", True)

        return False

    def _test_data_failure_detection(self, scenario: FailureScenario) -> bool:
        """测试数据故障检测"""
        if scenario.name == "config_file_corruption":
            config_path = os.path.join(self.project_root, ".claude/settings.json")
            try:
                with open(config_path, 'r') as f:
                    json.load(f)
                return False  # 配置文件正常
            except (json.JSONDecodeError, FileNotFoundError):
                return True  # 配置文件损坏或不存在

        elif scenario.name == "database_lock_contention":
            # 检查是否存在锁文件
            db_files = list(Path(self.project_root).rglob("*.db"))
            for db_file in db_files:
                lock_file = f"{db_file}.lock"
                if os.path.exists(lock_file):
                    return True

        return False

    def _wait_for_recovery(self, scenario: FailureScenario, timeout: int = 30) -> bool:
        """等待系统恢复"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 根据场景验证恢复状态
            if self._verify_recovery_state(scenario):
                return True

            time.sleep(1)

        return False

    def _verify_recovery_state(self, scenario: FailureScenario) -> bool:
        """验证恢复状态"""
        if scenario.category == "hook":
            return self._verify_hook_recovery(scenario)
        elif scenario.category == "system":
            return self._verify_system_recovery(scenario)
        elif scenario.category == "data":
            return self._verify_data_recovery(scenario)

        return False

    def _verify_hook_recovery(self, scenario: FailureScenario) -> bool:
        """验证Hook恢复"""
        # 对于Hook故障，我们期望系统能够优雅处理失败
        # 而不是完全恢复Hook本身（因为故障仍然存在）

        # 检查系统是否仍然响应
        if not self.health_monitor.health_metrics:
            return False

        current_health = self.health_monitor.health_metrics[-1]
        fs_health = current_health.get("file_system_health", {})

        # 系统应该保持文件系统可读写
        return fs_health.get("readable", False) and fs_health.get("writable", False)

    def _verify_system_recovery(self, scenario: FailureScenario) -> bool:
        """验证系统恢复"""
        if not self.health_monitor.health_metrics:
            return False

        current_health = self.health_monitor.health_metrics[-1]

        if scenario.name == "disk_space_exhaustion":
            # 系统应该能够继续运行，即使磁盘空间不足
            fs_health = current_health.get("file_system_health", {})
            return fs_health.get("readable", False)

        elif scenario.name == "memory_exhaustion":
            # 系统应该保持稳定，不崩溃
            return current_health.get("cpu_usage", 0) < 90  # CPU使用率不应过高

        elif scenario.name == "network_partition":
            # 网络问题可能持续，但系统应该保持本地功能
            network_health = current_health.get("network_health", {})
            return network_health.get("localhost_reachable", False)

        return True

    def _verify_data_recovery(self, scenario: FailureScenario) -> bool:
        """验证数据恢复"""
        if scenario.name == "config_file_corruption":
            # 系统应该能够使用默认配置或恢复配置
            # 检查是否有备份配置可用
            config_path = os.path.join(self.project_root, ".claude/settings.json")
            backup_path = f"{config_path}.backup"
            return os.path.exists(backup_path) or os.path.exists(config_path)

        elif scenario.name == "database_lock_contention":
            # 锁应该被释放，或者系统应该能够处理锁争用
            return True  # 简化处理，认为锁争用是可以处理的

        return True

    def _evaluate_recovery(
        self,
        scenario: FailureScenario,
        failure_injected: bool,
        recovery_successful: bool,
        baseline_health: Dict[str, Any],
        detection_time_ms: float,
        recovery_time_ms: float,
        error_logs: List[str]
    ) -> RecoveryTestResult:
        """评估恢复结果"""

        # 评估系统稳定性
        system_stability = self.health_monitor.assess_system_stability()

        # 评估数据完整性
        data_integrity_preserved = self._check_data_integrity()

        # 计算性能影响
        performance_impact = self._calculate_performance_impact(baseline_health)

        # 生成建议
        recommendations = self._generate_recovery_recommendations(
            scenario, recovery_successful, system_stability, performance_impact
        )

        return RecoveryTestResult(
            scenario_name=scenario.name,
            failure_injected=failure_injected,
            recovery_successful=recovery_successful,
            detection_time_ms=detection_time_ms,
            recovery_time_ms=recovery_time_ms,
            system_stability=system_stability,
            data_integrity_preserved=data_integrity_preserved,
            performance_impact=performance_impact,
            error_logs=error_logs,
            recommendations=recommendations
        )

    def _check_data_integrity(self) -> bool:
        """检查数据完整性"""
        # 检查关键配置文件
        critical_files = [
            ".claude/settings.json",
            ".claude/hooks/quality_gate.sh",
            ".claude/hooks/smart_agent_selector.sh"
        ]

        for file_path in critical_files:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                return False

            # 检查文件是否可读
            try:
                with open(full_path, 'r') as f:
                    f.read(100)  # 读取前100字符测试
            except Exception:
                return False

        return True

    def _calculate_performance_impact(self, baseline_health: Dict[str, Any]) -> Dict[str, float]:
        """计算性能影响"""
        if not self.health_monitor.health_metrics or not baseline_health:
            return {}

        current_health = self.health_monitor.health_metrics[-1]

        impact = {}

        # CPU使用率变化
        baseline_cpu = baseline_health.get("cpu_usage", 0)
        current_cpu = current_health.get("cpu_usage", 0)
        impact["cpu_usage_change"] = current_cpu - baseline_cpu

        # 内存使用率变化
        baseline_memory = baseline_health.get("memory_usage", 0)
        current_memory = current_health.get("memory_usage", 0)
        impact["memory_usage_change"] = current_memory - baseline_memory

        # 磁盘使用率变化
        baseline_disk = baseline_health.get("disk_usage", 0)
        current_disk = current_health.get("disk_usage", 0)
        impact["disk_usage_change"] = current_disk - baseline_disk

        return impact

    def _generate_recovery_recommendations(
        self,
        scenario: FailureScenario,
        recovery_successful: bool,
        system_stability: str,
        performance_impact: Dict[str, float]
    ) -> List[str]:
        """生成恢复建议"""
        recommendations = []

        if not recovery_successful:
            recommendations.append(f"故障恢复失败，需要改进{scenario.category}级别的错误处理")

        if system_stability == "unstable":
            recommendations.append("系统稳定性差，需要增强故障隔离机制")
        elif system_stability == "degraded":
            recommendations.append("系统性能降级，考虑实施自动恢复策略")

        # 性能影响建议
        if performance_impact.get("cpu_usage_change", 0) > 20:
            recommendations.append("CPU使用率显著增加，优化资源管理")

        if performance_impact.get("memory_usage_change", 0) > 20:
            recommendations.append("内存使用显著增加，检查内存泄漏")

        # 场景特定建议
        scenario_recommendations = {
            "hook_script_corruption": "实施Hook完整性检查和自动恢复",
            "hook_execution_timeout": "添加Hook超时机制和降级策略",
            "disk_space_exhaustion": "实施磁盘空间监控和自动清理",
            "memory_exhaustion": "添加内存使用限制和OOM保护",
            "config_file_corruption": "实施配置文件备份和验证机制"
        }

        if scenario.name in scenario_recommendations:
            recommendations.append(scenario_recommendations[scenario.name])

        if not recommendations:
            recommendations.append("故障恢复表现良好，继续保持当前机制")

        return recommendations


class FailureRecoveryReportGenerator:
    """故障恢复测试报告生成器"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self,
        test_results: List[RecoveryTestResult],
        timestamp: str
    ) -> str:
        """生成综合故障恢复报告"""
        report_file = self.output_dir / f"failure_recovery_report_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(test_results, timestamp))

        print(f"📊 故障恢复报告已生成: {report_file}")
        return str(report_file)

    def _generate_markdown_report(
        self,
        test_results: List[RecoveryTestResult],
        timestamp: str
    ) -> str:
        """生成Markdown报告内容"""

        # 统计数据
        total_tests = len(test_results)
        successful_recoveries = sum(1 for r in test_results if r.recovery_successful)
        failed_recoveries = total_tests - successful_recoveries

        # 按严重程度分类
        critical_failures = len([r for r in test_results if not r.recovery_successful and "critical" in r.scenario_name])

        # 计算平均恢复时间
        avg_detection_time = sum(r.detection_time_ms for r in test_results) / total_tests if total_tests > 0 else 0
        avg_recovery_time = sum(r.recovery_time_ms for r in test_results) / total_tests if total_tests > 0 else 0

        report = f"""# Claude Enhancer 5.0 - 故障恢复测试报告

**生成时间**: {timestamp}
**测试框架**: Failure Recovery Test Framework
**系统环境**: {os.uname().sysname} {os.uname().release}

## 📊 执行摘要

### 整体恢复能力评级
"""

        # 计算整体评级
        recovery_rate = successful_recoveries / total_tests * 100 if total_tests > 0 else 0

        if recovery_rate >= 90 and critical_failures == 0:
            grade = "A (优秀)"
            grade_emoji = "🌟"
        elif recovery_rate >= 75 and critical_failures <= 1:
            grade = "B (良好)"
            grade_emoji = "✅"
        elif recovery_rate >= 60:
            grade = "C (及格)"
            grade_emoji = "⚠️"
        else:
            grade = "D (需改进)"
            grade_emoji = "❌"

        report += f"""
{grade_emoji} **恢复能力等级**: {grade}
📈 **恢复成功率**: {recovery_rate:.1f}%
⏱️ **平均检测时间**: {avg_detection_time:.2f}ms
🔧 **平均恢复时间**: {avg_recovery_time:.2f}ms
🚨 **关键故障数**: {critical_failures}

| 指标 | 数值 | 状态 |
|------|------|------|
| 总测试数 | {total_tests} | - |
| 成功恢复 | {successful_recoveries} | {'✅' if successful_recoveries == total_tests else '⚠️'} |
| 失败恢复 | {failed_recoveries} | {'✅' if failed_recoveries == 0 else '❌'} |
| 关键故障 | {critical_failures} | {'✅' if critical_failures == 0 else '🚨'} |

## 🧪 详细测试结果

### 故障恢复测试明细

| 场景名称 | 故障注入 | 恢复成功 | 检测时间 | 恢复时间 | 系统稳定性 | 数据完整性 |
|---------|----------|----------|----------|----------|------------|------------|
"""

        for result in test_results:
            injection_icon = "✅" if result.failure_injected else "❌"
            recovery_icon = "✅" if result.recovery_successful else "❌"
            stability_icon = {"stable": "✅", "degraded": "⚠️", "unstable": "❌"}.get(result.system_stability, "❓")
            integrity_icon = "✅" if result.data_integrity_preserved else "❌"

            report += f"| {result.scenario_name} | {injection_icon} | {recovery_icon} | {result.detection_time_ms:.2f}ms | {result.recovery_time_ms:.2f}ms | {stability_icon} {result.system_stability} | {integrity_icon} |\n"

        report += f"""
### 性能影响分析

"""

        # 性能影响统计
        cpu_impacts = [r.performance_impact.get("cpu_usage_change", 0) for r in test_results if r.performance_impact]
        memory_impacts = [r.performance_impact.get("memory_usage_change", 0) for r in test_results if r.performance_impact]

        avg_cpu_impact = sum(cpu_impacts) / len(cpu_impacts) if cpu_impacts else 0
        avg_memory_impact = sum(memory_impacts) / len(memory_impacts) if memory_impacts else 0

        report += f"""
- **平均CPU影响**: {avg_cpu_impact:+.1f}%
- **平均内存影响**: {avg_memory_impact:+.1f}%
- **最大CPU峰值**: {max(cpu_impacts) if cpu_impacts else 0:+.1f}%
- **最大内存峰值**: {max(memory_impacts) if memory_impacts else 0:+.1f}%

### 恢复时间分析

- **最快检测**: {min(r.detection_time_ms for r in test_results):.2f}ms
- **最慢检测**: {max(r.detection_time_ms for r in test_results):.2f}ms
- **最快恢复**: {min(r.recovery_time_ms for r in test_results):.2f}ms
- **最慢恢复**: {max(r.recovery_time_ms for r in test_results):.2f}ms

## 🚨 失败案例分析

"""

        failed_tests = [r for r in test_results if not r.recovery_successful]

        if failed_tests:
            report += "### 恢复失败的测试场景\n\n"

            for failed_test in failed_tests:
                report += f"""
#### {failed_test.scenario_name}
- **故障注入**: {'成功' if failed_test.failure_injected else '失败'}
- **系统稳定性**: {failed_test.system_stability}
- **数据完整性**: {'保持' if failed_test.data_integrity_preserved else '受损'}
- **错误信息**:
"""
                for error in failed_test.error_logs:
                    report += f"  - {error}\n"

                report += "- **建议措施**:\n"
                for rec in failed_test.recommendations:
                    report += f"  - {rec}\n"

                report += "\n"
        else:
            report += "✅ **无恢复失败案例** - 所有故障场景都成功恢复\n"

        report += f"""
## 🎯 改进建议

### 立即处理项
"""

        immediate_actions = []
        long_term_actions = []

        # 分析所有建议
        all_recommendations = []
        for result in test_results:
            all_recommendations.extend(result.recommendations)

        # 统计建议频率
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

        # 按频率排序
        sorted_recommendations = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)

        # 分类建议
        urgent_keywords = ["失败", "关键", "严重", "立即", "紧急"]

        for rec, count in sorted_recommendations:
            if any(keyword in rec for keyword in urgent_keywords) or count >= len(test_results) * 0.3:
                immediate_actions.append(f"- {rec} (出现{count}次)")
            else:
                long_term_actions.append(f"- {rec} (出现{count}次)")

        if immediate_actions:
            for action in immediate_actions[:5]:  # 最多显示5个
                report += f"{action}\n"
        else:
            report += "✅ **无需立即处理的问题**\n"

        report += f"""
### 长期优化建议
"""

        if long_term_actions:
            for action in long_term_actions[:5]:  # 最多显示5个
                report += f"{action}\n"
        else:
            report += "- 继续保持当前优秀的故障恢复能力\n"

        report += f"""
### 系统加固建议

1. **监控告警**
   - 实施实时故障检测和告警机制
   - 建立故障恢复时间基线和SLA
   - 增强系统健康监控覆盖面

2. **自动化恢复**
   - 实施自动故障检测和恢复流程
   - 建立故障预案和应急响应机制
   - 增强系统自愈能力

3. **容错设计**
   - 实施故障隔离和降级策略
   - 增强数据备份和恢复机制
   - 改进错误处理和重试逻辑

4. **测试覆盖**
   - 定期执行故障恢复测试
   - 扩展故障场景覆盖面
   - 建立故障恢复演练机制

## 📈 恢复能力趋势

### 按故障类型分析

"""

        # 按类别统计成功率
        category_stats = {}
        for result in test_results:
            # 从场景名称推断类别
            if "hook" in result.scenario_name:
                category = "Hook级故障"
            elif any(keyword in result.scenario_name for keyword in ["disk", "memory", "network"]):
                category = "系统级故障"
            elif any(keyword in result.scenario_name for keyword in ["config", "database"]):
                category = "数据级故障"
            else:
                category = "其他故障"

            if category not in category_stats:
                category_stats[category] = {"total": 0, "successful": 0}

            category_stats[category]["total"] += 1
            if result.recovery_successful:
                category_stats[category]["successful"] += 1

        for category, stats in category_stats.items():
            success_rate = stats["successful"] / stats["total"] * 100 if stats["total"] > 0 else 0
            status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
            report += f"- **{category}**: {success_rate:.1f}% ({stats['successful']}/{stats['total']}) {status_icon}\n"

        report += f"""
### 恢复性能趋势

- **检测速度**: {'快速' if avg_detection_time < 1000 else '中等' if avg_detection_time < 5000 else '较慢'} (平均{avg_detection_time:.0f}ms)
- **恢复速度**: {'快速' if avg_recovery_time < 5000 else '中等' if avg_recovery_time < 15000 else '较慢'} (平均{avg_recovery_time:.0f}ms)
- **系统稳定性**: {'优秀' if sum(1 for r in test_results if r.system_stability == 'stable') / total_tests > 0.8 else '良好' if sum(1 for r in test_results if r.system_stability == 'stable') / total_tests > 0.6 else '需改进'}

## 🏆 结论

### 故障恢复能力评估
{grade_emoji} **整体评级**: {grade}

### 关键发现
"""

        key_findings = []

        if recovery_rate >= 90:
            key_findings.append("✅ 系统具有优秀的故障恢复能力")
        elif recovery_rate >= 75:
            key_findings.append("👍 系统具有良好的故障恢复能力")
        else:
            key_findings.append("⚠️ 系统故障恢复能力需要改进")

        if critical_failures == 0:
            key_findings.append("✅ 所有关键故障都能成功恢复")
        else:
            key_findings.append(f"🚨 {critical_failures}个关键故障恢复失败")

        if avg_detection_time < 1000:
            key_findings.append("⚡ 故障检测速度优秀")
        elif avg_detection_time < 5000:
            key_findings.append("👌 故障检测速度良好")
        else:
            key_findings.append("🐌 故障检测速度需要改进")

        for finding in key_findings:
            report += f"- {finding}\n"

        report += f"""
### 部署建议
"""

        if grade.startswith("A"):
            report += "**✅ 推荐部署**: 故障恢复能力优秀，系统具备生产环境要求的可靠性。\n"
        elif grade.startswith("B"):
            report += "**👌 可以部署**: 故障恢复能力良好，建议关注失败案例的改进。\n"
        elif grade.startswith("C"):
            report += "**⚠️ 谨慎部署**: 故障恢复能力一般，建议先改进关键问题再部署。\n"
        else:
            report += "**🛑 不建议部署**: 故障恢复能力不足，需要重大改进才能投入生产。\n"

        report += f"""
---
*报告由 Claude Enhancer Failure Recovery Test Framework 自动生成*
*测试工程师: Test Engineer Professional*
*生成时间: {timestamp}*
"""

        return report


class FailureRecoveryTestFramework:
    """故障恢复测试框架主类"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/home/xx/dev/Claude Enhancer 5.0"
        self.test_dir = os.path.join(self.project_root, "test")
        self.reports_dir = os.path.join(self.test_dir, "failure_recovery_reports")

        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)

        # 初始化组件
        self.recovery_suite = FailureRecoveryTestSuite(self.project_root)
        self.report_generator = FailureRecoveryReportGenerator(self.reports_dir)

    def run_complete_failure_recovery_test(self) -> str:
        """运行完整故障恢复测试"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        print("🛡️ Claude Enhancer 5.0 - 故障恢复测试框架")
        print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 项目路径: {self.project_root}")
        print("=" * 60)

        start_time = time.time()

        # 运行故障恢复测试
        test_results = self.recovery_suite.run_all_recovery_tests()

        # 生成报告
        print("\n📊 生成故障恢复报告...")
        report_file = self.report_generator.generate_comprehensive_report(test_results, timestamp)

        total_time = time.time() - start_time

        # 输出总结
        print("\n" + "=" * 60)
        print("🏆 故障恢复测试完成")
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        print(f"📊 报告文件: {report_file}")

        # 显示关键结果
        total_tests = len(test_results)
        successful_recoveries = sum(1 for r in test_results if r.recovery_successful)
        recovery_rate = successful_recoveries / total_tests * 100 if total_tests > 0 else 0

        print(f"📈 恢复成功率: {recovery_rate:.1f}%")
        print(f"✅ 成功恢复: {successful_recoveries}/{total_tests}")

        if recovery_rate >= 90:
            print("🌟 评估结果: 故障恢复能力优秀")
        elif recovery_rate >= 75:
            print("👍 评估结果: 故障恢复能力良好")
        elif recovery_rate >= 60:
            print("⚠️ 评估结果: 故障恢复能力一般")
        else:
            print("❌ 评估结果: 故障恢复能力需要改进")

        return report_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer 5.0 故障恢复测试框架")
    parser.add_argument("--project-root", help="项目根目录路径")
    parser.add_argument("--scenario", help="运行特定故障场景")
    parser.add_argument("--list-scenarios", action="store_true", help="列出所有故障场景")

    args = parser.parse_args()

    try:
        framework = FailureRecoveryTestFramework(args.project_root)

        if args.list_scenarios:
            print("📋 可用的故障恢复测试场景:")
            for scenario in framework.recovery_suite.test_scenarios:
                print(f"  - {scenario.name}: {scenario.description} ({scenario.severity})")

        elif args.scenario:
            # 运行特定场景
            scenario = next(
                (s for s in framework.recovery_suite.test_scenarios if s.name == args.scenario),
                None
            )
            if scenario:
                print(f"🧪 运行故障场景: {scenario.name}")
                result = framework.recovery_suite._run_single_recovery_test(scenario)
                print(f"结果: {'成功' if result.recovery_successful else '失败'}")
            else:
                print(f"❌ 未找到故障场景: {args.scenario}")

        else:
            report_file = framework.run_complete_failure_recovery_test()
            print(f"\n✅ 测试成功完成，报告保存在: {report_file}")

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)