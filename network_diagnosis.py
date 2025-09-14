#!/usr/bin/env python3
"""
网络诊断工具
检测客户端到VibePilot服务器的连接问题
"""

import socket
import requests
import subprocess
import sys
import time
from urllib.parse import urlparse

def test_dns_resolution(hostname):
    """测试DNS解析"""
    print(f"🔍 测试DNS解析: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS解析成功: {hostname} -> {ip}")
        return ip
    except socket.gaierror as e:
        print(f"❌ DNS解析失败: {e}")
        return None

def test_ping(ip, count=3):
    """测试ping连通性"""
    print(f"🏓 测试ping连通性: {ip}")
    try:
        if sys.platform.startswith('win'):
            cmd = ['ping', '-n', str(count), ip]
        else:
            cmd = ['ping', '-c', str(count), ip]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print(f"✅ Ping成功")
            # 提取ping时间
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line.lower() or 'ms' in line.lower():
                    print(f"   📊 {line.strip()}")
        else:
            print(f"❌ Ping失败: {result.stderr}")

    except subprocess.TimeoutExpired:
        print(f"❌ Ping超时")
    except Exception as e:
        print(f"❌ Ping错误: {e}")

def test_port_connection(ip, port):
    """测试端口连接"""
    print(f"🔌 测试端口连接: {ip}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            print(f"✅ 端口{port}连接成功")
            return True
        else:
            print(f"❌ 端口{port}连接失败 (错误码: {result})")
            return False
    except Exception as e:
        print(f"❌ 端口连接错误: {e}")
        return False

def test_http_request(url):
    """测试HTTP请求"""
    print(f"🌐 测试HTTP请求: {url}")
    try:
        # 设置多种User-Agent和Headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # 先测试HEAD请求
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"✅ HEAD请求成功: HTTP {response.status_code}")

        # 再测试GET请求
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ GET请求成功: HTTP {response.status_code}")
        print(f"   📊 响应大小: {len(response.content)} bytes")
        print(f"   📊 响应时间: {response.elapsed.total_seconds():.3f}s")

        # 检查响应头
        print(f"   📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   📋 Server: {response.headers.get('Server', 'N/A')}")

        return True

    except requests.exceptions.ConnectTimeout:
        print(f"❌ HTTP连接超时")
    except requests.exceptions.ReadTimeout:
        print(f"❌ HTTP读取超时")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTP连接错误: {e}")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误: {e}")
    except Exception as e:
        print(f"❌ HTTP请求错误: {e}")

    return False

def test_proxy_settings():
    """检测代理设置"""
    print(f"🔍 检测代理设置")

    # 检查环境变量
    import os
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']

    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   📋 发现代理设置: {var}={value}")

    # 检查系统代理
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler()
        print(f"   📋 系统代理处理器: {proxy_handler.proxies}")
    except Exception as e:
        print(f"   ⚠️ 无法检测系统代理: {e}")

def test_firewall_and_security():
    """检测防火墙和安全软件"""
    print(f"🛡️ 检测防火墙和安全设置")

    # 检测Windows防火墙
    if sys.platform.startswith('win'):
        try:
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'],
                                  capture_output=True, text=True, timeout=5)
            if 'State' in result.stdout:
                print(f"   📋 Windows防火墙状态检测完成")
                for line in result.stdout.split('\n'):
                    if 'State' in line:
                        print(f"   📋 {line.strip()}")
        except Exception:
            print(f"   ⚠️ 无法检测Windows防火墙状态")

    # 检测常见端口是否被阻止
    common_ports = [80, 443, 8080, 8000, 3000]
    print(f"   🔍 测试常见端口连接...")
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('www.google.com', port))
            sock.close()
            status = "开放" if result == 0 else "阻止"
            print(f"   📋 端口{port}: {status}")
        except Exception:
            print(f"   📋 端口{port}: 无法测试")

def main():
    """主诊断函数"""
    print("🚀 VibePilot网络连接诊断工具")
    print("=" * 60)

    # 目标服务器信息
    servers = [
        "http://146.190.52.84:8001",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ]

    for server_url in servers:
        print(f"\n🎯 诊断目标: {server_url}")
        print("-" * 40)

        parsed = urlparse(server_url)
        hostname = parsed.hostname
        port = parsed.port or 80

        # 1. DNS解析测试
        if hostname != 'localhost' and hostname != '127.0.0.1':
            ip = test_dns_resolution(hostname)
            if not ip:
                print(f"⏭️ 跳过{server_url}的后续测试\n")
                continue
        else:
            ip = hostname
            print(f"🔍 本地地址: {ip}")

        # 2. Ping测试
        if ip != 'localhost':
            test_ping(ip)

        # 3. 端口连接测试
        test_port_connection(ip, port)

        # 4. HTTP请求测试
        test_http_request(server_url)

        print()

    # 5. 系统网络环境检测
    print("🔧 系统网络环境诊断")
    print("-" * 40)
    test_proxy_settings()
    test_firewall_and_security()

    # 6. 网络接口信息
    print(f"\n📡 本地网络接口信息")
    print("-" * 40)
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   📋 主机名: {hostname}")
        print(f"   📋 本地IP: {local_ip}")

        # 获取所有网络接口
        addrs = socket.getaddrinfo(hostname, None)
        unique_ips = set()
        for addr in addrs:
            unique_ips.add(addr[4][0])

        for ip in unique_ips:
            print(f"   📋 网络接口: {ip}")

    except Exception as e:
        print(f"   ⚠️ 无法获取网络接口信息: {e}")

    # 7. 诊断总结和建议
    print(f"\n💡 诊断建议")
    print("-" * 40)
    print("如果以上测试失败，可能的解决方案:")
    print("1. 🔥 检查本地防火墙设置")
    print("2. 🌐 检查路由器/网关设置")
    print("3. 🔒 检查企业网络策略")
    print("4. 🔧 尝试不同的网络环境（手机热点）")
    print("5. 🌍 检查ISP是否阻止特定端口")
    print("6. 🦠 检查安全软件/杀毒软件设置")
    print("7. 📱 使用VPN或代理服务器")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 诊断被用户中断")
    except Exception as e:
        print(f"\n❌ 诊断工具错误: {e}")
        import traceback
        traceback.print_exc()