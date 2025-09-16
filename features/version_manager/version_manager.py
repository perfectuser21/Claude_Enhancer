#!/usr/bin/env python3
"""
Perfect21版本管理器
统一管理项目中所有组件的版本
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    from .semantic_version import SemanticVersion, Version
except ImportError:
    # 动态加载时的绝对导入
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from semantic_version import SemanticVersion, Version

logger = logging.getLogger("VersionManager")

class VersionManager:
    """Perfect21版本管理器"""

    def __init__(self, project_root: str = None):
        """
        初始化版本管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root or os.getcwd()
        self.version_sources = self._discover_version_sources()
        self.current_version = None
        self.version_history = []

        logger.info(f"版本管理器初始化 - 项目根目录: {self.project_root}")

    def _discover_version_sources(self) -> List[Dict[str, Any]]:
        """
        发现项目中的版本源文件

        Returns:
            List[Dict]: 版本源文件信息列表
        """
        sources = []
        patterns = [
            # Python文件中的版本定义
            {
                'pattern': '**/__init__.py',
                'regex': r'__version__\s*=\s*["\']([^"\']+)["\']',
                'type': 'python_version'
            },
            {
                'pattern': '**/config.py',
                'regex': r'["\']version["\']\s*:\s*["\']([^"\']+)["\']',
                'type': 'config_version'
            },
            {
                'pattern': '**/capability.py',
                'regex': r'["\']version["\']\s*:\s*["\']([^"\']+)["\']',
                'type': 'capability_version'
            },
            # API文件
            {
                'pattern': 'api/*.py',
                'regex': r'version\s*=\s*["\']([^"\']+)["\']',
                'type': 'api_version'
            },
            # 配置文件
            {
                'pattern': 'setup.py',
                'regex': r'version\s*=\s*["\']([^"\']+)["\']',
                'type': 'setup_version'
            }
        ]

        # 需要排除的目录
        excluded_dirs = {'venv', '.venv', 'env', '.env', 'node_modules', '.git', '__pycache__', '.pytest_cache'}

        for pattern_info in patterns:
            files = list(Path(self.project_root).glob(pattern_info['pattern']))
            for file_path in files:
                # 检查文件路径是否在排除目录中
                if self._should_exclude_path(file_path, excluded_dirs):
                    continue

                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        matches = re.findall(pattern_info['regex'], content)

                        for match in matches:
                            sources.append({
                                'file': str(file_path),
                                'relative_path': str(file_path.relative_to(self.project_root)),
                                'type': pattern_info['type'],
                                'version': match,
                                'regex': pattern_info['regex'],
                                'valid': SemanticVersion.is_valid(match)
                            })
                    except Exception as e:
                        logger.warning(f"读取文件 {file_path} 失败: {e}")

        logger.info(f"发现 {len(sources)} 个版本源")
        return sources

    def _should_exclude_path(self, file_path: Path, excluded_dirs: set) -> bool:
        """
        检查文件路径是否应该被排除

        Args:
            file_path: 文件路径
            excluded_dirs: 排除的目录集合

        Returns:
            bool: 是否应该排除
        """
        # 检查路径中的每个部分
        for part in file_path.parts:
            if part in excluded_dirs:
                return True
        return False

    def get_current_version(self) -> Optional[str]:
        """
        获取当前项目版本（从主__init__.py读取）

        Returns:
            Optional[str]: 当前版本字符串
        """
        main_init = os.path.join(self.project_root, '__init__.py')
        if os.path.exists(main_init):
            try:
                with open(main_init, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        self.current_version = match.group(1)
                        return self.current_version
            except Exception as e:
                logger.error(f"读取主版本文件失败: {e}")

        return None

    def set_version(self, new_version: str, update_all: bool = True) -> Dict[str, Any]:
        """
        设置新版本号

        Args:
            new_version: 新版本字符串
            update_all: 是否更新所有版本源

        Returns:
            Dict: 操作结果
        """
        # 验证版本格式
        if not SemanticVersion.is_valid(new_version):
            return {
                'success': False,
                'error': f'无效的版本格式: {new_version}'
            }

        logger.info(f"设置新版本: {new_version}")

        results = {
            'success': True,
            'version': new_version,
            'updated_files': [],
            'failed_files': [],
            'backup_created': False
        }

        # 创建备份
        backup_result = self._create_backup()
        results['backup_created'] = backup_result

        # 更新主版本文件
        main_result = self._update_main_version(new_version)
        if main_result['success']:
            results['updated_files'].append(main_result)
        else:
            results['failed_files'].append(main_result)

        # 更新所有版本源
        if update_all:
            sync_result = self.sync_all_versions(new_version)
            results['updated_files'].extend(sync_result['updated_files'])
            results['failed_files'].extend(sync_result['failed_files'])

        # 更新当前版本
        self.current_version = new_version

        # 记录版本历史
        self._record_version_change(new_version)

        results['success'] = len(results['failed_files']) == 0

        return results

    def _update_main_version(self, new_version: str) -> Dict[str, Any]:
        """更新主版本文件"""
        main_init = os.path.join(self.project_root, '__init__.py')

        try:
            with open(main_init, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换版本号
            new_content = re.sub(
                r'(__version__\s*=\s*["\'])[^"\']+(["\'])',
                f'\\g<1>{new_version}\\g<2>',
                content
            )

            with open(main_init, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                'success': True,
                'file': main_init,
                'old_version': self.current_version,
                'new_version': new_version
            }

        except Exception as e:
            return {
                'success': False,
                'file': main_init,
                'error': str(e)
            }

    def sync_all_versions(self, target_version: str = None) -> Dict[str, Any]:
        """
        同步所有版本源到目标版本

        Args:
            target_version: 目标版本，默认使用当前版本

        Returns:
            Dict: 同步结果
        """
        if not target_version:
            target_version = self.get_current_version()

        if not target_version:
            return {
                'success': False,
                'error': '无法确定目标版本'
            }

        logger.info(f"同步所有版本到: {target_version}")

        results = {
            'success': True,
            'target_version': target_version,
            'updated_files': [],
            'failed_files': [],
            'skipped_files': []
        }

        for source in self.version_sources:
            if source['file'].endswith('__init__.py') and '__init__.py' in source['file']:
                continue  # 跳过主版本文件

            update_result = self._update_version_in_file(
                source['file'],
                source['regex'],
                target_version
            )

            if update_result['success']:
                results['updated_files'].append(update_result)
            elif update_result.get('skipped'):
                results['skipped_files'].append(update_result)
            else:
                results['failed_files'].append(update_result)

        results['success'] = len(results['failed_files']) == 0

        return results

    def _update_version_in_file(self, file_path: str, regex: str, new_version: str) -> Dict[str, Any]:
        """在指定文件中更新版本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找现有版本
            matches = re.findall(regex, content)
            if not matches:
                return {
                    'success': False,
                    'skipped': True,
                    'file': file_path,
                    'error': '未找到版本定义'
                }

            old_version = matches[0]

            # 替换版本号
            new_content = re.sub(regex, lambda m: m.group(0).replace(old_version, new_version), content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                'success': True,
                'file': file_path,
                'old_version': old_version,
                'new_version': new_version
            }

        except Exception as e:
            return {
                'success': False,
                'file': file_path,
                'error': str(e)
            }

    def bump_version(self, bump_type: str) -> Dict[str, Any]:
        """
        自动递增版本号

        Args:
            bump_type: 递增类型 ('major', 'minor', 'patch')

        Returns:
            Dict: 操作结果
        """
        current = self.get_current_version()
        if not current:
            return {
                'success': False,
                'error': '无法获取当前版本'
            }

        try:
            new_version = SemanticVersion.bump_version(current, bump_type)
            return self.set_version(new_version, update_all=True)

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def validate_version_consistency(self) -> Dict[str, Any]:
        """
        验证版本一致性

        Returns:
            Dict: 验证结果
        """
        logger.info("验证版本一致性...")

        # 重新发现版本源
        self.version_sources = self._discover_version_sources()

        current = self.get_current_version()
        if not current:
            return {
                'success': False,
                'error': '无法获取当前版本'
            }

        results = {
            'success': True,
            'current_version': current,
            'total_sources': len(self.version_sources),
            'consistent_sources': 0,
            'inconsistent_sources': 0,
            'invalid_sources': 0,
            'details': []
        }

        for source in self.version_sources:
            detail = {
                'file': source['relative_path'],
                'type': source['type'],
                'version': source['version'],
                'valid': source['valid']
            }

            if not source['valid']:
                detail['status'] = 'invalid'
                results['invalid_sources'] += 1
            elif source['version'] == current:
                detail['status'] = 'consistent'
                results['consistent_sources'] += 1
            else:
                detail['status'] = 'inconsistent'
                results['inconsistent_sources'] += 1

            results['details'].append(detail)

        results['success'] = results['inconsistent_sources'] == 0 and results['invalid_sources'] == 0

        return results

    def get_version_info(self) -> Dict[str, Any]:
        """
        获取详细版本信息

        Returns:
            Dict: 版本详细信息
        """
        current = self.get_current_version()
        if not current:
            return {
                'success': False,
                'error': '无法获取当前版本'
            }

        version_info = SemanticVersion.extract_version_info(current)
        consistency_check = self.validate_version_consistency()

        return {
            'success': True,
            'current_version': current,
            'version_details': version_info,
            'consistency_check': consistency_check,
            'version_sources_count': len(self.version_sources),
            'project_root': self.project_root
        }

    def _create_backup(self) -> bool:
        """创建版本文件备份"""
        try:
            backup_dir = os.path.join(self.project_root, '.version_backups')
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_info = {
                'timestamp': timestamp,
                'current_version': self.get_current_version(),
                'version_sources': self.version_sources
            }

            backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            logger.info(f"创建版本备份: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False

    def _record_version_change(self, new_version: str) -> None:
        """记录版本变更历史"""
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'old_version': self.current_version,
            'new_version': new_version,
            'change_type': self._detect_change_type(self.current_version, new_version)
        }

        self.version_history.append(change_record)

        # 保存到文件
        history_file = os.path.join(self.project_root, '.version_history.json')
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.version_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存版本历史失败: {e}")

    def _detect_change_type(self, old_version: str, new_version: str) -> str:
        """检测版本变更类型"""
        if not old_version:
            return 'initial'

        try:
            old_v = SemanticVersion.parse(old_version)
            new_v = SemanticVersion.parse(new_version)

            if not old_v or not new_v:
                return 'unknown'

            if new_v.major > old_v.major:
                return 'major'
            elif new_v.minor > old_v.minor:
                return 'minor'
            elif new_v.patch > old_v.patch:
                return 'patch'
            else:
                return 'other'

        except Exception:
            return 'unknown'

    def generate_version_report(self) -> str:
        """
        生成版本报告

        Returns:
            str: 版本报告文本
        """
        info = self.get_version_info()

        if not info['success']:
            return f"❌ 无法生成版本报告: {info.get('error')}"

        current = info['current_version']
        details = info['version_details']
        consistency = info['consistency_check']

        report = f"""
📊 Perfect21 版本报告
{'='*50}

🔢 当前版本: {current}
📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 版本详情:
- 主版本号: {details['major']}
- 次版本号: {details['minor']}
- 修订号: {details['patch']}
- 预发布: {details['pre_release'] or '无'}
- 稳定版本: {'是' if details['is_stable'] else '否'}

🔍 一致性检查:
- 总版本源: {consistency['total_sources']}
- 一致版本源: {consistency['consistent_sources']}
- 不一致版本源: {consistency['inconsistent_sources']}
- 无效版本源: {consistency['invalid_sources']}
- 整体状态: {'✅ 一致' if consistency['success'] else '❌ 不一致'}

🚀 可用的下一版本:
- 主版本: {details['next_versions']['major']}
- 次版本: {details['next_versions']['minor']}
- 修订版: {details['next_versions']['patch']}
- Alpha版: {details['next_versions']['alpha']}
- Beta版: {details['next_versions']['beta']}
- RC版: {details['next_versions']['rc']}
"""

        if consistency['inconsistent_sources'] > 0:
            report += "\n⚠️  不一致的版本源:\n"
            for detail in consistency['details']:
                if detail['status'] == 'inconsistent':
                    report += f"  - {detail['file']}: {detail['version']}\n"

        return report

def initialize():
    """初始化version_manager功能"""
    import logging
    logger = logging.getLogger("Perfect21.VersionManager")

    try:
        logger.info("初始化version_manager功能...")
        # 这里可以添加初始化逻辑
        logger.info("version_manager功能初始化成功")
        return True
    except Exception as e:
        logger.error(f"version_manager功能初始化失败: {e}")
        return False

if __name__ == "__main__":
    # 测试脚本
    import sys

    vm = VersionManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'info':
            print(vm.generate_version_report())
        elif command == 'check':
            result = vm.validate_version_consistency()
            print(f"版本一致性: {'✅ 通过' if result['success'] else '❌ 失败'}")
        elif command == 'sync':
            result = vm.sync_all_versions()
            print(f"版本同步: {'✅ 成功' if result['success'] else '❌ 失败'}")
    else:
        print("用法: python version_manager.py [info|check|sync]")