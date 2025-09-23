#!/bin/bash

# =============================================================================
# 执行 Claude Enhancer 品牌统一
# =============================================================================

set -e

cd /home/xx/dev/Perfect21

echo "🚀 开始执行 Claude Enhancer 品牌统一..."

# 给脚本执行权限
chmod +x brand_unification_simple.sh

# 执行品牌统一脚本
echo "y" | ./brand_unification_simple.sh

echo "✅ 品牌统一脚本执行完成"