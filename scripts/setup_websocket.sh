#!/bin/bash

# WebSocket实时通信系统安装脚本
# 用于设置WebSocket所需的依赖和配置

set -e

echo "🚀 正在设置WebSocket实时通信系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "✅ Python3环境检查通过"

# 检查Node.js环境（用于前端）
if ! command -v node &> /dev/null; then
    echo "⚠️  警告: 未找到Node.js，前端WebSocket功能可能无法使用"
else
    echo "✅ Node.js环境检查通过"
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装Python依赖
echo "📚 安装Python依赖..."
pip install --upgrade pip

# 安装WebSocket相关依赖
pip install websockets

# 安装其他可能需要的依赖
pip install asyncio-mqtt 2>/dev/null || echo "⚠️  asyncio-mqtt安装失败（可选依赖）"

echo "✅ Python依赖安装完成"

# 检查前端依赖
if [ -f "frontend/package.json" ]; then
    echo "📦 检查前端依赖..."
    cd frontend

    # 检查是否有package-lock.json或yarn.lock
    if [ -f "package-lock.json" ]; then
        echo "🔄 使用npm安装前端依赖..."
        npm install
    elif [ -f "yarn.lock" ]; then
        echo "🔄 使用yarn安装前端依赖..."
        yarn install
    else
        echo "🔄 使用npm安装前端依赖..."
        npm install
    fi

    cd ..
    echo "✅ 前端依赖安装完成"
else
    echo "⚠️  未找到frontend/package.json，跳过前端依赖安装"
fi

# 创建配置文件
echo "⚙️  创建配置文件..."

# 创建WebSocket配置文件
cat > config/websocket.conf << 'EOF'
# WebSocket服务器配置
[server]
host = 0.0.0.0
port = 8765
debug = false

[security]
enable_auth = true
allowed_origins = *

[performance]
max_connections = 1000
heartbeat_interval = 30
cleanup_interval = 60
EOF

# 创建环境变量文件
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# WebSocket配置
WS_HOST=localhost
WS_PORT=8765
WS_DEBUG=false

# 前端配置
REACT_APP_WS_URL=ws://localhost:8765
EOF
    echo "✅ 创建.env配置文件"
else
    echo "⚠️  .env文件已存在，请手动添加WebSocket配置"
fi

# 创建启动脚本
echo "📝 创建启动脚本..."

cat > scripts/start_websocket.sh << 'EOF'
#!/bin/bash
# WebSocket服务器启动脚本

# 激活虚拟环境
source venv/bin/activate

# 启动WebSocket服务器
echo "🚀 启动WebSocket服务器..."
python src/websocket/server.py --host ${WS_HOST:-0.0.0.0} --port ${WS_PORT:-8765} ${WS_DEBUG:+--debug}
EOF

chmod +x scripts/start_websocket.sh

cat > scripts/test_websocket.sh << 'EOF'
#!/bin/bash
# WebSocket连接测试脚本

echo "🧪 测试WebSocket连接..."

# 使用Python测试WebSocket连接
python3 << 'PYTHON'
import asyncio
import websockets
import json
import sys

async def test_connection():
    uri = "ws://localhost:8765?user_id=test_user&username=Test%20User"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")

            # 发送测试消息
            test_message = {
                "type": "heartbeat",
                "data": {"test": True},
                "timestamp": "2024-01-01T12:00:00Z",
                "message_id": "test_msg_001"
            }

            await websocket.send(json.dumps(test_message))
            print("✅ 测试消息发送成功")

            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"✅ 收到响应: {response[:100]}...")

            return True

    except websockets.exceptions.ConnectionRefused:
        print("❌ 连接被拒绝 - WebSocket服务器可能未启动")
        return False
    except asyncio.TimeoutError:
        print("❌ 连接超时")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
PYTHON
EOF

chmod +x scripts/test_websocket.sh

echo "✅ 启动脚本创建完成"

# 创建systemd服务文件（可选）
if command -v systemctl &> /dev/null; then
    echo "🔧 创建systemd服务文件..."

    cat > claude-enhancer-websocket.service << EOF
[Unit]
Description=Claude Enhancer WebSocket Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python $(pwd)/src/websocket/server.py --host 0.0.0.0 --port 8765
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    echo "📋 systemd服务文件已创建: claude-enhancer-websocket.service"
    echo "   安装命令: sudo cp claude-enhancer-websocket.service /etc/systemd/system/"
    echo "   启动命令: sudo systemctl enable claude-enhancer-websocket && sudo systemctl start claude-enhancer-websocket"
fi

# 验证安装
echo "🔍 验证安装..."

# 检查Python模块
python3 -c "import websockets; print('✅ websockets模块可用')" 2>/dev/null || echo "❌ websockets模块不可用"

# 检查文件结构
required_files=(
    "src/websocket/__init__.py"
    "src/websocket/manager.py"
    "src/websocket/handlers.py"
    "src/websocket/events.py"
    "src/websocket/server.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
    fi
done

echo ""
echo "🎉 WebSocket实时通信系统安装完成！"
echo ""
echo "📋 下一步操作："
echo "   1. 启动WebSocket服务器: ./scripts/start_websocket.sh"
echo "   2. 测试连接: ./scripts/test_websocket.sh"
echo "   3. 查看使用指南: docs/WEBSOCKET_GUIDE.md"
echo ""
echo "🔧 配置文件位置:"
echo "   - 主配置: config/websocket.conf"
echo "   - 环境变量: .env"
echo ""
echo "📖 更多信息请查看: docs/WEBSOCKET_GUIDE.md"

# 取消虚拟环境激活
deactivate 2>/dev/null || true

echo "✨ 安装脚本执行完成！"