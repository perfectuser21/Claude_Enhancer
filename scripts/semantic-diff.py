#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
Semantic Diff Gate - 语义对比守门系统
Claude Enhancer Self-Healing Component
═══════════════════════════════════════════════════════════════

功能：在AI修改文件前，对比新旧逻辑差异，防止：
1. 重新添加已删除的功能
2. 推翻之前的优化决策
3. 引入已解决的问题

原理：不只是文本diff，而是语义分析
- 检测功能添加/删除
- 检测配置回退
- 检测复杂度增加
- 检测定位偏移
"""

import os
import sys
import json
import re
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_CACHE = PROJECT_ROOT / ".claude" / "memory-cache.json"
CONFIG_FILE = PROJECT_ROOT / ".self-healing.config"

# 颜色输出
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'

# ═══════════════════════════════════════════════════════════════
# 语义分析器
# ═══════════════════════════════════════════════════════════════

class SemanticAnalyzer:
    """语义分析器 - 理解代码/配置的意图变化"""

    def __init__(self):
        self.memory = self.load_memory()
        self.forbidden_patterns = self.load_forbidden_patterns()

    def load_memory(self) -> Dict:
        """加载记忆缓存"""
        if not MEMORY_CACHE.exists():
            return {}

        with open(MEMORY_CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_forbidden_patterns(self) -> Dict:
        """加载禁止模式（从记忆中提取）"""
        patterns = {
            'do_not_add_back': [],
            'do_not_recreate': [],
            'forbidden_terms': [],
            'enterprise_features': []
        }

        if 'recent_decisions' in self.memory:
            for decision_key, decision in self.memory['recent_decisions'].items():
                if 'do_not_add_back' in decision:
                    patterns['do_not_add_back'].extend(decision['do_not_add_back'])
                if 'do_not_recreate' in decision and decision.get('do_not_recreate'):
                    if 'deleted_files' in decision:
                        patterns['do_not_recreate'].extend(decision['deleted_files'])
                if 'forbidden_terms' in decision:
                    patterns['forbidden_terms'].extend(decision['forbidden_terms'])

        if 'system_constraints' in self.memory:
            constraints = self.memory['system_constraints']
            if 'forbidden_additions' in constraints:
                fa = constraints['forbidden_additions']
                if 'enterprise_features' in fa:
                    patterns['enterprise_features'].extend(fa['enterprise_features'])

        return patterns

    def analyze_diff(self, old_content: str, new_content: str,
                    file_path: str) -> Tuple[bool, List[str]]:
        """
        分析文件差异的语义含义

        Returns:
            (is_safe, warnings) - 是否安全，警告列表
        """
        warnings = []

        # 1. 检测功能重新添加
        warnings.extend(self._check_readded_features(old_content, new_content))

        # 2. 检测文件重新创建
        warnings.extend(self._check_recreated_files(file_path, old_content, new_content))

        # 3. 检测定位偏移
        warnings.extend(self._check_positioning_drift(old_content, new_content))

        # 4. 检测复杂度增加
        warnings.extend(self._check_complexity_increase(old_content, new_content, file_path))

        # 5. 检测企业功能添加
        warnings.extend(self._check_enterprise_features(new_content, file_path))

        is_safe = len(warnings) == 0
        return is_safe, warnings

    def _check_readded_features(self, old: str, new: str) -> List[str]:
        """检测已删除功能的重新添加"""
        warnings = []

        for pattern in self.forbidden_patterns['do_not_add_back']:
            # 检查：旧版本没有，新版本有
            pattern_regex = re.compile(re.escape(pattern), re.IGNORECASE)

            old_has = bool(pattern_regex.search(old))
            new_has = bool(pattern_regex.search(new))

            if not old_has and new_has:
                warnings.append(
                    f"🚫 检测到重新添加已删除功能: '{pattern}'\n"
                    f"   历史决策: 此功能已在之前决策中删除\n"
                    f"   建议: 检查memory-cache.json了解删除原因"
                )

        return warnings

    def _check_recreated_files(self, file_path: str, old: str, new: str) -> List[str]:
        """检测已删除文件的重新创建"""
        warnings = []

        file_name = os.path.basename(file_path)

        for pattern in self.forbidden_patterns['do_not_recreate']:
            if pattern in file_name or file_name in pattern:
                warnings.append(
                    f"🚫 检测到重新创建已删除文件: '{file_name}'\n"
                    f"   历史决策: 此文件已在之前决策中删除\n"
                    f"   原因: {self._get_deletion_reason(pattern)}\n"
                    f"   建议: 确认是否真的需要重新创建"
                )

        return warnings

    def _check_positioning_drift(self, old: str, new: str) -> List[str]:
        """检测定位偏移（如重新变成企业级）"""
        warnings = []

        for term in self.forbidden_patterns['forbidden_terms']:
            term_regex = re.compile(re.escape(term), re.IGNORECASE)

            old_has = bool(term_regex.search(old))
            new_has = bool(term_regex.search(new))

            if not old_has and new_has:
                warnings.append(
                    f"🚫 检测到定位偏移: 添加了'{term}'\n"
                    f"   系统定位: 个人AI编程助手（非企业级）\n"
                    f"   建议: 使用'个人工具'、'编程小白友好'等表述"
                )

        return warnings

    def _check_complexity_increase(self, old: str, new: str, file_path: str) -> List[str]:
        """检测复杂度增加"""
        warnings = []

        # 检查是否添加了大量新内容
        old_lines = old.split('\n')
        new_lines = new.split('\n')

        if len(new_lines) > len(old_lines) * 1.3:  # 增加超过30%
            increase = len(new_lines) - len(old_lines)
            warnings.append(
                f"⚠️  检测到文件大幅增长: +{increase}行 (+{increase/len(old_lines)*100:.0f}%)\n"
                f"   当前目标: 简化系统，保持编程小白友好\n"
                f"   建议: 考虑是否有更简洁的实现方式"
            )

        # 检查CLAUDE.md特殊逻辑
        if 'CLAUDE.md' in file_path:
            constraints = self.memory.get('system_constraints', {})
            max_lines = constraints.get('complexity_limits', {}).get('max_claude_md_lines', 400)

            if len(new_lines) > max_lines:
                warnings.append(
                    f"⚠️  CLAUDE.md超过目标行数: {len(new_lines)}行 (目标<{max_lines}行)\n"
                    f"   编程小白友好原则: 文档应简洁易读\n"
                    f"   建议: 将高级内容移到docs/advanced/"
                )

        return warnings

    def _check_enterprise_features(self, new: str, file_path: str) -> List[str]:
        """检测企业功能添加"""
        warnings = []

        for feature in self.forbidden_patterns['enterprise_features']:
            if feature in new:
                warnings.append(
                    f"🚫 检测到企业级功能: '{feature}'\n"
                    f"   用户定位: 编程小白 + 个人项目\n"
                    f"   建议: 确认Max 20X用户是否真的需要此功能"
                )

        # 检查文件路径
        enterprise_paths = ['sre/', 'canary', 'observability/slo']
        for path in enterprise_paths:
            if path in file_path:
                warnings.append(
                    f"🚫 检测到企业级路径: '{path}' in {file_path}\n"
                    f"   用户定位: 个人项目，不需要SRE/金丝雀等功能\n"
                    f"   建议: 考虑使用更简单的替代方案"
                )

        return warnings

    def _get_deletion_reason(self, file_pattern: str) -> str:
        """获取文件删除原因"""
        for decision_key, decision in self.memory.get('recent_decisions', {}).items():
            if 'deleted_files' in decision:
                for deleted in decision['deleted_files']:
                    if file_pattern in deleted:
                        return decision.get('rationale', '原因未记录')
        return "原因未记录"

# ═══════════════════════════════════════════════════════════════
# Diff比对器
# ═══════════════════════════════════════════════════════════════

class DiffComparator:
    """Diff比对器 - 生成友好的差异报告"""

    def __init__(self):
        self.analyzer = SemanticAnalyzer()

    def compare_files(self, file_path: str, old_content: str,
                     new_content: str, show_diff: bool = True) -> Dict:
        """
        比对文件并生成报告

        Args:
            file_path: 文件路径
            old_content: 旧内容
            new_content: 新内容
            show_diff: 是否显示详细diff

        Returns:
            {
                'is_safe': bool,
                'warnings': List[str],
                'diff': str,
                'summary': Dict
            }
        """
        # 语义分析
        is_safe, warnings = self.analyzer.analyze_diff(old_content, new_content, file_path)

        # 统计差异
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')

        # 生成unified diff
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f'a/{file_path}',
            tofile=f'b/{file_path}',
            lineterm=''
        ))

        # 统计添加/删除
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        summary = {
            'additions': additions,
            'deletions': deletions,
            'net_change': additions - deletions,
            'old_lines': len(old_lines),
            'new_lines': len(new_lines)
        }

        return {
            'is_safe': is_safe,
            'warnings': warnings,
            'diff': '\n'.join(diff) if show_diff else '',
            'summary': summary
        }

    def print_report(self, file_path: str, result: Dict):
        """打印友好的报告"""
        print(f"\n{Colors.CYAN}═══════════════════════════════════════════{Colors.NC}")
        print(f"{Colors.BOLD}Semantic Diff Gate Report{Colors.NC}")
        print(f"{Colors.CYAN}═══════════════════════════════════════════{Colors.NC}\n")

        print(f"{Colors.BOLD}File:{Colors.NC} {file_path}")

        summary = result['summary']
        print(f"\n{Colors.BLUE}Changes:{Colors.NC}")
        print(f"  +{summary['additions']} lines added")
        print(f"  -{summary['deletions']} lines deleted")
        print(f"  Net: {summary['net_change']:+d} lines")
        print(f"  Size: {summary['old_lines']} → {summary['new_lines']} lines")

        if result['warnings']:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  WARNINGS:{Colors.NC}")
            for warning in result['warnings']:
                print(f"\n{Colors.YELLOW}{warning}{Colors.NC}")

        if result['is_safe']:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SAFE TO PROCEED{Colors.NC}")
            print(f"{Colors.GREEN}No semantic conflicts detected{Colors.NC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ REVIEW REQUIRED{Colors.NC}")
            print(f"{Colors.RED}Potential regression or self-contradiction detected{Colors.NC}")
            print(f"\n{Colors.YELLOW}Actions:{Colors.NC}")
            print(f"  1. Review memory-cache.json for context")
            print(f"  2. Confirm this change aligns with previous decisions")
            print(f"  3. Update memory-cache.json if this is a new decision")

# ═══════════════════════════════════════════════════════════════
# CLI接口
# ═══════════════════════════════════════════════════════════════

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Semantic Diff Gate - 防止AI自我推翻的语义对比工具"
    )
    parser.add_argument('file', help='要检查的文件路径')
    parser.add_argument('--old', help='旧文件路径（默认为当前HEAD版本）')
    parser.add_argument('--new', help='新文件路径（默认为working tree）')
    parser.add_argument('--show-diff', action='store_true', help='显示详细diff')
    parser.add_argument('--strict', action='store_true', help='严格模式（任何警告都失败）')

    args = parser.parse_args()

    # 读取文件内容
    file_path = args.file

    if args.old:
        with open(args.old, 'r') as f:
            old_content = f.read()
    else:
        # 从git读取HEAD版本
        import subprocess
        try:
            old_content = subprocess.check_output(
                ['git', 'show', f'HEAD:{file_path}'],
                stderr=subprocess.DEVNULL
            ).decode('utf-8')
        except:
            old_content = ""  # 新文件

    if args.new:
        with open(args.new, 'r') as f:
            new_content = f.read()
    else:
        # 读取working tree
        with open(file_path, 'r') as f:
            new_content = f.read()

    # 执行比对
    comparator = DiffComparator()
    result = comparator.compare_files(file_path, old_content, new_content, args.show_diff)

    # 打印报告
    comparator.print_report(file_path, result)

    # 返回退出码
    if args.strict:
        sys.exit(0 if result['is_safe'] else 1)
    else:
        sys.exit(0)  # 非严格模式总是成功

if __name__ == '__main__':
    main()
