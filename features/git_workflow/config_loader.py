#!/usr/bin/env python3
"""
Perfect21 Git Hooks 配置加载器
支持YAML配置文件的现代化hooks管理
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("Perfect21.HooksConfig")

class HooksConfigLoader:
    """Git Hooks配置加载器"""

    def __init__(self, project_root: str = None, config_file: str = None):
        self.project_root = project_root or os.getcwd()
        self.config_file = config_file or os.path.join(
            self.project_root,
            'features/git_workflow/hooks_config.yaml'
        )
        self._config = None
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"配置文件不存在: {self.config_file}")
                self._config = self._get_default_config()
                return

            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            logger.info(f"成功加载hooks配置: {self.config_file}")

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "global": {
                "project_name": "Perfect21",
                "version": "2.1.0",
                "parallel_execution": True,
                "max_workers": 4,
                "timeout": 300,
                "log_level": "INFO"
            },
            "hooks": {},
            "hook_groups": {
                "essential": {
                    "hooks": ["pre-commit", "commit-msg", "pre-push"]
                }
            },
            "default_hook_group": "essential"
        }

    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self._config.get('global', {})

    def get_hook_config(self, hook_name: str) -> Optional[Dict[str, Any]]:
        """获取特定hook的配置"""
        hooks_config = self._config.get('hooks', {})
        return hooks_config.get(hook_name)

    def get_hook_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """获取hook组配置"""
        groups = self._config.get('hook_groups', {})
        return groups.get(group_name)

    def get_enabled_hooks(self, group_name: str = None) -> List[str]:
        """获取启用的hooks列表"""
        if group_name:
            group_config = self.get_hook_group(group_name)
            if group_config:
                return group_config.get('hooks', [])

        # 默认返回所有启用的hooks
        enabled_hooks = []
        hooks_config = self._config.get('hooks', {})

        for hook_name, config in hooks_config.items():
            if config.get('enabled', False):
                enabled_hooks.append(hook_name)

        return enabled_hooks

    def get_default_hook_group(self) -> str:
        """获取默认hook组"""
        return self._config.get('default_hook_group', 'essential')

    def is_hook_enabled(self, hook_name: str) -> bool:
        """检查hook是否启用"""
        hook_config = self.get_hook_config(hook_name)
        if not hook_config:
            return False
        return hook_config.get('enabled', False)

    def get_hook_agent(self, hook_name: str, branch: str = None) -> str:
        """获取hook对应的Agent"""
        hook_config = self.get_hook_config(hook_name)
        if not hook_config:
            return "@orchestrator"

        # 检查分支规则
        if branch and 'branch_rules' in hook_config:
            branch_rules = hook_config['branch_rules']

            # 精确匹配
            if branch in branch_rules:
                return branch_rules[branch].get('agent', hook_config.get('agent', '@orchestrator'))

            # 模式匹配
            for pattern, rule in branch_rules.items():
                if '*' in pattern:
                    prefix = pattern.split('*')[0]
                    if branch.startswith(prefix):
                        return rule.get('agent', hook_config.get('agent', '@orchestrator'))

        return hook_config.get('agent', '@orchestrator')

    def get_hook_timeout(self, hook_name: str) -> int:
        """获取hook超时时间"""
        hook_config = self.get_hook_config(hook_name)
        if hook_config:
            return hook_config.get('timeout', 120)

        global_config = self.get_global_config()
        return global_config.get('timeout', 300)

    def is_parallel_enabled(self, hook_name: str = None) -> bool:
        """检查是否启用并行执行"""
        if hook_name:
            hook_config = self.get_hook_config(hook_name)
            if hook_config and 'parallel' in hook_config:
                return hook_config['parallel']

        global_config = self.get_global_config()
        return global_config.get('parallel_execution', True)

    def get_max_workers(self) -> int:
        """获取最大工作线程数"""
        global_config = self.get_global_config()
        return global_config.get('max_workers', 4)

    def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件配置"""
        plugins = self._config.get('plugins', {})
        return plugins.get(plugin_name)

    def get_enabled_plugins(self, hook_name: str) -> List[str]:
        """获取hook启用的插件列表"""
        hook_config = self.get_hook_config(hook_name)
        if not hook_config:
            return []

        return hook_config.get('plugins', [])

    def get_environment_config(self, env_name: str = None) -> Dict[str, Any]:
        """获取环境配置"""
        if not env_name:
            env_name = os.getenv('PERFECT21_ENV', 'development')

        environments = self._config.get('environments', {})
        return environments.get(env_name, environments.get('development', {}))

    def get_integration_config(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """获取集成配置"""
        integrations = self._config.get('integrations', {})
        return integrations.get(integration_name)

    def validate_config(self) -> Dict[str, Any]:
        """验证配置文件"""
        errors = []
        warnings = []

        # 检查必需的配置项
        required_sections = ['global', 'hooks', 'hook_groups']
        for section in required_sections:
            if section not in self._config:
                errors.append(f"缺少必需的配置节: {section}")

        # 检查hook配置
        hooks_config = self._config.get('hooks', {})
        for hook_name, config in hooks_config.items():
            if not isinstance(config, dict):
                errors.append(f"Hook配置必须是字典类型: {hook_name}")
                continue

            # 检查必需的hook配置项
            required_hook_fields = ['enabled', 'category', 'priority', 'agent']
            for field in required_hook_fields:
                if field not in config:
                    warnings.append(f"Hook {hook_name} 缺少推荐的配置项: {field}")

        # 检查hook组配置
        groups = self._config.get('hook_groups', {})
        for group_name, group_config in groups.items():
            if 'hooks' not in group_config:
                errors.append(f"Hook组 {group_name} 必须包含hooks列表")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def update_hook_config(self, hook_name: str, config: Dict[str, Any]) -> bool:
        """更新hook配置"""
        try:
            if 'hooks' not in self._config:
                self._config['hooks'] = {}

            self._config['hooks'][hook_name] = config
            return self._save_config()

        except Exception as e:
            logger.error(f"更新hook配置失败: {e}")
            return False

    def enable_hook(self, hook_name: str) -> bool:
        """启用hook"""
        hook_config = self.get_hook_config(hook_name)
        if not hook_config:
            return False

        hook_config['enabled'] = True
        return self.update_hook_config(hook_name, hook_config)

    def disable_hook(self, hook_name: str) -> bool:
        """禁用hook"""
        hook_config = self.get_hook_config(hook_name)
        if not hook_config:
            return False

        hook_config['enabled'] = False
        return self.update_hook_config(hook_name, hook_config)

    def _save_config(self) -> bool:
        """保存配置文件"""
        try:
            # 创建备份
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                import shutil
                shutil.copy2(self.config_file, backup_file)

            # 保存新配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"配置文件已保存: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def reload_config(self) -> bool:
        """重新加载配置文件"""
        try:
            self._load_config()
            logger.info("配置文件已重新加载")
            return True
        except Exception as e:
            logger.error(f"重新加载配置文件失败: {e}")
            return False

    def get_config_summary(self) -> str:
        """获取配置摘要"""
        global_config = self.get_global_config()
        hooks_config = self._config.get('hooks', {})

        enabled_hooks = [name for name, config in hooks_config.items() if config.get('enabled')]

        return f"""
📋 Perfect21 Git Hooks 配置摘要
=====================================
项目: {global_config.get('project_name', 'Unknown')}
版本: {global_config.get('version', 'Unknown')}
并行执行: {'启用' if global_config.get('parallel_execution') else '禁用'}
最大工作线程: {global_config.get('max_workers', 4)}

📊 Hooks状态:
总数: {len(hooks_config)}
启用: {len(enabled_hooks)}
禁用: {len(hooks_config) - len(enabled_hooks)}

✅ 启用的Hooks:
{chr(10).join(f'  - {hook}' for hook in enabled_hooks[:5])}
{f'  ... 还有{len(enabled_hooks) - 5}个' if len(enabled_hooks) > 5 else ''}

📁 配置文件: {self.config_file}
        """.strip()

if __name__ == "__main__":
    # 测试配置加载器
    loader = HooksConfigLoader()

    print("=== 配置验证 ===")
    validation = loader.validate_config()
    print(f"配置有效: {'✅' if validation['valid'] else '❌'}")

    if validation['errors']:
        print("错误:")
        for error in validation['errors']:
            print(f"  - {error}")

    if validation['warnings']:
        print("警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    print("\n=== 配置摘要 ===")
    print(loader.get_config_summary())