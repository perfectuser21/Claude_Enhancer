#!/usr/bin/env python3
"""
CLAUDE.md Manager Capability Definition
Perfect21功能模块能力描述文件
"""

# Perfect21功能模块标准描述
CAPABILITY_INFO = {
    "name": "claude_md_manager",
    "display_name": "CLAUDE.md自动管理器",
    "version": "1.0.0",
    "description": "基于Claude Code最佳实践的CLAUDE.md动态更新和内存管理系统",
    "category": "documentation",
    "tags": ["claude-code", "memory", "documentation", "auto-update"],

    # 功能特性
    "features": [
        {
            "name": "dynamic_update",
            "description": "动态更新CLAUDE.md内容，自动同步项目状态",
            "subagent": "@technical-writer"
        },
        {
            "name": "memory_synchronization",
            "description": "内存银行同步，确保文档与代码状态一致",
            "subagent": "@business-analyst"
        },
        {
            "name": "template_management",
            "description": "模板管理系统，支持分层内存配置",
            "subagent": "@api-designer"
        },
        {
            "name": "content_analysis",
            "description": "智能内容分析，识别静态和动态区块",
            "subagent": "@code-reviewer"
        }
    ],

    # 依赖关系
    "dependencies": {
        "internal": [
            "version_manager",  # 获取版本信息
            "capability_discovery",  # 功能模块扫描
            "git_workflow"  # Git状态集成
        ],
        "external": [
            "jinja2",  # 模板引擎
            "markdown",  # Markdown处理
            "pyyaml"  # 配置文件处理
        ]
    },

    # CLI命令
    "cli_commands": [
        {
            "name": "claude-md",
            "description": "CLAUDE.md管理命令组",
            "subcommands": [
                {
                    "name": "sync",
                    "description": "同步CLAUDE.md内容",
                    "usage": "python3 main/cli.py claude-md sync"
                },
                {
                    "name": "status",
                    "description": "检查同步状态",
                    "usage": "python3 main/cli.py claude-md status"
                },
                {
                    "name": "template",
                    "description": "管理模板",
                    "usage": "python3 main/cli.py claude-md template [list|update]"
                },
                {
                    "name": "memory",
                    "description": "快速记忆管理",
                    "usage": "python3 main/cli.py claude-md memory --add \"记忆内容\""
                }
            ]
        }
    ],

    # API端点
    "api_endpoints": [
        {
            "path": "/claude-md/sync",
            "method": "POST",
            "description": "触发CLAUDE.md同步"
        },
        {
            "path": "/claude-md/status",
            "method": "GET",
            "description": "获取同步状态"
        },
        {
            "path": "/claude-md/memory",
            "method": "POST",
            "description": "添加快速记忆"
        }
    ],

    # Git钩子集成
    "git_hooks": [
        {
            "hook": "pre-commit",
            "action": "sync_project_status",
            "description": "提交前同步项目状态信息"
        },
        {
            "hook": "post-merge",
            "action": "sync_after_merge",
            "description": "合并后同步版本和功能变更"
        },
        {
            "hook": "post-checkout",
            "action": "update_branch_context",
            "description": "切换分支后更新分支上下文"
        }
    ],

    # SubAgent调用映射
    "subagent_mappings": {
        "content_generation": "@technical-writer",
        "template_analysis": "@api-designer",
        "memory_organization": "@business-analyst",
        "quality_check": "@code-reviewer",
        "sync_coordination": "@orchestrator"
    }
}

def get_capability_info():
    """获取功能模块能力信息"""
    return CAPABILITY_INFO