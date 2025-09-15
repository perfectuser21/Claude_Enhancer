#!/usr/bin/env python3
"""
测试capability_discovery功能
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_capability_discovery():
    """测试capability_discovery功能"""
    print("🚀 测试Perfect21 Capability Discovery功能")
    print("=" * 60)

    try:
        # 导入功能模块
        from features.capability_discovery import (
            CapabilityScanner,
            CapabilityRegistry,
            CapabilityLoader,
            bootstrap_capability_discovery
        )

        print("✅ 模块导入成功")

        # 测试扫描器
        print("\n📊 测试功能扫描器...")
        scanner = CapabilityScanner()
        capabilities = scanner.scan_all_features()

        print(f"发现 {len(capabilities)} 个功能模块:")
        for name, capability in capabilities.items():
            print(f"  - {name}: {capability.get('description', '无描述')}")

        # 显示统计信息
        stats = scanner.get_statistics()
        print(f"\n📈 扫描统计:")
        print(f"  总功能数: {stats['total_capabilities']}")
        print(f"  按分类: {stats['by_category']}")
        print(f"  核心功能: {stats['core_capabilities']}")

        # 测试注册器
        print("\n📝 测试功能注册器...")
        registry = CapabilityRegistry()

        # 只注册capability_discovery功能进行测试
        test_capabilities = {
            name: capability
            for name, capability in capabilities.items()
            if name == 'capability_discovery'
        }

        if test_capabilities:
            registration_results = registry.register_capabilities(test_capabilities)
            print(f"注册结果: {registration_results}")

        # 测试完整的启动流程
        print("\n🚀 测试完整启动流程...")
        bootstrap_result = bootstrap_capability_discovery(auto_reload=False)

        if bootstrap_result['success']:
            print("✅ 启动成功!")
            print(f"📊 统计信息: {bootstrap_result['statistics']}")
        else:
            print(f"❌ 启动失败: {bootstrap_result.get('error')}")

        print("\n🎉 capability_discovery功能测试完成!")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_capability_discovery()
    sys.exit(0 if success else 1)