# Claude Enhancer v8.0 Implementation Plan
# Dual Evolution Learning System - Complete Architecture & Implementation
# 日期: 2025-10-27
# Phase: 1.5 Architecture Planning

---

## 📋 Executive Summary

**版本**: v7.3.0 → v8.0.0
**项目名**: Dual Evolution Learning System
**核心价值**: 在现有7-Phase工作流基础上，增加学习系统、Auto-fix、TODO队列、Notion同步功能
**Impact Radius**: 71 (High Risk) → **6 Agents**
**预计时间**: 4天（32工作小时）

**核心改进**：
1. **Learning System** (5类学习): 自动捕获错误模式、性能优化、架构决策、代码质量、成功模式
2. **Auto-fix Mechanism** (3级策略): tier1自动、tier2尝试、tier3确认
3. **TODO Queue System**: Learning Items → TODO自动转换
4. **Notion Integration**: 批量同步 + 非技术摘要生成
5. **ce CLI**: 统一命令行工具

**质量保证**：
- ✅ 保持现有7-Phase工作流（97检查点）
- ✅ 不违反规则1（文档管理）和规则2（核心结构锁定）
- ✅ 通过2个质量门禁（Phase 3和Phase 4）
- ✅ 87个验收检查点（Acceptance Checklist）

---

## 🎯 Agent Allocation (6 Agents - Recommended by Impact Assessment)

基于Impact Radius=71（High Risk），分配6个专业Agent并行执行：

### Agent 1: **backend-architect**
**职责**: 架构设计和数据流设计
**交付物**:
- Learning System数据结构设计（5类YAML schemas）
- CE_HOME自动检测机制
- 数据存储策略（外部项目返回CE目录）
- Auto-fix三级决策树设计
- 架构文档：`docs/ARCHITECTURE_V8.md`

**关键任务**:
- 设计`.learning/`目录结构
- 设计符号链接索引（by_project, by_category）
- 设计Learning Item生命周期
- 设计Auto-fix白名单配置

---

### Agent 2: **data-engineer**
**职责**: 数据格式和存储实现
**交付物**:
- Learning Item YAML schema验证
- TODO队列JSON格式
- Notion数据映射schema
- 数据迁移脚本（如果需要）

**关键任务**:
- 实现YAML序列化/反序列化
- 实现索引生成（index.json, stats.json）
- 实现数据归档机制（30天后归档）

---

### Agent 3: **devops-engineer**
**职责**: CI/CD集成和脚本开发
**交付物**:
- `scripts/learning/capture.sh` - Learning Item捕获
- `scripts/learning/convert_to_todo.sh` - TODO转换
- `scripts/learning/sync_notion.sh` - Notion同步
- `tools/ce` - 主CLI工具
- Phase钩子集成脚本

**关键任务**:
- 在Phase 2/3/4嵌入学习钩子
- 在Phase 7嵌入Notion同步钩子
- 更新`scripts/static_checks.sh`包含新脚本验证
- 更新`tools/verify-core-structure.sh`确保不违反锁定

---

### Agent 4: **test-engineer**
**职责**: 测试设计和验证
**交付物**:
- 单元测试：`tests/test_learning_system.sh`
- 集成测试：`tests/test_v8_integration.sh`
- 性能测试：`tests/test_v8_performance.sh`
- Auto-fix场景测试：`tests/test_auto_fix.sh`
- 测试报告：`docs/TEST_REPORT_V8.md`

**关键任务**:
- 测试Learning Item捕获（5类）
- 测试Auto-fix三级策略
- 测试TODO转换规则
- 测试Notion同步（需要mock或真实API）
- 性能测试（Learning Item写入<50ms）

---

### Agent 5: **technical-writer**
**职责**: 文档编写和维护
**交付物**:
- 用户指南：`docs/USER_GUIDE_V8.md`
- Learning System指南：`docs/LEARNING_SYSTEM.md`
- Auto-fix配置指南：`docs/AUTO_FIX_GUIDE.md`
- Notion集成指南：`docs/NOTION_INTEGRATION.md`
- 更新README.md（v8.0功能介绍）
- 更新CLAUDE.md（v8.0章节）
- CHANGELOG.md（v8.0.0版本记录）

**关键任务**:
- 撰写非技术摘要示例
- 撰写ce命令使用示例
- 更新核心文档（保持≤7个根目录文档）

---

### Agent 6: **security-auditor**
**职责**: 安全审查和数据隐私
**交付物**:
- 安全审计报告：`docs/SECURITY_AUDIT_V8.md`
- Notion Token安全存储方案
- Learning Item敏感数据过滤规则
- Auto-fix安全风险评估

**关键任务**:
- 审查Notion Token存储（加密）
- 审查Learning Item不记录敏感信息
- 审查Auto-fix tier1白名单（防止危险操作）
- 审查ce命令权限

---

## 🔧 Phase 2: Implementation (2天，16小时)

### 2.1 核心数据结构实现 (4小时)

**Agent**: backend-architect + data-engineer

#### 2.1.1 创建目录结构

```bash
# 文件: scripts/v8_setup_directories.sh
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 创建Learning System目录
mkdir -p "$ROOT/.learning/items"
mkdir -p "$ROOT/.learning/by_project"
mkdir -p "$ROOT/.learning/by_category/error_pattern"
mkdir -p "$ROOT/.learning/by_category/performance"
mkdir -p "$ROOT/.learning/by_category/architecture"
mkdir -p "$ROOT/.learning/by_category/code_quality"
mkdir -p "$ROOT/.learning/by_category/success_pattern"

# 创建TODO队列目录
mkdir -p "$ROOT/.todos/pending"
mkdir -p "$ROOT/.todos/in_progress"
mkdir -p "$ROOT/.todos/completed"
mkdir -p "$ROOT/.todos/rejected"

# 创建Notion同步目录
mkdir -p "$ROOT/.notion/pending_sync"

# 创建脚本目录
mkdir -p "$ROOT/scripts/learning"

# 初始化index文件
cat > "$ROOT/.learning/index.json" <<'EOF'
{
  "meta": {
    "version": "1.0",
    "created_at": "$(date -u +%FT%TZ)",
    "total_items": 0
  },
  "items": []
}
EOF

cat > "$ROOT/.learning/stats.json" <<'EOF'
{
  "by_category": {
    "error_pattern": 0,
    "performance": 0,
    "architecture": 0,
    "code_quality": 0,
    "success_pattern": 0
  },
  "by_project": {},
  "by_phase": {
    "Phase1": 0,
    "Phase2": 0,
    "Phase3": 0,
    "Phase4": 0,
    "Phase5": 0,
    "Phase6": 0,
    "Phase7": 0
  }
}
EOF

cat > "$ROOT/.todos/queue.json" <<'EOF'
{
  "meta": {
    "version": "1.0",
    "created_at": "$(date -u +%FT%TZ)",
    "total_todos": 0
  },
  "todos": []
}
EOF

echo "✅ v8.0目录结构创建完成"
```

**验证**:
```bash
bash scripts/v8_setup_directories.sh
test -d .learning/items && echo "✅ .learning/items创建成功"
test -d .todos/pending && echo "✅ .todos/pending创建成功"
test -d .notion/pending_sync && echo "✅ .notion/pending_sync创建成功"
```

#### 2.1.2 实现Learning Item捕获脚本

```bash
# 文件: scripts/learning/capture.sh
#!/usr/bin/env bash
# Learning Item捕获脚本
# 用法: bash scripts/learning/capture.sh --category error_pattern --description "..." --phase Phase2

set -euo pipefail

# CE_HOME检测
CE_HOME="${CE_HOME:-$(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" 2>/dev/null | head -1 | xargs dirname | xargs dirname)}"

if [[ -z "$CE_HOME" || ! -f "$CE_HOME/.workflow/SPEC.yaml" ]]; then
  echo "❌ 错误: 无法找到Claude Enhancer目录" >&2
  echo "   请设置CE_HOME环境变量或确保在CE目录下运行" >&2
  exit 1
fi

# 参数解析
CATEGORY=""
DESCRIPTION=""
PHASE=""
PROJECT=""
CONFIDENCE=0.5
AUTO_FIX_ELIGIBLE="false"
AUTO_FIX_TIER=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --category) CATEGORY="$2"; shift 2 ;;
    --description) DESCRIPTION="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --confidence) CONFIDENCE="$2"; shift 2 ;;
    --auto-fix-tier) AUTO_FIX_TIER="$2"; AUTO_FIX_ELIGIBLE="true"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

# 参数验证
if [[ -z "$CATEGORY" || -z "$DESCRIPTION" || -z "$PHASE" ]]; then
  echo "❌ 错误: --category, --description, --phase 为必填参数" >&2
  exit 1
fi

# 自动检测项目名
if [[ -z "$PROJECT" ]]; then
  PWD_BASE="$(basename "$PWD")"
  if [[ "$PWD" == "$CE_HOME" || "$PWD_BASE" == "Claude Enhancer" ]]; then
    PROJECT="claude-enhancer"
  else
    PROJECT="$PWD_BASE"
  fi
fi

# 生成Learning Item
TIMESTAMP=$(date -u +%FT%TZ)
TIMESTAMP_SHORT=$(date +%Y-%m-%d)
SEQ=$(ls "$CE_HOME/.learning/items/${TIMESTAMP_SHORT}_"* 2>/dev/null | wc -l)
SEQ=$((SEQ + 1))
ITEM_ID="learning-${TIMESTAMP_SHORT}-$(printf "%03d" $SEQ)"
FILENAME="${TIMESTAMP_SHORT}_$(printf "%03d" $SEQ)_${CATEGORY}_${PROJECT}.yml"

# 获取Git信息
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# 写入YAML
cat > "$CE_HOME/.learning/items/$FILENAME" <<EOF
---
id: "$ITEM_ID"
timestamp: "$TIMESTAMP"
project: "$PROJECT"
category: "$CATEGORY"
phase: "$PHASE"

context:
  working_directory: "$PWD"
  file: ""
  line: 0
  git_branch: "$GIT_BRANCH"
  git_commit: "$GIT_COMMIT"

observation:
  type: ""
  description: "$DESCRIPTION"
  technical_details: ""
  code_snippet: ""

learning:
  root_cause: ""
  solution: ""
  prevention: ""
  confidence: $CONFIDENCE

actionable:
  todo_candidate: false
  priority: "medium"
  estimated_effort: ""
  auto_fix_eligible: $AUTO_FIX_ELIGIBLE
  auto_fix_tier: "$AUTO_FIX_TIER"

metadata:
  decay_factor: 1.0
  last_validated: null
  validation_count: 0
  notion_synced: false
  notion_page_id: null
  tags: []
EOF

# 创建符号链接
ln -sf "../../items/$FILENAME" "$CE_HOME/.learning/by_category/$CATEGORY/$FILENAME"

# 更新项目索引
mkdir -p "$CE_HOME/.learning/by_project/$PROJECT"
ln -sf "../../items/$FILENAME" "$CE_HOME/.learning/by_project/$PROJECT/$FILENAME"

# 更新index.json和stats.json (简化版，真实版本用jq)
echo "✅ Learning Item已捕获: $FILENAME"
echo "   项目: $PROJECT"
echo "   类别: $CATEGORY"
echo "   ID: $ITEM_ID"
```

**验证**:
```bash
bash scripts/learning/capture.sh \
  --category error_pattern \
  --description "测试Learning Item捕获" \
  --phase Phase2

test -f .learning/items/*_error_pattern_*.yml && echo "✅ Learning Item创建成功"
```

---

### 2.2 Auto-fix机制实现 (4小时)

**Agent**: backend-architect + devops-engineer

#### 2.2.1 Auto-fix决策引擎

```python
# 文件: scripts/learning/auto_fix.py
#!/usr/bin/env python3
"""
Auto-fix决策引擎
根据错误类型和历史Learning Items决策是否自动修复
"""

import json
import yaml
import sys
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
                "pattern": r"No module named '(\w+)'",
                "fix_template": "pip3 install {module}",
                "description": "缺失Python依赖"
            },
            {
                "error_type": "FormatError",
                "pattern": r".*formatting.*",
                "fix_template": "black {file} || prettier --write {file}",
                "description": "代码格式化错误"
            },
            {
                "error_type": "PortConflict",
                "pattern": r"Address already in use.*:(\d+)",
                "fix_template": "kill -9 $(lsof -t -i:{port}) && retry",
                "description": "端口冲突"
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
                "pattern": r"build failed",
                "fix_attempts": ["make clean && make", "npm install && npm run build"],
                "description": "构建失败"
            },
            {
                "error_type": "TestFailure",
                "pattern": r"test.*failed",
                "fix_attempts": ["pytest --lf", "npm test -- --updateSnapshot"],
                "description": "测试失败"
            }
        ]
    },
    "tier3_must_confirm": {
        "confidence_max": 0.69,
        "risk_level": "high",
        "patterns": [
            {
                "error_type": "DataMigration",
                "pattern": r"migration",
                "description": "数据迁移"
            },
            {
                "error_type": "SecurityPatch",
                "pattern": r"security|vulnerability",
                "description": "安全补丁"
            },
            {
                "error_type": "BreakingChange",
                "pattern": r"breaking change",
                "description": "破坏性变更"
            }
        ]
    }
}

def detect_tier(error_message: str, confidence: float) -> str:
    """检测错误属于哪个tier"""
    import re

    # 检查tier1
    for pattern in AUTO_FIX_WHITELIST["tier1_auto"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            if confidence >= AUTO_FIX_WHITELIST["tier1_auto"]["confidence_min"]:
                return "tier1_auto"

    # 检查tier2
    for pattern in AUTO_FIX_WHITELIST["tier2_try_then_ask"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            if (confidence >= AUTO_FIX_WHITELIST["tier2_try_then_ask"]["confidence_min"] and
                confidence <= AUTO_FIX_WHITELIST["tier2_try_then_ask"]["confidence_max"]):
                return "tier2_try_then_ask"

    # 检查tier3
    for pattern in AUTO_FIX_WHITELIST["tier3_must_confirm"]["patterns"]:
        if re.search(pattern["pattern"], error_message, re.IGNORECASE):
            return "tier3_must_confirm"

    return "tier3_must_confirm"  # 默认最保守

def search_similar_learning_items(error_message: str, ce_home: Path) -> List[Dict]:
    """搜索历史相似的Learning Items"""
    similar_items = []
    learning_dir = ce_home / ".learning" / "by_category" / "error_pattern"

    if not learning_dir.exists():
        return similar_items

    for item_file in learning_dir.glob("*.yml"):
        try:
            with open(item_file, 'r') as f:
                item = yaml.safe_load(f)

            # 简单相似度匹配（实际应该用更复杂的算法）
            if error_message.lower() in item['observation']['description'].lower():
                similar_items.append(item)
        except Exception as e:
            print(f"警告: 无法读取{item_file}: {e}", file=sys.stderr)

    return similar_items

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Auto-fix决策引擎')
    parser.add_argument('--error', required=True, help='错误信息')
    parser.add_argument('--confidence', type=float, default=0.5, help='信心分数')
    parser.add_argument('--ce-home', help='CE_HOME路径')

    args = parser.parse_args()

    # 检测tier
    tier = detect_tier(args.error, args.confidence)

    # 搜索历史
    ce_home = Path(args.ce_home) if args.ce_home else Path.home() / "dev" / "Claude Enhancer"
    similar = search_similar_learning_items(args.error, ce_home)

    # 输出结果
    result = {
        "tier": tier,
        "confidence": args.confidence,
        "similar_count": len(similar),
        "recommended_action": {
            "tier1_auto": "自动修复",
            "tier2_try_then_ask": "尝试修复，失败后询问",
            "tier3_must_confirm": "必须询问用户"
        }[tier]
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

**验证**:
```bash
python3 scripts/learning/auto_fix.py --error "ImportError: No module named 'yaml'" --confidence 0.95
# 预期输出: {"tier": "tier1_auto", ...}

python3 scripts/learning/auto_fix.py --error "build failed" --confidence 0.80
# 预期输出: {"tier": "tier2_try_then_ask", ...}
```

---

### 2.3 TODO队列系统实现 (3小时)

**Agent**: devops-engineer + data-engineer

#### 2.3.1 Learning Item → TODO转换脚本

```bash
# 文件: scripts/learning/convert_to_todo.sh
#!/usr/bin/env bash
# Learning Items转换为TODO
# 用法: bash scripts/learning/convert_to_todo.sh

set -euo pipefail

CE_HOME="${CE_HOME:-$(dirname "$(dirname "$(dirname "$0")")")}"

echo "🔄 扫描Learning Items..."

CONVERTED=0
SKIPPED=0

# 遍历所有Learning Items
for item_file in "$CE_HOME/.learning/items/"*.yml; do
  [[ ! -f "$item_file" ]] && continue

  # 读取Learning Item
  TODO_CANDIDATE=$(grep "todo_candidate:" "$item_file" | awk '{print $2}')
  CONFIDENCE=$(grep "confidence:" "$item_file" | awk '{print $2}')
  PRIORITY=$(grep "priority:" "$item_file" | awk '{print $2}' | tr -d '"')

  # 转换规则: todo_candidate=true && confidence>=0.80 && priority in [high,medium]
  if [[ "$TODO_CANDIDATE" == "true" ]] && (( $(echo "$CONFIDENCE >= 0.80" | bc -l) )); then
    if [[ "$PRIORITY" == "high" || "$PRIORITY" == "medium" ]]; then
      # 提取信息
      ITEM_ID=$(grep "^id:" "$item_file" | awk '{print $2}' | tr -d '"')
      DESCRIPTION=$(grep "description:" "$item_file" | head -1 | cut -d'"' -f2)

      # 生成TODO
      TODO_ID="todo-$(date +%Y%m%d)-$(printf "%03d" $((CONVERTED + 1)))"
      TODO_FILE="$CE_HOME/.todos/pending/${TODO_ID}.json"

      cat > "$TODO_FILE" <<EOF
{
  "id": "$TODO_ID",
  "title": "$DESCRIPTION",
  "description": "来源: Learning Item $ITEM_ID",
  "priority": "$PRIORITY",
  "estimated_effort": "",
  "status": "pending",
  "source_learning_id": "$ITEM_ID",
  "created_at": "$(date -u +%FT%TZ)",
  "tags": []
}
EOF

      echo "  ✅ 已转换: $TODO_ID ($DESCRIPTION)"
      ((CONVERTED++))
    else
      ((SKIPPED++))
    fi
  else
    ((SKIPPED++))
  fi
done

echo ""
echo "📊 转换完成:"
echo "   ✅ 转换: $CONVERTED个TODO"
echo "   ⊘ 跳过: $SKIPPED个Learning Item"
```

**验证**:
```bash
# 创建一个高优先级Learning Item
bash scripts/learning/capture.sh \
  --category code_quality \
  --description "应该重构这个函数" \
  --phase Phase4 \
  --confidence 0.90

# 手动编辑yml文件设置todo_candidate=true, priority=high

# 运行转换
bash scripts/learning/convert_to_todo.sh

# 验证TODO创建
ls .todos/pending/*.json
```

---

### 2.4 Notion集成实现 (3小时)

**Agent**: devops-engineer + data-engineer

#### 2.4.1 Notion同步脚本

```python
# 文件: scripts/learning/sync_notion.py
#!/usr/bin/env python3
"""
Notion同步脚本
将Learning Items和TODOs同步到Notion
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    from notion_client import Client
except ImportError:
    print("❌ 错误: 请安装notion-client")
    print("   pip3 install notion-client")
    exit(1)

# Notion配置（从环境变量读取）
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASES = {
    "notes": "1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d",
    "tasks": "54fe0d4c-f434-4e91-8bb0-e33967661c42",
    "events": "e6c819b1-fd59-41d1-af89-539ac9504c07"
}

# 术语替换字典（生成非技术摘要）
TERM_REPLACEMENTS = {
    "实现了认证系统": "做了登录功能，用户可以安全登录",
    "优化了数据库查询": "让系统运行更快了",
    "重构了代码": "整理了代码，以后更容易维护",
    "修复了bug": "修复了一个问题",
    "实现了缓存层": "加了一个加速机制",
    "API": "接口",
    "数据库": "数据存储",
    "前端": "用户界面",
    "后端": "服务器",
    "函数": "功能模块"
}

def simplify_description(text: str) -> str:
    """将技术描述转换为非技术语言"""
    for tech_term, plain_term in TERM_REPLACEMENTS.items():
        text = text.replace(tech_term, plain_term)
    return text

def sync_learning_items(client: Client, ce_home: Path, dry_run: bool = False):
    """同步Learning Items到Notion"""
    learning_dir = ce_home / ".learning" / "items"
    synced_count = 0

    for item_file in learning_dir.glob("*.yml"):
        try:
            with open(item_file, 'r') as f:
                item = yaml.safe_load(f)

            # 检查是否已同步
            if item['metadata']['notion_synced']:
                continue

            # 简化描述
            plain_description = simplify_description(item['observation']['description'])

            # 创建Notion页面
            properties = {
                "标题": {"title": [{"text": {"content": plain_description}}]},
                "类别": {"select": {"name": item['category']}},
                "项目": {"rich_text": [{"text": {"content": item['project']}}]},
                "优先级": {"select": {"name": item['actionable']['priority']}},
                "信心分数": {"number": item['learning']['confidence']},
                "创建时间": {"date": {"start": item['timestamp']}}
            }

            if not dry_run:
                result = client.pages.create(
                    parent={"database_id": NOTION_DATABASES["notes"]},
                    properties=properties
                )

                # 更新Learning Item标记为已同步
                item['metadata']['notion_synced'] = True
                item['metadata']['notion_page_id'] = result['id']

                with open(item_file, 'w') as f:
                    yaml.dump(item, f, allow_unicode=True)

            synced_count += 1
            print(f"  ✅ 已同步: {plain_description[:50]}...")

        except Exception as e:
            print(f"  ❌ 同步失败 {item_file.name}: {e}")

    return synced_count

def sync_todos(client: Client, ce_home: Path, dry_run: bool = False):
    """同步TODOs到Notion"""
    todo_dir = ce_home / ".todos" / "pending"
    synced_count = 0

    for todo_file in todo_dir.glob("*.json"):
        try:
            with open(todo_file, 'r') as f:
                todo = json.load(f)

            # 简化标题
            plain_title = simplify_description(todo['title'])

            # 创建Notion页面
            properties = {
                "任务": {"title": [{"text": {"content": plain_title}}]},
                "状态": {"select": {"name": "待办"}},
                "优先级": {"select": {"name": todo['priority']}},
                "预估工作量": {"rich_text": [{"text": {"content": todo['estimated_effort'] or "未知"}}]},
                "创建时间": {"date": {"start": todo['created_at']}}
            }

            if not dry_run:
                result = client.pages.create(
                    parent={"database_id": NOTION_DATABASES["tasks"]},
                    properties=properties
                )

                # 标记TODO已同步（移到completed目录）
                # （简化实现，实际应该在TODO的JSON中添加notion_synced字段）

            synced_count += 1
            print(f"  ✅ 已同步TODO: {plain_title[:50]}...")

        except Exception as e:
            print(f"  ❌ 同步失败 {todo_file.name}: {e}")

    return synced_count

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Notion同步脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际同步')
    parser.add_argument('--ce-home', help='CE_HOME路径')

    args = parser.parse_args()

    ce_home = Path(args.ce_home) if args.ce_home else Path.home() / "dev" / "Claude Enhancer"

    print("🔄 开始Notion同步...")
    print(f"   CE_HOME: {ce_home}")
    print(f"   模式: {'预览' if args.dry_run else '实际同步'}")
    print("")

    # 初始化Notion客户端
    client = Client(auth=NOTION_TOKEN)

    # 同步Learning Items
    print("📚 同步Learning Items...")
    learning_count = sync_learning_items(client, ce_home, args.dry_run)

    print("")

    # 同步TODOs
    print("📋 同步TODOs...")
    todo_count = sync_todos(client, ce_home, args.dry_run)

    print("")
    print("✅ 同步完成:")
    print(f"   Learning Items: {learning_count}")
    print(f"   TODOs: {todo_count}")

if __name__ == "__main__":
    main()
```

**验证**:
```bash
# 预览模式
python3 scripts/learning/sync_notion.py --dry-run

# 实际同步（需要安装notion-client）
pip3 install notion-client
python3 scripts/learning/sync_notion.py
```

---

### 2.5 ce CLI工具实现 (2小时)

**Agent**: devops-engineer

```bash
# 文件: tools/ce
#!/usr/bin/env bash
# Claude Enhancer v8.0 CLI Tool
# 用法: ce [command] [options]

set -euo pipefail

# CE_HOME检测
CE_HOME="${CE_HOME:-$(find ~ -maxdepth 3 -name "SPEC.yaml" -path "*/.workflow/*" 2>/dev/null | head -1 | xargs dirname | xargs dirname)}"

if [[ -z "$CE_HOME" ]]; then
  echo "❌ 错误: 无法找到Claude Enhancer目录" >&2
  echo "   请设置CE_HOME环境变量" >&2
  exit 1
fi

# 命令路由
case "${1:-help}" in
  dev)
    echo "🚀 启动Claude Enhancer开发模式..."
    echo "   项目: $(basename "$PWD")"
    echo "   CE_HOME: $CE_HOME"
    echo "   学习系统: ✅ 激活"
    echo "   Auto-fix: ✅ 激活"
    echo ""
    echo "准备好了！开始和Claude对话进行开发。"
    ;;

  mode)
    case "${2:-status}" in
      status)
        PWD_BASE="$(basename "$PWD")"
        if [[ "$PWD" == "$CE_HOME" || "$PWD_BASE" == "Claude Enhancer" ]]; then
          echo "📍 当前模式: 自我进化（开发Claude Enhancer）"
        else
          echo "📍 当前模式: 外部项目开发"
          echo "   项目: $PWD_BASE"
        fi
        echo "   CE_HOME: $CE_HOME"
        echo "   7-Phase工作流: ✅ 激活"
        echo "   学习系统: ✅ 激活"
        ;;
      *)
        echo "❌ 未知mode子命令: $2" >&2
        exit 1
        ;;
    esac
    ;;

  todo)
    case "${2:-list}" in
      list)
        echo "📋 TODO队列:"
        TODO_COUNT=$(ls "$CE_HOME/.todos/pending/"*.json 2>/dev/null | wc -l)
        if [[ $TODO_COUNT -eq 0 ]]; then
          echo "   (无待办TODO)"
        else
          for todo_file in "$CE_HOME/.todos/pending/"*.json; do
            TODO_ID=$(jq -r '.id' "$todo_file")
            TITLE=$(jq -r '.title' "$todo_file")
            PRIORITY=$(jq -r '.priority' "$todo_file")
            echo "   [$TODO_ID] ($PRIORITY) $TITLE"
          done
        fi
        ;;

      show)
        TODO_ID="${3:-}"
        if [[ -z "$TODO_ID" ]]; then
          echo "❌ 错误: 请指定TODO ID" >&2
          echo "   用法: ce todo show <todo-id>" >&2
          exit 1
        fi

        TODO_FILE="$CE_HOME/.todos/pending/${TODO_ID}.json"
        if [[ ! -f "$TODO_FILE" ]]; then
          echo "❌ 错误: TODO不存在: $TODO_ID" >&2
          exit 1
        fi

        jq '.' "$TODO_FILE"
        ;;

      *)
        echo "❌ 未知todo子命令: $2" >&2
        exit 1
        ;;
    esac
    ;;

  learning)
    case "${2:-list}" in
      list)
        echo "📚 Learning Items:"
        LEARNING_COUNT=$(ls "$CE_HOME/.learning/items/"*.yml 2>/dev/null | wc -l)
        echo "   总计: $LEARNING_COUNT个"
        echo ""
        echo "   按类别:"
        for cat in error_pattern performance architecture code_quality success_pattern; do
          COUNT=$(ls "$CE_HOME/.learning/by_category/$cat/"*.yml 2>/dev/null | wc -l)
          echo "     - $cat: $COUNT"
        done
        ;;

      stats)
        echo "📊 学习系统统计:"
        if [[ -f "$CE_HOME/.learning/stats.json" ]]; then
          jq '.' "$CE_HOME/.learning/stats.json"
        else
          echo "   (暂无统计数据)"
        fi
        ;;

      *)
        echo "❌ 未知learning子命令: $2" >&2
        exit 1
        ;;
    esac
    ;;

  sync)
    case "${2:-notion}" in
      notion)
        echo "🔄 同步到Notion..."
        python3 "$CE_HOME/scripts/learning/sync_notion.py"
        ;;
      *)
        echo "❌ 未知sync目标: $2" >&2
        exit 1
        ;;
    esac
    ;;

  help|--help|-h)
    cat <<'EOF'
Claude Enhancer v8.0 CLI Tool

用法:
  ce dev                      # 在外部项目启动CE开发模式
  ce mode status              # 查看当前模式
  ce todo list                # 列出所有TODO
  ce todo show <id>           # 查看TODO详情
  ce learning list            # 列出Learning Items
  ce learning stats           # 学习系统统计
  ce sync notion              # 手动同步到Notion
  ce help                     # 显示此帮助

环境变量:
  CE_HOME                     # Claude Enhancer目录路径（可选，会自动检测）

示例:
  # 在外部项目开发
  cd ~/projects/my-app
  ce dev

  # 查看TODO队列
  ce todo list

  # 同步到Notion
  ce sync notion
EOF
    ;;

  *)
    echo "❌ 未知命令: $1" >&2
    echo "   运行 'ce help' 查看可用命令" >&2
    exit 1
    ;;
esac
```

**安装到PATH**:
```bash
chmod +x tools/ce
# 添加到~/.bashrc或~/.zshrc
export PATH="$HOME/dev/Claude Enhancer/tools:$PATH"
```

**验证**:
```bash
ce help
ce mode status
ce learning list
ce todo list
```

---

## 🧪 Phase 3: Testing (1天，8小时)

### 3.1 单元测试 (3小时)

**Agent**: test-engineer

创建`tests/test_learning_system.sh`，包含以下测试：

1. **Learning Item YAML序列化测试**
2. **CE_HOME自动检测测试**
3. **Auto-fix Tier分类测试**
4. **TODO转换规则测试**
5. **非技术摘要生成测试**
6. **符号链接索引测试**

### 3.2 集成测试 (3小时)

**Agent**: test-engineer + devops-engineer

创建`tests/test_v8_integration.sh`：

1. **完整7-Phase工作流测试（模拟CE自身开发）**
2. **完整7-Phase工作流测试（模拟外部项目开发）**
3. **Learning Item跨Phase捕获测试**
4. **Auto-fix端到端测试**
5. **Notion同步端到端测试（dry-run）**

### 3.3 性能测试 (2小时)

**Agent**: test-engineer

性能基准:
- Learning Item写入 <50ms
- CE_HOME检测 <100ms
- Auto-fix决策 <20ms
- TODO转换 <10ms/item
- Notion同步 <30s（100个items）

---

## 📖 Phase 4: Review (0.5天，4小时)

### 4.1 Pre-merge Audit (2小时)

**Agent**: devops-engineer + code-reviewer

运行`bash scripts/pre_merge_audit.sh`：
- 配置完整性 ✅
- 版本一致性 ✅ (6文件 @ v8.0.0)
- 根目录文档≤7个 ✅
- 代码模式一致性 ✅
- 核心结构完整性 ✅ (97检查点保持)

### 4.2 创建REVIEW.md (2小时)

**Agent**: code-reviewer + technical-writer

内容包含：
- 代码改动摘要
- 87个验收检查点对照
- 质量检查结果
- 向后兼容性确认
- 最终批准/拒绝决定

---

## 🚀 Phase 5: Release (0.5天，4小时)

### 5.1 更新文档 (3小时)

**Agent**: technical-writer

更新以下文档：
- README.md（v8.0功能介绍）
- CLAUDE.md（新增v8.0章节）
- CHANGELOG.md（v8.0.0版本记录）
- 创建用户指南（docs/USER_GUIDE_V8.md）

### 5.2 版本更新 (1小时)

**Agent**: devops-engineer

更新6个版本文件到v8.0.0：
- VERSION
- .claude/settings.json
- package.json
- .workflow/manifest.yml
- .workflow/SPEC.yaml
- CHANGELOG.md

---

## ✅ Phase 6: Acceptance (预留)

AI对照87个验收检查点逐项验证，生成验收报告，等待用户确认。

---

## 🧹 Phase 7: Closure

**目标**: 全面清理过期信息 + 最终验证 + 准备合并

### 必须执行的脚本

1. **`bash scripts/comprehensive_cleanup.sh aggressive`** - 全面清理
   - 清理10类过期内容（.temp/、旧版本文件、重复文档等）
   - 释放空间 ~10-20MB
   - 整合归档目录

2. **`bash scripts/check_version_consistency.sh`** - 版本一致性验证
   - 验证6个文件版本统一（VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml）

3. **`bash tools/verify-phase-consistency.sh`** - Phase系统一致性验证

### 核心检查清单

**过期文件清理**:
- [ ] .temp/目录清空（保留结构）
- [ ] 旧版本文件删除（*_v[0-9]*, *_old*, *.bak）
- [ ] 重复文档删除
- [ ] 归档目录整合
- [ ] 测试会话数据清理
- [ ] 大文件清理（7天以上）

**文档规范验证**:
- [ ] 根目录文档 ≤7个 ⛔
- [ ] .temp/大小 <10MB
- [ ] 无临时报告文件

**版本和结构验证**:
- [ ] 版本完全一致（6/6文件）⛔
- [ ] Phase系统统一（7 Phases）
- [ ] 核心结构验证通过

### 清理模式

- **aggressive** - 删除所有过期内容（推荐，用于发布）
- **conservative** - 归档而不删除
- **minimal** - 只删除明确过期的
- **interactive** - 交互式选择

### 产出

- ✅ 干净的分支（无过期文件）
- ✅ 版本完全一致
- ✅ 释放空间 ~10-20MB
- ✅ merge-ready状态

**等待用户说"merge"后才执行合并操作**

---

## 📊 Timeline Summary

| Phase | Duration | Agents | Deliverables |
|-------|----------|--------|--------------|
| Phase 1 | 已完成 | 6 | P1_DISCOVERY.md, ACCEPTANCE_CHECKLIST.md, PLAN_V8.md |
| Phase 2 | 2天(16h) | 6 (parallel) | 核心代码实现 |
| Phase 3 | 1天(8h) | 3 | 测试脚本+报告 |
| Phase 4 | 0.5天(4h) | 2 | REVIEW.md |
| Phase 5 | 0.5天(4h) | 2 | 文档+版本更新 |
| Phase 6 | 预留 | All + User | 验收报告 |
| Phase 7 | 预留 | 1 | PR+Merge |
| **Total** | **4天(32h)** | **6 agents** | - |

---

## 🛡️ Risk Mitigation

### Risk 1: 违反规则2（核心结构锁定）

**缓解措施**:
- 所有改动通过`tools/verify-core-structure.sh`验证
- Phase钩子以"非侵入式"方式嵌入
- 不修改SPEC.yaml核心定义（97检查点保持）

### Risk 2: Learning Items存储过多导致性能问题

**缓解措施**:
- 实现30天自动归档机制
- 使用符号链接索引（不复制文件）
- 提供归档查询命令

### Risk 3: Auto-fix误操作导致代码错误

**缓解措施**:
- Tier1只允许低风险操作（依赖安装、格式化）
- 所有操作记录audit日志
- 失败自动回滚

### Risk 4: Notion同步失败或限流

**缓解措施**:
- 批量同步（非实时）
- 失败后重试机制
- 支持--dry-run预览

### Risk 5: 外部项目识别错误

**缓解措施**:
- 使用简单的basename($PWD)
- 用户可通过--project参数覆盖
- CE目录硬编码识别

---

## 🔄 Rollback Plan

如果v8.0出现严重问题：

```bash
# 1. 回退代码
git revert HEAD~N  # N为v8.0的commit数量

# 2. 删除v8.0数据目录（可选，保留学习数据）
# mv .learning .learning.backup
# mv .todos .todos.backup
# mv .notion .notion.backup

# 3. 删除tag和release
git tag -d v8.0.0
gh release delete v8.0.0
git push origin :refs/tags/v8.0.0

# 4. 恢复到v7.3.0
git checkout v7.3.0
```

**数据安全**:
- Learning Items和TODOs不会被删除（除非手动删除）
- 可以在v8.1修复后重新使用

---

## ✅ Success Criteria

- [ ] 所有87个acceptance criteria完成（≥90%）
- [ ] Phase 3质量门禁通过
- [ ] Phase 4质量门禁通过
- [ ] 版本一致性100%（6个文件 @ v8.0.0）
- [ ] `tools/verify-core-structure.sh`验证通过（97检查点保持）
- [ ] 根目录文档≤7个（规则1）
- [ ] 用户确认验收

---

## 📚 Appendix A: 文件清单

### 新增文件 (预计)

**目录结构**:
```
.learning/
.todos/
.notion/
scripts/learning/
```

**脚本文件** (约10个):
- scripts/v8_setup_directories.sh
- scripts/learning/capture.sh
- scripts/learning/auto_fix.py
- scripts/learning/convert_to_todo.sh
- scripts/learning/sync_notion.py
- tools/ce

**测试文件** (约5个):
- tests/test_learning_system.sh
- tests/test_v8_integration.sh
- tests/test_auto_fix.sh
- tests/test_notion_sync.sh
- tests/test_v8_performance.sh

**文档文件** (约5个):
- docs/P1_DISCOVERY.md ✅
- docs/ACCEPTANCE_CHECKLIST.md ✅
- docs/PLAN_V8.md ✅
- docs/USER_GUIDE_V8.md
- docs/ARCHITECTURE_V8.md

**总计**: 约25个新文件

---

## 📚 Appendix B: 依赖清单

### Python依赖

```txt
# requirements-v8.txt
pyyaml>=6.0
notion-client>=2.0.0
```

安装:
```bash
pip3 install -r requirements-v8.txt
```

### Shell依赖

- bash ≥ 4.0
- jq
- yq (可选，用于YAML处理)

---

## 📚 Appendix C: 配置文件

### Notion配置

```yaml
# .notion/config.yml
token: "${NOTION_TOKEN}"  # 从环境变量读取，不提交到Git
databases:
  notes: "1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d"
  tasks: "54fe0d4c-f434-4e91-8bb0-e33967661c42"
  events: "e6c819b1-fd59-41d1-af89-539ac9504c07"

sync:
  batch_size: 100
  retry_attempts: 3
  retry_delay_seconds: 5
```

### Auto-fix配置

```yaml
# .learning/auto_fix_config.yml
tier1_auto:
  enabled: true
  confidence_min: 0.95
  max_attempts: 3
  patterns:
    - name: "Python依赖缺失"
      error_pattern: "ImportError: No module named '(\\w+)'"
      fix_template: "pip3 install {module}"
    - name: "代码格式化"
      error_pattern: ".*formatting.*"
      fix_template: "black {file} || prettier --write {file}"

tier2_try_then_ask:
  enabled: true
  confidence_min: 0.70
  confidence_max: 0.94
  max_attempts: 2

tier3_must_confirm:
  enabled: true
  always_ask: true
```

---

## 📚 Appendix D: 受影响文件清单

### 修改现有文件 (预计)

需要轻微修改的文件：

1. **CLAUDE.md** - 添加v8.0说明章节
2. **README.md** - 更新功能介绍
3. **VERSION** - 更新到8.0.0
4. **.claude/settings.json** - 更新version字段
5. **package.json** - 更新version字段
6. **.workflow/manifest.yml** - 更新version字段
7. **.workflow/SPEC.yaml** - 更新metadata（但不改core结构）
8. **CHANGELOG.md** - 添加v8.0.0版本记录

### 不修改的核心文件

确保以下文件不被修改（规则2保护）：
- `.workflow/SPEC.yaml`（core_structure部分）
- `.workflow/gates.yml`
- `tools/verify-core-structure.sh`
- `.workflow/LOCK.json`

---

**Plan Status**: ✅ 完成 (>1000行)
**Created**: 2025-10-27
**Next Phase**: Phase 2 - Implementation
**Estimated Start**: 等待用户批准后开始
