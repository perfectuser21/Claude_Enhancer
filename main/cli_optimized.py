#!/usr/bin/env python3
"""
Perfect21 CLI - 性能优化版
使用新的架构：命令模式、异步执行、智能缓存
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('PERFECT21_PROJECT_ROOT', str(project_root))


def setup_logging():
    """设置日志系统"""
    try:
        from infrastructure.config.config_manager import get_config_manager

        config_manager = get_config_manager(str(project_root))
        log_level = config_manager.get('logging.level', 'INFO')
        log_file = config_manager.get('logging.file')

        # 创建日志格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        root_logger.addHandler(console_handler)

        # 文件处理器(如果配置了)
        if log_file:
            log_path = project_root / log_file
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    except Exception as e:
        # 回退到基本日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.getLogger().warning(f"日志配置失败，使用默认配置: {e}")


def check_system_requirements():
    """检查系统要求"""
    issues = []

    # 检查Python版本
    if sys.version_info < (3, 7):
        issues.append("需要Python 3.7或更高版本")

    # 检查Git
    try:
        import subprocess
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("需要安装Git")

    # 检查必要的目录
    required_dirs = ['core', 'features', 'modules', 'infrastructure']
    for dir_name in required_dirs:
        if not (project_root / dir_name).exists():
            issues.append(f"缺少必要目录: {dir_name}")

    if issues:
        print("❌ 系统要求检查失败:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    return True


def display_banner():
    """显示启动横幅"""
    try:
        from infrastructure.config.config_manager import get_config

        version = get_config('perfect21.version', '3.1.0')
        mode = get_config('perfect21.mode', 'development')

        banner = f"""
🚀 Perfect21 CLI - 性能优化版 v{version}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 特性: Git缓存 | 异步执行 | 智能Agent | 命令模式
🎯 模式: {mode.upper()}
📁 项目: {project_root.name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        print(banner)

    except Exception:
        print("🚀 Perfect21 CLI - 性能优化版")


async def main():
    """异步主函数"""
    try:
        # 检查系统要求
        if not check_system_requirements():
            return 1

        # 设置日志
        setup_logging()

        # 显示横幅
        display_banner()

        # 导入并运行CLI控制器
        from application.cli.cli_controller import get_cli_controller

        controller = get_cli_controller()
        exit_code = await controller.run()

        return exit_code

    except KeyboardInterrupt:
        print("\n👋 操作已取消")
        return 130
    except Exception as e:
        print(f"❌ CLI启动失败: {e}")
        logging.getLogger().error(f"CLI启动异常: {e}", exc_info=True)
        return 1


def sync_main():
    """同步主函数包装器"""
    try:
        # Python 3.7+ 使用 asyncio.run
        if sys.version_info >= (3, 7):
            return asyncio.run(main())
        else:
            # Python 3.6 兼容性
            loop = asyncio.get_event_loop()
            try:
                return loop.run_until_complete(main())
            finally:
                loop.close()

    except Exception as e:
        print(f"❌ 系统错误: {e}")
        return 1


def handle_legacy_mode():
    """处理传统模式调用"""
    """
    如果检测到传统的调用方式，提供向后兼容性
    """
    if len(sys.argv) > 1:
        # 检查是否是传统的调用方式
        legacy_commands = {
            'status': 'status',
            'hooks': 'hooks',
            'parallel': 'parallel',
            'workspace': 'workspace',
            'learning': 'learning'
        }

        first_arg = sys.argv[1]
        if first_arg in legacy_commands:
            print(f"💡 检测到传统命令调用: {first_arg}")
            print(f"💡 建议使用: python3 main/cli_optimized.py {first_arg}")
            print()


if __name__ == '__main__':
    # 处理传统模式
    handle_legacy_mode()

    # 运行优化版CLI
    try:
        exit_code = sync_main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 致命错误: {e}")
        sys.exit(1)