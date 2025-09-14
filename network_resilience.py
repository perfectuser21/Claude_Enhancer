#!/usr/bin/env python3
"""
VibePilot 网络韧性系统
多重访问方案自动切换，彻底解决网络限制问题
"""

import subprocess
import time
import socket
import urllib.request
import json
import os

class NetworkResilience:
    def __init__(self):
        self.config = {
            "primary_ports": [9999, 8443, 3000, 8001],
            "backup_ports": [443, 80, 22],
            "domain_alternatives": [
                "146.190.52.84",
                # 可以添加CDN域名
            ],
            "tunnel_methods": [
                "ssh_tunnel",
                "nginx_proxy",
                "port_forwarding"
            ]
        }

    def setup_multi_port_services(self):
        """在多个端口同时运行VibePilot服务"""
        services = []

        # 端口8443 - 常用的HTTPS备用端口
        services.append({
            "port": 8443,
            "command": self._get_vibepilot_command(8443),
            "description": "HTTPS备用端口"
        })

        # 端口2083 - Cloudflare常用端口
        services.append({
            "port": 2083,
            "command": self._get_vibepilot_command(2083),
            "description": "CDN兼容端口"
        })

        # 端口8080 - HTTP备用端口
        services.append({
            "port": 8080,
            "command": self._get_vibepilot_command(8080),
            "description": "HTTP备用端口"
        })

        return services

    def _get_vibepilot_command(self, port):
        """生成VibePilot启动命令"""
        return f"""python3 -c "
from features.ai_butler.api import AIButlerAPI
import uvicorn

api = AIButlerAPI()
print('🚁 VibePilot V2 多端口服务 - 端口{port}')
uvicorn.run(api.app, host='0.0.0.0', port={port}, log_level='info')
" """

    def setup_nginx_multi_proxy(self):
        """配置nginx多端口反向代理"""
        nginx_config = """
# 443端口 - 主要HTTPS入口
server {
    listen 443 ssl http2;
    server_name 146.190.52.84;

    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:9999;
        include /etc/nginx/proxy_params;
    }
}

# 8443端口 - 备用HTTPS
server {
    listen 8443 ssl http2;
    server_name 146.190.52.84;

    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    location / {
        proxy_pass http://127.0.0.1:9999;
        include /etc/nginx/proxy_params;
    }
}

# 2083端口 - CDN端口
server {
    listen 2083 ssl;
    server_name 146.190.52.84;

    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    location / {
        proxy_pass http://127.0.0.1:9999;
        include /etc/nginx/proxy_params;
    }
}
"""
        return nginx_config

    def setup_port_disguise(self):
        """端口伪装 - 让VibePilot看起来像常见服务"""
        # 让9999端口看起来像MySQL
        disguise_rules = [
            "iptables -t nat -A OUTPUT -p tcp --dport 3306 -j REDIRECT --to-port 9999",
            "iptables -t nat -A PREROUTING -p tcp --dport 3306 -j REDIRECT --to-port 9999"
        ]
        return disguise_rules

    def create_client_resilience_script(self):
        """为客户端创建智能连接脚本"""
        script = '''#!/bin/bash
# VibePilot 智能连接脚本 - 自动尝试多种方案

echo "🚁 VibePilot 智能连接系统启动"
echo "=================================="

# 连接方案列表
declare -a METHODS=(
    "https://146.190.52.84:443"
    "https://146.190.52.84:8443"
    "https://146.190.52.84:2083"
    "http://146.190.52.84:8080"
    "ssh_tunnel_8888"
    "ssh_tunnel_9000"
    "ssh_tunnel_7777"
)

# 测试直连方案
test_direct_connection() {
    local url=$1
    echo "测试: $url"

    if curl -k -s --connect-timeout 5 --max-time 10 "$url/health" >/dev/null 2>&1; then
        echo "✅ 直连成功: $url"
        open "$url" 2>/dev/null || echo "请在浏览器打开: $url"
        return 0
    else
        echo "❌ 直连失败: $url"
        return 1
    fi
}

# SSH隧道方案
setup_ssh_tunnel() {
    local local_port=$1
    echo "建立SSH隧道到本地端口: $local_port"

    # 检查端口是否被占用
    if lsof -i :$local_port >/dev/null 2>&1; then
        echo "端口 $local_port 被占用，跳过"
        return 1
    fi

    # 建立隧道
    ssh -f -N -i ~/.ssh/DigitalOcean/XX_VPS_2025 -L $local_port:localhost:9999 root@146.190.52.84 2>/dev/null

    sleep 2

    # 测试隧道
    if curl -s --connect-timeout 3 http://localhost:$local_port/health >/dev/null 2>&1; then
        echo "✅ SSH隧道成功: localhost:$local_port"
        open "http://localhost:$local_port" 2>/dev/null
        return 0
    else
        echo "❌ SSH隧道失败: $local_port"
        return 1
    fi
}

# 主连接逻辑
main() {
    for method in "${METHODS[@]}"; do
        echo "\\n尝试方案: $method"

        if [[ $method == ssh_tunnel_* ]]; then
            local_port=${method#ssh_tunnel_}
            if setup_ssh_tunnel $local_port; then
                echo "🎉 连接成功!"
                exit 0
            fi
        else
            if test_direct_connection $method; then
                echo "🎉 连接成功!"
                exit 0
            fi
        fi

        sleep 1
    done

    echo "❌ 所有连接方案都失败了"
    echo "💡 建议:"
    echo "1. 检查网络连接"
    echo "2. 尝试切换网络环境(手机热点)"
    echo "3. 联系管理员"
}

# 清理旧的隧道
echo "清理旧的SSH隧道..."
pkill -f "ssh.*localhost:.*root@146.190.52.84" 2>/dev/null

main
'''
        return script

def main():
    resilience = NetworkResilience()

    print("🛡️ 设置VibePilot网络韧性系统...")

    # 1. 设置nginx多端口代理
    nginx_config = resilience.setup_nginx_multi_proxy()
    print("📝 生成nginx多端口配置")

    # 2. 生成客户端智能连接脚本
    client_script = resilience.create_client_resilience_script()
    print("🔧 生成客户端智能连接脚本")

    # 保存客户端脚本
    with open("/tmp/vibepilot_smart_connect.sh", "w") as f:
        f.write(client_script)

    print("✅ 网络韧性系统配置完成!")
    print("📥 客户端脚本已保存到: /tmp/vibepilot_smart_connect.sh")

if __name__ == "__main__":
    main()