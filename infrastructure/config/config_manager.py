#!/usr/bin/env python3
"""
配置管理系统 - 类型安全的统一配置管理
支持多环境、热重载、Pydantic schema验证
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List, Type, TypeVar, Generic, get_type_hints
from pathlib import Path
import threading
from datetime import datetime
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator, ValidationError, SecretStr
    from pydantic.env_settings import BaseSettings
except ImportError:
    raise ImportError("Please install pydantic: pip install pydantic[dotenv]")

logger = logging.getLogger("ConfigManager")

T = TypeVar('T', bound=BaseModel)


class EnvironmentType(str, Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class CacheType(str, Enum):
    """缓存类型枚举"""
    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"


# ====================== Pydantic配置模型 ======================

class GitConfig(BaseModel):
    """Git相关配置"""
    cache_ttl: int = Field(default=30, ge=0, le=3600, description="Git缓存TTL（秒）")
    max_parallel_commands: int = Field(default=5, ge=1, le=20, description="最大并行Git命令数")
    batch_operations: bool = Field(default=True, description="启用批量操作")
    timeout: int = Field(default=300, ge=10, le=1800, description="Git命令超时时间（秒）")

    class Config:
        env_prefix = "PERFECT21_GIT_"
        case_sensitive = False


class PerformanceConfig(BaseModel):
    """性能相关配置"""
    enable_cache: bool = Field(default=True, description="启用缓存")
    async_operations: bool = Field(default=True, description="启用异步操作")
    batch_git_operations: bool = Field(default=True, description="启用批量Git操作")
    max_concurrent_commands: int = Field(default=10, ge=1, le=100, description="最大并发命令数")
    memory_limit_mb: int = Field(default=512, ge=64, le=8192, description="内存限制（MB）")

    class Config:
        env_prefix = "PERFECT21_PERFORMANCE_"
        case_sensitive = False


class CLIConfig(BaseModel):
    """CLI相关配置"""
    max_output_lines: int = Field(default=1000, ge=100, le=10000, description="最大输出行数")
    enable_colors: bool = Field(default=True, description="启用颜色输出")
    default_timeout: int = Field(default=300, ge=10, le=3600, description="默认超时时间（秒）")
    progress_indicators: bool = Field(default=True, description="显示进度指示器")

    class Config:
        env_prefix = "PERFECT21_CLI_"
        case_sensitive = False


class LoggingConfig(BaseModel):
    """日志相关配置"""
    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_size_mb: int = Field(default=10, ge=1, le=1000, description="日志文件最大大小（MB）")
    backup_count: int = Field(default=5, ge=1, le=50, description="日志备份文件数量")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")

    @validator('file')
    def validate_log_file(cls, v):
        if v and not v.endswith('.log'):
            return f"{v}.log"
        return v

    class Config:
        env_prefix = "PERFECT21_LOG_"
        case_sensitive = False


class Perfect21Config(BaseModel):
    """Perfect21核心配置"""
    version: str = Field(default="3.1.0", description="版本号")
    mode: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT, description="运行模式")
    project_root: Optional[str] = Field(default=None, description="项目根目录")
    enable_monitoring: bool = Field(default=True, description="启用监控")
    data_dir: str = Field(default="data", description="数据目录")
    logs_dir: str = Field(default="logs", description="日志目录")
    temp_dir: str = Field(default="temp", description="临时目录")

    class Config:
        env_prefix = "PERFECT21_"
        case_sensitive = False


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="127.0.0.1", description="服务器地址")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    workers: int = Field(default=1, ge=1, le=32, description="工作进程数")
    reload: bool = Field(default=False, description="自动重载")
    debug: bool = Field(default=False, description="调试模式")
    max_connections: int = Field(default=1000, ge=1, le=10000, description="最大连接数")
    keepalive_timeout: int = Field(default=65, ge=1, le=300, description="Keep-Alive超时")

    class Config:
        env_prefix = "PERFECT21_SERVER_"
        case_sensitive = False


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: DatabaseType = Field(default=DatabaseType.SQLITE, description="数据库类型")
    path: Optional[str] = Field(default=None, description="SQLite数据库路径")
    host: Optional[str] = Field(default=None, description="数据库主机")
    port: Optional[int] = Field(default=None, ge=1, le=65535, description="数据库端口")
    name: Optional[str] = Field(default=None, description="数据库名称")
    user: Optional[str] = Field(default=None, description="数据库用户")
    password: Optional[SecretStr] = Field(default=None, description="数据库密码")
    pool_size: int = Field(default=5, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, le=100, description="连接池最大溢出")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="连接池超时")

    @validator('port')
    def validate_port_with_type(cls, v, values):
        db_type = values.get('type')
        if v is None and db_type != DatabaseType.SQLITE:
            if db_type == DatabaseType.POSTGRESQL:
                return 5432
            elif db_type == DatabaseType.MYSQL:
                return 3306
        return v

    class Config:
        env_prefix = "PERFECT21_DB_"
        case_sensitive = False


class CacheConfig(BaseModel):
    """缓存配置"""
    type: CacheType = Field(default=CacheType.MEMORY, description="缓存类型")
    default_ttl: int = Field(default=1800, ge=1, le=86400, description="默认TTL（秒）")
    file_dir: Optional[str] = Field(default=None, description="文件缓存目录")
    redis_host: Optional[str] = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis端口")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis数据库")
    redis_password: Optional[SecretStr] = Field(default=None, description="Redis密码")

    class Config:
        env_prefix = "PERFECT21_CACHE_"
        case_sensitive = False


class AuthConfig(BaseModel):
    """认证配置"""
    jwt_secret_key: SecretStr = Field(description="JWT密钥")
    access_token_expire_hours: int = Field(default=1, ge=1, le=168, description="访问令牌过期时间（小时）")
    refresh_token_expire_days: int = Field(default=7, ge=1, le=365, description="刷新令牌过期时间（天）")
    password_min_length: int = Field(default=8, ge=6, le=128, description="密码最小长度")
    max_login_attempts: int = Field(default=5, ge=1, le=20, description="最大登录尝试次数")
    lockout_duration_minutes: int = Field(default=15, ge=1, le=1440, description="锁定持续时间（分钟）")

    class Config:
        env_prefix = "PERFECT21_AUTH_"
        case_sensitive = False


class RateLimitingConfig(BaseModel):
    """API限流配置"""
    enabled: bool = Field(default=True, description="启用限流")
    default_max_requests: int = Field(default=1000, ge=1, le=100000, description="默认最大请求数")
    default_window_seconds: int = Field(default=3600, ge=1, le=86400, description="默认时间窗口（秒）")
    endpoint_limits: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="端点特殊限制")

    class Config:
        env_prefix = "PERFECT21_RATE_"
        case_sensitive = False


class SecurityConfig(BaseModel):
    """安全配置"""
    allowed_origins: List[str] = Field(default=["*"], description="允许的CORS源")
    cors_credentials: bool = Field(default=True, description="CORS凭据")
    secure_cookies: bool = Field(default=False, description="安全Cookie")
    session_secure: bool = Field(default=False, description="安全会话")
    content_type_nosniff: bool = Field(default=True, description="内容类型嗅探保护")
    frame_deny: bool = Field(default=True, description="帧拒绝")
    xss_protection: bool = Field(default=True, description="XSS保护")

    class Config:
        env_prefix = "PERFECT21_SECURITY_"
        case_sensitive = False


class MonitoringConfig(BaseModel):
    """监控配置"""
    enabled: bool = Field(default=True, description="启用监控")
    metrics_endpoint: str = Field(default="/metrics", description="指标端点")
    health_check_endpoint: str = Field(default="/health", description="健康检查端点")
    performance_tracking: bool = Field(default=True, description="性能跟踪")

    class Config:
        env_prefix = "PERFECT21_MONITORING_"
        case_sensitive = False


class TaskExecutionConfig(BaseModel):
    """任务执行配置"""
    max_parallel_tasks: int = Field(default=5, ge=1, le=50, description="最大并行任务数")
    default_timeout: int = Field(default=300, ge=10, le=3600, description="默认超时时间（秒）")
    max_timeout: int = Field(default=1800, ge=60, le=7200, description="最大超时时间（秒）")
    result_cache_ttl: int = Field(default=3600, ge=60, le=86400, description="结果缓存TTL（秒）")

    class Config:
        env_prefix = "PERFECT21_TASK_"
        case_sensitive = False


class GitWorkflowConfig(BaseModel):
    """Git工作流配置"""
    enabled: bool = Field(default=True, description="启用Git工作流")
    auto_hooks: bool = Field(default=True, description="自动Git钩子")
    branch_protection: bool = Field(default=False, description="分支保护")
    require_pr_review: bool = Field(default=False, description="需要PR审查")

    class Config:
        env_prefix = "PERFECT21_GIT_WORKFLOW_"
        case_sensitive = False


class FileUploadConfig(BaseModel):
    """文件上传配置"""
    enabled: bool = Field(default=True, description="启用文件上传")
    max_file_size: str = Field(default="10MB", description="最大文件大小")
    allowed_extensions: List[str] = Field(default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt"], description="允许的文件扩展名")
    upload_dir: str = Field(default="uploads", description="上传目录")

    @validator('max_file_size')
    def validate_file_size(cls, v):
        if not v.endswith(('B', 'KB', 'MB', 'GB')):
            raise ValueError('文件大小必须以B、KB、MB或GB结尾')
        return v

    class Config:
        env_prefix = "PERFECT21_UPLOAD_"
        case_sensitive = False


class EmailConfig(BaseModel):
    """邮件配置"""
    enabled: bool = Field(default=False, description="启用邮件")
    smtp_server: Optional[str] = Field(default=None, description="SMTP服务器")
    smtp_port: int = Field(default=587, ge=1, le=65535, description="SMTP端口")
    smtp_user: Optional[str] = Field(default=None, description="SMTP用户")
    smtp_password: Optional[SecretStr] = Field(default=None, description="SMTP密码")
    from_address: Optional[str] = Field(default=None, description="发件人地址")

    class Config:
        env_prefix = "PERFECT21_EMAIL_"
        case_sensitive = False


class BackupConfig(BaseModel):
    """备份配置"""
    enabled: bool = Field(default=False, description="启用备份")
    schedule: str = Field(default="0 2 * * *", description="备份计划（cron格式）")
    retention_days: int = Field(default=30, ge=1, le=365, description="保留天数")
    backup_dir: str = Field(default="backups", description="备份目录")

    class Config:
        env_prefix = "PERFECT21_BACKUP_"
        case_sensitive = False


class Perfect21ConfigModel(BaseModel):
    """Perfect21完整配置模型"""
    perfect21: Perfect21Config = Field(default_factory=Perfect21Config)
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    auth: AuthConfig = Field(default_factory=lambda: AuthConfig(jwt_secret_key="dev-secret-key-change-in-production"))
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    task_execution: TaskExecutionConfig = Field(default_factory=TaskExecutionConfig)
    git_workflow: GitWorkflowConfig = Field(default_factory=GitWorkflowConfig)
    file_upload: FileUploadConfig = Field(default_factory=FileUploadConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"  # 禁止额外字段


class TypeSafeConfigManager:
    """类型安全的配置管理器"""

    def __init__(self, project_root: str = None):
        """
        初始化配置管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self._config: Optional[Perfect21ConfigModel] = None
        self._config_lock = threading.RLock()
        self._watchers: List[callable] = []
        self._validation_errors: List[str] = []

        # 配置文件路径
        self.config_dir = self.project_root / "config"
        self.default_config_file = self.config_dir / "default.yaml"
        self.env_config_file = self.config_dir / f"{self._get_environment()}.yaml"
        self.user_config_file = self.project_root / ".perfect21" / "config.yaml"
        self.env_file = self.project_root / ".env"

        # 加载配置
        self._load_and_validate_config()

    def _get_environment(self) -> EnvironmentType:
        """获取当前环境"""
        env_str = os.getenv("PERFECT21_ENV", "development")
        try:
            return EnvironmentType(env_str)
        except ValueError:
            logger.warning(f"无效的环境类型: {env_str}，使用默认值: development")
            return EnvironmentType.DEVELOPMENT

    def _load_and_validate_config(self):
        """加载并验证所有配置"""
        with self._config_lock:
            try:
                # 1. 收集所有配置源
                config_data = {}

                # 2. 加载默认配置文件
                if self.default_config_file.exists():
                    default_config = self._load_yaml_file(self.default_config_file)
                    self._deep_merge(config_data, default_config)

                # 3. 加载环境特定配置文件
                if self.env_config_file.exists():
                    env_config = self._load_yaml_file(self.env_config_file)
                    self._deep_merge(config_data, env_config)

                # 4. 加载用户配置文件
                if self.user_config_file.exists():
                    user_config = self._load_yaml_file(self.user_config_file)
                    self._deep_merge(config_data, user_config)

                # 5. 使用Pydantic进行类型验证和环境变量注入
                self._config = Perfect21ConfigModel(**config_data)
                self._validation_errors = []

                logger.info("配置加载和验证完成")

            except ValidationError as e:
                self._validation_errors = [str(error) for error in e.errors()]
                logger.error(f"配置验证失败: {e}")
                # 使用默认配置
                self._config = Perfect21ConfigModel()

            except Exception as e:
                logger.error(f"配置加载失败: {e}")
                self._validation_errors = [str(e)]
                # 使用默认配置
                self._config = Perfect21ConfigModel()

    def _get_default_config(self) -> Perfect21ConfigModel:
        """获取默认配置"""
        return Perfect21ConfigModel()

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                logger.debug(f"加载配置文件: {file_path}")
                return config
        except Exception as e:
            logger.warning(f"加载配置文件失败 {file_path}: {e}")
            return {}

    def _resolve_secret_values(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的密钥值"""

        def resolve_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value is None:
                    logger.warning(f"环境变量 {env_var} 未设置")
                    return value
                return env_value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value

        return resolve_value(config_data)

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """设置嵌套配置值"""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]):
        """深度合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default=None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            配置值
        """
        with self._config_lock:
            if self._config is None:
                return default

            keys = key.split('.')
            value = self._config

            try:
                for k in keys:
                    if hasattr(value, k):
                        value = getattr(value, k)
                    else:
                        return default
                return value
            except (AttributeError, KeyError):
                return default

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值（类型安全）

        Args:
            key: 配置键
            value: 配置值

        Returns:
            是否设置成功
        """
        with self._config_lock:
            if self._config is None:
                return False

            try:
                keys = key.split('.')
                if len(keys) == 1:
                    # 顶级配置项
                    if hasattr(self._config, keys[0]):
                        # 获取字段类型并验证
                        field_info = self._config.__fields__[keys[0]]
                        if field_info.type_:
                            validated_value = field_info.type_(value)
                            setattr(self._config, keys[0], validated_value)
                            self._notify_watchers(key, value)
                            return True
                elif len(keys) == 2:
                    # 嵌套配置项
                    section = getattr(self._config, keys[0], None)
                    if section and hasattr(section, keys[1]):
                        setattr(section, keys[1], value)
                        self._notify_watchers(key, value)
                        return True
                return False
            except (ValidationError, ValueError, AttributeError) as e:
                logger.error(f"设置配置值失败: {e}")
                return False

    def get_section(self, section: str) -> Optional[BaseModel]:
        """
        获取配置节（类型安全）

        Args:
            section: 节名称

        Returns:
            配置节对象
        """
        with self._config_lock:
            if self._config is None:
                return None
            return getattr(self._config, section, None)

    def reload(self) -> bool:
        """
        重新加载配置

        Returns:
            是否成功
        """
        try:
            self._load_and_validate_config()
            self._notify_watchers('*', None)
            logger.info("配置重新加载成功")
            return len(self._validation_errors) == 0
        except Exception as e:
            logger.error(f"配置重新加载失败: {e}")
            return False

    def save_user_config(self, config: Union[Dict[str, Any], Perfect21ConfigModel]) -> bool:
        """
        保存用户配置（类型安全）

        Args:
            config: 用户配置

        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            self.user_config_file.parent.mkdir(parents=True, exist_ok=True)

            # 如果是Pydantic模型，转换为字典
            if isinstance(config, Perfect21ConfigModel):
                config_dict = config.dict(exclude_unset=True, by_alias=True)
                # 处理SecretStr字段
                config_dict = self._serialize_secrets(config_dict)
            else:
                config_dict = config

            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"用户配置已保存: {self.user_config_file}")
            return True

        except Exception as e:
            logger.error(f"保存用户配置失败: {e}")
            return False

    def export_config(self, file_path: str, include_secrets: bool = False) -> bool:
        """
        导出当前配置（类型安全）

        Args:
            file_path: 导出文件路径
            include_secrets: 是否包含敏感信息

        Returns:
            是否成功
        """
        try:
            with self._config_lock:
                if self._config is None:
                    return False

                config_dict = self._config.dict(exclude_unset=True, by_alias=True)

                if not include_secrets:
                    config_dict = self._mask_secrets(config_dict)
                else:
                    config_dict = self._serialize_secrets(config_dict)

                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"配置已导出: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False

    def validate_config(self) -> List[str]:
        """
        验证配置（由Pydantic自动完成）

        Returns:
            错误列表
        """
        return self._validation_errors.copy()

    def add_watcher(self, callback: callable) -> None:
        """
        添加配置变更监听器

        Args:
            callback: 回调函数，签名为 callback(key, value)
        """
        self._watchers.append(callback)

    def remove_watcher(self, callback: callable) -> None:
        """
        移除配置变更监听器

        Args:
            callback: 要移除的回调函数
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def _notify_watchers(self, key: str, value: Any) -> None:
        """通知配置变更监听器"""
        for watcher in self._watchers:
            try:
                watcher(key, value)
            except Exception as e:
                logger.warning(f"配置变更通知失败: {e}")

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'project_root': str(self.project_root),
            'environment': self._get_environment().value,
            'config_files': {
                'default': str(self.default_config_file) if self.default_config_file.exists() else None,
                'environment': str(self.env_config_file) if self.env_config_file.exists() else None,
                'user': str(self.user_config_file) if self.user_config_file.exists() else None,
                'env': str(self.env_file) if self.env_file.exists() else None
            },
            'validation_errors': self.validate_config(),
            'watcher_count': len(self._watchers),
            'config_loaded': self._config is not None,
            'last_loaded': datetime.now().isoformat() if self._config else None
        }

    def get_typed_config(self) -> Optional[Perfect21ConfigModel]:
        """获取类型化配置对象"""
        with self._config_lock:
            return self._config

    def _serialize_secrets(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """序列化SecretStr字段"""
        def process_value(value):
            if hasattr(value, 'get_secret_value'):
                return value.get_secret_value()
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value

        return process_value(config_dict)

    def _mask_secrets(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """遮蔽敏感信息"""
        secret_fields = {'password', 'secret', 'key', 'token'}

        def mask_value(key, value):
            if any(secret_field in key.lower() for secret_field in secret_fields):
                return "***MASKED***"
            elif isinstance(value, dict):
                return {k: mask_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [mask_value(str(i), item) for i, item in enumerate(value)]
            return value

        return {k: mask_value(k, v) for k, v in config_dict.items()}

    def create_config_schema(self) -> Dict[str, Any]:
        """创建配置schema文档"""
        return Perfect21ConfigModel.schema()

    def validate_partial_config(self, config_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证部分配置数据"""
        try:
            # 创建临时配置对象进行验证
            temp_config = Perfect21ConfigModel(**config_data)
            return True, []
        except ValidationError as e:
            errors = [f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}" for error in e.errors()]
            return False, errors


# 为了向后兼容，保留原有的ConfigManager类
class ConfigManager(TypeSafeConfigManager):
    """向后兼容的配置管理器"""

    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节（返回字典格式以保持兼容性）"""
        typed_section = super().get_section(section)
        if typed_section:
            return typed_section.dict()
        return {}

    def create_typed_configs(self) -> Dict[str, Any]:
        """创建类型化配置对象（向后兼容）"""
        if self._config:
            return {
                'perfect21': self._config.perfect21,
                'git': self._config.git,
                'performance': self._config.performance,
                'cli': self._config.cli,
                'logging': self._config.logging,
                'server': self._config.server,
                'database': self._config.database,
                'cache': self._config.cache,
                'auth': self._config.auth,
                'rate_limiting': self._config.rate_limiting,
                'security': self._config.security,
                'monitoring': self._config.monitoring,
                'task_execution': self._config.task_execution,
                'git_workflow': self._config.git_workflow,
                'file_upload': self._config.file_upload,
                'email': self._config.email,
                'backup': self._config.backup
            }
        return {}


# 全局配置管理器实例
_config_manager: Optional[TypeSafeConfigManager] = None


def get_config_manager(project_root: str = None) -> TypeSafeConfigManager:
    """获取配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = TypeSafeConfigManager(project_root)
    return _config_manager


def get_config(key: str, default=None) -> Any:
    """便捷函数：获取配置值"""
    manager = get_config_manager()
    return manager.get(key, default)


def set_config(key: str, value: Any) -> bool:
    """便捷函数：设置配置值（类型安全）"""
    manager = get_config_manager()
    return manager.set(key, value)


def get_typed_config() -> Optional[Perfect21ConfigModel]:
    """便捷函数：获取完整的类型化配置"""
    manager = get_config_manager()
    return manager.get_typed_config()


def validate_config_data(config_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """便捷函数：验证配置数据"""
    manager = get_config_manager()
    return manager.validate_partial_config(config_data)


def get_config_schema() -> Dict[str, Any]:
    """便捷函数：获取配置schema"""
    manager = get_config_manager()
    return manager.create_config_schema()


# 类型安全的配置访问器
def get_server_config() -> Optional[ServerConfig]:
    """获取服务器配置"""
    config = get_typed_config()
    return config.server if config else None


def get_database_config() -> Optional[DatabaseConfig]:
    """获取数据库配置"""
    config = get_typed_config()
    return config.database if config else None


def get_auth_config() -> Optional[AuthConfig]:
    """获取认证配置"""
    config = get_typed_config()
    return config.auth if config else None


def get_cache_config() -> Optional[CacheConfig]:
    """获取缓存配置"""
    config = get_typed_config()
    return config.cache if config else None