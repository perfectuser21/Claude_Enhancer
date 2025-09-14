#!/bin/bash
# Perfect21 SSH隧道连接脚本

echo "🚇 建立Perfect21 SSH隧道到VPS..."

# 清理旧的SSH连接
echo "清理旧连接..."
pkill -f 'ssh.*146.190.52.84' 2>/dev/null || true

# 智能寻找可用端口
find_available_port() {
    for port in 7777 6666 8080 8888 9000 5555 4444; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done
    echo 7777  # 默认端口
}

LOCAL_PORT=$(find_available_port)

echo "使用本地端口: $LOCAL_PORT"
echo "建立隧道: localhost:$LOCAL_PORT -> VPS:9999"
echo "需要输入VPS root密码..."

# 建立SSH隧道
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -L $LOCAL_PORT:localhost:9999 root@146.190.52.84 -N &

SSH_PID=$!
echo "SSH进程ID: $SSH_PID"

# 等待连接建立
echo "等待连接建立(10秒)..."
sleep 10

# 测试连接
echo "测试隧道连接..."
if curl -s --connect-timeout 5 --max-time 10 http://localhost:$LOCAL_PORT >/dev/null 2>&1; then
    echo "✅ SSH隧道建立成功!"
    echo "🌐 访问地址: http://localhost:$LOCAL_PORT"

    # 自动打开浏览器
    echo "正在打开浏览器..."
    open "http://localhost:$LOCAL_PORT" 2>/dev/null &

    echo ""
    echo "🎉 连接成功！浏览器应该已经打开了"
    echo "💡 关闭隧道: kill $SSH_PID"
    echo "💡 或者运行: pkill -f 'ssh.*146.190.52.84'"
else
    echo "❌ 隧道测试失败，但SSH可能已连接"
    echo "💡 手动测试: curl http://localhost:$LOCAL_PORT"
    echo "💡 手动打开: open http://localhost:$LOCAL_PORT"
fi

echo ""
echo "隧道信息:"
echo "本地地址: http://localhost:$LOCAL_PORT"
echo "VPS地址: http://146.190.52.84:9999"
echo "SSH PID: $SSH_PID"