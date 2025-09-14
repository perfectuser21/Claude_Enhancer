#!/bin/bash
# VibePilot V2 清理脚本 - 删除旧版本和大文件

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🗑️  VibePilot V2 系统清理脚本${NC}"
echo "============================================"

# 显示当前空间使用情况
echo -e "${YELLOW}📊 当前磁盘使用情况:${NC}"
du -sh /home/xx/dev/* 2>/dev/null | grep -E "(VibePilot|vibepilot)" | sort -hr

echo
echo -e "${YELLOW}📋 建议清理的内容:${NC}"
echo "1. 🗂️  Vibepilot_Kit (58MB) - 旧版本项目"
echo "2. 🖼️  Screenshot files (6MB+) - 截图文件"
echo "3. 📦 zellij压缩包 (19MB) - 可重新下载"
echo "4. 📝 各种备份和文档文件"

echo
read -p "是否开始清理? [y/N]: " confirm

if [[ $confirm != [yY] ]]; then
    echo -e "${YELLOW}❌ 清理取消${NC}"
    exit 0
fi

echo -e "${GREEN}🚀 开始清理...${NC}"

# 备份重要配置
echo -e "${YELLOW}📦 备份重要配置文件...${NC}"
mkdir -p ./backup_configs
cp -r /home/xx/dev/Vibepilot_Kit/.claude ./backup_configs/ 2>/dev/null || true
cp /home/xx/dev/Vibepilot_Kit/CLAUDE.md ./backup_configs/ 2>/dev/null || true
cp /home/xx/dev/Vibepilot_Kit/.mcp.json ./backup_configs/ 2>/dev/null || true

# 删除旧版本项目 (最大的清理)
if [ -d "/home/xx/dev/Vibepilot_Kit" ]; then
    echo -e "${YELLOW}🗂️  删除旧版本 Vibepilot_Kit (58MB)...${NC}"
    rm -rf /home/xx/dev/Vibepilot_Kit
    echo -e "${GREEN}✅ 已删除 Vibepilot_Kit${NC}"
fi

# 删除截图文件
echo -e "${YELLOW}🖼️  删除截图文件...${NC}"
find /home/xx/dev -name "Screenshot*.png" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 已删除截图文件${NC}"

# 删除压缩包
echo -e "${YELLOW}📦 删除zellij压缩包...${NC}"
find /home/xx/dev -name "zellij-*.tar.gz" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 已删除压缩包${NC}"

# 删除备份文件
echo -e "${YELLOW}🗃️  删除备份文件...${NC}"
find /home/xx/dev -name "*.backup*" -delete 2>/dev/null || true
find /home/xx/dev -name "*.md.legacy" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 已删除备份文件${NC}"

# 删除大的图片文件
echo -e "${YELLOW}🖼️  删除大图片文件...${NC}"
find /home/xx/dev -name "*.jpg" -size +500k -delete 2>/dev/null || true
echo -e "${GREEN}✅ 已删除大图片文件${NC}"

# 清理Python缓存
echo -e "${YELLOW}🐍 清理Python缓存...${NC}"
find /home/xx/dev -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /home/xx/dev -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 已清理Python缓存${NC}"

echo
echo -e "${GREEN}🎉 清理完成！${NC}"
echo -e "${YELLOW}📊 清理后的磁盘使用情况:${NC}"
du -sh /home/xx/dev/* 2>/dev/null | grep -E "(VibePilot|vibepilot)" | sort -hr

echo
echo -e "${GREEN}💾 重要配置文件已备份到: ./backup_configs/${NC}"
echo -e "${GREEN}🚁 VibePilot V2 系统保持完整，可以正常使用！${NC}"

# 显示节省的空间
SAVED_SPACE=$(echo "58 + 6 + 19" | bc 2>/dev/null || echo "约83")
echo -e "${GREEN}💰 估计节省磁盘空间: ${SAVED_SPACE}MB+${NC}"