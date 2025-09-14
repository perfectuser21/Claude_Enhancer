#!/usr/bin/env python3
"""
客户端网络连接测试工具
帮助诊断从本地Mac到VPS的连接问题
"""

import socket
import subprocess
import time
import json
import sys
from urllib.parse import urlparse

def test_basic_connectivity():
    """基础连接测试"""
    print("🔍 基础网络连接测试")
    print("="*50)

    tests = [
        ("Google DNS", "8.8.8.8", 53),
        ("VPS SSH", "146.190.52.84", 22),
        ("VPS HTTP", "146.190.52.84", 80),
        ("VPS VibePilot", "146.190.52.84", 9999),
    ]

    results = {}

    for name, host, port in tests:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            start_time = time.time()
            result = sock.connect_ex((host, port))
            connect_time = (time.time() - start_time) * 1000
            sock.close()

            if result == 0:
                print(f"✅ {name}: 连接成功 ({connect_time:.1f}ms)")
                results[name] = {"status": "success", "time": connect_time}
            else:
                print(f"❌ {name}: 连接失败 (错误码: {result})")
                results[name] = {"status": "failed", "error": result}

        except Exception as e:
            print(f"❌ {name}: 异常 - {e}")
            results[name] = {"status": "error", "error": str(e)}

    return results

def test_http_requests():
    """HTTP请求测试"""
    print("\n🌐 HTTP请求测试")
    print("="*50)

    import urllib.request
    import urllib.error

    urls = [
        ("Google", "http://www.google.com"),
        ("VPS 80端口", "http://146.190.52.84"),
        ("VPS 9999端口", "http://146.190.52.84:9999"),
        ("VPS 健康检查", "http://146.190.52.84:9999/health"),
    ]

    results = {}

    for name, url in urls:
        try:
            start_time = time.time()
            req = urllib.request.Request(url, headers={'User-Agent': 'VibePilot-Test/1.0'})
            response = urllib.request.urlopen(req, timeout=10)
            response_time = (time.time() - start_time) * 1000
            content = response.read()

            print(f"✅ {name}: HTTP {response.status} ({response_time:.1f}ms, {len(content)} bytes)")
            results[name] = {
                "status": "success",
                "code": response.status,
                "time": response_time,
                "size": len(content)
            }

        except urllib.error.HTTPError as e:
            print(f"⚠️ {name}: HTTP {e.code} - {e.reason}")
            results[name] = {"status": "http_error", "code": e.code, "reason": e.reason}

        except urllib.error.URLError as e:
            print(f"❌ {name}: URL错误 - {e.reason}")
            results[name] = {"status": "url_error", "reason": str(e.reason)}

        except Exception as e:
            print(f"❌ {name}: 异常 - {e}")
            results[name] = {"status": "error", "error": str(e)}

    return results

def test_dns_resolution():
    """DNS解析测试"""
    print("\n🔍 DNS解析测试")
    print("="*50)

    domains = [
        "google.com",
        "146.190.52.84",  # 这个是IP，测试反向解析
    ]

    results = {}

    for domain in domains:
        try:
            start_time = time.time()
            if domain == "146.190.52.84":
                # 测试IP可达性
                result = socket.gethostbyname(domain)
                print(f"✅ IP {domain}: 可达 -> {result}")
            else:
                result = socket.gethostbyname(domain)
                resolve_time = (time.time() - start_time) * 1000
                print(f"✅ {domain}: 解析成功 -> {result} ({resolve_time:.1f}ms)")

            results[domain] = {"status": "success", "ip": result}

        except Exception as e:
            print(f"❌ {domain}: 解析失败 - {e}")
            results[domain] = {"status": "failed", "error": str(e)}

    return results

def test_local_network():
    """本地网络环境测试"""
    print("\n📡 本地网络环境")
    print("="*50)

    try:
        # 获取本地IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"📋 主机名: {hostname}")
        print(f"📋 本地IP: {local_ip}")

        # 检查网络接口
        try:
            import subprocess
            if sys.platform == "darwin":  # macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                interfaces = []
                current_interface = None

                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t') and not line.startswith(' '):
                        current_interface = line.split(':')[0]
                    elif 'inet ' in line and current_interface:
                        ip = line.split('inet ')[1].split(' ')[0]
                        if ip != '127.0.0.1':
                            interfaces.append(f"{current_interface}: {ip}")

                print(f"📋 网络接口:")
                for interface in interfaces:
                    print(f"   - {interface}")

        except Exception as e:
            print(f"⚠️ 无法获取网络接口信息: {e}")

    except Exception as e:
        print(f"❌ 本地网络检查失败: {e}")

def generate_diagnostics_script():
    """生成给用户的诊断脚本"""
    script_content = '''#!/usr/bin/env python3
"""
VibePilot客户端连接诊断工具
请在你的Mac上运行此脚本
"""

import socket
import urllib.request
import time
import sys

def test_vibepilot_connection():
    print("🚁 VibePilot连接测试")
    print("="*40)

    # 1. 基础连接测试
    print("\\n1. 测试端口连接...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('146.190.52.84', 9999))
        sock.close()

        if result == 0:
            print("✅ 端口9999连接成功")
        else:
            print(f"❌ 端口9999连接失败 (错误: {result})")
            print("可能原因:")
            print("  - 防火墙阻止连接")
            print("  - 网络运营商限制")
            print("  - VPN或代理问题")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

    # 2. HTTP测试
    print("\\n2. 测试HTTP访问...")
    try:
        req = urllib.request.Request(
            'http://146.190.52.84:9999/health',
            headers={'User-Agent': 'VibePilot-Test/1.0'}
        )
        start_time = time.time()
        response = urllib.request.urlopen(req, timeout=15)
        response_time = (time.time() - start_time) * 1000
        content = response.read().decode('utf-8')

        print(f"✅ HTTP访问成功 ({response_time:.1f}ms)")
        print(f"📋 响应: {content}")

    except Exception as e:
        print(f"❌ HTTP访问失败: {e}")

        # 建议解决方案
        print("\\n💡 建议解决方案:")
        print("1. 检查你的防火墙设置")
        print("2. 尝试关闭VPN/代理")
        print("3. 尝试使用手机热点")
        print("4. 使用SSH隧道:")
        print("   ssh -L 9999:localhost:9999 root@146.190.52.84")
        print("   然后访问: http://localhost:9999")

if __name__ == "__main__":
    test_vibepilot_connection()
'''

    return script_content

def main():
    """主测试函数"""
    print("🚁 VibePilot客户端网络诊断工具")
    print("🌍 从服务器端测试到客户端的连通性")
    print("="*60)

    # 执行所有测试
    connectivity_results = test_basic_connectivity()
    http_results = test_http_requests()
    dns_results = test_dns_resolution()
    test_local_network()

    # 生成总结报告
    print("\n📊 诊断总结")
    print("="*50)

    total_tests = len(connectivity_results) + len(http_results) + len(dns_results)
    passed_tests = 0

    for results in [connectivity_results, http_results, dns_results]:
        for test, result in results.items():
            if result.get("status") == "success":
                passed_tests += 1

    print(f"📈 测试通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")

    # 检查关键服务
    vibepilot_working = (
        http_results.get("VPS 9999端口", {}).get("status") == "success" or
        http_results.get("VPS 健康检查", {}).get("status") == "success"
    )

    if vibepilot_working:
        print("✅ VibePilot服务正常运行")
        print("\\n🎯 如果你仍无法访问，问题在客户端网络:")
    else:
        print("❌ VibePilot服务可能有问题")

    print("\\n💡 客户端诊断脚本已生成...")

    # 保存客户端诊断脚本
    script = generate_diagnostics_script()
    script_path = "/tmp/client_test.py"

    with open(script_path, 'w') as f:
        f.write(script)

    print(f"📝 客户端测试脚本: {script_path}")
    print("\\n🔧 请在你的Mac上运行以下命令:")
    print(f"curl -s http://146.190.52.84:8002 | head -20")
    print("或者:")
    print("python3 <(curl -s http://146.190.52.84:8002)")

    # 启动简单HTTP服务器提供脚本下载
    try:
        import http.server
        import socketserver
        import threading
        import os

        os.chdir('/tmp')

        class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

        def start_server():
            with socketserver.TCPServer(("0.0.0.0", 8002), QuietHTTPRequestHandler) as httpd:
                httpd.serve_forever()

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        print(f"\\n🌐 临时下载服务启动: http://146.190.52.84:8002/client_test.py")

    except Exception as e:
        print(f"⚠️ 无法启动下载服务: {e}")

if __name__ == "__main__":
    main()