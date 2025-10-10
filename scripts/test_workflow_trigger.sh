#!/bin/bash
# 测试工作流自动启动功能

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🧪 Claude Enhancer 工作流触发测试"
echo "================================================"
echo

# 测试函数
test_trigger() {
    local test_name="$1"
    local prompt="$2"
    local expected_trigger="$3"

    echo -e "${BLUE}测试: $test_name${NC}"
    echo "输入: $prompt"

    # 调用hook
    result=$(.claude/hooks/workflow_auto_start.sh "$prompt" 2>&1 || true)

    if [[ "$expected_trigger" == "YES" ]]; then
        if echo "$result" | grep -q "执行模式启动"; then
            echo -e "${GREEN}✅ 通过 - 正确触发工作流${NC}"
        else
            echo -e "${RED}❌ 失败 - 应该触发但未触发${NC}"
            echo "输出: $result"
        fi
    else
        if echo "$result" | grep -q "执行模式启动"; then
            echo -e "${RED}❌ 失败 - 不应触发但触发了${NC}"
            echo "输出: $result"
        else
            echo -e "${GREEN}✅ 通过 - 正确保持讨论模式${NC}"
        fi
    fi

    echo
}

# 测试套件
echo "== 1. 触发词测试 =="
echo

test_trigger "触发词1" "现在开始实现用户登录功能" "YES"
test_trigger "触发词2" "现在开始执行数据库迁移" "YES"
test_trigger "触发词3" "开始工作流，创建API接口" "YES"
test_trigger "触发词4" "let's implement the auth system" "YES"
test_trigger "触发词5" "let's start building the dashboard" "YES"

echo "== 2. 非触发词测试（应保持讨论模式） =="
echo

test_trigger "讨论1" "这个功能应该怎么实现？" "NO"
test_trigger "讨论2" "分析一下代码结构" "NO"
test_trigger "讨论3" "帮我理解这个bug" "NO"
test_trigger "讨论4" "what should we do here?" "NO"

echo "================================================"
echo -e "${GREEN}测试完成！${NC}"
echo

# 检查当前状态
echo "📊 当前状态："
echo "  分支: $(git rev-parse --abbrev-ref HEAD)"
echo "  Phase: $(cat .phase/current 2>/dev/null || echo 'N/A')"
echo "  Active: $(grep phase .workflow/ACTIVE 2>/dev/null || echo 'N/A')"
