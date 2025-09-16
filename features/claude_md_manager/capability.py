#!/usr/bin/env python3
"""
CLAUDE.md Manager Capability Definition
Perfect21功能模块能力描述文件
"""

# Perfect21功能模块标准描述
CAPABILITY = {
    "name": "claude_md_manager",
    "version": "2.3.0",
    "description": "Perfect21的CLAUDE.md自动管理和内存同步系统",
    "category": "unknown",
    "priority": "low",
    "is_core": False,

    "agents_can_use": [
        "technical-writer",
        "business-analyst",
        "api-designer",
        "code-reviewer",
        "orchestrator"
    ],

    "functions": {
        "sync_claude_md": "同步CLAUDE.md内容与项目状态",
        "update_memory_bank": "更新内存银行信息",
        "template_management": "管理CLAUDE.md模板",
        "content_analysis": "分析和优化文档内容",
        "auto_update": "自动更新项目状态信息",
        "memory_sync": "内存与代码状态同步",
        "git_integration": "与Git工作流集成"
    },

    "integration_points": [
        "pre_commit",
        "post_merge",
        "post_checkout",
        "version_update",
        "project_status_change"
    ],

    "dependencies": [
        "jinja2",
        "markdown",
        "pyyaml",
        "pathlib",
        "json"
    ],

    "configuration": {
        "auto_sync": True,
        "template_path": "templates/claude_md.j2",
        "backup_enabled": True,
        "memory_retention": 30
    }
}

def get_capability_info():
    """获取功能模块能力信息"""
    return CAPABILITY