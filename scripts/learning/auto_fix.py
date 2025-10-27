#!/usr/bin/env python3
"""
Auto-fix决策引擎
根据错误类型和历史Learning Items决策是否自动修复
用法: python3 auto_fix.py --error "错误信息" --confidence 0.95
"""

import json
import yaml
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional

# Auto-fix白名单配置
AUTO_FIX_WHITELIST = {
    "tier1_auto": {
        "confidence_min": 0.95,
        "risk_level": "low",
        "patterns": [
            {
                "error_type": "ImportError",
                "pattern": r"No module named ['\"](\w+)['\"]",
                "fix_template": "pip3 install {module}",
                "description": "缺失Python依赖"
            },
            {
                "error_type": "ImportError",
                "pattern": r"cannot import name",
                "fix_template": "检查导入路径",
                "description": "导入错误"
            },
            {
                "error_type": "FormatError",
                "pattern": r"formatting|format",
                "fix_template": "black {file} || prettier --write {file}",
                "description": "代码格式化错误"
            },
            {
                "error_type": "PortConflict",
                "pattern": r"Address already in use.*:(\d+)",
                "fix_template": "kill -9 $(lsof -t -i:{port}) && retry",
                "description": "端口冲突"
            },
            {
                "error_type": "SyntaxError",
                "pattern": r"syntax error",
                "fix_template": "检查语法",
                "description": "语法错误"
            }
        ]
    },
    "tier2_try_then_ask": {
        "confidence_min": 0.70,
        "confidence_max": 0.94,
        "risk_level": "medium",
        "patterns": [
            {
                "error_type": "BuildFailure",
                "pattern": r"build failed|make.*error",
                "fix_attempts": ["make clean && make", "npm install && npm run build"],
                "description": "构建失败"
            },
            {
                "error_type": "TestFailure",
                "pattern": r"test.*failed|FAILED",
                "fix_attempts": ["pytest --lf", "npm test -- --updateSnapshot"],
                "description": "测试失败"
            },
            {
                "error_type": "DependencyError",
                "pattern": r"dependency|requirements",
                "fix_attempts": ["pip3 install -r requirements.txt", "npm install"],
                "description": "依赖问题"
            }
        ]
    },
    "tier3_must_confirm": {
        "confidence_max": 0.69,
        "risk_level": "high",
        "patterns": [
            {
                "error_type": "DataMigration",
                "pattern": r"migration|schema change",
                "description": "数据迁移"
            },
            {
                "error_type": "SecurityPatch",
                "pattern": r"security|vulnerability|CVE-",
                "description": "安全补丁"
            },
            {
                "error_type": "BreakingChange",
                "pattern": r"breaking change|incompatible",
                "description": "破坏性变更"
            },
            {
                "error_type": "ProductionDeploy",
                "pattern": r"production|prod|deploy",
                "description": "生产部署"
            }
        ]
    }
}


def detect_tier(error_message: str, confidence: float) -> tuple:
    """
    检测错误属于哪个tier
    返回: (tier, matched_pattern)
    """
    # 检查tier1
    for pattern in AUTO_FIX_WHITELIST["tier1_auto"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            if confidence >= AUTO_FIX_WHITELIST["tier1_auto"]["confidence_min"]:
                return ("tier1_auto", pattern)

    # 检查tier2
    for pattern in AUTO_FIX_WHITELIST["tier2_try_then_ask"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            if (confidence >= AUTO_FIX_WHITELIST["tier2_try_then_ask"]["confidence_min"] and
                confidence <= AUTO_FIX_WHITELIST["tier2_try_then_ask"]["confidence_max"]):
                return ("tier2_try_then_ask", pattern)

    # 检查tier3
    for pattern in AUTO_FIX_WHITELIST["tier3_must_confirm"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            return ("tier3_must_confirm", pattern)

    # 默认最保守
    return ("tier3_must_confirm", {"description": "未知错误类型"})


def search_similar_learning_items(error_message: str, ce_home: Path) -> List[Dict]:
    """搜索历史相似的Learning Items"""
    similar_items = []
    learning_dir = ce_home / ".learning" / "by_category" / "error_pattern"

    if not learning_dir.exists():
        return similar_items

    for item_file in learning_dir.glob("*.yml"):
        try:
            # 解析符号链接
            real_path = item_file.resolve()
            with open(real_path, 'r') as f:
                item = yaml.safe_load(f)

            # 简单相似度匹配
            if error_message.lower() in item.get('observation', {}).get('description', '').lower():
                similar_items.append({
                    'id': item.get('id'),
                    'description': item.get('observation', {}).get('description'),
                    'solution': item.get('learning', {}).get('solution'),
                    'confidence': item.get('learning', {}).get('confidence', 0)
                })
        except Exception as e:
            print(f"警告: 无法读取{item_file}: {e}", file=sys.stderr)

    return similar_items


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Auto-fix决策引擎')
    parser.add_argument('--error', required=True, help='错误信息')
    parser.add_argument('--confidence', type=float, default=0.5, help='信心分数 (0-1)')
    parser.add_argument('--ce-home', help='CE_HOME路径')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')

    args = parser.parse_args()

    # 检测tier
    tier, pattern = detect_tier(args.error, args.confidence)

    # 搜索历史
    ce_home_path = args.ce_home if args.ce_home else str(Path.home() / "dev" / "Claude Enhancer")
    ce_home = Path(ce_home_path)

    similar = []
    if ce_home.exists():
        similar = search_similar_learning_items(args.error, ce_home)

    # 生成建议
    action_map = {
        "tier1_auto": "自动修复（无需询问）",
        "tier2_try_then_ask": "尝试修复，失败后询问",
        "tier3_must_confirm": "必须询问用户确认"
    }

    result = {
        "tier": tier,
        "confidence": args.confidence,
        "error_type": pattern.get("error_type", "Unknown"),
        "description": pattern.get("description", ""),
        "recommended_action": action_map[tier],
        "similar_count": len(similar),
        "similar_items": similar[:3] if similar else [],  # 最多返回3个
        "can_auto_fix": tier == "tier1_auto"
    }

    # 添加修复建议
    if "fix_template" in pattern:
        result["fix_template"] = pattern["fix_template"]
    elif "fix_attempts" in pattern:
        result["fix_attempts"] = pattern["fix_attempts"]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"🔍 Auto-fix决策结果")
        print(f"   Tier: {tier}")
        print(f"   错误类型: {result['error_type']}")
        print(f"   描述: {result['description']}")
        print(f"   信心分数: {args.confidence}")
        print(f"   建议行动: {result['recommended_action']}")
        print(f"   历史相似: {len(similar)}个")

        if similar:
            print(f"\n   相似Learning Items:")
            for item in similar[:3]:
                print(f"     - {item['id']}: {item['description'][:50]}...")

        if "fix_template" in result:
            print(f"\n   修复模板: {result['fix_template']}")
        elif "fix_attempts" in result:
            print(f"\n   修复尝试:")
            for i, attempt in enumerate(result['fix_attempts'], 1):
                print(f"     {i}. {attempt}")

    # 返回退出码（0=可自动修复，1=需要确认）
    sys.exit(0 if result["can_auto_fix"] else 1)


if __name__ == "__main__":
    main()
