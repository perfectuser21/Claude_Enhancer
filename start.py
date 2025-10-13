#!/usr/bin/env python3
"""
FastAPI任务管理系统启动脚本
==========================

提供多种启动模式和环境配置
"""

import os
import sys
import click
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from src.core.config import get_settings, validate_config


@click.group()
def cli():
    """FastAPI任务管理系统 - 启动脚本"""
    pass


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="服务器主机地址")
@click.option("--port", "-p", default=8000, type=int, help="服务器端口")
@click.option("--reload", "-r", is_flag=True, help="启用热重载（开发模式）")
@click.option("--workers", "-w", default=1, type=int, help="工作进程数量")
@click.option("--log-level", default="info", help="日志级别")
def serve(host, port, reload, workers, log_level):
    """启动FastAPI服务器"""
    click.echo("🚀 启动任务管理系统...")

    # 验证配置
    if not validate_config():
        click.echo("❌ 配置验证失败，请检查配置文件", err=True)
        sys.exit(1)

    settings = get_settings()

    # 使用配置中的值，命令行参数优先级更高
    final_host = host if host != "0.0.0.0" else settings.HOST
    final_port = port if port != 8000 else settings.PORT
    final_reload = reload or settings.DEBUG

    click.echo(f"📡 服务器地址: http://{final_host}:{final_port}")
    click.echo(f"🔧 环境: {settings.ENVIRONMENT}")
    click.echo(f"🔄 热重载: {'启用' if final_reload else '禁用'}")
    click.echo(f"👥 工作进程: {workers}")

    # 启动服务器
    uvicorn.run(
        "src.main:app",
        host=final_host,
        port=final_port,
        reload=final_reload,
        workers=workers if not final_reload else 1,  # 热重载模式只能单进程
        log_level=log_level,
        access_log=True,
        use_colors=True,
    )


@cli.command()
def dev():
    """开发模式启动（带热重载）"""
    click.echo("🔧 启动开发模式...")
    serve.main(["--reload", "--log-level", "debug"], standalone_mode=False)


@cli.command()
def prod():
    """生产模式启动"""
    click.echo("🏭 启动生产模式...")

    settings = get_settings()
    if settings.ENVIRONMENT != "production":
        click.echo("⚠️ 警告: 当前环境不是production，建议检查配置", fg="yellow")

    serve.main(["--workers", "4", "--log-level", "warning"], standalone_mode=False)


@cli.command()
def check():
    """检查系统配置和依赖"""
    click.echo("🔍 系统检查...")

    # 检查配置
    if validate_config():
        click.echo("✅ 配置验证通过")
    else:
        click.echo("❌ 配置验证失败")
        return

    # 检查依赖
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2",
        "redis",
        "jose",
        "passlib",
        "pydantic",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            click.echo(f"✅ {package}")
        except ImportError:
            click.echo(f"❌ {package}")
            missing_packages.append(package)

    if missing_packages:
        click.echo(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        click.echo("请运行: pip install -r requirements.txt")
    else:
        click.echo("\n✅ 所有依赖包已安装")

    # 检查数据库连接
    try:
        from src.core.database import get_db_manager

        db_manager = get_db_manager()
        if db_manager.test_connection():
            click.echo("✅ 数据库连接正常")
        else:
            click.echo("❌ 数据库连接失败")
    except Exception as e:
        click.echo(f"❌ 数据库检查失败: {e}")

    # 检查Redis连接
    try:
        from src.core.database import get_db_manager

        db_manager = get_db_manager()
        if db_manager.test_redis_connection():
            click.echo("✅ Redis连接正常")
        else:
            click.echo("❌ Redis连接失败")
    except Exception as e:
        click.echo(f"❌ Redis检查失败: {e}")


@cli.command()
def init():
    """初始化数据库和系统数据"""
    click.echo("🗄️ 初始化数据库...")

    try:
        from src.core.database import init_db

        init_db()
        click.echo("✅ 数据库初始化完成")
    except Exception as e:
        click.echo(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


@cli.command()
@click.option("--backup-dir", default="./backups", help="备份目录")
def backup():
    """备份数据库"""
    click.echo("💾 备份数据库...")

    import subprocess
    from datetime import datetime

    settings = get_settings()
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"task_manager_backup_{timestamp}.sql"

    try:
        pass  # Auto-fixed empty block
        # 使用pg_dump备份数据库
        cmd = ["pg_dump", settings.DATABASE_URL, "-f", str(backup_file), "--verbose"]

        subprocess.run(cmd, check=True)
        click.echo(f"✅ 数据库备份完成: {backup_file}")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ 数据库备份失败: {e}")
    except FileNotFoundError:
        click.echo("❌ 未找到pg_dump命令，请安装PostgreSQL客户端工具")


@cli.command()
def version():
    """显示版本信息"""
    settings = get_settings()
    click.echo(f"任务管理系统 v{settings.VERSION}")
    click.echo(f"FastAPI版本: {__import__('fastapi').__version__}")
    click.echo(f"Python版本: {sys.version}")


if __name__ == "__main__":
    cli()
