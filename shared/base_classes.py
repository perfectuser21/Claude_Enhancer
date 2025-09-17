#!/usr/bin/env python3
"""
Perfect21 抽象基类
实现单一职责原则(SRP)和开闭原则(OCP)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .interfaces import (
    ILogger, IConfigManager, ITaskAnalyzer, IExecutor,
    IParallelExecutor, ISequentialExecutor, IWorkflowOrchestrator,
    IQualityGate, IDecisionRecorder, ILearningSystem, IEventBus,
    ICacheManager, ExecutionContext, ExecutionResult, AgentTask,
    ExecutionMode, TaskStatus, EventTypes
)


class BaseLogger:
    """基础日志器实现"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, error: Exception = None, **kwargs) -> None:
        if error:
            self.logger.error(f"{message}: {str(error)}", extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, extra=kwargs)


class BaseConfigManager(IConfigManager):
    """基础配置管理器"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {
            'perfect21.version': '3.0.0',
            'perfect21.mode': 'development',
            'logging.level': 'INFO',
            'logging.file': 'logs/perfect21.log',
            'execution.max_workers': 10,
            'execution.timeout': 300,
            'quality.coverage_threshold': 0.9,
            'quality.performance_threshold': 200
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔的嵌套键"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return self._defaults.get(key, default)

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点分隔的嵌套键"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        import json
        import yaml
        import os

        if not os.path.exists(config_path):
            return self._defaults.copy()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    config = json.load(f)
                elif config_path.endswith(('.yml', '.yaml')):
                    config = yaml.safe_load(f)
                else:
                    raise ValueError("Unsupported config file format")

            self._config.update(config)
            return self._config

        except Exception as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            return self._defaults.copy()

    def validate_config(self) -> bool:
        """验证配置有效性"""
        required_keys = [
            'perfect21.version',
            'execution.max_workers',
            'execution.timeout'
        ]

        for key in required_keys:
            if self.get(key) is None:
                return False

        return True


class BaseTaskAnalyzer(ITaskAnalyzer):
    """基础任务分析器"""

    def __init__(self, logger: ILogger, config: IConfigManager):
        self.logger = logger
        self.config = config

    def analyze_task(self, task_description: str, context: ExecutionContext) -> List[AgentTask]:
        """分析任务并分解为子任务"""
        # 基础实现 - 子类可以重写
        tasks = []

        # 简单的关键词匹配分解
        if "api" in task_description.lower():
            tasks.append(AgentTask("api-designer", "设计API接口", 1))
            tasks.append(AgentTask("backend-architect", "实现后端逻辑", 2))

        if "frontend" in task_description.lower() or "ui" in task_description.lower():
            tasks.append(AgentTask("frontend-specialist", "实现前端界面", 2))

        if "test" in task_description.lower():
            tasks.append(AgentTask("test-engineer", "编写测试用例", 3))

        if "deploy" in task_description.lower():
            tasks.append(AgentTask("deployment-manager", "部署应用", 4))

        # 如果没有匹配的任务，创建默认任务
        if not tasks:
            tasks.append(AgentTask("project-manager", task_description, 1))

        self.logger.info(f"任务分析完成，生成{len(tasks)}个子任务")
        return tasks

    def determine_execution_mode(self, tasks: List[AgentTask]) -> ExecutionMode:
        """确定执行模式"""
        if len(tasks) <= 1:
            return ExecutionMode.SEQUENTIAL

        # 检查依赖关系
        has_dependencies = any(task.dependencies for task in tasks)

        if has_dependencies:
            return ExecutionMode.HYBRID
        else:
            return ExecutionMode.PARALLEL

    def calculate_dependencies(self, tasks: List[AgentTask]) -> Dict[str, List[str]]:
        """计算任务依赖关系"""
        dependencies = {}

        for task in tasks:
            if task.dependencies:
                dependencies[task.agent_name] = task.dependencies
            else:
                dependencies[task.agent_name] = []

        return dependencies


class BaseExecutor(IExecutor):
    """基础执行器"""

    def __init__(self, logger: ILogger, config: IConfigManager):
        self.logger = logger
        self.config = config
        self._is_healthy = True

    async def execute(self, task: AgentTask, context: ExecutionContext) -> ExecutionResult:
        """执行单个任务 - 模板方法"""
        start_time = datetime.now()

        try:
            self.logger.info(f"开始执行任务: {task.agent_name} - {task.task_description}")

            # 执行前检查
            if not self.is_healthy():
                raise Exception("Executor is not healthy")

            # 调用具体执行逻辑
            result = await self._execute_task(task, context)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.logger.info(f"任务执行完成: {task.agent_name}, 耗时: {execution_time:.2f}s")

            return ExecutionResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    'task_id': task.agent_name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                }
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.logger.error(f"任务执行失败: {task.agent_name}", e)

            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={
                    'task_id': task.agent_name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                }
            )

    @abstractmethod
    async def _execute_task(self, task: AgentTask, context: ExecutionContext) -> Any:
        """具体执行逻辑 - 子类必须实现"""
        pass

    def is_healthy(self) -> bool:
        """检查执行器健康状态"""
        return self._is_healthy


class BaseParallelExecutor(BaseExecutor, IParallelExecutor):
    """基础并行执行器"""

    def __init__(self, logger: ILogger, config: IConfigManager):
        super().__init__(logger, config)
        self.max_workers = config.get('execution.max_workers', 10)

    async def execute_parallel(self, tasks: List[AgentTask], context: ExecutionContext) -> List[ExecutionResult]:
        """并行执行多个任务"""
        self.logger.info(f"开始并行执行{len(tasks)}个任务，最大工作线程: {self.max_workers}")

        # 使用semaphore限制并发数
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_semaphore(task: AgentTask) -> ExecutionResult:
            async with semaphore:
                return await self.execute(task, context)

        # 并行执行所有任务
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ExecutionResult(
                    success=False,
                    error_message=str(result),
                    metadata={'task_id': tasks[i].agent_name}
                ))
            else:
                processed_results.append(result)

        successful = sum(1 for r in processed_results if r.success)
        self.logger.info(f"并行执行完成: {successful}/{len(tasks)} 成功")

        return processed_results

    def set_max_workers(self, count: int) -> None:
        """设置最大工作线程数"""
        self.max_workers = max(1, count)
        self.logger.info(f"最大工作线程数设置为: {self.max_workers}")

    async def _execute_task(self, task: AgentTask, context: ExecutionContext) -> Any:
        """并行执行器的默认任务执行"""
        # 模拟执行
        await asyncio.sleep(0.1)
        return f"Task {task.agent_name} completed"


class BaseSequentialExecutor(BaseExecutor, ISequentialExecutor):
    """基础顺序执行器"""

    async def execute_sequential(self, tasks: List[AgentTask], context: ExecutionContext) -> List[ExecutionResult]:
        """顺序执行多个任务"""
        self.logger.info(f"开始顺序执行{len(tasks)}个任务")

        results = []
        for i, task in enumerate(tasks):
            self.logger.info(f"执行任务 {i+1}/{len(tasks)}: {task.agent_name}")
            result = await self.execute(task, context)
            results.append(result)

            # 如果任务失败且不允许继续，停止执行
            if not result.success and not self._should_continue_on_failure(task):
                self.logger.error(f"任务失败，停止后续执行: {task.agent_name}")
                break

        successful = sum(1 for r in results if r.success)
        self.logger.info(f"顺序执行完成: {successful}/{len(results)} 成功")

        return results

    def _should_continue_on_failure(self, task: AgentTask) -> bool:
        """判断任务失败时是否继续执行"""
        # 可以根据任务类型或配置决定
        return False

    async def _execute_task(self, task: AgentTask, context: ExecutionContext) -> Any:
        """顺序执行器的默认任务执行"""
        # 模拟执行
        await asyncio.sleep(0.1)
        return f"Task {task.agent_name} completed"


class BaseQualityGate(IQualityGate):
    """基础质量门"""

    def __init__(self, logger: ILogger, config: IConfigManager):
        self.logger = logger
        self.config = config

    def check_quality(self, result: ExecutionResult, criteria: Dict[str, Any]) -> bool:
        """质量检查"""
        if not result.success:
            return False

        # 检查执行时间
        max_time = criteria.get('max_execution_time', self.config.get('quality.performance_threshold', 200))
        if result.execution_time > max_time:
            self.logger.warning(f"执行时间超过阈值: {result.execution_time:.2f}s > {max_time}s")
            return False

        # 检查数据完整性
        if criteria.get('require_data', False) and not result.data:
            self.logger.warning("缺少必需的执行结果数据")
            return False

        return True

    def get_quality_metrics(self) -> Dict[str, Any]:
        """获取质量指标"""
        return {
            'performance_threshold': self.config.get('quality.performance_threshold', 200),
            'coverage_threshold': self.config.get('quality.coverage_threshold', 0.9),
            'last_check_time': datetime.now().isoformat()
        }


class BaseEventBus(IEventBus):
    """基础事件总线"""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self._handlers: Dict[str, List[Callable]] = {}

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """发布事件"""
        self.logger.debug(f"发布事件: {event_type}")

        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"事件处理器执行失败: {event_type}", e)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        self.logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self.logger.debug(f"取消订阅事件: {event_type}")
            except ValueError:
                pass