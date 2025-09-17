

---
## Perfect21功能区域
_此区域由Perfect21自动管理，包含所有注册的功能_



ity_discovery自动注册 - git_workflow*











## Perfect21功能: git_workflow

**版本**: 2.3.0
**更新时间**: 2025-09-16 18:29:51
**描述**: Perfect21的Git工作流管理和自动化功能模块
**分类**: workflow
**优先级**: high

### 可用函数:
- `install_hooks`: 安装Perfect21 Git钩子到项目
- `uninstall_hooks`: 卸载Perfect21 Git钩子
- `create_feature_branch`: 创建符合规范的功能分支
- `create_release_branch`: 创建发布分支
- `merge_to_main`: 安全地合并分支到主分支
- `branch_analysis`: 分析分支状态和保护规则
- `cleanup_branches`: 清理过期分支
- `validate_commit`: 验证提交消息格式
- `pre_commit_check`: 执行提交前检查
- `pre_push_validation`: 执行推送前验证
- `post_merge_integration`: 执行合并后集成测试

### 集成时机:
- pre_commit
- commit_msg
- pre_push
- post_checkout
- post_merge
- project_initialization
- branch_operations

### 使用方式:
```python
# 调用Perfect21功能
from features.git_workflow import get_manager
manager = get_manager()
result = manager.function_name()
```

---
*此功能由Perfect21 capability_discovery自动注册 - git_workflow*

### capability_discovery
**描述**: 动态发现Perfect21功能并为@orchestrator提供集成桥梁
**类别**: meta | **优先级**: critical
**可用函数**: scan_features, load_capability, register_to_agents, hot_reload, validate_capability, get_capability_catalog, get_perfect21_capabilities, save_capabilities_manifest, get_capabilities_for_orchestrator

### workflow_engine
**描述**: Perfect21多Agent工作流执行引擎，实现真正的并行协作
**类别**: execution | **优先级**: critical
**可用函数**: execute_parallel_tasks, execute_sequential_pipeline, handle_dependencies, monitor_execution, integrate_results, create_task_graph, validate_workflow, get_execution_status

### version_manager
**描述**: Perfect21的统一版本管理和发布系统
**类别**: management | **优先级**: high
**可用函数**: get_current_version, set_version, bump_version, sync_all_versions, validate_version, create_release, get_version_info, check_version_consistency, generate_changelog, create_version_tag, suggest_version_bump, generate_upgrade_report, validate_version_history, analyze_breaking_changes

### git_workflow
**描述**: Perfect21的Git工作流管理和自动化功能模块
**类别**: workflow | **优先级**: high
**可用函数**: install_hooks, uninstall_hooks, create_feature_branch, create_release_branch, merge_to_main, branch_analysis, cleanup_branches, validate_commit, pre_commit_check, pre_push_validation, post_merge_integration

### workflow_templates
**描述**: Perfect21工作流模板系统，提供预定义的多Agent协作模板
**类别**: development | **优先级**: high
**可用函数**: get_template, list_templates, search_templates, create_custom_template, get_templates_by_category, get_templates_by_pattern, export_template, validate_template, get_statistics
