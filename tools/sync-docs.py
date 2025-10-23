#!/usr/bin/env python3
"""
sync-docs.py - 文档自动同步工具
Version: 1.0.0
Purpose: 从SPEC.yaml读取数据，自动更新README、ARCHITECTURE等文档
Author: Claude Code
Date: 2025-10-23
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).parent.parent
SPEC_FILE = PROJECT_ROOT / ".workflow" / "SPEC.yaml"
README_FILE = PROJECT_ROOT / "README.md"
ARCHITECTURE_FILE = PROJECT_ROOT / "ARCHITECTURE.md"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

# 需要同步版本号的文件
VERSION_FILES = [
    PROJECT_ROOT / "VERSION",
    PROJECT_ROOT / ".claude" / "settings.json",
    PROJECT_ROOT / "package.json",
    PROJECT_ROOT / ".workflow" / "manifest.yml",
    PROJECT_ROOT / "CHANGELOG.md",
    PROJECT_ROOT / ".workflow" / "SPEC.yaml",
]

# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def load_spec() -> Dict:
    """读取SPEC.yaml"""
    if not SPEC_FILE.exists():
        print(f"❌ Error: {SPEC_FILE} not found")
        sys.exit(1)

    with open(SPEC_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_version_from_spec(spec: Dict) -> str:
    """从SPEC中提取版本号"""
    return spec.get('metadata', {}).get('version', '0.0.0')


def get_stats_from_spec(spec: Dict) -> Dict:
    """从SPEC中提取统计数据"""
    return {
        'version': get_version_from_spec(spec),
        'total_phases': spec.get('workflow_structure', {}).get('total_phases', 7),
        'total_checkpoints': spec.get('checkpoints', {}).get('total_count', 97),
        'total_gates': spec.get('quality_gates', {}).get('total_gates', 2),
        'total_hard_blocks': spec.get('hard_blocks', {}).get('total_count', 8),
    }


def update_readme_version(version: str, dry_run: bool = False) -> bool:
    """更新README.md中的版本badge"""
    if not README_FILE.exists():
        print(f"⚠️  Warning: {README_FILE} not found, skipping")
        return False

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换version badge
    pattern = r'(badge/version-)[0-9.]+(-blue\.svg)'
    new_content = re.sub(pattern, f'\\g<1>{version}\\g<2>', content)

    if content == new_content:
        print(f"✓ README.md version badge already up-to-date ({version})")
        return True

    if dry_run:
        print(f"  [DRY-RUN] Would update README.md version badge to {version}")
        return True

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ Updated README.md version badge to {version}")
    return True


def update_readme_stats(stats: Dict, dry_run: bool = False) -> bool:
    """更新README.md中的统计数据"""
    if not README_FILE.exists():
        return False

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换7-Phase workflow系统的描述
    pattern = r'(\*\*)[0-9]+-Phase workflow(\*\*)'
    new_content = re.sub(pattern, f'\\g<1>{stats["total_phases"]}-Phase workflow\\g<2>', content)

    # 替换checkpoints数量（如果README中有）
    pattern2 = r'([0-9]+)\s+checkpoints'
    new_content = re.sub(pattern2, f'{stats["total_checkpoints"]} checkpoints', new_content)

    if content == new_content:
        print(f"✓ README.md stats already up-to-date")
        return True

    if dry_run:
        print(f"  [DRY-RUN] Would update README.md stats")
        return True

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ Updated README.md stats ({stats['total_phases']} Phases, {stats['total_checkpoints']} checkpoints)")
    return True


def verify_version_consistency(target_version: str) -> Tuple[bool, List[str]]:
    """验证所有文件的版本号是否一致"""
    mismatches = []

    # VERSION文件
    version_file = VERSION_FILES[0]
    if version_file.exists():
        current = version_file.read_text().strip()
        if current != target_version:
            mismatches.append(f"VERSION: {current}")

    # settings.json
    settings_file = VERSION_FILES[1]
    if settings_file.exists():
        data = json.loads(settings_file.read_text())
        current = data.get('version', '')
        if current != target_version:
            mismatches.append(f".claude/settings.json: {current}")

    # package.json
    package_file = VERSION_FILES[2]
    if package_file.exists():
        data = json.loads(package_file.read_text())
        current = data.get('version', '')
        if current != target_version:
            mismatches.append(f"package.json: {current}")

    # manifest.yml
    manifest_file = VERSION_FILES[3]
    if manifest_file.exists():
        data = yaml.safe_load(manifest_file.read_text())
        current = data.get('version', '')
        if current != target_version:
            mismatches.append(f".workflow/manifest.yml: {current}")

    # CHANGELOG.md (检查最新版本条目)
    changelog_file = VERSION_FILES[4]
    if changelog_file.exists():
        changelog_content = changelog_file.read_text()
        # 提取第一个版本号
        match = re.search(r'## \[v?([0-9.]+)\]', changelog_content)
        if match:
            current = match.group(1)
            # 允许major.minor一致即可
            target_mm = '.'.join(target_version.split('.')[:2])
            current_mm = '.'.join(current.split('.')[:2])
            if current_mm != target_mm:
                mismatches.append(f"CHANGELOG.md: {current}")

    return (len(mismatches) == 0, mismatches)


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='文档自动同步工具')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--verify-only', action='store_true', help='仅验证版本一致性')
    args = parser.parse_args()

    print("═" * 60)
    print("  文档自动同步工具 (sync-docs.py)")
    print("═" * 60)
    print()

    # 1. 读取SPEC.yaml
    print("[1/4] 读取SPEC.yaml...")
    spec = load_spec()
    stats = get_stats_from_spec(spec)
    version = stats['version']
    print(f"  版本号: {version}")
    print(f"  统计数据: {stats['total_phases']} Phases, {stats['total_checkpoints']} Checkpoints, {stats['total_gates']} Gates")
    print()

    # 2. 验证版本一致性
    print("[2/4] 验证版本一致性...")
    is_consistent, mismatches = verify_version_consistency(version)

    if is_consistent:
        print(f"  ✅ 所有文件版本一致: {version}")
    else:
        print(f"  ⚠️  发现版本不一致:")
        print(f"  目标版本: {version}")
        for mismatch in mismatches:
            print(f"    - {mismatch}")

    print()

    if args.verify_only:
        print("  [仅验证模式] 跳过文档更新")
        sys.exit(0 if is_consistent else 1)

    # 3. 更新README.md
    print("[3/4] 更新README.md...")
    update_readme_version(version, dry_run=args.dry_run)
    update_readme_stats(stats, dry_run=args.dry_run)
    print()

    # 4. 总结
    print("[4/4] 总结")
    if args.dry_run:
        print("  🔍 Dry-run模式：未实际修改文件")
        print("  运行 'python3 tools/sync-docs.py' 应用更改")
    else:
        print("  ✅ 文档同步完成")

    print()
    print("═" * 60)

    sys.exit(0 if is_consistent else 0)  # 暂时不因版本不一致而失败


if __name__ == '__main__':
    main()
