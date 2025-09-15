#!/usr/bin/env python3
"""
Perfect21 版本升级决策引擎
基于变更分析自动建议合适的版本升级类型
"""

import os
import re
import json
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .semantic_version import SemanticVersion

class VersionAdvisor:
    """版本升级决策引擎"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.breaking_changes_patterns = [
            # API变更模式
            r'删除.*public.*方法',
            r'移除.*API.*接口',
            r'更改.*public.*签名',
            r'删除.*CLI.*命令',
            r'移除.*配置.*选项',

            # 架构变更模式
            r'重构.*架构',
            r'更换.*核心.*依赖',
            r'迁移.*到.*框架',
            r'重新设计.*系统',

            # 兼容性变更模式
            r'不兼容.*变更',
            r'breaking.*change',
            r'升级.*最低.*版本',
            r'更改.*默认.*行为'
        ]

        self.feature_changes_patterns = [
            # 功能新增模式
            r'新增.*功能',
            r'添加.*模块',
            r'实现.*特性',
            r'集成.*系统',

            # 接口扩展模式
            r'新增.*API',
            r'添加.*CLI.*命令',
            r'扩展.*接口',
            r'支持.*新.*Agent',

            # 配置扩展模式
            r'新增.*配置.*选项',
            r'支持.*新.*参数',
            r'扩展.*配置.*格式'
        ]

        self.patch_changes_patterns = [
            # Bug修复模式
            r'修复.*bug',
            r'解决.*问题',
            r'修正.*错误',
            r'fix.*issue',

            # 性能优化模式
            r'优化.*性能',
            r'提升.*效率',
            r'改进.*速度',
            r'减少.*内存',

            # 文档更新模式
            r'更新.*文档',
            r'完善.*注释',
            r'修改.*README',
            r'补充.*说明'
        ]

    def analyze_changes_since_last_version(self) -> Dict[str, Any]:
        """分析自上次版本以来的变更"""
        try:
            # 获取最新标签
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {'error': '无法获取最新版本标签'}

            last_tag = result.stdout.strip()

            # 获取自上次标签以来的提交
            result = subprocess.run(
                ['git', 'log', f'{last_tag}..HEAD', '--oneline'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {'error': '无法获取提交历史'}

            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # 获取文件变更统计
            result = subprocess.run(
                ['git', 'diff', f'{last_tag}..HEAD', '--name-status'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            file_changes = result.stdout.strip().split('\n') if result.stdout.strip() else []

            return {
                'last_tag': last_tag,
                'commits': commits,
                'file_changes': file_changes,
                'commit_count': len(commits)
            }

        except Exception as e:
            return {'error': f'分析变更失败: {str(e)}'}

    def classify_changes(self, changes_data: Dict[str, Any]) -> Dict[str, Any]:
        """分类变更类型"""
        if 'error' in changes_data:
            return changes_data

        commits = changes_data.get('commits', [])
        file_changes = changes_data.get('file_changes', [])

        # 分析提交消息 - 优先检测Conventional Commits格式
        breaking_indicators = 0
        feature_indicators = 0
        patch_indicators = 0

        # Conventional Commits类型计数
        conventional_types = {
            'feat': 0,
            'fix': 0,
            'docs': 0,
            'style': 0,
            'refactor': 0,
            'test': 0,
            'chore': 0,
            'build': 0,
            'ci': 0,
            'perf': 0
        }

        for commit in commits:
            commit_msg = commit.lower()

            # 提取提交消息部分（去掉hash）
            if ' ' in commit_msg:
                commit_content = commit_msg.split(' ', 1)[1]  # 去掉commit hash部分
            else:
                commit_content = commit_msg

            # 首先检查Conventional Commits格式
            conventional_detected = False
            for commit_type in conventional_types.keys():
                if commit_content.startswith(f'{commit_type}:') or commit_content.startswith(f'{commit_type}('):
                    conventional_types[commit_type] += 1
                    conventional_detected = True

                    # 根据Conventional Commits类型分类
                    if commit_type in ['feat']:
                        feature_indicators += 1
                    elif commit_type in ['fix', 'perf']:
                        patch_indicators += 1
                    elif commit_type in ['docs', 'style', 'refactor', 'test', 'chore', 'build', 'ci']:
                        patch_indicators += 1  # 维护性变更

                    # 检查是否包含BREAKING CHANGE
                    if 'breaking' in commit_content or 'breaking change' in commit_content:
                        breaking_indicators += 1

                    break

            # 如果不是Conventional Commits格式，使用传统模式匹配
            if not conventional_detected:
                # 检查breaking changes
                for pattern in self.breaking_changes_patterns:
                    if re.search(pattern, commit_content, re.IGNORECASE):
                        breaking_indicators += 1
                        break

                # 检查feature changes
                for pattern in self.feature_changes_patterns:
                    if re.search(pattern, commit_content, re.IGNORECASE):
                        feature_indicators += 1
                        break

                # 检查patch changes
                for pattern in self.patch_changes_patterns:
                    if re.search(pattern, commit_content, re.IGNORECASE):
                        patch_indicators += 1
                        break

        # 分析文件变更 - 只有在提交消息模糊时才参考文件路径
        api_changes = 0
        new_features = 0
        config_changes = 0

        # 如果已经有明确的Conventional Commits类型，降低文件路径权重
        has_conventional_commits = sum(conventional_types.values()) > 0

        for change in file_changes:
            if not change.strip():
                continue

            status, filepath = change.split('\t', 1)

            # API相关变更 - 仅在没有明确提交类型时参考
            if any(api_file in filepath for api_file in ['api/', '__init__.py', 'cli.py']):
                if status == 'D':  # 删除API通常是breaking
                    breaking_indicators += 1
                elif status == 'A' and not has_conventional_commits:  # 新增API
                    feature_indicators += 1
                else:  # 修改
                    api_changes += 1

            # 新功能模块 - 更严格的判断
            # 只有在没有Conventional Commits且路径明确是新功能时才计算
            if ('features/' in filepath and status == 'A' and
                not has_conventional_commits and
                not any(fix_pattern in filepath.lower() for fix_pattern in ['fix', 'bug', 'patch', 'repair'])):
                new_features += 1
                feature_indicators += 1

            # 配置文件变更
            if any(config_file in filepath for config_file in ['config', 'capability.py', 'CLAUDE.md']):
                config_changes += 1

        return {
            'breaking_indicators': breaking_indicators,
            'feature_indicators': feature_indicators,
            'patch_indicators': patch_indicators,
            'api_changes': api_changes,
            'new_features': new_features,
            'config_changes': config_changes,
            'total_commits': len(commits),
            'total_file_changes': len(file_changes),
            'conventional_types': conventional_types,
            'has_conventional_commits': has_conventional_commits
        }

    def suggest_version_bump(self, current_version: str) -> Dict[str, Any]:
        """建议版本升级类型"""
        # 分析变更
        changes_data = self.analyze_changes_since_last_version()
        if 'error' in changes_data:
            return changes_data

        classification = self.classify_changes(changes_data)

        # 决策逻辑
        suggestion = self._make_version_decision(classification)

        # 生成新版本号
        try:
            if suggestion['bump_type'] == 'major':
                new_version = SemanticVersion.bump_version(current_version, 'major')
            elif suggestion['bump_type'] == 'minor':
                new_version = SemanticVersion.bump_version(current_version, 'minor')
            elif suggestion['bump_type'] == 'patch':
                new_version = SemanticVersion.bump_version(current_version, 'patch')
            else:
                new_version = current_version

        except Exception as e:
            return {'error': f'生成新版本号失败: {str(e)}'}

        return {
            'current_version': current_version,
            'suggested_version': new_version,
            'bump_type': suggestion['bump_type'],
            'confidence': suggestion['confidence'],
            'reasoning': suggestion['reasoning'],
            'analysis': classification,
            'changes_summary': changes_data
        }

    def _make_version_decision(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """基于分析结果做出版本决策"""
        breaking = classification['breaking_indicators']
        features = classification['feature_indicators']
        patches = classification['patch_indicators']
        new_features = classification['new_features']
        conventional_types = classification.get('conventional_types', {})
        has_conventional = classification.get('has_conventional_commits', False)

        # Major版本判断
        if breaking > 0:
            return {
                'bump_type': 'major',
                'confidence': 'high',
                'reasoning': f'检测到{breaking}个breaking changes指标，建议Major版本升级'
            }

        # Conventional Commits优先判断
        if has_conventional:
            fix_count = conventional_types.get('fix', 0)
            feat_count = conventional_types.get('feat', 0)
            maintenance_count = sum(conventional_types.get(t, 0) for t in ['docs', 'style', 'refactor', 'test', 'chore', 'build', 'ci', 'perf'])

            # 如果只有fix、perf、维护性变更，建议Patch版本
            if fix_count > 0 or maintenance_count > 0:
                if feat_count == 0:  # 没有新功能
                    return {
                        'bump_type': 'patch',
                        'confidence': 'high',
                        'reasoning': f'基于Conventional Commits分析：{fix_count}个fix + {maintenance_count}个维护性变更，建议Patch版本升级'
                    }

            # 如果有feat类型，建议Minor版本
            if feat_count > 0:
                return {
                    'bump_type': 'minor',
                    'confidence': 'high',
                    'reasoning': f'基于Conventional Commits分析：{feat_count}个新功能，建议Minor版本升级'
                }

        # 传统分析逻辑（向后兼容）
        # 新功能模块判断（仅在没有Conventional Commits时使用）
        if new_features > 0 and not has_conventional:
            return {
                'bump_type': 'minor',
                'confidence': 'medium',
                'reasoning': f'检测到{new_features}个新功能模块，建议Minor版本升级'
            }

        # Minor版本判断
        if features > 2 or (features > 0 and patches < features):
            return {
                'bump_type': 'minor',
                'confidence': 'medium',
                'reasoning': f'检测到{features}个功能增强指标，建议Minor版本升级'
            }

        # Patch版本判断
        if patches > 0 or classification['total_commits'] > 0:
            return {
                'bump_type': 'patch',
                'confidence': 'medium',
                'reasoning': f'检测到{patches}个修复/优化指标，建议Patch版本升级'
            }

        # 无变更
        return {
            'bump_type': 'none',
            'confidence': 'high',
            'reasoning': '未检测到需要版本升级的变更'
        }

    def generate_upgrade_report(self, current_version: str) -> str:
        """生成版本升级报告"""
        suggestion = self.suggest_version_bump(current_version)

        if 'error' in suggestion:
            return f"❌ 版本升级分析失败: {suggestion['error']}"

        report = f"""
📊 Perfect21 版本升级建议报告
{'='*50}

🔢 当前版本: {suggestion['current_version']}
🎯 建议版本: {suggestion['suggested_version']}
📈 升级类型: {suggestion['bump_type'].upper()}
🎯 置信度: {suggestion['confidence']}

💡 决策理由:
{suggestion['reasoning']}

📋 变更分析:
- 总提交数: {suggestion['analysis']['total_commits']}
- 文件变更数: {suggestion['analysis']['total_file_changes']}
- Breaking变更指标: {suggestion['analysis']['breaking_indicators']}
- 功能增强指标: {suggestion['analysis']['feature_indicators']}
- 修复优化指标: {suggestion['analysis']['patch_indicators']}
- 新功能模块: {suggestion['analysis']['new_features']}

🔍 详细变更:
"""

        # 添加提交详情
        commits = suggestion['changes_summary'].get('commits', [])
        if commits:
            report += "\n📝 最近提交:\n"
            for commit in commits[:5]:  # 只显示前5个
                report += f"  - {commit}\n"
            if len(commits) > 5:
                report += f"  ... 还有{len(commits) - 5}个提交\n"

        return report

    def validate_version_history(self) -> Dict[str, Any]:
        """验证版本历史合理性"""
        try:
            # 获取所有版本标签
            result = subprocess.run(
                ['git', 'tag', '-l', 'v*', '--sort=-version:refname'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return {'error': '无法获取版本标签'}

            tags = [tag.strip() for tag in result.stdout.strip().split('\n') if tag.strip()]

            if not tags:
                return {'error': '未找到版本标签'}

            # 分析版本历史
            version_history = []
            issues = []

            for i, tag in enumerate(tags):
                version_str = tag[1:] if tag.startswith('v') else tag

                if not SemanticVersion.is_valid(version_str):
                    issues.append(f"无效版本格式: {tag}")
                    continue

                version_info = SemanticVersion.extract_version_info(version_str)

                # 检查版本跳跃
                if i < len(tags) - 1:
                    next_tag = tags[i + 1]
                    next_version_str = next_tag[1:] if next_tag.startswith('v') else next_tag

                    if SemanticVersion.is_valid(next_version_str):
                        comparison = SemanticVersion.compare(next_version_str, version_str)
                        if comparison >= 0:
                            issues.append(f"版本倒序问题: {next_tag} -> {tag}")

                version_history.append({
                    'tag': tag,
                    'version': version_str,
                    'valid': version_info['valid'],
                    'details': version_info
                })

            return {
                'success': True,
                'version_history': version_history,
                'total_versions': len(version_history),
                'issues': issues,
                'latest_version': tags[0] if tags else None
            }

        except Exception as e:
            return {'error': f'验证版本历史失败: {str(e)}'}

if __name__ == "__main__":
    # 测试脚本
    advisor = VersionAdvisor()

    # 测试版本建议
    from .version_manager import VersionManager
    vm = VersionManager()
    current = vm.get_current_version()

    if current:
        print("=== 版本升级建议 ===")
        print(advisor.generate_upgrade_report(current))

        print("\n=== 版本历史验证 ===")
        history = advisor.validate_version_history()
        if history.get('success'):
            print(f"✅ 版本历史验证通过")
            print(f"总版本数: {history['total_versions']}")
            if history['issues']:
                print("⚠️ 发现问题:")
                for issue in history['issues']:
                    print(f"  - {issue}")
        else:
            print(f"❌ 版本历史验证失败: {history.get('error')}")