#!/usr/bin/env python3
"""
Perfect21 - 企业级多Agent协作开发平台
基于claude-code-unified-agents的智能开发助手
"""

import os
import sys
import argparse
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.config import config
from modules.utils import setup_logging, get_project_info, format_execution_result
from modules.logger import log_info, log_error, log_git_operation
from features.git_workflow import GitHooks, WorkflowManager, BranchManager

class Perfect21:
    """Perfect21主程序"""

    def __init__(self):
        self.project_root = os.getcwd()
        self.config = config

        # 设置日志
        setup_logging(
            self.config.get('logging.level', 'INFO'),
            self.config.get('logging.file', 'logs/perfect21.log')
        )

        # 初始化组件
        self.git_hooks = GitHooks(self.project_root)
        self.workflow_manager = WorkflowManager(self.project_root)
        self.branch_manager = BranchManager(self.project_root)

        log_info("Perfect21初始化完成")

    def status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            project_info = get_project_info(self.project_root)
            hook_status = self.git_hooks.get_hook_status()
            workflow_status = self.workflow_manager.get_workflow_status()
            branch_status = self.branch_manager.get_branch_status()

            status_info = {
                'perfect21': {
                    'version': self.config.get('perfect21.version'),
                    'mode': self.config.get('perfect21.mode'),
                    'core_agents_available': project_info.get('has_core_agents', False),
                    'agent_count': project_info.get('agent_count', 0)
                },
                'project': project_info,
                'git_hooks': hook_status,
                'workflow': workflow_status,
                'branches': branch_status
            }

            return {
                'success': True,
                'status': status_info
            }

        except Exception as e:
            log_error("获取系统状态失败", e)
            return {
                'success': False,
                'error': str(e)
            }

    def git_hook_handler(self, hook_type: str, *args) -> Dict[str, Any]:
        """Git钩子处理器"""
        try:
            log_git_operation(f"触发{hook_type}钩子", {'args': args})

            if hook_type == 'pre-commit':
                result = self.git_hooks.pre_commit_hook()
            elif hook_type == 'pre-push':
                remote = args[0] if args else 'origin'
                result = self.git_hooks.pre_push_hook(remote)
            elif hook_type == 'post-checkout':
                old_ref, new_ref, branch_flag = args[:3] if len(args) >= 3 else ('', '', '1')
                result = self.git_hooks.post_checkout_hook(old_ref, new_ref, branch_flag)
            else:
                return {
                    'success': False,
                    'message': f"不支持的钩子类型: {hook_type}"
                }

            log_git_operation(f"{hook_type}钩子完成", result)
            return result

        except Exception as e:
            log_error(f"Git钩子处理失败: {hook_type}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"{hook_type}钩子执行失败"
            }

    def workflow_command(self, action: str, *args) -> Dict[str, Any]:
        """工作流命令处理"""
        try:
            if action == 'create-feature':
                if not args:
                    return {'success': False, 'message': '请提供功能名称'}
                feature_name = args[0]
                from_branch = args[1] if len(args) > 1 else 'develop'
                result = self.workflow_manager.create_feature_branch(feature_name, from_branch)

            elif action == 'create-release':
                if not args:
                    return {'success': False, 'message': '请提供版本号'}
                version = args[0]
                from_branch = args[1] if len(args) > 1 else 'develop'
                result = self.workflow_manager.create_release_branch(version, from_branch)

            elif action == 'merge-to-main':
                if not args:
                    return {'success': False, 'message': '请提供源分支名称'}
                source_branch = args[0]
                delete_source = len(args) < 2 or args[1].lower() != 'keep'
                result = self.workflow_manager.merge_to_main(source_branch, delete_source)

            elif action == 'branch-info':
                branch_name = args[0] if args else None
                if branch_name:
                    result = self.branch_manager.validate_branch_name(branch_name)
                else:
                    result = self.branch_manager.get_branch_status()

            elif action == 'cleanup':
                days = int(args[0]) if args else 30
                result = self.branch_manager.cleanup_old_branches(days)

            else:
                return {
                    'success': False,
                    'message': f"不支持的工作流操作: {action}"
                }

            log_git_operation(f"工作流操作: {action}", result)
            return result

        except Exception as e:
            log_error(f"工作流命令失败: {action}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"工作流操作{action}失败"
            }

    def run_command(self, command: str, args: list = None) -> Dict[str, Any]:
        """运行命令"""
        args = args or []

        try:
            if command == 'status':
                return self.status()
            elif command == 'git-hook':
                if not args:
                    return {'success': False, 'message': '请指定钩子类型'}
                return self.git_hook_handler(args[0], *args[1:])
            elif command == 'workflow':
                if not args:
                    return {'success': False, 'message': '请指定工作流操作'}
                return self.workflow_command(args[0], *args[1:])
            else:
                return {
                    'success': False,
                    'message': f"未知命令: {command}"
                }

        except Exception as e:
            log_error(f"命令执行失败: {command}", e)
            return {
                'success': False,
                'error': str(e),
                'message': f"命令{command}执行失败"
            }

    def cleanup(self) -> None:
        """清理Perfect21实例，释放内存"""
        try:
            # 清理Git Hooks系统
            if hasattr(self, 'git_hooks') and self.git_hooks:
                if hasattr(self.git_hooks, 'cleanup'):
                    self.git_hooks.cleanup()

            # 清理工作流管理器
            if hasattr(self, 'workflow_manager') and self.workflow_manager:
                if hasattr(self.workflow_manager, 'cleanup'):
                    self.workflow_manager.cleanup()

            # 清理分支管理器
            if hasattr(self, 'branch_manager') and self.branch_manager:
                if hasattr(self.branch_manager, 'cleanup'):
                    self.branch_manager.cleanup()

            # 清理配置引用
            if hasattr(self, 'config'):
                self.config = None

            # 强制垃圾回收
            import gc
            gc.collect()

            log_info("Perfect21清理完成")

        except Exception as e:
            log_error("Perfect21清理失败", e)

    def __del__(self):
        """析构函数，确保资源被清理"""
        try:
            self.cleanup()
        except:
            pass

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 - 基于claude-code-unified-agents的Git工作流管理')
    parser.add_argument('command', help='命令: status, git-hook, workflow')
    parser.add_argument('args', nargs='*', help='命令参数')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 创建Perfect21实例
    p21 = Perfect21()

    # 执行命令
    result = p21.run_command(args.command, args.args)

    # 输出结果
    if args.verbose:
        print(format_execution_result(result))
    else:
        if result.get('success'):
            print(result.get('message', '操作成功'))
        else:
            print(f"错误: {result.get('message', '操作失败')}")
            if result.get('error'):
                print(f"详情: {result['error']}")

    # 返回退出码
    sys.exit(0 if result.get('success') else 1)

if __name__ == '__main__':
    main()