#!/usr/bin/env bash
set -euo pipefail

# Claude Enhancer 入口总开关 - 确保进入8-Phase工作流
# 使用方式: ce-enter "P3 修复登录节流"

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="${REPO_ROOT}/.workflow"
WORKTREES_BASE="/srv/worktrees"
LOG_FILE="${WORKFLOW_DIR}/logs/enter.log"

# 确保日志目录存在
mkdir -p "${WORKFLOW_DIR}/logs"

# 日志函数
log() {
    local msg="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') [ce-enter] ${msg}" >> "${LOG_FILE}"
    echo -e "${GREEN}[CE]${NC} ${msg}"
}

error() {
    local msg="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') [ce-enter] ERROR: ${msg}" >> "${LOG_FILE}"
    echo -e "${RED}[ERROR]${NC} ${msg}" >&2
}

# 清洗中文为slug
slugify() {
    local input="$1"
    # 使用Python进行中文转拼音（如果可用）
    if command -v python3 >/dev/null 2>&1; then
        echo "$input" | python3 -c "
import sys, re
text = sys.stdin.read().strip()
# 简单的中文替换规则
replacements = {
    '修复': 'fix', '登录': 'login', '节流': 'throttle',
    '优化': 'optimize', '添加': 'add', '删除': 'delete',
    '更新': 'update', '重构': 'refactor', '测试': 'test',
    '文档': 'docs', '配置': 'config', '部署': 'deploy'
}
for ch, en in replacements.items():
    text = text.replace(ch, en)
# 清理非字母数字字符
text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
text = re.sub(r'^-+|-+$', '', text)
print(text.lower() or 'dev')
" 2>/dev/null || echo "dev"
    else
        # 后备方案：简单清理
        echo "$input" | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/^-*//;s/-*$//' | tr '[:upper:]' '[:lower:]' | head -c 30
    fi
}

# 解析参数
TASK_DESC="${1:-}"
if [ -z "$TASK_DESC" ]; then
    # 无参数默认
    PHASE="P3"
    SLUG="dev"
    log "使用默认参数: P3/dev"
else
    # 从描述中提取phase（如果有）
    if [[ "$TASK_DESC" =~ ^P[1-8] ]]; then
        PHASE=$(echo "$TASK_DESC" | grep -oE '^P[1-8]')
        TASK_DESC=${TASK_DESC#$PHASE }
    else
        PHASE="P3"
    fi
    SLUG=$(slugify "$TASK_DESC")
    log "解析任务: phase=$PHASE, slug=$SLUG"
fi

# 生成分支名
DATE=$(date +'%Y%m%d')
TIME=$(date +'%H%M%S')
BRANCH_NAME="${PHASE}/${DATE}-${SLUG}-${TIME}"

# 检查当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# 判断是否需要创建新分支
NEED_NEW_BRANCH=false
if [[ ! "$CURRENT_BRANCH" =~ ^P[1-8]/[0-9]{8}- ]]; then
    NEED_NEW_BRANCH=true
    log "当前分支不符合规范: $CURRENT_BRANCH，需要创建新分支"
fi

# 检查ACTIVE文件
NEED_ACTIVE=false
if [ ! -f "${WORKFLOW_DIR}/ACTIVE" ]; then
    NEED_ACTIVE=true
    log "缺少ACTIVE文件，需要创建"
else
    # 验证ACTIVE格式
    if ! grep -q "^phase:" "${WORKFLOW_DIR}/ACTIVE" || \
       ! grep -q "^ticket:" "${WORKFLOW_DIR}/ACTIVE" || \
       ! grep -q "^started_at:" "${WORKFLOW_DIR}/ACTIVE"; then
        NEED_ACTIVE=true
        log "ACTIVE文件格式不完整，需要重建"
    fi
fi

# 创建新分支（如果需要）
if [ "$NEED_NEW_BRANCH" = true ]; then
    log "创建新分支: $BRANCH_NAME"

    # 保存当前工作
    if [ -n "$(git status --porcelain)" ]; then
        log "暂存当前工作..."
        git stash push -m "Auto-stash by ce-enter at $(date)" || true
    fi

    # 创建并切换分支
    git checkout -b "$BRANCH_NAME" || {
        error "无法创建分支 $BRANCH_NAME"
        exit 1
    }

    CURRENT_BRANCH="$BRANCH_NAME"
fi

# 创建或更新ACTIVE文件
if [ "$NEED_ACTIVE" = true ] || [ "$NEED_NEW_BRANCH" = true ]; then
    log "生成ACTIVE文件..."

    TICKET="T-${DATE}-$(printf "%03d" $((RANDOM % 1000)))"
    STARTED_AT=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

    cat > "${WORKFLOW_DIR}/ACTIVE" <<EOF
phase: ${PHASE}
ticket: ${TICKET}
started_at: ${STARTED_AT}
description: ${TASK_DESC:-Development task}
branch: ${CURRENT_BRANCH}
EOF

    log "ACTIVE文件已创建: phase=$PHASE, ticket=$TICKET"
fi

# 设置worktree
REPO_NAME=$(basename "$REPO_ROOT")
WORKTREE_PATH="${WORKTREES_BASE}/${REPO_NAME}/${CURRENT_BRANCH}"

# 检查worktree是否已存在
if git worktree list | grep -q "$WORKTREE_PATH"; then
    log "Worktree已存在: $WORKTREE_PATH"
else
    log "创建worktree: $WORKTREE_PATH"

    # 确保目录存在
    sudo mkdir -p "$(dirname "$WORKTREE_PATH")"
    sudo chown -R $(id -u):$(id -g) "${WORKTREES_BASE}/${REPO_NAME}" 2>/dev/null || true

    # 添加worktree
    git worktree add "$WORKTREE_PATH" "$CURRENT_BRANCH" || {
        error "无法创建worktree"
        exit 1
    }
fi

# 同步ACTIVE到worktree
cp "${WORKFLOW_DIR}/ACTIVE" "${WORKTREE_PATH}/.workflow/ACTIVE" 2>/dev/null || {
    mkdir -p "${WORKTREE_PATH}/.workflow"
    cp "${WORKFLOW_DIR}/ACTIVE" "${WORKTREE_PATH}/.workflow/ACTIVE"
}

# 输出启动信息
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Claude Enhancer 工作流已启动${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📍 分支: ${YELLOW}${CURRENT_BRANCH}${NC}"
echo -e "📂 工位: ${YELLOW}${WORKTREE_PATH}${NC}"
echo -e "🎯 阶段: ${YELLOW}${PHASE}${NC}"
echo -e "🎫 票据: ${YELLOW}$(grep '^ticket:' "${WORKFLOW_DIR}/ACTIVE" | cut -d' ' -f2)${NC}"
echo -e "⏰ 开始: ${YELLOW}$(grep '^started_at:' "${WORKFLOW_DIR}/ACTIVE" | cut -d' ' -f2-)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 记录到日志
log "Session started: branch=$CURRENT_BRANCH, worktree=$WORKTREE_PATH"

# 检查Claude CLI是否安装
if ! command -v claude >/dev/null 2>&1; then
    error "Claude Code CLI未安装。请先安装: npm install -g @anthropic-ai/claude-cli"
    exit 1
fi

# 切换到worktree并启动Claude
echo -e "${BLUE}正在启动Claude Code...${NC}"
cd "$WORKTREE_PATH"

# 设置环境变量标记
export CE_WORKFLOW_ACTIVE=1
export CE_BRANCH="${CURRENT_BRANCH}"
export CE_PHASE="${PHASE}"

# 启动Claude Code CLI
exec claude "$@"