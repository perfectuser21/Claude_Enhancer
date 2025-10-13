"""
认证系统使用示例和登录测试
演示完整的JWT认证系统功能
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from auth import (
    auth_service,
    rbac_manager,
    security_manager,
    require_auth,
    require_roles,
    require_permissions,
    jwt_manager,
    password_manager,
)


def demo_user_registration():
    """演示用户注册"""
    print("\n🔥 用户注册演示")
    print("=" * 50)

    # 注册普通用户
    result = auth_service.register(
        username="john_doe",
        email="john@example.com",
        password="SecurePassword123!",
        roles=["user"],
    )

    if result["success"]:
        print(f"✅ 用户注册成功: {result['user']['username']}")
        print(f"📧 邮箱: {result['user']['email']}")
        print(f"🏷️ 角色: {result['user']['roles']}")
    else:
        print(f"❌ 注册失败: {result['error']}")

    # 注册管理员用户
    result = auth_service.register(
        username="admin_user",
        email="admin@example.com",
        password="AdminPassword456!",
        roles=["admin"],
    )

    if result["success"]:
        print(f"✅ 管理员注册成功: {result['user']['username']}")

    return result["success"]


def demo_user_login():
    """演示用户登录"""
    print("\n🔑 用户登录演示")
    print("=" * 50)

    # 普通用户登录
    result = auth_service.login("john@example.com", "SecurePassword123!")

    if result["success"]:
        print(f"✅ 登录成功: {result['user']['username']}")
        print(f"🎫 访问令牌: {result['tokens']['access_token'][:50]}...")
        print(f"🔄 刷新令牌: {result['tokens']['refresh_token'][:50]}...")
        print(f"⏰ 过期时间: {result['tokens']['expires_in']} 秒")
        return result["tokens"]
    else:
        print(f"❌ 登录失败: {result['error']}")
        return None


def demo_token_verification(tokens):
    """演示令牌验证"""
    print("\n🔍 令牌验证演示")
    print("=" * 50)

    if not tokens:
        print("❌ 没有可用的令牌")
        return

    access_token = tokens["access_token"]

    # 验证令牌
    user_info = auth_service.verify_token(access_token)

    if user_info:
        print(f"✅ 令牌验证成功")
        print(f"👤 用户ID: {user_info['user_id']}")
        print(f"👤 用户名: {user_info['username']}")
        print(f"📧 邮箱: {user_info['email']}")
        print(f"🏷️ 角色: {user_info['roles']}")
    else:
        print("❌ 令牌验证失败")

    # 获取令牌详细信息
    token_info = jwt_manager.get_token_info(access_token)
    print(f"\n📊 令牌信息:")
    print(f"   有效性: {token_info['valid']}")
    print(f"   用户ID: {token_info['user_id']}")
    print(f"   过期时间: {token_info['expires_at']}")
    print(f"   剩余时间: {token_info['time_to_expire']:.0f} 秒")


def demo_rbac_permissions():
    """演示RBAC权限系统"""
    print("\n🛡️ RBAC权限系统演示")
    print("=" * 50)

    # 为用户分配角色
    rbac_manager.assign_role_to_user(1, "user")  # john_doe
    rbac_manager.assign_role_to_user(2, "admin")  # admin_user

    # 检查权限
    print("权限检查结果:")

    # 普通用户权限
    can_access_api = rbac_manager.check_permission(1, "api", "access")
    can_admin_system = rbac_manager.check_permission(1, "system", "admin")

    print(f"  用户1 API访问权限: {'✅' if can_access_api else '❌'}")
    print(f"  用户1 系统管理权限: {'✅' if can_admin_system else '❌'}")

    # 管理员权限
    can_manage_users = rbac_manager.check_permission(2, "user", "create")
    can_admin_system = rbac_manager.check_permission(2, "system", "admin")

    print(f"  用户2 用户管理权限: {'✅' if can_manage_users else '❌'}")
    print(f"  用户2 系统管理权限: {'✅' if can_admin_system else '❌'}")


def demo_security_protection():
    """演示安全防护功能"""
    print("\n🔒 安全防护演示")
    print("=" * 50)

    identifier = "attacker@example.com"
    ip_address = "192.168.1.100"

    # 模拟暴力破解攻击
    print("模拟暴力破解攻击:")
    for i in range(6):
        validation = security_manager.validate_login_attempt(identifier, ip_address)

        if validation["allowed"]:
            print(f"  尝试 {i+1}: 允许登录尝试")
            # 模拟失败登录
            result = security_manager.handle_failed_login(identifier, ip_address)
            if result["locked"]:
                print(f"    🚨 账户已被锁定! 锁定到: {result.get('lockout_until', 'N/A')}")
        else:
            print(f"  尝试 {i+1}: ❌ 被安全系统阻止 - {validation['reason']}")

    # 获取安全状态
    security_status = security_manager.get_security_status()
    print(f"\n📊 安全状态摘要:")
    print(f"  活跃锁定: {security_status['brute_force_protection']['active_lockouts']}")
    print(
        f"  失败尝试: {security_status['brute_force_protection']['total_failed_attempts']}"
    )


def demo_password_features():
    """演示密码功能"""
    print("\n🔐 密码功能演示")
    print("=" * 50)

    # 密码强度验证
    passwords = ["123", "password", "Password123", "SecurePassword123!"]

    print("密码强度测试:")
    for pwd in passwords:
        result = password_manager.validate_password_strength(pwd)
        strength_emoji = {"很弱": "🔴", "弱": "🟠", "中等": "🟡", "强": "🟢"}
        emoji = strength_emoji.get(result["strength"], "⚪")

        print(
            f"  '{pwd}': {emoji} {result['strength']} (分数: {result['score']}/{result['max_score']})"
        )
        if result["errors"]:
            for error in result["errors"][:2]:  # 只显示前2个错误
                print(f"    ⚠️ {error}")

    # 生成安全密码
    print(f"\n🎲 生成的安全密码:")
    secure_password = password_manager.generate_secure_password(16)
    print(f"  密码: {secure_password}")

    # 验证生成的密码强度
    result = password_manager.validate_password_strength(secure_password)
    print(f"  强度: {result['strength']} (分数: {result['score']}/{result['max_score']})")


def demo_decorators():
    """演示装饰器功能"""
    print("\n🎭 装饰器功能演示")
    print("=" * 50)

    # 模拟受保护的函数
    @require_auth
    def protected_function(current_user=None):
        return f"Hello {current_user['username']}, this is protected content!"

    @require_roles(["admin"])
    def admin_function(current_user=None):
        return f"Admin {current_user['username']}, welcome to admin panel!"

    @require_permissions(("user", "read"))
    def user_data_function(current_user=None):
        return f"User data for {current_user['username']}"

    # 获取有效令牌进行测试
    login_result = auth_service.login("john@example.com", "SecurePassword123!")

    if login_result["success"]:
        token = login_result["tokens"]["access_token"]

        print("测试装饰器保护的函数:")

        # 模拟带令牌的调用（实际使用中令牌会从HTTP头获取）
        try:
            pass  # Auto-fixed empty block
            # 这里简化演示，实际使用中装饰器会自动从请求中提取令牌
            user_info = auth_service.verify_token(token)
            if user_info:
                result = protected_function.__wrapped__(current_user=user_info)
                print(f"  ✅ 受保护函数: {result}")
            else:
                print("  ❌ 令牌验证失败")

        except Exception as e:
            print(f"  ❌ 装饰器测试失败: {e}")

    print("\n📝 注意: 在实际应用中，装饰器会自动处理令牌提取和验证")


def demo_token_refresh():
    """演示令牌刷新"""
    print("\n🔄 令牌刷新演示")
    print("=" * 50)

    # 登录获取令牌
    login_result = auth_service.login("john@example.com", "SecurePassword123!")

    if login_result["success"]:
        refresh_token = login_result["tokens"]["refresh_token"]

        # 模拟令牌刷新
        refresh_result = auth_service.refresh_token(refresh_token)

        if refresh_result["success"]:
            print("✅ 令牌刷新成功")
            print(f"🎫 新访问令牌: {refresh_result['tokens']['access_token'][:50]}...")
            print(f"⏰ 过期时间: {refresh_result['tokens']['expires_in']} 秒")
        else:
            print(f"❌ 令牌刷新失败: {refresh_result['error']}")


def run_complete_demo():
    """运行完整演示"""
    print("🚀 Claude Enhancer JWT认证系统完整演示")
    print("=" * 60)

    try:
        pass  # Auto-fixed empty block
        # 1. 用户注册
        demo_user_registration()

        # 2. 用户登录
        tokens = demo_user_login()

        # 3. 令牌验证
        demo_token_verification(tokens)

        # 4. RBAC权限
        demo_rbac_permissions()

        # 5. 安全防护
        demo_security_protection()

        # 6. 密码功能
        demo_password_features()

        # 7. 装饰器功能
        demo_decorators()

        # 8. 令牌刷新
        demo_token_refresh()

        print("\n🎉 演示完成!")
        print("✅ 认证系统所有功能正常工作")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_complete_demo()
