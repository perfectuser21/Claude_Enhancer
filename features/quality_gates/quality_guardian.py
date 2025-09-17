"""
Quality Guardian - Mock Implementation for Testing
质量守护者 - 预防性质量检查系统
"""

from typing import Dict, Any, List, Optional
import re
import json
from datetime import datetime


class QualityGuardian:
    """质量守护者 - 预防性质量检查"""

    def __init__(self):
        self.quality_rules = self._load_default_rules()
        self.quality_history: List[Dict[str, Any]] = []

    def check_quality_gate(self, gate_config: Dict[str, Any], quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查质量门"""
        try:
            gate_name = gate_config.get('name', 'Unknown Gate')
            checks = gate_config.get('checks', [])

            passed_checks = 0
            failed_checks = []
            check_details = []

            for check in checks:
                check_type = check.get('type', '')
                check_result = self._execute_quality_check(check, quality_data)

                check_details.append({
                    'type': check_type,
                    'passed': check_result['passed'],
                    'value': check_result.get('value'),
                    'threshold': check_result.get('threshold'),
                    'message': check_result.get('message', '')
                })

                if check_result['passed']:
                    passed_checks += 1
                else:
                    failed_checks.append({
                        'type': check_type,
                        'reason': check_result.get('message', 'Check failed')
                    })

            overall_passed = len(failed_checks) == 0
            quality_score = (passed_checks / len(checks) * 100) if checks else 100

            result = {
                'passed': overall_passed,
                'gate_name': gate_name,
                'checks_total': len(checks),
                'checks_passed': passed_checks,
                'checks_failed': len(failed_checks),
                'quality_score': quality_score,
                'failed_checks': failed_checks,
                'check_details': check_details,
                'timestamp': datetime.now().isoformat()
            }

            # 记录质量历史
            self.quality_history.append(result)

            return result

        except Exception as e:
            return {
                'passed': False,
                'error': f"Quality gate check failed: {str(e)}",
                'quality_score': 0
            }

    def _execute_quality_check(self, check: Dict[str, Any], quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个质量检查"""
        check_type = check.get('type', '')

        if check_type == 'code_coverage':
            threshold = check.get('threshold', 80)
            actual_coverage = quality_data.get('code_coverage', 0)
            passed = actual_coverage >= threshold

            return {
                'passed': passed,
                'value': actual_coverage,
                'threshold': threshold,
                'message': f"Code coverage: {actual_coverage}% (required: {threshold}%)"
            }

        elif check_type == 'complexity':
            max_complexity = check.get('max_value', 10)
            actual_complexity = quality_data.get('complexity', 0)
            passed = actual_complexity <= max_complexity

            return {
                'passed': passed,
                'value': actual_complexity,
                'threshold': max_complexity,
                'message': f"Complexity: {actual_complexity} (max: {max_complexity})"
            }

        elif check_type == 'security_scan':
            required = check.get('required', True)
            scan_passed = quality_data.get('security_scan', False)
            passed = not required or scan_passed

            return {
                'passed': passed,
                'value': scan_passed,
                'message': f"Security scan: {'Passed' if scan_passed else 'Failed'}"
            }

        elif check_type == 'response_time':
            max_time = check.get('max_ms', 200)
            actual_time = quality_data.get('response_time', 0)
            passed = actual_time <= max_time

            return {
                'passed': passed,
                'value': actual_time,
                'threshold': max_time,
                'message': f"Response time: {actual_time}ms (max: {max_time}ms)"
            }

        elif check_type == 'memory_usage':
            max_memory = check.get('max_mb', 512)
            actual_memory = quality_data.get('memory_usage', 0)
            passed = actual_memory <= max_memory

            return {
                'passed': passed,
                'value': actual_memory,
                'threshold': max_memory,
                'message': f"Memory usage: {actual_memory}MB (max: {max_memory}MB)"
            }

        elif check_type == 'cpu_usage':
            max_cpu = check.get('max_percent', 80)
            actual_cpu = quality_data.get('cpu_usage', 0)
            passed = actual_cpu <= max_cpu

            return {
                'passed': passed,
                'value': actual_cpu,
                'threshold': max_cpu,
                'message': f"CPU usage: {actual_cpu}% (max: {max_cpu}%)"
            }

        else:
            return {
                'passed': False,
                'message': f"Unknown check type: {check_type}"
            }

    def analyze_code_quality(self, code_sample: str) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            quality_metrics = {
                'line_count': len(code_sample.split('\n')),
                'complexity_score': self._calculate_complexity(code_sample),
                'maintainability_score': self._calculate_maintainability(code_sample),
                'readability_score': self._calculate_readability(code_sample),
                'security_issues': self._detect_security_issues(code_sample)
            }

            overall_score = (
                quality_metrics['maintainability_score'] * 0.4 +
                quality_metrics['readability_score'] * 0.3 +
                (10 - quality_metrics['complexity_score']) * 0.3
            )

            return {
                'success': True,
                'overall_score': round(overall_score, 2),
                'metrics': quality_metrics,
                'recommendations': self._generate_recommendations(quality_metrics)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Code quality analysis failed: {str(e)}"
            }

    def get_quality_rules(self) -> List[Dict[str, Any]]:
        """获取质量规则"""
        return self.quality_rules

    def calculate_quality_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """计算质量得分"""
        try:
            # 标准化指标 (0-10分制)
            normalized_metrics = {}

            # 复杂度 (越低越好)
            complexity = metrics.get('complexity', 5)
            normalized_metrics['complexity'] = max(0, 10 - complexity)

            # 覆盖率 (越高越好)
            coverage = metrics.get('coverage', 80)
            normalized_metrics['coverage'] = min(10, coverage / 10)

            # 重复度 (越低越好)
            duplication = metrics.get('duplication', 10)
            normalized_metrics['duplication'] = max(0, 10 - duplication / 10)

            # 可维护性 (越高越好)
            maintainability = metrics.get('maintainability', 8)
            normalized_metrics['maintainability'] = maintainability

            # 计算加权平均分
            weights = {
                'complexity': 0.25,
                'coverage': 0.30,
                'duplication': 0.20,
                'maintainability': 0.25
            }

            weighted_score = sum(
                normalized_metrics.get(metric, 0) * weight
                for metric, weight in weights.items()
            )

            return {
                'score': round(weighted_score, 2),
                'grade': self._get_quality_grade(weighted_score),
                'normalized_metrics': normalized_metrics,
                'original_metrics': metrics
            }

        except Exception as e:
            return {
                'score': 0,
                'error': f"Quality score calculation failed: {str(e)}"
            }

    def _load_default_rules(self) -> List[Dict[str, Any]]:
        """加载默认质量规则"""
        return [
            {
                'name': 'Code Coverage',
                'type': 'coverage',
                'threshold': 80,
                'severity': 'high',
                'description': 'Minimum code coverage percentage'
            },
            {
                'name': 'Cyclomatic Complexity',
                'type': 'complexity',
                'max_value': 10,
                'severity': 'medium',
                'description': 'Maximum cyclomatic complexity per function'
            },
            {
                'name': 'Code Duplication',
                'type': 'duplication',
                'max_percentage': 15,
                'severity': 'medium',
                'description': 'Maximum code duplication percentage'
            },
            {
                'name': 'Security Scan',
                'type': 'security',
                'required': True,
                'severity': 'high',
                'description': 'Security vulnerability scan must pass'
            },
            {
                'name': 'Performance Test',
                'type': 'performance',
                'max_response_time': 200,
                'severity': 'high',
                'description': 'API response time under 200ms'
            }
        ]

    def _calculate_complexity(self, code: str) -> int:
        """计算代码复杂度"""
        # 简化的复杂度计算
        complexity = 1  # 基础复杂度

        # 条件语句增加复杂度
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\belif\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\btry\b', code))
        complexity += len(re.findall(r'\bexcept\b', code))
        complexity += len(re.findall(r'\band\b', code))
        complexity += len(re.findall(r'\bor\b', code))

        return min(complexity, 20)  # 最大复杂度限制为20

    def _calculate_maintainability(self, code: str) -> float:
        """计算可维护性分数"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return 10.0

        # 基于多个因素计算可维护性
        factors = {
            'avg_line_length': min(10, 100 / (sum(len(line) for line in non_empty_lines) / len(non_empty_lines))),
            'comment_ratio': min(10, len([line for line in lines if line.strip().startswith('#')]) / len(non_empty_lines) * 50),
            'function_count': min(10, len(re.findall(r'\bdef\b', code)) * 2),
            'complexity_penalty': max(0, 10 - self._calculate_complexity(code) * 0.5)
        }

        return round(sum(factors.values()) / len(factors), 2)

    def _calculate_readability(self, code: str) -> float:
        """计算可读性分数"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return 10.0

        # 基于命名、注释、格式等计算可读性
        factors = {
            'naming_quality': self._assess_naming_quality(code),
            'indentation_consistency': self._assess_indentation(non_empty_lines),
            'comment_quality': self._assess_comments(lines),
            'line_length': self._assess_line_length(non_empty_lines)
        }

        return round(sum(factors.values()) / len(factors), 2)

    def _detect_security_issues(self, code: str) -> List[str]:
        """检测安全问题"""
        issues = []

        # 简单的安全模式检测
        if 'eval(' in code:
            issues.append('Use of eval() function detected')
        if 'exec(' in code:
            issues.append('Use of exec() function detected')
        if 'shell=True' in code:
            issues.append('Shell injection risk detected')
        if re.search(r'password\s*=\s*["\'].*["\']', code, re.IGNORECASE):
            issues.append('Hardcoded password detected')
        if 'import os' in code and 'os.system' in code:
            issues.append('Direct OS command execution detected')

        return issues

    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if metrics['complexity_score'] > 10:
            recommendations.append('考虑重构复杂函数，拆分为更小的函数')

        if metrics['line_count'] > 100:
            recommendations.append('文件过长，考虑拆分为多个模块')

        if metrics['maintainability_score'] < 7:
            recommendations.append('增加注释，改善变量命名，提高代码可维护性')

        if metrics['readability_score'] < 7:
            recommendations.append('改善代码格式，使用更清晰的变量名')

        if metrics['security_issues']:
            recommendations.append('修复检测到的安全问题')

        return recommendations

    def _assess_naming_quality(self, code: str) -> float:
        """评估命名质量"""
        # 简化的命名质量评估
        variables = re.findall(r'\b[a-z_][a-z0-9_]*\b', code.lower())
        if not variables:
            return 10.0

        # 检查有意义的命名
        meaningful_names = [var for var in variables if len(var) > 2 and var not in ['for', 'if', 'in', 'or', 'and']]
        ratio = len(meaningful_names) / len(variables) if variables else 1

        return min(10, ratio * 10)

    def _assess_indentation(self, lines: List[str]) -> float:
        """评估缩进一致性"""
        if not lines:
            return 10.0

        indentations = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if not indentations:
            return 10.0

        # 检查缩进是否为4的倍数（Python标准）
        consistent_indents = [indent for indent in indentations if indent % 4 == 0]
        ratio = len(consistent_indents) / len(indentations)

        return min(10, ratio * 10)

    def _assess_comments(self, lines: List[str]) -> float:
        """评估注释质量"""
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])

        if total_lines == 0:
            return 10.0

        comment_ratio = comment_lines / total_lines
        # 理想的注释比例是10-30%
        if 0.1 <= comment_ratio <= 0.3:
            return 10.0
        elif comment_ratio < 0.1:
            return max(0, comment_ratio * 50)  # 注释太少
        else:
            return max(0, 10 - (comment_ratio - 0.3) * 20)  # 注释太多

    def _assess_line_length(self, lines: List[str]) -> float:
        """评估行长度"""
        if not lines:
            return 10.0

        long_lines = [line for line in lines if len(line) > 80]
        ratio = 1 - (len(long_lines) / len(lines))

        return min(10, ratio * 10)

    def _get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 9:
            return 'A+'
        elif score >= 8:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 6:
            return 'C'
        elif score >= 5:
            return 'D'
        else:
            return 'F'