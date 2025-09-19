"""
Perfect21 核心接口定义
所有features必须实现这些接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"

@dataclass
class FeatureConfig:
    """Feature配置"""
    name: str
    version: str
    enabled: bool = True
    config: Dict[str, Any] = None

class FeatureInterface(ABC):
    """所有Feature必须实现的接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """功能名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """版本号"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """功能描述"""
        pass

    @property
    @abstractmethod
    def required_agents(self) -> List[str]:
        """推荐的agents组合"""
        pass

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化功能"""
        pass

    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> bool:
        """验证功能是否可用"""
        pass

    @abstractmethod
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行功能"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """获取功能度量（可选）"""
        return {}

    def get_status(self) -> Dict[str, Any]:
        """获取功能状态（可选）"""
        return {"enabled": True}

class WorkflowInterface(ABC):
    """工作流接口"""

    @abstractmethod
    def generate(self, request: str) -> Dict[str, Any]:
        """生成工作流"""
        pass

    @abstractmethod
    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        pass

    @abstractmethod
    def validate(self, workflow: Dict[str, Any]) -> bool:
        """验证工作流"""
        pass

class AgentSelectorInterface(ABC):
    """Agent选择器接口"""

    @abstractmethod
    def select_agents(self, task: str, min_agents: int = 3, max_agents: int = 5) -> List[str]:
        """选择合适的agents"""
        pass

    @abstractmethod
    def get_success_patterns(self) -> Dict[str, List[str]]:
        """获取成功模式"""
        pass

    @abstractmethod
    def record_result(self, task: str, agents: List[str], success: bool) -> None:
        """记录执行结果用于学习"""
        pass

class QualityGateInterface(ABC):
    """质量门接口"""

    @abstractmethod
    def check(self, artifact: Any, criteria: Dict[str, Any]) -> bool:
        """检查质量标准"""
        pass

    @abstractmethod
    def get_report(self) -> Dict[str, Any]:
        """获取质量报告"""
        pass

class ExecutorInterface(ABC):
    """执行器接口"""

    @abstractmethod
    def execute(self, tasks: List[Dict[str, Any]], mode: ExecutionMode) -> List[Dict[str, Any]]:
        """执行任务"""
        pass

    @abstractmethod
    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        pass

    @abstractmethod
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        pass

class MemoryInterface(ABC):
    """记忆系统接口"""

    @abstractmethod
    def save(self, key: str, value: Any, category: str = "general") -> bool:
        """保存记忆"""
        pass

    @abstractmethod
    def load(self, key: str, category: str = "general") -> Optional[Any]:
        """加载记忆"""
        pass

    @abstractmethod
    def search(self, pattern: str, category: str = None) -> List[Dict[str, Any]]:
        """搜索记忆"""
        pass

    @abstractmethod
    def analyze_patterns(self) -> Dict[str, Any]:
        """分析模式"""
        pass