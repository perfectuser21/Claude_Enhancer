#!/bin/bash
# Claude Enhancer 综合清理脚本
# 用途: Phase 7 Closure阶段的完整清理
# 版本: 1.0
# 日期: 2025-10-27

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# 检测CE_HOME
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

cd "$CE_HOME"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Claude Enhancer 综合清理                                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 读取清理模式
CLEANUP_MODE="${1:-interactive}"

if [[ "$CLEANUP_MODE" == "interactive" ]]; then
  echo -e "${YELLOW}请选择清理方案:${NC}"
  echo "  1) 激进清理 - 删除所有过期内容 (推荐)"
  echo "  2) 保守清理 - 归档而不删除"
  echo "  3) 最小清理 - 只删除明确过期的"
  echo ""
  read -r -p "请选择 (1-3): " choice

  case $choice in
    1) CLEANUP_MODE="aggressive" ;;
    2) CLEANUP_MODE="conservative" ;;
    3) CLEANUP_MODE="minimal" ;;
    *) echo "无效选择，使用保守清理"; CLEANUP_MODE="conservative" ;;
  esac
fi

echo -e "${CYAN}清理模式: $CLEANUP_MODE${NC}"
echo ""

CLEANED_COUNT=0
FREED_SPACE=0

# =============================================================================
# 激进清理
# =============================================================================
if [[ "$CLEANUP_MODE" == "aggressive" ]]; then
  echo -e "${YELLOW}[激进清理模式]${NC}"
  echo ""

  # 1. 清空.temp
  echo "[1/8] 清空.temp目录..."
  if [[ -d .temp ]]; then
    TEMP_SIZE=$(du -sb .temp 2>/dev/null | cut -f1)
    rm -rf .temp/*
    mkdir -p .temp/analysis .temp/reports
    touch .temp/.gitkeep
    echo -e "  ${GREEN}✓${NC} 清理.temp/ (释放 $((TEMP_SIZE / 1024 / 1024))MB)"
    FREED_SPACE=$((FREED_SPACE + TEMP_SIZE))
  fi

  # 2. 删除旧版本文件
  echo "[2/8] 删除旧版本文件..."
  OLD_FILES=(
    "./GO_LIVE_v6.0.sh"
    "./docs/RELEASE_NOTES_v1.0.md"
    "./docs/API_REFERENCE_v1.0.md"
    "./test/test_dashboard_v2.sh"
  )
  for file in "${OLD_FILES[@]}"; do
    if [[ -f "$file" ]]; then
      rm -f "$file"
      echo -e "  ${GREEN}✓${NC} 删除 $file"
      ((CLEANED_COUNT++))
    fi
  done
  find ./test -name "test_dashboard_v2*.py" -delete 2>/dev/null || true

  # 3. 删除重复文档
  echo "[3/8] 删除重复文档..."
  DUPLICATE_DOCS=(
    "docs/PLAN_AUDIT_FIX.md"
    "docs/PLAN_STRESS_TEST.md"
    "docs/PLAN.md"
  )
  for doc in "${DUPLICATE_DOCS[@]}"; do
    if [[ -f "$doc" ]]; then
      rm -f "$doc"
      echo -e "  ${GREEN}✓${NC} 删除 $doc"
      ((CLEANED_COUNT++))
    fi
  done

  # 4. 清理归档目录
  echo "[4/8] 整合归档目录..."
  mkdir -p archive/{v6.0,hooks,workflow}

  if [[ -d .archive/old_versions ]]; then
    mv .archive/old_versions/* archive/v6.0/ 2>/dev/null || true
    rmdir .archive/old_versions .archive 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 整合 .archive/old_versions"
  fi

  if [[ -d .claude/hooks/archive.backup ]]; then
    mv .claude/hooks/archive.backup/* archive/hooks/ 2>/dev/null || true
    rmdir .claude/hooks/archive.backup 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 整合 .claude/hooks/archive.backup"
  fi

  if [[ -d .claude/hooks/archive ]]; then
    mv .claude/hooks/archive/* archive/hooks/ 2>/dev/null || true
    rmdir .claude/hooks/archive 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 整合 .claude/hooks/archive"
  fi

  # 5. 清理测试会话
  echo "[5/8] 清理测试会话数据..."
  rm -rf .workflow/cli/state/sessions/* 2>/dev/null || true
  rm -rf .claude/knowledge/sessions/* 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 清理会话数据"

  # 6. 删除过期配置
  echo "[6/8] 删除过期配置..."
  if [[ -f .workflow/gates.yml.backup_old_phases ]]; then
    rm -f .workflow/gates.yml.backup_old_phases
    echo -e "  ${GREEN}✓${NC} 删除 gates.yml.backup_old_phases"
    ((CLEANED_COUNT++))
  fi

  # 7. 清理大文件
  echo "[7/8] 清理大文件..."
  find ./test/reports -name "*.html" -mtime +7 -delete 2>/dev/null || true
  find .workflow/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 清理旧测试报告和日志"

  # 8. Git清理
  echo "[8/8] Git仓库清理..."
  git gc --quiet 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Git gc完成"

# =============================================================================
# 保守清理
# =============================================================================
elif [[ "$CLEANUP_MODE" == "conservative" ]]; then
  echo -e "${YELLOW}[保守清理模式]${NC}"
  echo ""

  # 1. 只清理.temp中7天以上的文件
  echo "[1/6] 清理.temp旧文件..."
  if [[ -d .temp ]]; then
    find .temp -type f -mtime +7 -delete 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 清理7天以上的文件"
  fi

  # 2. 归档旧版本文件
  echo "[2/6] 归档旧版本文件..."
  mkdir -p archive/v6.0
  [[ -f ./GO_LIVE_v6.0.sh ]] && mv ./GO_LIVE_v6.0.sh archive/v6.0/ && echo -e "  ${GREEN}✓${NC} 归档 GO_LIVE_v6.0.sh"
  [[ -f ./docs/TRUTH_v6.0.md ]] && mv ./docs/TRUTH_v6.0.md archive/v6.0/ && echo -e "  ${GREEN}✓${NC} 归档 TRUTH_v6.0.md"
  [[ -f ./core/hooks/enforcer_v2.sh ]] && mv ./core/hooks/enforcer_v2.sh archive/v6.0/ && echo -e "  ${GREEN}✓${NC} 归档 enforcer_v2.sh"

  # 3. 归档重复文档
  echo "[3/6] 归档重复文档..."
  mkdir -p archive/plans
  [[ -f docs/PLAN.md ]] && mv docs/PLAN.md archive/plans/ && echo -e "  ${GREEN}✓${NC} 归档 PLAN.md"
  [[ -f docs/PLAN_AUDIT_FIX.md ]] && mv docs/PLAN_AUDIT_FIX.md archive/plans/ && echo -e "  ${GREEN}✓${NC} 归档 PLAN_AUDIT_FIX.md"
  [[ -f docs/PLAN_STRESS_TEST.md ]] && mv docs/PLAN_STRESS_TEST.md archive/plans/ && echo -e "  ${GREEN}✓${NC} 归档 PLAN_STRESS_TEST.md"

  # 4. 整合归档目录
  echo "[4/6] 整合归档..."
  mkdir -p archive/hooks
  [[ -d .claude/hooks/archive.backup ]] && mv .claude/hooks/archive.backup/* archive/hooks/ 2>/dev/null && echo -e "  ${GREEN}✓${NC} 整合hooks备份"
  [[ -d .claude/hooks/archive ]] && mv .claude/hooks/archive/* archive/hooks/ 2>/dev/null && echo -e "  ${GREEN}✓${NC} 整合hooks归档"

  # 5. 清理旧日志
  echo "[5/6] 清理旧日志..."
  find .workflow/logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 清理30天以上的日志"

  # 6. 清理旧测试报告
  echo "[6/6] 清理旧测试报告..."
  find ./test/reports -name "*.html" -mtime +30 -delete 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} 清理30天以上的报告"

# =============================================================================
# 最小清理
# =============================================================================
elif [[ "$CLEANUP_MODE" == "minimal" ]]; then
  echo -e "${YELLOW}[最小清理模式]${NC}"
  echo ""

  # 1. 清理废弃工作
  echo "[1/3] 清理废弃工作..."
  if [[ -d .temp/orphaned_work ]]; then
    rm -rf .temp/orphaned_work
    echo -e "  ${GREEN}✓${NC} 删除 .temp/orphaned_work"
    ((CLEANED_COUNT++))
  fi

  # 2. 删除已完成计划
  echo "[2/3] 删除已完成计划..."
  [[ -f docs/PLAN_AUDIT_FIX.md ]] && rm -f docs/PLAN_AUDIT_FIX.md && echo -e "  ${GREEN}✓${NC} 删除 PLAN_AUDIT_FIX.md" && ((CLEANED_COUNT++))
  [[ -f docs/PLAN_STRESS_TEST.md ]] && rm -f docs/PLAN_STRESS_TEST.md && echo -e "  ${GREEN}✓${NC} 删除 PLAN_STRESS_TEST.md" && ((CLEANED_COUNT++))

  # 3. 删除过期配置
  echo "[3/3] 删除过期配置..."
  [[ -f .workflow/gates.yml.backup_old_phases ]] && rm -f .workflow/gates.yml.backup_old_phases && echo -e "  ${GREEN}✓${NC} 删除 gates.yml.backup_old_phases" && ((CLEANED_COUNT++))
fi

# =============================================================================
# 清理后验证
# =============================================================================
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  清理后验证                                               ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查根目录文档数量
ROOT_DOCS=$(find . -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l)
if [[ $ROOT_DOCS -le 7 ]]; then
  echo -e "${GREEN}✓${NC} 根目录文档: $ROOT_DOCS/7"
else
  echo -e "${RED}✗${NC} 根目录文档: $ROOT_DOCS/7 (超过限制!)"
fi

# 检查.temp大小
if [[ -d .temp ]]; then
  TEMP_SIZE=$(du -sh .temp 2>/dev/null | cut -f1)
  echo -e "${GREEN}✓${NC} .temp/大小: $TEMP_SIZE"
fi

# 检查Git状态
UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l)
if [[ $UNCOMMITTED -gt 0 ]]; then
  echo -e "${YELLOW}⚠${NC}  有 $UNCOMMITTED 个未提交的更改"
else
  echo -e "${GREEN}✓${NC} Git工作区干净"
fi

# Phase状态清理（Phase 7完成时执行）
echo ""
echo -e "${CYAN}[Phase状态清理]${NC}"

PHASE_STATE_FILES=(".phase/current" ".workflow/current" ".phase/completed" ".phase/phase1_confirmed" ".workflow/workflow_complete")
NEEDS_CLEANUP=false

# 检测清理条件
if [[ -f ".phase/current" ]]; then
  current_phase=$(cat .phase/current 2>/dev/null || echo "")
  [[ "${current_phase,,}" == "phase7" ]] && NEEDS_CLEANUP=true && echo -e "  ${GREEN}✓${NC} Phase 7完成"
else
  for file in "${PHASE_STATE_FILES[@]}"; do
    [[ -f "$file" ]] && NEEDS_CLEANUP=true && break
  done
fi

# 执行清理和验证
if [[ "$NEEDS_CLEANUP" == "true" ]]; then
  for file in "${PHASE_STATE_FILES[@]}"; do
    rm -f "$file" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 已删除: $file"
  done
  # 验证
  for file in "${PHASE_STATE_FILES[@]}"; do
    [[ -f "$file" ]] && echo -e "  ${RED}✗${NC} 验证失败: $file" && exit 1
  done
  echo -e "  ${GREEN}✓${NC} Phase状态完全清理（5/5文件）"
else
  echo -e "  ${CYAN}ℹ${NC}  无需清理"
fi

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  清理完成                                                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}清理模式:${NC} $CLEANUP_MODE"
echo -e "${GREEN}清理文件:${NC} ~$CLEANED_COUNT 个"
if [[ $FREED_SPACE -gt 0 ]]; then
  echo -e "${GREEN}释放空间:${NC} ~$((FREED_SPACE / 1024 / 1024))MB"
fi
echo ""

if [[ $UNCOMMITTED -gt 0 ]]; then
  echo -e "${YELLOW}下一步:${NC}"
  echo "  git add -A"
  echo "  git commit -m 'chore: comprehensive cleanup for v8.0'"
  echo ""
fi
