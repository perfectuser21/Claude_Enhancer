#!/usr/bin/env python3
"""
Perfect21 Git Integration Package
智能化Git工作流管理系统
"""

# 导出主要类和函数
from .git_hooks import (
    GitHooksManager,
    HookType,
    get_git_hooks_manager,
    install_all_hooks,
    execute_hook_by_name
)

from .git_integration import (
    GitWorkflowManager,
    WorkflowType,
    MergeStrategy,
    get_git_workflow_manager,
    start_feature_workflow,
    smart_commit
)

from .workflow_manager import (
    AdvancedGitWorkflowManager,
    TaskPriority,
    WorkflowStage,
    get_advanced_workflow_manager
)

from .cli import GitCLI

__version__ = '1.0.0'
__author__ = 'Perfect21 Team'
__description__ = 'Intelligent Git workflow management for personal development'

# 快捷函数
def quick_start(project_root: str = None):
    """快速启动Perfect21 Git工作流"""
    import asyncio
    
    async def _quick_start():
        # 初始化管理器
        manager = get_advanced_workflow_manager(project_root)
        
        # 安装基本钩子
        hooks_result = await install_all_hooks(project_root)
        
        # 显示仪表板
        dashboard = await manager.get_dashboard_data()
        
        return {
            'manager_initialized': True,
            'hooks_installed': hooks_result,
            'dashboard': dashboard
        }
    
    return asyncio.run(_quick_start())


# 模块信息
__all__ = [
    # Hooks
    'GitHooksManager',
    'HookType',
    'get_git_hooks_manager',
    'install_all_hooks',
    'execute_hook_by_name',
    
    # Workflow
    'GitWorkflowManager',
    'WorkflowType', 
    'MergeStrategy',
    'get_git_workflow_manager',
    'start_feature_workflow',
    'smart_commit',
    
    # Advanced Workflow
    'AdvancedGitWorkflowManager',
    'TaskPriority',
    'WorkflowStage', 
    'get_advanced_workflow_manager',
    
    # CLI
    'GitCLI',
    'quick_start'
]