#!/usr/bin/env python3
"""
Perfect21 解耦核心系统
基于SOLID原则的高度解耦架构实现
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .interfaces import (
    IPerfect21Core, ExecutionContext, ExecutionResult,
    ILogger, IConfigManager, ITaskAnalyzer, IExecutorFactory,
    IWorkflowFactory, IDecisionRecorder, ILearningSystem,
    IEventBus, ICacheManager, EventTypes
)
from .dependency_injection import Injectable, ServiceLocator
from .base_classes import BaseLogger


@Injectable(name='perfect21_core', singleton=True)
class Perfect21Core(IPerfect21Core):
    """Perfect21解耦核心系统"""

    def __init__(self,
                 logger: ILogger,
                 config: IConfigManager,
                 task_analyzer: ITaskAnalyzer,
                 executor_factory: IExecutorFactory,
                 workflow_factory: IWorkflowFactory,
                 decision_recorder: IDecisionRecorder,
                 learning_system: ILearningSystem,
                 event_bus: IEventBus,
                 cache_manager: ICacheManager):

        # 依赖注入的组件
        self.logger = logger
        self.config = config
        self.task_analyzer = task_analyzer
        self.executor_factory = executor_factory
        self.workflow_factory = workflow_factory
        self.decision_recorder = decision_recorder
        self.learning_system = learning_system
        self.event_bus = event_bus
        self.cache_manager = cache_manager

        # 系统状态
        self.is_initialized = False
        self.active_executions = {}
        self.system_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'uptime_start': datetime.now()
        }

        # 注册事件监听器
        self._register_event_handlers()

    def initialize_services(self) -> None:
        """初始化服务"""
        try:
            self.logger.info("初始化Perfect21核心服务...")

            # 验证配置
            if not self.config.validate_config():
                raise Exception("配置验证失败")

            # 预热缓存
            self._warmup_cache()

            # 初始化学习系统
            self._initialize_learning_system()

            # 标记初始化完成
            self.is_initialized = True

            # 发布初始化完成事件
            self.event_bus.publish(EventTypes.SYSTEM_STARTED, {
                'timestamp': datetime.now().isoformat(),
                'version': self.config.get('perfect21.version'),
                'mode': self.config.get('perfect21.mode')
            })

            self.logger.info("Perfect21核心服务初始化完成")

        except Exception as e:
            self.logger.error("服务初始化失败", e)
            raise

    async def execute_request(self, request: str, context: ExecutionContext) -> ExecutionResult:
        """执行用户请求 - 主要业务逻辑入口"""
        execution_id = f"exec_{int(time.time())}"
        start_time = datetime.now()

        try:
            # 检查系统状态
            if not self.is_initialized:
                return ExecutionResult(
                    success=False,
                    error_message="系统未初始化"
                )

            self.logger.info(f"开始执行请求: {execution_id}")
            self.system_metrics['total_requests'] += 1

            # 发布请求开始事件
            self.event_bus.publish(EventTypes.TASK_STARTED, {
                'execution_id': execution_id,
                'request': request,
                'context': context.__dict__
            })

            # 第一步：任务分析
            self.logger.info("步骤1: 分析用户请求")
            analysis_result = await self._analyze_user_request(request, context)
            if not analysis_result['success']:
                return ExecutionResult(
                    success=False,
                    error_message=f"任务分析失败: {analysis_result['error']}"
                )

            tasks = analysis_result['tasks']
            execution_mode = analysis_result['execution_mode']

            # 记录分析决策
            self.decision_recorder.record_decision({
                'title': f'任务分析决策 - {execution_id}',
                'context': f'用户请求: {request}',
                'decision': f'分解为{len(tasks)}个子任务，执行模式: {execution_mode.value}',
                'alternatives': analysis_result.get('alternative_strategies', []),
                'metadata': {'execution_id': execution_id, 'request_type': 'user_request'}
            })

            # 第二步：选择执行策略
            self.logger.info("步骤2: 选择执行策略")
            strategy_result = await self._select_execution_strategy(tasks, execution_mode, context)
            if not strategy_result['success']:
                return ExecutionResult(
                    success=False,
                    error_message=f"策略选择失败: {strategy_result['error']}"
                )

            execution_strategy = strategy_result['strategy']
            workflow_template = strategy_result.get('workflow_template')

            # 第三步：执行任务
            self.logger.info(f"步骤3: 执行任务 (策略: {execution_strategy})")

            if workflow_template:
                # 使用工作流模式执行
                execution_result = await self._execute_with_workflow(
                    workflow_template, tasks, context, execution_id
                )
            else:
                # 使用直接执行模式
                execution_result = await self._execute_direct(
                    tasks, execution_mode, context, execution_id
                )

            # 第四步：学习和改进
            self.logger.info("步骤4: 学习和改进")
            await self._learn_from_execution(execution_result, request, context)

            # 更新系统指标
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            if execution_result.success:
                self.system_metrics['successful_requests'] += 1
            else:
                self.system_metrics['failed_requests'] += 1

            # 更新平均响应时间
            total_requests = self.system_metrics['total_requests']
            current_avg = self.system_metrics['average_response_time']
            self.system_metrics['average_response_time'] = (
                (current_avg * (total_requests - 1) + execution_time) / total_requests
            )

            # 发布完成事件
            self.event_bus.publish(
                EventTypes.TASK_COMPLETED if execution_result.success else EventTypes.TASK_FAILED,
                {
                    'execution_id': execution_id,
                    'success': execution_result.success,
                    'execution_time': execution_time,
                    'result_data': execution_result.data
                }
            )

            self.logger.info(f"请求执行完成: {execution_id}, 耗时: {execution_time:.2f}s")

            return ExecutionResult(
                success=execution_result.success,
                data={
                    'execution_id': execution_id,
                    'strategy': execution_strategy,
                    'tasks_executed': len(tasks),
                    'result': execution_result.data
                },
                error_message=execution_result.error_message,
                execution_time=execution_time,
                metadata={
                    'analysis_result': analysis_result,
                    'strategy_result': strategy_result
                }
            )

        except Exception as e:
            self.logger.error(f"请求执行失败: {execution_id}", e)
            self.system_metrics['failed_requests'] += 1

            # 发布错误事件
            self.event_bus.publish(EventTypes.SYSTEM_ERROR, {
                'execution_id': execution_id,
                'error': str(e),
                'request': request
            })

            return ExecutionResult(
                success=False,
                error_message=str(e),
                metadata={'execution_id': execution_id}
            )

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        uptime = (datetime.now() - self.system_metrics['uptime_start']).total_seconds()

        return {
            'system': {
                'initialized': self.is_initialized,
                'version': self.config.get('perfect21.version'),
                'mode': self.config.get('perfect21.mode'),
                'uptime_seconds': uptime
            },
            'metrics': {
                **self.system_metrics,
                'success_rate': (
                    self.system_metrics['successful_requests'] /
                    max(1, self.system_metrics['total_requests'])
                ) * 100
            },
            'services': {
                'logger': 'healthy',
                'config': 'healthy' if self.config.validate_config() else 'unhealthy',
                'task_analyzer': 'healthy',
                'executor_factory': 'healthy',
                'workflow_factory': 'healthy',
                'decision_recorder': 'healthy',
                'learning_system': 'healthy',
                'event_bus': 'healthy',
                'cache_manager': 'healthy'
            },
            'active_executions': len(self.active_executions),
            'cache_stats': self.cache_manager.get_stats() if hasattr(self.cache_manager, 'get_stats') else {},
            'learning_stats': self.learning_system.get_performance_summary() if hasattr(self.learning_system, 'get_performance_summary') else {}
        }

    def shutdown(self) -> None:
        """关闭系统"""
        try:
            self.logger.info("开始关闭Perfect21核心系统...")

            # 等待活跃执行完成
            if self.active_executions:
                self.logger.info(f"等待{len(self.active_executions)}个活跃执行完成...")
                # 这里可以实现优雅关闭逻辑

            # 清理缓存
            self.cache_manager.clear()

            # 发布关闭事件
            self.event_bus.publish('system.shutdown', {
                'timestamp': datetime.now().isoformat(),
                'final_metrics': self.system_metrics
            })

            self.is_initialized = False
            self.logger.info("Perfect21核心系统已关闭")

        except Exception as e:
            self.logger.error("系统关闭失败", e)

    # ================ 私有方法 ================

    async def _analyze_user_request(self, request: str, context: ExecutionContext) -> Dict[str, Any]:
        """分析用户请求"""
        try:
            # 检查缓存
            cache_key = f"analysis_{hash(request)}"
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                self.logger.debug("使用缓存的分析结果")
                return cached_result

            # 进行任务分析
            tasks = self.task_analyzer.analyze_task(request, context)
            execution_mode = self.task_analyzer.determine_execution_mode(tasks)
            dependencies = self.task_analyzer.calculate_dependencies(tasks)

            result = {
                'success': True,
                'tasks': tasks,
                'execution_mode': execution_mode,
                'dependencies': dependencies,
                'alternative_strategies': self._get_alternative_strategies(tasks, execution_mode)
            }

            # 缓存结果
            self.cache_manager.set(cache_key, result, ttl=3600)

            return result

        except Exception as e:
            self.logger.error("任务分析失败", e)
            return {
                'success': False,
                'error': str(e)
            }

    async def _select_execution_strategy(self, tasks, execution_mode, context) -> Dict[str, Any]:
        """选择执行策略"""
        try:
            # 分析任务复杂度
            complexity = self._analyze_task_complexity(tasks)

            # 获取学习系统建议
            recommendations = []
            for task in tasks:
                task_recommendations = self.learning_system.get_recommendations(task.agent_name)
                recommendations.extend(task_recommendations)

            # 决定是否使用工作流
            use_workflow = self._should_use_workflow(tasks, complexity, execution_mode)

            if use_workflow:
                # 选择工作流模板
                workflow_type = self._select_workflow_template(complexity, context)
                workflow_template = self.workflow_factory.create_workflow_template(workflow_type)

                return {
                    'success': True,
                    'strategy': 'workflow',
                    'workflow_template': workflow_template,
                    'complexity': complexity,
                    'recommendations': recommendations
                }
            else:
                return {
                    'success': True,
                    'strategy': 'direct',
                    'execution_mode': execution_mode,
                    'complexity': complexity,
                    'recommendations': recommendations
                }

        except Exception as e:
            self.logger.error("策略选择失败", e)
            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_with_workflow(self, workflow_template, tasks, context, execution_id) -> ExecutionResult:
        """使用工作流模式执行"""
        try:
            orchestrator = self.workflow_factory.create_workflow_orchestrator()

            # 将任务映射到工作流阶段
            # 这里需要根据具体的工作流模板来映射任务

            result = await orchestrator.execute_workflow(workflow_template, context)

            return ExecutionResult(
                success=result.success,
                data={
                    'execution_mode': 'workflow',
                    'workflow_result': result.data
                },
                error_message=result.error_message,
                metadata={'execution_id': execution_id}
            )

        except Exception as e:
            self.logger.error("工作流执行失败", e)
            return ExecutionResult(
                success=False,
                error_message=str(e),
                metadata={'execution_id': execution_id}
            )

    async def _execute_direct(self, tasks, execution_mode, context, execution_id) -> ExecutionResult:
        """直接执行模式"""
        try:
            if execution_mode.value == 'parallel':
                executor = self.executor_factory.create_parallel_executor()
                results = await executor.execute_parallel(tasks, context)
            else:
                executor = self.executor_factory.create_sequential_executor()
                results = await executor.execute_sequential(tasks, context)

            # 分析执行结果
            successful_results = [r for r in results if r.success]
            failed_results = [r for r in results if not r.success]

            return ExecutionResult(
                success=len(failed_results) == 0,
                data={
                    'execution_mode': execution_mode.value,
                    'successful_tasks': len(successful_results),
                    'failed_tasks': len(failed_results),
                    'results': [r.__dict__ for r in results]
                },
                error_message=f"{len(failed_results)} tasks failed" if failed_results else None,
                metadata={'execution_id': execution_id}
            )

        except Exception as e:
            self.logger.error("直接执行失败", e)
            return ExecutionResult(
                success=False,
                error_message=str(e),
                metadata={'execution_id': execution_id}
            )

    async def _learn_from_execution(self, execution_result, request, context) -> None:
        """从执行中学习"""
        try:
            # 提取学习数据
            feedback_data = {
                'request_type': self._classify_request_type(request),
                'success_rate': 1.0 if execution_result.success else 0.0,
                'execution_time': execution_result.execution_time,
                'complexity_score': self._calculate_complexity_score(request, execution_result)
            }

            # 让学习系统学习
            self.learning_system.learn_from_execution(execution_result, feedback_data)

            self.logger.debug("学习完成")

        except Exception as e:
            self.logger.error("学习过程失败", e)

    def _register_event_handlers(self) -> None:
        """注册事件处理器"""
        self.event_bus.subscribe(EventTypes.TASK_STARTED, self._handle_task_started)
        self.event_bus.subscribe(EventTypes.TASK_COMPLETED, self._handle_task_completed)
        self.event_bus.subscribe(EventTypes.TASK_FAILED, self._handle_task_failed)

    def _handle_task_started(self, data: Dict[str, Any]) -> None:
        """处理任务开始事件"""
        execution_id = data.get('execution_id')
        if execution_id:
            self.active_executions[execution_id] = {
                'start_time': datetime.now(),
                'status': 'running'
            }

    def _handle_task_completed(self, data: Dict[str, Any]) -> None:
        """处理任务完成事件"""
        execution_id = data.get('execution_id')
        if execution_id in self.active_executions:
            self.active_executions[execution_id]['status'] = 'completed'
            self.active_executions[execution_id]['end_time'] = datetime.now()

    def _handle_task_failed(self, data: Dict[str, Any]) -> None:
        """处理任务失败事件"""
        execution_id = data.get('execution_id')
        if execution_id in self.active_executions:
            self.active_executions[execution_id]['status'] = 'failed'
            self.active_executions[execution_id]['end_time'] = datetime.now()

    def _warmup_cache(self) -> None:
        """预热缓存"""
        # 可以预加载一些常用的配置或数据
        self.cache_manager.set('system_config', self.config.get('perfect21'), ttl=7200)

    def _initialize_learning_system(self) -> None:
        """初始化学习系统"""
        # 可以加载历史学习数据
        pass

    def _get_alternative_strategies(self, tasks, execution_mode) -> list:
        """获取替代策略"""
        alternatives = []

        if execution_mode.value == 'parallel':
            alternatives.append('sequential_for_safety')
        elif execution_mode.value == 'sequential':
            alternatives.append('parallel_for_speed')

        if len(tasks) > 3:
            alternatives.append('workflow_for_complexity')

        return alternatives

    def _analyze_task_complexity(self, tasks) -> str:
        """分析任务复杂度"""
        if len(tasks) <= 2:
            return 'low'
        elif len(tasks) <= 5:
            return 'medium'
        else:
            return 'high'

    def _should_use_workflow(self, tasks, complexity, execution_mode) -> bool:
        """判断是否使用工作流"""
        return (
            complexity in ['medium', 'high'] or
            len(tasks) > 4 or
            any(task.dependencies for task in tasks)
        )

    def _select_workflow_template(self, complexity, context) -> str:
        """选择工作流模板"""
        if complexity == 'high' or context.config.get('quality_priority', False):
            return 'premium_quality'
        else:
            return 'rapid_development'

    def _classify_request_type(self, request: str) -> str:
        """分类请求类型"""
        request_lower = request.lower()

        if any(keyword in request_lower for keyword in ['api', 'interface', 'endpoint']):
            return 'api_development'
        elif any(keyword in request_lower for keyword in ['ui', 'frontend', 'interface']):
            return 'frontend_development'
        elif any(keyword in request_lower for keyword in ['test', 'testing', 'verify']):
            return 'testing'
        elif any(keyword in request_lower for keyword in ['deploy', 'deployment', 'release']):
            return 'deployment'
        else:
            return 'general'

    def _calculate_complexity_score(self, request: str, execution_result: ExecutionResult) -> float:
        """计算复杂度分数"""
        base_score = len(request.split()) / 10.0  # 基于请求长度

        if execution_result.execution_time:
            time_score = min(execution_result.execution_time / 60.0, 1.0)  # 基于执行时间
        else:
            time_score = 0.5

        return min((base_score + time_score) / 2.0, 1.0)