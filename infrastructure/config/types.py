#!/usr/bin/env python3
"""
配置类型定义 - TypeScript风格的类型定义
提供完整的类型安全支持
"""

from typing import Dict, Any, List, Optional, Union, Literal, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass

try:
    from pydantic import BaseModel, Field
except ImportError:
    # 如果没有pydantic，提供基础类型定义
    class BaseModel:
        pass

    def Field(**kwargs):
        return None

# ====================== 基础类型定义 ======================

ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]
EnvironmentName = Literal["development", "testing", "staging", "production"]
LogLevelName = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DatabaseTypeName = Literal["sqlite", "postgresql", "mysql"]
CacheTypeName = Literal["memory", "file", "redis"]

# ====================== TypeScript风格的接口定义 ======================

class IServerConfig:
    """服务器配置接口"""
    host: str
    port: int
    workers: int
    reload: bool
    debug: bool
    max_connections: int
    keepalive_timeout: int

class IDatabaseConfig:
    """数据库配置接口"""
    type: DatabaseTypeName
    path: Optional[str]
    host: Optional[str]
    port: Optional[int]
    name: Optional[str]
    user: Optional[str]
    password: Optional[str]
    pool_size: int
    max_overflow: int
    pool_timeout: int

class ICacheConfig:
    """缓存配置接口"""
    type: CacheTypeName
    default_ttl: int
    file_dir: Optional[str]
    redis_host: Optional[str]
    redis_port: int
    redis_db: int
    redis_password: Optional[str]

class IAuthConfig:
    """认证配置接口"""
    jwt_secret_key: str
    access_token_expire_hours: int
    refresh_token_expire_days: int
    password_min_length: int
    max_login_attempts: int
    lockout_duration_minutes: int

class ILoggingConfig:
    """日志配置接口"""
    level: LogLevelName
    file: Optional[str]
    max_size_mb: int
    backup_count: int
    format: str

class IPerfect21Config:
    """Perfect21核心配置接口"""
    version: str
    mode: EnvironmentName
    project_root: Optional[str]
    enable_monitoring: bool
    data_dir: str
    logs_dir: str
    temp_dir: str

class IRateLimitingConfig:
    """API限流配置接口"""
    enabled: bool
    default_max_requests: int
    default_window_seconds: int
    endpoint_limits: Dict[str, Dict[str, int]]

class ISecurityConfig:
    """安全配置接口"""
    allowed_origins: List[str]
    cors_credentials: bool
    secure_cookies: bool
    session_secure: bool
    content_type_nosniff: bool
    frame_deny: bool
    xss_protection: bool

class IMonitoringConfig:
    """监控配置接口"""
    enabled: bool
    metrics_endpoint: str
    health_check_endpoint: str
    performance_tracking: bool

class ITaskExecutionConfig:
    """任务执行配置接口"""
    max_parallel_tasks: int
    default_timeout: int
    max_timeout: int
    result_cache_ttl: int

class IGitWorkflowConfig:
    """Git工作流配置接口"""
    enabled: bool
    auto_hooks: bool
    branch_protection: bool
    require_pr_review: bool

class IFileUploadConfig:
    """文件上传配置接口"""
    enabled: bool
    max_file_size: str
    allowed_extensions: List[str]
    upload_dir: str

class IEmailConfig:
    """邮件配置接口"""
    enabled: bool
    smtp_server: Optional[str]
    smtp_port: int
    smtp_user: Optional[str]
    smtp_password: Optional[str]
    from_address: Optional[str]

class IBackupConfig:
    """备份配置接口"""
    enabled: bool
    schedule: str
    retention_days: int
    backup_dir: str

class IGitConfig:
    """Git相关配置接口"""
    cache_ttl: int
    max_parallel_commands: int
    batch_operations: bool
    timeout: int

class IPerformanceConfig:
    """性能相关配置接口"""
    enable_cache: bool
    async_operations: bool
    batch_git_operations: bool
    max_concurrent_commands: int
    memory_limit_mb: int

class ICLIConfig:
    """CLI相关配置接口"""
    max_output_lines: int
    enable_colors: bool
    default_timeout: int
    progress_indicators: bool

# ====================== 完整配置接口 ======================

class IPerfect21ConfigModel:
    """Perfect21完整配置模型接口"""
    perfect21: IPerfect21Config
    server: IServerConfig
    database: IDatabaseConfig
    cache: ICacheConfig
    auth: IAuthConfig
    rate_limiting: IRateLimitingConfig
    security: ISecurityConfig
    monitoring: IMonitoringConfig
    task_execution: ITaskExecutionConfig
    git_workflow: IGitWorkflowConfig
    file_upload: IFileUploadConfig
    email: IEmailConfig
    backup: IBackupConfig
    git: IGitConfig
    performance: IPerformanceConfig
    cli: ICLIConfig
    logging: ILoggingConfig

# ====================== 配置验证类型 ======================

@dataclass
class ConfigValidationError:
    """配置验证错误"""
    field: str
    message: str
    value: Any
    expected_type: str

@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[ConfigValidationError]
    warnings: List[str]

# ====================== 配置管理器接口 ======================

class IConfigManager:
    """配置管理器接口"""

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass

    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        pass

    def get_section(self, section: str) -> Optional[BaseModel]:
        """获取配置节"""
        pass

    def reload(self) -> bool:
        """重新加载配置"""
        pass

    def validate_config(self) -> List[str]:
        """验证配置"""
        pass

    def export_config(self, file_path: str, include_secrets: bool = False) -> bool:
        """导出配置"""
        pass

    def save_user_config(self, config: Union[Dict[str, Any], BaseModel]) -> bool:
        """保存用户配置"""
        pass

# ====================== 泛型配置访问器 ======================

T = TypeVar('T', bound=BaseModel)

class ConfigAccessor(Generic[T]):
    """类型安全的配置访问器"""

    def __init__(self, config_type: type[T], manager: IConfigManager):
        self.config_type = config_type
        self.manager = manager

    def get(self) -> Optional[T]:
        """获取类型化配置"""
        section_name = self.config_type.__name__.lower().replace('config', '')
        return self.manager.get_section(section_name)

    def set(self, config: T) -> bool:
        """设置类型化配置"""
        section_name = self.config_type.__name__.lower().replace('config', '')
        return self.manager.set(section_name, config)

# ====================== 实用类型守卫 ======================

def is_development_mode(config: IPerfect21Config) -> bool:
    """检查是否为开发模式"""
    return config.mode == "development"

def is_production_mode(config: IPerfect21Config) -> bool:
    """检查是否为生产模式"""
    return config.mode == "production"

def has_database_config(config: IDatabaseConfig) -> bool:
    """检查是否有有效的数据库配置"""
    if config.type == "sqlite":
        return bool(config.path)
    else:
        return bool(config.host and config.name and config.user)

def has_cache_config(config: ICacheConfig) -> bool:
    """检查是否有有效的缓存配置"""
    if config.type == "redis":
        return bool(config.redis_host)
    elif config.type == "file":
        return bool(config.file_dir)
    return True  # memory cache always available

def has_email_config(config: IEmailConfig) -> bool:
    """检查是否有有效的邮件配置"""
    return (config.enabled and
            bool(config.smtp_server and config.smtp_user and
                 config.smtp_password and config.from_address))

# ====================== 配置合并策略 ======================

class ConfigMergeStrategy(Enum):
    """配置合并策略"""
    REPLACE = "replace"  # 完全替换
    MERGE = "merge"      # 深度合并
    APPEND = "append"    # 追加（仅适用于列表）
    UPDATE = "update"    # 更新（仅适用于字典）

@dataclass
class ConfigMergeRule:
    """配置合并规则"""
    path: str
    strategy: ConfigMergeStrategy
    priority: int = 0

# ====================== 配置模板类型 ======================

class ConfigTemplate:
    """配置模板"""
    name: str
    description: str
    environment: EnvironmentName
    template_data: Dict[str, Any]
    required_env_vars: List[str]
    optional_env_vars: List[str]

# ====================== 导出所有类型 ======================

__all__ = [
    # 基础类型
    'ConfigValue', 'EnvironmentName', 'LogLevelName',
    'DatabaseTypeName', 'CacheTypeName',

    # 配置接口
    'IServerConfig', 'IDatabaseConfig', 'ICacheConfig', 'IAuthConfig',
    'ILoggingConfig', 'IPerfect21Config', 'IRateLimitingConfig',
    'ISecurityConfig', 'IMonitoringConfig', 'ITaskExecutionConfig',
    'IGitWorkflowConfig', 'IFileUploadConfig', 'IEmailConfig',
    'IBackupConfig', 'IGitConfig', 'IPerformanceConfig', 'ICLIConfig',
    'IPerfect21ConfigModel',

    # 验证类型
    'ConfigValidationError', 'ConfigValidationResult',

    # 管理器接口
    'IConfigManager', 'ConfigAccessor',

    # 类型守卫
    'is_development_mode', 'is_production_mode', 'has_database_config',
    'has_cache_config', 'has_email_config',

    # 合并策略
    'ConfigMergeStrategy', 'ConfigMergeRule', 'ConfigTemplate'
]