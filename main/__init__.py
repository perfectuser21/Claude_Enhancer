"""
Perfect21 Main Module
基于claude-code-unified-agents的主程序入口
"""

from .vp import Perfect21
from .cli import main as cli_main

__all__ = ['Perfect21', 'cli_main']