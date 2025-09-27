"""
认证模块 - JWT认证系统
提供完整的用户认证、授权、安全防护功能

主要组件：
- AuthService: 核心认证服务
- JWTTokenManager: JWT令牌管理
- PasswordManager: 密码安全处理
- RBACManager: 角色权限管理
- SecurityManager: 安全防护
- 各种中间件和装饰器

使用示例：
    from auth import auth_service, require_auth, require_roles

    # 用户注册
    result = auth_service.register("username", "email@domain.com", "password")

    # 用户登录
    result = auth_service.login("email@domain.com", "password")

    # 使用装饰器保护路由
    @require_auth
    def protected_route():
        return "This is protected"

    @require_roles(["admin"])
    def admin_only_route():
        return "Admin only"
"""

from .auth import AuthService, User, auth_service
from .jwt import JWTTokenManager, TokenBlacklist, jwt_manager, token_blacklist
from .password import PasswordManager, PasswordPolicy, password_manager, password_policy
from .rbac import RBACManager, Permission, Role, rbac_manager
from .security import (
    BruteForceProtection,
    IPBlocklist,
    SecurityManager,
    ThreatLevel,
    SecurityEventType,
    brute_force_protection,
    ip_blocklist,
    security_manager,
)
from .middleware import (
    AuthMiddleware,
    FlaskAuthMiddleware,
    FastAPIAuthMiddleware,
    require_auth,
    require_roles,
    require_permissions,
    require_admin,
    require_owner,
    optional_auth,
    rate_limit,
    check_permission,
    check_role,
    get_current_user_from_token,
    TokenValidator,
    SecurityUtils,
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude Enhancer Team"

# 导出的主要类和函数
__all__ = [
    # 核心服务
    "AuthService",
    "User",
    "auth_service",
    # JWT管理
    "JWTTokenManager",
    "TokenBlacklist",
    "jwt_manager",
    "token_blacklist",
    # 密码管理
    "PasswordManager",
    "PasswordPolicy",
    "password_manager",
    "password_policy",
    # RBAC权限
    "RBACManager",
    "Permission",
    "Role",
    "rbac_manager",
    # 安全防护
    "BruteForceProtection",
    "IPBlocklist",
    "SecurityManager",
    "ThreatLevel",
    "SecurityEventType",
    "brute_force_protection",
    "ip_blocklist",
    "security_manager",
    # 中间件和装饰器
    "AuthMiddleware",
    "FlaskAuthMiddleware",
    "FastAPIAuthMiddleware",
    "require_auth",
    "require_roles",
    "require_permissions",
    "require_admin",
    "require_owner",
    "optional_auth",
    "rate_limit",
    "check_permission",
    "check_role",
    "get_current_user_from_token",
    "TokenValidator",
    "SecurityUtils",
]


def get_auth_system_info():
    """获取认证系统信息"""
    return {
        "name": "Claude Enhancer JWT Authentication System",
        "version": __version__,
        "author": __author__,
        "components": {
            "auth_service": "Core authentication service",
            "jwt_manager": "JWT token management",
            "password_manager": "Password security handling",
            "rbac_manager": "Role-based access control",
            "security_manager": "Security protection and monitoring",
            "middleware": "Authentication middleware and decorators",
        },
        "features": [
            "JWT token authentication",
            "bcrypt password hashing",
            "Role-based access control (RBAC)",
            "Brute force protection",
            "IP blacklisting",
            "Token refresh mechanism",
            "Password strength validation",
            "Security monitoring",
            "Flask/FastAPI middleware support",
        ],
    }


def quick_setup():
    """快速设置认证系统"""
    print("🔐 Claude Enhancer JWT Authentication System")
    print(f"📦 Version: {__version__}")
    print("\n🚀 Quick Setup:")
    print("1. Import the auth service:")
    print("   from auth import auth_service")
    print("\n2. Register a user:")
    print(
        "   result = auth_service.register('username', 'email@domain.com', 'password')"
    )
    print("\n3. Login:")
    print("   result = auth_service.login('email@domain.com', 'password')")
    print("\n4. Use decorators to protect routes:")
    print("   @require_auth")
    print("   def protected_function():")
    print("       return 'Protected content'")
    print("\n📚 Full documentation available in README.md")


if __name__ == "__main__":
    quick_setup()
