#!/usr/bin/env python3
"""
Perfect21 API服务器启动脚本
支持开发和生产环境配置
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.config import config
from modules.logger import setup_logging, log_info, log_error
from modules.database import db_manager
from modules.cache import cache_manager

def check_dependencies():
    """检查依赖项"""
    try:
        import fastapi
        import uvicorn
        import jwt
        import sqlite3
        log_info("依赖项检查通过")
        return True
    except ImportError as e:
        log_error(f"依赖项缺失: {e}")
        return False

def initialize_database():
    """初始化数据库"""
    try:
        db_manager.initialize()
        log_info("数据库初始化成功")
        return True
    except Exception as e:
        log_error("数据库初始化失败", e)
        return False

def check_environment():
    """检查环境配置"""
    try:
        # 检查必要的环境变量
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not jwt_secret and config.get('perfect21.mode') == 'production':
            log_error("生产环境必须设置JWT_SECRET_KEY环境变量")
            return False

        # 检查目录权限
        data_dir = config.get('perfect21.data_dir', 'data')
        logs_dir = config.get('perfect21.logs_dir', 'logs')

        for directory in [data_dir, logs_dir]:
            os.makedirs(directory, exist_ok=True)
            if not os.access(directory, os.W_OK):
                log_error(f"目录没有写权限: {directory}")
                return False

        log_info("环境检查通过")
        return True
    except Exception as e:
        log_error("环境检查失败", e)
        return False

def setup_logging_config(log_level: str = None):
    """设置日志配置"""
    try:
        log_level = log_level or config.get('logging.level', 'INFO')
        log_file = config.get('logging.file', 'logs/api.log')

        setup_logging(log_level, log_file)
        log_info(f"日志配置完成: 级别={log_level}, 文件={log_file}")
        return True
    except Exception as e:
        print(f"日志配置失败: {e}")
        return False

def create_admin_user():
    """创建管理员用户"""
    try:
        from features.auth_system import AuthManager

        auth_manager = AuthManager()

        # 检查是否已存在管理员
        admin_user = auth_manager.user_service.find_user("admin")
        if admin_user:
            log_info("管理员用户已存在")
            return True

        # 创建管理员用户
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin123!')
        result = auth_manager.register(
            username="admin",
            email="admin@perfect21.local",
            password=admin_password,
            role="admin"
        )

        if result['success']:
            log_info("管理员用户创建成功")
            log_info(f"管理员账户: admin / {admin_password}")
            return True
        else:
            log_error(f"管理员用户创建失败: {result['message']}")
            return False

    except Exception as e:
        log_error("创建管理员用户失败", e)
        return False

def run_health_check():
    """运行健康检查"""
    try:
        # 数据库健康检查
        db_stats = db_manager.get_database_stats()
        if 'error' in db_stats:
            log_error("数据库健康检查失败")
            return False

        # 缓存健康检查
        cache_health = cache_manager.health_check()
        if cache_health['status'] != 'healthy':
            log_error("缓存健康检查失败")
            return False

        log_info("健康检查通过")
        return True
    except Exception as e:
        log_error("健康检查失败", e)
        return False

def start_server(host: str = None, port: int = None, workers: int = None,
                reload: bool = False, debug: bool = False):
    """启动API服务器"""
    try:
        import uvicorn

        # 从配置获取默认值
        host = host or config.get('server.host', '127.0.0.1')
        port = port or config.get('server.port', 8000)
        workers = workers or config.get('server.workers', 1)

        # 生产环境配置
        if config.get('perfect21.mode') == 'production':
            reload = False
            debug = False
            if workers == 1:
                workers = 4

        log_info(f"启动API服务器: {host}:{port} (workers={workers})")

        # 启动服务器
        uvicorn.run(
            "api.rest_server:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level="debug" if debug else "info",
            access_log=True
        )

    except Exception as e:
        log_error("启动服务器失败", e)
        sys.exit(1)

def show_system_info():
    """显示系统信息"""
    print("=" * 60)
    print("Perfect21 后端API服务器")
    print("=" * 60)

    try:
        # 基本信息
        print(f"版本: {config.get('perfect21.version', 'Unknown')}")
        print(f"模式: {config.get('perfect21.mode', 'Unknown')}")
        print(f"Python版本: {sys.version.split()[0]}")

        # 数据库信息
        db_stats = db_manager.get_database_stats()
        print(f"数据库类型: {db_stats.get('database_type', 'Unknown')}")
        print(f"数据库大小: {db_stats.get('database_size', 0) // 1024}KB")

        # 缓存信息
        cache_stats = cache_manager.get_stats()
        print(f"缓存类型: {cache_stats.get('type', 'Unknown')}")

        # 端点信息
        server_host = config.get('server.host', '127.0.0.1')
        server_port = config.get('server.port', 8000)
        print(f"API地址: http://{server_host}:{server_port}")
        print(f"API文档: http://{server_host}:{server_port}/docs")

    except Exception as e:
        print(f"获取系统信息失败: {e}")

    print("=" * 60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 API服务器启动脚本')

    parser.add_argument('--host', default=None, help='服务器地址')
    parser.add_argument('--port', type=int, default=None, help='端口号')
    parser.add_argument('--workers', type=int, default=None, help='工作进程数')
    parser.add_argument('--reload', action='store_true', help='开发模式自动重载')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default=None, help='日志级别')
    parser.add_argument('--skip-checks', action='store_true', help='跳过启动检查')
    parser.add_argument('--create-admin', action='store_true', help='仅创建管理员用户')
    parser.add_argument('--health-check', action='store_true', help='仅运行健康检查')
    parser.add_argument('--info', action='store_true', help='显示系统信息')

    args = parser.parse_args()

    # 设置日志
    if not setup_logging_config(args.log_level):
        sys.exit(1)

    # 显示系统信息
    if args.info:
        show_system_info()
        return

    # 仅运行健康检查
    if args.health_check:
        if run_health_check():
            print("✅ 健康检查通过")
            sys.exit(0)
        else:
            print("❌ 健康检查失败")
            sys.exit(1)

    # 仅创建管理员用户
    if args.create_admin:
        if not args.skip_checks:
            if not check_dependencies() or not initialize_database():
                sys.exit(1)

        if create_admin_user():
            print("✅ 管理员用户创建成功")
            sys.exit(0)
        else:
            print("❌ 管理员用户创建失败")
            sys.exit(1)

    # 正常启动流程
    print("🚀 启动Perfect21 API服务器...")

    if not args.skip_checks:
        print("📋 运行启动检查...")

        # 检查依赖项
        if not check_dependencies():
            print("❌ 依赖项检查失败")
            sys.exit(1)

        # 检查环境
        if not check_environment():
            print("❌ 环境检查失败")
            sys.exit(1)

        # 初始化数据库
        if not initialize_database():
            print("❌ 数据库初始化失败")
            sys.exit(1)

        # 创建管理员用户
        if not create_admin_user():
            print("⚠️  管理员用户创建失败，但继续启动")

        # 运行健康检查
        if not run_health_check():
            print("❌ 健康检查失败")
            sys.exit(1)

        print("✅ 启动检查通过")

    # 显示系统信息
    show_system_info()

    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        debug=args.debug
    )

if __name__ == "__main__":
    main()