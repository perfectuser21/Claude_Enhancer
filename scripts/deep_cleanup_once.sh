#!/bin/bash
# Deep Cleanup Script (One-Time Use)
# 用途：清理100+个历史垃圾文件（backup, old, timestamped files）
# 运行一次后释放~50MB空间

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

cd "$CE_HOME"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Deep Cleanup - One-Time Historical Garbage Removal      ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 备份目录
BACKUP_DIR=".cleanup_backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}备份目录: $BACKUP_DIR${NC}"
echo -e "${YELLOW}如果清理有问题，可以从这里恢复${NC}"
echo ""

CLEANED_COUNT=0
FREED_SPACE=0

# =============================================================================
# 1. Timestamped Backup Files (43个文件)
# =============================================================================
echo -e "${CYAN}[1/7] 清理Timestamped Backup文件...${NC}"

FILES_TO_CLEAN=(
  "CLAUDE.md.backup.1761196057"
  "CLAUDE.md.backup.1761196073"
  "CLAUDE.md.backup.1761565817"
  "CLAUDE.md.backup.1761569922"
  "CLAUDE.md.backup.1761881385"
  "README.md.backup.1761196057"
  "README.md.backup.1761196073"
  "README.md.backup.1761565817"
  "README.md.backup.1761569922"
  "README.md.backup.1761881385"
  "package.json.backup.1761196057"
  "package.json.backup.1761196073"
  "package.json.backup.1761565817"
  "package.json.backup.1761569922"
  "package.json.backup.1761881385"
  ".workflow/manifest.yml.backup.1761196057"
  ".workflow/manifest.yml.backup.1761196073"
  ".workflow/manifest.yml.backup.1761569922"
  ".workflow/manifest.yml.backup.1761881385"
  ".workflow/manifest.yml.backup.1761565817"
  ".workflow/STAGES.yml.backup.20251029_102704"
  ".workflow/executor.sh.backup"
  ".claude/settings.json.backup"
  ".claude/settings.json.backup.1761196057"
  ".claude/settings.json.backup.1761196073"
  ".claude/settings.json.backup.1761565817"
  ".claude/settings.json.backup.1761569922"
  ".claude/settings.json.backup.1761881385"
  ".claude/memory-cache.json.backup"
  ".phase/current.backup"
  ".phase/phase1_confirmed.backup"
)

for file in "${FILES_TO_CLEAN[@]}"; do
  if [[ -f "$file" ]]; then
    # 备份
    mkdir -p "$BACKUP_DIR/$(dirname "$file")"
    cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true

    # 计算大小
    SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
    FREED_SPACE=$((FREED_SPACE + SIZE))

    # 删除
    rm -f "$file"
    echo -e "  ${GREEN}✓${NC} 已删除: $file"
    ((CLEANED_COUNT++))
  fi
done

# =============================================================================
# 2. 通用模式清理
# =============================================================================
echo ""
echo -e "${CYAN}[2/7] 清理通用Backup模式文件...${NC}"

# 查找并清理 *.backup.* 文件
find . -type f -name "*.backup.*" ! -path "./.cleanup_backup/*" ! -path "./.git/*" -print0 2>/dev/null | while IFS= read -r -d '' file; do
  # 备份
  mkdir -p "$BACKUP_DIR/$(dirname "$file")"
  cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true

  # 删除
  rm -f "$file"
  echo -e "  ${GREEN}✓${NC} 已删除: $file"
  ((CLEANED_COUNT++))
done

# =============================================================================
# 3. Stale Test Results
# =============================================================================
echo ""
echo -e "${CYAN}[3/7] 清理Stale Test Results...${NC}"

if [[ -d "test-results" ]]; then
  # 备份
  mkdir -p "$BACKUP_DIR/test-results"
  cp -r test-results/* "$BACKUP_DIR/test-results/" 2>/dev/null || true

  # 删除旧的test results（保留最近3个）
  find test-results -type f -name "*.xml" -o -name "*.json" -o -name "*.md" | sort -r | tail -n +4 | while read -r file; do
    rm -f "$file"
    echo -e "  ${GREEN}✓${NC} 已删除: $file"
    ((CLEANED_COUNT++))
  done
fi

# =============================================================================
# 4. Phase-Prefixed Steps (已废弃)
# =============================================================================
echo ""
echo -e "${CYAN}[4/7] 清理Phase-Prefixed废弃步骤...${NC}"

DEPRECATED_STEPS=(
  ".workflow/steps/step_05_phase1"
  ".workflow/steps/step_06_phase2"
  ".workflow/steps/step_07_phase3"
  ".workflow/steps/step_08_phase4"
  ".workflow/steps/step_09_phase5"
)

for step in "${DEPRECATED_STEPS[@]}"; do
  if [[ -f "$step" ]]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$step")"
    cp "$step" "$BACKUP_DIR/$step" 2>/dev/null || true
    rm -f "$step"
    echo -e "  ${GREEN}✓${NC} 已删除: $step"
    ((CLEANED_COUNT++))
  fi
done

# =============================================================================
# 5. Backup Directories
# =============================================================================
echo ""
echo -e "${CYAN}[5/7] 清理Backup目录...${NC}"

BACKUP_DIRS=(
  ".chaos_backup"
  ".learning_backup"
  ".performance_backup"
)

for dir in "${BACKUP_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    # 备份
    mkdir -p "$BACKUP_DIR"
    cp -r "$dir" "$BACKUP_DIR/" 2>/dev/null || true

    # 删除
    rm -rf "$dir"
    echo -e "  ${GREEN}✓${NC} 已删除: $dir"
    ((CLEANED_COUNT++))
  fi
done

# =============================================================================
# 6. Old Versioned Files
# =============================================================================
echo ""
echo -e "${CYAN}[6/7] 清理Old/Versioned文件...${NC}"

# 清理 *_old*, *.old, *_v[0-9]* 文件
find . -type f \( -name "*_old*" -o -name "*.old" -o -name "*_v[0-9]*" \) ! -path "./.cleanup_backup/*" ! -path "./.git/*" -print0 2>/dev/null | while IFS= read -r -d '' file; do
  mkdir -p "$BACKUP_DIR/$(dirname "$file")"
  cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
  rm -f "$file"
  echo -e "  ${GREEN}✓${NC} 已删除: $file"
  ((CLEANED_COUNT++))
done

# =============================================================================
# 7. Timestamped Documents
# =============================================================================
echo ""
echo -e "${CYAN}[7/7] 清理Timestamped Documents...${NC}"

find . -type f -regex ".*_[0-9]{8}_[0-9]{6}.*\\.md" ! -path "./.cleanup_backup/*" ! -path "./.git/*" -print0 2>/dev/null | while IFS= read -r -d '' file; do
  mkdir -p "$BACKUP_DIR/$(dirname "$file")"
  cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
  rm -f "$file"
  echo -e "  ${GREEN}✓${NC} 已删除: $file"
  ((CLEANED_COUNT++))
done

# =============================================================================
# 清理完成
# =============================================================================
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  清理完成                                                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}清理文件数量:${NC} $CLEANED_COUNT 个"
if [[ $FREED_SPACE -gt 0 ]]; then
  echo -e "${GREEN}释放空间:${NC} ~$((FREED_SPACE / 1024 / 1024))MB"
fi
echo -e "${GREEN}备份位置:${NC} $BACKUP_DIR"
echo ""

# 验证根目录文档数量
ROOT_DOCS=$(find . -maxdepth 1 -name "*.md" | wc -l)
echo -e "${CYAN}验证结果:${NC}"
echo -e "  根目录文档数量: $ROOT_DOCS (应该≤7)"

if [[ $ROOT_DOCS -le 7 ]]; then
  echo -e "  ${GREEN}✓${NC} 根目录文档数量符合规范"
else
  echo -e "  ${YELLOW}⚠${NC}  根目录文档仍然过多，需要手动检查"
fi

echo ""
echo -e "${YELLOW}💡 如果需要恢复，运行:${NC}"
echo -e "   cp -r $BACKUP_DIR/* ./"
echo ""
echo -e "${GREEN}✅ Deep cleanup完成！${NC}"
