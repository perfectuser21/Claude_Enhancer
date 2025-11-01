#!/bin/bash
# Bypass Permissions Verification Script
# 用途：验证bypass permissions配置是否正确
# 检查项：settings.json配置、全局gates、Task工具权限

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Bypass Permissions Configuration Verification           ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

ISSUES=0

# =============================================================================
# 1. 检查.claude/settings.json
# =============================================================================
echo -e "${CYAN}[1/4] 检查.claude/settings.json配置...${NC}"

SETTINGS_FILE=".claude/settings.json"
if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo -e "  ${RED}✗${NC} $SETTINGS_FILE 不存在"
  ((ISSUES++))
else
  # 检查defaultMode
  if grep -q '"defaultMode".*:.*"bypassPermissions"' "$SETTINGS_FILE"; then
    echo -e "  ${GREEN}✓${NC} defaultMode设置为bypassPermissions"
  else
    echo -e "  ${RED}✗${NC} defaultMode未设置或设置错误"
    echo -e "     应该是: \"defaultMode\": \"bypassPermissions\""
    ((ISSUES++))
  fi

  # 检查Task工具是否在allow列表
  if grep -q '"Task"' "$SETTINGS_FILE"; then
    echo -e "  ${GREEN}✓${NC} Task工具已在allow列表"
  else
    echo -e "  ${RED}✗${NC} Task工具不在allow列表"
    echo -e "     需要添加: \"Task\""
    ((ISSUES++))
  fi

  # 检查其他关键工具
  REQUIRED_TOOLS=("Bash" "Read" "Write" "Edit" "Glob" "Grep" "TodoWrite")
  for tool in "${REQUIRED_TOOLS[@]}"; do
    if grep -q "\"$tool\"" "$SETTINGS_FILE"; then
      echo -e "  ${GREEN}✓${NC} $tool工具已配置"
    else
      echo -e "  ${YELLOW}⚠${NC}  $tool工具未配置（可选）"
    fi
  done
fi

# =============================================================================
# 2. 检查全局配置文件~/.claude.json
# =============================================================================
echo ""
echo -e "${CYAN}[2/4] 检查~/.claude.json全局配置...${NC}"

GLOBAL_CONFIG="$HOME/.claude.json"
if [[ ! -f "$GLOBAL_CONFIG" ]]; then
  echo -e "  ${YELLOW}⚠${NC}  ~/.claude.json 不存在（可选文件）"
else
  # 检查bypass permissions gate
  if grep -q '"tengu_disable_bypass_permissions_mode"' "$GLOBAL_CONFIG"; then
    GATE_VALUE=$(grep -oP '"tengu_disable_bypass_permissions_mode"\s*:\s*\K(true|false)' "$GLOBAL_CONFIG" || echo "unknown")

    if [[ "$GATE_VALUE" == "false" ]]; then
      echo -e "  ${GREEN}✓${NC} Bypass permissions mode已启用（gate=false）"
    elif [[ "$GATE_VALUE" == "true" ]]; then
      echo -e "  ${RED}✗${NC} Bypass permissions mode已禁用（gate=true）"
      echo -e "     需要设置: \"tengu_disable_bypass_permissions_mode\": false"
      ((ISSUES++))
    else
      echo -e "  ${YELLOW}⚠${NC}  无法读取gate值"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC}  未找到bypass permissions gate配置（可选）"
  fi
fi

# =============================================================================
# 3. 检查settings.json结构完整性
# =============================================================================
echo ""
echo -e "${CYAN}[3/4] 检查settings.json结构完整性...${NC}"

if [[ -f "$SETTINGS_FILE" ]]; then
  # 检查JSON是否有效
  if jq empty "$SETTINGS_FILE" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} JSON格式有效"

    # 检查permissions结构
    if jq -e '.permissions' "$SETTINGS_FILE" > /dev/null 2>&1; then
      echo -e "  ${GREEN}✓${NC} permissions字段存在"

      # 检查allow数组
      if jq -e '.permissions.allow' "$SETTINGS_FILE" > /dev/null 2>&1; then
        ALLOW_COUNT=$(jq '.permissions.allow | length' "$SETTINGS_FILE")
        echo -e "  ${GREEN}✓${NC} allow列表存在（$ALLOW_COUNT项）"
      else
        echo -e "  ${RED}✗${NC} allow列表不存在"
        ((ISSUES++))
      fi
    else
      echo -e "  ${RED}✗${NC} permissions字段不存在"
      ((ISSUES++))
    fi
  else
    echo -e "  ${RED}✗${NC} JSON格式无效"
    ((ISSUES++))
  fi
fi

# =============================================================================
# 4. 生成诊断报告
# =============================================================================
echo ""
echo -e "${CYAN}[4/4] 生成诊断报告...${NC}"

REPORT_FILE=".workflow/bypass_permissions_diagnostic.txt"
{
  echo "Bypass Permissions Diagnostic Report"
  echo "Generated: $(date -Iseconds)"
  echo "========================================"
  echo ""
  echo "1. Settings File: $SETTINGS_FILE"
  if [[ -f "$SETTINGS_FILE" ]]; then
    echo "   - Exists: YES"
    echo "   - defaultMode: $(grep -oP '"defaultMode"\s*:\s*"\K[^"]+' "$SETTINGS_FILE" || echo "NOT FOUND")"
    echo "   - Task in allow: $(grep -q '"Task"' "$SETTINGS_FILE" && echo "YES" || echo "NO")"
    echo "   - Bash in allow: $(grep -q '"Bash"' "$SETTINGS_FILE" && echo "YES" || echo "NO")"
  else
    echo "   - Exists: NO"
  fi
  echo ""
  echo "2. Global Config: $GLOBAL_CONFIG"
  if [[ -f "$GLOBAL_CONFIG" ]]; then
    echo "   - Exists: YES"
    echo "   - Gate value: $(grep -oP '"tengu_disable_bypass_permissions_mode"\s*:\s*\K(true|false)' "$GLOBAL_CONFIG" || echo "NOT FOUND")"
  else
    echo "   - Exists: NO"
  fi
  echo ""
  echo "3. Issues Found: $ISSUES"
  echo ""
  echo "4. Recommendations:"
  if [[ $ISSUES -eq 0 ]]; then
    echo "   - ✓ Configuration looks good!"
  else
    echo "   - Review the issues above and fix them"
    echo "   - Restart Claude Code after making changes"
  fi
} > "$REPORT_FILE"

echo -e "  ${GREEN}✓${NC} 诊断报告已生成: $REPORT_FILE"

# =============================================================================
# 总结
# =============================================================================
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  验证完成                                                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [[ $ISSUES -eq 0 ]]; then
  echo -e "${GREEN}✅ 所有检查通过！Bypass permissions配置正确。${NC}"
  echo ""
  echo -e "${CYAN}配置要点：${NC}"
  echo -e "  1. ✓ defaultMode = bypassPermissions"
  echo -e "  2. ✓ Task工具在allow列表"
  echo -e "  3. ✓ JSON格式有效"
  echo ""
  exit 0
else
  echo -e "${RED}❌ 发现 $ISSUES 个问题${NC}"
  echo ""
  echo -e "${YELLOW}修复建议：${NC}"
  echo -e "  1. 检查.claude/settings.json配置"
  echo -e "  2. 确保defaultMode设置为bypassPermissions"
  echo -e "  3. 确保Task、Bash、Read、Write等工具在allow列表"
  echo -e "  4. 重启Claude Code使配置生效"
  echo ""
  echo -e "${CYAN}详细报告：${NC} $REPORT_FILE"
  echo ""
  exit 1
fi
