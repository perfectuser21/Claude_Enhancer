"""
Perfect21 - 基于claude-code-unified-agents的智能Git工作流管理平台

核心特性:
- 53个claude-code-unified-agents官方Agent
- 智能Git工作流SubAgent调用编排器
- 轻量化企业级架构
- 模块化扩展支持

架构组成:
├── core/                           # claude-code-unified-agents核心
├── features/git_workflow/          # Git工作流功能
├── modules/                        # 核心工具模块
└── main/                          # 程序入口点

使用方式:
    python3 main/cli.py status        # 查看系统状态
    python3 main/cli.py hooks list    # 查看可用钩子
    python3 main/cli.py workflow list # 查看工作流操作
"""

__version__ = "2.3.0"
__title__ = "Perfect21"
__description__ = "基于claude-code-unified-agents的智能Git工作流管理平台"
__author__ = "Perfect21 Team"

# 导入核心组件
from main import Perfect21, cli_main
from features.git_workflow import GitHooks, WorkflowManager, BranchManager
from modules import config, perfect21_logger

__all__ = [
    'Perfect21', 'cli_main',
    'GitHooks', 'WorkflowManager', 'BranchManager',
    'config', 'perfect21_logger'
]