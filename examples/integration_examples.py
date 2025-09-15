#!/usr/bin/env python3
"""
Perfect21 集成示例
演示如何在其他程序中调用Perfect21进行开发任务
"""

import os
import sys
import json
import time
import requests
import subprocess
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.perfect21_sdk import Perfect21SDK, Perfect21Context, quick_task

def example_1_basic_sdk_usage():
    """示例1: 基本SDK使用"""
    print("=== 示例1: 基本SDK使用 ===")

    # 创建SDK实例
    sdk = Perfect21SDK()

    # 检查系统状态
    status = sdk.status()
    print(f"Perfect21状态: {'✅ 可用' if status['success'] else '❌ 不可用'}")

    # 执行开发任务
    print("\n执行任务: 创建一个简单的Python函数...")
    result = sdk.task("创建一个计算斐波那契数列的Python函数")

    if result['success']:
        print("✅ 任务执行成功")
        print(f"输出: {result['stdout'][:200]}...")  # 显示前200字符
    else:
        print("❌ 任务执行失败")
        print(f"错误: {result.get('stderr', result.get('error'))}")

def example_2_workflow_integration():
    """示例2: Git工作流集成"""
    print("\n=== 示例2: Git工作流集成 ===")

    sdk = Perfect21SDK()

    # 创建功能分支
    print("创建功能分支...")
    result = sdk.git_workflow(
        action='create-feature',
        name='user-auth-api',
        from_branch='develop'
    )

    if result['success']:
        print("✅ 功能分支创建成功")
    else:
        print(f"❌ 分支创建失败: {result.get('error')}")

    # 分支信息查询
    print("\n查询分支信息...")
    result = sdk.git_workflow(action='branch-info')
    print(f"分支信息: {result.get('output', '')[:150]}...")

def example_3_async_tasks():
    """示例3: 异步任务处理"""
    print("\n=== 示例3: 异步任务处理 ===")

    sdk = Perfect21SDK()

    # 任务完成回调
    def on_task_complete(task_id: str, result: Dict[str, Any]):
        print(f"🎉 异步任务 {task_id[:8]} 完成!")
        print(f"成功: {result['success']}")
        if result.get('stdout'):
            print(f"输出: {result['stdout'][:100]}...")

    # 启动多个异步任务
    tasks = [
        "创建用户注册API接口",
        "编写用户认证中间件",
        "设计用户数据模型"
    ]

    task_ids = []
    for task_desc in tasks:
        print(f"启动异步任务: {task_desc}")
        task_id = sdk.async_task(task_desc, callback=on_task_complete)
        task_ids.append(task_id)

    print(f"✅ 启动了 {len(task_ids)} 个异步任务")
    print("等待任务完成...")

    # 等待一段时间让任务完成
    time.sleep(5)

def example_4_context_manager():
    """示例4: 上下文管理器使用"""
    print("\n=== 示例4: 上下文管理器使用 ===")

    # 使用上下文管理器自动管理资源
    with Perfect21Context() as p21:
        # 批量执行任务
        tasks = [
            "生成用户模型的单元测试",
            "创建API文档",
            "设置CI/CD流水线配置"
        ]

        results = []
        for task in tasks:
            print(f"执行: {task}")
            result = p21.task(task, timeout=60)  # 较短超时用于演示
            results.append((task, result['success']))

        # 输出结果统计
        success_count = sum(1 for _, success in results if success)
        print(f"\n📊 任务完成统计: {success_count}/{len(results)} 成功")

def example_5_quick_functions():
    """示例5: 便捷函数使用"""
    print("\n=== 示例5: 便捷函数使用 ===")

    # 快速任务执行
    print("使用快速函数执行任务...")
    result = quick_task("创建一个简单的配置文件解析器")

    if result['success']:
        print("✅ 快速任务执行成功")
    else:
        print(f"❌ 快速任务失败: {result.get('error')}")

def example_6_rest_api_client():
    """示例6: REST API客户端调用"""
    print("\n=== 示例6: REST API客户端调用 ===")

    # 注意: 需要先启动REST API服务器
    api_base = "http://127.0.0.1:8000"

    try:
        # 健康检查
        response = requests.get(f"{api_base}/health")
        if response.status_code == 200:
            print("✅ REST API服务可用")

            # 执行任务
            task_data = {
                "description": "创建一个简单的日志记录类",
                "timeout": 120
            }

            print("通过REST API执行任务...")
            response = requests.post(f"{api_base}/task", json=task_data)

            if response.status_code == 200:
                result = response.json()
                print(f"任务执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
            else:
                print(f"❌ API调用失败: {response.status_code}")

        else:
            print("❌ REST API服务不可用")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到REST API服务器")
        print("请先运行: python3 api/rest_server.py")

def example_7_command_line_integration():
    """示例7: 命令行集成"""
    print("\n=== 示例7: 命令行集成 ===")

    project_root = os.path.dirname(os.path.dirname(__file__))

    # 通过subprocess调用Perfect21
    commands = [
        # 获取状态
        ['python3', 'main/cli.py', 'status'],

        # 查看可用钩子
        ['python3', 'main/cli.py', 'hooks', 'list'],

        # 查看工作流操作
        ['python3', 'main/cli.py', 'workflow', 'list']
    ]

    for cmd in commands:
        print(f"\n执行命令: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"✅ 命令执行成功")
                print(f"输出: {result.stdout[:200]}...")
            else:
                print(f"❌ 命令执行失败")
                print(f"错误: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⏰ 命令执行超时")
        except Exception as e:
            print(f"❌ 命令执行异常: {e}")

def example_8_hooks_automation():
    """示例8: Git钩子自动化"""
    print("\n=== 示例8: Git钩子自动化 ===")

    sdk = Perfect21SDK()

    # 安装标准钩子组
    print("安装Perfect21 Git钩子...")
    result = sdk.install_hooks(hook_group='standard', force=False)

    if result['success']:
        print("✅ Git钩子安装成功")
        print("现在Git操作将自动触发Perfect21检查")
    else:
        print(f"❌ 钩子安装失败: {result.get('error')}")

def example_9_ci_cd_integration():
    """示例9: CI/CD集成示例"""
    print("\n=== 示例9: CI/CD集成示例 ===")

    # 模拟CI/CD流水线中的Perfect21调用
    def ci_build_stage():
        """CI构建阶段"""
        print("🔨 CI构建阶段: 代码质量检查")

        result = quick_task("执行代码质量检查和测试")
        return result['success']

    def ci_test_stage():
        """CI测试阶段"""
        print("🧪 CI测试阶段: 自动化测试")

        result = quick_task("运行完整的测试套件")
        return result['success']

    def ci_deploy_stage():
        """CI部署阶段"""
        print("🚀 CI部署阶段: 部署准备")

        result = quick_task("准备生产环境部署配置")
        return result['success']

    # 执行CI流水线
    stages = [ci_build_stage, ci_test_stage, ci_deploy_stage]

    for i, stage in enumerate(stages, 1):
        print(f"\n--- 阶段 {i} ---")
        if not stage():
            print(f"❌ 阶段 {i} 失败，停止流水线")
            break
        print(f"✅ 阶段 {i} 成功")
    else:
        print("\n🎉 CI/CD流水线执行完成！")

def main():
    """运行所有示例"""
    print("🚀 Perfect21 集成示例演示")
    print("=" * 50)

    examples = [
        example_1_basic_sdk_usage,
        example_2_workflow_integration,
        example_3_async_tasks,
        example_4_context_manager,
        example_5_quick_functions,
        example_6_rest_api_client,
        example_7_command_line_integration,
        example_8_hooks_automation,
        example_9_ci_cd_integration
    ]

    for i, example in enumerate(examples, 1):
        try:
            print(f"\n🔄 运行示例 {i}...")
            example()
            print(f"✅ 示例 {i} 完成")
        except Exception as e:
            print(f"❌ 示例 {i} 失败: {e}")

        # 在示例之间暂停
        time.sleep(1)

    print("\n🎉 所有示例演示完成！")
    print("\n📚 要了解更多集成方式，请查看:")
    print("  - api/perfect21_sdk.py (Python SDK)")
    print("  - api/rest_server.py (REST API)")
    print("  - examples/integration_examples.py (本文件)")

if __name__ == "__main__":
    main()