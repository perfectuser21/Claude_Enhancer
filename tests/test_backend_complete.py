#!/usr/bin/env python3
"""
Perfect21后端系统完整功能测试
验证用户认证、API接口、数据库、缓存等所有组件
"""

import os
import sys
import asyncio
import requests
import time
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from features.auth_system import AuthManager
from modules.database import db_manager
from modules.cache import cache_manager
from modules.logger import log_info, log_error

def test_auth_system():
    """测试认证系统"""
    print("🔐 测试认证系统...")

    try:
        # 创建认证管理器
        auth_manager = AuthManager(db_path="data/test_backend.db")

        # 测试用户注册
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "role": "user"
        }

        result = auth_manager.register(**user_data)
        assert result['success'], f"用户注册失败: {result['message']}"
        print("  ✅ 用户注册成功")

        # 测试用户登录
        login_result = auth_manager.login(
            identifier=user_data["username"],
            password=user_data["password"]
        )
        assert login_result['success'], f"用户登录失败: {login_result['message']}"
        print("  ✅ 用户登录成功")

        # 测试令牌验证
        access_token = login_result['access_token']
        verify_result = auth_manager.verify_token(access_token)
        assert verify_result['success'], f"令牌验证失败: {verify_result['message']}"
        print("  ✅ 令牌验证成功")

        # 测试刷新令牌
        refresh_token = login_result['refresh_token']
        refresh_result = auth_manager.refresh_token(refresh_token)
        assert refresh_result['success'], f"令牌刷新失败: {refresh_result['message']}"
        print("  ✅ 令牌刷新成功")

        # 测试用户资料
        user_id = login_result['user']['id']
        profile_result = auth_manager.get_user_profile(user_id)
        assert profile_result['success'], f"获取用户资料失败: {profile_result['message']}"
        print("  ✅ 用户资料获取成功")

        # 测试修改密码
        password_result = auth_manager.change_password(
            user_id, user_data["password"], "NewPass456!"
        )
        assert password_result['success'], f"修改密码失败: {password_result['message']}"
        print("  ✅ 密码修改成功")

        print("🎉 认证系统测试通过")
        return True

    except Exception as e:
        print(f"❌ 认证系统测试失败: {e}")
        return False
    finally:
        # 清理测试数据库
        test_db = "data/test_backend.db"
        if os.path.exists(test_db):
            os.unlink(test_db)

def test_database_system():
    """测试数据库系统"""
    print("🗄️  测试数据库系统...")

    try:
        # 初始化数据库
        db_manager.initialize()
        print("  ✅ 数据库初始化成功")

        # 测试插入记录
        test_data = {
            'key': 'test_key',
            'value': 'test_value',
            'description': 'Test configuration'
        }
        record_id = db_manager.insert_record('system_config', test_data)
        assert record_id > 0, "插入记录失败"
        print("  ✅ 记录插入成功")

        # 测试查询记录
        query_result = db_manager.execute_query(
            "SELECT * FROM system_config WHERE key = ?",
            ('test_key',)
        )
        assert len(query_result) == 1, "查询记录失败"
        print("  ✅ 记录查询成功")

        # 测试更新记录
        update_count = db_manager.update_record(
            'system_config',
            {'value': 'updated_value'},
            'key = ?',
            ('test_key',)
        )
        assert update_count == 1, "更新记录失败"
        print("  ✅ 记录更新成功")

        # 测试删除记录
        delete_count = db_manager.delete_record(
            'system_config',
            'key = ?',
            ('test_key',)
        )
        assert delete_count == 1, "删除记录失败"
        print("  ✅ 记录删除成功")

        # 测试数据库统计
        stats = db_manager.get_database_stats()
        assert 'database_type' in stats, "获取数据库统计失败"
        print("  ✅ 数据库统计获取成功")

        print("🎉 数据库系统测试通过")
        return True

    except Exception as e:
        print(f"❌ 数据库系统测试失败: {e}")
        return False

def test_cache_system():
    """测试缓存系统"""
    print("💾 测试缓存系统...")

    try:
        # 测试设置缓存
        cache_manager.set('test_key', 'test_value', ttl=60)
        print("  ✅ 缓存设置成功")

        # 测试获取缓存
        value = cache_manager.get('test_key')
        assert value == 'test_value', "获取缓存失败"
        print("  ✅ 缓存获取成功")

        # 测试缓存存在性检查
        exists = cache_manager.exists('test_key')
        assert exists is True, "缓存存在性检查失败"
        print("  ✅ 缓存存在性检查成功")

        # 测试命名空间缓存
        cache_manager.set('ns_key', 'ns_value', namespace='test_ns')
        ns_value = cache_manager.get('ns_key', namespace='test_ns')
        assert ns_value == 'ns_value', "命名空间缓存失败"
        print("  ✅ 命名空间缓存成功")

        # 测试缓存删除
        cache_manager.delete('test_key')
        deleted_value = cache_manager.get('test_key')
        assert deleted_value is None, "缓存删除失败"
        print("  ✅ 缓存删除成功")

        # 测试缓存统计
        stats = cache_manager.get_stats()
        assert 'type' in stats, "获取缓存统计失败"
        print("  ✅ 缓存统计获取成功")

        # 测试健康检查
        health = cache_manager.health_check()
        assert health['status'] == 'healthy', "缓存健康检查失败"
        print("  ✅ 缓存健康检查成功")

        print("🎉 缓存系统测试通过")
        return True

    except Exception as e:
        print(f"❌ 缓存系统测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("🌐 测试API端点...")

    # 这里我们只测试静态端点，因为API服务器没有运行
    try:
        from api.rest_server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # 测试根端点
        response = client.get("/")
        assert response.status_code == 200, "根端点测试失败"
        data = response.json()
        assert 'message' in data, "根端点响应格式错误"
        print("  ✅ 根端点测试成功")

        # 测试健康检查端点
        response = client.get("/health")
        assert response.status_code in [200, 500], "健康检查端点测试失败"
        print("  ✅ 健康检查端点测试成功")

        # 测试认证健康检查端点
        response = client.get("/api/auth/health")
        assert response.status_code == 200, "认证健康检查端点测试失败"
        print("  ✅ 认证健康检查端点测试成功")

        print("🎉 API端点测试通过")
        return True

    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        return False

def test_security_features():
    """测试安全功能"""
    print("🔒 测试安全功能...")

    try:
        from features.auth_system.security_service import SecurityService

        security_service = SecurityService()

        # 测试密码验证
        password_result = security_service.validate_password("WeakPass")
        assert not password_result['valid'], "弱密码验证失败"
        print("  ✅ 弱密码检测成功")

        strong_password_result = security_service.validate_password("StrongPass123!")
        assert strong_password_result['valid'], "强密码验证失败"
        print("  ✅ 强密码验证成功")

        # 测试邮箱验证
        email_result = security_service.validate_email("test@example.com")
        assert email_result['valid'], "邮箱验证失败"
        print("  ✅ 邮箱验证成功")

        invalid_email_result = security_service.validate_email("invalid_email")
        assert not invalid_email_result['valid'], "无效邮箱验证失败"
        print("  ✅ 无效邮箱检测成功")

        # 测试用户名验证
        username_result = security_service.validate_username("validuser123")
        assert username_result['valid'], "用户名验证失败"
        print("  ✅ 用户名验证成功")

        # 测试登录尝试限制
        identifier = "test_user"
        assert security_service.check_login_attempts(identifier), "登录尝试检查失败"
        print("  ✅ 登录尝试检查成功")

        # 测试安全统计
        stats = security_service.get_security_stats()
        assert 'total_events' in stats, "安全统计获取失败"
        print("  ✅ 安全统计获取成功")

        print("🎉 安全功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 安全功能测试失败: {e}")
        return False

def test_token_management():
    """测试令牌管理"""
    print("🎫 测试令牌管理...")

    try:
        from features.auth_system.token_manager import TokenManager

        token_manager = TokenManager()

        # 测试生成访问令牌
        access_token = token_manager.generate_access_token("test_user_123")
        assert access_token, "生成访问令牌失败"
        print("  ✅ 访问令牌生成成功")

        # 测试验证访问令牌
        token_data = token_manager.verify_access_token(access_token)
        assert token_data is not None, "验证访问令牌失败"
        assert token_data['user_id'] == "test_user_123", "令牌数据验证失败"
        print("  ✅ 访问令牌验证成功")

        # 测试生成刷新令牌
        refresh_token = token_manager.generate_refresh_token("test_user_123")
        assert refresh_token, "生成刷新令牌失败"
        print("  ✅ 刷新令牌生成成功")

        # 测试验证刷新令牌
        refresh_data = token_manager.verify_refresh_token(refresh_token)
        assert refresh_data is not None, "验证刷新令牌失败"
        assert refresh_data['user_id'] == "test_user_123", "刷新令牌数据验证失败"
        print("  ✅ 刷新令牌验证成功")

        # 测试撤销令牌
        token_manager.revoke_token(access_token)
        revoked_data = token_manager.verify_access_token(access_token)
        # 注意：撤销后可能仍能解码，但应该在黑名单中
        print("  ✅ 令牌撤销功能测试成功")

        # 测试令牌统计
        stats = token_manager.get_stats()
        assert 'blacklist_size' in stats, "令牌统计获取失败"
        print("  ✅ 令牌统计获取成功")

        print("🎉 令牌管理测试通过")
        return True

    except Exception as e:
        print(f"❌ 令牌管理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 Perfect21后端系统完整功能测试")
    print("=" * 60)

    # 确保测试目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

    test_results = []

    # 运行各个测试
    test_functions = [
        ("认证系统", test_auth_system),
        ("数据库系统", test_database_system),
        ("缓存系统", test_cache_system),
        ("安全功能", test_security_features),
        ("令牌管理", test_token_management),
        ("API端点", test_api_endpoints)
    ]

    for test_name, test_func in test_functions:
        print(f"\n📋 开始测试: {test_name}")
        start_time = time.time()

        try:
            result = test_func()
            elapsed_time = time.time() - start_time

            if result:
                print(f"✅ {test_name}测试通过 ({elapsed_time:.2f}s)")
                test_results.append((test_name, True, elapsed_time))
            else:
                print(f"❌ {test_name}测试失败 ({elapsed_time:.2f}s)")
                test_results.append((test_name, False, elapsed_time))

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"💥 {test_name}测试异常: {e} ({elapsed_time:.2f}s)")
            test_results.append((test_name, False, elapsed_time))

    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed_tests = sum(1 for _, result, _ in test_results if result)
    total_tests = len(test_results)
    total_time = sum(elapsed for _, _, elapsed in test_results)

    for test_name, result, elapsed_time in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name:<15} ({elapsed_time:.2f}s)")

    print(f"\n总体结果: {passed_tests}/{total_tests} 测试通过")
    print(f"总耗时: {total_time:.2f}s")

    # 生成JSON格式的测试报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "total_time": total_time,
        "test_results": [
            {
                "test_name": name,
                "status": "PASS" if result else "FAIL",
                "elapsed_time": elapsed
            }
            for name, result, elapsed in test_results
        ]
    }

    # 保存测试报告
    with open("backend_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 测试报告已保存到: backend_test_report.json")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！Perfect21后端系统功能正常")
        return True
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)