#!/usr/bin/env bash
# Claude Enhancer 7.0 - Project Initializer (Simple Version)
# 只做一件事：快速初始化项目，链接到中央引擎

set -euo pipefail

VERSION="7.0.0"

# 参数
TARGET_PATH="${1:?Usage: $0 <project-path> [type] [stack]}"
PROJECT_TYPE="${2:-web-app}"
PROJECT_STACK="${3:-generic}"

# 计算路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_ABS="$(mkdir -p "$(dirname "$TARGET_PATH")" && cd "$(dirname "$TARGET_PATH")" && pwd)/$(basename "$TARGET_PATH")"
PROJECT_NAME="$(basename "$TARGET_ABS")"

echo "🚀 Initializing: $PROJECT_NAME"

# 创建项目目录
mkdir -p "$TARGET_ABS/.claude"
cd "$TARGET_ABS"

# 链接引擎（简单直接）
ln -sf "$ENGINE_ROOT/.claude/engine" .claude/engine
ln -sf "$ENGINE_ROOT/.claude/hooks" .claude/hooks
ln -sf "$ENGINE_ROOT/.claude/templates" .claude/templates

# VERSION
echo "$VERSION" > VERSION

# 配置文件
cat > .claude/config.json <<JSON
{
  "project": "$PROJECT_NAME",
  "type": "$PROJECT_TYPE",
  "stack": "$PROJECT_STACK",
  "engine_root": "$ENGINE_ROOT",
  "version": "$VERSION",
  "created_at": "$(date -Iseconds)"
}
JSON

# README
cat > README.md <<MD
# $PROJECT_NAME

Type: \`$PROJECT_TYPE\` | Stack: \`$PROJECT_STACK\`

Engine: Linked to Claude Enhancer 7.0

## Usage

\`\`\`bash
bash .claude/engine/workflow.sh --validate
bash .claude/engine/agent_selector.sh --plan
\`\`\`
MD

# CLAUDE.md
cat > CLAUDE.md <<MD
# Claude Enhancer Project

Type: $PROJECT_TYPE
Stack: $PROJECT_STACK
Engine: $ENGINE_ROOT/.claude/engine

Follow 7-Phase workflow.
MD

# .gitignore
cat > .gitignore <<'GI'
node_modules/
venv/
.env
.DS_Store
.claude/knowledge/sessions/
GI

# 基础目录
case "$PROJECT_TYPE" in
  web-app)
    mkdir -p src public
    echo 'export const hello = () => "Hello";' > "src/index.${PROJECT_STACK}"
    echo '<!doctype html><title>App</title><div id="root"></div>' > public/index.html
    ;;
  cli-tool)
    mkdir -p bin src
    echo '#!/usr/bin/env bash\necho "Hello CLI"' > bin/run.sh
    chmod +x bin/run.sh
    ;;
  library)
    mkdir -p src tests
    echo 'export const add = (a,b) => a+b;' > "src/main.${PROJECT_STACK}"
    ;;
  *)
    mkdir -p src
    ;;
esac

# Git初始化
git init -q
git add -A
git commit -qm "chore: init with Claude Enhancer $VERSION"

echo "✅ Done! Project created at: $TARGET_ABS"
tree -L 2 -a . 2>/dev/null || ls -la
