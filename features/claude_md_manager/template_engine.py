#!/usr/bin/env python3
"""
Template Engine - CLAUDE.md模板引擎系统

基于模板的智能文档管理，明确区分固定/动态内容，
支持增量更新、内容去重、生命周期管理。
"""

import os
import re
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ContentBlock:
    """内容块定义"""
    id: str
    type: str  # 'fixed', 'dynamic', 'volatile'
    title: str
    template: str
    variables: Dict[str, Any]
    lifecycle_days: Optional[int] = None
    update_strategy: str = 'replace'  # 'replace', 'append', 'merge'
    priority: int = 0

@dataclass
class DocumentTemplate:
    """文档模板定义"""
    name: str
    version: str
    description: str
    fixed_blocks: List[ContentBlock]
    dynamic_blocks: List[ContentBlock]
    metadata: Dict[str, Any]

class TemplateEngine:
    """CLAUDE.md模板引擎"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        self.project_root = project_root
        self.templates_dir = os.path.join(project_root, 'features', 'claude_md_manager', 'templates')
        self.claude_md_path = os.path.join(project_root, 'CLAUDE.md')

        # 确保模板目录存在
        os.makedirs(self.templates_dir, exist_ok=True)

        # 加载默认模板
        self.default_template = self._create_default_template()

    def _create_default_template(self) -> DocumentTemplate:
        """创建默认模板"""

        # 固定内容块
        fixed_blocks = [
            ContentBlock(
                id="project_identity",
                type="fixed",
                title="项目身份",
                template="> 🎯 **项目身份**: Perfect21 - 智能编排器调用claude-code-unified-agents的56个专业Agent\n> 🔑 **核心原则**: 不重复造轮子，只做智能调用和工作流编排",
                variables={},
                priority=1
            ),
            ContentBlock(
                id="core_essence",
                type="fixed",
                title="项目本质",
                template="""## 🎯 项目本质

Perfect21 = **智能编排器** + claude-code-unified-agents

- **我们负责**: 任务分析、Agent选择、流程编排
- **官方Agent负责**: 具体实现、专业能力、质量保证

### 🔑 不变的核心理念
- **不重复造轮子**: 永远优先使用官方Agent
- **专注编排价值**: Perfect21只做智能调用和工作流管理
- **最小架构**: 从701个文件精简到13个核心文件""",
                variables={},
                priority=2
            ),
            ContentBlock(
                id="basic_usage",
                type="fixed",
                title="基本使用",
                template="""## 🚀 基本使用

```bash
# 核心功能 - 开发任务统一入口
python3 main/cli.py develop "任务描述"
python3 main/cli.py develop "任务描述" --template 模板名

# 系统管理
python3 main/cli.py status
python3 main/cli.py hooks install
python3 main/cli.py workflow list
```""",
                variables={},
                priority=3
            ),
            ContentBlock(
                id="simplified_architecture",
                type="fixed",
                title="简化架构",
                template="""## 🏗️ 简化架构

```
Perfect21/
├── core/claude-code-unified-agents/    # 56个官方Agent (不可修改)
├── features/                          # 功能层：编排器
│   ├── capability_discovery/          # 动态功能发现
│   ├── version_manager/               # 版本管理
│   └── git_workflow/                  # Git工作流
├── main/                              # 入口层：CLI
└── modules/                           # 工具层：配置日志
```""",
                variables={},
                priority=4
            ),
            ContentBlock(
                id="extension_rules",
                type="fixed",
                title="扩展规则",
                template="""## 📁 扩展规则

1. **新功能**: 在features/目录创建SubAgent编排器
2. **不重复实现**: 优先寻找现有Agent
3. **保持轻量**: 新增代码必须有明确编排价值""",
                variables={},
                priority=5
            )
        ]

        # 动态内容块
        dynamic_blocks = [
            ContentBlock(
                id="current_status",
                type="dynamic",
                title="当前状态",
                template="""## 📊 当前状态

### 🚀 版本信息
- **当前版本**: {current_version} ({status})
- **最后更新**: {last_update}

### 🔧 模块状态
{module_status}""",
                variables={
                    "current_version": "v2.3.0",
                    "status": "生产就绪",
                    "last_update": "{auto_date}",
                    "module_status": "{auto_modules}"
                },
                lifecycle_days=7,
                update_strategy="replace",
                priority=10
            ),
            ContentBlock(
                id="documentation_note",
                type="volatile",
                title="文档说明",
                template="""> 📝 **文档说明**: 固定核心部分(上半)请勿频繁修改，动态状态部分(下半)可随时更新""",
                variables={},
                lifecycle_days=30,
                update_strategy="replace",
                priority=99
            )
        ]

        return DocumentTemplate(
            name="perfect21_core",
            version="1.0.0",
            description="Perfect21核心文档模板",
            fixed_blocks=fixed_blocks,
            dynamic_blocks=dynamic_blocks,
            metadata={
                "created": datetime.now().isoformat(),
                "author": "claude_md_manager",
                "purpose": "intelligent_document_management"
            }
        )

    def render_template(self, template: DocumentTemplate, data: Dict[str, Any] = None) -> str:
        """渲染模板为文档内容"""
        if data is None:
            data = {}

        # 自动变量
        auto_vars = {
            "auto_date": datetime.now().strftime('%Y-%m-%d'),
            "auto_timestamp": datetime.now().isoformat(),
            "auto_modules": self._generate_module_status(),
            "auto_features_count": self._count_features()
        }

        # 合并数据
        merged_data = {**auto_vars, **data}

        content_parts = []

        # 文档标题
        content_parts.append("# Perfect21 项目核心文档\n")

        # 渲染固定内容块
        content_parts.append("<!-- ================== 固定核心部分 - 请勿频繁修改 ================== -->\n")

        for block in sorted(template.fixed_blocks, key=lambda x: x.priority):
            rendered_content = self._render_block(block, merged_data)
            if rendered_content:
                content_parts.append(rendered_content + "\n")

        # 渲染动态内容块
        content_parts.append("<!-- ================== 动态状态部分 - 可随时更新 ================== -->\n")

        for block in sorted(template.dynamic_blocks, key=lambda x: x.priority):
            rendered_content = self._render_block(block, merged_data)
            if rendered_content:
                content_parts.append(rendered_content + "\n")

        return "\n".join(content_parts)

    def _render_block(self, block: ContentBlock, data: Dict[str, Any]) -> str:
        """渲染单个内容块"""
        template_str = block.template

        # 替换变量
        for var_name, var_value in {**block.variables, **data}.items():
            if isinstance(var_value, str):
                template_str = template_str.replace(f"{{{var_name}}}", var_value)
            elif var_value is not None:
                template_str = template_str.replace(f"{{{var_name}}}", str(var_value))

        return template_str

    def _generate_module_status(self) -> str:
        """生成模块状态信息"""
        features_dir = os.path.join(self.project_root, 'features')
        status_lines = []

        if os.path.exists(features_dir):
            for module_name in sorted(os.listdir(features_dir)):
                module_path = os.path.join(features_dir, module_name)
                if os.path.isdir(module_path) and not module_name.startswith('.'):
                    # 简单的模块状态检查
                    capability_file = os.path.join(module_path, 'capability.py')
                    if os.path.exists(capability_file):
                        status_lines.append(f"- **{module_name}**: ✅ 正常")
                    else:
                        status_lines.append(f"- **{module_name}**: ⚠️ 基础")

        return "\n".join(status_lines) if status_lines else "- 暂无模块"

    def _count_features(self) -> int:
        """统计功能模块数量"""
        features_dir = os.path.join(self.project_root, 'features')
        if os.path.exists(features_dir):
            return len([d for d in os.listdir(features_dir)
                       if os.path.isdir(os.path.join(features_dir, d)) and not d.startswith('.')])
        return 0

    def save_template(self, template: DocumentTemplate, filename: str = None) -> str:
        """保存模板到文件"""
        if filename is None:
            filename = f"{template.name}_v{template.version}.yaml"

        template_path = os.path.join(self.templates_dir, filename)

        template_data = {
            'name': template.name,
            'version': template.version,
            'description': template.description,
            'metadata': template.metadata,
            'fixed_blocks': [asdict(block) for block in template.fixed_blocks],
            'dynamic_blocks': [asdict(block) for block in template.dynamic_blocks]
        }

        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)

        return template_path

    def load_template(self, filename: str) -> DocumentTemplate:
        """从文件加载模板"""
        template_path = os.path.join(self.templates_dir, filename)

        with open(template_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        fixed_blocks = [ContentBlock(**block) for block in data['fixed_blocks']]
        dynamic_blocks = [ContentBlock(**block) for block in data['dynamic_blocks']]

        return DocumentTemplate(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            fixed_blocks=fixed_blocks,
            dynamic_blocks=dynamic_blocks,
            metadata=data['metadata']
        )

    def get_block_by_id(self, template: DocumentTemplate, block_id: str) -> Optional[ContentBlock]:
        """根据ID获取内容块"""
        all_blocks = template.fixed_blocks + template.dynamic_blocks
        for block in all_blocks:
            if block.id == block_id:
                return block
        return None

    def update_block_variables(self, template: DocumentTemplate, block_id: str, new_variables: Dict[str, Any]) -> bool:
        """更新内容块变量"""
        block = self.get_block_by_id(template, block_id)
        if block:
            block.variables.update(new_variables)
            return True
        return False

    def analyze_current_document(self) -> Dict[str, Any]:
        """分析当前文档结构"""
        if not os.path.exists(self.claude_md_path):
            return {'exists': False}

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        analysis = {
            'exists': True,
            'total_lines': len(content.split('\n')),
            'has_fixed_marker': '<!-- =====' in content and '固定核心' in content,
            'has_dynamic_marker': '<!-- =====' in content and '动态状态' in content,
            'detected_blocks': self._detect_content_blocks(content),
            'size_bytes': len(content.encode('utf-8'))
        }

        return analysis

    def _detect_content_blocks(self, content: str) -> List[Dict[str, Any]]:
        """检测内容中的现有块"""
        blocks = []
        lines = content.split('\n')

        current_block = None
        for i, line in enumerate(lines):
            if line.startswith('## '):
                if current_block:
                    blocks.append(current_block)

                current_block = {
                    'title': line[3:].strip(),
                    'start_line': i,
                    'content_lines': []
                }
            elif current_block:
                current_block['content_lines'].append(line)

        if current_block:
            blocks.append(current_block)

        return blocks

    def generate_document(self, custom_data: Dict[str, Any] = None) -> str:
        """生成完整文档"""
        return self.render_template(self.default_template, custom_data)

if __name__ == "__main__":
    # 测试模板引擎
    engine = TemplateEngine()

    # 生成文档
    doc_content = engine.generate_document({
        "current_version": "v2.3.1",
        "status": "测试版本"
    })

    print("=== 生成的文档内容 ===")
    print(doc_content[:500] + "..." if len(doc_content) > 500 else doc_content)

    # 分析现有文档
    analysis = engine.analyze_current_document()
    print(f"\n=== 文档分析 ===")
    print(f"文档存在: {analysis.get('exists')}")
    if analysis.get('exists'):
        print(f"总行数: {analysis.get('total_lines')}")
        print(f"有固定标记: {analysis.get('has_fixed_marker')}")
        print(f"有动态标记: {analysis.get('has_dynamic_marker')}")
        print(f"检测到块数: {len(analysis.get('detected_blocks', []))}")

    # 保存默认模板
    template_path = engine.save_template(engine.default_template)
    print(f"\n模板已保存到: {template_path}")