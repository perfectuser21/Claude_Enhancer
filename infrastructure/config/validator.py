#!/usr/bin/env python3
"""
配置验证器 - 高级类型安全验证
提供详细的验证报告和修复建议
"""

import re
import json
from typing import Dict, Any, List, Optional, Union, Type, get_type_hints
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from pydantic import BaseModel, ValidationError, Field
    from pydantic.fields import FieldInfo
except ImportError:
    raise ImportError("Please install pydantic: pip install pydantic[dotenv]")

from .types import (
    ConfigValidationError, ConfigValidationResult,
    EnvironmentName, LogLevelName, DatabaseTypeName, CacheTypeName
)

# ====================== 验证规则定义 ======================

@dataclass
class ValidationRule:
    """验证规则"""
    field_path: str
    rule_type: str
    parameters: Dict[str, Any]
    error_message: str
    severity: str = "error"  # error, warning, info

@dataclass
class ValidationContext:
    """验证上下文"""
    environment: str
    config_source: str
    timestamp: datetime
    strict_mode: bool = True

class ConfigValidator:
    """高级配置验证器"""

    def __init__(self, strict_mode: bool = True):
        """
        初始化验证器

        Args:
            strict_mode: 严格模式，启用所有验证规则
        """
        self.strict_mode = strict_mode
        self.custom_rules: List[ValidationRule] = []
        self.warnings: List[str] = []
        self.errors: List[ConfigValidationError] = []

    def add_custom_rule(self, rule: ValidationRule) -> None:
        """添加自定义验证规则"""
        self.custom_rules.append(rule)

    def validate_config_data(
        self,
        config_data: Dict[str, Any],
        config_model: Type[BaseModel],
        context: Optional[ValidationContext] = None
    ) -> ConfigValidationResult:
        """
        验证配置数据

        Args:
            config_data: 配置数据
            config_model: Pydantic配置模型
            context: 验证上下文

        Returns:
            验证结果
        """
        self.errors.clear()
        self.warnings.clear()

        if context is None:
            context = ValidationContext(
                environment="development",
                config_source="unknown",
                timestamp=datetime.now(),
                strict_mode=self.strict_mode
            )

        try:
            # 1. Pydantic模型验证
            validated_config = config_model(**config_data)

            # 2. 环境特定验证
            self._validate_environment_specific(config_data, context)

            # 3. 业务逻辑验证
            self._validate_business_logic(validated_config, context)

            # 4. 安全性验证
            self._validate_security(validated_config, context)

            # 5. 性能配置验证
            self._validate_performance(validated_config, context)

            # 6. 自定义规则验证
            self._validate_custom_rules(config_data, context)

        except ValidationError as e:
            for error in e.errors():
                self.errors.append(ConfigValidationError(
                    field=".".join(str(loc) for loc in error['loc']),
                    message=error['msg'],
                    value=error.get('input'),
                    expected_type=error['type']
                ))

        return ConfigValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )

    def _validate_environment_specific(
        self,
        config_data: Dict[str, Any],
        context: ValidationContext
    ) -> None:
        """验证环境特定配置"""

        # 获取环境和各配置节
        env = context.environment
        perfect21_config = config_data.get('perfect21', {})
        server_config = config_data.get('server', {})
        database_config = config_data.get('database', {})
        auth_config = config_data.get('auth', {})
        security_config = config_data.get('security', {})

        # 生产环境特定验证
        if env == "production":
            self._validate_production_config(
                perfect21_config, server_config, database_config,
                auth_config, security_config
            )

        # 开发环境特定验证
        elif env == "development":
            self._validate_development_config(
                perfect21_config, server_config, database_config,
                auth_config, security_config
            )

    def _validate_production_config(
        self,
        perfect21_config: Dict[str, Any],
        server_config: Dict[str, Any],
        database_config: Dict[str, Any],
        auth_config: Dict[str, Any],
        security_config: Dict[str, Any]
    ) -> None:
        """验证生产环境配置"""

        # 服务器配置验证
        if server_config.get('debug', False):
            self.errors.append(ConfigValidationError(
                field="server.debug",
                message="生产环境不应启用调试模式",
                value=True,
                expected_type="false"
            ))

        if server_config.get('reload', False):
            self.warnings.append("生产环境建议禁用自动重载")

        # 认证配置验证
        jwt_secret = auth_config.get('jwt_secret_key', '')
        if jwt_secret in ['dev-secret-key-change-in-production', 'secret']:
            self.errors.append(ConfigValidationError(
                field="auth.jwt_secret_key",
                message="生产环境必须使用强密钥",
                value=jwt_secret,
                expected_type="strong secret key"
            ))

        if auth_config.get('access_token_expire_hours', 0) > 24:
            self.warnings.append("生产环境建议令牌过期时间不超过24小时")

        # 安全配置验证
        allowed_origins = security_config.get('allowed_origins', [])
        if '*' in allowed_origins:
            self.errors.append(ConfigValidationError(
                field="security.allowed_origins",
                message="生产环境不应允许所有CORS源",
                value=allowed_origins,
                expected_type="specific domains"
            ))

        if not security_config.get('secure_cookies', True):
            self.errors.append(ConfigValidationError(
                field="security.secure_cookies",
                message="生产环境必须启用安全Cookie",
                value=False,
                expected_type="true"
            ))

    def _validate_development_config(
        self,
        perfect21_config: Dict[str, Any],
        server_config: Dict[str, Any],
        database_config: Dict[str, Any],
        auth_config: Dict[str, Any],
        security_config: Dict[str, Any]
    ) -> None:
        """验证开发环境配置"""

        # 开发环境建议
        if not server_config.get('reload', True):
            self.warnings.append("开发环境建议启用自动重载")

        if not server_config.get('debug', True):
            self.warnings.append("开发环境建议启用调试模式")

        # 数据库路径检查
        if database_config.get('type') == 'sqlite':
            db_path = database_config.get('path', '')
            if db_path and not db_path.startswith('data/'):
                self.warnings.append("开发环境建议SQLite数据库放在data目录下")

    def _validate_business_logic(
        self,
        config: BaseModel,
        context: ValidationContext
    ) -> None:
        """验证业务逻辑"""

        # 检查数据库和缓存配置的一致性
        self._validate_database_cache_consistency(config)

        # 检查认证和安全配置的一致性
        self._validate_auth_security_consistency(config)

        # 检查任务执行配置的合理性
        self._validate_task_execution_logic(config)

    def _validate_database_cache_consistency(self, config: BaseModel) -> None:
        """验证数据库和缓存配置一致性"""

        database_config = getattr(config, 'database', None)
        cache_config = getattr(config, 'cache', None)

        if not database_config or not cache_config:
            return

        # 如果使用SQLite，建议使用文件缓存而不是Redis
        if (database_config.type == 'sqlite' and
            cache_config.type == 'redis'):
            self.warnings.append(
                "使用SQLite数据库时，建议使用file缓存而不是Redis缓存"
            )

        # 如果使用PostgreSQL/MySQL，建议使用Redis缓存
        if (database_config.type in ['postgresql', 'mysql'] and
            cache_config.type == 'memory'):
            self.warnings.append(
                "使用分布式数据库时，建议使用Redis缓存而不是内存缓存"
            )

    def _validate_auth_security_consistency(self, config: BaseModel) -> None:
        """验证认证和安全配置一致性"""

        auth_config = getattr(config, 'auth', None)
        security_config = getattr(config, 'security', None)

        if not auth_config or not security_config:
            return

        # 如果启用安全Cookie，JWT过期时间应该合理
        if (security_config.secure_cookies and
            auth_config.access_token_expire_hours > 72):
            self.warnings.append(
                "启用安全Cookie时，建议JWT过期时间不超过72小时"
            )

        # 如果允许凭证，应该限制CORS源
        if (security_config.cors_credentials and
            '*' in security_config.allowed_origins):
            self.errors.append(ConfigValidationError(
                field="security.cors_credentials",
                message="允许凭证时不能使用通配符CORS源",
                value=True,
                expected_type="specific origins"
            ))

    def _validate_task_execution_logic(self, config: BaseModel) -> None:
        """验证任务执行配置逻辑"""

        task_config = getattr(config, 'task_execution', None)
        performance_config = getattr(config, 'performance', None)

        if not task_config or not performance_config:
            return

        # 任务并发数不应超过性能配置的最大并发数
        if (task_config.max_parallel_tasks >
            performance_config.max_concurrent_commands):
            self.warnings.append(
                "任务并发数建议不超过性能配置的最大并发数"
            )

        # 最大超时时间应该大于默认超时时间
        if task_config.max_timeout <= task_config.default_timeout:
            self.errors.append(ConfigValidationError(
                field="task_execution.max_timeout",
                message="最大超时时间必须大于默认超时时间",
                value=task_config.max_timeout,
                expected_type=f"greater than {task_config.default_timeout}"
            ))

    def _validate_security(self, config: BaseModel, context: ValidationContext) -> None:
        """验证安全配置"""

        auth_config = getattr(config, 'auth', None)
        security_config = getattr(config, 'security', None)

        if auth_config:
            # JWT密钥强度检查
            if hasattr(auth_config, 'jwt_secret_key'):
                secret = auth_config.jwt_secret_key
                if hasattr(secret, 'get_secret_value'):
                    secret_value = secret.get_secret_value()
                else:
                    secret_value = str(secret)

                self._validate_jwt_secret_strength(secret_value)

            # 密码策略检查
            if auth_config.password_min_length < 8:
                self.warnings.append("建议密码最小长度至少为8位")

            # 锁定策略检查
            if auth_config.max_login_attempts > 10:
                self.warnings.append("建议最大登录尝试次数不超过10次")

        if security_config:
            # CORS配置检查
            self._validate_cors_configuration(security_config)

            # 安全头检查
            self._validate_security_headers(security_config)

    def _validate_jwt_secret_strength(self, secret: str) -> None:
        """验证JWT密钥强度"""

        if len(secret) < 32:
            self.errors.append(ConfigValidationError(
                field="auth.jwt_secret_key",
                message="JWT密钥长度至少32位",
                value=f"length={len(secret)}",
                expected_type="length>=32"
            ))

        # 检查是否包含多种字符类型
        has_upper = bool(re.search(r'[A-Z]', secret))
        has_lower = bool(re.search(r'[a-z]', secret))
        has_digit = bool(re.search(r'\d', secret))
        has_special = bool(re.search(r'[!@#$%^&*(),.?\":{}|<>]', secret))

        strength_score = sum([has_upper, has_lower, has_digit, has_special])

        if strength_score < 3:
            self.warnings.append(
                "JWT密钥建议包含大写字母、小写字母、数字和特殊字符"
            )

    def _validate_cors_configuration(self, security_config) -> None:
        """验证CORS配置"""

        allowed_origins = getattr(security_config, 'allowed_origins', [])
        cors_credentials = getattr(security_config, 'cors_credentials', False)

        # 检查危险的CORS配置
        if '*' in allowed_origins and cors_credentials:
            self.errors.append(ConfigValidationError(
                field="security.allowed_origins",
                message="允许凭证时不能使用通配符源",
                value=allowed_origins,
                expected_type="specific domains"
            ))

        # 检查本地开发配置
        localhost_patterns = ['localhost', '127.0.0.1', '0.0.0.0']
        has_localhost = any(
            any(pattern in origin for pattern in localhost_patterns)
            for origin in allowed_origins if isinstance(origin, str)
        )

        if has_localhost and cors_credentials:
            self.warnings.append(
                "生产环境不建议允许localhost跨域访问"
            )

    def _validate_security_headers(self, security_config) -> None:
        """验证安全头配置"""

        if not getattr(security_config, 'content_type_nosniff', True):
            self.warnings.append("建议启用Content-Type nosniff保护")

        if not getattr(security_config, 'frame_deny', True):
            self.warnings.append("建议启用X-Frame-Options保护")

        if not getattr(security_config, 'xss_protection', True):
            self.warnings.append("建议启用XSS保护")

    def _validate_performance(self, config: BaseModel, context: ValidationContext) -> None:
        """验证性能配置"""

        performance_config = getattr(config, 'performance', None)
        server_config = getattr(config, 'server', None)

        if not performance_config or not server_config:
            return

        # 检查并发数和工作进程数的关系
        max_concurrent = performance_config.max_concurrent_commands
        workers = getattr(server_config, 'workers', 1)

        if max_concurrent < workers:
            self.warnings.append(
                "最大并发命令数建议不少于工作进程数"
            )

        # 检查内存限制
        memory_limit = performance_config.memory_limit_mb
        if memory_limit < 256:
            self.warnings.append("内存限制建议不少于256MB")

        if workers > 1 and memory_limit < workers * 128:
            self.warnings.append(
                f"多进程模式下建议内存限制至少{workers * 128}MB"
            )

    def _validate_custom_rules(
        self,
        config_data: Dict[str, Any],
        context: ValidationContext
    ) -> None:
        """验证自定义规则"""

        for rule in self.custom_rules:
            try:
                self._apply_validation_rule(rule, config_data, context)
            except Exception as e:
                self.warnings.append(f"自定义规则验证失败: {rule.field_path} - {e}")

    def _apply_validation_rule(
        self,
        rule: ValidationRule,
        config_data: Dict[str, Any],
        context: ValidationContext
    ) -> None:
        """应用验证规则"""

        # 获取字段值
        field_value = self._get_nested_value(config_data, rule.field_path)

        # 根据规则类型进行验证
        if rule.rule_type == "range":
            min_val = rule.parameters.get('min')
            max_val = rule.parameters.get('max')
            if not (min_val <= field_value <= max_val):
                if rule.severity == "error":
                    self.errors.append(ConfigValidationError(
                        field=rule.field_path,
                        message=rule.error_message,
                        value=field_value,
                        expected_type=f"{min_val}-{max_val}"
                    ))
                else:
                    self.warnings.append(f"{rule.field_path}: {rule.error_message}")

        elif rule.rule_type == "regex":
            pattern = rule.parameters.get('pattern')
            if not re.match(pattern, str(field_value)):
                if rule.severity == "error":
                    self.errors.append(ConfigValidationError(
                        field=rule.field_path,
                        message=rule.error_message,
                        value=field_value,
                        expected_type=f"pattern: {pattern}"
                    ))
                else:
                    self.warnings.append(f"{rule.field_path}: {rule.error_message}")

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字段值"""
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def generate_validation_report(
        self,
        result: ConfigValidationResult,
        output_format: str = "text"
    ) -> str:
        """
        生成验证报告

        Args:
            result: 验证结果
            output_format: 输出格式 (text|json|html)

        Returns:
            格式化的报告
        """

        if output_format == "json":
            return json.dumps(asdict(result), indent=2, ensure_ascii=False)

        elif output_format == "html":
            return self._generate_html_report(result)

        else:  # text
            return self._generate_text_report(result)

    def _generate_text_report(self, result: ConfigValidationResult) -> str:
        """生成文本格式报告"""

        lines = []
        lines.append("=" * 60)
        lines.append("Perfect21 配置验证报告")
        lines.append("=" * 60)
        lines.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"总体状态: {'✓ 通过' if result.is_valid else '✗ 失败'}")
        lines.append(f"错误数量: {len(result.errors)}")
        lines.append(f"警告数量: {len(result.warnings)}")
        lines.append("")

        if result.errors:
            lines.append("错误详情:")
            lines.append("-" * 40)
            for i, error in enumerate(result.errors, 1):
                lines.append(f"{i}. 字段: {error.field}")
                lines.append(f"   消息: {error.message}")
                lines.append(f"   当前值: {error.value}")
                lines.append(f"   期望类型: {error.expected_type}")
                lines.append("")

        if result.warnings:
            lines.append("警告详情:")
            lines.append("-" * 40)
            for i, warning in enumerate(result.warnings, 1):
                lines.append(f"{i}. {warning}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_html_report(self, result: ConfigValidationResult) -> str:
        """生成HTML格式报告"""

        status_color = "green" if result.is_valid else "red"
        status_text = "通过" if result.is_valid else "失败"

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Perfect21 配置验证报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .status {{ color: {status_color}; font-weight: bold; }}
                .errors {{ background: #ffebee; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .warnings {{ background: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .item {{ margin: 10px 0; padding: 10px; border-left: 3px solid #ddd; }}
                .error-item {{ border-left-color: #f44336; }}
                .warning-item {{ border-left-color: #ff9800; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Perfect21 配置验证报告</h1>
                <p>验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>总体状态: <span class="status">{status_text}</span></p>
                <p>错误数量: {len(result.errors)} | 警告数量: {len(result.warnings)}</p>
            </div>
        """

        if result.errors:
            html += """
            <div class="errors">
                <h2>错误详情</h2>
            """
            for error in result.errors:
                html += f"""
                <div class="item error-item">
                    <strong>字段:</strong> {error.field}<br>
                    <strong>消息:</strong> {error.message}<br>
                    <strong>当前值:</strong> {error.value}<br>
                    <strong>期望类型:</strong> {error.expected_type}
                </div>
                """
            html += "</div>"

        if result.warnings:
            html += """
            <div class="warnings">
                <h2>警告详情</h2>
            """
            for warning in result.warnings:
                html += f"""
                <div class="item warning-item">
                    {warning}
                </div>
                """
            html += "</div>"

        html += """
        </body>
        </html>
        """

        return html

# ====================== 预定义验证规则 ======================

def get_default_validation_rules() -> List[ValidationRule]:
    """获取默认验证规则"""

    return [
        ValidationRule(
            field_path="server.port",
            rule_type="range",
            parameters={"min": 1024, "max": 65535},
            error_message="端口号必须在1024-65535范围内",
            severity="error"
        ),
        ValidationRule(
            field_path="auth.password_min_length",
            rule_type="range",
            parameters={"min": 6, "max": 128},
            error_message="密码最小长度必须在6-128范围内",
            severity="error"
        ),
        ValidationRule(
            field_path="database.path",
            rule_type="regex",
            parameters={"pattern": r"^[^<>:\"|?*]+\.db$"},
            error_message="SQLite数据库文件名格式无效",
            severity="warning"
        ),
    ]