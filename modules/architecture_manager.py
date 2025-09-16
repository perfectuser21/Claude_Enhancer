#!/usr/bin/env python3
"""
Perfect21 Architecture Manager
架构管理和统一协调系统
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 导入各个子系统
from .dependency_injection import container, setup_perfect21_services
from .plugin_system import plugin_manager, bootstrap_plugin_system
from .state_manager import global_state_manager, setup_perfect21_states
from .fault_tolerance import fault_manager, setup_perfect21_fault_tolerance
from .monitoring import monitoring_system, setup_perfect21_monitoring

logger = logging.getLogger("Perfect21.ArchitectureManager")

class SystemStatus(Enum):
    """系统状态"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class ArchitectureHealth:
    """架构健康状态"""
    overall_status: SystemStatus
    subsystem_status: Dict[str, str]
    performance_metrics: Dict[str, float]
    error_count: int
    uptime: float
    last_check: float

class ArchitectureManager:
    """架构管理器 - Perfect21系统的大脑"""

    def __init__(self):
        self.start_time = time.time()
        self.status = SystemStatus.INITIALIZING
        self.subsystems = {
            'dependency_injection': container,
            'plugin_system': plugin_manager,
            'state_manager': global_state_manager,
            'fault_tolerance': fault_manager,
            'monitoring': monitoring_system
        }
        self.initialization_order = [
            'dependency_injection',
            'state_manager',
            'fault_tolerance',
            'monitoring',
            'plugin_system'
        ]
        self._lock = threading.RLock()

    def initialize_perfect21(self) -> Dict[str, Any]:
        """初始化Perfect21架构"""
        logger.info("开始初始化Perfect21架构...")

        initialization_results = {}

        try:
            with self._lock:
                # 1. 设置依赖注入
                logger.info("1/5 设置依赖注入系统...")
                setup_perfect21_services()
                initialization_results['dependency_injection'] = {'success': True, 'message': '依赖注入设置完成'}

                # 2. 初始化状态管理
                logger.info("2/5 初始化状态管理系统...")
                setup_perfect21_states()
                initialization_results['state_manager'] = {'success': True, 'message': '状态管理系统初始化完成'}

                # 3. 设置故障容错
                logger.info("3/5 设置故障容错系统...")
                setup_perfect21_fault_tolerance()
                initialization_results['fault_tolerance'] = {'success': True, 'message': '故障容错系统设置完成'}

                # 4. 启动监控系统
                logger.info("4/5 启动监控系统...")
                setup_perfect21_monitoring()
                initialization_results['monitoring'] = {'success': True, 'message': '监控系统启动完成'}

                # 5. 启动插件系统
                logger.info("5/5 启动插件系统...")
                plugin_result = bootstrap_plugin_system()
                initialization_results['plugin_system'] = plugin_result

                # 更新系统状态
                self.status = SystemStatus.RUNNING
                global_state_manager.set_state(
                    'global', 'perfect21.architecture.status',
                    self.status.value, 'architecture_manager'
                )

                logger.info("Perfect21架构初始化完成!")

                return {
                    'success': True,
                    'status': self.status.value,
                    'initialization_time': time.time() - self.start_time,
                    'subsystem_results': initialization_results,
                    'message': 'Perfect21架构初始化成功'
                }

        except Exception as e:
            self.status = SystemStatus.ERROR
            logger.error(f"Perfect21架构初始化失败: {e}")

            # 报告故障
            fault_manager.report_fault(
                module_name='architecture_manager',
                fault_type='initialization_failure',
                fault_level='critical',
                error=e,
                context={'initialization_results': initialization_results}
            )

            return {
                'success': False,
                'error': str(e),
                'status': self.status.value,
                'partial_results': initialization_results,
                'message': 'Perfect21架构初始化失败'
            }

    def get_architecture_health(self) -> ArchitectureHealth:
        """获取架构健康状态"""
        with self._lock:
            # 收集各子系统状态
            subsystem_status = {}

            # 依赖注入状态
            try:
                dependency_issues = container.validate_dependencies()
                subsystem_status['dependency_injection'] = 'healthy' if not any(dependency_issues.values()) else 'degraded'
            except Exception:
                subsystem_status['dependency_injection'] = 'error'

            # 插件系统状态
            try:
                plugin_health = plugin_manager.get_system_health()
                subsystem_status['plugin_system'] = 'healthy' if plugin_health['active_plugins'] > 0 else 'warning'
            except Exception:
                subsystem_status['plugin_system'] = 'error'

            # 状态管理状态
            try:
                state_health = global_state_manager.get_health_status()
                subsystem_status['state_manager'] = 'healthy' if state_health['total_states'] > 0 else 'warning'
            except Exception:
                subsystem_status['state_manager'] = 'error'

            # 故障容错状态
            try:
                fault_health = fault_manager.get_system_health()
                subsystem_status['fault_tolerance'] = fault_health['overall_health']
            except Exception:
                subsystem_status['fault_tolerance'] = 'error'

            # 监控系统状态
            try:
                monitoring_data = monitoring_system.get_dashboard_data()
                subsystem_status['monitoring'] = 'healthy' if monitoring_data['monitoring_status']['active'] else 'warning'
            except Exception:
                subsystem_status['monitoring'] = 'error'

            # 计算整体状态
            error_count = sum(1 for status in subsystem_status.values() if status == 'error')
            degraded_count = sum(1 for status in subsystem_status.values() if status in ['degraded', 'warning'])

            if error_count > 0:
                overall_status = SystemStatus.ERROR
            elif degraded_count > 2:
                overall_status = SystemStatus.DEGRADED
            else:
                overall_status = SystemStatus.RUNNING

            # 性能指标
            try:
                system_metrics = monitoring_system.system_monitor.get_system_metrics()
                performance_metrics = {
                    'cpu_percent': system_metrics.get('cpu_percent', 0),
                    'memory_percent': system_metrics.get('memory_percent', 0),
                    'uptime': system_metrics.get('uptime', 0)
                }
            except Exception:
                performance_metrics = {}

            return ArchitectureHealth(
                overall_status=overall_status,
                subsystem_status=subsystem_status,
                performance_metrics=performance_metrics,
                error_count=error_count,
                uptime=time.time() - self.start_time,
                last_check=time.time()
            )

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """获取综合状态报告"""
        health = self.get_architecture_health()

        # 依赖关系分析
        dependency_analysis = container.validate_dependencies()

        # 插件状态
        plugin_health = plugin_manager.get_system_health()

        # 故障统计
        fault_stats = fault_manager.get_fault_statistics()

        # 监控数据
        monitoring_data = monitoring_system.get_dashboard_data()

        # Agent协作效果
        agent_effectiveness = self._analyze_agent_collaboration()

        return {
            'architecture_health': asdict(health),
            'dependency_analysis': dependency_analysis,
            'plugin_system': plugin_health,
            'fault_statistics': fault_stats,
            'monitoring_data': monitoring_data,
            'agent_collaboration': agent_effectiveness,
            'recommendations': self._generate_recommendations(health)
        }

    def _analyze_agent_collaboration(self) -> Dict[str, Any]:
        """分析Agent协作效果"""
        try:
            # 从监控数据获取Agent执行统计
            agent_metrics = monitoring_system.agent_metrics

            if not agent_metrics:
                return {
                    'total_agents': 0,
                    'active_agents': 0,
                    'collaboration_score': 0,
                    'message': '暂无Agent协作数据'
                }

            active_agents = len(agent_metrics)
            total_executions = sum(
                sum(ops.get('total_executions', 0) for ops in agent_ops.values())
                for agent_ops in agent_metrics.values()
            )
            successful_executions = sum(
                sum(ops.get('successful_executions', 0) for ops in agent_ops.values())
                for agent_ops in agent_metrics.values()
            )

            success_rate = successful_executions / total_executions if total_executions > 0 else 0
            collaboration_score = min(100, success_rate * 100)

            return {
                'total_agents': active_agents,
                'active_agents': active_agents,
                'total_executions': total_executions,
                'success_rate': success_rate,
                'collaboration_score': collaboration_score,
                'agent_details': dict(agent_metrics)
            }

        except Exception as e:
            logger.error(f"分析Agent协作效果失败: {e}")
            return {
                'error': str(e),
                'collaboration_score': 0
            }

    def _generate_recommendations(self, health: ArchitectureHealth) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 性能建议
        cpu_percent = health.performance_metrics.get('cpu_percent', 0)
        memory_percent = health.performance_metrics.get('memory_percent', 0)

        if cpu_percent > 80:
            recommendations.append("CPU使用率过高，建议优化计算密集型操作")

        if memory_percent > 85:
            recommendations.append("内存使用率过高，建议启用缓存清理或增加内存")

        # 子系统建议
        for subsystem, status in health.subsystem_status.items():
            if status == 'error':
                recommendations.append(f"子系统 {subsystem} 状态异常，需要立即检查")
            elif status in ['degraded', 'warning']:
                recommendations.append(f"子系统 {subsystem} 性能下降，建议优化")

        # 架构建议
        if health.error_count > 0:
            recommendations.append("系统存在错误，建议启用故障恢复机制")

        if not recommendations:
            recommendations.append("系统运行正常，建议定期监控和维护")

        return recommendations

    def shutdown_perfect21(self) -> Dict[str, Any]:
        """优雅关闭Perfect21"""
        logger.info("开始关闭Perfect21系统...")

        shutdown_results = {}

        try:
            with self._lock:
                self.status = SystemStatus.MAINTENANCE

                # 反向关闭子系统
                for subsystem_name in reversed(self.initialization_order):
                    try:
                        if subsystem_name == 'monitoring':
                            monitoring_system.stop_monitoring()
                        elif subsystem_name == 'fault_tolerance':
                            fault_manager.stop_health_monitoring()

                        shutdown_results[subsystem_name] = {'success': True}
                        logger.info(f"子系统 {subsystem_name} 关闭完成")

                    except Exception as e:
                        shutdown_results[subsystem_name] = {'success': False, 'error': str(e)}
                        logger.error(f"子系统 {subsystem_name} 关闭失败: {e}")

                logger.info("Perfect21系统关闭完成")

                return {
                    'success': True,
                    'shutdown_results': shutdown_results,
                    'uptime': time.time() - self.start_time,
                    'message': 'Perfect21系统优雅关闭完成'
                }

        except Exception as e:
            logger.error(f"Perfect21系统关闭失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'partial_results': shutdown_results,
                'message': 'Perfect21系统关闭失败'
            }

# 全局架构管理器
architecture_manager = ArchitectureManager()

def bootstrap_perfect21() -> Dict[str, Any]:
    """启动Perfect21完整架构"""
    return architecture_manager.initialize_perfect21()

def get_perfect21_status() -> Dict[str, Any]:
    """获取Perfect21状态"""
    return architecture_manager.get_comprehensive_status()

def shutdown_perfect21() -> Dict[str, Any]:
    """关闭Perfect21系统"""
    return architecture_manager.shutdown_perfect21()

if __name__ == "__main__":
    # 测试架构管理器
    print("启动Perfect21架构...")
    result = bootstrap_perfect21()
    print("启动结果:", result)

    time.sleep(2)

    print("\n获取系统状态...")
    status = get_perfect21_status()
    print("系统状态:", status['architecture_health'])

    print("\n关闭Perfect21...")
    shutdown_result = shutdown_perfect21()
    print("关闭结果:", shutdown_result)