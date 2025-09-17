#!/usr/bin/env python3
"""
Perfect21 测试覆盖率质量门
=========================

检查测试覆盖率是否达到要求的阈值
"""

import asyncio
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import GateResult, GateStatus, GateSeverity


class CoverageGate:
    """测试覆盖率质量门"""

    def __init__(self, project_root: str, config):
        self.project_root = Path(project_root)
        self.config = config

    async def check(self, context: str = "commit") -> GateResult:
        """执行测试覆盖率检查"""
        start_time = datetime.now()
        violations = []
        details = {}
        suggestions = []

        try:
            # 1. 运行测试并生成覆盖率报告
            coverage_result = await self._run_coverage_analysis()
            details["coverage"] = coverage_result

            # 2. 检查覆盖率阈值
            line_coverage = coverage_result.get("line_coverage", 0)
            branch_coverage = coverage_result.get("branch_coverage", 0)
            function_coverage = coverage_result.get("function_coverage", 0)

            # 行覆盖率检查
            if line_coverage < self.config.min_line_coverage:
                violations.append({
                    "type": "insufficient_line_coverage",
                    "message": f"行覆盖率不足: {line_coverage:.1f}% < {self.config.min_line_coverage}%",
                    "severity": "high",
                    "current": line_coverage,
                    "required": self.config.min_line_coverage
                })
                suggestions.append(f"增加测试以提高行覆盖率到 {self.config.min_line_coverage}%")

            # 分支覆盖率检查
            if branch_coverage < self.config.min_branch_coverage:
                violations.append({
                    "type": "insufficient_branch_coverage",
                    "message": f"分支覆盖率不足: {branch_coverage:.1f}% < {self.config.min_branch_coverage}%",
                    "severity": "medium",
                    "current": branch_coverage,
                    "required": self.config.min_branch_coverage
                })
                suggestions.append(f"增加边界条件测试以提高分支覆盖率到 {self.config.min_branch_coverage}%")

            # 函数覆盖率检查
            if function_coverage < self.config.min_function_coverage:
                violations.append({
                    "type": "insufficient_function_coverage",
                    "message": f"函数覆盖率不足: {function_coverage:.1f}% < {self.config.min_function_coverage}%",
                    "severity": "medium",
                    "current": function_coverage,
                    "required": self.config.min_function_coverage
                })
                suggestions.append(f"为未测试的函数添加测试用例")

            # 3. 检查未覆盖的关键文件
            uncovered_critical = await self._check_uncovered_critical_files(coverage_result)
            details["uncovered_critical"] = uncovered_critical
            if uncovered_critical["files"]:
                violations.append({
                    "type": "uncovered_critical_files",
                    "message": f"关键文件未测试: {len(uncovered_critical['files'])} 个",
                    "severity": "high",
                    "files": uncovered_critical["files"]
                })
                suggestions.append("为关键业务逻辑文件添加测试")

            # 4. 检查测试质量
            test_quality = await self._check_test_quality()
            details["test_quality"] = test_quality
            if test_quality["issues"]:
                for issue in test_quality["issues"]:
                    violations.append({
                        "type": "test_quality_issue",
                        "message": issue["message"],
                        "severity": issue["severity"],
                        "file": issue.get("file", "")
                    })

            # 计算覆盖率分数
            score = self._calculate_coverage_score(coverage_result, violations)

            # 确定状态
            if line_coverage < self.config.min_line_coverage:
                status = GateStatus.FAILED
                severity = GateSeverity.HIGH
                message = f"测试覆盖率不达标: {line_coverage:.1f}%"
            elif branch_coverage < self.config.min_branch_coverage:
                status = GateStatus.WARNING
                severity = GateSeverity.MEDIUM
                message = f"分支覆盖率偏低: {branch_coverage:.1f}%"
            elif violations:
                status = GateStatus.WARNING
                severity = GateSeverity.LOW
                message = f"发现 {len(violations)} 个覆盖率问题"
            else:
                status = GateStatus.PASSED
                severity = GateSeverity.INFO
                message = f"测试覆盖率达标: {line_coverage:.1f}%"

            # 添加覆盖率改进建议
            if violations:
                suggestions.extend([
                    "运行 pytest --cov-report=html 查看详细覆盖率报告",
                    "使用 pytest --cov-report=term-missing 查看未覆盖的行",
                    "考虑添加集成测试和端到端测试",
                    "定期审查和更新测试用例"
                ])

            execution_time = (datetime.now() - start_time).total_seconds()

            return GateResult(
                gate_name="coverage",
                status=status,
                severity=severity,
                score=score,
                message=message,
                details=details,
                violations=violations,
                suggestions=list(set(suggestions)),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "context": context,
                    "tests_run": coverage_result.get("tests_run", 0),
                    "test_files": coverage_result.get("test_files", 0)
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name="coverage",
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"覆盖率检查失败: {str(e)}",
                details={"error": str(e)},
                violations=[{"type": "check_error", "message": str(e), "severity": "high"}],
                suggestions=["检查测试环境和依赖", "确保pytest和coverage已安装"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    async def _run_coverage_analysis(self) -> Dict[str, Any]:
        """运行覆盖率分析"""
        try:
            # 首先尝试运行现有的测试
            test_result = subprocess.run([
                'python3', '-m', 'pytest',
                '--cov=' + str(self.project_root),
                '--cov-report=xml',
                '--cov-report=json',
                '--cov-report=term',
                '--cov-config=.coveragerc',
                'tests/',
                '-v'
            ], capture_output=True, text=True, timeout=300, cwd=str(self.project_root))

            # 解析XML覆盖率报告
            xml_coverage = await self._parse_xml_coverage()
            json_coverage = await self._parse_json_coverage()

            # 如果有覆盖率数据，使用它
            if xml_coverage or json_coverage:
                coverage_data = json_coverage or xml_coverage
            else:
                # 否则尝试简单的测试覆盖率分析
                coverage_data = await self._simple_coverage_analysis()

            # 统计测试信息
            test_files = list(self.project_root.rglob("test_*.py")) + list(self.project_root.rglob("*_test.py"))
            tests_run = self._count_tests_from_output(test_result.stdout) if test_result.returncode == 0 else 0

            coverage_data.update({
                "tests_run": tests_run,
                "test_files": len(test_files),
                "test_successful": test_result.returncode == 0,
                "test_output": test_result.stdout[-1000:] if test_result.stdout else "",  # 最后1000字符
                "test_errors": test_result.stderr[-1000:] if test_result.stderr else ""
            })

            return coverage_data

        except subprocess.TimeoutExpired:
            return {
                "line_coverage": 0,
                "branch_coverage": 0,
                "function_coverage": 0,
                "error": "测试执行超时",
                "tests_run": 0,
                "test_files": 0,
                "test_successful": False
            }
        except Exception as e:
            return {
                "line_coverage": 0,
                "branch_coverage": 0,
                "function_coverage": 0,
                "error": str(e),
                "tests_run": 0,
                "test_files": 0,
                "test_successful": False
            }

    async def _parse_xml_coverage(self) -> Optional[Dict[str, Any]]:
        """解析XML覆盖率报告"""
        xml_file = self.project_root / "coverage.xml"
        if not xml_file.exists():
            return None

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # 获取总体覆盖率
            line_rate = float(root.get('line-rate', 0)) * 100
            branch_rate = float(root.get('branch-rate', 0)) * 100

            # 统计文件覆盖率
            file_coverage = []
            for package in root.findall('.//package'):
                for class_elem in package.findall('classes/class'):
                    filename = class_elem.get('filename', '')
                    file_line_rate = float(class_elem.get('line-rate', 0)) * 100
                    file_branch_rate = float(class_elem.get('branch-rate', 0)) * 100

                    file_coverage.append({
                        "file": filename,
                        "line_coverage": file_line_rate,
                        "branch_coverage": file_branch_rate
                    })

            return {
                "line_coverage": line_rate,
                "branch_coverage": branch_rate,
                "function_coverage": line_rate,  # XML格式中通常没有单独的函数覆盖率
                "file_coverage": file_coverage,
                "source": "xml"
            }

        except Exception:
            return None

    async def _parse_json_coverage(self) -> Optional[Dict[str, Any]]:
        """解析JSON覆盖率报告"""
        json_file = self.project_root / "coverage.json"
        if not json_file.exists():
            return None

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            totals = data.get('totals', {})
            line_coverage = (totals.get('covered_lines', 0) / totals.get('num_statements', 1)) * 100
            branch_coverage = (totals.get('covered_branches', 0) / totals.get('num_branches', 1)) * 100 if totals.get('num_branches', 0) > 0 else line_coverage

            # 文件级别覆盖率
            file_coverage = []
            for filename, file_data in data.get('files', {}).items():
                summary = file_data.get('summary', {})
                file_line_coverage = (summary.get('covered_lines', 0) / summary.get('num_statements', 1)) * 100
                file_branch_coverage = (summary.get('covered_branches', 0) / summary.get('num_branches', 1)) * 100 if summary.get('num_branches', 0) > 0 else file_line_coverage

                file_coverage.append({
                    "file": filename,
                    "line_coverage": file_line_coverage,
                    "branch_coverage": file_branch_coverage
                })

            return {
                "line_coverage": line_coverage,
                "branch_coverage": branch_coverage,
                "function_coverage": line_coverage,
                "file_coverage": file_coverage,
                "source": "json"
            }

        except Exception:
            return None

    async def _simple_coverage_analysis(self) -> Dict[str, Any]:
        """简单的覆盖率分析（当没有专业工具时）"""
        # 统计Python文件和测试文件
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

        test_files = [f for f in python_files if 'test' in f.name.lower()]
        source_files = [f for f in python_files if 'test' not in f.name.lower()]

        # 简单估算：假设每个测试文件测试对应的源文件
        estimated_coverage = min((len(test_files) / len(source_files)) * 100, 100) if source_files else 0

        return {
            "line_coverage": estimated_coverage,
            "branch_coverage": estimated_coverage * 0.8,  # 估算分支覆盖率为行覆盖率的80%
            "function_coverage": estimated_coverage * 0.9,  # 估算函数覆盖率
            "file_coverage": [],
            "source": "estimated",
            "source_files": len(source_files),
            "test_files": len(test_files)
        }

    async def _check_uncovered_critical_files(self, coverage_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查未覆盖的关键文件"""
        critical_patterns = [
            "main/*.py",
            "api/*.py",
            "features/*/manager.py",
            "features/*/orchestrator.py",
            "features/*/gateway.py"
        ]

        critical_files = []
        for pattern in critical_patterns:
            critical_files.extend(self.project_root.rglob(pattern))

        uncovered_files = []
        file_coverage = coverage_result.get("file_coverage", [])

        for critical_file in critical_files:
            file_rel_path = str(critical_file.relative_to(self.project_root))

            # 查找该文件的覆盖率
            file_cov = next((fc for fc in file_coverage if fc["file"] in file_rel_path), None)

            if not file_cov or file_cov["line_coverage"] < 50:  # 覆盖率低于50%视为未充分测试
                uncovered_files.append({
                    "file": file_rel_path,
                    "coverage": file_cov["line_coverage"] if file_cov else 0,
                    "reason": "关键业务逻辑文件"
                })

        return {
            "files": uncovered_files,
            "critical_files_total": len(critical_files)
        }

    async def _check_test_quality(self) -> Dict[str, Any]:
        """检查测试质量"""
        test_files = list(self.project_root.rglob("test_*.py")) + list(self.project_root.rglob("*_test.py"))
        issues = []

        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_rel_path = str(test_file.relative_to(self.project_root))

                # 检查测试文件是否有断言
                if 'assert' not in content and 'assertEqual' not in content and 'assertTrue' not in content:
                    issues.append({
                        "file": file_rel_path,
                        "message": "测试文件缺少断言",
                        "severity": "medium"
                    })

                # 检查是否有空测试
                test_functions = content.count('def test_')
                if test_functions == 0:
                    issues.append({
                        "file": file_rel_path,
                        "message": "文件中没有测试函数",
                        "severity": "high"
                    })

                # 检查测试函数长度（简单检查）
                lines = content.split('\n')
                in_test_function = False
                test_function_lines = 0
                for line in lines:
                    if line.strip().startswith('def test_'):
                        in_test_function = True
                        test_function_lines = 0
                    elif in_test_function:
                        if line.strip() and not line.startswith(' '):
                            if test_function_lines > 50:  # 测试函数过长
                                issues.append({
                                    "file": file_rel_path,
                                    "message": "测试函数过长，考虑拆分",
                                    "severity": "low"
                                })
                            in_test_function = False
                        else:
                            test_function_lines += 1

            except Exception:
                continue

        return {
            "issues": issues,
            "test_files_checked": len(test_files)
        }

    def _count_tests_from_output(self, output: str) -> int:
        """从测试输出中统计测试数量"""
        import re
        # 查找类似 "collected 25 items" 或 "25 passed" 的模式
        patterns = [
            r'collected (\d+) items',
            r'(\d+) passed',
            r'=+ (\d+) passed'
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return int(match.group(1))

        return 0

    def _calculate_coverage_score(self, coverage_result: Dict[str, Any], violations: List[Dict[str, Any]]) -> float:
        """计算覆盖率分数"""
        line_coverage = coverage_result.get("line_coverage", 0)
        branch_coverage = coverage_result.get("branch_coverage", 0)
        function_coverage = coverage_result.get("function_coverage", 0)

        # 基础分数基于覆盖率
        base_score = (line_coverage * 0.5 + branch_coverage * 0.3 + function_coverage * 0.2)

        # 根据违规情况扣分
        for violation in violations:
            vtype = violation.get("type", "")
            severity = violation.get("severity", "medium")

            if vtype == "insufficient_line_coverage":
                base_score -= 20
            elif vtype == "insufficient_branch_coverage":
                base_score -= 10
            elif vtype == "insufficient_function_coverage":
                base_score -= 5
            elif vtype == "uncovered_critical_files":
                base_score -= 15
            elif vtype == "test_quality_issue":
                if severity == "high":
                    base_score -= 10
                elif severity == "medium":
                    base_score -= 5
                else:
                    base_score -= 2

        # 如果测试失败，额外扣分
        if not coverage_result.get("test_successful", True):
            base_score -= 30

        # 确保分数在0-100范围内
        return max(0.0, min(100.0, base_score))