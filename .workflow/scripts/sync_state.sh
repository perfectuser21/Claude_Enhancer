#!/bin/bash
# sync_state.sh - 状态同步检查脚本
# Purpose: 修复CE-ISSUE-003 - 确保.phase/current与.workflow/ACTIVE一致
# Version: 1.0.0
# Created: 2025-10-09

set -euo pipefail

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# 路径定义
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly CURRENT_FILE="${PROJECT_ROOT}/.phase/current"
readonly ACTIVE_FILE="${PROJECT_ROOT}/.workflow/ACTIVE"

# ==================== 主逻辑 ====================

main() {
    echo -e "${CYAN}[SYNC_STATE] 开始状态同步检查...${NC}"

    # 1. 读取.phase/current
    if [[ ! -f "$CURRENT_FILE" ]]; then
        echo -e "${RED}❌ ERROR: .phase/current 不存在${NC}"
        echo "  路径: $CURRENT_FILE"
        echo "  建议: 初始化工作流 - echo 'P1' > $CURRENT_FILE"
        exit 1
    fi

    CURRENT_PHASE=$(cat "$CURRENT_FILE" 2>/dev/null | tr -d '[:space:]' || echo "MISSING")
    echo -e "${CYAN}  .phase/current: ${NC}$CURRENT_PHASE"

    # 2. 读取.workflow/ACTIVE中的phase字段
    if [[ ! -f "$ACTIVE_FILE" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: .workflow/ACTIVE 不存在${NC}"
        echo "  当前phase: $CURRENT_PHASE"
        echo "  状态: 无活跃工作流"
        echo ""
        echo "建议:"
        echo "  - 如果需要开始工作流，运行: bash .workflow/executor.sh"
        echo "  - 或手动创建ACTIVE文件"
        exit 0
    fi

    # 使用Python解析YAML（因为yq未安装）
    ACTIVE_PHASE=$(python3 << 'EOF'
import yaml
import sys

try:
    with open('.workflow/ACTIVE', 'r') as f:
        data = yaml.safe_load(f)
        if data and 'phase' in data:
            print(data['phase'].strip())
        else:
            print("MISSING")
except Exception as e:
    print("MISSING", file=sys.stderr)
    sys.exit(1)
EOF
)

    if [[ $? -ne 0 || "$ACTIVE_PHASE" == "MISSING" ]]; then
        echo -e "${RED}❌ ERROR: 无法解析.workflow/ACTIVE中的phase字段${NC}"
        echo "  请确保ACTIVE文件包含有效的YAML格式和phase字段"
        exit 1
    fi

    echo -e "${CYAN}  .workflow/ACTIVE: ${NC}$ACTIVE_PHASE"

    # 3. 检查一致性
    if [[ "$CURRENT_PHASE" != "$ACTIVE_PHASE" ]]; then
        echo ""
        echo -e "${RED}❌ ERROR: 状态不一致检测到！${NC}"
        echo ""
        echo "  .phase/current:   $CURRENT_PHASE"
        echo "  .workflow/ACTIVE: $ACTIVE_PHASE"
        echo ""
        echo -e "${YELLOW}这通常表示：${NC}"
        echo "  1. 工作流执行被中断"
        echo "  2. 手动修改了某个状态文件"
        echo "  3. 系统异常导致状态不同步"
        echo ""
        echo -e "${CYAN}修复方案：${NC}"
        echo ""
        echo "  选项1: 同步ACTIVE到current（更新ACTIVE文件）"
        echo "    echo '$CURRENT_PHASE' | python3 -c \"import yaml, sys; data=yaml.safe_load(open('.workflow/ACTIVE')); data['phase']='$CURRENT_PHASE'; yaml.dump(data, open('.workflow/ACTIVE', 'w'))\""
        echo ""
        echo "  选项2: 同步current到ACTIVE（更新current文件）"
        echo "    echo '$ACTIVE_PHASE' > $CURRENT_FILE"
        echo ""
        echo "  选项3: 清理ACTIVE文件（如果工作流已完成）"
        echo "    rm .workflow/ACTIVE"
        echo ""
        echo "  选项4: 手动检查并决定哪个是正确状态"
        echo "    - 查看git log确认最后的phase"
        echo "    - 查看.gates/目录中的签名文件"
        echo ""
        exit 1
    fi

    echo -e "${GREEN}✅ 状态一致性检查通过${NC}"

    # 4. 检查24h过期
    if [[ -f "$ACTIVE_FILE" ]]; then
        ACTIVE_TIME=$(stat -c '%Y' "$ACTIVE_FILE" 2>/dev/null || stat -f '%m' "$ACTIVE_FILE" 2>/dev/null || echo "0")
        NOW=$(date +%s)
        AGE=$((NOW - ACTIVE_TIME))
        HOURS=$((AGE / 3600))

        echo ""
        echo -e "${CYAN}[过期检查]${NC}"
        echo "  ACTIVE文件年龄: ${HOURS}小时"

        if [[ $HOURS -gt 24 ]]; then
            echo -e "${YELLOW}⚠️  WARNING: .workflow/ACTIVE已过期 ${HOURS}小时${NC}"
            echo ""
            echo "建议:"
            echo "  - 如果工作流仍在进行，考虑更新ACTIVE文件时间戳: touch .workflow/ACTIVE"
            echo "  - 如果工作流已完成，清理ACTIVE文件: rm .workflow/ACTIVE"
            echo "  - 如果需要重新启动工作流，运行: bash .workflow/executor.sh"
        else
            echo -e "${GREEN}✅ ACTIVE文件未过期（< 24小时）${NC}"
        fi
    fi

    # 5. 如果当前是DONE，建议清理ACTIVE
    echo ""
    echo -e "${CYAN}[完成状态检查]${NC}"
    if [[ "$CURRENT_PHASE" == "DONE" ]]; then
        echo -e "${GREEN}✅ 工作流已完成 (DONE)${NC}"
        echo ""
        echo "建议:"
        echo "  1. 清理ACTIVE文件: rm .workflow/ACTIVE"
        echo "  2. 或开始新工作流: bash .workflow/executor.sh"
        echo "  3. 查看完成的gates: ls -la .gates/"
    else
        echo "  当前phase: $CURRENT_PHASE（工作流进行中）"
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}状态检查完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 执行主函数
main "$@"
