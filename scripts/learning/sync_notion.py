#!/usr/bin/env python3
"""
Notion同步脚本
将Learning Items和TODOs同步到Notion
用法: python3 sync_notion.py [--dry-run]
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 检查notion-client是否安装
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️  警告: notion-client未安装")
    print("   运行: pip3 install notion-client")
    print("   继续以dry-run模式运行...")

# Notion配置（从环境变量读取Token）
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASES = {
    "notes": "1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d",
    "tasks": "54fe0d4c-f434-4e91-8bb0-e33967661c42",
    "events": "e6c819b1-fd59-41d1-af89-539ac9504c07"
}

# 术语替换字典（生成非技术摘要）
TERM_REPLACEMENTS = {
    # 技术术语 → 人话
    "实现了认证系统": "做了登录功能，用户可以安全登录",
    "优化了数据库查询": "让系统运行更快了",
    "重构了代码": "整理了代码，以后更容易维护",
    "修复了bug": "修复了一个问题",
    "实现了缓存层": "加了一个加速机制",

    # 单个术语
    "API": "接口",
    "JWT": "登录凭证",
    "OAuth": "第三方登录",
    "Token": "凭证",
    "Hash": "加密",
    "数据库": "数据存储",
    "SQL": "数据查询",
    "NoSQL": "数据存储",
    "Schema": "数据结构",
    "前端": "用户界面",
    "后端": "服务器",
    "中间件": "中间处理层",
    "函数": "功能模块",
    "变量": "数据",
    "类": "模块",
    "对象": "实例",
    "bcrypt": "密码加密工具",
    "Redis": "快速缓存",
    "Docker": "容器工具",
    "Kubernetes": "集群管理",
}


def simplify_description(text: str) -> str:
    """将技术描述转换为非技术语言"""
    result = text
    for tech_term, plain_term in TERM_REPLACEMENTS.items():
        result = result.replace(tech_term, plain_term)
    return result


def sync_learning_items(client, ce_home: Path, dry_run: bool = False):
    """同步Learning Items到Notion"""
    learning_dir = ce_home / ".learning" / "items"
    synced_count = 0
    skipped_count = 0

    if not learning_dir.exists():
        print("   ⚠️  .learning/items/ 目录不存在")
        return 0

    print(f"   扫描Learning Items: {learning_dir}")

    for item_file in learning_dir.glob("*.yml"):
        try:
            with open(item_file, 'r') as f:
                item = yaml.safe_load(f)

            # 检查是否已同步
            if item.get('metadata', {}).get('notion_synced', False):
                skipped_count += 1
                continue

            # 简化描述（非技术语言）
            plain_description = simplify_description(
                item.get('observation', {}).get('description', '')
            )

            # 构建Notion页面属性
            properties = {
                "标题": {
                    "title": [{"text": {"content": plain_description[:100]}}]  # Notion限制100字符
                },
                "类别": {
                    "select": {"name": item.get('category', 'unknown')}
                },
                "项目": {
                    "rich_text": [{"text": {"content": item.get('project', 'unknown')}}]
                },
                "优先级": {
                    "select": {"name": item.get('actionable', {}).get('priority', 'medium')}
                },
                "信心分数": {
                    "number": item.get('learning', {}).get('confidence', 0)
                },
                "创建时间": {
                    "date": {"start": item.get('timestamp', datetime.now().isoformat())}
                }
            }

            # 构建页面内容
            technical_details = item.get('observation', {}).get('technical_details', '')
            solution = item.get('learning', {}).get('solution', '')

            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "详细描述"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": plain_description}}]
                    }
                }
            ]

            if solution:
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "解决方案"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": simplify_description(solution)}}]
                        }
                    }
                ])

            if technical_details:
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"text": {"content": "技术细节"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": technical_details[:2000]}}]  # Notion限制
                        }
                    }
                ])

            if dry_run or not NOTION_AVAILABLE:
                print(f"   [DRY-RUN] 将同步: {item.get('id')} - {plain_description[:50]}...")
                synced_count += 1
            else:
                result = client.pages.create(
                    parent={"database_id": NOTION_DATABASES["notes"]},
                    properties=properties,
                    children=children
                )

                # 更新Learning Item标记为已同步
                item['metadata']['notion_synced'] = True
                item['metadata']['notion_page_id'] = result['id']

                with open(item_file, 'w') as f:
                    yaml.dump(item, f, allow_unicode=True, default_flow_style=False)

                print(f"   ✅ 已同步: {item.get('id')} - {plain_description[:50]}...")
                synced_count += 1

        except Exception as e:
            print(f"   ❌ 同步失败 {item_file.name}: {e}")

    print(f"   📊 Learning Items: {synced_count}个新同步, {skipped_count}个已跳过")
    return synced_count


def sync_todos(client, ce_home: Path, dry_run: bool = False):
    """同步TODOs到Notion"""
    todo_dir = ce_home / ".todos" / "pending"
    synced_count = 0

    if not todo_dir.exists():
        print("   ⚠️  .todos/pending/ 目录不存在")
        return 0

    print(f"   扫描TODO队列: {todo_dir}")

    for todo_file in todo_dir.glob("*.json"):
        try:
            with open(todo_file, 'r') as f:
                todo = json.load(f)

            # 简化标题
            plain_title = simplify_description(todo.get('title', ''))

            # 构建Notion页面属性
            properties = {
                "任务": {
                    "title": [{"text": {"content": plain_title[:100]}}]
                },
                "状态": {
                    "select": {"name": "待办"}
                },
                "优先级": {
                    "select": {"name": todo.get('priority', 'medium')}
                },
                "预估工作量": {
                    "rich_text": [{"text": {"content": todo.get('estimated_effort', '未知')}}]
                },
                "创建时间": {
                    "date": {"start": todo.get('created_at', datetime.now().isoformat())}
                }
            }

            # 构建内容
            description = simplify_description(todo.get('description', ''))
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": description[:2000]}}]
                    }
                }
            ]

            if dry_run or not NOTION_AVAILABLE:
                print(f"   [DRY-RUN] 将同步TODO: {todo.get('id')} - {plain_title[:50]}...")
                synced_count += 1
            else:
                result = client.pages.create(
                    parent={"database_id": NOTION_DATABASES["tasks"]},
                    properties=properties,
                    children=children
                )

                print(f"   ✅ 已同步TODO: {todo.get('id')} - {plain_title[:50]}...")
                synced_count += 1

                # TODO: 标记TODO已同步（可选，这里简化处理）

        except Exception as e:
            print(f"   ❌ 同步失败 {todo_file.name}: {e}")

    print(f"   📊 TODOs: {synced_count}个同步")
    return synced_count


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Notion同步脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际同步')
    parser.add_argument('--ce-home', help='CE_HOME路径')

    args = parser.parse_args()

    # 获取CE_HOME
    ce_home_path = args.ce_home if args.ce_home else os.getenv('CE_HOME')
    if not ce_home_path:
        ce_home_path = str(Path.home() / "dev" / "Claude Enhancer")

    ce_home = Path(ce_home_path)

    if not ce_home.exists():
        print(f"❌ 错误: CE_HOME目录不存在: {ce_home}")
        return 1

    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🔄 Notion同步                                            ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"   CE_HOME: {ce_home}")
    print(f"   模式: {'🔍 预览 (dry-run)' if args.dry_run or not NOTION_AVAILABLE else '✅ 实际同步'}")
    print("")

    # 初始化Notion客户端
    client = None
    if NOTION_AVAILABLE and not args.dry_run:
        try:
            client = Client(auth=NOTION_TOKEN)
            print("   ✅ Notion客户端初始化成功")
        except Exception as e:
            print(f"   ❌ Notion客户端初始化失败: {e}")
            print("   切换到dry-run模式...")
            args.dry_run = True

    print("")

    # 同步Learning Items
    print("📚 同步Learning Items...")
    learning_count = sync_learning_items(client, ce_home, args.dry_run)

    print("")

    # 同步TODOs
    print("📋 同步TODOs...")
    todo_count = sync_todos(client, ce_home, args.dry_run)

    print("")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  ✅ 同步完成                                              ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"   Learning Items: {learning_count}个")
    print(f"   TODOs: {todo_count}个")
    print("")

    if args.dry_run or not NOTION_AVAILABLE:
        print("💡 提示: 这是预览模式")
        if not NOTION_AVAILABLE:
            print("   安装notion-client后可实际同步:")
            print("   pip3 install notion-client")
        print("")

    return 0


if __name__ == "__main__":
    exit(main())
