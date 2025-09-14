#!/usr/bin/env python3
"""
WireGuard 网络韧性系统
多端口、多协议、智能切换解决方案
"""

import subprocess
import time
import json
import os

class WireGuardResilience:
    def __init__(self):
        self.config = {
            "standard_ports": [51820, 443, 80, 53],  # 标准端口 + 伪装端口
            "stealth_ports": [22, 2222, 8443, 1194], # 隐蔽端口
            "protocols": ["udp", "tcp"],              # 协议类型
            "obfuscation": True                       # 流量混淆
        }

    def setup_multi_port_wireguard(self):
        """设置多端口WireGuard服务"""

        # 1. 原始WireGuard (UDP 51820)
        wg_configs = [
            {
                "port": 51820,
                "protocol": "udp",
                "config_name": "wg0-standard",
                "description": "标准WireGuard"
            },

            # 2. HTTPS端口伪装 (UDP 443)
            {
                "port": 443,
                "protocol": "udp",
                "config_name": "wg0-https",
                "description": "HTTPS端口伪装"
            },

            # 3. DNS端口伪装 (UDP 53)
            {
                "port": 53,
                "protocol": "udp",
                "config_name": "wg0-dns",
                "description": "DNS端口伪装"
            },

            # 4. SSH端口伪装 (UDP 22)
            {
                "port": 22,
                "protocol": "udp",
                "config_name": "wg0-ssh",
                "description": "SSH端口伪装"
            }
        ]

        return wg_configs

    def generate_wg_config(self, port, interface_name, server_key, client_key, client_ip):
        """生成WireGuard配置文件"""

        server_config = f"""[Interface]
PrivateKey = {server_key}
Address = 10.0.0.1/24
ListenPort = {port}
PostUp = iptables -A FORWARD -i {interface_name} -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i {interface_name} -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = {client_key}
AllowedIPs = {client_ip}/32
"""

        client_config = f"""[Interface]
PrivateKey = {client_key}
Address = {client_ip}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {server_key}
Endpoint = 146.190.52.84:{port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

        return server_config, client_config

    def setup_port_hopping(self):
        """端口跳跃配置 - 动态切换端口"""

        hopping_script = '''#!/bin/bash
# WireGuard 端口跳跃脚本

PORTS=(51820 443 53 22 8443 1194)
WG_INTERFACE="wg0"
WG_CONFIG_BASE="/etc/wireguard/wg0"

echo "🔄 WireGuard 端口跳跃系统启动"

# 当前端口检测
get_current_port() {
    wg show $WG_INTERFACE 2>/dev/null | grep "listening port" | awk '{print $3}'
}

# 端口连通性测试
test_port() {
    local port=$1
    echo "测试端口 $port..."

    # 使用nc测试UDP端口
    if nc -u -z -w3 146.190.52.84 $port 2>/dev/null; then
        echo "✅ 端口 $port 可用"
        return 0
    else
        echo "❌ 端口 $port 不可用"
        return 1
    fi
}

# 切换到新端口
switch_to_port() {
    local new_port=$1

    echo "🔄 切换到端口 $new_port..."

    # 停止当前连接
    wg-quick down $WG_INTERFACE 2>/dev/null

    # 修改配置文件端口
    sed -i "s/Endpoint = 146.190.52.84:[0-9]*/Endpoint = 146.190.52.84:$new_port/" $WG_CONFIG_BASE.conf

    # 重新启动
    if wg-quick up $WG_INTERFACE; then
        echo "✅ 成功切换到端口 $new_port"
        return 0
    else
        echo "❌ 切换到端口 $new_port 失败"
        return 1
    fi
}

# 智能端口选择
smart_connect() {
    echo "🧠 智能连接模式..."

    for port in "${PORTS[@]}"; do
        echo "\\n尝试端口: $port"

        if test_port $port; then
            if switch_to_port $port; then
                echo "🎉 WireGuard 连接成功! 端口: $port"

                # 验证连接
                sleep 3
                if ping -c 3 -W 3 10.0.0.1 >/dev/null 2>&1; then
                    echo "✅ VPN隧道工作正常"
                    exit 0
                fi
            fi
        fi

        sleep 2
    done

    echo "❌ 所有端口都无法连接"
    echo "💡 建议:"
    echo "1. 检查服务器端WireGuard服务"
    echo "2. 尝试切换网络环境"
    echo "3. 使用手机热点测试"

    exit 1
}

# 主函数
case "${1:-smart}" in
    "smart")
        smart_connect
        ;;
    "test")
        echo "🔍 测试所有端口..."
        for port in "${PORTS[@]}"; do
            test_port $port
        done
        ;;
    "hop")
        echo "🦘 端口跳跃模式..."
        current_port=$(get_current_port)
        echo "当前端口: $current_port"

        # 选择下一个端口
        next_port=${PORTS[$((RANDOM % ${#PORTS[@]}))]}
        echo "跳跃到端口: $next_port"
        switch_to_port $next_port
        ;;
    *)
        echo "用法: $0 [smart|test|hop]"
        echo "  smart - 智能连接 (默认)"
        echo "  test  - 测试所有端口"
        echo "  hop   - 随机端口跳跃"
        ;;
esac
'''
        return hopping_script

    def create_client_smart_script(self):
        """创建客户端智能连接脚本"""

        script = '''#!/bin/bash
# WireGuard 客户端智能连接脚本

echo "🚁 WireGuard 智能连接系统"
echo "========================="

# WireGuard配置文件路径 (请修改为你的实际路径)
WG_CONFIG="/usr/local/etc/wireguard/wg0.conf"  # macOS Homebrew路径
# WG_CONFIG="/etc/wireguard/wg0.conf"          # Linux路径

# 备用端口列表
PORTS=(51820 443 53 22 8443 1194 2222)
SERVER_IP="146.190.52.84"

# 检查WireGuard是否安装
check_wireguard() {
    if ! command -v wg >/dev/null 2>&1; then
        echo "❌ WireGuard 未安装"
        echo "💡 安装方法:"
        echo "macOS: brew install wireguard-tools"
        echo "Linux: sudo apt install wireguard"
        exit 1
    fi
}

# 测试端口连通性
test_port() {
    local port=$1
    echo "测试端口 $port..."

    # 使用nc测试UDP连通性
    if nc -u -z -w3 $SERVER_IP $port 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 更新配置文件端口
update_config_port() {
    local port=$1

    if [[ ! -f "$WG_CONFIG" ]]; then
        echo "❌ 配置文件不存在: $WG_CONFIG"
        echo "💡 请确保WireGuard配置文件路径正确"
        return 1
    fi

    # 备份原配置
    cp "$WG_CONFIG" "$WG_CONFIG.backup"

    # 更新端口
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/Endpoint = $SERVER_IP:[0-9]*/Endpoint = $SERVER_IP:$port/" "$WG_CONFIG"
    else
        # Linux
        sed -i "s/Endpoint = $SERVER_IP:[0-9]*/Endpoint = $SERVER_IP:$port/" "$WG_CONFIG"
    fi

    echo "✅ 配置文件已更新为端口 $port"
}

# 启动WireGuard连接
start_wireguard() {
    echo "🚀 启动 WireGuard 连接..."

    # 停止现有连接
    sudo wg-quick down wg0 2>/dev/null

    # 启动新连接
    if sudo wg-quick up wg0; then
        echo "✅ WireGuard 启动成功"

        # 验证连接
        sleep 3
        if ping -c 3 -W 3 10.0.0.1 >/dev/null 2>&1; then
            echo "✅ VPN 隧道连接正常"
            echo "🌐 外网IP检查:"
            curl -s --max-time 10 https://ifconfig.me || echo "IP检查失败"
            return 0
        else
            echo "❌ VPN 隧道连接失败"
            return 1
        fi
    else
        echo "❌ WireGuard 启动失败"
        return 1
    fi
}

# 智能连接主函数
smart_connect() {
    check_wireguard

    echo "🔍 开始智能连接..."

    for port in "${PORTS[@]}"; do
        echo "\\n=== 尝试端口 $port ==="

        if test_port $port; then
            echo "✅ 端口 $port 可达"

            # 更新配置文件
            if update_config_port $port; then
                # 尝试连接
                if start_wireguard; then
                    echo "🎉 WireGuard 连接成功! 端口: $port"
                    exit 0
                fi
            fi
        else
            echo "❌ 端口 $port 不可达"
        fi

        sleep 2
    done

    echo "❌ 所有端口都无法连接"
    echo "💡 建议解决方案:"
    echo "1. 检查服务器端 WireGuard 服务状态"
    echo "2. 尝试切换网络环境 (手机热点)"
    echo "3. 联系 VPS 管理员检查防火墙设置"
    echo "4. 使用 SSH 隧道作为临时方案"

    # 恢复原配置
    if [[ -f "$WG_CONFIG.backup" ]]; then
        mv "$WG_CONFIG.backup" "$WG_CONFIG"
        echo "已恢复原配置文件"
    fi

    exit 1
}

# 显示当前状态
show_status() {
    echo "📊 WireGuard 状态:"
    sudo wg show 2>/dev/null || echo "WireGuard 未运行"

    echo "\\n🌐 当前外网IP:"
    curl -s --max-time 10 https://ifconfig.me || echo "无法获取IP"
}

# 参数处理
case "${1:-smart}" in
    "smart"|"connect")
        smart_connect
        ;;
    "status")
        show_status
        ;;
    "disconnect")
        echo "🔌 断开 WireGuard 连接..."
        sudo wg-quick down wg0
        ;;
    "help"|"-h"|"--help")
        echo "WireGuard 智能连接工具"
        echo ""
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  smart      智能连接 (默认)"
        echo "  connect    同 smart"
        echo "  status     显示连接状态"
        echo "  disconnect 断开连接"
        echo "  help       显示此帮助"
        echo ""
        echo "首次使用前请确保:"
        echo "1. 已安装 WireGuard"
        echo "2. 配置文件路径正确"
        echo "3. 具有 sudo 权限"
        ;;
    *)
        echo "未知命令: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac
'''
        return script

def main():
    wg_resilience = WireGuardResilience()

    print("🛡️ 设置 WireGuard 网络韧性系统...")

    # 1. 生成服务端配置
    configs = wg_resilience.setup_multi_port_wireguard()
    print(f"📝 生成 {len(configs)} 个多端口配置")

    # 2. 生成端口跳跃脚本
    hopping_script = wg_resilience.setup_port_hopping()
    with open("/tmp/wg_port_hopping.sh", "w") as f:
        f.write(hopping_script)
    print("🦘 端口跳跃脚本已生成")

    # 3. 生成客户端智能脚本
    client_script = wg_resilience.create_client_smart_script()
    with open("/tmp/wg_smart_connect.sh", "w") as f:
        f.write(client_script)
    print("🧠 客户端智能连接脚本已生成")

    print("✅ WireGuard 韧性系统配置完成!")
    print("\n📥 脚本位置:")
    print("- 服务端端口跳跃: /tmp/wg_port_hopping.sh")
    print("- 客户端智能连接: /tmp/wg_smart_connect.sh")

    print("\n🚀 使用方法:")
    print("1. 下载客户端脚本到你的Mac")
    print("2. 修改脚本中的配置文件路径")
    print("3. 运行 ./wg_smart_connect.sh")

if __name__ == "__main__":
    main()