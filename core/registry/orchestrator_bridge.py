#!/usr/bin/env python3
"""
@orchestrator集成桥梁
整合到capability_discovery模块中
"""

import json
import os

class OrchestratorBridge:
    """@orchestrator集成桥梁"""

    def __init__(self):
        self.capabilities = self._load_capabilities_manifest()

    def _load_capabilities_manifest(self) -> dict:
        """加载Perfect21完整能力清单"""

        # 读取已注册的功能
        capabilities_file = os.path.join(
            os.getcwd(), 'core', 'claude-code-unified-agents', 'perfect21_capabilities.json'
        )

        registered_capabilities = {}
        if os.path.exists(capabilities_file):
            try:
                with open(capabilities_file, 'r', encoding='utf-8') as f:
                    registered_capabilities = json.load(f)
            except Exception:
                pass

        return {
            "platform_info": {
                "name": "Perfect21",
                "version": "2.4.0",
                "description": "企业级多Agent协作开发平台扩展包",
                "core_agents": 56,
                "architecture": "claude-code-unified-agents扩展功能"
            },
            "registered_features": registered_capabilities,
            "integration_features": {
                "git_workflow": True,
                "version_management": True,
                "claude_md_management": True,
                "capability_discovery": True
            }
        }

    def get_capabilities_for_orchestrator(self) -> str:
        """为@orchestrator生成能力描述"""

        capabilities = self.capabilities
        registered = capabilities["registered_features"]

        orchestrator_briefing = f"""
# Perfect21平台能力简报

## 平台概览
- **名称**: {capabilities['platform_info']['name']} v{capabilities['platform_info']['version']}
- **定位**: {capabilities['platform_info']['description']}
- **核心**: {capabilities['platform_info']['core_agents']}个专业Agent + Perfect21扩展功能

## Perfect21已注册功能

"""

        # 添加已注册的功能
        for name, feature in registered.items():
            agents_list = ', '.join(feature.get('agents_can_use', ['orchestrator']))
            functions_list = ', '.join(feature.get('functions', []))

            orchestrator_briefing += f"""
### {feature.get('name', name)}
- **描述**: {feature.get('description', '未提供描述')}
- **类别**: {feature.get('category', 'unknown')}
- **优先级**: {feature.get('priority', 'normal')}
- **可使用的Agent**: {agents_list}
- **提供功能**: {functions_list}
"""

        orchestrator_briefing += f"""

## 如何使用Perfect21功能

作为@orchestrator，你可以：

1. **调用Git工作流功能**:
   - "使用Perfect21的git_workflow功能创建feature分支"
   - "调用Perfect21的Git hooks进行代码质量检查"

2. **使用版本管理功能**:
   - "让Perfect21的version_manager检查版本一致性"
   - "调用Perfect21进行版本升级"

3. **使用CLAUDE.md管理功能**:
   - "让Perfect21的claude_md_manager更新项目文档"
   - "调用Perfect21进行文档生命周期管理"

4. **动态发现新功能**:
   - "让Perfect21扫描并注册新功能"
   - "获取Perfect21的最新功能清单"

## 重要提示

Perfect21是功能扩展包，提供claude-code-unified-agents没有的功能。你可以直接调用这些功能，无需通过Perfect21的中间层。
"""

        return orchestrator_briefing

    def save_capabilities_manifest(self):
        """保存能力清单供@orchestrator读取"""
        manifest_path = "/tmp/perfect21_capabilities.json"
        briefing_path = "/tmp/perfect21_orchestrator_briefing.md"

        # 保存JSON格式的详细能力清单
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.capabilities, f, indent=2, ensure_ascii=False)

        # 保存给@orchestrator的简报
        with open(briefing_path, 'w', encoding='utf-8') as f:
            f.write(self.get_capabilities_for_orchestrator())

        return {
            "manifest_file": manifest_path,
            "briefing_file": briefing_path,
            "capabilities_count": len(self.capabilities["registered_features"])
        }

    def get_perfect21_info_for_orchestrator(self) -> dict:
        """获取Perfect21信息供@orchestrator使用"""

        # 保存能力清单
        capabilities_info = self.save_capabilities_manifest()

        return {
            "platform_info": self.capabilities["platform_info"],
            "registered_features": self.capabilities["registered_features"],
            "capabilities_briefing": self.get_capabilities_for_orchestrator(),
            "manifest_files": capabilities_info
        }