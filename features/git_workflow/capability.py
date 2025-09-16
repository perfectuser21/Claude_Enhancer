"""
git_workflow功能描述文件
Perfect21的Git工作流管理功能
"""

CAPABILITY = {
    "name": "git_workflow",
    "version": "2.3.0",
    "description": "Perfect21的Git工作流管理和自动化功能模块",
    "category": "workflow",
    "priority": "high",
    "is_core": True,

    "agents_can_use": [
        "orchestrator",
        "devops-engineer",
        "backend-architect",
        "code-reviewer",
        "test-engineer",
        "deployment-manager"
    ],

    "functions": {
        "install_hooks": "安装Perfect21 Git钩子到项目",
        "uninstall_hooks": "卸载Perfect21 Git钩子",
        "create_feature_branch": "创建符合规范的功能分支",
        "create_release_branch": "创建发布分支",
        "merge_to_main": "安全地合并分支到主分支",
        "branch_analysis": "分析分支状态和保护规则",
        "cleanup_branches": "清理过期分支",
        "validate_commit": "验证提交消息格式",
        "pre_commit_check": "执行提交前检查",
        "pre_push_validation": "执行推送前验证",
        "post_merge_integration": "执行合并后集成测试"
    },

    "integration_points": [
        "pre_commit",
        "commit_msg",
        "pre_push",
        "post_checkout",
        "post_merge",
        "project_initialization",
        "branch_operations"
    ],

    "dependencies": [
        "git",
        "python3",
        "subprocess",
        "pathlib",
        "typing"
    ],

    "hooks_supported": [
        "pre-commit",
        "commit-msg",
        "pre-push",
        "post-checkout",
        "post-merge",
        "post-commit",
        "prepare-commit-msg",
        "pre-rebase",
        "pre-auto-gc",
        "applypatch-msg",
        "pre-applypatch",
        "post-applypatch",
        "post-rewrite"
    ],

    "branch_strategies": [
        "git-flow",
        "github-flow",
        "gitlab-flow",
        "custom"
    ],

    "configuration": {
        "default_branch": "main",
        "protected_branches": ["main", "master", "develop"],
        "require_review": True,
        "auto_delete_merged": False,
        "commit_message_format": "conventional"
    }
}

def get_capability_info():
    """获取功能模块能力信息"""
    return CAPABILITY