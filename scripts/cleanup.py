#!/usr/bin/env python3
"""
Perfect21 清理脚本
清理冗余文件，保持项目整洁
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    """清理项目"""

    base_dir = Path(__file__).parent.parent
    archive_dir = base_dir / "archive" / datetime.now().strftime("%Y-%m-%d")
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 清理规则
    cleanup_rules = {
        # 清理pycache
        "**/__pycache__": "delete",
        "**/*.pyc": "delete",

        # 归档旧报告
        "*_report.md": "archive",
        "*_report.json": "archive",
        "*_results.json": "archive",
        "*_results.md": "archive",

        # 归档测试文件
        "test_*.py": "archive",
        "demo_*.py": "archive",

        # 清理临时文件
        "*.tmp": "delete",
        "*.log": "archive",
        ".DS_Store": "delete",
    }

    stats = {"deleted": 0, "archived": 0, "cleaned_dirs": 0}

    # 执行清理
    for pattern, action in cleanup_rules.items():
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                if action == "delete":
                    file_path.unlink()
                    stats["deleted"] += 1
                    print(f"删除: {file_path.relative_to(base_dir)}")
                elif action == "archive":
                    dest = archive_dir / file_path.relative_to(base_dir)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest))
                    stats["archived"] += 1
                    print(f"归档: {file_path.relative_to(base_dir)}")

    # 清理空目录
    for dir_path in sorted(base_dir.rglob("*"), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            if "archive" not in str(dir_path):
                dir_path.rmdir()
                stats["cleaned_dirs"] += 1
                print(f"清理空目录: {dir_path.relative_to(base_dir)}")

    # 统计
    print("\n" + "="*50)
    print(f"清理完成:")
    print(f"  删除文件: {stats['deleted']}")
    print(f"  归档文件: {stats['archived']}")
    print(f"  清理目录: {stats['cleaned_dirs']}")
    print(f"  归档位置: {archive_dir.relative_to(base_dir)}")

    return stats

if __name__ == "__main__":
    cleanup_project()