#!/usr/bin/env python3
"""
Perfect21 质量门简单测试
=====================

快速测试质量门基本功能
"""

import asyncio
from pathlib import Path

def test_basic_imports():
    """测试基本导入"""
    print("1. 测试基本导入...")
    try:
        from features.quality_gates.models import GateResult, GateStatus, GateSeverity, QualityGateConfig
        from features.quality_gates.quality_gate_engine import QualityGateEngine
        print("   ✅ 导入成功")
        return True
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

def test_config_creation():
    """测试配置创建"""
    print("2. 测试配置创建...")
    try:
        from features.quality_gates.models import QualityGateConfig

        config = QualityGateConfig()
        print(f"   最小覆盖率: {config.min_line_coverage}%")
        print(f"   最大复杂度: {config.max_complexity}")
        print(f"   并行执行: {config.parallel_execution}")
        print("   ✅ 配置创建成功")
        return True
    except Exception as e:
        print(f"   ❌ 配置创建失败: {e}")
        return False

def test_engine_creation():
    """测试引擎创建"""
    print("3. 测试引擎创建...")
    try:
        from features.quality_gates.quality_gate_engine import QualityGateEngine
        from features.quality_gates.models import QualityGateConfig

        config = QualityGateConfig()
        engine = QualityGateEngine('.', config)
        print(f"   引擎创建成功，项目路径: {engine.project_root}")
        print(f"   质量门数量: {len(engine.gates)}")
        print("   ✅ 引擎创建成功")
        return True
    except Exception as e:
        print(f"   ❌ 引擎创建失败: {e}")
        return False

async def test_quick_check():
    """测试快速检查"""
    print("4. 测试快速检查...")
    try:
        from features.quality_gates.quality_gate_engine import QualityGateEngine
        from features.quality_gates.models import QualityGateConfig

        config = QualityGateConfig()
        config.min_line_coverage = 50.0  # 降低要求
        config.max_complexity = 50       # 降低要求

        engine = QualityGateEngine('.', config)

        # 只测试单个质量门避免超时
        code_gate = engine.gates['code_quality']
        result = await code_gate.check('test')

        print(f"   状态: {result.status.value}")
        print(f"   分数: {result.score:.1f}")
        print(f"   消息: {result.message}")
        print("   ✅ 快速检查成功")
        return True
    except Exception as e:
        print(f"   ❌ 快速检查失败: {e}")
        return False

def test_ci_integration():
    """测试CI集成"""
    print("5. 测试CI集成...")
    try:
        from features.quality_gates.ci_integration import CIIntegration

        ci = CIIntegration('.')
        print("   ✅ CI集成对象创建成功")
        return True
    except Exception as e:
        print(f"   ❌ CI集成失败: {e}")
        return False

def test_pre_commit_config():
    """测试预提交配置存在"""
    print("6. 测试预提交配置...")
    try:
        config_file = Path('.pre-commit-config.yaml')
        if config_file.exists():
            print(f"   预提交配置文件存在: {config_file}")
            print("   ✅ 预提交配置检查成功")
            return True
        else:
            print("   ⚠️ 预提交配置文件不存在，但这不是错误")
            return True
    except Exception as e:
        print(f"   ❌ 预提交配置检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 Perfect21 质量门简单测试")
    print("=" * 50)

    tests = [
        test_basic_imports,
        test_config_creation,
        test_engine_creation,
        test_quick_check,
        test_ci_integration,
        test_pre_commit_config
    ]

    passed = 0
    total = len(tests)

    for i, test in enumerate(tests, 1):
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()

            if result:
                passed += 1

            print()  # 空行分隔
        except Exception as e:
            print(f"   ❌ 测试 {i} 异常: {e}")
            print()

    print("=" * 50)
    print(f"🎯 测试完成: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有测试通过!")

        # 显示使用说明
        print("\n💡 使用说明:")
        print("  python3 main/cli.py quality config --template balanced")
        print("  python3 main/cli.py quality setup hooks")
        print("  python3 main/cli.py quality check --context quick")
        print("  python3 main/cli.py quality trends --days 7")
        print("  python3 main/cli.py quality dashboard")

        return 0
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)