#!/bin/bash

# Perfect21开发环境快速启动脚本

set -e

echo "🚀 Perfect21开发服务器启动中..."

# 检查Python版本
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "📋 Python版本: $python_version"

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p data logs cache temp uploads

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "⚡ 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt

# 设置环境变量
export ENV=development
export JWT_SECRET_KEY="dev-secret-key-change-in-production"
export PYTHONPATH=$(pwd)

# 运行数据库迁移
echo "🗄️  初始化数据库..."
python3 scripts/start_api.py --create-admin

# 显示系统信息
echo "📊 系统信息:"
python3 scripts/start_api.py --info

# 启动开发服务器
echo "🌐 启动开发服务器..."
echo "📚 API文档地址: http://127.0.0.1:8000/docs"
echo "🔍 健康检查: http://127.0.0.1:8000/health"
echo "🔐 认证端点: http://127.0.0.1:8000/api/auth"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

# 启动服务器
python3 scripts/start_api.py --reload --debug --log-level DEBUG

deactivate