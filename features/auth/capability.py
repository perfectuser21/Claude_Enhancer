#!/usr/bin/env python3
"""
Perfect21 用户登录API 能力定义
将用户认证API注册到Perfect21能力发现系统
"""

import os
import sys
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from features.capability_discovery.capability import CapabilityDefinition


def get_auth_api_capability() -> CapabilityDefinition:
    """
    获取用户登录API的能力定义

    Returns:
        CapabilityDefinition: 认证API能力定义
    """

    return CapabilityDefinition(
        name="auth_api",
        description="企业级用户认证API - 提供完整的登录、令牌管理和会话控制功能",
        version="1.0.0",
        category="security",
        priority=9,  # 高优先级，安全相关

        # 依赖项
        dependencies=[
            "flask>=2.0.0",
            "PyJWT>=2.0.0",
            "bcrypt>=3.2.0",
            "SQLAlchemy>=1.4.0",
            "redis>=4.0.0",
            "pydantic>=1.8.0",
            "psycopg2-binary>=2.9.0",  # PostgreSQL支持
            "flask-cors>=3.0.0"
        ],

        # API端点定义
        endpoints=[
            {
                "path": "/api/v1/auth/login",
                "method": "POST",
                "description": "用户登录认证",
                "auth_required": False,
                "rate_limit": "10/minute",
                "parameters": [
                    {"name": "username", "type": "string", "required": True},
                    {"name": "password", "type": "string", "required": True},
                    {"name": "remember_me", "type": "boolean", "required": False},
                    {"name": "captcha_token", "type": "string", "required": False},
                    {"name": "device_fingerprint", "type": "string", "required": False}
                ],
                "responses": {
                    "200": "登录成功，返回JWT令牌",
                    "401": "认证失败",
                    "429": "请求过于频繁"
                }
            },
            {
                "path": "/api/v1/auth/validate",
                "method": "POST",
                "description": "验证JWT令牌有效性",
                "auth_required": False,
                "rate_limit": "100/minute",
                "parameters": [
                    {"name": "token", "type": "string", "required": True}
                ],
                "responses": {
                    "200": "令牌验证结果",
                    "400": "参数错误"
                }
            },
            {
                "path": "/api/v1/auth/refresh",
                "method": "POST",
                "description": "刷新访问令牌",
                "auth_required": False,
                "rate_limit": "30/minute",
                "parameters": [
                    {"name": "refresh_token", "type": "string", "required": True}
                ],
                "responses": {
                    "200": "令牌刷新成功",
                    "401": "刷新令牌无效"
                }
            },
            {
                "path": "/api/v1/auth/logout",
                "method": "POST",
                "description": "用户登出",
                "auth_required": True,
                "rate_limit": "20/minute",
                "parameters": [],
                "responses": {
                    "200": "登出成功",
                    "401": "未认证"
                }
            },
            {
                "path": "/api/v1/auth/profile",
                "method": "GET",
                "description": "获取用户档案",
                "auth_required": True,
                "rate_limit": "60/minute",
                "parameters": [],
                "responses": {
                    "200": "用户档案信息",
                    "401": "未认证"
                }
            },
            {
                "path": "/api/v1/auth/health",
                "method": "GET",
                "description": "API健康检查",
                "auth_required": False,
                "rate_limit": "200/minute",
                "parameters": [],
                "responses": {
                    "200": "服务健康",
                    "503": "服务不可用"
                }
            }
        ],

        # 功能特性
        features=[
            "JWT令牌认证机制",
            "密码bcrypt哈希存储",
            "账户锁定与解锁",
            "IP地址限流保护",
            "会话生命周期管理",
            "基于角色的权限控制",
            "完整的审计日志记录",
            "令牌自动刷新机制",
            "验证码防暴力破解",
            "设备指纹识别",
            "多数据库支持",
            "Redis会话存储",
            "RESTful API设计",
            "OpenAPI 3.1规范",
            "CORS跨域支持",
            "Docker容器化部署"
        ],

        # 安全特性
        security_features=[
            "bcrypt密码哈希算法（12轮加盐）",
            "HS256 JWT签名验证",
            "访问令牌短期有效（1小时）",
            "刷新令牌轮换机制",
            "IP地址频率限制",
            "账户自动锁定保护",
            "登录失败计数器",
            "会话令牌绑定验证",
            "完整审计日志追踪",
            "SQL注入防护",
            "XSS攻击防护",
            "CSRF保护机制",
            "HTTPS传输加密",
            "安全HTTP头设置",
            "设备指纹验证",
            "验证码集成支持"
        ],

        # 配置要求
        config_required=[
            {
                "name": "jwt_secret_key",
                "description": "JWT签名密钥",
                "type": "string",
                "required": True,
                "min_length": 64,
                "example": "your-super-secret-256-bit-key"
            },
            {
                "name": "database_url",
                "description": "数据库连接URL",
                "type": "string",
                "required": True,
                "example": "postgresql://user:password@localhost/perfect21_auth"
            },
            {
                "name": "redis_host",
                "description": "Redis服务器地址",
                "type": "string",
                "required": False,
                "default": "localhost"
            },
            {
                "name": "redis_port",
                "description": "Redis服务器端口",
                "type": "integer",
                "required": False,
                "default": 6379
            },
            {
                "name": "api_host",
                "description": "API服务器绑定地址",
                "type": "string",
                "required": False,
                "default": "0.0.0.0"
            },
            {
                "name": "api_port",
                "description": "API服务器端口",
                "type": "integer",
                "required": False,
                "default": 8080
            },
            {
                "name": "max_login_attempts",
                "description": "最大登录失败次数",
                "type": "integer",
                "required": False,
                "default": 5
            },
            {
                "name": "lockout_duration",
                "description": "账户锁定时长（秒）",
                "type": "integer",
                "required": False,
                "default": 900
            }
        ],

        # 健康检查配置
        health_check_endpoint="/api/v1/auth/health",
        health_check_interval=30,

        # 使用示例
        usage_examples=[
            {
                "title": "基本登录",
                "description": "使用用户名和密码登录",
                "code": """
curl -X POST https://api.perfect21.dev/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "john_doe",
    "password": "secure_password123",
    "remember_me": false
  }'
"""
            },
            {
                "title": "令牌验证",
                "description": "验证JWT令牌有效性",
                "code": """
curl -X POST https://api.perfect21.dev/v1/auth/validate \\
  -H "Content-Type: application/json" \\
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
"""
            },
            {
                "title": "获取用户档案",
                "description": "获取当前认证用户信息",
                "code": """
curl -X GET https://api.perfect21.dev/v1/auth/profile \\
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
"""
            },
            {
                "title": "Python客户端",
                "description": "Python客户端集成示例",
                "code": """
from features.auth_api.client import Perfect21AuthClient

client = Perfect21AuthClient('https://api.perfect21.dev/v1')

# 登录
result = await client.login('username', 'password')
if result.success:
    access_token = result.access_token

    # 使用令牌发送请求
    response = await client.make_authenticated_request('/api/some-endpoint')
"""
            }
        ],

        # 部署配置
        deployment_config={
            "docker_image": "perfect21/auth-api:1.0.0",
            "ports": [8080],
            "environment_variables": [
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "REDIS_URL",
                "FLASK_ENV"
            ],
            "volumes": [
                "/app/logs:/logs",
                "/app/config:/config"
            ],
            "dependencies": [
                "postgres:13",
                "redis:6-alpine"
            ]
        },

        # 监控配置
        monitoring_config={
            "metrics_endpoint": "/api/v1/auth/metrics",
            "log_level": "INFO",
            "log_file": "/logs/auth-api.log",
            "alert_webhooks": [
                "/webhooks/auth-failure",
                "/webhooks/account-lockout",
                "/webhooks/high-error-rate"
            ]
        },

        # 文档配置
        documentation={
            "openapi_spec": "/features/auth_api/openapi_specification.yaml",
            "readme": "/features/auth_api/README.md",
            "api_docs_url": "https://docs.perfect21.dev/api/auth",
            "postman_collection": "/features/auth_api/postman_collection.json"
        },

        # CLI命令
        cli_commands=[
            {
                "name": "auth-api",
                "description": "认证API管理命令",
                "subcommands": [
                    {
                        "name": "start",
                        "description": "启动API服务器",
                        "options": ["--host", "--port", "--debug"]
                    },
                    {
                        "name": "status",
                        "description": "检查API服务状态",
                        "options": ["--detailed"]
                    },
                    {
                        "name": "test",
                        "description": "运行API测试套件",
                        "options": ["--coverage", "--verbose"]
                    },
                    {
                        "name": "init-db",
                        "description": "初始化数据库表结构",
                        "options": ["--force"]
                    },
                    {
                        "name": "create-user",
                        "description": "创建管理员用户",
                        "options": ["--username", "--email", "--role"]
                    }
                ]
            }
        ],

        # 测试配置
        test_config={
            "test_database_url": "sqlite:///test_auth.db",
            "test_redis_db": 1,
            "test_jwt_secret": "test-secret-key",
            "unit_tests": "features/auth_api/tests/test_unit.py",
            "integration_tests": "features/auth_api/tests/test_integration.py",
            "performance_tests": "features/auth_api/tests/test_performance.py",
            "coverage_threshold": 90
        }
    )


def register_auth_api():
    """
    注册认证API到Perfect21能力系统

    Returns:
        dict: 注册结果
    """
    try:
        from features.capability_discovery.registry import get_capability_registry

        # 获取能力注册表
        registry = get_capability_registry()

        # 注册认证API能力
        capability = get_auth_api_capability()
        result = registry.register_capability(capability)

        if result['success']:
            print("✅ 认证API能力注册成功")
            return {
                'success': True,
                'message': '认证API能力已成功注册到Perfect21系统',
                'capability_name': 'auth_api',
                'version': '1.0.0'
            }
        else:
            print(f"❌ 认证API能力注册失败: {result['message']}")
            return {
                'success': False,
                'message': f"注册失败: {result['message']}"
            }

    except Exception as e:
        print(f"❌ 认证API能力注册异常: {e}")
        return {
            'success': False,
            'message': f"注册异常: {str(e)}"
        }


def get_auth_api_briefing() -> str:
    """
    获取认证API能力简报
    用于Perfect21系统的能力注入

    Returns:
        str: 能力简报文本
    """

    return """
🔐 Perfect21 用户认证API (auth_api v1.0.0)

## 核心功能
- JWT令牌认证系统（HS256签名）
- 企业级密码安全（bcrypt 12轮）
- 智能账户保护（失败锁定）
- IP限流防护（10次/5分钟）
- 会话生命周期管理
- 基于角色的权限控制
- 完整审计日志追踪

## API端点
POST /api/v1/auth/login     - 用户登录认证
POST /api/v1/auth/validate  - 令牌有效性验证
POST /api/v1/auth/refresh   - 刷新访问令牌
POST /api/v1/auth/logout    - 安全登出会话
GET  /api/v1/auth/profile   - 获取用户档案
GET  /api/v1/auth/health    - API健康检查

## 安全特性
- 防暴力破解（5次失败锁定15分钟）
- 验证码集成（3次失败后启用）
- 设备指纹识别
- SQL注入/XSS防护
- HTTPS强制传输
- 令牌轮换机制

## 支持的用户角色
- admin: 系统管理员（全部权限）
- developer: 开发人员（项目+代码权限）
- user: 普通用户（基础读写权限）
- guest: 访客用户（只读权限）

## Perfect21集成
- CLI命令: python3 main/cli.py auth-api start
- 能力发现: 自动注册到Perfect21系统
- 监控集成: 健康检查和指标收集
- 日志集成: 统一日志格式和审计

## 快速使用
```bash
# 启动认证API服务
python3 main/cli.py auth-api start --port 8080

# 测试登录
curl -X POST localhost:8080/api/v1/auth/login \\
  -d '{"username":"admin","password":"password"}'
```

Perfect21认证API为整个平台提供统一、安全、可扩展的身份认证服务，
确保所有用户操作都经过严格的身份验证和权限控制。
"""


def get_cli_integration() -> Dict[str, Any]:
    """
    获取CLI集成配置
    用于将认证API命令集成到Perfect21 CLI

    Returns:
        dict: CLI集成配置
    """

    return {
        'command_name': 'auth-api',
        'description': '用户认证API管理',
        'handler_function': 'handle_auth_api',
        'subcommands': [
            {
                'name': 'start',
                'description': '启动认证API服务器',
                'arguments': [
                    {'name': '--host', 'help': 'API服务器地址', 'default': '0.0.0.0'},
                    {'name': '--port', 'help': 'API服务器端口', 'type': int, 'default': 8080},
                    {'name': '--debug', 'help': '启用调试模式', 'action': 'store_true'},
                    {'name': '--workers', 'help': 'Gunicorn工作进程数', 'type': int, 'default': 4}
                ]
            },
            {
                'name': 'status',
                'description': '检查API服务状态',
                'arguments': [
                    {'name': '--url', 'help': 'API服务URL', 'default': 'http://localhost:8080'},
                    {'name': '--detailed', 'help': '显示详细状态', 'action': 'store_true'}
                ]
            },
            {
                'name': 'test',
                'description': '运行API测试套件',
                'arguments': [
                    {'name': '--unit', 'help': '只运行单元测试', 'action': 'store_true'},
                    {'name': '--integration', 'help': '只运行集成测试', 'action': 'store_true'},
                    {'name': '--performance', 'help': '运行性能测试', 'action': 'store_true'},
                    {'name': '--coverage', 'help': '生成覆盖率报告', 'action': 'store_true'}
                ]
            },
            {
                'name': 'init-db',
                'description': '初始化数据库',
                'arguments': [
                    {'name': '--force', 'help': '强制重新创建表', 'action': 'store_true'},
                    {'name': '--sample-data', 'help': '创建示例数据', 'action': 'store_true'}
                ]
            },
            {
                'name': 'create-user',
                'description': '创建用户账户',
                'arguments': [
                    {'name': 'username', 'help': '用户名'},
                    {'name': 'email', 'help': '邮箱地址'},
                    {'name': '--password', 'help': '用户密码'},
                    {'name': '--role', 'help': '用户角色', 'choices': ['admin', 'developer', 'user', 'guest'], 'default': 'user'},
                    {'name': '--active', 'help': '激活账户', 'action': 'store_true', 'default': True}
                ]
            },
            {
                'name': 'metrics',
                'description': '显示API指标',
                'arguments': [
                    {'name': '--live', 'help': '实时监控', 'action': 'store_true'},
                    {'name': '--export', 'help': '导出指标数据', 'action': 'store_true'}
                ]
            }
        ]
    }


if __name__ == '__main__':
    # 直接运行时注册能力
    result = register_auth_api()
    if result['success']:
        print("\n" + get_auth_api_briefing())
    else:
        print(f"注册失败: {result['message']}")