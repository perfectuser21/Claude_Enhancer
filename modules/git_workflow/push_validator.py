#!/usr/bin/env python3
"""
推送验证器
负责推送前的完整性验证
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

logger = logging.getLogger("PushValidator")

class PushValidator:
    """推送验证器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # 受保护的分支
        self.protected_branches = ['main', 'master', 'production', 'release']

        logger.info("推送验证器初始化完成")

    def validate_push(self, remote: str, remote_url: str, local_ref: str, remote_ref: str) -> Dict[str, Any]:
        """验证推送操作"""
        try:
            # 解析分支信息
            branch_name = self._extract_branch_name(local_ref)

            # 检查分支保护
            protection_check = self._check_branch_protection(branch_name)

            # 检查提交历史
            commit_check = self._check_commit_history(local_ref, remote_ref)

            # 检查远程状态
            remote_check = self._check_remote_status(remote, remote_url)

            # 评估推送风险
            risk_assessment = self._assess_push_risk(branch_name, commit_check)

            return {
                'branch_name': branch_name,
                'protection_check': protection_check,
                'commit_check': commit_check,
                'remote_check': remote_check,
                'risk_assessment': risk_assessment,
                'validation_time': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"推送验证失败: {e}")
            return {
                'error': str(e),
                'branch_name': 'unknown',
                'validation_failed': True
            }

    def _extract_branch_name(self, ref: str) -> str:
        """从引用中提取分支名"""
        if ref.startswith('refs/heads/'):
            return ref[11:]  # 移除 'refs/heads/' 前缀
        return ref

    def _check_branch_protection(self, branch_name: str) -> Dict[str, Any]:
        """检查分支保护策略"""
        is_protected = branch_name in self.protected_branches

        protection_rules = []
        if is_protected:
            protection_rules.extend([
                "禁止直接推送到受保护分支",
                "需要通过Pull Request流程",
                "需要代码审查和批准"
            ])

        return {
            'is_protected': is_protected,
            'protection_rules': protection_rules,
            'should_block': is_protected
        }

    def _check_commit_history(self, local_ref: str, remote_ref: str) -> Dict[str, Any]:
        """检查提交历史"""
        try:
            # 获取待推送的提交数量
            count_result = subprocess.run(
                ['git', 'rev-list', '--count', f'{remote_ref}..{local_ref}'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            commit_count = int(count_result.stdout.strip()) if count_result.stdout.strip() else 0

            # 获取提交列表
            if commit_count > 0:
                commits_result = subprocess.run(
                    ['git', 'log', '--oneline', f'{remote_ref}..{local_ref}'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )

                commits = commits_result.stdout.strip().split('\n') if commits_result.stdout.strip() else []
            else:
                commits = []

            return {
                'commit_count': commit_count,
                'commits': commits,
                'has_new_commits': commit_count > 0
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"检查提交历史失败: {e}")
            return {
                'error': str(e),
                'commit_count': 0,
                'commits': [],
                'has_new_commits': False
            }

    def _check_remote_status(self, remote: str, remote_url: str) -> Dict[str, Any]:
        """检查远程仓库状态"""
        try:
            # 检查远程仓库连接
            remote_result = subprocess.run(
                ['git', 'ls-remote', remote],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            return {
                'remote_accessible': True,
                'remote_name': remote,
                'remote_url': remote_url,
                'connection_verified': True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"检查远程仓库失败: {e}")
            return {
                'remote_accessible': False,
                'remote_name': remote,
                'remote_url': remote_url,
                'connection_verified': False,
                'error': str(e)
            }
        except subprocess.TimeoutExpired:
            return {
                'remote_accessible': False,
                'remote_name': remote,
                'remote_url': remote_url,
                'connection_verified': False,
                'error': "远程仓库连接超时"
            }

    def _assess_push_risk(self, branch_name: str, commit_check: Dict[str, Any]) -> Dict[str, Any]:
        """评估推送风险"""
        risk_level = "low"
        risk_factors = []

        # 评估分支风险
        if branch_name in self.protected_branches:
            risk_level = "critical"
            risk_factors.append("推送到受保护分支")

        # 评估提交数量风险
        commit_count = commit_check.get('commit_count', 0)
        if commit_count > 10:
            risk_level = "high" if risk_level != "critical" else risk_level
            risk_factors.append(f"大量提交推送 ({commit_count}个)")
        elif commit_count > 5:
            risk_level = "medium" if risk_level == "low" else risk_level
            risk_factors.append(f"中等数量提交推送 ({commit_count}个)")

        # 评估分支类型风险
        if 'hotfix' in branch_name.lower():
            risk_level = "high" if risk_level not in ["critical", "high"] else risk_level
            risk_factors.append("热修复分支需要特别注意")

        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level, risk_factors)
        }

    def _get_risk_recommendation(self, risk_level: str, risk_factors: List[str]) -> str:
        """获取风险建议"""
        if risk_level == "critical":
            return "强烈建议阻止此推送，使用Pull Request流程"
        elif risk_level == "high":
            return "建议额外审查，确保代码质量和测试覆盖"
        elif risk_level == "medium":
            return "建议进行基础验证，确保功能正常"
        else:
            return "风险较低，可以正常推送"

    def get_push_recommendations(self, branch_name: str, remote: str) -> List[str]:
        """获取推送建议"""
        recommendations = []

        # 基于分支名的建议
        if 'feature' in branch_name.lower():
            recommendations.append("功能分支推送前应确保功能完整")
            recommendations.append("建议创建Pull Request进行代码审查")

        if 'bugfix' in branch_name.lower():
            recommendations.append("修复分支应包含相关测试验证")
            recommendations.append("确保修复不会引入新问题")

        if 'hotfix' in branch_name.lower():
            recommendations.append("热修复需要快速验证和部署")
            recommendations.append("应同时更新相关文档和版本号")

        # 基于远程仓库的建议
        if remote == 'origin':
            recommendations.append("推送到主仓库，确保代码质量")

        return recommendations