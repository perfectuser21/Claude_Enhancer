"""
Claude Enhancer 认证服务配置模块
统一管理所有配置参数
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "Claude Enhancer Auth Service"
    VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # 服务器配置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8080, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")

    # 安全配置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")

    # 数据库配置
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")

    # Redis配置
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_POOL_SIZE: int = Field(default=50, env="REDIS_POOL_SIZE")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")

    # JWT配置
    JWT_ALGORITHM: str = Field(default="RS256", env="JWT_ALGORITHM")
    JWT_PRIVATE_KEY: Optional[str] = Field(default=None, env="JWT_PRIVATE_KEY")
    JWT_PUBLIC_KEY: Optional[str] = Field(default=None, env="JWT_PUBLIC_KEY")
    JWT_PRIVATE_KEY_PATH: str = Field(
        default="/secrets/jwt_private_key.pem", env="JWT_PRIVATE_KEY_PATH"
    )
    JWT_PUBLIC_KEY_PATH: str = Field(
        default="/secrets/jwt_public_key.pem", env="JWT_PUBLIC_KEY_PATH"
    )
    JWT_ACCESS_TOKEN_TTL: int = Field(default=900, env="JWT_ACCESS_TOKEN_TTL")  # 15分钟
    JWT_REFRESH_TOKEN_TTL: int = Field(
        default=604800, env="JWT_REFRESH_TOKEN_TTL"
    )  # 7天
    JWT_ISSUER: str = Field(default="claude-enhancer-auth", env="JWT_ISSUER")
    JWT_AUDIENCE: str = Field(default="claude-enhancer-api", env="JWT_AUDIENCE")
    JWT_KEY_ROTATION_INTERVAL: int = Field(
        default=86400, env="JWT_KEY_ROTATION_INTERVAL"
    )  # 24小时

    # 密码配置
    PASSWORD_MIN_LENGTH: int = Field(default=12, env="PASSWORD_MIN_LENGTH")
    PASSWORD_MAX_LENGTH: int = Field(default=128, env="PASSWORD_MAX_LENGTH")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(
        default=True, env="PASSWORD_REQUIRE_UPPERCASE"
    )
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(
        default=True, env="PASSWORD_REQUIRE_LOWERCASE"
    )
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    PASSWORD_HISTORY_COUNT: int = Field(default=5, env="PASSWORD_HISTORY_COUNT")
    PASSWORD_PEPPER: str = Field(..., env="PASSWORD_PEPPER")
    PASSWORD_BCRYPT_ROUNDS: int = Field(default=12, env="PASSWORD_BCRYPT_ROUNDS")

    # MFA配置
    MFA_TOTP_ISSUER: str = Field(default="Claude Enhancer", env="MFA_TOTP_ISSUER")
    MFA_TOTP_WINDOW: int = Field(default=1, env="MFA_TOTP_WINDOW")  # ±30秒
    MFA_BACKUP_CODES_COUNT: int = Field(default=10, env="MFA_BACKUP_CODES_COUNT")
    MFA_SMS_VALID_MINUTES: int = Field(default=5, env="MFA_SMS_VALID_MINUTES")
    MFA_EMAIL_VALID_MINUTES: int = Field(default=10, env="MFA_EMAIL_VALID_MINUTES")

    # 会话配置
    SESSION_TTL: int = Field(default=1800, env="SESSION_TTL")  # 30分钟
    SESSION_MAX_PER_USER: int = Field(default=5, env="SESSION_MAX_PER_USER")
    SESSION_CLEANUP_INTERVAL: int = Field(
        default=3600, env="SESSION_CLEANUP_INTERVAL"
    )  # 1小时

    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT_REQUESTS: int = Field(
        default=100, env="RATE_LIMIT_DEFAULT_REQUESTS"
    )
    RATE_LIMIT_DEFAULT_WINDOW: int = Field(default=60, env="RATE_LIMIT_DEFAULT_WINDOW")
    RATE_LIMIT_AUTH_REQUESTS: int = Field(default=10, env="RATE_LIMIT_AUTH_REQUESTS")
    RATE_LIMIT_AUTH_WINDOW: int = Field(default=60, env="RATE_LIMIT_AUTH_WINDOW")
    RATE_LIMIT_LOGIN_REQUESTS: int = Field(default=5, env="RATE_LIMIT_LOGIN_REQUESTS")
    RATE_LIMIT_LOGIN_WINDOW: int = Field(default=300, env="RATE_LIMIT_LOGIN_WINDOW")

    # 账户锁定配置
    ACCOUNT_LOCKOUT_ENABLED: bool = Field(default=True, env="ACCOUNT_LOCKOUT_ENABLED")
    ACCOUNT_LOCKOUT_ATTEMPTS: int = Field(default=5, env="ACCOUNT_LOCKOUT_ATTEMPTS")
    ACCOUNT_LOCKOUT_DURATION: int = Field(
        default=3600, env="ACCOUNT_LOCKOUT_DURATION"
    )  # 1小时
    ACCOUNT_LOCKOUT_INCREMENT: bool = Field(
        default=True, env="ACCOUNT_LOCKOUT_INCREMENT"
    )

    # 邮件配置
    EMAIL_ENABLED: bool = Field(default=True, env="EMAIL_ENABLED")
    EMAIL_SMTP_HOST: str = Field(default="localhost", env="EMAIL_SMTP_HOST")
    EMAIL_SMTP_PORT: int = Field(default=587, env="EMAIL_SMTP_PORT")
    EMAIL_SMTP_USERNAME: Optional[str] = Field(default=None, env="EMAIL_SMTP_USERNAME")
    EMAIL_SMTP_PASSWORD: Optional[str] = Field(default=None, env="EMAIL_SMTP_PASSWORD")
    EMAIL_SMTP_TLS: bool = Field(default=True, env="EMAIL_SMTP_TLS")
    EMAIL_FROM_ADDRESS: str = Field(
        default="noreply@claude-enhancer.com", env="EMAIL_FROM_ADDRESS"
    )
    EMAIL_FROM_NAME: str = Field(default="Claude Enhancer", env="EMAIL_FROM_NAME")
    EMAIL_VERIFICATION_TTL: int = Field(
        default=3600, env="EMAIL_VERIFICATION_TTL"
    )  # 1小时
    EMAIL_RESET_PASSWORD_TTL: int = Field(
        default=3600, env="EMAIL_RESET_PASSWORD_TTL"
    )  # 1小时

    # SMS配置
    SMS_ENABLED: bool = Field(default=True, env="SMS_ENABLED")
    SMS_PROVIDER: str = Field(default="twilio", env="SMS_PROVIDER")
    SMS_API_KEY: Optional[str] = Field(default=None, env="SMS_API_KEY")
    SMS_API_SECRET: Optional[str] = Field(default=None, env="SMS_API_SECRET")
    SMS_FROM_NUMBER: Optional[str] = Field(default=None, env="SMS_FROM_NUMBER")
    SMS_DAILY_LIMIT: int = Field(default=20, env="SMS_DAILY_LIMIT")

    # RabbitMQ配置
    RABBITMQ_URL: str = Field(..., env="RABBITMQ_URL")
    RABBITMQ_EXCHANGE: str = Field(default="claude-enhancer.events", env="RABBITMQ_EXCHANGE")
    RABBITMQ_QUEUE_PREFIX: str = Field(
        default="auth-service", env="RABBITMQ_QUEUE_PREFIX"
    )
    RABBITMQ_POOL_SIZE: int = Field(default=10, env="RABBITMQ_POOL_SIZE")

    # gRPC配置
    GRPC_PORT: int = Field(default=50051, env="GRPC_PORT")
    GRPC_MAX_WORKERS: int = Field(default=10, env="GRPC_MAX_WORKERS")
    GRPC_KEEPALIVE_TIME: int = Field(default=10000, env="GRPC_KEEPALIVE_TIME")
    GRPC_KEEPALIVE_TIMEOUT: int = Field(default=3000, env="GRPC_KEEPALIVE_TIMEOUT")

    # 监控配置
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_PORT: int = Field(default=8000, env="METRICS_PORT")
    JAEGER_ENABLED: bool = Field(default=True, env="JAEGER_ENABLED")
    JAEGER_ENDPOINT: str = Field(
        default="http://jaeger-collector:14268/api/traces", env="JAEGER_ENDPOINT"
    )
    JAEGER_AGENT_HOST: str = Field(default="jaeger-agent", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: int = Field(default=6831, env="JAEGER_AGENT_PORT")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json 或 text
    LOG_FILE: Optional[str] = Field(default="/var/log/auth-service.log", env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(default=100, env="LOG_MAX_SIZE")  # MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # 缓存配置
    CACHE_TTL_DEFAULT: int = Field(default=300, env="CACHE_TTL_DEFAULT")  # 5分钟
    CACHE_TTL_USER_PERMISSIONS: int = Field(
        default=300, env="CACHE_TTL_USER_PERMISSIONS"
    )
    CACHE_TTL_USER_ROLES: int = Field(default=600, env="CACHE_TTL_USER_ROLES")
    CACHE_TTL_PERMISSION_CHECK: int = Field(
        default=300, env="CACHE_TTL_PERMISSION_CHECK"
    )
    CACHE_LOCAL_SIZE: int = Field(default=1000, env="CACHE_LOCAL_SIZE")
    CACHE_LOCAL_TTL: int = Field(default=60, env="CACHE_LOCAL_TTL")  # 1分钟

    # API配置
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    API_TIMEOUT: int = Field(default=30, env="API_TIMEOUT")
    API_MAX_REQUEST_SIZE: int = Field(default=10, env="API_MAX_REQUEST_SIZE")  # MB

    # 安全头配置
    SECURITY_HEADERS_ENABLED: bool = Field(default=True, env="SECURITY_HEADERS_ENABLED")
    HSTS_MAX_AGE: int = Field(default=31536000, env="HSTS_MAX_AGE")  # 1年
    CSP_POLICY: str = Field(
        default="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        env="CSP_POLICY",
    )

    # 开发配置
    RELOAD: bool = Field(default=False, env="RELOAD")
    RELOAD_DIRS: List[str] = Field(default=["app"], env="RELOAD_DIRS")

    # OAuth2配置
    OAUTH2_ENABLED: bool = Field(default=False, env="OAUTH2_ENABLED")
    OAUTH2_GOOGLE_CLIENT_ID: Optional[str] = Field(
        default=None, env="OAUTH2_GOOGLE_CLIENT_ID"
    )
    OAUTH2_GOOGLE_CLIENT_SECRET: Optional[str] = Field(
        default=None, env="OAUTH2_GOOGLE_CLIENT_SECRET"
    )
    OAUTH2_MICROSOFT_CLIENT_ID: Optional[str] = Field(
        default=None, env="OAUTH2_MICROSOFT_CLIENT_ID"
    )
    OAUTH2_MICROSOFT_CLIENT_SECRET: Optional[str] = Field(
        default=None, env="OAUTH2_MICROSOFT_CLIENT_SECRET"
    )

    # 前端配置
    FRONTEND_URL: str = Field(default="https://app.claude-enhancer.com", env="FRONTEND_URL")
    FRONTEND_VERIFY_EMAIL_PATH: str = Field(
        default="/verify-email", env="FRONTEND_VERIFY_EMAIL_PATH"
    )
    FRONTEND_RESET_PASSWORD_PATH: str = Field(
        default="/reset-password", env="FRONTEND_RESET_PASSWORD_PATH"
    )

    # 数据保护配置
    DATA_ENCRYPTION_KEY: str = Field(..., env="DATA_ENCRYPTION_KEY")
    GDPR_COMPLIANCE: bool = Field(default=True, env="GDPR_COMPLIANCE")
    DATA_RETENTION_DAYS: int = Field(default=2555, env="DATA_RETENTION_DAYS")  # 7年
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=2555, env="AUDIT_LOG_RETENTION_DAYS")

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("RELOAD_DIRS", pre=True)
    def parse_reload_dirs(cls, v):
        if isinstance(v, str):
            return [dir.strip() for dir in v.split(",")]
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("LOG_FORMAT")
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()

    @validator("JWT_ALGORITHM")
    def validate_jwt_algorithm(cls, v):
        valid_algorithms = ["RS256", "RS384", "RS512", "HS256", "HS384", "HS512"]
        if v not in valid_algorithms:
            raise ValueError(f"JWT algorithm must be one of: {valid_algorithms}")
        return v

    @validator("SMS_PROVIDER")
    def validate_sms_provider(cls, v):
        valid_providers = ["twilio", "aws_sns", "aliyun"]
        if v.lower() not in valid_providers:
            raise ValueError(f"SMS provider must be one of: {valid_providers}")
        return v.lower()

    @property
    def database_config(self) -> dict:
        """数据库连接配置"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_recycle": self.DATABASE_POOL_RECYCLE,
        }

    @property
    def redis_config(self) -> dict:
        """Redis连接配置"""
        return {
            "url": self.REDIS_URL,
            "password": self.REDIS_PASSWORD,
            "db": self.REDIS_DB,
            "pool_size": self.REDIS_POOL_SIZE,
            "timeout": self.REDIS_TIMEOUT,
        }

    @property
    def jwt_config(self) -> dict:
        """JWT配置"""
        return {
            "algorithm": self.JWT_ALGORITHM,
            "private_key": self.JWT_PRIVATE_KEY,
            "public_key": self.JWT_PUBLIC_KEY,
            "private_key_path": self.JWT_PRIVATE_KEY_PATH,
            "public_key_path": self.JWT_PUBLIC_KEY_PATH,
            "access_token_ttl": self.JWT_ACCESS_TOKEN_TTL,
            "refresh_token_ttl": self.JWT_REFRESH_TOKEN_TTL,
            "issuer": self.JWT_ISSUER,
            "audience": self.JWT_AUDIENCE,
            "key_rotation_interval": self.JWT_KEY_ROTATION_INTERVAL,
        }

    @property
    def email_config(self) -> dict:
        """邮件配置"""
        return {
            "enabled": self.EMAIL_ENABLED,
            "smtp_host": self.EMAIL_SMTP_HOST,
            "smtp_port": self.EMAIL_SMTP_PORT,
            "smtp_username": self.EMAIL_SMTP_USERNAME,
            "smtp_password": self.EMAIL_SMTP_PASSWORD,
            "smtp_tls": self.EMAIL_SMTP_TLS,
            "from_address": self.EMAIL_FROM_ADDRESS,
            "from_name": self.EMAIL_FROM_NAME,
            "verification_ttl": self.EMAIL_VERIFICATION_TTL,
            "reset_password_ttl": self.EMAIL_RESET_PASSWORD_TTL,
        }

    @property
    def security_config(self) -> dict:
        """安全配置"""
        return {
            "password_min_length": self.PASSWORD_MIN_LENGTH,
            "password_max_length": self.PASSWORD_MAX_LENGTH,
            "password_require_uppercase": self.PASSWORD_REQUIRE_UPPERCASE,
            "password_require_lowercase": self.PASSWORD_REQUIRE_LOWERCASE,
            "password_require_numbers": self.PASSWORD_REQUIRE_NUMBERS,
            "password_require_special": self.PASSWORD_REQUIRE_SPECIAL,
            "password_history_count": self.PASSWORD_HISTORY_COUNT,
            "password_pepper": self.PASSWORD_PEPPER,
            "bcrypt_rounds": self.PASSWORD_BCRYPT_ROUNDS,
            "account_lockout_enabled": self.ACCOUNT_LOCKOUT_ENABLED,
            "account_lockout_attempts": self.ACCOUNT_LOCKOUT_ATTEMPTS,
            "account_lockout_duration": self.ACCOUNT_LOCKOUT_DURATION,
            "rate_limit_enabled": self.RATE_LIMIT_ENABLED,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（带缓存）"""
    return Settings()


# 全局配置实例
settings = get_settings()


# 配置验证
def validate_config():
    """验证配置完整性"""
    errors = []

    # 必需的密钥检查
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY is required")

    if not settings.PASSWORD_PEPPER:
        errors.append("PASSWORD_PEPPER is required")

    if not settings.DATA_ENCRYPTION_KEY:
        errors.append("DATA_ENCRYPTION_KEY is required")

    # JWT密钥检查
    if settings.JWT_ALGORITHM.startswith("RS") and not (
        settings.JWT_PRIVATE_KEY or os.path.exists(settings.JWT_PRIVATE_KEY_PATH)
    ):
        errors.append("JWT private key is required for RS algorithms")

    # 数据库URL检查
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")

    # Redis URL检查
    if not settings.REDIS_URL:
        errors.append("REDIS_URL is required")

    # RabbitMQ URL检查
    if not settings.RABBITMQ_URL:
        errors.append("RABBITMQ_URL is required")

    if errors:
        raise ValueError(
            f"Configuration validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


# 启动时验证配置
if __name__ != "__main__":
    validate_config()
