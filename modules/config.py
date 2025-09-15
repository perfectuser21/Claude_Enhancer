#!/usr/bin/env python3
"""
Configuration Manager - 配置管理
Perfect21最小配置系统
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("ConfigManager")

class ConfigManager:
    """配置管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.config_dir = os.path.join(self.project_root, 'config')
        self.config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'perfect21': {
                'version': '2.0.0',
                'mode': 'minimal',
                'core_path': 'core/claude-code-unified-agents/.claude/agents'
            },
            'git_workflow': {
                'enabled': True,
                'hooks': {
                    'pre_commit': True,
                    'pre_push': True,
                    'post_checkout': True
                },
                'protection_rules': {
                    'protected_branches': ['main', 'master'],
                    'require_review': True
                }
            },
            'subagents': {
                'timeout': 300,
                'retry_count': 2,
                'available_agents': [
                    'code-reviewer', 'security-auditor', 'test-engineer',
                    'performance-engineer', 'devops-engineer', 'orchestrator'
                ]
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/perfect21.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_core_agents_path(self) -> str:
        """获取核心Agent路径"""
        core_path = self.get('perfect21.core_path')
        return os.path.join(self.project_root, core_path)

    def is_git_workflow_enabled(self) -> bool:
        """检查Git工作流是否启用"""
        return self.get('git_workflow.enabled', True)

    def get_protected_branches(self) -> list:
        """获取受保护分支列表"""
        return self.get('git_workflow.protection_rules.protected_branches', ['main', 'master'])

    def get_available_subagents(self) -> list:
        """获取可用的SubAgent列表"""
        return self.get('subagents.available_agents', [])

    def save_config(self, filepath: str = None) -> bool:
        """保存配置到文件"""
        try:
            if not filepath:
                os.makedirs(self.config_dir, exist_ok=True)
                filepath = os.path.join(self.config_dir, 'perfect21.json')

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {filepath}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def load_config(self, filepath: str = None) -> bool:
        """从文件加载配置"""
        try:
            if not filepath:
                filepath = os.path.join(self.config_dir, 'perfect21.json')

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)

                logger.info(f"配置已从文件加载: {filepath}")
                return True
            else:
                logger.info(f"配置文件不存在，使用默认配置: {filepath}")
                return False

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return False

# 全局配置实例
config = ConfigManager()