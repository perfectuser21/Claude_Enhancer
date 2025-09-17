"""
Perfect21 CLI命令模块
将庞大的cli.py拆分为独立的命令模块
"""

from .status import handle_status
from .git_hooks import handle_git_hooks
from .workflow import handle_workflow
from .branch import handle_branch
from .parallel import handle_parallel, handle_parallel_status, handle_parallel_command
from .monitor import handle_monitor
from .develop import handle_develop
from .orchestrator import handle_orchestrator
from .workspace import handle_workspace
from .learning import handle_learning
from .templates import handle_templates
from .claude_md import handle_claude_md

__all__ = [
    'handle_status',
    'handle_git_hooks',
    'handle_workflow',
    'handle_branch',
    'handle_parallel',
    'handle_parallel_status',
    'handle_parallel_command',
    'handle_monitor',
    'handle_develop',
    'handle_orchestrator',
    'handle_workspace',
    'handle_learning',
    'handle_templates',
    'handle_claude_md'
]