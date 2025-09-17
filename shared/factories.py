#!/usr/bin/env python3
"""
Perfect21 工厂模式实现
实现开闭原则(OCP) - 对扩展开放，对修改关闭
"""

from typing import Dict, Type, Any, Optional
from abc import ABC, abstractmethod

from .interfaces import (
    IExecutorFactory, IWorkflowFactory, IParallelExecutor,
    ISequentialExecutor, IWorkflowTemplate, IWorkflowOrchestrator,
    ILogger, IConfigManager, IEventBus, ICacheManager
)
from .base_classes import BaseParallelExecutor, BaseSequentialExecutor
from .core_components import WorkflowOrchestrator
from .dependency_injection import Injectable, ServiceLocator


# ================ 工作流模板实现 ================

class WorkflowTemplate(IWorkflowTemplate):
    """基础工作流模板"""

    def __init__(self, name: str, stages: list, metadata: dict = None):
        self.name = name
        self.stages = stages
        self.metadata = metadata or {}

    def get_template_name(self) -> str:
        return self.name

    def get_stages(self) -> list:
        return self.stages

    def validate_template(self) -> bool:
        """验证模板有效性"""
        if not self.name or not self.stages:
            return False

        # 检查每个阶段的必需字段
        for stage in self.stages:
            if not isinstance(stage, dict) or 'name' not in stage:
                return False

        return True


class PremiumQualityWorkflowTemplate(WorkflowTemplate):
    """高质量工作流模板"""

    def __init__(self):
        stages = [
            {
                'name': 'deep_understanding',
                'description': '深度理解阶段',
                'agents': ['project-manager', 'business-analyst', 'technical-writer'],
                'execution_mode': 'parallel',
                'timeout': 300,
                'sync_point': {
                    'type': 'consensus_check',
                    'conditions': ['requirement_clarity', 'business_alignment']
                }
            },
            {
                'name': 'architecture_design',
                'description': '架构设计阶段',
                'agents': ['api-designer', 'backend-architect', 'database-specialist'],
                'execution_mode': 'sequential',
                'timeout': 600,
                'sync_point': {
                    'type': 'design_review',
                    'conditions': ['architecture_consistency', 'security_review']
                }
            },
            {
                'name': 'parallel_implementation',
                'description': '并行实现阶段',
                'agents': ['backend-architect', 'frontend-specialist', 'test-engineer'],
                'execution_mode': 'parallel',
                'timeout': 900,
                'sync_point': {
                    'type': 'integration_check',
                    'conditions': ['api_consistency', 'test_coverage']
                }
            },
            {
                'name': 'comprehensive_testing',
                'description': '全面测试阶段',
                'agents': ['test-engineer', 'security-auditor', 'performance-engineer'],
                'execution_mode': 'parallel',
                'timeout': 600,
                'sync_point': {
                    'type': 'quality_gate',
                    'conditions': ['test_pass_rate', 'security_scan', 'performance_benchmark']
                }
            },
            {
                'name': 'deployment_preparation',
                'description': '部署准备阶段',
                'agents': ['deployment-manager', 'devops-engineer', 'monitoring-specialist'],
                'execution_mode': 'sequential',
                'timeout': 300,
                'sync_point': {
                    'type': 'deployment_readiness',
                    'conditions': ['deployment_config', 'monitoring_setup']
                }
            }
        ]

        super().__init__(
            name='premium_quality_workflow',
            stages=stages,
            metadata={
                'quality_focus': True,
                'estimated_duration': 2700,  # 45分钟
                'complexity': 'high',
                'recommended_for': ['production_features', 'critical_systems']
            }
        )


class RapidDevelopmentWorkflowTemplate(WorkflowTemplate):
    """快速开发工作流模板"""

    def __init__(self):
        stages = [
            {
                'name': 'requirement_analysis',
                'description': '需求分析',
                'agents': ['business-analyst'],
                'execution_mode': 'sequential',
                'timeout': 180,
                'sync_point': {
                    'type': 'requirement_check',
                    'conditions': ['requirement_clarity']
                }
            },
            {
                'name': 'rapid_implementation',
                'description': '快速实现',
                'agents': ['backend-architect', 'frontend-specialist'],
                'execution_mode': 'parallel',
                'timeout': 600,
                'sync_point': {
                    'type': 'basic_integration',
                    'conditions': ['basic_functionality']
                }
            },
            {
                'name': 'basic_testing',
                'description': '基础测试',
                'agents': ['test-engineer'],
                'execution_mode': 'sequential',
                'timeout': 300,
                'sync_point': {
                    'type': 'basic_quality',
                    'conditions': ['core_functionality_test']
                }
            }
        ]

        super().__init__(
            name='rapid_development_workflow',
            stages=stages,
            metadata={
                'speed_focus': True,
                'estimated_duration': 1080,  # 18分钟
                'complexity': 'low',
                'recommended_for': ['prototypes', 'simple_features', 'bug_fixes']
            }
        )


# ================ 执行器实现 ================

class ClaudeCodeParallelExecutor(BaseParallelExecutor):
    """Claude Code并行执行器"""

    async def _execute_task(self, task, context):
        """执行Claude Code agent任务"""
        # 这里集成真实的Claude Code agent调用
        self.logger.info(f"执行Claude Code Agent: {task.agent_name}")

        # 模拟agent执行
        import asyncio
        await asyncio.sleep(1)  # 模拟执行时间

        return {
            'agent': task.agent_name,
            'task': task.task_description,
            'result': f"Agent {task.agent_name} 执行完成",
            'execution_type': 'parallel'
        }


class ClaudeCodeSequentialExecutor(BaseSequentialExecutor):
    """Claude Code顺序执行器"""

    async def _execute_task(self, task, context):
        """执行Claude Code agent任务"""
        self.logger.info(f"执行Claude Code Agent: {task.agent_name}")

        # 模拟agent执行
        import asyncio
        await asyncio.sleep(1)

        return {
            'agent': task.agent_name,
            'task': task.task_description,
            'result': f"Agent {task.agent_name} 执行完成",
            'execution_type': 'sequential'
        }


# ================ 工厂实现 ================

@Injectable(name='executor_factory', singleton=True)
class ExecutorFactory(IExecutorFactory):
    """执行器工厂"""

    def __init__(self, logger: ILogger, config: IConfigManager):
        self.logger = logger
        self.config = config

    def create_parallel_executor(self) -> IParallelExecutor:
        """创建并行执行器"""
        executor = ClaudeCodeParallelExecutor(self.logger, self.config)
        max_workers = self.config.get('execution.max_workers', 10)
        executor.set_max_workers(max_workers)

        self.logger.info(f"创建并行执行器，最大工作线程: {max_workers}")
        return executor

    def create_sequential_executor(self) -> ISequentialExecutor:
        """创建顺序执行器"""
        executor = ClaudeCodeSequentialExecutor(self.logger, self.config)
        self.logger.info("创建顺序执行器")
        return executor


@Injectable(name='workflow_factory', singleton=True)
class WorkflowFactory(IWorkflowFactory):
    """工作流工厂"""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self._template_registry: Dict[str, Type[IWorkflowTemplate]] = {
            'premium_quality': PremiumQualityWorkflowTemplate,
            'rapid_development': RapidDevelopmentWorkflowTemplate
        }

    def create_workflow_template(self, template_type: str) -> IWorkflowTemplate:
        """创建工作流模板"""
        if template_type not in self._template_registry:
            available = ', '.join(self._template_registry.keys())
            raise ValueError(f"未知的工作流模板类型: {template_type}. 可用类型: {available}")

        template_class = self._template_registry[template_type]
        template = template_class()

        self.logger.info(f"创建工作流模板: {template_type}")
        return template

    def create_workflow_orchestrator(self) -> IWorkflowOrchestrator:
        """创建工作流编排器"""
        # 使用依赖注入获取依赖
        logger = ServiceLocator.get('logger')
        event_bus = ServiceLocator.get('event_bus')
        cache_manager = ServiceLocator.get('cache_manager')

        orchestrator = WorkflowOrchestrator(logger, event_bus, cache_manager)
        self.logger.info("创建工作流编排器")
        return orchestrator

    def register_template(self, template_type: str, template_class: Type[IWorkflowTemplate]) -> None:
        """注册新的工作流模板类型"""
        self._template_registry[template_type] = template_class
        self.logger.info(f"注册工作流模板: {template_type}")

    def list_available_templates(self) -> list:
        """列出可用的工作流模板"""
        return list(self._template_registry.keys())


# ================ 统一工厂管理器 ================

@Injectable(name='factory_manager', singleton=True)
class FactoryManager:
    """工厂管理器 - 统一管理所有工厂"""

    def __init__(self, executor_factory: IExecutorFactory, workflow_factory: IWorkflowFactory):
        self.executor_factory = executor_factory
        self.workflow_factory = workflow_factory

    def create_execution_context(self, request: str, project_path: str, config: dict) -> Any:
        """创建执行上下文"""
        from .interfaces import ExecutionContext
        import time

        return ExecutionContext(
            task_id=f"task_{int(time.time())}",
            user_request=request,
            project_path=project_path,
            config=config,
            metadata={'created_at': time.time()}
        )

    def create_workflow_execution_pipeline(self, template_type: str) -> tuple:
        """创建完整的工作流执行管道"""
        # 创建模板
        template = self.workflow_factory.create_workflow_template(template_type)

        # 创建编排器
        orchestrator = self.workflow_factory.create_workflow_orchestrator()

        # 根据模板特点选择执行器
        if template_type == 'premium_quality':
            parallel_executor = self.executor_factory.create_parallel_executor()
            sequential_executor = self.executor_factory.create_sequential_executor()
            return template, orchestrator, parallel_executor, sequential_executor
        else:
            # 对于快速开发，优先使用并行执行器
            executor = self.executor_factory.create_parallel_executor()
            return template, orchestrator, executor, None

    def get_recommended_workflow(self, complexity: str, priority: str) -> str:
        """根据复杂度和优先级推荐工作流"""
        if complexity.lower() in ['high', 'complex'] or priority.lower() in ['critical', 'production']:
            return 'premium_quality'
        else:
            return 'rapid_development'


# ================ 插件化扩展支持 ================

class PluginRegistry:
    """插件注册表 - 支持动态扩展"""

    def __init__(self):
        self._plugins: Dict[str, Any] = {}

    def register_plugin(self, name: str, plugin: Any) -> None:
        """注册插件"""
        self._plugins[name] = plugin

    def get_plugin(self, name: str) -> Optional[Any]:
        """获取插件"""
        return self._plugins.get(name)

    def list_plugins(self) -> list:
        """列出所有插件"""
        return list(self._plugins.keys())


# 全局插件注册表
plugin_registry = PluginRegistry()