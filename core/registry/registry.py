#!/usr/bin/env python3
"""
Perfect21功能注册器
向claude-code-unified-agents注册发现的功能
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger("CapabilityRegistry")

class CapabilityRegistry:
    """功能注册器"""

    def __init__(self, claude_agents_path: str = None):
        """
        初始化注册器

        Args:
            claude_agents_path: claude-code-unified-agents路径
        """
        self.claude_agents_path = claude_agents_path or os.path.join(
            os.getcwd(), 'core', 'claude-code-unified-agents'
        )
        self.registered_capabilities = {}
        self.registration_log = []

        logger.info(f"功能注册器初始化 - Agent路径: {self.claude_agents_path}")

    def discover_capabilities(self) -> Dict[str, Any]:
        """
        发现所有可用的功能模块

        Returns:
            Dict[str, Any]: 发现的功能模块信息
        """
        from .scanner import CapabilityScanner

        scanner = CapabilityScanner()
        capabilities = scanner.scan_all_features()

        logger.info(f"发现 {len(capabilities)} 个功能模块")
        return capabilities

    def register_capabilities(self, capabilities: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        批量注册功能到claude-code-unified-agents

        Args:
            capabilities: 功能字典，如果为None则自动发现

        Returns:
            Dict[str, bool]: 注册结果，键为功能名，值为是否成功
        """
        if capabilities is None:
            capabilities = self.discover_capabilities()

        logger.info(f"开始注册 {len(capabilities)} 个功能...")

        results = {}

        # 按优先级排序，核心功能优先注册
        sorted_capabilities = self._sort_by_priority(capabilities)

        for name, capability in sorted_capabilities:
            try:
                success = self._register_single_capability(name, capability)
                results[name] = success

                if success:
                    self.registered_capabilities[name] = capability
                    logger.info(f"功能注册成功: {name}")
                else:
                    logger.warning(f"功能注册失败: {name}")

            except Exception as e:
                logger.error(f"注册功能 {name} 时发生异常: {e}")
                results[name] = False

        self._save_registration_log(results)

        success_count = sum(results.values())
        logger.info(f"功能注册完成: {success_count}/{len(capabilities)} 成功")

        return results

    def _sort_by_priority(self, capabilities: Dict[str, Any]) -> List[tuple]:
        """
        按优先级排序功能

        Args:
            capabilities: 功能字典

        Returns:
            List[tuple]: 排序后的(name, capability)元组列表
        """
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

        def get_priority_value(item):
            name, capability = item
            priority = capability.get('priority', 'low')
            is_core = capability.get('is_core', False)
            # 核心功能优先级更高
            return (0 if is_core else 1, priority_order.get(priority, 3))

        return sorted(capabilities.items(), key=get_priority_value)

    def _register_single_capability(self, name: str, capability: Dict[str, Any]) -> bool:
        """
        注册单个功能

        Args:
            name: 功能名称
            capability: 功能信息

        Returns:
            bool: 注册是否成功
        """
        try:
            # 1. 创建Agent描述文件
            self._create_agent_descriptions(name, capability)

            # 2. 更新全局功能目录
            self._update_global_catalog(name, capability)

            # 3. 创建集成脚本
            self._create_integration_script(name, capability)

            # 4. 验证注册结果
            return self._verify_registration(name, capability)

        except Exception as e:
            logger.error(f"注册功能 {name} 失败: {e}")
            return False

    def _create_agent_descriptions(self, name: str, capability: Dict[str, Any]) -> None:
        """
        为相关Agent创建功能描述

        Args:
            name: 功能名称
            capability: 功能信息
        """
        agents_can_use = capability.get('agents_can_use', [])

        for agent_name in agents_can_use:
            self._add_capability_to_agent(agent_name, name, capability)

    def _add_capability_to_agent(self, agent_name: str, capability_name: str, capability: Dict[str, Any]) -> None:
        """
        向特定Agent添加功能描述

        Args:
            agent_name: Agent名称
            capability_name: 功能名称
            capability: 功能信息
        """
        # 查找Agent文件路径
        agent_file = self._find_agent_file(agent_name)

        if not agent_file:
            logger.warning(f"未找到Agent文件: {agent_name}")
            return

        # 读取现有Agent描述
        agent_content = self._read_agent_file(agent_file)

        # 添加功能描述
        updated_content = self._inject_capability_description(
            agent_content, capability_name, capability
        )

        # 写回Agent文件
        self._write_agent_file(agent_file, updated_content)

        logger.debug(f"向Agent {agent_name} 添加功能: {capability_name}")

    def _find_agent_file(self, agent_name: str) -> Optional[str]:
        """
        查找Agent文件路径

        Args:
            agent_name: Agent名称

        Returns:
            Optional[str]: Agent文件路径
        """
        possible_paths = [
            os.path.join(self.claude_agents_path, '.claude', 'agents', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'core', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'development', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'infrastructure', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'quality', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'business', f'{agent_name}.md'),
            os.path.join(self.claude_agents_path, '.claude', 'agents', 'specialized', f'{agent_name}.md'),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _read_agent_file(self, agent_file: str) -> str:
        """读取Agent文件内容（带路径遍历防护）"""
        try:
            # 路径遍历防护：确保文件路径在预期目录内
            agent_file_path = os.path.abspath(agent_file)
            allowed_base_path = os.path.abspath(self.claude_agents_path)

            # 检查文件路径是否在允许的目录内
            if not agent_file_path.startswith(allowed_base_path):
                logger.error(f"安全错误：尝试访问不允许的路径: {agent_file}")
                return ""

            # 检查文件存在性
            if not os.path.exists(agent_file_path):
                logger.error(f"文件不存在: {agent_file_path}")
                return ""

            with open(agent_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取Agent文件失败: {agent_file} - {e}")
            return ""

    def _inject_capability_description(self, agent_content: str, capability_name: str, capability: Dict[str, Any]) -> str:
        """
        向Agent描述中注入功能信息（防重复注入）

        Args:
            agent_content: 原Agent内容
            capability_name: 功能名称
            capability: 功能信息

        Returns:
            str: 更新后的Agent内容
        """
        # 简单策略：不注入到orchestrator.md
        # orchestrator.md已经有完整的Perfect21功能区域，由人工维护
        # 避免重复注入和文件污染
        if "name: orchestrator" in agent_content:
            logger.info(f"跳过向orchestrator注入功能 {capability_name}（人工维护）")
            return agent_content

        # 检查是否已经存在该功能的描述，避免重复
        if f"### {capability_name}" in agent_content:
            logger.info(f"功能 {capability_name} 已存在于Agent中，跳过注入")
            return agent_content

        # 确保有Perfect21功能区域
        if "## Perfect21功能区域" not in agent_content:
            agent_content += "\n\n---\n## Perfect21功能区域\n_此区域由Perfect21自动管理，包含所有注册的功能_\n"

        # 构建简洁的功能描述
        capability_section = f"""

### {capability_name}
**描述**: {capability.get('description', '无描述')}
**类别**: {capability.get('category', 'unknown')} | **优先级**: {capability.get('priority', 'low')}
**可用函数**: {', '.join(capability.get('functions', {}).keys())}
"""

        # 在功能区域末尾添加
        agent_content = agent_content.rstrip() + capability_section

        return agent_content

    def _write_agent_file(self, agent_file: str, content: str) -> None:
        """写入Agent文件"""
        try:
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"写入Agent文件失败: {agent_file} - {e}")

    def _update_global_catalog(self, name: str, capability: Dict[str, Any]) -> None:
        """
        更新全局功能目录

        Args:
            name: 功能名称
            capability: 功能信息
        """
        catalog_file = os.path.join(self.claude_agents_path, 'perfect21_capabilities.json')

        # 读取现有目录
        catalog = self._load_catalog(catalog_file)

        # 更新功能信息
        catalog[name] = {
            'name': capability.get('name', name),
            'description': capability.get('description', ''),
            'category': capability.get('category', 'unknown'),
            'priority': capability.get('priority', 'low'),
            'is_core': capability.get('is_core', False),
            'agents_can_use': capability.get('agents_can_use', []),
            'functions': list(capability.get('functions', {}).keys()),
            'integration_points': capability.get('integration_points', []),
            'registered_at': self._get_timestamp()
        }

        # 保存目录
        self._save_catalog(catalog_file, catalog)

        logger.debug(f"更新全局功能目录: {name}")

    def _load_catalog(self, catalog_file: str) -> Dict[str, Any]:
        """加载功能目录"""
        if os.path.exists(catalog_file):
            try:
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载功能目录失败: {e}")

        return {}

    def _save_catalog(self, catalog_file: str, catalog: Dict[str, Any]) -> None:
        """保存功能目录"""
        try:
            os.makedirs(os.path.dirname(catalog_file), exist_ok=True)
            with open(catalog_file, 'w', encoding='utf-8') as f:
                json.dump(catalog, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存功能目录失败: {e}")

    def _create_integration_script(self, name: str, capability: Dict[str, Any]) -> None:
        """
        创建功能集成脚本

        Args:
            name: 功能名称
            capability: 功能信息
        """
        script_content = f'''#!/usr/bin/env python3
"""
Perfect21功能集成脚本: {name}
自动生成的集成代码
"""

def integrate_{name}():
    """集成{name}功能到claude-code-unified-agents"""
    print("正在集成功能: {name}")

    # TODO: 实现具体的集成逻辑
    # 这里可以添加功能初始化、配置加载等代码

    return True

if __name__ == "__main__":
    integrate_{name}()
'''

        script_file = os.path.join(
            self.claude_agents_path, 'integrations', f'{name}_integration.py'
        )

        os.makedirs(os.path.dirname(script_file), exist_ok=True)

        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            logger.debug(f"创建集成脚本: {script_file}")
        except Exception as e:
            logger.error(f"创建集成脚本失败: {e}")

    def _verify_registration(self, name: str, capability: Dict[str, Any]) -> bool:
        """
        验证功能注册结果

        Args:
            name: 功能名称
            capability: 功能信息

        Returns:
            bool: 验证是否通过
        """
        # 检查功能目录是否更新
        catalog_file = os.path.join(self.claude_agents_path, 'perfect21_capabilities.json')
        if not os.path.exists(catalog_file):
            return False

        catalog = self._load_catalog(catalog_file)
        if name not in catalog:
            return False

        # 检查相关Agent文件是否更新
        agents_can_use = capability.get('agents_can_use', [])
        for agent_name in agents_can_use:
            agent_file = self._find_agent_file(agent_name)
            if agent_file and os.path.exists(agent_file):
                agent_content = self._read_agent_file(agent_file)

                # 跳过orchestrator验证，因为orchestrator是人工维护的
                if agent_name == "orchestrator":
                    continue

                if f"### {name}" not in agent_content:
                    logger.warning(f"Agent {agent_name} 未正确更新功能信息")
                    return False

        return True

    def _save_registration_log(self, results: Dict[str, bool]) -> None:
        """保存注册日志"""
        log_entry = {
            'timestamp': self._get_timestamp(),
            'total_capabilities': len(results),
            'successful': sum(results.values()),
            'failed': len(results) - sum(results.values()),
            'details': results
        }

        self.registration_log.append(log_entry)

        # 保存到文件
        log_file = os.path.join(self.claude_agents_path, 'registration_log.json')
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.registration_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存注册日志失败: {e}")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()

    def get_registered_capabilities(self) -> Dict[str, Any]:
        """
        获取已注册的功能列表

        Returns:
            Dict: 已注册的功能
        """
        return self.registered_capabilities.copy()

    def unregister_capability(self, name: str) -> bool:
        """
        注销功能

        Args:
            name: 功能名称

        Returns:
            bool: 注销是否成功
        """
        if name not in self.registered_capabilities:
            logger.warning(f"功能 {name} 未注册，无法注销")
            return False

        try:
            # 从全局目录移除
            catalog_file = os.path.join(self.claude_agents_path, 'perfect21_capabilities.json')
            catalog = self._load_catalog(catalog_file)

            if name in catalog:
                del catalog[name]
                self._save_catalog(catalog_file, catalog)

            # 从本地记录移除
            del self.registered_capabilities[name]

            logger.info(f"功能注销成功: {name}")
            return True

        except Exception as e:
            logger.error(f"注销功能 {name} 失败: {e}")
            return False

    def get_registration_statistics(self) -> Dict[str, Any]:
        """
        获取注册统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            'total_registered': len(self.registered_capabilities),
            'by_category': self._group_by_category(),
            'by_priority': self._group_by_priority(),
            'recent_registrations': len(self.registration_log)
        }

    def _group_by_category(self) -> Dict[str, int]:
        """按分类分组统计"""
        categories = {}
        for capability in self.registered_capabilities.values():
            category = capability.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _group_by_priority(self) -> Dict[str, int]:
        """按优先级分组统计"""
        priorities = {}
        for capability in self.registered_capabilities.values():
            priority = capability.get('priority', 'low')
            priorities[priority] = priorities.get(priority, 0) + 1
        return priorities