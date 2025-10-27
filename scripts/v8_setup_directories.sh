#!/usr/bin/env bash
# v8.0目录结构初始化脚本
# 用途：创建Learning System、TODO队列、Notion同步所需的目录结构
# 日期：2025-10-27

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🏗️  初始化Claude Enhancer v8.0目录结构..."
echo "   根目录: $ROOT"
echo ""

# 创建Learning System目录
echo "[1/4] 创建Learning System目录..."
mkdir -p "$ROOT/.learning/items"
mkdir -p "$ROOT/.learning/by_project"
mkdir -p "$ROOT/.learning/by_category/error_pattern"
mkdir -p "$ROOT/.learning/by_category/performance"
mkdir -p "$ROOT/.learning/by_category/architecture"
mkdir -p "$ROOT/.learning/by_category/code_quality"
mkdir -p "$ROOT/.learning/by_category/success_pattern"
echo "   ✅ .learning/ 创建完成"

# 创建TODO队列目录
echo "[2/4] 创建TODO队列目录..."
mkdir -p "$ROOT/.todos/pending"
mkdir -p "$ROOT/.todos/in_progress"
mkdir -p "$ROOT/.todos/completed"
mkdir -p "$ROOT/.todos/rejected"
echo "   ✅ .todos/ 创建完成"

# 创建Notion同步目录
echo "[3/4] 创建Notion同步目录..."
mkdir -p "$ROOT/.notion/pending_sync"
echo "   ✅ .notion/ 创建完成"

# 创建脚本目录
echo "[4/4] 创建Learning脚本目录..."
mkdir -p "$ROOT/scripts/learning"
echo "   ✅ scripts/learning/ 创建完成"

# 初始化index文件
echo ""
echo "📝 初始化索引文件..."

cat > "$ROOT/.learning/index.json" <<EOF
{
  "meta": {
    "version": "1.0",
    "created_at": "$(date -u +%FT%TZ)",
    "total_items": 0
  },
  "items": []
}
EOF
echo "   ✅ .learning/index.json"

cat > "$ROOT/.learning/stats.json" <<EOF
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
echo "   ✅ .learning/stats.json"

cat > "$ROOT/.todos/queue.json" <<EOF
{
  "meta": {
    "version": "1.0",
    "created_at": "$(date -u +%FT%TZ)",
    "total_todos": 0
  },
  "todos": []
}
EOF
echo "   ✅ .todos/queue.json"

cat > "$ROOT/.notion/config.yml" <<'EOF'
# Notion Integration Configuration
# Token从环境变量NOTION_TOKEN读取，不要硬编码在这里

token_env_var: "NOTION_TOKEN"

databases:
  notes: "1fb0ec1c-c75b-482b-be0c-ffd4fdb5fd4d"
  tasks: "54fe0d4c-f434-4e91-8bb0-e33967661c42"
  events: "e6c819b1-fd59-41d1-af89-539ac9504c07"

sync:
  batch_size: 100
  retry_attempts: 3
  retry_delay_seconds: 5
  dry_run_default: false
EOF
echo "   ✅ .notion/config.yml"

# 更新.gitignore
echo ""
echo "🔒 更新.gitignore（保护用户数据）..."
if ! grep -q ".learning/" "$ROOT/.gitignore" 2>/dev/null; then
  cat >> "$ROOT/.gitignore" <<'EOF'

# Claude Enhancer v8.0 - Learning System
.learning/items/
.learning/by_project/
.learning/by_category/
.todos/
.notion/pending_sync/
.notion/sync_history.json
EOF
  echo "   ✅ .gitignore已更新"
else
  echo "   ⊘ .gitignore已包含v8.0规则"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ v8.0目录结构初始化完成                                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "目录结构："
echo "  .learning/          # Learning System数据"
echo "    ├── items/        # Learning Item存储"
echo "    ├── by_project/   # 按项目索引"
echo "    ├── by_category/  # 按类别索引"
echo "    ├── index.json    # 全局索引"
echo "    └── stats.json    # 统计信息"
echo ""
echo "  .todos/             # TODO队列"
echo "    ├── pending/      # 待处理"
echo "    ├── in_progress/  # 进行中"
echo "    ├── completed/    # 已完成"
echo "    └── rejected/     # 已拒绝"
echo ""
echo "  .notion/            # Notion同步"
echo "    ├── config.yml    # 配置文件"
echo "    └── pending_sync/ # 待同步队列"
echo ""
echo "  scripts/learning/   # Learning脚本目录"
echo ""
echo "下一步："
echo "  1. 运行: bash scripts/learning/capture.sh --help"
echo "  2. 开始捕获Learning Items"
echo ""
