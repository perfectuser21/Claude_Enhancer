"""
Runtime Type Validation
Pydantic-based runtime validation for Perfect21
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator, ValidationError, EmailStr

from .types import (
    ExecutionMode, WorkflowState, TaskStatus, SyncPointType, UserRole, SecurityLevel
)


# ==================== Core Data Validators ====================

class TaskValidator(BaseModel):
    """任务数据验证器"""
    task_id: str = Field(min_length=3, max_length=100)
    agent: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=5, max_length=500)
    stage: str = Field(min_length=2, max_length=50)
    priority: int = Field(ge=1, le=10)
    timeout: int = Field(gt=0, le=7200)  # Max 2 hours
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = Field(None, max_length=1000)
    retry_count: int = Field(ge=0, le=10)
    max_retries: int = Field(ge=0, le=10)
    dependencies: List[str] = Field(default_factory=list, max_items=50)
    outputs: List[str] = Field(default_factory=list, max_items=100)

    @validator('task_id')
    def validate_task_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('task_id can only contain alphanumeric characters, underscores, and hyphens')
        return v

    @validator('agent')
    def validate_agent(cls, v: str) -> str:
        if not v.startswith('@'):
            raise ValueError('agent must start with @')
        if not re.match(r'^@[a-zA-Z0-9_-]+$', v):
            raise ValueError('agent name can only contain alphanumeric characters, underscores, and hyphens')
        return v

    @validator('completed_at')
    def validate_completion_time(cls, v: Optional[datetime], values: Dict[str, Any]) -> Optional[datetime]:
        if v is not None and 'started_at' in values and values['started_at'] is not None:
            if v < values['started_at']:
                raise ValueError('completed_at cannot be before started_at')
        return v

    @validator('retry_count')
    def validate_retry_count(cls, v: int, values: Dict[str, Any]) -> int:
        if 'max_retries' in values and v > values['max_retries']:
            raise ValueError('retry_count cannot exceed max_retries')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class StageValidator(BaseModel):
    """阶段数据验证器"""
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=500)
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    tasks: List[TaskValidator] = Field(default_factory=list, max_items=100)
    dependencies: List[str] = Field(default_factory=list, max_items=20)
    sync_point: Optional[Dict[str, Any]] = None
    quality_gate: Optional[Dict[str, Any]] = None
    thinking_mode: Optional[str] = Field(None, max_length=50)
    timeout: int = Field(default=1800, gt=0, le=14400)  # Max 4 hours
    status: TaskStatus = TaskStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: List[str] = Field(default_factory=list, max_items=100)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_\s-]+$', v):
            raise ValueError('stage name can only contain alphanumeric characters, spaces, underscores, and hyphens')
        return v.strip()

    @validator('tasks')
    def validate_tasks(cls, v: List[TaskValidator]) -> List[TaskValidator]:
        if len(v) > 100:
            raise ValueError('stage cannot have more than 100 tasks')

        # Check for duplicate task IDs
        task_ids = [task.task_id for task in v]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError('duplicate task IDs found in stage')

        return v

    @validator('dependencies')
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError('duplicate dependencies found')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class WorkflowValidator(BaseModel):
    """工作流数据验证器"""
    workflow_id: str = Field(min_length=5, max_length=100)
    workflow_name: str = Field(min_length=3, max_length=200)
    state: WorkflowState = WorkflowState.INITIALIZED
    current_stage: Optional[str] = Field(None, max_length=100)
    stages: Dict[str, StageValidator] = Field(default_factory=dict, max_items=50)
    global_context: Dict[str, Any] = Field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list, max_items=10000)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_recovery_count: int = Field(default=0, ge=0, le=20)
    max_error_recovery: int = Field(default=5, ge=1, le=20)

    @validator('workflow_id')
    def validate_workflow_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('workflow_id can only contain alphanumeric characters, underscores, and hyphens')
        return v

    @validator('stages')
    def validate_stages(cls, v: Dict[str, StageValidator]) -> Dict[str, StageValidator]:
        if len(v) > 50:
            raise ValueError('workflow cannot have more than 50 stages')

        # Validate stage dependencies
        stage_names = set(v.keys())
        for stage_name, stage in v.items():
            for dep in stage.dependencies:
                if dep not in stage_names:
                    raise ValueError(f'stage {stage_name} depends on non-existent stage {dep}')

        return v

    @validator('current_stage')
    def validate_current_stage(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if v is not None and 'stages' in values:
            if v not in values['stages']:
                raise ValueError(f'current_stage {v} does not exist in stages')
        return v

    @validator('error_recovery_count')
    def validate_error_recovery_count(cls, v: int, values: Dict[str, Any]) -> int:
        if 'max_error_recovery' in values and v > values['max_error_recovery']:
            raise ValueError('error_recovery_count cannot exceed max_error_recovery')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class UserValidator(BaseModel):
    """用户数据验证器"""
    id: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('username')
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('username can only contain alphanumeric characters, underscores, and hyphens')
        return v.lower()

    @validator('metadata')
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Limit metadata size
        import json
        if len(json.dumps(v)) > 10000:  # 10KB limit
            raise ValueError('metadata too large (max 10KB)')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


class SyncPointValidator(BaseModel):
    """同步点验证器"""
    sync_id: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=3, max_length=200)
    type: SyncPointType
    validation_criteria: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, gt=0, le=3600)  # Max 1 hour
    must_pass: bool = True
    created_at: str  # ISO format datetime string
    status: str = Field(default='waiting')

    @validator('sync_id')
    def validate_sync_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('sync_id can only contain alphanumeric characters, underscores, and hyphens')
        return v

    @validator('created_at')
    def validate_created_at(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('created_at must be a valid ISO format datetime string')
        return v

    @validator('status')
    def validate_status(cls, v: str) -> str:
        valid_statuses = {'waiting', 'passed', 'failed', 'timeout', 'skipped'}
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v

    class Config:
        use_enum_values = True
        validate_assignment = True


# ==================== Configuration Validators ====================

class DatabaseConfigValidator(BaseModel):
    """数据库配置验证器"""
    url: str = Field(min_length=10)
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=86400)

    @validator('url')
    def validate_url(cls, v: str) -> str:
        valid_schemes = ['sqlite:///', 'postgresql://', 'mysql://']
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(f'database URL must start with one of {valid_schemes}')
        return v

    class Config:
        validate_assignment = True


class RedisConfigValidator(BaseModel):
    """Redis配置验证器"""
    host: str = Field(default='localhost')
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: Optional[str] = None
    timeout: int = Field(default=5, ge=1, le=60)
    max_connections: int = Field(default=50, ge=1, le=1000)

    class Config:
        validate_assignment = True


class SecurityConfigValidator(BaseModel):
    """安全配置验证器"""
    secret_key: str = Field(min_length=32)
    algorithm: str = Field(default='HS256')
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)  # Max 24 hours
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)  # Max 90 days
    max_login_attempts: int = Field(default=5, ge=1, le=20)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    password_min_length: int = Field(default=8, ge=6, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digits: bool = Field(default=True)
    password_require_special: bool = Field(default=False)

    @validator('algorithm')
    def validate_algorithm(cls, v: str) -> str:
        valid_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if v not in valid_algorithms:
            raise ValueError(f'algorithm must be one of {valid_algorithms}')
        return v

    @validator('secret_key')
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('secret_key must be at least 32 characters long')
        return v

    class Config:
        validate_assignment = True


class APIConfigValidator(BaseModel):
    """API配置验证器"""
    host: str = Field(default='0.0.0.0')
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1, le=32)
    timeout: int = Field(default=30, ge=1, le=300)
    max_request_size: int = Field(default=16777216, ge=1024, le=104857600)  # 1KB to 100MB
    cors_origins: List[str] = Field(default_factory=list)
    debug: bool = Field(default=False)

    @validator('cors_origins')
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        for origin in v:
            if not (origin == '*' or origin.startswith(('http://', 'https://'))):
                raise ValueError(f'invalid CORS origin: {origin}')
        return v

    class Config:
        validate_assignment = True


# ==================== Validation Helper Functions ====================

def validate_task_data(data: Dict[str, Any]) -> TaskValidator:
    """验证任务数据"""
    try:
        return TaskValidator(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid task data: {e}")


def validate_stage_data(data: Dict[str, Any]) -> StageValidator:
    """验证阶段数据"""
    try:
        return StageValidator(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid stage data: {e}")


def validate_workflow_data(data: Dict[str, Any]) -> WorkflowValidator:
    """验证工作流数据"""
    try:
        return WorkflowValidator(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid workflow data: {e}")


def validate_user_data(data: Dict[str, Any]) -> UserValidator:
    """验证用户数据"""
    try:
        return UserValidator(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid user data: {e}")


def validate_sync_point_data(data: Dict[str, Any]) -> SyncPointValidator:
    """验证同步点数据"""
    try:
        return SyncPointValidator(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid sync point data: {e}")


def validate_password_strength(password: str, config: SecurityConfigValidator) -> bool:
    """验证密码强度"""
    if len(password) < config.password_min_length:
        raise ValueError(f"Password must be at least {config.password_min_length} characters long")

    if config.password_require_uppercase and not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")

    if config.password_require_lowercase and not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")

    if config.password_require_digits and not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")

    if config.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")

    return True


def validate_execution_plan(data: Dict[str, Any]) -> bool:
    """验证执行计划数据"""
    required_fields = ['type']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    plan_type = data['type']
    valid_types = ['parallel', 'sequential', 'layered', 'hybrid']
    if plan_type not in valid_types:
        raise ValueError(f"Invalid plan type: {plan_type}, must be one of {valid_types}")

    if plan_type == 'parallel' and 'groups' not in data:
        raise ValueError("Parallel execution plan must have 'groups' field")

    if plan_type == 'sequential' and 'order' not in data:
        raise ValueError("Sequential execution plan must have 'order' field")

    if plan_type == 'layered' and 'levels' not in data:
        raise ValueError("Layered execution plan must have 'levels' field")

    return True


# ==================== Export ====================

__all__ = [
    'TaskValidator',
    'StageValidator',
    'WorkflowValidator',
    'UserValidator',
    'SyncPointValidator',
    'DatabaseConfigValidator',
    'RedisConfigValidator',
    'SecurityConfigValidator',
    'APIConfigValidator',
    'validate_task_data',
    'validate_stage_data',
    'validate_workflow_data',
    'validate_user_data',
    'validate_sync_point_data',
    'validate_password_strength',
    'validate_execution_plan'
]