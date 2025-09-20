#!/bin/bash
# Task Type Detector
# 识别任务类型并推荐Agent组合

set -e

# 读取输入
INPUT=$(cat)

# 如果不是Task调用，直接通过
if ! echo "$INPUT" | grep -q '"name"\s*:\s*"Task"'; then
    echo "$INPUT"
    exit 0
fi

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]')

# 检测任务类型并给出建议
detect_and_suggest() {
    local desc="$1"

    # 认证相关
    if echo "$desc" | grep -qiE "登录|认证|auth|用户|权限|jwt|oauth|session|password"; then
        echo "🔍 检测到认证任务" >&2
        echo "   推荐使用: backend-architect, security-auditor, test-engineer, api-designer, database-specialist (5个Agent)" >&2
        return
    fi

    # API开发
    if echo "$desc" | grep -qiE "api|接口|rest|graphql|endpoint|route|swagger"; then
        echo "🔍 检测到API开发任务" >&2
        echo "   推荐使用: api-designer, backend-architect, test-engineer, technical-writer (4个Agent)" >&2
        return
    fi

    # 数据库
    if echo "$desc" | grep -qiE "数据库|database|schema|sql|mongodb|redis|表结构|migration"; then
        echo "🔍 检测到数据库任务" >&2
        echo "   推荐使用: database-specialist, backend-architect, performance-engineer (3个Agent)" >&2
        return
    fi

    # 前端开发
    if echo "$desc" | grep -qiE "前端|frontend|react|vue|ui|组件|页面|component|界面"; then
        echo "🔍 检测到前端任务" >&2
        echo "   推荐使用: frontend-specialist, ux-designer, test-engineer (3个Agent)" >&2
        return
    fi

    # 测试
    if echo "$desc" | grep -qiE "测试|test|spec|jest|mocha|pytest|unit|e2e|integration"; then
        echo "🔍 检测到测试任务" >&2
        echo "   推荐使用: test-engineer, e2e-test-specialist, performance-tester (3个Agent)" >&2
        return
    fi
}

# 执行检测（输出到stderr，不影响正常流程）
if [ -n "$TASK_DESC" ]; then
    detect_and_suggest "$TASK_DESC"
fi

# 输出原始内容
echo "$INPUT"