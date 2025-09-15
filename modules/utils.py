#!/usr/bin/env python3
"""
Utilities - 工具函数
Perfect21公共工具函数
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("Utils")

def setup_logging(log_level: str = 'INFO', log_file: str = None) -> None:
    """设置日志系统"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # 文件处理器(如果指定)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def run_command(cmd: List[str], cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': ' '.join(cmd)
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'timeout',
            'message': f"命令执行超时({timeout}秒): {' '.join(cmd)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"命令执行失败: {' '.join(cmd)}"
        }

def check_git_repository(project_root: str = None) -> bool:
    """检查是否为Git仓库"""
    project_root = project_root or os.getcwd()
    git_dir = os.path.join(project_root, '.git')
    return os.path.exists(git_dir)

def get_project_info(project_root: str = None) -> Dict[str, Any]:
    """获取项目基本信息"""
    project_root = project_root or os.getcwd()

    info = {
        'project_root': project_root,
        'is_git_repo': check_git_repository(project_root),
        'has_core_agents': False,
        'perfect21_structure': False
    }

    # 检查core agents
    core_agents_path = os.path.join(project_root, 'core/claude-code-unified-agents/.claude/agents')
    if os.path.exists(core_agents_path):
        info['has_core_agents'] = True
        agent_files = list(Path(core_agents_path).rglob('*.md'))
        info['agent_count'] = len(agent_files)

    # 检查Perfect21结构
    required_dirs = ['core', 'features', 'modules', 'main']
    existing_dirs = [d for d in required_dirs if os.path.exists(os.path.join(project_root, d))]
    info['perfect21_structure'] = len(existing_dirs) == len(required_dirs)
    info['existing_dirs'] = existing_dirs

    # Git信息
    if info['is_git_repo']:
        git_info = run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=project_root)
        if git_info['success']:
            info['current_branch'] = git_info['stdout'].strip()

    return info

def validate_subagent_name(agent_name: str) -> Dict[str, Any]:
    """验证SubAgent名称"""
    valid_agents = [
        'orchestrator', 'code-reviewer', 'security-auditor', 'test-engineer',
        'performance-engineer', 'devops-engineer', 'backend-architect',
        'frontend-specialist', 'database-specialist', 'deployment-manager',
        'monitoring-specialist', 'ai-engineer', 'data-engineer'
    ]

    # 移除@前缀
    clean_name = agent_name.lstrip('@')

    return {
        'original': agent_name,
        'clean_name': clean_name,
        'is_valid': clean_name in valid_agents,
        'available_agents': valid_agents,
        'suggestion': f"@{clean_name}" if not agent_name.startswith('@') else agent_name
    }

def format_execution_result(result: Dict[str, Any]) -> str:
    """格式化执行结果用于显示"""
    if not isinstance(result, dict):
        return str(result)

    output = []

    if 'success' in result:
        status = "✅ 成功" if result['success'] else "❌ 失败"
        output.append(f"状态: {status}")

    if 'message' in result:
        output.append(f"消息: {result['message']}")

    if 'agent' in result:
        output.append(f"调用Agent: {result['agent']}")

    if 'execution_time' in result:
        output.append(f"执行时间: {result['execution_time']:.2f}秒")

    if 'error' in result and result.get('error'):
        output.append(f"错误: {result['error']}")

    return '\n'.join(output)

def create_task_summary(task_type: str, details: Dict[str, Any]) -> str:
    """创建任务摘要"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"Perfect21任务执行摘要 - {timestamp}\n"
    summary += f"{'='*50}\n"
    summary += f"任务类型: {task_type}\n"

    if 'branch' in details:
        summary += f"分支: {details['branch']}\n"

    if 'files' in details:
        file_count = len(details['files']) if isinstance(details['files'], list) else details['files']
        summary += f"涉及文件: {file_count}\n"

    if 'agents_called' in details:
        agents = ', '.join(details['agents_called']) if isinstance(details['agents_called'], list) else details['agents_called']
        summary += f"调用Agent: {agents}\n"

    summary += f"{'='*50}\n"

    return summary

def ensure_directory(path: str) -> bool:
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {path}: {e}")
        return False

def cleanup_temp_files(project_root: str = None, patterns: List[str] = None) -> Dict[str, Any]:
    """清理临时文件"""
    project_root = project_root or os.getcwd()
    patterns = patterns or ['*.tmp', '*.temp', '*~', '*.bak', '__pycache__']

    cleaned_files = []
    errors = []

    try:
        for pattern in patterns:
            for file_path in Path(project_root).rglob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                    elif file_path.is_dir() and pattern == '__pycache__':
                        import shutil
                        shutil.rmtree(file_path)
                        cleaned_files.append(str(file_path))
                except Exception as e:
                    errors.append(f"{file_path}: {e}")

        return {
            'success': True,
            'cleaned_files': cleaned_files,
            'count': len(cleaned_files),
            'errors': errors
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'cleaned_files': cleaned_files,
            'count': len(cleaned_files)
        }