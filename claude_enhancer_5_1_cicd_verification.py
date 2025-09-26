#!/usr/bin/env python3
"""
Claude Enhancer 5.1 CI/CD验证脚本
=============================================================================
全面验证CI/CD流程的各个环节
- 构建流程验证
- 测试自动化检查
- 代码质量验证
- 安全扫描分析
- 部署脚本检查
- 回滚机制测试
=============================================================================
"""

import json
import subprocess
import sys
import os
import yaml
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cicd_verification.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CICDVerificationReport:
    """CI/CD验证报告生成器"""

    def __init__(self):
        self.results = {
            "验证时间": datetime.now().isoformat(),
            "项目": "Claude Enhancer 5.1",
            "版本": "5.1.0",
            "构建状态": {},
            "测试结果": {},
            "质量检查": {},
            "安全扫描": {},
            "部署准备": {},
            "回滚机制": {},
            "总体评估": {},
            "改进建议": [],
        }
        self.score = 0
        self.max_score = 0

    def add_check(self, category: str, item: str, status: str, details: Dict = None):
        """添加检查项目"""
        if category not in self.results:
            self.results[category] = {}

        self.results[category][item] = {
            "状态": status,
            "时间": datetime.now().strftime("%H:%M:%S"),
            "详情": details or {},
        }

        # 计分
        self.max_score += 1
        if status in ["✅ 通过", "🟢 正常", "✅ 可用"]:
            self.score += 1
        elif status in ["⚠️ 警告", "🟡 部分通过"]:
            self.score += 0.5

    def generate_report(self) -> str:
        """生成报告"""
        overall_score = (self.score / self.max_score * 100) if self.max_score > 0 else 0

        if overall_score >= 90:
            self.results["总体评估"]["状态"] = "🟢 优秀"
            self.results["总体评估"]["建议"] = "CI/CD流程配置完善，可以投入生产使用"
        elif overall_score >= 75:
            self.results["总体评估"]["状态"] = "🟡 良好"
            self.results["总体评估"]["建议"] = "CI/CD流程基本完善，建议解决警告项目"
        elif overall_score >= 60:
            self.results["总体评估"]["状态"] = "🟠 中等"
            self.results["总体评估"]["建议"] = "CI/CD流程需要改进，存在一些问题需要解决"
        else:
            self.results["总体评估"]["状态"] = "🔴 需改进"
            self.results["总体评估"]["建议"] = "CI/CD流程存在重大问题，需要全面检查和改进"

        self.results["总体评估"]["得分"] = f"{overall_score:.1f}%"

        return json.dumps(self.results, ensure_ascii=False, indent=2)


class CICDVerifier:
    """CI/CD验证器"""

    def __init__(self):
        self.report = CICDVerificationReport()
        self.project_root = Path("/home/xx/dev/Claude Enhancer 5.0")

    def verify_build_process(self):
        """验证构建流程"""
        logger.info("🔍 验证构建流程...")

        # 1. 检查Dockerfile
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            with open(dockerfile_path, "r") as f:
                content = f.read()

            # 验证多阶段构建
            if "FROM" in content and "as" in content:
                self.report.add_check("构建状态", "多阶段构建", "✅ 通过", {"描述": "使用多阶段构建优化镜像大小"})
            else:
                self.report.add_check("构建状态", "多阶段构建", "⚠️ 警告", {"描述": "未使用多阶段构建"})

            # 验证安全配置
            if "USER" in content and "claude" in content:
                self.report.add_check("构建状态", "安全用户", "✅ 通过", {"描述": "使用非root用户运行应用"})
            else:
                self.report.add_check("构建状态", "安全用户", "❌ 失败", {"描述": "应该使用非root用户运行应用"})

            # 验证健康检查
            if "HEALTHCHECK" in content:
                self.report.add_check("构建状态", "健康检查", "✅ 通过", {"描述": "配置了容器健康检查"})
            else:
                self.report.add_check("构建状态", "健康检查", "⚠️ 警告", {"描述": "建议添加健康检查配置"})

        # 2. 检查docker-compose配置
        compose_files = list(self.project_root.glob("docker-compose*.yml"))
        if compose_files:
            self.report.add_check(
                "构建状态",
                "容器编排",
                "✅ 通过",
                {"描述": f"找到 {len(compose_files)} 个docker-compose配置文件"},
            )
        else:
            self.report.add_check(
                "构建状态", "容器编排", "⚠️ 警告", {"描述": "未找到docker-compose配置文件"}
            )

        # 3. 检查requirements.txt
        requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                deps = f.readlines()

            self.report.add_check(
                "构建状态",
                "依赖管理",
                "✅ 通过",
                {
                    "描述": f"定义了 {len([d for d in deps if d.strip() and not d.startswith('#')])} 个依赖包"
                },
            )
        else:
            self.report.add_check(
                "构建状态", "依赖管理", "❌ 失败", {"描述": "未找到requirements.txt文件"}
            )

    def verify_test_automation(self):
        """验证测试自动化"""
        logger.info("🧪 验证测试自动化...")

        # 1. 检查GitHub Actions工作流
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml"))
            self.report.add_check(
                "测试结果",
                "CI工作流",
                "✅ 通过",
                {"描述": f"配置了 {len(workflow_files)} 个GitHub Actions工作流"},
            )

            # 分析工作流内容
            for workflow_file in workflow_files:
                with open(workflow_file, "r") as f:
                    content = f.read()

                # 检查测试步骤
                if "pytest" in content or "test" in content.lower():
                    self.report.add_check(
                        "测试结果",
                        f"测试步骤-{workflow_file.name}",
                        "✅ 通过",
                        {"描述": "包含自动化测试步骤"},
                    )

                # 检查安全扫描
                if (
                    "security" in content.lower()
                    or "bandit" in content
                    or "safety" in content
                ):
                    self.report.add_check(
                        "测试结果", f"安全扫描-{workflow_file.name}", "✅ 通过", {"描述": "包含安全扫描步骤"}
                    )

                # 检查覆盖率
                if "coverage" in content or "cov" in content:
                    self.report.add_check(
                        "测试结果", f"覆盖率检查-{workflow_file.name}", "✅ 通过", {"描述": "包含覆盖率检查"}
                    )
        else:
            self.report.add_check(
                "测试结果", "CI工作流", "❌ 失败", {"描述": "未找到GitHub Actions工作流配置"}
            )

        # 2. 检查测试文件
        test_files = []
        for pattern in ["test_*.py", "*_test.py", "test*.py"]:
            test_files.extend(list(self.project_root.rglob(pattern)))

        if test_files:
            self.report.add_check(
                "测试结果", "测试文件", "✅ 通过", {"描述": f"找到 {len(test_files)} 个测试文件"}
            )
        else:
            self.report.add_check("测试结果", "测试文件", "⚠️ 警告", {"描述": "未找到测试文件"})

        # 3. 检查pytest配置
        pytest_configs = (
            list(self.project_root.glob("pytest.ini"))
            + list(self.project_root.glob("pyproject.toml"))
            + list(self.project_root.glob("setup.cfg"))
        )

        if pytest_configs:
            self.report.add_check("测试结果", "测试配置", "✅ 通过", {"描述": "配置了pytest测试框架"})
        else:
            self.report.add_check("测试结果", "测试配置", "⚠️ 警告", {"描述": "建议配置pytest测试框架"})

    def verify_code_quality(self):
        """验证代码质量检查"""
        logger.info("📋 验证代码质量检查...")

        # 1. 检查代码格式化工具配置
        quality_tools = {
            "Black配置": ["pyproject.toml", ".black"],
            "Flake8配置": [".flake8", "setup.cfg"],
            "MyPy配置": ["mypy.ini", "pyproject.toml"],
            "isort配置": [".isort.cfg", "pyproject.toml"],
        }

        for tool, config_files in quality_tools.items():
            found = any((self.project_root / cf).exists() for cf in config_files)
            if found:
                self.report.add_check("质量检查", tool, "✅ 通过", {"描述": "配置了代码质量工具"})
            else:
                self.report.add_check("质量检查", tool, "⚠️ 警告", {"描述": "建议配置代码质量工具"})

        # 2. 检查pre-commit hooks
        precommit_config = self.project_root / ".pre-commit-config.yaml"
        if precommit_config.exists():
            self.report.add_check(
                "质量检查", "Pre-commit Hooks", "✅ 通过", {"描述": "配置了pre-commit hooks"}
            )
        else:
            self.report.add_check(
                "质量检查", "Pre-commit Hooks", "⚠️ 警告", {"描述": "建议配置pre-commit hooks"}
            )

        # 3. 检查Claude Enhancer hooks
        claude_hooks_dir = self.project_root / ".claude" / "hooks"
        if claude_hooks_dir.exists():
            hook_files = list(claude_hooks_dir.glob("*.sh"))
            self.report.add_check(
                "质量检查",
                "Claude Hooks",
                "✅ 通过",
                {"描述": f"配置了 {len(hook_files)} 个Claude Enhancer hooks"},
            )
        else:
            self.report.add_check(
                "质量检查", "Claude Hooks", "⚠️ 警告", {"描述": "未找到Claude Enhancer hooks配置"}
            )

    def verify_security_scanning(self):
        """验证安全扫描"""
        logger.info("🔒 验证安全扫描...")

        # 1. 检查工作流中的安全扫描
        workflows_dir = self.project_root / ".github" / "workflows"
        security_tools_found = set()

        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                with open(workflow_file, "r") as f:
                    content = f.read().lower()

                if "bandit" in content:
                    security_tools_found.add("Bandit")
                if "safety" in content:
                    security_tools_found.add("Safety")
                if "semgrep" in content:
                    security_tools_found.add("Semgrep")
                if "trivy" in content:
                    security_tools_found.add("Trivy")
                if "snyk" in content:
                    security_tools_found.add("Snyk")

        if security_tools_found:
            self.report.add_check(
                "安全扫描",
                "静态安全分析",
                "✅ 通过",
                {"描述": f"配置了安全扫描工具: {', '.join(security_tools_found)}"},
            )
        else:
            self.report.add_check("安全扫描", "静态安全分析", "❌ 失败", {"描述": "未配置安全扫描工具"})

        # 2. 检查依赖安全
        requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():
            # 简单检查是否有版本锁定
            with open(requirements_path, "r") as f:
                content = f.read()

            versioned_deps = len(
                [line for line in content.split("\n") if "==" in line or ">=" in line]
            )
            total_deps = len(
                [
                    line
                    for line in content.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
            )

            if versioned_deps / max(total_deps, 1) > 0.8:
                self.report.add_check(
                    "安全扫描",
                    "依赖版本锁定",
                    "✅ 通过",
                    {"描述": f"{versioned_deps}/{total_deps} 个依赖已锁定版本"},
                )
            else:
                self.report.add_check("安全扫描", "依赖版本锁定", "⚠️ 警告", {"描述": "建议锁定更多依赖版本"})

        # 3. 检查容器安全配置
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            with open(dockerfile_path, "r") as f:
                content = f.read()

            security_checks = {
                "非root用户": "USER" in content
                and "root" not in content.split("USER")[-1],
                "只读文件系统": "read_only" in content or "readonly" in content,
                "安全选项": "security_opt" in content or "no-new-privileges" in content,
            }

            passed_checks = sum(security_checks.values())
            total_checks = len(security_checks)

            if passed_checks >= 2:
                self.report.add_check(
                    "安全扫描",
                    "容器安全",
                    "✅ 通过",
                    {"描述": f"通过了 {passed_checks}/{total_checks} 项安全检查"},
                )
            else:
                self.report.add_check(
                    "安全扫描",
                    "容器安全",
                    "⚠️ 警告",
                    {"描述": f"仅通过了 {passed_checks}/{total_checks} 项安全检查"},
                )

    def verify_deployment_readiness(self):
        """验证部署准备状态"""
        logger.info("🚀 验证部署准备状态...")

        # 1. 检查部署脚本
        scripts_dir = self.project_root / "deployment" / "scripts"
        if scripts_dir.exists():
            script_files = list(scripts_dir.glob("*.sh"))
            deployment_strategies = []

            for script in script_files:
                if "blue-green" in script.name:
                    deployment_strategies.append("Blue-Green")
                if "canary" in script.name:
                    deployment_strategies.append("Canary")
                if "rolling" in script.name:
                    deployment_strategies.append("Rolling")

            if deployment_strategies:
                self.report.add_check(
                    "部署准备",
                    "部署策略",
                    "✅ 通过",
                    {"描述": f"支持部署策略: {', '.join(deployment_strategies)}"},
                )
            else:
                self.report.add_check("部署准备", "部署策略", "⚠️ 警告", {"描述": "未找到部署策略脚本"})
        else:
            self.report.add_check("部署准备", "部署策略", "❌ 失败", {"描述": "未找到部署脚本目录"})

        # 2. 检查环境配置
        env_files = list(self.project_root.glob(".env*"))
        if env_files:
            self.report.add_check(
                "部署准备", "环境配置", "✅ 通过", {"描述": f"找到 {len(env_files)} 个环境配置文件"}
            )
        else:
            self.report.add_check("部署准备", "环境配置", "⚠️ 警告", {"描述": "建议提供环境配置示例文件"})

        # 3. 检查生产配置
        prod_configs = [
            self.project_root / "docker-compose.production.yml",
            self.project_root / "deployment" / "docker-compose.prod.yml",
            self.project_root / "k8s",
            self.project_root / "terraform",
        ]

        found_prod_configs = [config.name for config in prod_configs if config.exists()]

        if found_prod_configs:
            self.report.add_check(
                "部署准备",
                "生产配置",
                "✅ 通过",
                {"描述": f"配置了生产环境: {', '.join(found_prod_configs)}"},
            )
        else:
            self.report.add_check("部署准备", "生产配置", "❌ 失败", {"描述": "未找到生产环境配置"})

        # 4. 检查监控配置
        monitoring_configs = [
            self.project_root / "monitoring",
            self.project_root / "prometheus.yml",
            self.project_root / "grafana",
        ]

        found_monitoring = [
            config.name for config in monitoring_configs if config.exists()
        ]

        if found_monitoring:
            self.report.add_check(
                "部署准备", "监控配置", "✅ 通过", {"描述": f"配置了监控: {', '.join(found_monitoring)}"}
            )
        else:
            self.report.add_check("部署准备", "监控配置", "⚠️ 警告", {"描述": "建议配置监控系统"})

    def verify_rollback_mechanism(self):
        """验证回滚机制"""
        logger.info("🔄 验证回滚机制...")

        # 1. 检查回滚脚本
        rollback_scripts = []
        for pattern in ["**/rollback*.sh", "**/rollback*.py"]:
            rollback_scripts.extend(list(self.project_root.rglob(pattern)))

        if rollback_scripts:
            self.report.add_check(
                "回滚机制", "回滚脚本", "✅ 通过", {"描述": f"找到 {len(rollback_scripts)} 个回滚脚本"}
            )
        else:
            self.report.add_check("回滚机制", "回滚脚本", "❌ 失败", {"描述": "未找到回滚脚本"})

        # 2. 检查CI/CD中的回滚配置
        workflows_dir = self.project_root / ".github" / "workflows"
        rollback_in_ci = False

        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.yml"):
                with open(workflow_file, "r") as f:
                    content = f.read().lower()

                if "rollback" in content:
                    rollback_in_ci = True
                    break

        if rollback_in_ci:
            self.report.add_check("回滚机制", "CI集成", "✅ 通过", {"描述": "CI/CD流程包含回滚配置"})
        else:
            self.report.add_check("回滚机制", "CI集成", "⚠️ 警告", {"描述": "建议在CI/CD中配置自动回滚"})

        # 3. 检查数据库迁移回滚
        migration_dirs = [
            self.project_root / "database" / "migrations",
            self.project_root / "migrations",
            self.project_root / "alembic",
        ]

        migration_found = any(d.exists() for d in migration_dirs)

        if migration_found:
            self.report.add_check("回滚机制", "数据库迁移", "✅ 通过", {"描述": "配置了数据库迁移管理"})
        else:
            self.report.add_check("回滚机制", "数据库迁移", "⚠️ 警告", {"描述": "建议配置数据库迁移管理"})

    def run_comprehensive_verification(self):
        """运行综合验证"""
        logger.info("🚀 开始Claude Enhancer 5.1 CI/CD综合验证...")

        try:
            # 执行所有验证
            self.verify_build_process()
            self.verify_test_automation()
            self.verify_code_quality()
            self.verify_security_scanning()
            self.verify_deployment_readiness()
            self.verify_rollback_mechanism()

            # 生成改进建议
            self._generate_improvement_suggestions()

            logger.info("✅ CI/CD验证完成")
            return True

        except Exception as e:
            logger.error(f"❌ CI/CD验证过程中发生错误: {e}")
            return False

    def _generate_improvement_suggestions(self):
        """生成改进建议"""
        suggestions = []

        # 基于检查结果生成建议
        for category, items in self.report.results.items():
            if isinstance(items, dict):
                for item, details in items.items():
                    if isinstance(details, dict) and details.get("状态") in [
                        "❌ 失败",
                        "⚠️ 警告",
                    ]:
                        suggestions.append(
                            {
                                "类别": category,
                                "项目": item,
                                "状态": details["状态"],
                                "建议": details["详情"].get("描述", "需要改进"),
                            }
                        )

        self.report.results["改进建议"] = suggestions

    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_enhancer_5_1_cicd_report_{timestamp}.json"

        report_content = self.report.generate_report()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"📊 CI/CD验证报告已保存至: {filename}")
        return filename


def generate_html_report(json_report_path: str):
    """生成HTML报告"""
    with open(json_report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Enhancer 5.1 CI/CD验证报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .header p {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin: 10px 0;
        }}
        .score-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .score {{
            font-size: 4em;
            font-weight: bold;
            color: #27ae60;
            margin: 20px 0;
        }}
        .status {{
            font-size: 1.5em;
            margin: 15px 0;
        }}
        .categories {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        .category {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        .category:hover {{
            transform: translateY(-5px);
        }}
        .category h3 {{
            color: #2c3e50;
            margin-top: 0;
            font-size: 1.4em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .check-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        .check-item:last-child {{
            border-bottom: none;
        }}
        .check-name {{
            flex: 1;
            color: #34495e;
            font-weight: 500;
        }}
        .check-status {{
            margin-left: 10px;
            font-weight: bold;
        }}
        .pass {{ color: #27ae60; }}
        .warn {{ color: #f39c12; }}
        .fail {{ color: #e74c3c; }}
        .suggestions {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .suggestions h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .suggestion-item {{
            background: #fff;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Claude Enhancer 5.1</h1>
            <h2>CI/CD流程验证报告</h2>
            <p>生成时间: {data.get('验证时间', 'N/A')}</p>
            <p>项目版本: {data.get('版本', 'N/A')}</p>
        </div>

        <div class="score-card">
            <h3>📊 总体评估</h3>
            <div class="score">{data.get('总体评估', {}).get('得分', 'N/A')}</div>
            <div class="status">{data.get('总体评估', {}).get('状态', 'N/A')}</div>
            <p>{data.get('总体评估', {}).get('建议', 'N/A')}</p>
        </div>

        <div class="categories">
    """

    # 生成各类别的检查结果
    categories = ["构建状态", "测试结果", "质量检查", "安全扫描", "部署准备", "回滚机制"]

    for category in categories:
        if category in data:
            html_content += f"""
            <div class="category">
                <h3>{category}</h3>
            """

            for item, details in data[category].items():
                status = details.get("状态", "N/A")
                css_class = (
                    "pass" if "✅" in status else ("warn" if "⚠️" in status else "fail")
                )

                html_content += f"""
                <div class="check-item">
                    <span class="check-name">{item}</span>
                    <span class="check-status {css_class}">{status}</span>
                </div>
                """

            html_content += "</div>"

    html_content += """
        </div>

        <div class="suggestions">
            <h3>💡 改进建议</h3>
    """

    # 添加改进建议
    suggestions = data.get("改进建议", [])
    if suggestions:
        for suggestion in suggestions:
            html_content += f"""
            <div class="suggestion-item">
                <strong>{suggestion.get('类别', 'N/A')} - {suggestion.get('项目', 'N/A')}</strong><br>
                状态: {suggestion.get('状态', 'N/A')}<br>
                建议: {suggestion.get('建议', 'N/A')}
            </div>
            """
    else:
        html_content += "<p>🎉 太棒了！没有改进建议，CI/CD配置已经很完善了！</p>"

    html_content += """
        </div>

        <div class="timestamp">
            <p>报告生成完毕 | Claude Enhancer 5.1 DevOps团队</p>
        </div>
    </div>
</body>
</html>
    """

    html_filename = json_report_path.replace(".json", ".html")
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"📊 HTML报告已生成: {html_filename}")
    return html_filename


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 Claude Enhancer 5.1 CI/CD流程验证")
    print("=" * 80)

    verifier = CICDVerifier()

    # 运行验证
    success = verifier.run_comprehensive_verification()

    if success:
        # 保存报告
        json_report = verifier.save_report()
        html_report = generate_html_report(json_report)

        print("\n" + "=" * 80)
        print("✅ CI/CD验证完成！")
        print(f"📊 JSON报告: {json_report}")
        print(f"🌐 HTML报告: {html_report}")
        print("=" * 80)

        # 显示简要结果
        report_data = json.loads(verifier.report.generate_report())
        print(f"\n📈 总体评估: {report_data['总体评估']['状态']}")
        print(f"📊 得分: {report_data['总体评估']['得分']}")
        print(f"💡 建议: {report_data['总体评估']['建议']}")

        return 0
    else:
        print("\n❌ CI/CD验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
