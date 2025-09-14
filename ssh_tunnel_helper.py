#!/usr/bin/env python3
"""
Perfect21 SSH隧道连接助手
解决SSH认证问题并建立隧道连接
"""

import subprocess
import time
import sys
import os

def test_ssh_connection():
    """测试SSH连接和认证"""
    print("🔍 测试SSH连接...")

    # 方法1: 测试基本SSH连接
    print("\n1. 测试SSH基本连接...")
    try:
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10',
            '-o', 'BatchMode=yes',  # 不提示密码
            'root@146.190.52.84', 'echo "SSH连接成功"'
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print("✅ SSH密钥认证成功")
            return True
        else:
            print(f"❌ SSH认证失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SSH连接异常: {e}")
        return False

def setup_ssh_tunnel():
    """建立SSH隧道"""
    print("\n🔧 建立SSH隧道...")

    try:
        # 使用密码认证的SSH隧道
        cmd = [
            'ssh', '-L', '9999:localhost:9999',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            'root@146.190.52.84',
            '-N'  # 不执行远程命令
        ]

        print("SSH隧道命令:", ' '.join(cmd))
        print("🔐 请输入VPS root密码...")

        # 启动SSH隧道
        process = subprocess.Popen(cmd)

        # 等待隧道建立
        print("⏳ 等待隧道建立...")
        time.sleep(3)

        # 测试隧道连接
        if test_tunnel_connection():
            print("✅ SSH隧道建立成功!")
            print("🌐 请在浏览器访问: http://localhost:9999")
            print("🚨 保持此窗口开启，按Ctrl+C退出")

            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🔚 关闭SSH隧道...")
                process.terminate()
        else:
            print("❌ 隧道连接失败")
            process.terminate()

    except Exception as e:
        print(f"❌ 隧道建立失败: {e}")

def test_tunnel_connection():
    """测试隧道连接是否成功"""
    import urllib.request

    try:
        req = urllib.request.Request(
            'http://localhost:9999/health',
            headers={'User-Agent': 'Perfect21-Tunnel-Test/1.0'}
        )
        response = urllib.request.urlopen(req, timeout=5)
        return response.status == 200
    except:
        return False

def alternative_solutions():
    """提供替代解决方案"""
    print("\n🔄 替代解决方案:")
    print("1. 使用密码认证SSH:")
    print("   ssh -o PreferredAuthentications=password -L 9999:localhost:9999 root@146.190.52.84")

    print("\n2. 配置SSH密钥 (一次性设置):")
    print("   ssh-keygen -t rsa -b 4096 -f ~/.ssh/vibepilot_key")
    print("   ssh-copy-id -i ~/.ssh/vibepilot_key root@146.190.52.84")

    print("\n3. 使用不同端口尝试:")
    print("   直接访问: http://146.190.52.84")
    print("   备用端口: http://146.190.52.84:8080")

    print("\n4. 网络切换测试:")
    print("   - 尝试手机热点")
    print("   - 尝试不同WiFi网络")
    print("   - 使用VPN服务")

if __name__ == "__main__":
    print("🚀 Perfect21 SSH隧道连接助手")
    print("=" * 40)

    # 检查SSH命令是否可用
    try:
        subprocess.run(['ssh', '-V'], capture_output=True)
    except FileNotFoundError:
        print("❌ SSH命令不可用，请安装OpenSSH客户端")
        sys.exit(1)

    # 测试SSH连接
    if test_ssh_connection():
        setup_ssh_tunnel()
    else:
        print("\n🔧 SSH密钥认证失败，尝试密码认证...")
        alternative_solutions()

        # 尝试密码认证
        print("\n🚀 启动密码认证SSH隧道...")
        try:
            subprocess.run([
                'ssh', '-o', 'PreferredAuthentications=password',
                '-L', '9999:localhost:9999',
                'root@146.190.52.84', '-N'
            ])
        except KeyboardInterrupt:
            print("\n🔚 SSH隧道已关闭")