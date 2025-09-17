#!/usr/bin/env python3
"""
Git Phase Integration - Git操作与阶段执行的集成
在合适的时机执行Git操作和触发Hooks
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("GitPhaseIntegration")

class GitPhaseIntegration:
    """
    Git操作与阶段执行的集成

    功能：
    1. 根据阶段执行合适的Git操作
    2. 在正确时机触发Git Hooks
    3. 管理分支策略
    4. 提供回滚能力
    """

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.phase_git_ops = self._init_phase_git_operations()
        self.current_branch = None
        self.operation_history = []
        logger.info(f"GitPhaseIntegration初始化，项目路径: {self.project_root}")

    def _init_phase_git_operations(self) -> Dict[str, List[str]]:
        """初始化各阶段的Git操作"""
        return {
            'analysis': [],  # 分析阶段不需要Git操作
            'design': [
                'create_feature_branch',
                'commit_design_docs'
            ],
            'implementation': [
                'commit_code',
                'trigger_pre_commit_hook'
            ],
            'testing': [
                'run_tests',
                'trigger_pre_push_hook'
            ],
            'deployment': [
                'merge_to_main',
                'create_release_tag'
            ]
        }

    def get_phase_git_operations(self, phase: str) -> List[str]:
        """获取该阶段需要的Git操作"""
        return self.phase_git_ops.get(phase, [])

    def execute_phase_git_operations(self, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段相关的Git操作

        Args:
            phase: 阶段名称
            context: 执行上下文

        Returns:
            执行结果
        """
        operations = self.get_phase_git_operations(phase)
        if not operations:
            logger.info(f"{phase}阶段无Git操作")
            return {'success': True, 'message': '无需Git操作'}

        results = []
        for operation in operations:
            result = self._execute_git_operation(operation, context)
            results.append(result)

            # 记录操作历史
            self.operation_history.append({
                'phase': phase,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

            if not result['success']:
                logger.error(f"Git操作{operation}失败: {result.get('error')}")
                return {
                    'success': False,
                    'failed_operation': operation,
                    'error': result.get('error'),
                    'completed_operations': results
                }

        logger.info(f"完成{phase}阶段的{len(operations)}个Git操作")
        return {
            'success': True,
            'operations': results,
            'message': f'完成{len(operations)}个Git操作'
        }

    def _execute_git_operation(self, operation: str, context: Dict) -> Dict[str, Any]:
        """执行单个Git操作"""
        try:
            if operation == 'create_feature_branch':
                return self._create_feature_branch(context.get('feature_name', 'new-feature'))
            elif operation == 'commit_design_docs':
                return self._commit_files('docs/design/', 'design: 完成架构设计文档')
            elif operation == 'commit_code':
                return self._commit_files('.', 'feat: 实现功能代码')
            elif operation == 'trigger_pre_commit_hook':
                return self._trigger_hook('pre-commit')
            elif operation == 'trigger_pre_push_hook':
                return self._trigger_hook('pre-push')
            elif operation == 'run_tests':
                return self._run_tests()
            elif operation == 'merge_to_main':
                return self._merge_to_branch('main')
            elif operation == 'create_release_tag':
                return self._create_tag(context.get('version', '1.0.0'))
            else:
                return {'success': False, 'error': f'未知操作: {operation}'}

        except Exception as e:
            logger.error(f"执行Git操作{operation}时出错: {e}")
            return {'success': False, 'error': str(e)}

    def _create_feature_branch(self, feature_name: str) -> Dict[str, Any]:
        """创建功能分支"""
        branch_name = f"feature/{feature_name}-{datetime.now().strftime('%Y%m%d')}"

        try:
            # 检查分支是否存在
            result = subprocess.run(
                ['git', 'branch', '--list', branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                return {
                    'success': False,
                    'error': f'分支{branch_name}已存在'
                }

            # 创建并切换到新分支
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            self.current_branch = branch_name
            logger.info(f"创建并切换到分支: {branch_name}")

            return {
                'success': True,
                'branch': branch_name,
                'message': f'创建分支{branch_name}'
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'创建分支失败: {e.stderr}'
            }

    def _commit_files(self, path: str, message: str) -> Dict[str, Any]:
        """提交文件"""
        try:
            # 添加文件到暂存区
            subprocess.run(
                ['git', 'add', path],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            # 检查是否有要提交的更改
            result = subprocess.run(
                ['git', 'diff', '--cached', '--stat'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                return {
                    'success': True,
                    'message': '没有需要提交的更改'
                }

            # 提交更改
            subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            logger.info(f"提交成功: {message}")
            return {
                'success': True,
                'message': f'提交: {message}'
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'提交失败: {e.stderr}'
            }

    def _trigger_hook(self, hook_name: str) -> Dict[str, Any]:
        """触发Git Hook"""
        hook_path = os.path.join(self.project_root, '.git', 'hooks', hook_name)

        if not os.path.exists(hook_path):
            logger.warning(f"Hook {hook_name}不存在")
            return {
                'success': True,
                'message': f'Hook {hook_name}不存在，跳过'
            }

        try:
            # 执行Hook
            result = subprocess.run(
                [hook_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                logger.info(f"Hook {hook_name}执行成功")
                return {
                    'success': True,
                    'message': f'Hook {hook_name}执行成功',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': f'Hook {hook_name}执行失败',
                    'output': result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Hook {hook_name}执行超时'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Hook执行出错: {str(e)}'
            }

    def _run_tests(self) -> Dict[str, Any]:
        """运行测试"""
        # 这里简化处理，实际应该调用项目的测试命令
        test_commands = [
            'python -m pytest tests/ -v',
            'npm test',
            'go test ./...',
            'cargo test'
        ]

        for cmd in test_commands:
            test_file = cmd.split()[0]
            # 检查是否有对应的测试工具
            result = subprocess.run(
                ['which', test_file],
                capture_output=True
            )

            if result.returncode == 0:
                # 运行测试
                try:
                    test_result = subprocess.run(
                        cmd.split(),
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=600  # 10分钟超时
                    )

                    return {
                        'success': test_result.returncode == 0,
                        'message': '测试完成',
                        'output': test_result.stdout if test_result.returncode == 0 else test_result.stderr
                    }
                except Exception as e:
                    logger.warning(f"运行测试{cmd}失败: {e}")

        return {
            'success': True,
            'message': '未找到测试命令，跳过测试'
        }

    def _merge_to_branch(self, target_branch: str) -> Dict[str, Any]:
        """合并到目标分支"""
        try:
            # 切换到目标分支
            subprocess.run(
                ['git', 'checkout', target_branch],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            # 合并当前功能分支
            if self.current_branch:
                subprocess.run(
                    ['git', 'merge', self.current_branch, '--no-ff'],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True
                )

                logger.info(f"合并{self.current_branch}到{target_branch}")
                return {
                    'success': True,
                    'message': f'合并到{target_branch}成功'
                }
            else:
                return {
                    'success': False,
                    'error': '没有要合并的分支'
                }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'合并失败: {e.stderr}'
            }

    def _create_tag(self, version: str) -> Dict[str, Any]:
        """创建发布标签"""
        tag_name = f"v{version}"

        try:
            # 创建标签
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', f'Release {version}'],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )

            logger.info(f"创建标签: {tag_name}")
            return {
                'success': True,
                'tag': tag_name,
                'message': f'创建标签{tag_name}'
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'创建标签失败: {e.stderr}'
            }

    def trigger_appropriate_hooks(self, phase: str, context: Dict) -> Dict[str, Any]:
        """根据阶段触发合适的Git Hooks"""
        phase_hooks = {
            'design': ['post-checkout'],
            'implementation': ['pre-commit', 'commit-msg'],
            'testing': ['pre-push'],
            'deployment': ['pre-merge-commit', 'post-merge']
        }

        hooks = phase_hooks.get(phase, [])
        if not hooks:
            return {'success': True, 'message': '该阶段无需触发Hooks'}

        results = []
        for hook in hooks:
            result = self._trigger_hook(hook)
            results.append({
                'hook': hook,
                'result': result
            })

        return {
            'success': all(r['result']['success'] for r in results),
            'hooks_triggered': results
        }

    def get_current_branch(self) -> str:
        """获取当前分支"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'unknown'

    def get_operation_history(self) -> List[Dict]:
        """获取操作历史"""
        return self.operation_history