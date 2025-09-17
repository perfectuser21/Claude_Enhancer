"""
Perfect21 Type Definitions
Comprehensive type definitions for all data structures
"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from typing import (
    Any, Callable, Dict, List, Literal, Optional, Protocol, TypedDict, Union
)

try:
    from typing_extensions import NotRequired
except ImportError:
    try:
        from typing import NotRequired  # Python 3.11+
    except ImportError:
        # Fallback for older Python versions
        class NotRequiredMeta(type):
            def __getitem__(cls, item):
                return item

        class NotRequired(metaclass=NotRequiredMeta):
            pass

from pydantic import BaseModel, EmailStr, Field, validator


# ==================== Core Enums ====================

class ExecutionMode(str, Enum):
    """执行模式枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    LAYERED_SEQUENTIAL = "layered_sequential_with_parallel_groups"
    DOMAIN_PARALLEL = "domain_parallel"
    PARALLEL_THEN_SYNC = "parallel_then_sync"


class WorkflowState(str, Enum):
    """工作流状态枚举"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    CREATED = "created"
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class SyncPointType(str, Enum):
    """同步点类型"""
    VALIDATION = "validation"
    CHECKPOINT = "checkpoint"
    QUALITY_GATE = "quality_gate"
    CONSENSUS = "consensus"
    DEPENDENCY = "dependency"


class UserRole(str, Enum):
    """用户角色"""
    USER = "user"
    ADMIN = "admin"
    DEVELOPER = "developer"
    MANAGER = "manager"


class SecurityLevel(str, Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==================== TypedDict Definitions ====================

class UserData(TypedDict):
    """用户数据类型"""
    id: str
    username: str
    email: str
    role: UserRole
    created_at: NotRequired[str]
    last_login: NotRequired[str]
    is_active: NotRequired[bool]
    metadata: NotRequired[Dict[str, Any]]


class TokenData(TypedDict):
    """令牌数据类型"""
    user_id: str
    username: str
    role: UserRole
    exp: int
    iat: int
    jti: NotRequired[str]


class AuthResult(TypedDict):
    """认证结果类型"""
    success: bool
    message: str
    user: NotRequired[UserData]
    access_token: NotRequired[str]
    refresh_token: NotRequired[str]
    expires_in: NotRequired[float]
    error: NotRequired[str]


class TaskData(TypedDict):
    """任务数据类型"""
    task_id: str
    agent: str
    description: str
    stage: str
    priority: int
    timeout: int
    status: TaskStatus
    created_at: str
    started_at: NotRequired[str]
    completed_at: NotRequired[str]
    result: NotRequired[Dict[str, Any]]
    error: NotRequired[str]
    retry_count: int
    max_retries: int
    dependencies: List[str]
    outputs: List[str]


class StageData(TypedDict):
    """阶段数据类型"""
    name: str
    description: str
    execution_mode: ExecutionMode
    tasks: List[TaskData]
    dependencies: List[str]
    sync_point: NotRequired[Dict[str, Any]]
    quality_gate: NotRequired[Dict[str, Any]]
    thinking_mode: NotRequired[str]
    timeout: int
    status: TaskStatus
    started_at: NotRequired[str]
    completed_at: NotRequired[str]
    outputs: List[str]


class WorkflowData(TypedDict):
    """工作流数据类型"""
    workflow_id: str
    workflow_name: str
    state: WorkflowState
    current_stage: NotRequired[str]
    stages: Dict[str, StageData]
    global_context: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    quality_metrics: Dict[str, Any]
    started_at: NotRequired[str]
    completed_at: NotRequired[str]
    error_recovery_count: int
    max_error_recovery: int


class SyncPointData(TypedDict):
    """同步点数据类型"""
    sync_id: str
    name: str
    type: SyncPointType
    validation_criteria: Dict[str, Any]
    timeout: int
    must_pass: bool
    created_at: str
    status: str


class QualityGateData(TypedDict):
    """质量门数据类型"""
    gate_id: str
    name: str
    checklist: List[str]
    criteria: Dict[str, Any]
    must_pass: bool
    automated: bool


class CapabilityData(TypedDict):
    """能力数据类型"""
    name: str
    version: str
    description: str
    dependencies: List[str]
    status: str
    metadata: Dict[str, Any]


class AgentConfig(TypedDict):
    """Agent配置类型"""
    name: str
    role: str
    expertise: List[str]
    capabilities: List[str]
    priority: int
    timeout: int
    max_retries: int
    parallel_safe: bool


class WorkflowConfig(TypedDict):
    """工作流配置类型"""
    name: str
    description: str
    version: str
    stages: List[Dict[str, Any]]
    global_context: NotRequired[Dict[str, Any]]
    quality_gates: NotRequired[List[QualityGateData]]
    sync_points: NotRequired[List[SyncPointData]]


class ExecutionPlan(TypedDict):
    """执行计划类型"""
    type: Literal["parallel", "sequential", "layered", "hybrid"]
    groups: NotRequired[List[Dict[str, List[str]]]]
    order: NotRequired[List[str]]
    levels: NotRequired[List[List[str]]]
    estimated_duration: NotRequired[int]
    resource_requirements: NotRequired[Dict[str, Any]]


class PerformanceMetrics(TypedDict):
    """性能指标类型"""
    total_execution_time: float
    stage_execution_times: Dict[str, float]
    task_execution_times: Dict[str, float]
    sync_point_wait_times: Dict[str, float]
    quality_gate_check_times: Dict[str, float]
    memory_usage: NotRequired[Dict[str, Any]]
    cpu_usage: NotRequired[Dict[str, Any]]


class SecurityEvent(TypedDict):
    """安全事件类型"""
    event_id: str
    event_type: str
    user_id: NotRequired[str]
    ip_address: str
    timestamp: str
    severity: SecurityLevel
    description: str
    metadata: NotRequired[Dict[str, Any]]


class CacheEntry(TypedDict):
    """缓存条目类型"""
    key: str
    value: Any
    ttl: int
    created_at: str
    access_count: int
    last_accessed: str


# ==================== Pydantic Models ====================

class TaskModel(BaseModel):
    """任务模型"""
    task_id: str
    agent: str
    description: str
    stage: str
    priority: int = Field(ge=1, le=10)
    timeout: int = Field(gt=0)
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = Field(ge=0)
    max_retries: int = Field(ge=0)
    dependencies: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)

    @validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError('task_id must be at least 3 characters long')
        return v

    @validator('agent')
    def validate_agent(cls, v: str) -> str:
        if not v or not v.startswith('@'):
            raise ValueError('agent must start with @')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class StageModel(BaseModel):
    """阶段模型"""
    name: str
    description: str
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    tasks: List[TaskModel] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    sync_point: Optional[Dict[str, Any]] = None
    quality_gate: Optional[Dict[str, Any]] = None
    thinking_mode: Optional[str] = None
    timeout: int = Field(default=1800, gt=0)
    status: TaskStatus = TaskStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: List[str] = Field(default_factory=list)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not v or len(v) < 2:
            raise ValueError('stage name must be at least 2 characters long')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class WorkflowModel(BaseModel):
    """工作流模型"""
    workflow_id: str
    workflow_name: str
    state: WorkflowState = WorkflowState.INITIALIZED
    current_stage: Optional[str] = None
    stages: Dict[str, StageModel] = Field(default_factory=dict)
    global_context: Dict[str, Any] = Field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_recovery_count: int = Field(default=0, ge=0)
    max_error_recovery: int = Field(default=5, ge=1)

    @validator('workflow_id')
    def validate_workflow_id(cls, v: str) -> str:
        if not v or len(v) < 5:
            raise ValueError('workflow_id must be at least 5 characters long')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class UserModel(BaseModel):
    """用户模型"""
    id: str
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('username')
    def validate_username(cls, v: str) -> str:
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('username can only contain alphanumeric characters, underscores, and hyphens')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class ConfigModel(BaseModel):
    """配置模型"""
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    database_url: str
    redis_url: Optional[str] = None
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    max_login_attempts: int = Field(default=5, ge=1)
    rate_limit_per_minute: int = Field(default=60, ge=1)

    @validator('secret_key')
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('secret_key must be at least 32 characters long')
        return v

    class Config:
        validate_assignment = True


# ==================== Protocols ====================

class CacheProtocol(Protocol):
    """缓存协议"""

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        ...

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        ...

    def clear(self) -> bool:
        """清空缓存"""
        ...


class LoggerProtocol(Protocol):
    """日志协议"""

    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        ...

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        ...


class DatabaseProtocol(Protocol):
    """数据库协议"""

    def connect(self) -> bool:
        """连接数据库"""
        ...

    def disconnect(self) -> bool:
        """断开数据库连接"""
        ...

    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL查询"""
        ...

    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """获取单行结果"""
        ...

    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取所有结果"""
        ...


class EventHandlerProtocol(Protocol):
    """事件处理器协议"""

    def handle(self, event_data: Dict[str, Any]) -> Any:
        """处理事件"""
        ...


class ValidatorProtocol(Protocol):
    """验证器协议"""

    def validate(self, data: Any) -> bool:
        """验证数据"""
        ...

    def get_errors(self) -> List[str]:
        """获取验证错误"""
        ...


# ==================== Callable Types ====================

TaskExecutor = Callable[[str], Dict[str, Any]]
StageCallback = Callable[[StageModel], None]
TaskCallback = Callable[[TaskModel], None]
ErrorHandler = Callable[[Exception], Dict[str, Any]]
ProgressCallback = Callable[[float], None]


# ==================== Union Types ====================

ExecutionResult = Union[Dict[str, Any], Exception]
ValidationResult = Union[bool, Dict[str, Any]]
CacheValue = Union[str, int, float, bool, Dict[str, Any], List[Any]]


# ==================== Constants ====================

DEFAULT_TASK_TIMEOUT = 300
DEFAULT_STAGE_TIMEOUT = 1800
DEFAULT_WORKFLOW_TIMEOUT = 3600
MAX_RETRY_COUNT = 3
DEFAULT_CACHE_TTL = 3600

# API Response Types
class APISuccessResponse(TypedDict):
    success: bool
    data: Any
    message: str

class APIErrorResponse(TypedDict):
    success: bool
    error: str
    code: str
    details: NotRequired[Dict[str, Any]]

APIResponse = Union[APISuccessResponse, APIErrorResponse]


# ==================== Export ====================

__all__ = [
    # Enums
    'ExecutionMode',
    'WorkflowState',
    'TaskStatus',
    'SyncPointType',
    'UserRole',
    'SecurityLevel',

    # TypedDict
    'UserData',
    'TokenData',
    'AuthResult',
    'TaskData',
    'StageData',
    'WorkflowData',
    'SyncPointData',
    'QualityGateData',
    'CapabilityData',
    'AgentConfig',
    'WorkflowConfig',
    'ExecutionPlan',
    'PerformanceMetrics',
    'SecurityEvent',
    'CacheEntry',
    'APISuccessResponse',
    'APIErrorResponse',
    'APIResponse',

    # Pydantic Models
    'TaskModel',
    'StageModel',
    'WorkflowModel',
    'UserModel',
    'ConfigModel',

    # Protocols
    'CacheProtocol',
    'LoggerProtocol',
    'DatabaseProtocol',
    'EventHandlerProtocol',
    'ValidatorProtocol',

    # Callable Types
    'TaskExecutor',
    'StageCallback',
    'TaskCallback',
    'ErrorHandler',
    'ProgressCallback',

    # Union Types
    'ExecutionResult',
    'ValidationResult',
    'CacheValue',

    # Constants
    'DEFAULT_TASK_TIMEOUT',
    'DEFAULT_STAGE_TIMEOUT',
    'DEFAULT_WORKFLOW_TIMEOUT',
    'MAX_RETRY_COUNT',
    'DEFAULT_CACHE_TTL'
]