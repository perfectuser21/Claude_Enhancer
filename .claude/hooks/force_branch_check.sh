#!/bin/bash
# Claude Enhancer - PrePrompt强制分支检查（规则0：Phase -1）
# 版本：1.0
# 创建日期：2025-10-15
# 目的：在AI思考之前注入强制警告，确保100%遵守Phase -1分支检查

# ============================================
# 这是PrePrompt Hook - 在AI开始思考之前运行
# 功能：
# 1. 检测当前分支
# 2. 如果在main/master，注入强制警告到AI上下文
# 3. 强制AI创建新分支后才能继续
# ============================================

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 记录激活
echo "$(date +'%F %T') [force_branch_check.sh v1.0] PrePrompt triggered" >> "$LOG_FILE"

# 获取当前分支
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# 如果不在git仓库，跳过
if [[ -z "$current_branch" ]]; then
    exit 0
fi

# ============================================
# 核心逻辑：检测main/master分支
# ============================================

if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
    # 检测到主分支 - 注入强制警告到AI上下文

    cat <<'EOF' >&2

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ⚠️ ⚠️ ⚠️  CRITICAL: 你正在 MAIN/MASTER 分支上！ ⚠️ ⚠️ ⚠️             ║
║                                                                           ║
║  🔴 规则0（Phase -1）强制要求：新任务 = 新分支                          ║
║                                                                           ║
║  ❌ 你**禁止**在main/master分支上执行任何Write/Edit操作                 ║
║                                                                           ║
║  ✅ 你**必须**先执行以下命令创建新分支：                                ║
║                                                                           ║
║     git checkout -b feature/任务描述                                     ║
║                                                                           ║
║  📋 分支命名规范：                                                       ║
║     • feature/xxx  - 新功能开发                                         ║
║     • bugfix/xxx   - Bug修复                                            ║
║     • perf/xxx     - 性能优化                                           ║
║     • docs/xxx     - 文档更新                                           ║
║     • experiment/xxx - 实验性改动                                       ║
║                                                                           ║
║  💡 这是100%强制规则，不是建议！                                        ║
║     违反将导致Hook硬阻止（exit 1）                                      ║
║                                                                           ║
║  🎯 正确流程：                                                           ║
║     Phase -1: 创建分支 ← 你在这里（必须先完成）                        ║
║     Phase  0: 探索发现                                                  ║
║     Phase  1: 规划架构                                                  ║
║     Phase  2: 编码实现                                                  ║
║     Phase  3: 测试验证                                                  ║
║     Phase  4: 代码审查                                                  ║
║     Phase  5: 发布监控                                                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF

    echo "$(date +'%F %T') [force_branch_check.sh v1.0] WARNING: AI on $current_branch, warning injected" >> "$LOG_FILE"

    # PrePrompt hook不应该阻止（exit 0），而是注入警告
    # 实际阻止由PreToolUse hook (branch_helper.sh) 完成
    exit 0
else
    # 在feature分支上 - 静默通过
    echo "$(date +'%F %T') [force_branch_check.sh v1.0] PASSED: on branch $current_branch" >> "$LOG_FILE"
    exit 0
fi
