#!/usr/bin/env python3
"""
Perfect21认证系统测试演示
快速演示测试功能和覆盖范围
"""

import os
import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 设置测试环境变量
os.environ.update({
    'JWT_SECRET_KEY': 'demo_secret_key_for_testing_only',
    'TESTING': 'true',
    'LOG_LEVEL': 'INFO'
})

def demo_password_encryption():
    """演示密码加密功能"""
    print("🔐 密码加密演示")
    print("-" * 40)

    from features.auth_system.user_service import UserService

    user_service = UserService("data/demo_auth.db")

    # 演示密码哈希
    password = "DemoPassword123!"
    print(f"原始密码: {password}")

    hashed = user_service._hash_password(password)
    print(f"哈希后: {hashed[:50]}...")

    # 创建测试用户来验证密码
    user_service.init_tables()
    user_id = user_service.create_user(
        username="testuser",
        email="test@example.com",
        password=password
    )

    # 验证密码
    is_valid = user_service.verify_password(user_id, password)
    print(f"验证结果: {'✅ 正确' if is_valid else '❌ 错误'}")

    # 验证错误密码
    is_invalid = user_service.verify_password(user_id, "wrongpassword")
    print(f"错误密码验证: {'❌ 意外通过' if is_invalid else '✅ 正确拒绝'}")

    print()


def demo_jwt_tokens():
    """演示JWT令牌功能"""
    print("🎫 JWT令牌演示")
    print("-" * 40)

    from features.auth_system.token_manager import TokenManager

    token_manager = TokenManager("demo_secret_key")

    # 生成访问令牌
    user_id = "demo_user_123"
    access_token = token_manager.generate_access_token(user_id)
    print(f"访问令牌: {access_token[:50]}...")

    # 验证令牌
    payload = token_manager.verify_access_token(access_token)
    if payload:
        print(f"令牌验证: ✅ 成功")
        print(f"用户ID: {payload['user_id']}")
        print(f"令牌类型: {payload['type']}")
    else:
        print(f"令牌验证: ❌ 失败")

    # 生成刷新令牌
    refresh_token = token_manager.generate_refresh_token(user_id)
    print(f"刷新令牌: {refresh_token[:50]}...")

    # 撤销令牌演示
    token_manager.revoke_token(access_token)
    revoked_payload = token_manager.verify_access_token(access_token)
    print(f"撤销后验证: {'❌ 意外通过' if revoked_payload else '✅ 正确拒绝'}")

    print()


def demo_security_features():
    """演示安全功能"""
    print("🛡️  安全功能演示")
    print("-" * 40)

    from features.auth_system.security_service import SecurityService

    security_service = SecurityService()

    # 密码强度验证
    passwords = [
        "123456",  # 弱密码
        "password",  # 常见密码
        "StrongPass123!"  # 强密码
    ]

    for password in passwords:
        result = security_service.validate_password(password)
        status = "✅ 通过" if result['valid'] else "❌ 拒绝"
        strength = result.get('strength', 'unknown')
        print(f"密码 '{password[:10]}...': {status} ({strength})")

    print()

    # 邮箱验证
    emails = [
        "valid@example.com",  # 有效
        "invalid.email",  # 无效
        "test@domain.co.uk"  # 有效
    ]

    for email in emails:
        result = security_service.validate_email(email)
        status = "✅ 有效" if result['valid'] else "❌ 无效"
        print(f"邮箱 '{email}': {status}")

    print()

    # 登录尝试限制演示
    identifier = "demo@example.com"
    print(f"登录尝试限制演示 ({identifier}):")

    # 模拟多次失败登录
    for i in range(6):
        can_login = security_service.check_login_attempts(identifier)
        if can_login:
            security_service.record_failed_attempt(identifier)
            print(f"  尝试 {i+1}: ✅ 允许登录")
        else:
            print(f"  尝试 {i+1}: ❌ 账户锁定")

    print()


def demo_complete_auth_flow():
    """演示完整认证流程"""
    print("🔄 完整认证流程演示")
    print("-" * 40)

    from features.auth_system.auth_manager import AuthManager

    auth_manager = AuthManager("data/demo_auth_flow.db")

    # 1. 用户注册
    print("1. 用户注册...")
    registration_result = auth_manager.register(
        username="demouser",
        email="demo@example.com",
        password="DemoPass123!"
    )

    if registration_result['success']:
        print(f"   ✅ 注册成功: {registration_result['message']}")
        user_id = registration_result['user_id']
    else:
        print(f"   ❌ 注册失败: {registration_result['message']}")
        return

    # 2. 用户登录
    print("2. 用户登录...")
    login_result = auth_manager.login(
        identifier="demouser",
        password="DemoPass123!"
    )

    if login_result['success']:
        print(f"   ✅ 登录成功")
        access_token = login_result['access_token']
        refresh_token = login_result['refresh_token']
        print(f"   访问令牌: {access_token[:30]}...")
    else:
        print(f"   ❌ 登录失败: {login_result['message']}")
        return

    # 3. 令牌验证
    print("3. 令牌验证...")
    verify_result = auth_manager.verify_token(access_token)

    if verify_result['success']:
        print(f"   ✅ 令牌有效")
        print(f"   用户: {verify_result['user']['username']}")
    else:
        print(f"   ❌ 令牌无效: {verify_result['message']}")

    # 4. 刷新令牌
    print("4. 刷新令牌...")
    refresh_result = auth_manager.refresh_token(refresh_token)

    if refresh_result['success']:
        print(f"   ✅ 刷新成功")
        new_access_token = refresh_result['access_token']
        print(f"   新访问令牌: {new_access_token[:30]}...")
    else:
        print(f"   ❌ 刷新失败: {refresh_result['message']}")

    # 5. 密码修改
    print("5. 密码修改...")
    change_result = auth_manager.change_password(
        user_id=user_id,
        old_password="DemoPass123!",
        new_password="NewDemoPass123!"
    )

    if change_result['success']:
        print(f"   ✅ 密码修改成功")
    else:
        print(f"   ❌ 密码修改失败: {change_result['message']}")

    # 6. 用户登出
    print("6. 用户登出...")
    logout_result = auth_manager.logout(access_token)

    if logout_result['success']:
        print(f"   ✅ 登出成功")
    else:
        print(f"   ❌ 登出失败: {logout_result['message']}")

    # 7. 验证登出后令牌失效
    print("7. 验证令牌失效...")
    verify_after_logout = auth_manager.verify_token(access_token)

    if not verify_after_logout['success']:
        print(f"   ✅ 令牌已失效")
    else:
        print(f"   ❌ 令牌仍然有效（异常）")

    print()


def demo_performance_test():
    """演示性能测试"""
    print("⚡ 性能测试演示")
    print("-" * 40)

    from features.auth_system.token_manager import TokenManager

    token_manager = TokenManager("demo_secret_key")

    # 令牌生成性能测试
    print("令牌生成性能测试（100次）:")
    start_time = time.time()

    for i in range(100):
        token = token_manager.generate_access_token(f"user_{i}")

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / 100

    print(f"  总时间: {total_time:.4f}s")
    print(f"  平均时间: {avg_time:.4f}s")
    print(f"  吞吐量: {100/total_time:.1f} tokens/s")

    # 令牌验证性能测试
    print("\n令牌验证性能测试（100次）:")
    test_token = token_manager.generate_access_token("test_user")

    start_time = time.time()

    for i in range(100):
        payload = token_manager.verify_access_token(test_token)

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / 100

    print(f"  总时间: {total_time:.4f}s")
    print(f"  平均时间: {avg_time:.4f}s")
    print(f"  吞吐量: {100/total_time:.1f} verifications/s")

    print()


def demo_security_tests():
    """演示安全测试"""
    print("🔒 安全测试演示")
    print("-" * 40)

    from features.auth_system.auth_manager import AuthManager

    auth_manager = AuthManager("data/demo_auth_security.db")

    # 注册测试用户
    auth_manager.register(
        username="securitytest",
        email="security@example.com",
        password="SecurityPass123!"
    )

    # SQL注入尝试
    print("SQL注入防护测试:")
    sql_payloads = [
        "admin'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "admin' UNION SELECT * FROM users; --"
    ]

    for payload in sql_payloads:
        result = auth_manager.login(
            identifier=payload,
            password="anypassword"
        )
        status = "❌ 被阻止" if not result['success'] else "⚠️  可能有漏洞"
        print(f"  载荷 '{payload[:20]}...': {status}")

    print()

    # 暴力破解防护测试
    print("暴力破解防护测试:")
    for i in range(7):
        result = auth_manager.login(
            identifier="securitytest",
            password="wrongpassword"
        )

        if i < 5:
            expected = "允许尝试"
        else:
            expected = "账户锁定"

        actual = "允许尝试" if result['error'] != 'TOO_MANY_ATTEMPTS' else "账户锁定"
        status = "✅" if expected == actual else "❌"

        print(f"  尝试 {i+1}: {status} {actual}")

    print()


def cleanup_demo_files():
    """清理演示文件"""
    demo_files = [
        "data/demo_auth.db",
        "data/demo_auth_flow.db",
        "data/demo_auth_security.db"
    ]

    for file_path in demo_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


def main():
    """主演示函数"""
    print("🚀 Perfect21认证系统测试演示")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)

    try:
        # 运行演示
        demo_password_encryption()
        demo_jwt_tokens()
        demo_security_features()
        demo_complete_auth_flow()
        demo_performance_test()
        demo_security_tests()

        print("✅ 演示完成！")
        print()
        print("📋 测试覆盖范围:")
        print("  ✅ 密码加密和验证")
        print("  ✅ JWT令牌生成和验证")
        print("  ✅ 安全策略和验证")
        print("  ✅ 完整认证流程")
        print("  ✅ 性能指标测试")
        print("  ✅ 安全防护测试")
        print()
        print("🎯 要运行完整测试套件，请执行:")
        print("   python run_auth_tests.py")

    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理演示文件
        cleanup_demo_files()


if __name__ == "__main__":
    main()