#!/usr/bin/env python3
"""
测试Git自动化工作流
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / ".claude/core"))

from git_automation import GitAutomation
from phase_state_machine import PhaseStateMachine, PhaseType

def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def test_git_automation():
    """测试Git自动化功能"""
    print("=" * 60)
    print("🧪 Git自动化工作流测试")
    print("=" * 60)

    # 初始化
    git = GitAutomation()
    psm = PhaseStateMachine()

    # 测试1: 获取当前状态
    print("\n📊 当前状态:")
    print(f"  Branch: {git.get_current_branch()}")
    print(f"  Phase: {git.get_current_phase()}")

    # 测试2: 模拟P1->P2->P3流程
    print("\n🔄 模拟Phase进度:")

    phases = [
        (PhaseType.P1_REQUIREMENTS, "需求分析"),
        (PhaseType.P2_DESIGN, "架构设计"),
        (PhaseType.P3_IMPLEMENTATION, "功能实现"),
        (PhaseType.P4_TESTING, "测试验证"),
        (PhaseType.P5_REVIEW, "代码审查"),
        (PhaseType.P6_RELEASE, "发布准备"),
    ]

    for phase, description in phases[:3]:  # 只测试前3个Phase
        print(f"\n  ▶️ 进入{phase.value}: {description}")

        # 转换到Phase
        success = psm.transition_to_phase(
            phase,
            "test_automation",
            {"test": True}
        )

        if success:
            print(f"    ✅ Phase转换成功")

            # 模拟完成Phase
            psm.update_phase_progress(1.0)
            time.sleep(0.5)  # 给Git自动化时间执行

            # 检查是否触发了Git操作
            if phase == PhaseType.P3_IMPLEMENTATION:
                print(f"    🔍 检查是否触发了自动提交...")
                # 注意：实际提交会被Git hooks阻止，这里只是测试流程

        else:
            print(f"    ❌ Phase转换失败")

    # 测试3: 测试Git自动化命令
    print("\n🎯 测试Git自动化命令:")

    test_cases = [
        ("获取当前分支", lambda: git.get_current_branch()),
        ("获取当前Phase", lambda: git.get_current_phase()),
        # 注意：下面的操作会实际修改Git状态，谨慎使用
        # ("创建feature分支", lambda: git.auto_create_branch("TEST-001", "test-feature")),
        # ("自动提交", lambda: git.auto_commit_phase("P3", "test: 测试提交")),
        # ("创建tag", lambda: git.auto_tag_release("v0.0.1-test")),
    ]

    for test_name, test_func in test_cases:
        try:
            result = test_func()
            print(f"  ✅ {test_name}: {result}")
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")

    # 测试4: 验证配置
    print("\n⚙️ 验证配置:")
    config_path = Path(__file__).parent / ".workflow/config.yml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        git_config = config.get('git', {})
        print(f"  auto_commit: {git_config.get('auto_commit', False)}")
        print(f"  auto_tag: {git_config.get('auto_tag', False)}")
        print(f"  auto_pr: {git_config.get('auto_pr', False)}")
        print(f"  auto_merge: {git_config.get('auto_merge', False)}")
    else:
        print("  ⚠️ 配置文件不存在")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

def test_workflow_simulation():
    """模拟完整的6-Phase工作流"""
    print("\n" + "=" * 60)
    print("🚀 模拟完整6-Phase工作流")
    print("=" * 60)

    print("""
工作流说明:
1. P1 Requirements - 需求分析 → 生成PLAN.md
2. P2 Design - 架构设计 → 生成DESIGN.md
3. P3 Implementation - 代码实现 → 自动git commit
4. P4 Testing - 测试验证 → 自动git commit
5. P5 Review - 代码审查 → 自动git commit
6. P6 Release - 发布准备 → 自动git tag

Git自动化特性:
- P3/P4/P5结束时自动提交代码
- P6结束时自动打tag
- 可选：自动创建PR（需要gh CLI）
- 可选：自动合并到main（默认关闭）
    """)

    # 显示当前配置状态
    git = GitAutomation()
    print(f"\n📍 当前状态:")
    print(f"   分支: {git.get_current_branch()}")
    print(f"   Phase: {git.get_current_phase()}")

    # 检查是否在feature分支
    current_branch = git.get_current_branch()
    if not current_branch.startswith("feature/"):
        print("\n⚠️ 建议在feature分支上测试")
        print("   运行: python git_automation.py branch TEST-001 demo")

    print("\n提示: 实际使用时，Phase会根据你的操作自动推进")
    print("      Git操作会在Phase完成时自动触发")

if __name__ == "__main__":
    # 检查依赖
    try:
        import yaml
        print("✅ yaml模块已安装")
    except ImportError:
        print("❌ 请安装pyyaml: pip install pyyaml")
        sys.exit(1)

    # 运行测试
    test_git_automation()
    test_workflow_simulation()