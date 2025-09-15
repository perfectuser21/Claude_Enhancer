"""
version_manager功能描述文件
Perfect21的统一版本管理和发布系统
"""

CAPABILITY = {
    "name": "version_manager",
    "version": "2.1.0",
    "description": "Perfect21的统一版本管理和发布系统",
    "category": "management",
    "priority": "high",
    "is_core": True,

    "agents_can_use": [
        "orchestrator",
        "project-manager",
        "deployment-manager",
        "devops-engineer",
        "backend-architect"
    ],

    "functions": {
        "get_current_version": "获取当前Perfect21版本",
        "set_version": "设置新的版本号",
        "bump_version": "自动递增版本号(major/minor/patch)",
        "sync_all_versions": "同步所有模块的版本号",
        "validate_version": "验证版本号格式",
        "create_release": "创建新的发布版本",
        "get_version_info": "获取详细的版本信息",
        "check_version_consistency": "检查版本一致性",
        "generate_changelog": "生成版本更新日志",
        "create_version_tag": "创建Git版本标签"
    },

    "integration_points": [
        "project_initialization",
        "pre_commit",
        "pre_release",
        "post_release",
        "version_update",
        "deployment"
    ],

    "dependencies": [
        "semantic_version",
        "git",
        "pathlib",
        "typing",
        "datetime",
        "json"
    ],

    "versioning_rules": {
        "scheme": "semantic",  # major.minor.patch
        "format": "x.y.z",
        "pre_release_format": "x.y.z-alpha.n | x.y.z-beta.n | x.y.z-rc.n",
        "tag_format": "v{version}",
        "branch_format": "release/v{version}"
    },

    "version_sources": [
        "__init__.py",
        "modules/config.py",
        "features/*/capability.py",
        "api/*.py",
        "setup.py",
        "pyproject.toml"
    ],

    "release_types": {
        "major": "Breaking changes, incompatible API changes",
        "minor": "New features, backwards compatible",
        "patch": "Bug fixes, backwards compatible",
        "pre-release": "Alpha, beta, release candidate versions"
    },

    "configuration": {
        "auto_sync": True,
        "strict_validation": True,
        "require_changelog": True,
        "create_git_tags": True,
        "backup_before_change": True
    }
}