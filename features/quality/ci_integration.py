#!/usr/bin/env python3
"""
Perfect21 CI/CD 质量门集成
=========================

与CI/CD管道集成，自动执行质量检查
"""

import asyncio
import json
import os
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .quality_gate_engine import QualityGateEngine, QualityGateConfig


class CIIntegration:
    """CI/CD集成管理器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config = QualityGateConfig()

    async def setup_pre_commit_hooks(self) -> Dict[str, Any]:
        """设置预提交钩子"""
        try:
            # 创建Git hooks目录
            hooks_dir = self.project_root / ".git" / "hooks"
            hooks_dir.mkdir(exist_ok=True)

            # 创建pre-commit钩子
            pre_commit_hook = hooks_dir / "pre-commit"
            hook_content = self._generate_pre_commit_hook()

            with open(pre_commit_hook, 'w', encoding='utf-8') as f:
                f.write(hook_content)

            # 设置执行权限
            pre_commit_hook.chmod(0o755)

            # 创建pre-push钩子
            pre_push_hook = hooks_dir / "pre-push"
            push_hook_content = self._generate_pre_push_hook()

            with open(pre_push_hook, 'w', encoding='utf-8') as f:
                f.write(push_hook_content)

            pre_push_hook.chmod(0o755)

            return {
                "status": "success",
                "message": "Git hooks安装成功",
                "hooks_installed": ["pre-commit", "pre-push"],
                "hooks_dir": str(hooks_dir)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Git hooks安装失败: {str(e)}",
                "error": str(e)
            }

    def _generate_pre_commit_hook(self) -> str:
        """生成pre-commit钩子脚本"""
        return '''#!/bin/bash
# Perfect21 Pre-commit Quality Gate

set -e

echo "🔍 运行Perfect21质量门检查..."

# 运行快速质量检查
python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.quality_gate_engine import QualityGateEngine, QualityGateConfig

async def run_quick_check():
    config = QualityGateConfig()
    config.fail_fast = True
    config.parallel_execution = True

    engine = QualityGateEngine('.', config)
    results = await engine.run_quick_check()

    if results['status'] != 'passed':
        print(f'\\n❌ 质量门检查失败: {results[\"message\"]}')
        print('\\n详细信息:')
        for gate_name, result in results['details'].items():
            if hasattr(result, 'status') and result.status.value != 'passed':
                print(f'  - {gate_name}: {result.message}')
                for violation in result.violations[:3]:  # 只显示前3个违规
                    print(f'    • {violation.get(\"message\", str(violation))}')

        print('\\n💡 建议:')
        suggestions = set()
        for gate_name, result in results['details'].items():
            if hasattr(result, 'suggestions'):
                suggestions.update(result.suggestions[:2])
        for suggestion in list(suggestions)[:5]:
            print(f'  - {suggestion}')

        sys.exit(1)
    else:
        print(f'✅ 质量门检查通过 (分数: {results[\"score\"]:.1f})')

asyncio.run(run_quick_check())
"

echo "✅ 质量门检查完成"
'''

    def _generate_pre_push_hook(self) -> str:
        """生成pre-push钩子脚本"""
        return '''#!/bin/bash
# Perfect21 Pre-push Quality Gate

set -e

echo "🚀 运行完整质量门检查..."

# 运行完整质量检查
python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.quality_gate_engine import QualityGateEngine, QualityGateConfig

async def run_full_check():
    config = QualityGateConfig()
    config.fail_fast = False
    config.parallel_execution = True

    engine = QualityGateEngine('.', config)
    results = await engine.run_all_gates('push')

    overall = results.get('overall')
    if not overall or overall.status.value == 'failed':
        print(f'\\n❌ 质量门检查失败')
        print(engine.generate_report(results))
        sys.exit(1)
    elif overall.status.value == 'warning':
        print(f'\\n⚠️  质量门检查有警告')
        print(engine.generate_report(results))
        print('\\n继续推送，但请注意修复警告...')
    else:
        print(f'\\n✅ 所有质量门检查通过 (分数: {overall.score:.1f})')

asyncio.run(run_full_check())
"

echo "✅ 完整质量检查完成"
'''

    async def generate_github_actions_workflow(self) -> Dict[str, Any]:
        """生成GitHub Actions工作流"""
        try:
            workflow_content = {
                "name": "Perfect21 Quality Gates",
                "on": {
                    "push": {
                        "branches": ["main", "develop", "feature/*"]
                    },
                    "pull_request": {
                        "branches": ["main", "develop"]
                    }
                },
                "jobs": {
                    "quality-gates": {
                        "runs-on": "ubuntu-latest",
                        "strategy": {
                            "matrix": {
                                "python-version": ["3.8", "3.9", "3.10", "3.11"]
                            }
                        },
                        "steps": [
                            {
                                "uses": "actions/checkout@v3"
                            },
                            {
                                "name": "Set up Python ${{ matrix.python-version }}",
                                "uses": "actions/setup-python@v4",
                                "with": {
                                    "python-version": "${{ matrix.python-version }}"
                                }
                            },
                            {
                                "name": "Install dependencies",
                                "run": self._get_install_dependencies_script()
                            },
                            {
                                "name": "Run Code Quality Gate",
                                "run": "python3 -m pytest tests/ --cov=. --cov-report=xml --cov-report=json"
                            },
                            {
                                "name": "Run Security Gate",
                                "run": "python3 -m bandit -r . -f json -o bandit-report.json || true"
                            },
                            {
                                "name": "Run Performance Gate",
                                "run": self._get_performance_test_script()
                            },
                            {
                                "name": "Run Architecture Gate",
                                "run": self._get_architecture_test_script()
                            },
                            {
                                "name": "Run All Quality Gates",
                                "run": self._get_quality_gates_script()
                            },
                            {
                                "name": "Upload Coverage Reports",
                                "uses": "codecov/codecov-action@v3",
                                "with": {
                                    "file": "./coverage.xml",
                                    "flags": "unittests",
                                    "name": "codecov-umbrella"
                                }
                            },
                            {
                                "name": "Upload Quality Gate Results",
                                "uses": "actions/upload-artifact@v3",
                                "with": {
                                    "name": "quality-gate-results",
                                    "path": ".perfect21/quality_gate_history.json"
                                }
                            }
                        ]
                    }
                }
            }

            # 保存工作流文件
            workflows_dir = self.project_root / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            workflow_file = workflows_dir / "quality-gates.yml"
            with open(workflow_file, 'w', encoding='utf-8') as f:
                yaml.dump(workflow_content, f, default_flow_style=False, sort_keys=False)

            return {
                "status": "success",
                "message": "GitHub Actions工作流已生成",
                "file": str(workflow_file),
                "workflow": workflow_content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"生成工作流失败: {str(e)}",
                "error": str(e)
            }

    def _get_install_dependencies_script(self) -> str:
        """获取依赖安装脚本"""
        return """
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov bandit safety radon flake8 mypy
"""

    def _get_performance_test_script(self) -> str:
        """获取性能测试脚本"""
        return """
python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.performance_gate import PerformanceGate
from features.quality_gates.quality_gate_engine import QualityGateConfig

async def test_performance():
    config = QualityGateConfig()
    gate = PerformanceGate('.', config)
    result = await gate.check('ci')

    if result.status.value == 'failed':
        print(f'Performance gate failed: {result.message}')
        sys.exit(1)
    else:
        print(f'Performance gate passed: {result.score:.1f}')

asyncio.run(test_performance())
"
"""

    def _get_architecture_test_script(self) -> str:
        """获取架构测试脚本"""
        return """
python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.architecture_gate import ArchitectureGate
from features.quality_gates.quality_gate_engine import QualityGateConfig

async def test_architecture():
    config = QualityGateConfig()
    gate = ArchitectureGate('.', config)
    result = await gate.check('ci')

    if result.status.value == 'failed':
        print(f'Architecture gate failed: {result.message}')
        sys.exit(1)
    else:
        print(f'Architecture gate passed: {result.score:.1f}')

asyncio.run(test_architecture())
"
"""

    def _get_quality_gates_script(self) -> str:
        """获取完整质量门测试脚本"""
        return """
python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.quality_gate_engine import QualityGateEngine, QualityGateConfig

async def run_all_gates():
    config = QualityGateConfig()
    config.fail_fast = False
    config.parallel_execution = True

    engine = QualityGateEngine('.', config)
    results = await engine.run_all_gates('ci')

    print(engine.generate_report(results))

    overall = results.get('overall')
    if overall and overall.status.value == 'failed':
        sys.exit(1)

asyncio.run(run_all_gates())
"
"""

    async def generate_gitlab_ci_config(self) -> Dict[str, Any]:
        """生成GitLab CI配置"""
        try:
            config_content = {
                "stages": ["test", "quality", "deploy"],
                "variables": {
                    "PIP_CACHE_DIR": "$CI_PROJECT_DIR/.cache/pip"
                },
                "cache": {
                    "paths": [".cache/pip", "venv/"]
                },
                "before_script": [
                    "python --version",
                    "pip install virtualenv",
                    "virtualenv venv",
                    "source venv/bin/activate",
                    "pip install --upgrade pip",
                    "pip install -r requirements.txt",
                    "pip install pytest pytest-cov bandit safety radon flake8"
                ],
                "test": {
                    "stage": "test",
                    "script": [
                        "pytest tests/ --cov=. --cov-report=xml --cov-report=json"
                    ],
                    "coverage": "/^TOTAL.+?(\\d+\\%)$/",
                    "artifacts": {
                        "reports": {
                            "coverage_report": {
                                "coverage_format": "cobertura",
                                "path": "coverage.xml"
                            }
                        }
                    }
                },
                "quality-gates": {
                    "stage": "quality",
                    "script": [
                        self._get_quality_gates_script()
                    ],
                    "artifacts": {
                        "paths": [".perfect21/quality_gate_history.json"],
                        "reports": {
                            "junit": "junit-*.xml"
                        }
                    },
                    "only": ["main", "develop", "merge_requests"]
                },
                "security-scan": {
                    "stage": "quality",
                    "script": [
                        "bandit -r . -f json -o bandit-report.json",
                        "safety check --json --output safety-report.json"
                    ],
                    "artifacts": {
                        "paths": ["bandit-report.json", "safety-report.json"]
                    },
                    "allow_failure": True
                }
            }

            # 保存配置文件
            config_file = self.project_root / ".gitlab-ci.yml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_content, f, default_flow_style=False, sort_keys=False)

            return {
                "status": "success",
                "message": "GitLab CI配置已生成",
                "file": str(config_file),
                "config": config_content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"生成GitLab CI配置失败: {str(e)}",
                "error": str(e)
            }

    async def setup_continuous_monitoring(self) -> Dict[str, Any]:
        """设置持续监控"""
        try:
            # 创建监控脚本
            monitoring_script = self.project_root / "scripts" / "quality_monitor.py"
            monitoring_script.parent.mkdir(exist_ok=True)

            script_content = '''#!/usr/bin/env python3
"""
Perfect21 质量持续监控
====================

定期运行质量检查并报告结果
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from features.quality_gates.quality_gate_engine import QualityGateEngine, QualityGateConfig

async def run_monitoring():
    """运行质量监控"""
    print(f"🔍 开始质量监控 - {datetime.now().isoformat()}")

    config = QualityGateConfig()
    config.parallel_execution = True
    config.fail_fast = False

    engine = QualityGateEngine('.', config)

    # 运行所有质量门
    results = await engine.run_all_gates('monitoring')

    # 生成报告
    report = engine.generate_report(results)
    print(report)

    # 保存监控结果
    monitoring_dir = Path('.perfect21/monitoring')
    monitoring_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = monitoring_dir / f'quality_report_{timestamp}.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    # 检查质量趋势
    trends = engine.get_quality_trends(days=7)
    print("\\n📊 质量趋势:")
    print(f"  总执行次数: {trends.get('total_executions', 0)}")

    if trends.get('average_score_trend'):
        latest_score = trends['average_score_trend'][-1]['score']
        print(f"  最新平均分数: {latest_score}")

    # 检查是否需要告警
    overall = results.get('overall')
    if overall and overall.status.value == 'failed':
        print("\\n🚨 质量告警: 检测到严重质量问题!")
        return 1
    elif overall and overall.status.value == 'warning':
        print("\\n⚠️  质量警告: 发现质量问题，请关注")
        return 0
    else:
        print("\\n✅ 质量状态良好")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(run_monitoring())
    sys.exit(exit_code)
'''

            with open(monitoring_script, 'w', encoding='utf-8') as f:
                f.write(script_content)

            monitoring_script.chmod(0o755)

            # 创建cron任务配置
            cron_config = '''# Perfect21 质量监控 Cron 任务
# 每天8点运行质量检查
0 8 * * * cd /path/to/Perfect21 && python3 scripts/quality_monitor.py >> logs/quality_monitor.log 2>&1

# 每周一早上生成质量趋势报告
0 9 * * 1 cd /path/to/Perfect21 && python3 -c "
import asyncio
import sys
sys.path.append('.')
from features.quality_gates.quality_gate_engine import QualityGateEngine
engine = QualityGateEngine('.')
trends = engine.get_quality_trends(days=30)
print('Weekly Quality Trends:', trends)
" >> logs/weekly_trends.log 2>&1
'''

            cron_file = self.project_root / "scripts" / "quality_cron.txt"
            with open(cron_file, 'w', encoding='utf-8') as f:
                f.write(cron_config)

            return {
                "status": "success",
                "message": "持续监控已设置",
                "monitoring_script": str(monitoring_script),
                "cron_config": str(cron_file),
                "instructions": [
                    "1. 将监控脚本设置为可执行: chmod +x scripts/quality_monitor.py",
                    "2. 添加cron任务: crontab -e，然后添加scripts/quality_cron.txt中的内容",
                    "3. 修改cron任务中的路径为实际项目路径",
                    "4. 确保logs目录存在: mkdir -p logs"
                ]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"设置持续监控失败: {str(e)}",
                "error": str(e)
            }

    async def create_quality_dashboard(self) -> Dict[str, Any]:
        """创建质量仪表板"""
        try:
            dashboard_script = self.project_root / "scripts" / "quality_dashboard.py"
            dashboard_script.parent.mkdir(exist_ok=True)

            script_content = '''#!/usr/bin/env python3
"""
Perfect21 质量仪表板
==================

生成质量监控仪表板
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from features.quality_gates.quality_gate_engine import QualityGateEngine

async def generate_dashboard():
    """生成质量仪表板"""
    engine = QualityGateEngine('.')

    # 获取质量趋势
    trends = engine.get_quality_trends(days=30)

    # 获取执行历史
    history = engine.get_execution_history(limit=20)

    # 生成HTML仪表板
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 质量仪表板</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; }}
        .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .trend {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .chart {{ background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .violation {{ background: #ffebee; padding: 10px; margin: 5px 0; border-left: 4px solid #f44336; }}
        .success {{ background: #e8f5e8; padding: 10px; margin: 5px 0; border-left: 4px solid #4caf50; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Perfect21 质量仪表板</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="trend">
        <div class="metric">
            <h3>📊 质量概览</h3>
            <p>总执行次数: {trends.get('total_executions', 0)}</p>
            <p>监控天数: 30天</p>
        </div>

        <div class="metric">
            <h3>🏆 质量门性能</h3>
            <ul>
    """

    for gate_name, performance in trends.get('gate_performance', {}).items():
        html_content += f"<li>{gate_name}: {performance['average_score']:.1f}分 ({performance['executions']}次执行)</li>"

    html_content += """
            </ul>
        </div>
    </div>

    <div class="chart">
        <h3>📈 最近执行历史</h3>
    """

    for entry in history[-10:]:  # 最近10次执行
        timestamp = entry['timestamp'][:19].replace('T', ' ')
        summary = entry['summary']
        status_class = 'success' if summary['failed'] == 0 else 'violation'

        html_content += f"""
        <div class="{status_class}">
            <strong>{timestamp}</strong> -
            通过: {summary['passed']}, 失败: {summary['failed']},
            平均分数: {summary['average_score']:.1f}
        </div>
        """

    html_content += """
    </div>

    <div class="chart">
        <h3>🔍 常见违规类型</h3>
        <ul>
    """

    for violation_type, count in trends.get('common_violations', {}).items():
        html_content += f"<li>{violation_type}: {count}次</li>"

    html_content += """
        </ul>
    </div>

    <div class="chart">
        <h3>💡 改进建议</h3>
        <ul>
    """

    for suggestion in trends.get('improvement_suggestions', []):
        html_content += f"<li>{suggestion}</li>"

    html_content += """
        </ul>
    </div>

</body>
</html>
    """

    # 保存仪表板
    dashboard_file = Path('.perfect21/quality_dashboard.html')
    dashboard_file.parent.mkdir(exist_ok=True)

    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 质量仪表板已生成: {dashboard_file}")
    print(f"🌐 在浏览器中打开: file://{dashboard_file.absolute()}")

if __name__ == "__main__":
    asyncio.run(generate_dashboard())
'''

            with open(dashboard_script, 'w', encoding='utf-8') as f:
                f.write(script_content)

            dashboard_script.chmod(0o755)

            return {
                "status": "success",
                "message": "质量仪表板脚本已创建",
                "script": str(dashboard_script),
                "usage": "运行 python3 scripts/quality_dashboard.py 生成仪表板"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"创建质量仪表板失败: {str(e)}",
                "error": str(e)
            }

    async def setup_all_integrations(self) -> Dict[str, Any]:
        """设置所有CI/CD集成"""
        results = {}

        # 设置Git hooks
        results["git_hooks"] = await self.setup_pre_commit_hooks()

        # 生成GitHub Actions
        results["github_actions"] = await self.generate_github_actions_workflow()

        # 生成GitLab CI
        results["gitlab_ci"] = await self.generate_gitlab_ci_config()

        # 设置持续监控
        results["monitoring"] = await self.setup_continuous_monitoring()

        # 创建质量仪表板
        results["dashboard"] = await self.create_quality_dashboard()

        # 统计成功数量
        successful = len([r for r in results.values() if r.get("status") == "success"])
        total = len(results)

        return {
            "status": "success" if successful == total else "partial",
            "message": f"CI/CD集成完成: {successful}/{total} 个组件成功",
            "results": results,
            "next_steps": [
                "1. 提交Git hooks到版本控制",
                "2. 在CI/CD平台中启用工作流",
                "3. 配置cron任务进行持续监控",
                "4. 定期查看质量仪表板",
                "5. 根据质量报告调整开发流程"
            ]
        }