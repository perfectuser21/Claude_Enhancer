#!/usr/bin/env python3
"""
Perfect21 核心接口定义
实现依赖倒置原则(DIP) - 所有模块依赖抽象而非具体实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, Protocol
from dataclasses import dataclass
from enum import Enum
import asyncio


# ================ 核心数据结构 ================

@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    user_request: str
    project_path: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None


@dataclass
class ExecutionResult:
    """执行结果标准格式"""
    success: bool
    data: Any = None
    error_message: str = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class AgentTask:
    """Agent任务定义"""
    agent_name: str
    task_description: str
    priority: int = 1
    dependencies: List[str] = None
    timeout: int = 300


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ================ 核心接口定义 ================

class ILogger(Protocol):
    """日志接口"""
    def info(self, message: str, **kwargs) -> None: ...
    def error(self, message: str, error: Exception = None, **kwargs) -> None: ...
    def warning(self, message: str, **kwargs) -> None: ...
    def debug(self, message: str, **kwargs) -> None: ...


class IConfigManager(ABC):
    """配置管理接口"""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass

    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置有效性"""
        pass


class ITaskAnalyzer(ABC):
    """任务分析器接口"""

    @abstractmethod
    def analyze_task(self, task_description: str, context: ExecutionContext) -> List[AgentTask]:
        """分析任务并分解为子任务"""
        pass

    @abstractmethod
    def determine_execution_mode(self, tasks: List[AgentTask]) -> ExecutionMode:
        """确定执行模式"""
        pass

    @abstractmethod
    def calculate_dependencies(self, tasks: List[AgentTask]) -> Dict[str, List[str]]:
        """计算任务依赖关系"""
        pass


class IExecutor(ABC):
    """执行器基础接口"""

    @abstractmethod
    async def execute(self, task: AgentTask, context: ExecutionContext) -> ExecutionResult:
        """执行单个任务"""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """检查执行器健康状态"""
        pass


class IParallelExecutor(IExecutor):
    """并行执行器接口"""

    @abstractmethod
    async def execute_parallel(self, tasks: List[AgentTask], context: ExecutionContext) -> List[ExecutionResult]:
        """并行执行多个任务"""
        pass

    @abstractmethod
    def set_max_workers(self, count: int) -> None:
        """设置最大工作线程数"""
        pass


class ISequentialExecutor(IExecutor):
    """顺序执行器接口"""

    @abstractmethod
    async def execute_sequential(self, tasks: List[AgentTask], context: ExecutionContext) -> List[ExecutionResult]:
        """顺序执行多个任务"""
        pass


class IWorkflowTemplate(ABC):
    """工作流模板接口"""

    @abstractmethod
    def get_template_name(self) -> str:
        """获取模板名称"""
        pass

    @abstractmethod
    def get_stages(self) -> List[Dict[str, Any]]:
        """获取工作流阶段"""
        pass

    @abstractmethod
    def validate_template(self) -> bool:
        """验证模板有效性"""
        pass


class IWorkflowOrchestrator(ABC):
    """工作流编排器接口"""

    @abstractmethod
    async def execute_workflow(self, template: IWorkflowTemplate, context: ExecutionContext) -> ExecutionResult:
        """执行工作流"""
        pass

    @abstractmethod
    def validate_sync_point(self, criteria: Dict[str, Any]) -> bool:
        """验证同步点"""
        pass

    @abstractmethod
    def get_execution_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        pass


class IQualityGate(ABC):
    """质量门接口"""

    @abstractmethod
    def check_quality(self, result: ExecutionResult, criteria: Dict[str, Any]) -> bool:
        """质量检查"""
        pass

    @abstractmethod
    def get_quality_metrics(self) -> Dict[str, Any]:
        """获取质量指标"""
        pass


class IDecisionRecorder(ABC):
    """决策记录器接口"""

    @abstractmethod
    def record_decision(self, decision: Dict[str, Any]) -> None:
        """记录决策"""
        pass

    @abstractmethod
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        pass


class ILearningSystem(ABC):
    """学习系统接口"""

    @abstractmethod
    def learn_from_execution(self, result: ExecutionResult, feedback: Dict[str, Any] = None) -> None:
        """从执行结果中学习"""
        pass

    @abstractmethod
    def get_recommendations(self, task_type: str) -> List[str]:
        """获取改进建议"""
        pass


class IEventBus(ABC):
    """事件总线接口"""

    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """发布事件"""
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        pass


class ICacheManager(ABC):
    """缓存管理器接口"""

    @abstractmethod
    def get(self, key: str) -> Any:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass


class IServiceRegistry(ABC):
    """服务注册表接口"""

    @abstractmethod
    def register_service(self, name: str, service: Any, interface: type = None) -> None:
        """注册服务"""
        pass

    @abstractmethod
    def get_service(self, name: str, interface: type = None) -> Any:
        """获取服务"""
        pass

    @abstractmethod
    def unregister_service(self, name: str) -> None:
        """注销服务"""
        pass

    @abstractmethod
    def list_services(self) -> List[str]:
        """列出所有服务"""
        pass


# ================ 组合接口 ================

class IPerfect21Core(ABC):
    """Perfect21核心系统接口"""

    @abstractmethod
    async def execute_request(self, request: str, context: ExecutionContext) -> ExecutionResult:
        """执行用户请求"""
        pass

    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        pass

    @abstractmethod
    def initialize_services(self) -> None:
        """初始化服务"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """关闭系统"""
        pass


# ================ 工厂接口 ================

class IExecutorFactory(ABC):
    """执行器工厂接口"""

    @abstractmethod
    def create_parallel_executor(self) -> IParallelExecutor:
        """创建并行执行器"""
        pass

    @abstractmethod
    def create_sequential_executor(self) -> ISequentialExecutor:
        """创建顺序执行器"""
        pass


class IWorkflowFactory(ABC):
    """工作流工厂接口"""

    @abstractmethod
    def create_workflow_template(self, template_type: str) -> IWorkflowTemplate:
        """创建工作流模板"""
        pass

    @abstractmethod
    def create_workflow_orchestrator(self) -> IWorkflowOrchestrator:
        """创建工作流编排器"""
        pass


# ================ 事件定义 ================

class EventTypes:
    """事件类型常量"""
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    QUALITY_CHECK_FAILED = "quality.check.failed"
    SYSTEM_ERROR = "system.error"


# ================ 异常定义 ================

class Perfect21Exception(Exception):
    """Perfect21基础异常"""
    pass


class TaskExecutionException(Perfect21Exception):
    """任务执行异常"""
    pass


class WorkflowException(Perfect21Exception):
    """工作流异常"""
    pass


class QualityGateException(Perfect21Exception):
    """质量门异常"""
    pass


class ConfigurationException(Perfect21Exception):
    """配置异常"""
    pass


class ServiceNotFoundException(Perfect21Exception):
    """服务未找到异常"""
    pass