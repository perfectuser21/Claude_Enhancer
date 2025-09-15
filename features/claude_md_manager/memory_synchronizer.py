#!/usr/bin/env python3
"""
Memory Synchronizer - 内存银行同步器
确保CLAUDE.md文档与实际代码状态保持一致性，实现Claude Code的内存管理最佳实践
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Set
from pathlib import Path

class MemorySynchronizer:
    """内存银行同步器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # 内存文件路径
        self.claude_md_path = os.path.join(self.project_root, 'CLAUDE.md')
        self.claude_local_path = os.path.join(self.project_root, 'CLAUDE.local.md')

        # 同步状态文件
        self.sync_state_path = os.path.join(self.project_root, '.claude', 'sync_state.json')
        self._ensure_claude_dir()

    def _ensure_claude_dir(self):
        """确保.claude目录存在"""
        claude_dir = os.path.join(self.project_root, '.claude')
        os.makedirs(claude_dir, exist_ok=True)

    def synchronize_memory_bank(self) -> Dict[str, Any]:
        """同步内存银行"""
        try:
            sync_result = {
                'timestamp': datetime.now().isoformat(),
                'files_checked': [],
                'inconsistencies_found': [],
                'fixes_applied': [],
                'success': True
            }

            # 1. 检查架构模式一致性
            arch_check = self._check_architecture_consistency()
            sync_result['architecture_check'] = arch_check
            if arch_check['inconsistencies']:
                sync_result['inconsistencies_found'].extend(arch_check['inconsistencies'])

            # 2. 验证功能模块描述准确性
            features_check = self._check_features_consistency()
            sync_result['features_check'] = features_check
            if features_check['inconsistencies']:
                sync_result['inconsistencies_found'].extend(features_check['inconsistencies'])

            # 3. 同步版本信息
            version_sync = self._sync_version_info()
            sync_result['version_sync'] = version_sync
            if version_sync.get('updated'):
                sync_result['fixes_applied'].append('version_info_updated')

            # 4. 验证依赖关系
            deps_check = self._check_dependencies_consistency()
            sync_result['dependencies_check'] = deps_check

            # 5. 更新同步状态
            self._update_sync_state(sync_result)

            return sync_result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _check_architecture_consistency(self) -> Dict[str, Any]:
        """检查架构模式一致性"""
        inconsistencies = []

        # 读取CLAUDE.md中的架构描述
        claude_content = self._read_claude_md()

        # 实际目录结构
        actual_structure = self._scan_project_structure()

        # 检查核心目录是否存在
        expected_dirs = ['core', 'features', 'modules', 'main', 'api']
        for dir_name in expected_dirs:
            dir_path = os.path.join(self.project_root, dir_name)
            if not os.path.exists(dir_path):
                inconsistencies.append({
                    'type': 'missing_directory',
                    'expected': dir_name,
                    'description': f'预期目录 {dir_name} 不存在'
                })

        # 检查features目录下的模块
        features_in_docs = self._extract_features_from_docs(claude_content)
        actual_features = self._scan_features_directory()

        # 查找未文档化的功能
        undocumented = actual_features - features_in_docs
        if undocumented:
            inconsistencies.append({
                'type': 'undocumented_features',
                'features': list(undocumented),
                'description': f'发现 {len(undocumented)} 个未在文档中描述的功能模块'
            })

        # 查找已删除但仍在文档中的功能
        outdated = features_in_docs - actual_features
        if outdated:
            inconsistencies.append({
                'type': 'outdated_documentation',
                'features': list(outdated),
                'description': f'文档中存在 {len(outdated)} 个已不存在的功能模块'
            })

        return {
            'inconsistencies': inconsistencies,
            'actual_structure': actual_structure,
            'features_in_docs': list(features_in_docs),
            'actual_features': list(actual_features)
        }

    def _check_features_consistency(self) -> Dict[str, Any]:
        """检查功能模块一致性"""
        inconsistencies = []

        features_dir = os.path.join(self.project_root, 'features')
        if not os.path.exists(features_dir):
            return {'inconsistencies': []}

        for feature_name in os.listdir(features_dir):
            feature_path = os.path.join(features_dir, feature_name)
            if not os.path.isdir(feature_path) or feature_name.startswith('.'):
                continue

            # 检查必要文件
            expected_files = ['__init__.py', 'capability.py']
            for expected_file in expected_files:
                file_path = os.path.join(feature_path, expected_file)
                if not os.path.exists(file_path):
                    inconsistencies.append({
                        'type': 'missing_capability_file',
                        'feature': feature_name,
                        'missing_file': expected_file,
                        'description': f'功能模块 {feature_name} 缺少必要文件 {expected_file}'
                    })

            # 检查capability.py的内容完整性
            capability_path = os.path.join(feature_path, 'capability.py')
            if os.path.exists(capability_path):
                capability_check = self._validate_capability_file(feature_name, capability_path)
                if capability_check['issues']:
                    inconsistencies.extend(capability_check['issues'])

        return {'inconsistencies': inconsistencies}

    def _validate_capability_file(self, feature_name: str, capability_path: str) -> Dict[str, Any]:
        """验证capability.py文件"""
        issues = []

        try:
            with open(capability_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查必要的字段
            required_fields = ['CAPABILITY_INFO', 'name', 'version', 'description']
            for field in required_fields:
                if field not in content:
                    issues.append({
                        'type': 'missing_capability_field',
                        'feature': feature_name,
                        'missing_field': field,
                        'description': f'capability.py缺少必要字段: {field}'
                    })

            # 检查模块名称一致性
            if f'"name": "{feature_name}"' not in content and f"'name': '{feature_name}'" not in content:
                issues.append({
                    'type': 'name_mismatch',
                    'feature': feature_name,
                    'description': f'capability.py中的name字段与目录名不匹配'
                })

        except Exception as e:
            issues.append({
                'type': 'capability_file_error',
                'feature': feature_name,
                'error': str(e),
                'description': f'读取capability.py文件时出错'
            })

        return {'issues': issues}

    def _sync_version_info(self) -> Dict[str, Any]:
        """同步版本信息"""
        try:
            # 获取实际版本
            actual_version = self._get_actual_version()

            # 读取CLAUDE.md中的版本
            claude_content = self._read_claude_md()
            doc_version = self._extract_version_from_docs(claude_content)

            if actual_version != doc_version:
                # 更新文档中的版本信息
                updated_content = self._update_version_in_docs(claude_content, actual_version)
                self._write_claude_md(updated_content)

                return {
                    'updated': True,
                    'old_version': doc_version,
                    'new_version': actual_version,
                    'message': f'版本信息已从 {doc_version} 更新为 {actual_version}'
                }
            else:
                return {
                    'updated': False,
                    'current_version': actual_version,
                    'message': '版本信息已是最新'
                }

        except Exception as e:
            return {
                'updated': False,
                'error': str(e),
                'message': '版本同步失败'
            }

    def _check_dependencies_consistency(self) -> Dict[str, Any]:
        """检查依赖关系一致性"""
        dependencies_info = {
            'python_imports': set(),
            'internal_dependencies': set(),
            'external_dependencies': set(),
            'issues': []
        }

        # 扫描Python文件的导入
        for root, dirs, files in os.walk(self.project_root):
            # 跳过不必要的目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    deps = self._extract_imports_from_file(file_path)
                    dependencies_info['python_imports'].update(deps)

        # 分类依赖
        for dep in dependencies_info['python_imports']:
            if dep.startswith('features.') or dep.startswith('modules.') or dep.startswith('main.'):
                dependencies_info['internal_dependencies'].add(dep)
            elif not dep.startswith('.') and not dep in ['os', 'sys', 'json', 're', 'datetime']:
                dependencies_info['external_dependencies'].add(dep)

        return {
            'internal_count': len(dependencies_info['internal_dependencies']),
            'external_count': len(dependencies_info['external_dependencies']),
            'internal_deps': list(dependencies_info['internal_dependencies']),
            'external_deps': list(dependencies_info['external_dependencies']),
            'issues': dependencies_info['issues']
        }

    def _extract_imports_from_file(self, file_path: str) -> Set[str]:
        """从Python文件中提取导入"""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # 简化的导入解析
                        if line.startswith('import '):
                            module = line[7:].split()[0].split('.')[0]
                            imports.add(module)
                        elif line.startswith('from '):
                            module = line[5:].split(' import')[0].strip()
                            imports.add(module.split('.')[0])
        except:
            pass
        return imports

    # 辅助方法
    def _read_claude_md(self) -> str:
        """读取CLAUDE.md文件"""
        if os.path.exists(self.claude_md_path):
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _write_claude_md(self, content: str):
        """写入CLAUDE.md文件"""
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _scan_project_structure(self) -> Dict[str, Any]:
        """扫描项目结构"""
        structure = {}
        for item in os.listdir(self.project_root):
            item_path = os.path.join(self.project_root, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                structure[item] = 'directory'
            elif os.path.isfile(item_path):
                structure[item] = 'file'
        return structure

    def _scan_features_directory(self) -> Set[str]:
        """扫描features目录"""
        features = set()
        features_dir = os.path.join(self.project_root, 'features')
        if os.path.exists(features_dir):
            for item in os.listdir(features_dir):
                item_path = os.path.join(features_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    features.add(item)
        return features

    def _extract_features_from_docs(self, content: str) -> Set[str]:
        """从文档中提取功能模块列表"""
        features = set()
        # 简化的正则匹配，查找features/目录结构
        import re
        pattern = r'features/([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, content)
        features.update(matches)
        return features

    def _get_actual_version(self) -> str:
        """获取实际版本"""
        try:
            import subprocess
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "v2.2.0"  # 默认版本

    def _extract_version_from_docs(self, content: str) -> str:
        """从文档中提取版本信息"""
        import re
        match = re.search(r'\*版本: Perfect21 ([v\d\.]+)', content)
        if match:
            return match.group(1)
        return "unknown"

    def _update_version_in_docs(self, content: str, new_version: str) -> str:
        """更新文档中的版本信息"""
        import re
        content = re.sub(
            r'\*版本: Perfect21 [v\d\.]+',
            f'*版本: Perfect21 {new_version}',
            content
        )
        return content

    def _update_sync_state(self, sync_result: Dict[str, Any]):
        """更新同步状态"""
        try:
            with open(self.sync_state_path, 'w', encoding='utf-8') as f:
                json.dump(sync_result, f, ensure_ascii=False, indent=2)
        except:
            pass

    def get_sync_report(self) -> Dict[str, Any]:
        """获取同步报告"""
        try:
            if os.path.exists(self.sync_state_path):
                with open(self.sync_state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass

        return {
            'message': '未找到同步历史',
            'needs_sync': True
        }

if __name__ == "__main__":
    # 测试脚本
    synchronizer = MemorySynchronizer()
    result = synchronizer.synchronize_memory_bank()
    print(json.dumps(result, ensure_ascii=False, indent=2))