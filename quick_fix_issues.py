#!/usr/bin/env python3
"""
Perfect21 快速问题修复脚本
解决测试中发现的关键问题
"""

import os
import sys
from pathlib import Path

def fix_git_hooks_interface():
    """修复GitHooks类缺失的get_installed_hooks方法"""
    hooks_file = Path("features/git_workflow/hooks.py")

    if not hooks_file.exists():
        print(f"❌ 文件不存在: {hooks_file}")
        return False

    print(f"🔧 修复GitHooks接口: {hooks_file}")

    # 读取现有内容
    with open(hooks_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已有该方法
    if 'def get_installed_hooks(' in content:
        print("✅ get_installed_hooks方法已存在")
        return True

    # 添加缺失的方法
    fix_code = '''
    def get_installed_hooks(self):
        """获取已安装的Git钩子列表"""
        installed = []
        git_hooks_dir = os.path.join(self.repo_root, '.git', 'hooks')

        if not os.path.exists(git_hooks_dir):
            return installed

        # 检查支持的钩子类型
        supported_hooks = [
            'pre-commit', 'commit-msg', 'pre-push',
            'post-checkout', 'post-merge', 'post-commit'
        ]

        for hook_name in supported_hooks:
            hook_path = os.path.join(git_hooks_dir, hook_name)
            if os.path.exists(hook_path) and os.path.isfile(hook_path):
                installed.append(hook_name)

        return installed
'''

    # 在类定义末尾添加方法（在最后一个方法后）
    if 'class GitHooks:' in content or 'class GitHooks(' in content:
        # 找到类的最后位置并添加方法
        lines = content.split('\n')
        insert_position = -1

        # 寻找类的最后一个方法
        in_class = False
        for i, line in enumerate(lines):
            if 'class GitHooks' in line:
                in_class = True
            elif in_class and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                # 类结束
                insert_position = i
                break

        if insert_position > 0:
            lines.insert(insert_position, fix_code)
            content = '\n'.join(lines)
        else:
            # 如果找不到合适位置，添加到文件末尾
            content += fix_code

        # 写回文件
        with open(hooks_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ 已添加get_installed_hooks方法")
        return True
    else:
        print("❌ 未找到GitHooks类定义")
        return False

def create_version_manager_fix():
    """创建version_manager导入问题的修复"""
    print("🔧 创建version_manager导入修复")

    # 创建一个修复包装器
    fix_content = '''#!/usr/bin/env python3
"""
Version Manager导入修复包装器
解决模块导入路径问题
"""

import os
import sys
import importlib.util
from pathlib import Path

def get_version_manager():
    """动态获取VersionManager类"""
    try:
        # 尝试正常导入
        from features.version_manager import get_global_version_manager
        return get_global_version_manager()
    except ImportError:
        # 使用动态导入
        current_dir = Path(__file__).parent
        vm_file = current_dir / "features" / "version_manager" / "version_manager.py"

        if vm_file.exists():
            spec = importlib.util.spec_from_file_location("version_manager_module", vm_file)
            vm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vm_module)

            return vm_module.VersionManager()
        else:
            raise ImportError(f"无法找到version_manager.py: {vm_file}")

def test_version_manager():
    """测试版本管理器功能"""
    try:
        vm = get_version_manager()
        version = vm.get_current_version()
        print(f"✅ Version Manager测试成功，版本: {version}")
        return True
    except Exception as e:
        print(f"❌ Version Manager测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_version_manager()
    sys.exit(0 if success else 1)
'''

    fix_file = Path("version_manager_fix.py")
    with open(fix_file, 'w', encoding='utf-8') as f:
        f.write(fix_content)

    print(f"✅ 创建修复脚本: {fix_file}")
    return True

def verify_fixes():
    """验证修复结果"""
    print("\n🔍 验证修复结果...")

    # 测试GitHooks修复
    try:
        from features.git_workflow import GitHooks
        hooks = GitHooks()
        if hasattr(hooks, 'get_installed_hooks'):
            result = hooks.get_installed_hooks()
            print(f"✅ GitHooks.get_installed_hooks() 可用，返回: {result}")
        else:
            print("❌ GitHooks.get_installed_hooks() 方法仍然缺失")
    except Exception as e:
        print(f"❌ GitHooks测试失败: {e}")

    # 测试version_manager修复
    try:
        import subprocess
        result = subprocess.run([sys.executable, "version_manager_fix.py"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Version Manager修复验证成功")
        else:
            print(f"❌ Version Manager修复验证失败: {result.stderr}")
    except Exception as e:
        print(f"❌ Version Manager修复验证异常: {e}")

def main():
    """主修复流程"""
    print("🚀 Perfect21 快速问题修复")
    print("=" * 40)

    success_count = 0
    total_fixes = 2

    # 修复1: GitHooks接口
    if fix_git_hooks_interface():
        success_count += 1

    # 修复2: Version Manager导入
    if create_version_manager_fix():
        success_count += 1

    print(f"\n📊 修复完成: {success_count}/{total_fixes}")

    # 验证修复
    verify_fixes()

    print(f"\n🎯 修复建议:")
    print(f"1. 运行测试验证修复效果: python3 test_actual_functionality.py")
    print(f"2. 如果GitHooks修复不完整，请手动添加缺失方法")
    print(f"3. Version Manager使用修复脚本: python3 version_manager_fix.py")

    return success_count == total_fixes

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)