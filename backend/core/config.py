#!/usr/bin/env python3
"""
应用程序配置管理
支持多环境配置和环境变量
"""

import os
from typing import Optional, List
from functools import lru_cache
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """应用程序设置"""

    # === 基础配置 ===
    APP_NAME: str = "Perfect21 Auth System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # === 服务器配置 ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # === 数据库配置 ===
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/perfect21_auth"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # === Redis配置 ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # === JWT配置 ===
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "perfect21-auth"
    JWT_AUDIENCE: str = "perfect21-users"

    # RSA密钥文件路径
    JWT_PRIVATE_KEY_PATH: str = "config/keys/jwt_private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "config/keys/jwt_public_key.pem"

    # === 密码配置 ===
    PASSWORD_BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_REQUIRE_COMPLEXITY: bool = True

    # === 安全配置 ===
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION: int = 30  # 分钟
    SESSION_TIMEOUT_HOURS: int = 24

    # === 速率限制 ===
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_LOGIN_REQUESTS_PER_MINUTE: int = 5

    # === CORS配置 ===
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]

    # === 日志配置 ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None

    # === 邮件配置 ===
    MAIL_SERVER: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM_ADDRESS: Optional[str] = None

    # === 监控配置 ===
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090

    # === 开发配置 ===
    RELOAD: bool = False
    ACCESS_LOG: bool = True

    @validator('REDIS_URL', pre=True)
    def build_redis_url(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v

        password_part = ""
        if values.get('REDIS_PASSWORD'):
            password_part = f":{values['REDIS_PASSWORD']}@"

        return f"redis://{password_part}{values.get('REDIS_HOST', 'localhost')}:{values.get('REDIS_PORT', 6379)}/{values.get('REDIS_DB', 0)}"

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v

    @validator('CORS_METHODS', pre=True)
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v

    @validator('CORS_HEADERS', pre=True)
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class DevelopmentSettings(Settings):
    """开发环境配置"""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"
    RELOAD: bool = True

    # 开发环境使用SQLite
    DATABASE_URL: str = "sqlite:///./data/perfect21_dev.db"

class ProductionSettings(Settings):
    """生产环境配置"""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    RELOAD: bool = False
    ACCESS_LOG: bool = True

    # 生产环境必须使用强密码
    @validator('JWT_SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == "your-super-secret-jwt-key-change-this-in-production":
            raise ValueError("生产环境必须修改JWT密钥")
        if len(v) < 32:
            raise ValueError("JWT密钥长度至少32位")
        return v

class TestSettings(Settings):
    """测试环境配置"""
    DEBUG: bool = True
    ENVIRONMENT: str = "test"
    DATABASE_URL: str = "sqlite:///:memory:"
    DATABASE_ECHO: bool = False

    # 测试环境使用内存Redis（需要fakeredis）
    REDIS_URL: str = "redis://localhost:6379/15"

    # 测试环境加快密码哈希速度
    PASSWORD_BCRYPT_ROUNDS: int = 4

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例"""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()

# 全局配置实例
settings = get_settings()