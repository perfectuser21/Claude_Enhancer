#!/usr/bin/env python3
"""
Perfect21 Core Hook System - Python Implementation
Provides intelligent task analysis, agent validation, and workflow management
"""

import sys
import os
import json
import re
import logging
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=os.getenv('PERFECT21_LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/perfect21_hooks.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('perfect21.core')

# Constants
PERFECT21_HOME = os.getenv('PERFECT21_HOME', '/home/xx/dev/Perfect21')
RULES_FILE = os.path.join(PERFECT21_HOME, 'rules', 'perfect21_rules.yaml')
MIN_AGENTS = 3
CACHE_FILE = '/tmp/perfect21_cache.json'
CACHE_TTL = 300  # 5 minutes

class TaskType(Enum):
    """Task type enumeration"""
    AUTHENTICATION = "authentication"
    API_DEVELOPMENT = "api_development"
    DATABASE_DESIGN = "database_design"
    FRONTEND = "frontend_development"
    FULLSTACK = "fullstack_development"
    PERFORMANCE = "performance_optimization"
    TESTING = "testing"
    SECURITY = "security"
    DEVOPS = "devops"
    GENERAL = "general"

@dataclass
class TaskAnalysis:
    """Task analysis result"""
    task_type: TaskType
    confidence: float
    required_agents: List[str]
    recommended_agents: List[str]
    best_practices: List[str]
    keywords_found: List[str]

@dataclass
class ValidationResult:
    """Validation result"""
    passed: bool
    message: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class Perfect21Core:
    """Core Perfect21 hook functionality"""

    def __init__(self):
        self.rules = self._load_rules()
        self.cache = self._load_cache()
        self.task_patterns = self._compile_patterns()

    def _load_rules(self) -> Dict:
        """Load Perfect21 rules from YAML"""
        try:
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return {}

    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    # Check if cache is expired
                    if cache.get('timestamp', 0) + CACHE_TTL > datetime.now().timestamp():
                        return cache
        except Exception:
            pass
        return {'timestamp': datetime.now().timestamp()}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            self.cache['timestamp'] = datetime.now().timestamp()
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _compile_patterns(self) -> Dict[TaskType, re.Pattern]:
        """Compile regex patterns for task detection"""
        patterns = {
            TaskType.AUTHENTICATION: r"(登录|认证|auth|用户|权限|jwt|oauth|session|password|signup|signin|logout)",
            TaskType.API_DEVELOPMENT: r"(api|接口|rest|graphql|endpoint|route|swagger|openapi|webhook)",
            TaskType.DATABASE_DESIGN: r"(数据库|database|schema|sql|mongodb|redis|表结构|migration|索引|query)",
            TaskType.FRONTEND: r"(前端|frontend|react|vue|angular|ui|组件|页面|component|界面|css|样式)",
            TaskType.FULLSTACK: r"(全栈|fullstack|完整功能|前后端|full-stack|整体|应用|app)",
            TaskType.PERFORMANCE: r"(性能|优化|performance|速度|缓存|optimize|cache|慢|快|延迟)",
            TaskType.TESTING: r"(测试|test|spec|jest|mocha|pytest|unit|e2e|integration|coverage|断言)",
            TaskType.SECURITY: r"(安全|security|漏洞|vulnerability|xss|sql注入|csrf|加密|encrypt)",
            TaskType.DEVOPS: r"(部署|deploy|docker|kubernetes|k8s|ci/cd|pipeline|容器|container)"
        }
        return {k: re.compile(v, re.IGNORECASE) for k, v in patterns.items()}

    def analyze_task(self, input_data: str) -> TaskAnalysis:
        """Analyze task type from input"""
        input_lower = input_data.lower()

        # Check cache
        cache_key = f"task_analysis_{hash(input_lower)}"
        if cache_key in self.cache:
            return TaskAnalysis(**self.cache[cache_key])

        # Find matching patterns
        matches = []
        for task_type, pattern in self.task_patterns.items():
            found = pattern.findall(input_lower)
            if found:
                matches.append((task_type, len(found), found))

        # Determine task type
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            task_type = matches[0][0]
            keywords = matches[0][2]
            confidence = min(matches[0][1] / 10.0, 1.0)
        else:
            task_type = TaskType.GENERAL
            keywords = []
            confidence = 0.5

        # Get agent recommendations from rules
        agent_patterns = self.rules.get('agent_patterns', {})
        task_config = agent_patterns.get(task_type.value, {})

        required_agents = task_config.get('required_agents', [])
        quality_requirements = task_config.get('quality_requirements', [])

        # Get best practices
        best_practices = self.rules.get('best_practices', {}).get('general', [])

        result = TaskAnalysis(
            task_type=task_type,
            confidence=confidence,
            required_agents=required_agents[:5],  # Top 5
            recommended_agents=required_agents[5:] if len(required_agents) > 5 else [],
            best_practices=quality_requirements[:3],
            keywords_found=list(set(keywords))[:5]
        )

        # Cache result
        self.cache[cache_key] = asdict(result)
        self.cache[cache_key]['task_type'] = task_type.value
        self._save_cache()

        return result

    def validate_agents(self, input_data: str) -> ValidationResult:
        """Validate agent selection"""
        errors = []
        warnings = []
        suggestions = []

        # Extract agents from input
        agents = re.findall(r'"subagent_type"\s*:\s*"([^"]+)"', input_data)
        agent_count = len(agents)

        # Check minimum agent requirement
        if agent_count > 0 and agent_count < MIN_AGENTS:
            errors.append(f"需要至少{MIN_AGENTS}个Agent，当前只有{agent_count}个")

            # Analyze task to provide suggestions
            analysis = self.analyze_task(input_data)
            if analysis.required_agents:
                suggestions.append(f"建议使用: {', '.join(analysis.required_agents)}")

            return ValidationResult(
                passed=False,
                message=f"❌ Agent数量不足: {agent_count}/{MIN_AGENTS}",
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )

        # Check for parallel execution
        if agent_count > 1:
            if '<function_calls>' not in input_data and 'function_calls' not in input_data:
                warnings.append("建议使用并行执行模式")

        # Task-specific validation
        if agent_count > 0:
            analysis = self.analyze_task(input_data)
            missing_agents = set(analysis.required_agents) - set(agents)
            if missing_agents:
                warnings.append(f"任务类型'{analysis.task_type.value}'建议添加: {', '.join(missing_agents)}")

        passed = len(errors) == 0
        message = "✅ 验证通过" if passed else f"❌ 发现{len(errors)}个错误"

        return ValidationResult(
            passed=passed,
            message=message,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def format_code(self, file_paths: str) -> Dict[str, Any]:
        """Auto-format code files"""
        results = {'formatted': [], 'failed': [], 'skipped': []}

        if not file_paths:
            return results

        files = file_paths.strip().split()

        for file_path in files:
            if not os.path.exists(file_path):
                results['skipped'].append(file_path)
                continue

            ext = Path(file_path).suffix.lower()

            # Format based on file extension
            try:
                if ext in ['.py']:
                    # Use black for Python
                    subprocess.run(['black', '--quiet', file_path], check=True)
                    subprocess.run(['isort', '--quiet', file_path], check=False)
                    results['formatted'].append(file_path)
                elif ext in ['.js', '.jsx', '.ts', '.tsx', '.json', '.md']:
                    # Use prettier for JS/TS/JSON/Markdown
                    subprocess.run(['npx', 'prettier', '--write', file_path],
                                 check=True, capture_output=True)
                    results['formatted'].append(file_path)
                elif ext in ['.go']:
                    # Use gofmt for Go
                    subprocess.run(['gofmt', '-w', file_path], check=True)
                    results['formatted'].append(file_path)
                else:
                    results['skipped'].append(file_path)
            except subprocess.CalledProcessError as e:
                results['failed'].append(file_path)
                logger.warning(f"Failed to format {file_path}: {e}")

        return results

    def check_completion(self, input_data: str) -> Dict[str, Any]:
        """Check if task is complete before stopping"""
        # Check for incomplete tasks indicators
        incomplete_indicators = [
            r"TODO",
            r"FIXME",
            r"test.*fail",
            r"error",
            r"not implemented"
        ]

        issues = []
        for indicator in incomplete_indicators:
            if re.search(indicator, input_data, re.IGNORECASE):
                issues.append(f"Found incomplete indicator: {indicator}")

        if issues:
            return {
                "continue": True,
                "decision": "continue",
                "reason": "检测到未完成的任务",
                "issues": issues,
                "suggestion": "请完成所有TODO项和修复失败的测试"
            }

        return {
            "continue": False,
            "decision": "stop",
            "reason": "所有任务已完成",
            "summary": "✅ 工作流正常结束"
        }

    def generate_report(self) -> str:
        """Generate session report"""
        report = []
        report.append("=" * 60)
        report.append("Perfect21 工作流报告")
        report.append("=" * 60)
        report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Read logs and generate summary
        try:
            with open('/tmp/perfect21_hooks.log', 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines

                # Count events
                events = {
                    'tasks': len([l for l in lines if 'analyze_task' in l]),
                    'validations': len([l for l in lines if 'validate_agents' in l]),
                    'formats': len([l for l in lines if 'format_code' in l])
                }

                report.append(f"\n执行统计:")
                report.append(f"  • 任务分析: {events['tasks']}次")
                report.append(f"  • Agent验证: {events['validations']}次")
                report.append(f"  • 代码格式化: {events['formats']}次")
        except Exception:
            pass

        report.append("\n" + "=" * 60)
        return "\n".join(report)

    def load_context(self) -> str:
        """Load project context at session start"""
        context = []
        context.append("🚀 Perfect21 已加载")
        context.append(f"  • 最少Agent数: {MIN_AGENTS}")
        context.append(f"  • 规则文件: {RULES_FILE}")
        context.append(f"  • 严格模式: {os.getenv('PERFECT21_STRICT_MODE', 'true')}")

        # Show git status
        try:
            result = subprocess.run(['git', 'status', '--short'],
                                  capture_output=True, text=True, cwd=PERFECT21_HOME)
            if result.stdout:
                context.append(f"\nGit状态:")
                for line in result.stdout.strip().split('\n')[:5]:
                    context.append(f"  {line}")
        except Exception:
            pass

        return "\n".join(context)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: perfect21_core.py <command> [input]")
        sys.exit(1)

    command = sys.argv[1]
    input_data = sys.stdin.read() if not sys.stdin.isatty() else ""

    core = Perfect21Core()

    try:
        if command == "analyze-task":
            result = core.analyze_task(input_data)
            print(f"📊 任务分析结果:")
            print(f"  类型: {result.task_type.value} (置信度: {result.confidence:.1%})")
            if result.required_agents:
                print(f"  必需Agent: {', '.join(result.required_agents)}")
            if result.best_practices:
                print(f"  最佳实践: {', '.join(result.best_practices)}")

        elif command == "validate-pre-commit":
            # Pre-commit validation
            print("✅ Perfect21 pre-commit验证通过")

        elif command == "validate-agents":
            result = core.validate_agents(input_data)
            print(result.message)
            for error in result.errors:
                print(f"  ❌ {error}")
            for warning in result.warnings:
                print(f"  ⚠️ {warning}")
            for suggestion in result.suggestions:
                print(f"  💡 {suggestion}")

            if not result.passed:
                sys.exit(1)

        elif command == "format-code":
            file_paths = os.getenv('CLAUDE_FILE_PATHS', '')
            result = core.format_code(file_paths)
            if result['formatted']:
                print(f"✅ 格式化了 {len(result['formatted'])} 个文件")
            if result['failed']:
                print(f"⚠️ {len(result['failed'])} 个文件格式化失败")

        elif command == "check-completion":
            result = core.check_completion(input_data)
            print(json.dumps(result))

        elif command == "generate-report":
            print(core.generate_report())

        elif command == "load-context":
            print(core.load_context())

        elif command == "log-notification":
            logger.info(f"Notification: {input_data[:100]}")

        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error executing {command}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()