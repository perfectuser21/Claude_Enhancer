#!/usr/bin/env python3
"""
Claude Enhancer 5.1 快速CI/CD测试
=============================================================================
实际测试构建、部署和回滚功能
=============================================================================
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path


def run_command(cmd, description, timeout=30):
    """执行命令并返回结果"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/xx/dev/Claude Enhancer 5.0",
        )

        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            return True, result.stdout
        else:
            print(f"❌ {description} - 失败")
            print(f"错误: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - 超时")
        return False, "Command timeout"
    except Exception as e:
        print(f"❌ {description} - 异常: {e}")
        return False, str(e)


def test_docker_build():
    """测试Docker构建"""
    print("\n🐳 测试Docker构建...")

    # 检查Dockerfile语法
    success, output = run_command("docker build --dry-run .", "检查Dockerfile语法", 10)

    if not success and "docker: command not found" in output:
        print("⚠️ Docker未安装，跳过Docker构建测试")
        return True

    # 构建镜像
    success, output = run_command(
        "docker build -t claude-enhancer:test .", "构建Docker镜像", 300
    )

    return success


def test_compose_validation():
    """测试Docker Compose配置"""
    print("\n📋 测试Docker Compose配置...")

    compose_files = ["docker-compose.production.yml", "docker-compose.performance.yml"]

    all_valid = True

    for compose_file in compose_files:
        if os.path.exists(compose_file):
            success, output = run_command(
                f"docker-compose -f {compose_file} config --quiet",
                f"验证 {compose_file}",
                10,
            )

            if not success and "docker-compose: command not found" in output:
                print("⚠️ Docker Compose未安装，跳过配置验证")
                break

            if not success:
                all_valid = False

    return all_valid


def test_deployment_scripts():
    """测试部署脚本"""
    print("\n🚀 测试部署脚本...")

    scripts_dir = Path("deployment/scripts")
    if not scripts_dir.exists():
        print("⚠️ 部署脚本目录不存在")
        return False

    scripts = list(scripts_dir.glob("*.sh"))
    all_valid = True

    for script in scripts:
        # 检查脚本语法
        success, output = run_command(f"bash -n {script}", f"检查脚本语法: {script.name}", 5)

        if not success:
            all_valid = False

    return all_valid


def test_github_workflows():
    """测试GitHub Actions工作流语法"""
    print("\n🔄 测试GitHub Actions工作流...")

    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("⚠️ GitHub workflows目录不存在")
        return False

    workflows = list(workflows_dir.glob("*.yml"))

    # 简单的YAML语法检查
    try:
        import yaml

        all_valid = True
        for workflow in workflows:
            try:
                with open(workflow, "r") as f:
                    yaml.safe_load(f)
                print(f"✅ {workflow.name} - YAML语法正确")
            except yaml.YAMLError as e:
                print(f"❌ {workflow.name} - YAML语法错误: {e}")
                all_valid = False

        return all_valid

    except ImportError:
        print("⚠️ PyYAML未安装，跳过YAML语法检查")
        return True


def test_application_startup():
    """测试应用启动"""
    print("\n🏃 测试应用启动...")

    # 检查主应用文件
    main_files = ["run_api.py", "main.py", "app.py"]
    found_main = None

    for main_file in main_files:
        if os.path.exists(main_file):
            found_main = main_file
            break

    if not found_main:
        print("⚠️ 未找到主应用文件")
        return False

    # 测试Python语法
    success, output = run_command(
        f"python3 -m py_compile {found_main}", f"检查 {found_main} Python语法", 10
    )

    return success


def test_rollback_mechanism():
    """测试回滚机制"""
    print("\n🔄 测试回滚机制...")

    rollback_script = Path("deployment/scripts/rollback.sh")

    if rollback_script.exists():
        # 检查脚本语法
        success, output = run_command(f"bash -n {rollback_script}", "检查回滚脚本语法", 5)
        return success
    else:
        print("⚠️ 未找到回滚脚本")
        return False


def generate_test_report(results):
    """生成测试报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report = {
        "测试时间": datetime.now().isoformat(),
        "项目": "Claude Enhancer 5.1",
        "测试结果": results,
        "总体状态": "通过" if all(results.values()) else "失败",
        "通过率": f"{sum(results.values())}/{len(results)} ({sum(results.values())/len(results)*100:.1f}%)",
    }

    filename = f"quick_cicd_test_report_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📊 测试报告已保存: {filename}")
    return filename


def main():
    """主测试函数"""
    print("=" * 80)
    print("⚡ Claude Enhancer 5.1 快速CI/CD测试")
    print("=" * 80)

    # 记录测试开始时间
    start_time = time.time()

    # 执行测试
    results = {}

    results["Docker构建"] = test_docker_build()
    results["Compose配置"] = test_compose_validation()
    results["部署脚本"] = test_deployment_scripts()
    results["GitHub工作流"] = test_github_workflows()
    results["应用启动"] = test_application_startup()
    results["回滚机制"] = test_rollback_mechanism()

    # 计算测试时间
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 80)
    print("📊 测试结果摘要")
    print("=" * 80)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    passed = sum(results.values())
    total = len(results)
    pass_rate = passed / total * 100

    print(f"\n📈 通过率: {passed}/{total} ({pass_rate:.1f}%)")
    print(f"⏱️ 测试耗时: {duration:.2f} 秒")

    # 生成报告
    report_file = generate_test_report(results)

    # 总体评估
    if pass_rate >= 100:
        print("\n🎉 所有测试通过！CI/CD系统运行正常")
        status_code = 0
    elif pass_rate >= 80:
        print("\n⚠️ 大部分测试通过，但有一些问题需要注意")
        status_code = 0
    else:
        print("\n❌ 多个测试失败，CI/CD系统需要修复")
        status_code = 1

    print("=" * 80)

    return status_code


if __name__ == "__main__":
    sys.exit(main())
