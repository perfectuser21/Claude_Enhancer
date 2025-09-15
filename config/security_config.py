#!/usr/bin/env python3
"""
安全配置管理器
从环境变量和配置文件安全加载敏感信息
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("SecurityConfig")

class SecurityConfig:
    """安全配置管理器"""

    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.env_file = self.config_dir / "security.env"
        self._load_config()

    def _load_config(self):
        """加载安全配置"""
        # 1. 尝试从环境文件加载
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                logger.info("从 security.env 加载配置完成")
            except Exception as e:
                logger.warning(f"加载 security.env 失败: {e}")

    def get(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """安全获取配置值"""
        value = os.getenv(key, default)

        if required and not value:
            raise ValueError(f"必需的配置项缺失: {key}")

        return value

    def get_ssh_config(self) -> Dict[str, str]:
        """获取SSH配置"""
        return {
            'host': self.get('SSH_HOST', '127.0.0.1'),
            'user': self.get('SSH_USER', 'root'),
            'port': int(self.get('SSH_PORT', '22')),
            'key_path': self.get('SSH_KEY_PATH', '~/.ssh/id_rsa')
        }

    def get_db_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        return {
            'host': self.get('DB_HOST', 'localhost'),
            'port': int(self.get('DB_PORT', '5432')),
            'name': self.get('DB_NAME', 'perfect21'),
            'user': self.get('DB_USER', 'perfect21'),
            'password': self.get('DB_PASSWORD', required=False)
        }

    def mask_sensitive(self, value: str, show_chars: int = 4) -> str:
        """掩码敏感信息用于日志"""
        if not value or len(value) <= show_chars:
            return "*" * len(value) if value else ""

        return value[:show_chars] + "*" * (len(value) - show_chars)

# 全局配置实例
security_config = SecurityConfig()