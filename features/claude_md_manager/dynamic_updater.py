#!/usr/bin/env python3
"""
Dynamic Updater - CLAUDE.md动态更新器
自动更新CLAUDE.md文件中的动态内容，保持项目文档与代码状态同步
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目路径以便导入其他模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class DynamicUpdater:
    """CLAUDE.md动态更新器"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            # 从当前文件位置推断项目根目录
            current_file = os.path.abspath(__file__)
            # features/claude_md_manager/dynamic_updater.py -> 向上2级
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        self.project_root = project_root
        self.claude_md_path = os.path.join(self.project_root, 'CLAUDE.md')
        self.claude_local_path = os.path.join(self.project_root, 'CLAUDE.local.md')

        # 动态内容标记
        self.dynamic_markers = {
            'version_info': '## 🎯 项目概述',
            'system_status': '## 🏗️ 系统架构',
            'capabilities': '### 完整的企业级架构',
            'last_update': '*最后更新:'
        }

    def sync_claude_md(self) -> Dict[str, Any]:
        """同步CLAUDE.md文件"""
        try:
            # 收集动态数据
            dynamic_data = self._collect_dynamic_data()

            # 读取当前CLAUDE.md
            current_content = self._read_claude_md()

            # 更新动态内容
            updated_content = self._update_dynamic_content(current_content, dynamic_data)

            # 写回文件
            self._write_claude_md(updated_content)

            return {
                'success': True,
                'message': 'CLAUDE.md同步成功',
                'updates': list(dynamic_data.keys()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'CLAUDE.md同步失败'
            }

    def _collect_dynamic_data(self) -> Dict[str, Any]:
        """收集动态数据"""
        data = {}

        # 1. 版本信息
        try:
            data['version'] = self._get_version_info()
        except:
            data['version'] = "未知版本"

        # 2. 系统状态
        try:
            data['system_status'] = self._get_system_status()
        except:
            data['system_status'] = "状态检查失败"

        # 3. 功能模块
        try:
            data['capabilities'] = self._get_capabilities_info()
        except:
            data['capabilities'] = []

        # 4. Git状态
        try:
            data['git_status'] = self._get_git_status()
        except:
            data['git_status'] = {}

        # 5. 统计信息
        try:
            data['statistics'] = self._get_project_statistics()
        except:
            data['statistics'] = {}

        # 6. 更新时间
        data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['iso_date'] = datetime.now().strftime('%Y-%m-%d')

        return data

    def _get_version_info(self) -> str:
        """获取版本信息"""
        try:
            # 尝试从version_manager获取
            from features.version_manager.version_manager import VersionManager
            vm = VersionManager()
            return vm.get_current_version()
        except:
            # 回退到Git标签
            import subprocess
            try:
                result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        return "v2.2.0"  # 默认版本

    def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'perfect21_available': True,
            'agents_count': 56,
            'core_modules': 3
        }

        # 检查核心模块
        features_dir = os.path.join(self.project_root, 'features')
        if os.path.exists(features_dir):
            modules = [d for d in os.listdir(features_dir)
                      if os.path.isdir(os.path.join(features_dir, d)) and not d.startswith('.')]
            status['core_modules'] = len(modules)
            status['modules'] = modules

        return status

    def _get_capabilities_info(self) -> List[Dict[str, Any]]:
        """获取功能模块信息"""
        capabilities = []
        features_dir = os.path.join(self.project_root, 'features')

        if os.path.exists(features_dir):
            for module_name in os.listdir(features_dir):
                module_path = os.path.join(features_dir, module_name)
                if os.path.isdir(module_path) and not module_name.startswith('.'):
                    cap_info = self._analyze_module_capability(module_name, module_path)
                    if cap_info:
                        capabilities.append(cap_info)

        return capabilities

    def _analyze_module_capability(self, module_name: str, module_path: str) -> Optional[Dict[str, Any]]:
        """分析模块功能"""
        capability_file = os.path.join(module_path, 'capability.py')

        if os.path.exists(capability_file):
            try:
                # 尝试读取capability.py
                with open(capability_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单解析（生产环境建议使用AST）
                    if 'CAPABILITY_INFO' in content:
                        return {
                            'name': module_name,
                            'status': 'configured',
                            'has_capability': True
                        }
            except:
                pass

        # 默认分析
        return {
            'name': module_name,
            'status': 'basic',
            'has_capability': False
        }

    def _get_git_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        import subprocess
        git_info = {}

        try:
            # 当前分支
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                git_info['current_branch'] = result.stdout.strip()
        except:
            git_info['current_branch'] = 'unknown'

        try:
            # 提交数量
            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                git_info['total_commits'] = int(result.stdout.strip())
        except:
            git_info['total_commits'] = 0

        return git_info

    def _get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        stats = {
            'total_files': 0,
            'python_files': 0,
            'features_count': 0,
            'lines_of_code': 0
        }

        try:
            for root, dirs, files in os.walk(self.project_root):
                # 跳过隐藏目录和特定目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]

                for file in files:
                    if not file.startswith('.'):
                        stats['total_files'] += 1

                        if file.endswith('.py'):
                            stats['python_files'] += 1

                            # 计算代码行数（简化版）
                            try:
                                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                    lines = len([line for line in f if line.strip() and not line.strip().startswith('#')])
                                    stats['lines_of_code'] += lines
                            except:
                                pass

            # 功能模块数量
            features_dir = os.path.join(self.project_root, 'features')
            if os.path.exists(features_dir):
                stats['features_count'] = len([d for d in os.listdir(features_dir)
                                             if os.path.isdir(os.path.join(features_dir, d)) and not d.startswith('.')])
        except:
            pass

        return stats

    def _read_claude_md(self) -> str:
        """读取CLAUDE.md文件"""
        if os.path.exists(self.claude_md_path):
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """获取默认模板"""
        return """# Claude Code 项目指导文档

**项目名称**: Perfect21
**项目类型**: 企业级多Agent协作开发平台
**技术栈**: Python, claude-code-unified-agents, Git Hooks, 语义化版本管理
**目标用户**: 追求极致质量的开发者和团队

## 🎯 项目概述

Perfect21 是一个企业级多Agent协作开发平台，基于claude-code-unified-agents核心，集成了智能Git工作流、统一版本管理、动态功能发现等企业级开发特性。

---

*最后更新: {timestamp}*
*版本: Perfect21 {version}*
*系统状态: 运行正常*
"""

    def _update_dynamic_content(self, content: str, dynamic_data: Dict[str, Any]) -> str:
        """更新动态内容"""
        # 更新最后更新时间
        version = dynamic_data.get('version', 'v2.2.0')
        timestamp = dynamic_data.get('iso_date', '2025-09-16')

        # 使用正则表达式更新最后更新信息
        content = re.sub(
            r'\*最后更新:.*?\*',
            f'*最后更新: {timestamp}*',
            content
        )

        content = re.sub(
            r'\*版本: Perfect21.*?\*',
            f'*版本: Perfect21 {version}*',
            content
        )

        # 更新核心模块信息（如果存在统计模式）
        stats = dynamic_data.get('statistics', {})
        if stats:
            features_count = stats.get('features_count', 0)
            content = re.sub(
                r'\*核心模块: \d+ 个',
                f'*核心模块: {features_count}个',
                content
            )

        return content

    def _write_claude_md(self, content: str):
        """写入CLAUDE.md文件"""
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        try:
            if not os.path.exists(self.claude_md_path):
                return {
                    'exists': False,
                    'last_modified': None,
                    'size': 0,
                    'needs_sync': True
                }

            import os
            stat = os.stat(self.claude_md_path)

            return {
                'exists': True,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size': stat.st_size,
                'needs_sync': self._check_needs_sync(),
                'path': self.claude_md_path
            }

        except Exception as e:
            return {
                'error': str(e),
                'needs_sync': True
            }

    def _check_needs_sync(self) -> bool:
        """检查是否需要同步"""
        # 简化逻辑：检查最后修改时间
        try:
            if not os.path.exists(self.claude_md_path):
                return True

            # 检查文件是否过期（比如超过1小时）
            import time
            stat = os.stat(self.claude_md_path)
            age_hours = (time.time() - stat.st_mtime) / 3600

            return age_hours > 1  # 1小时后需要同步

        except:
            return True

if __name__ == "__main__":
    # 测试脚本
    updater = DynamicUpdater()
    result = updater.sync_claude_md()
    print(json.dumps(result, ensure_ascii=False, indent=2))