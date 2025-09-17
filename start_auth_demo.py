#!/usr/bin/env python3
"""
Perfect21认证系统演示脚本
展示完整的登录功能实现
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")

    required_packages = ['fastapi', 'uvicorn', 'bcrypt', 'pyjwt', 'redis']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")

    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False

    return True

def setup_environment():
    """设置环境变量"""
    print("🔧 设置环境变量...")

    # 设置JWT密钥
    os.environ['JWT_SECRET_KEY'] = 'perfect21_demo_jwt_secret_key_for_testing_12345'

    # 设置允许的CORS域名
    os.environ['ALLOWED_ORIGINS'] = 'http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000'

    print("  ✅ JWT_SECRET_KEY")
    print("  ✅ ALLOWED_ORIGINS")

def start_server():
    """启动API服务器"""
    print("🚀 启动Perfect21认证API服务器...")

    try:
        # 启动服务器
        process = subprocess.Popen([
            sys.executable, "api/rest_server.py",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print("  ✅ 服务器启动中...")
        print("  📡 地址: http://127.0.0.1:8000")
        print("  📚 API文档: http://127.0.0.1:8000/docs")
        print("  🔐 认证端点: http://127.0.0.1:8000/api/auth")

        # 等待服务器启动
        time.sleep(3)

        return process

    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return None

def demo_api_calls():
    """演示API调用"""
    print("\n🎯 演示API调用...")

    try:
        import requests

        base_url = "http://127.0.0.1:8000"

        # 1. 健康检查
        print("1. 健康检查...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   状态: {response.status_code}")

        # 2. 用户注册
        print("2. 用户注册...")
        register_data = {
            "username": "demouser",
            "email": "demo@perfect21.com",
            "password": "DemoPassword123!",
            "role": "user"
        }

        response = requests.post(f"{base_url}/api/auth/register", json=register_data, timeout=10)
        print(f"   注册状态: {response.status_code}")
        if response.status_code == 200:
            register_result = response.json()
            print(f"   注册成功: {register_result.get('success')}")

        # 3. 用户登录
        print("3. 用户登录...")
        login_data = {
            "identifier": "demouser",
            "password": "DemoPassword123!",
            "remember_me": False
        }

        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        print(f"   登录状态: {response.status_code}")

        if response.status_code == 200:
            login_result = response.json()
            if login_result.get('success'):
                access_token = login_result.get('access_token')
                print(f"   登录成功!")
                print(f"   访问令牌: {access_token[:50]}...")

                # 4. 访问受保护资源
                print("4. 访问受保护资源...")
                headers = {"Authorization": f"Bearer {access_token}"}

                # 验证令牌
                response = requests.get(f"{base_url}/api/auth/verify", headers=headers, timeout=5)
                print(f"   令牌验证: {response.status_code}")

                # 获取用户资料
                response = requests.get(f"{base_url}/api/auth/profile", headers=headers, timeout=5)
                print(f"   用户资料: {response.status_code}")

                return True

        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ API调用失败: {e}")
        return False
    except ImportError:
        print("⚠️ 需要安装 requests: pip install requests")
        return False

def show_features():
    """显示功能特性"""
    print("\n🎉 Perfect21认证系统功能特性:")
    print("=" * 50)

    features = [
        "🔐 JWT认证中间件 - 安全的令牌验证",
        "🔒 bcrypt密码加密 - 12轮强加密",
        "🗄️ Redis会话管理 - 高性能会话存储",
        "🚦 API速率限制 - 滑动窗口算法",
        "🛡️ 安全策略验证 - 密码强度、防暴力破解",
        "📋 完整认证流程 - 注册/登录/登出/刷新",
        "⚡ 高性能架构 - Redis缓存、连接池",
        "🔧 生产就绪 - 错误处理、日志记录",
        "📖 完整API文档 - FastAPI自动生成",
        "🎯 易于集成 - 依赖注入、中间件"
    ]

    for feature in features:
        print(f"  {feature}")

    print(f"\n📚 API文档地址: http://127.0.0.1:8000/docs")
    print(f"🔗 认证端点: http://127.0.0.1:8000/api/auth")

def main():
    """主函数"""
    print("🚀 Perfect21认证系统演示")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        return

    # 设置环境
    setup_environment()

    # 启动服务器
    server_process = start_server()
    if not server_process:
        return

    try:
        # 演示API调用
        demo_success = demo_api_calls()

        # 显示功能特性
        show_features()

        if demo_success:
            print("\n✅ 演示完成！认证系统运行正常")
        else:
            print("\n⚠️ 演示部分功能可能需要手动测试")

        print("\n🌐 可以通过以下方式测试:")
        print("  • 浏览器访问: http://127.0.0.1:8000/docs")
        print("  • API工具(如Postman)测试认证端点")
        print("  • 运行测试脚本: python test_login_complete.py")

        print("\n按 Ctrl+C 停止服务器")

        # 自动打开浏览器
        try:
            webbrowser.open("http://127.0.0.1:8000/docs")
        except:
            pass

        # 等待用户停止
        server_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✅ 服务器已停止")

if __name__ == "__main__":
    main()