#!/usr/bin/env python3
"""
配置Schema生成器 - 自动生成JSON Schema和TypeScript定义
支持文档生成、IDE集成和自动补全
"""

import json
from typing import Dict, Any, Optional, List, Type, get_type_hints
from pathlib import Path
from datetime import datetime

try:
    from pydantic import BaseModel
    from pydantic.schema import schema
except ImportError:
    raise ImportError("Please install pydantic: pip install pydantic[dotenv]")

from .config_manager import Perfect21ConfigModel


class ConfigSchemaGenerator:
    """配置Schema生成器"""

    def __init__(self):
        """初始化生成器"""
        self.base_schema = None
        self.typescript_interfaces = []

    def generate_json_schema(
        self,
        config_model: Type[BaseModel] = Perfect21ConfigModel,
        title: str = "Perfect21 Configuration Schema",
        description: str = "JSON Schema for Perfect21 configuration validation"
    ) -> Dict[str, Any]:
        """
        生成JSON Schema

        Args:
            config_model: Pydantic配置模型
            title: Schema标题
            description: Schema描述

        Returns:
            JSON Schema字典
        """

        # 生成基础schema
        base_schema = schema([config_model], title=title, description=description)

        # 添加自定义属性
        enhanced_schema = self._enhance_schema(base_schema)

        # 添加示例
        enhanced_schema = self._add_examples(enhanced_schema)

        # 添加元数据
        enhanced_schema["$id"] = "https://perfect21.dev/schemas/config.json"
        enhanced_schema["$comment"] = f"Generated on {datetime.now().isoformat()}"

        self.base_schema = enhanced_schema
        return enhanced_schema

    def _enhance_schema(self, base_schema: Dict[str, Any]) -> Dict[str, Any]:
        """增强Schema定义"""

        enhanced = base_schema.copy()

        # 添加自定义格式验证
        definitions = enhanced.get('definitions', {})

        for def_name, definition in definitions.items():
            if 'properties' in definition:
                self._enhance_properties(definition['properties'])

        return enhanced

    def _enhance_properties(self, properties: Dict[str, Any]) -> None:
        """增强属性定义"""

        for prop_name, prop_def in properties.items():
            # 添加常见格式验证
            if 'email' in prop_name.lower():
                prop_def['format'] = 'email'

            elif 'url' in prop_name.lower() or 'endpoint' in prop_name.lower():
                prop_def['format'] = 'uri'

            elif 'password' in prop_name.lower() or 'secret' in prop_name.lower():
                prop_def['format'] = 'password'
                prop_def['writeOnly'] = True

            elif 'port' in prop_name.lower():
                prop_def['minimum'] = 1
                prop_def['maximum'] = 65535

            elif 'timeout' in prop_name.lower():
                prop_def['minimum'] = 1

            elif 'ttl' in prop_name.lower():
                prop_def['minimum'] = 0

            # 添加字段描述增强
            if prop_name == 'host':
                prop_def['examples'] = ['localhost', '127.0.0.1', '0.0.0.0']

            elif prop_name == 'level' and prop_def.get('enum'):
                prop_def['description'] = (
                    prop_def.get('description', '') +
                    ' 可选值: ' + ', '.join(prop_def['enum'])
                )

    def _add_examples(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """添加配置示例"""

        examples = {
            "development": self._get_development_example(),
            "production": self._get_production_example(),
            "testing": self._get_testing_example()
        }

        schema['examples'] = examples
        return schema

    def _get_development_example(self) -> Dict[str, Any]:
        """获取开发环境配置示例"""
        return {
            "perfect21": {
                "version": "3.1.0",
                "mode": "development",
                "enable_monitoring": True,
                "data_dir": "data",
                "logs_dir": "logs",
                "temp_dir": "temp"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "workers": 1,
                "reload": True,
                "debug": True,
                "max_connections": 100,
                "keepalive_timeout": 65
            },
            "database": {
                "type": "sqlite",
                "path": "data/development.db",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30
            },
            "cache": {
                "type": "memory",
                "default_ttl": 1800
            },
            "auth": {
                "jwt_secret_key": "dev-secret-key-change-in-production",
                "access_token_expire_hours": 24,
                "refresh_token_expire_days": 30,
                "password_min_length": 6,
                "max_login_attempts": 10,
                "lockout_duration_minutes": 5
            },
            "security": {
                "allowed_origins": ["*"],
                "cors_credentials": True,
                "secure_cookies": False,
                "session_secure": False
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/development.log"
            }
        }

    def _get_production_example(self) -> Dict[str, Any]:
        """获取生产环境配置示例"""
        return {
            "perfect21": {
                "version": "3.1.0",
                "mode": "production",
                "enable_monitoring": True,
                "data_dir": "/var/lib/perfect21/data",
                "logs_dir": "/var/log/perfect21",
                "temp_dir": "/tmp/perfect21"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "reload": False,
                "debug": False,
                "max_connections": 1000,
                "keepalive_timeout": 65
            },
            "database": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "name": "perfect21_prod",
                "user": "perfect21_user",
                "password": "${DATABASE_PASSWORD}",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30
            },
            "cache": {
                "type": "redis",
                "default_ttl": 3600,
                "redis_host": "localhost",
                "redis_port": 6379,
                "redis_db": 0,
                "redis_password": "${REDIS_PASSWORD}"
            },
            "auth": {
                "jwt_secret_key": "${JWT_SECRET_KEY}",
                "access_token_expire_hours": 1,
                "refresh_token_expire_days": 7,
                "password_min_length": 8,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 15
            },
            "security": {
                "allowed_origins": ["https://yourdomain.com"],
                "cors_credentials": True,
                "secure_cookies": True,
                "session_secure": True
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/perfect21/api.log"
            }
        }

    def _get_testing_example(self) -> Dict[str, Any]:
        """获取测试环境配置示例"""
        return {
            "perfect21": {
                "version": "3.1.0",
                "mode": "testing",
                "enable_monitoring": False,
                "data_dir": "test_data",
                "logs_dir": "test_logs",
                "temp_dir": "test_temp"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8001,
                "workers": 1,
                "reload": False,
                "debug": True,
                "max_connections": 10,
                "keepalive_timeout": 5
            },
            "database": {
                "type": "sqlite",
                "path": ":memory:",
                "pool_size": 1,
                "max_overflow": 0,
                "pool_timeout": 5
            },
            "cache": {
                "type": "memory",
                "default_ttl": 60
            },
            "auth": {
                "jwt_secret_key": "test-secret-key",
                "access_token_expire_hours": 1,
                "refresh_token_expire_days": 1,
                "password_min_length": 4,
                "max_login_attempts": 100,
                "lockout_duration_minutes": 1
            },
            "logging": {
                "level": "DEBUG"
            }
        }

    def generate_typescript_definitions(
        self,
        config_model: Type[BaseModel] = Perfect21ConfigModel,
        interface_name: str = "Perfect21Config"
    ) -> str:
        """
        生成TypeScript接口定义

        Args:
            config_model: Pydantic配置模型
            interface_name: 接口名称

        Returns:
            TypeScript定义字符串
        """

        if not self.base_schema:
            self.generate_json_schema(config_model)

        ts_definitions = []

        # 添加文件头注释
        ts_definitions.append("/**")
        ts_definitions.append(" * Perfect21 Configuration TypeScript Definitions")
        ts_definitions.append(f" * Generated on {datetime.now().isoformat()}")
        ts_definitions.append(" * DO NOT EDIT MANUALLY")
        ts_definitions.append(" */")
        ts_definitions.append("")

        # 生成枚举定义
        ts_definitions.extend(self._generate_enums())
        ts_definitions.append("")

        # 生成接口定义
        ts_definitions.extend(self._generate_interfaces(interface_name))

        return "\n".join(ts_definitions)

    def _generate_enums(self) -> List[str]:
        """生成TypeScript枚举"""

        enums = []

        # 环境类型枚举
        enums.extend([
            "export enum EnvironmentType {",
            "  DEVELOPMENT = 'development',",
            "  TESTING = 'testing',",
            "  STAGING = 'staging',",
            "  PRODUCTION = 'production'",
            "}",
            ""
        ])

        # 日志级别枚举
        enums.extend([
            "export enum LogLevel {",
            "  DEBUG = 'DEBUG',",
            "  INFO = 'INFO',",
            "  WARNING = 'WARNING',",
            "  ERROR = 'ERROR',",
            "  CRITICAL = 'CRITICAL'",
            "}",
            ""
        ])

        # 数据库类型枚举
        enums.extend([
            "export enum DatabaseType {",
            "  SQLITE = 'sqlite',",
            "  POSTGRESQL = 'postgresql',",
            "  MYSQL = 'mysql'",
            "}",
            ""
        ])

        # 缓存类型枚举
        enums.extend([
            "export enum CacheType {",
            "  MEMORY = 'memory',",
            "  FILE = 'file',",
            "  REDIS = 'redis'",
            "}",
            ""
        ])

        return enums

    def _generate_interfaces(self, root_interface_name: str) -> List[str]:
        """生成TypeScript接口"""

        interfaces = []

        # 生成子接口
        definitions = self.base_schema.get('definitions', {})

        for def_name, definition in definitions.items():
            if def_name == root_interface_name:
                continue

            interface_name = self._convert_to_interface_name(def_name)
            interface_lines = self._generate_single_interface(interface_name, definition)
            interfaces.extend(interface_lines)
            interfaces.append("")

        # 生成根接口
        root_definition = definitions.get(root_interface_name, {})
        root_interface_lines = self._generate_single_interface(root_interface_name, root_definition)
        interfaces.extend(root_interface_lines)

        return interfaces

    def _convert_to_interface_name(self, name: str) -> str:
        """转换为TypeScript接口名"""
        # 移除 "Config" 后缀，然后添加接口前缀
        clean_name = name.replace('Config', '').replace('Model', '')
        return f"I{clean_name}Config"

    def _generate_single_interface(self, interface_name: str, definition: Dict[str, Any]) -> List[str]:
        """生成单个TypeScript接口"""

        lines = []
        lines.append(f"export interface {interface_name} {{")

        properties = definition.get('properties', {})
        required = definition.get('required', [])

        for prop_name, prop_def in properties.items():
            prop_type = self._convert_to_typescript_type(prop_def)
            optional_marker = '' if prop_name in required else '?'
            description = prop_def.get('description', '')

            if description:
                lines.append(f"  /** {description} */")

            lines.append(f"  {prop_name}{optional_marker}: {prop_type};")

        lines.append("}")

        return lines

    def _convert_to_typescript_type(self, prop_def: Dict[str, Any]) -> str:
        """转换为TypeScript类型"""

        # 处理枚举类型
        if 'enum' in prop_def:
            enum_values = [f"'{value}'" for value in prop_def['enum']]
            return ' | '.join(enum_values)

        # 处理引用类型
        if '$ref' in prop_def:
            ref_name = prop_def['$ref'].split('/')[-1]
            return self._convert_to_interface_name(ref_name)

        # 处理基础类型
        prop_type = prop_def.get('type', 'any')

        if prop_type == 'string':
            return 'string'
        elif prop_type == 'integer' or prop_type == 'number':
            return 'number'
        elif prop_type == 'boolean':
            return 'boolean'
        elif prop_type == 'array':
            items_type = self._convert_to_typescript_type(prop_def.get('items', {}))
            return f'{items_type}[]'
        elif prop_type == 'object':
            # 检查是否有additionalProperties
            additional_props = prop_def.get('additionalProperties')
            if additional_props:
                if isinstance(additional_props, dict):
                    value_type = self._convert_to_typescript_type(additional_props)
                else:
                    value_type = 'any'
                return f'{{ [key: string]: {value_type} }}'
            else:
                return 'object'
        else:
            return 'any'

    def generate_vscode_settings(
        self,
        schema_file_path: str = "config/schema.json"
    ) -> Dict[str, Any]:
        """
        生成VSCode设置文件

        Args:
            schema_file_path: Schema文件相对路径

        Returns:
            VSCode设置字典
        """

        return {
            "json.schemas": [
                {
                    "fileMatch": [
                        "config/*.yaml",
                        "config/*.yml",
                        ".perfect21/config.yaml",
                        ".perfect21/config.yml"
                    ],
                    "url": f"./{schema_file_path}"
                }
            ],
            "yaml.schemas": {
                f"./{schema_file_path}": [
                    "config/*.yaml",
                    "config/*.yml",
                    ".perfect21/config.yaml",
                    ".perfect21/config.yml"
                ]
            },
            "files.associations": {
                "*.perfect21.yaml": "yaml",
                "*.perfect21.yml": "yaml"
            }
        }

    def save_schema_files(
        self,
        output_dir: Path,
        include_typescript: bool = True,
        include_vscode: bool = True
    ) -> Dict[str, str]:
        """
        保存所有Schema文件

        Args:
            output_dir: 输出目录
            include_typescript: 是否生成TypeScript定义
            include_vscode: 是否生成VSCode设置

        Returns:
            生成的文件路径字典
        """

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # 生成JSON Schema
        json_schema = self.generate_json_schema()
        schema_file = output_dir / "config-schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(json_schema, f, indent=2, ensure_ascii=False)
        generated_files['json_schema'] = str(schema_file)

        # 生成TypeScript定义
        if include_typescript:
            ts_definitions = self.generate_typescript_definitions()
            ts_file = output_dir / "config.d.ts"
            with open(ts_file, 'w', encoding='utf-8') as f:
                f.write(ts_definitions)
            generated_files['typescript'] = str(ts_file)

        # 生成VSCode设置
        if include_vscode:
            vscode_settings = self.generate_vscode_settings("config-schema.json")
            vscode_dir = output_dir / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            settings_file = vscode_dir / "settings.json"

            # 如果settings.json已存在，合并设置
            existing_settings = {}
            if settings_file.exists():
                try:
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        existing_settings = json.load(f)
                except json.JSONDecodeError:
                    pass

            # 合并设置
            merged_settings = {**existing_settings, **vscode_settings}

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(merged_settings, f, indent=2, ensure_ascii=False)
            generated_files['vscode_settings'] = str(settings_file)

        return generated_files

    def generate_documentation(self) -> str:
        """生成配置文档"""

        if not self.base_schema:
            self.generate_json_schema()

        doc_lines = []

        # 文档头部
        doc_lines.extend([
            "# Perfect21 配置文档",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 概述",
            "",
            "Perfect21 使用 YAML 格式的配置文件，支持多环境配置和环境变量注入。",
            "所有配置都经过严格的类型验证，确保配置的正确性和安全性。",
            "",
            "## 配置文件位置",
            "",
            "配置文件按以下优先级加载：",
            "",
            "1. `config/default.yaml` - 默认配置",
            "2. `config/{environment}.yaml` - 环境特定配置",
            "3. `.perfect21/config.yaml` - 用户配置",
            "4. 环境变量 - 最高优先级",
            "",
            "## 环境变量",
            "",
            "支持通过环境变量覆盖配置，前缀为 `PERFECT21_`：",
            "",
            "```bash",
            "export PERFECT21_SERVER_PORT=9000",
            "export PERFECT21_LOG_LEVEL=DEBUG",
            "export PERFECT21_DB_PASSWORD=secret",
            "```",
            "",
            "## 配置节详情",
            ""
        ])

        # 生成各配置节的文档
        definitions = self.base_schema.get('definitions', {})

        for def_name, definition in definitions.items():
            if def_name == 'Perfect21ConfigModel':
                continue

            section_name = def_name.lower().replace('config', '')
            doc_lines.append(f"### {section_name}")
            doc_lines.append("")

            description = definition.get('description', f'{section_name}相关配置')
            doc_lines.append(description)
            doc_lines.append("")

            # 配置项表格
            doc_lines.extend([
                "| 配置项 | 类型 | 默认值 | 描述 |",
                "|--------|------|--------|------|"
            ])

            properties = definition.get('properties', {})
            required = definition.get('required', [])

            for prop_name, prop_def in properties.items():
                prop_type = self._get_doc_type(prop_def)
                default_value = prop_def.get('default', '-')
                description = prop_def.get('description', '-')
                required_mark = " **(必需)**" if prop_name in required else ""

                doc_lines.append(
                    f"| `{prop_name}`{required_mark} | {prop_type} | `{default_value}` | {description} |"
                )

            doc_lines.append("")

        # 配置示例
        doc_lines.extend([
            "## 配置示例",
            "",
            "### 开发环境配置",
            "",
            "```yaml"
        ])

        # 添加开发环境示例
        import yaml
        dev_example = self._get_development_example()
        doc_lines.append(yaml.dump(dev_example, default_flow_style=False, allow_unicode=True))
        doc_lines.append("```")
        doc_lines.append("")

        # 生产环境示例
        doc_lines.extend([
            "### 生产环境配置",
            "",
            "```yaml"
        ])

        prod_example = self._get_production_example()
        doc_lines.append(yaml.dump(prod_example, default_flow_style=False, allow_unicode=True))
        doc_lines.append("```")

        return "\n".join(doc_lines)

    def _get_doc_type(self, prop_def: Dict[str, Any]) -> str:
        """获取文档用的类型字符串"""

        if 'enum' in prop_def:
            return f"enum: {', '.join(prop_def['enum'])}"

        prop_type = prop_def.get('type', 'any')

        if prop_type == 'string':
            return 'string'
        elif prop_type == 'integer':
            return 'integer'
        elif prop_type == 'number':
            return 'number'
        elif prop_type == 'boolean':
            return 'boolean'
        elif prop_type == 'array':
            return 'array'
        elif prop_type == 'object':
            return 'object'
        else:
            return prop_type