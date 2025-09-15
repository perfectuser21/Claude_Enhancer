#!/usr/bin/env python3
"""
Template Manager - 模板管理器
管理CLAUDE.md的分层模板系统，支持团队模板和个人配置
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class TemplateManager:
    """模板管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # 模板路径
        self.templates_dir = os.path.join(self.project_root, '.claude', 'templates')
        self.team_template = os.path.join(self.templates_dir, 'team_claude_md.template')
        self.personal_template = os.path.join(self.templates_dir, 'personal_claude_md.template')

        # 确保模板目录存在
        self._ensure_templates_dir()

    def _ensure_templates_dir(self):
        """确保模板目录存在"""
        os.makedirs(self.templates_dir, exist_ok=True)

    def initialize_templates(self) -> Dict[str, Any]:
        """初始化默认模板"""
        try:
            results = []

            # 创建团队模板
            if not os.path.exists(self.team_template):
                team_template_content = self._get_default_team_template()
                with open(self.team_template, 'w', encoding='utf-8') as f:
                    f.write(team_template_content)
                results.append('team_template_created')

            # 创建个人模板
            if not os.path.exists(self.personal_template):
                personal_template_content = self._get_default_personal_template()
                with open(self.personal_template, 'w', encoding='utf-8') as f:
                    f.write(personal_template_content)
                results.append('personal_template_created')

            return {
                'success': True,
                'actions': results,
                'templates_dir': self.templates_dir
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def render_claude_md(self, template_vars: Dict[str, Any]) -> str:
        """渲染CLAUDE.md内容"""
        try:
            # 使用简化的模板渲染（生产环境建议使用Jinja2）
            template = self._load_team_template()

            # 简单的变量替换
            for key, value in template_vars.items():
                placeholder = f'{{{{{key}}}}}'
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                template = template.replace(placeholder, str(value))

            return template

        except Exception as e:
            # 回退到默认模板
            return self._get_fallback_template(template_vars)

    def render_personal_config(self, user_config: Dict[str, Any]) -> str:
        """渲染个人配置文件"""
        try:
            template = self._load_personal_template()

            # 渲染个人配置
            for key, value in user_config.items():
                placeholder = f'{{{{{key}}}}}'
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                template = template.replace(placeholder, str(value))

            return template

        except Exception as e:
            return self._get_fallback_personal_config(user_config)

    def update_template(self, template_type: str, content: str) -> Dict[str, Any]:
        """更新模板"""
        try:
            if template_type == 'team':
                template_path = self.team_template
            elif template_type == 'personal':
                template_path = self.personal_template
            else:
                return {
                    'success': False,
                    'error': f'未知的模板类型: {template_type}'
                }

            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'template_type': template_type,
                'template_path': template_path,
                'updated_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_template_info(self) -> Dict[str, Any]:
        """获取模板信息"""
        info = {
            'templates_dir': self.templates_dir,
            'team_template': {
                'path': self.team_template,
                'exists': os.path.exists(self.team_template),
                'size': 0,
                'last_modified': None
            },
            'personal_template': {
                'path': self.personal_template,
                'exists': os.path.exists(self.personal_template),
                'size': 0,
                'last_modified': None
            }
        }

        # 获取团队模板信息
        if os.path.exists(self.team_template):
            stat = os.stat(self.team_template)
            info['team_template']['size'] = stat.st_size
            info['team_template']['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # 获取个人模板信息
        if os.path.exists(self.personal_template):
            stat = os.stat(self.personal_template)
            info['personal_template']['size'] = stat.st_size
            info['personal_template']['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return info

    def _load_team_template(self) -> str:
        """加载团队模板"""
        if os.path.exists(self.team_template):
            with open(self.team_template, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_team_template()

    def _load_personal_template(self) -> str:
        """加载个人模板"""
        if os.path.exists(self.personal_template):
            with open(self.personal_template, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_personal_template()

    def _get_default_team_template(self) -> str:
        """获取默认团队模板"""
        return """# Claude Code 项目指导文档

**项目名称**: {{project_name}}
**项目类型**: {{project_type}}
**技术栈**: {{tech_stack}}
**目标用户**: {{target_users}}

## 🎯 项目概述

{{project_description}}

### 核心理念
{{core_principles}}

## 🏗️ 系统架构

### 完整的企业级架构

```
{{project_structure}}
```

### SubAgent调用策略

{{subagent_strategy}}

## 🚀 使用方法

### 快速开始
```bash
{{quick_start_commands}}
```

### Git工作流管理
```bash
{{git_workflow_commands}}
```

## 💡 设计原则

{{design_principles}}

## 🔧 技术实现

{{technical_implementation}}

## 📊 核心价值

{{core_values}}

## 📁 文件管理规则 (重要!)

### 🚨 严格遵守的架构原则

{{architecture_rules}}

## 🎉 版本更新

### ✨ 新增功能
{{new_features}}

### 🎯 系统升级
{{system_upgrades}}

### 📊 技术指标
{{technical_metrics}}

---

*最后更新: {{last_updated}}*
*版本: Perfect21 {{version}}*
*架构: {{architecture_info}}*
*核心模块: {{module_count}} | Agent集成: {{agent_count}} | 系统状态: {{system_status}}*
"""

    def _get_default_personal_template(self) -> str:
        """获取默认个人模板"""
        return """# CLAUDE.md 个人配置

## 🔧 个人开发偏好

### 代码风格
{{code_style_preferences}}

### 常用命令
{{frequent_commands}}

### 工作流配置
{{workflow_preferences}}

## 🎯 项目记忆

### 快速记忆
{{quick_memories}}

### 上下文信息
{{context_info}}

## 📝 开发笔记

{{dev_notes}}

---

*个人配置更新时间: {{updated_at}}*
*配置版本: {{config_version}}*
"""

    def _get_fallback_template(self, vars: Dict[str, Any]) -> str:
        """回退模板"""
        return f"""# Claude Code 项目指导文档

**项目名称**: Perfect21
**项目类型**: 企业级多Agent协作开发平台
**版本**: {vars.get('version', 'v2.2.0')}

## 🎯 项目概述

Perfect21 是一个企业级多Agent协作开发平台，基于claude-code-unified-agents核心，集成了智能Git工作流、统一版本管理、动态功能发现等企业级开发特性。

---

*最后更新: {vars.get('last_updated', datetime.now().strftime('%Y-%m-%d'))}*
*系统状态: {vars.get('system_status', '运行正常')}*
"""

    def _get_fallback_personal_config(self, config: Dict[str, Any]) -> str:
        """回退个人配置"""
        return f"""# CLAUDE.md 个人配置

## 🔧 个人开发偏好

根据您的需要自定义开发偏好...

---

*个人配置更新时间: {datetime.now().isoformat()}*
"""

    def create_template_from_existing(self, source_path: str, template_type: str) -> Dict[str, Any]:
        """从现有文件创建模板"""
        try:
            if not os.path.exists(source_path):
                return {
                    'success': False,
                    'error': f'源文件不存在: {source_path}'
                }

            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 将动态内容替换为模板变量
            template_content = self._convert_to_template(content)

            # 保存模板
            result = self.update_template(template_type, template_content)

            if result['success']:
                result['source_file'] = source_path
                result['message'] = f'从 {source_path} 创建 {template_type} 模板成功'

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _convert_to_template(self, content: str) -> str:
        """将内容转换为模板"""
        import re

        # 替换版本信息
        content = re.sub(r'Perfect21 v[\d\.]+', 'Perfect21 {{version}}', content)

        # 替换时间信息
        content = re.sub(r'\*最后更新: \d{4}-\d{2}-\d{2}', '*最后更新: {{last_updated}}', content)

        # 替换统计信息
        content = re.sub(r'\*核心模块: \d+', '*核心模块: {{module_count}}', content)

        return content

if __name__ == "__main__":
    # 测试脚本
    manager = TemplateManager()
    result = manager.initialize_templates()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 测试模板信息
    info = manager.get_template_info()
    print(json.dumps(info, ensure_ascii=False, indent=2))