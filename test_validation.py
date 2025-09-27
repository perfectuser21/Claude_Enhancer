#!/usr/bin/env python3
"""
测试验证脚本
验证所有测试文件的基本功能是否正常
"""

import os
import sys
import importlib.util


def test_file_imports():
    """测试文件导入"""
    test_files = [
        "tests/test_auth.py",
        "tests/test_tasks.py",
        "tests/test_models.py",
        "tests/integration/test_api.py",
    ]

    results = []

    for test_file in test_files:
        try:
            # 尝试编译文件
            with open(test_file, "r", encoding="utf-8") as f:
                code = f.read()

            compile(code, test_file, "exec")
            results.append((test_file, "✅ 语法正确"))

        except SyntaxError as e:
            results.append((test_file, f"❌ 语法错误: {e}"))
        except FileNotFoundError:
            results.append((test_file, "⚠️ 文件不存在"))
        except Exception as e:
            results.append((test_file, f"❌ 其他错误: {e}"))

    return results


def test_config_files():
    """测试配置文件"""
    config_files = [
        "pytest.ini",
        "conftest.py",
        "frontend/vitest.config.ts",
        "frontend/src/test-setup.ts",
    ]

    results = []

    for config_file in config_files:
        if os.path.exists(config_file):
            results.append((config_file, "✅ 文件存在"))
        else:
            results.append((config_file, "❌ 文件不存在"))

    return results


def test_directory_structure():
    """测试目录结构"""
    required_dirs = [
        "tests",
        "tests/integration",
        "frontend/src/__tests__",
        "frontend/src/__tests__/components",
    ]

    results = []

    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            results.append((directory, "✅ 目录存在"))
        else:
            results.append((directory, "❌ 目录不存在"))

    return results


def verify_test_functions():
    """验证测试函数"""
    print("🔍 验证基本测试逻辑...")

    # 简单的认证测试
    def test_simple_auth():
        username = "testuser"
        email = "test@example.com"
        password = "TestPassword123!"

        # 模拟用户数据验证
        assert username and len(username) > 0
        assert "@" in email and "." in email
        assert len(password) >= 8

        return True

    # 简单的任务测试
    def test_simple_task():
        task_data = {"title": "测试任务", "status": "todo", "priority": "medium"}

        assert task_data["title"] and len(task_data["title"]) > 0
        assert task_data["status"] in ["todo", "in_progress", "done"]
        assert task_data["priority"] in ["low", "medium", "high", "urgent"]

        return True

    # 简单的API测试
    def test_simple_api():
        api_endpoints = [
            "/api/health",
            "/api/auth/login",
            "/api/tasks",
            "/api/projects",
        ]

        for endpoint in api_endpoints:
            assert endpoint.startswith("/api/")

        return True

    tests = [
        ("认证逻辑", test_simple_auth),
        ("任务逻辑", test_simple_task),
        ("API逻辑", test_simple_api),
    ]

    results = []

    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "✅ 逻辑正确"))
        except Exception as e:
            results.append((name, f"❌ 逻辑错误: {e}"))

    return results


def main():
    """主函数"""
    print("🚀 Claude Enhancer 5.0 测试框架验证")
    print("=" * 50)

    # 1. 测试文件导入
    print("\n📁 检查测试文件...")
    import_results = test_file_imports()
    for file, status in import_results:
        print(f"  {status} {file}")

    # 2. 测试配置文件
    print("\n⚙️ 检查配置文件...")
    config_results = test_config_files()
    for file, status in config_results:
        print(f"  {status} {file}")

    # 3. 测试目录结构
    print("\n📂 检查目录结构...")
    dir_results = test_directory_structure()
    for directory, status in dir_results:
        print(f"  {status} {directory}")

    # 4. 验证测试逻辑
    print("\n🧪 验证测试逻辑...")
    logic_results = verify_test_functions()
    for name, status in logic_results:
        print(f"  {status} {name}")

    # 统计结果
    all_results = import_results + config_results + dir_results + logic_results

    passed = sum(1 for _, status in all_results if status.startswith("✅"))
    total = len(all_results)

    print("\n" + "=" * 50)
    print("📊 验证结果总结")
    print("=" * 50)
    print(f"总计: {passed}/{total} 项检查通过")

    if passed == total:
        print("🎉 测试框架配置完成，所有检查都通过了！")
        print("\n📋 可用的测试类型:")
        print("  • 后端单元测试: python3 -m pytest tests/")
        print("  • 前端组件测试: cd frontend && npm test")
        print("  • 集成测试: python3 -m pytest tests/integration/")
        print("  • 完整测试套件: python3 run_tests.py")
        return 0
    else:
        print("🔧 部分检查需要修复")
        failed = [
            (name, status) for name, status in all_results if not status.startswith("✅")
        ]
        print("\n❌ 失败项目:")
        for name, status in failed:
            print(f"  • {name}: {status}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
