# Code Quality Checker - Architecture Design Plan

## 1. Project Overview

### Purpose
A CLI tool for analyzing code quality of Python and Shell scripts, detecting complexity issues, and enforcing naming conventions.

### Key Features
- **Complexity Detection**: Line count, nesting depth, cyclomatic complexity
- **Naming Convention Checks**: Function/variable naming standards
- **Multi-format Output**: JSON and Markdown reports
- **Configurable Rules**: Custom rules via YAML configuration

### Technology Stack
- **Language**: Python 3.8+
- **Parsing**: Regular expressions + AST for Python
- **Configuration**: PyYAML
- **Testing**: pytest
- **CLI Framework**: argparse
- **Shell Integration**: Bash wrapper script

---

## 2. Directory Structure

```
tools/code_quality_checker/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py         # Abstract base parser
│   │   ├── python_parser.py       # Python code parser
│   │   └── shell_parser.py        # Shell script parser
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── base_checker.py        # Abstract base checker
│   │   ├── complexity_checker.py  # Complexity analysis
│   │   └── naming_checker.py      # Naming convention checks
│   ├── reporters/
│   │   ├── __init__.py
│   │   ├── base_reporter.py       # Abstract base reporter
│   │   ├── json_reporter.py       # JSON output
│   │   └── markdown_reporter.py   # Markdown output
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py       # Load and validate rules.yml
│       ├── file_scanner.py        # Scan directories for target files
│       └── rule_engine.py         # Rule evaluation logic
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_parsers.py
│   │   ├── test_checkers.py
│   │   └── test_reporters.py
│   ├── integration/
│   │   └── test_e2e_workflow.py
│   └── fixtures/
│       ├── sample_python.py       # Test Python files
│       ├── sample_shell.sh        # Test shell files
│       └── test_rules.yml         # Test configuration
├── config/
│   ├── default_rules.yml          # Default quality rules
│   └── rules_schema.json          # JSON schema for validation
├── docs/
│   ├── ARCHITECTURE.md            # This document
│   ├── USER_GUIDE.md              # Usage instructions
│   └── API_REFERENCE.md           # Module API docs
├── scripts/
│   └── check_code_quality.sh      # Bash wrapper script
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # Quick start guide
```

---

## 3. Core Module Architecture

### 3.1 Parsers Module (`src/parsers/`)

**Purpose**: Extract structural information from source files.

#### Base Parser Interface
```python
# base_parser.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CodeElement:
    """Represents a parsed code element (function, class, etc.)"""
    type: str           # 'function', 'class', 'method'
    name: str
    start_line: int
    end_line: int
    params: List[str]
    nesting_depth: int
    raw_code: str

class BaseParser(ABC):
    """Abstract base class for all parsers"""

    @abstractmethod
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse a file and return structured data"""
        pass

    @abstractmethod
    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions"""
        pass

    @abstractmethod
    def extract_variables(self, content: str) -> List[str]:
        """Extract variable names"""
        pass

    def count_lines(self, content: str) -> Dict[str, int]:
        """Count total/code/comment lines"""
        lines = content.split('\n')
        return {
            'total': len(lines),
            'code': self._count_code_lines(lines),
            'comments': self._count_comment_lines(lines)
        }

    @abstractmethod
    def _count_code_lines(self, lines: List[str]) -> int:
        pass

    @abstractmethod
    def _count_comment_lines(self, lines: List[str]) -> int:
        pass
```

#### Python Parser
```python
# python_parser.py
import ast
import re
from typing import List, Dict, Any

class PythonParser(BaseParser):
    """Parser for Python files using AST and regex"""

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse Python file using AST"""
        with open(filepath, 'r') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {'error': str(e), 'functions': [], 'variables': []}

        return {
            'filepath': filepath,
            'language': 'python',
            'functions': self.extract_functions(content),
            'variables': self.extract_variables(content),
            'line_counts': self.count_lines(content)
        }

    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract function definitions using AST"""
        tree = ast.parse(content)
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(CodeElement(
                    type='function',
                    name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    params=[arg.arg for arg in node.args.args],
                    nesting_depth=self._calculate_nesting_depth(node),
                    raw_code=ast.get_source_segment(content, node)
                ))

        return functions

    def extract_variables(self, content: str) -> List[str]:
        """Extract variable names using regex"""
        # Pattern: variable_name = value
        pattern = r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*='
        variables = []

        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                variables.append(match.group(2))

        return list(set(variables))  # Remove duplicates

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in a function"""
        depth = 0
        max_depth = 0

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                depth += 1
                max_depth = max(max_depth, depth)

        return max_depth

    def _count_code_lines(self, lines: List[str]) -> int:
        """Count non-empty, non-comment lines"""
        return sum(1 for line in lines
                   if line.strip() and not line.strip().startswith('#'))

    def _count_comment_lines(self, lines: List[str]) -> int:
        """Count comment lines"""
        return sum(1 for line in lines if line.strip().startswith('#'))
```

#### Shell Parser
```python
# shell_parser.py
import re
from typing import List, Dict, Any

class ShellParser(BaseParser):
    """Parser for Shell scripts using regex"""

    FUNCTION_PATTERN = r'^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)\s*\{'
    VARIABLE_PATTERN = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)='

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse shell script file"""
        with open(filepath, 'r') as f:
            content = f.read()

        return {
            'filepath': filepath,
            'language': 'shell',
            'functions': self.extract_functions(content),
            'variables': self.extract_variables(content),
            'line_counts': self.count_lines(content)
        }

    def extract_functions(self, content: str) -> List[CodeElement]:
        """Extract shell function definitions"""
        functions = []
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            match = re.match(self.FUNCTION_PATTERN, lines[i])
            if match:
                func_name = match.group(1)
                start_line = i + 1
                end_line = self._find_function_end(lines, i)

                functions.append(CodeElement(
                    type='function',
                    name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    params=[],  # Shell functions don't have explicit params
                    nesting_depth=self._calculate_nesting_depth_shell(
                        '\n'.join(lines[start_line:end_line])
                    ),
                    raw_code='\n'.join(lines[start_line-1:end_line])
                ))
            i += 1

        return functions

    def extract_variables(self, content: str) -> List[str]:
        """Extract variable assignments"""
        variables = []
        for line in content.split('\n'):
            match = re.match(self.VARIABLE_PATTERN, line)
            if match:
                variables.append(match.group(1))
        return list(set(variables))

    def _find_function_end(self, lines: List[str], start_idx: int) -> int:
        """Find the closing brace of a function"""
        brace_count = 0
        for i in range(start_idx, len(lines)):
            brace_count += lines[i].count('{') - lines[i].count('}')
            if brace_count == 0 and '{' in lines[start_idx]:
                return i + 1
        return len(lines)

    def _calculate_nesting_depth_shell(self, code: str) -> int:
        """Calculate nesting depth for shell code"""
        depth = 0
        max_depth = 0

        for line in code.split('\n'):
            if re.search(r'\b(if|for|while|case)\b', line):
                depth += 1
                max_depth = max(max_depth, depth)
            if re.search(r'\b(fi|done|esac)\b', line):
                depth -= 1

        return max_depth

    def _count_code_lines(self, lines: List[str]) -> int:
        return sum(1 for line in lines
                   if line.strip() and not line.strip().startswith('#'))

    def _count_comment_lines(self, lines: List[str]) -> int:
        return sum(1 for line in lines if line.strip().startswith('#'))
```

---

### 3.2 Checkers Module (`src/checkers/`)

**Purpose**: Apply quality rules to parsed code.

#### Base Checker Interface
```python
# base_checker.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CheckResult:
    """Result of a quality check"""
    rule_id: str
    severity: str      # 'error', 'warning', 'info'
    message: str
    location: Dict[str, Any]  # {'file': str, 'line': int, 'element': str}
    suggestion: str

class BaseChecker(ABC):
    """Abstract base class for all checkers"""

    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules

    @abstractmethod
    def check(self, parsed_data: Dict[str, Any]) -> List[CheckResult]:
        """Run checks on parsed data"""
        pass

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled in configuration"""
        return self.rules.get(rule_id, {}).get('enabled', True)

    def get_rule_threshold(self, rule_id: str, default: Any) -> Any:
        """Get threshold value for a rule"""
        return self.rules.get(rule_id, {}).get('threshold', default)
```

#### Complexity Checker
```python
# complexity_checker.py
from typing import List, Dict, Any

class ComplexityChecker(BaseChecker):
    """Check code complexity metrics"""

    DEFAULT_RULES = {
        'max_function_lines': {'enabled': True, 'threshold': 150},
        'max_nesting_depth': {'enabled': True, 'threshold': 4},
        'max_file_lines': {'enabled': True, 'threshold': 500},
        'min_comment_ratio': {'enabled': True, 'threshold': 0.1}
    }

    def check(self, parsed_data: Dict[str, Any]) -> List[CheckResult]:
        """Run complexity checks"""
        results = []

        # Check file length
        if self.is_rule_enabled('max_file_lines'):
            results.extend(self._check_file_length(parsed_data))

        # Check function complexity
        if self.is_rule_enabled('max_function_lines'):
            results.extend(self._check_function_length(parsed_data))

        # Check nesting depth
        if self.is_rule_enabled('max_nesting_depth'):
            results.extend(self._check_nesting_depth(parsed_data))

        # Check comment ratio
        if self.is_rule_enabled('min_comment_ratio'):
            results.extend(self._check_comment_ratio(parsed_data))

        return results

    def _check_file_length(self, data: Dict[str, Any]) -> List[CheckResult]:
        """Check if file is too long"""
        max_lines = self.get_rule_threshold('max_file_lines', 500)
        total_lines = data['line_counts']['total']

        if total_lines > max_lines:
            return [CheckResult(
                rule_id='max_file_lines',
                severity='warning',
                message=f'File has {total_lines} lines (max: {max_lines})',
                location={'file': data['filepath'], 'line': 1},
                suggestion=f'Consider splitting into smaller modules'
            )]
        return []

    def _check_function_length(self, data: Dict[str, Any]) -> List[CheckResult]:
        """Check if functions are too long"""
        max_lines = self.get_rule_threshold('max_function_lines', 150)
        results = []

        for func in data['functions']:
            func_lines = func.end_line - func.start_line + 1
            if func_lines > max_lines:
                results.append(CheckResult(
                    rule_id='max_function_lines',
                    severity='error',
                    message=f'Function "{func.name}" has {func_lines} lines (max: {max_lines})',
                    location={
                        'file': data['filepath'],
                        'line': func.start_line,
                        'element': func.name
                    },
                    suggestion=f'Break down into smaller functions'
                ))

        return results

    def _check_nesting_depth(self, data: Dict[str, Any]) -> List[CheckResult]:
        """Check if nesting is too deep"""
        max_depth = self.get_rule_threshold('max_nesting_depth', 4)
        results = []

        for func in data['functions']:
            if func.nesting_depth > max_depth:
                results.append(CheckResult(
                    rule_id='max_nesting_depth',
                    severity='warning',
                    message=f'Function "{func.name}" has nesting depth {func.nesting_depth} (max: {max_depth})',
                    location={
                        'file': data['filepath'],
                        'line': func.start_line,
                        'element': func.name
                    },
                    suggestion='Reduce nesting by extracting logic or using early returns'
                ))

        return results

    def _check_comment_ratio(self, data: Dict[str, Any]) -> List[CheckResult]:
        """Check if code has enough comments"""
        min_ratio = self.get_rule_threshold('min_comment_ratio', 0.1)
        counts = data['line_counts']

        if counts['code'] == 0:
            return []

        ratio = counts['comments'] / counts['code']

        if ratio < min_ratio:
            return [CheckResult(
                rule_id='min_comment_ratio',
                severity='info',
                message=f'Comment ratio {ratio:.2%} is below minimum {min_ratio:.2%}',
                location={'file': data['filepath'], 'line': 1},
                suggestion='Add more comments to explain complex logic'
            )]
        return []
```

#### Naming Checker
```python
# naming_checker.py
import re
from typing import List, Dict, Any

class NamingChecker(BaseChecker):
    """Check naming conventions"""

    DEFAULT_RULES = {
        'python_function_naming': {
            'enabled': True,
            'pattern': r'^[a-z_][a-z0-9_]*$',
            'description': 'snake_case for functions'
        },
        'python_variable_naming': {
            'enabled': True,
            'pattern': r'^[a-z_][a-z0-9_]*$',
            'description': 'snake_case for variables'
        },
        'shell_function_naming': {
            'enabled': True,
            'pattern': r'^[a-z_][a-z0-9_]*$',
            'description': 'snake_case for shell functions'
        },
        'avoid_single_char_names': {
            'enabled': True,
            'exceptions': ['i', 'j', 'k', 'x', 'y', 'z']
        }
    }

    def check(self, parsed_data: Dict[str, Any]) -> List[CheckResult]:
        """Run naming convention checks"""
        results = []
        language = parsed_data['language']

        # Check function naming
        if language == 'python' and self.is_rule_enabled('python_function_naming'):
            results.extend(self._check_function_naming(parsed_data, 'python_function_naming'))
        elif language == 'shell' and self.is_rule_enabled('shell_function_naming'):
            results.extend(self._check_function_naming(parsed_data, 'shell_function_naming'))

        # Check variable naming
        if language == 'python' and self.is_rule_enabled('python_variable_naming'):
            results.extend(self._check_variable_naming(parsed_data, 'python_variable_naming'))

        # Check for single-character names
        if self.is_rule_enabled('avoid_single_char_names'):
            results.extend(self._check_single_char_names(parsed_data))

        return results

    def _check_function_naming(self, data: Dict[str, Any], rule_id: str) -> List[CheckResult]:
        """Check if function names match pattern"""
        pattern = self.rules.get(rule_id, {}).get('pattern', r'.*')
        description = self.rules.get(rule_id, {}).get('description', 'naming convention')
        results = []

        for func in data['functions']:
            if not re.match(pattern, func.name):
                results.append(CheckResult(
                    rule_id=rule_id,
                    severity='warning',
                    message=f'Function "{func.name}" does not match {description}',
                    location={
                        'file': data['filepath'],
                        'line': func.start_line,
                        'element': func.name
                    },
                    suggestion=f'Rename to match pattern: {pattern}'
                ))

        return results

    def _check_variable_naming(self, data: Dict[str, Any], rule_id: str) -> List[CheckResult]:
        """Check if variable names match pattern"""
        pattern = self.rules.get(rule_id, {}).get('pattern', r'.*')
        description = self.rules.get(rule_id, {}).get('description', 'naming convention')
        results = []

        for var in data['variables']:
            if not re.match(pattern, var):
                results.append(CheckResult(
                    rule_id=rule_id,
                    severity='info',
                    message=f'Variable "{var}" does not match {description}',
                    location={'file': data['filepath'], 'line': 0, 'element': var},
                    suggestion=f'Rename to match pattern: {pattern}'
                ))

        return results

    def _check_single_char_names(self, data: Dict[str, Any]) -> List[CheckResult]:
        """Check for single-character names (except common loop vars)"""
        exceptions = self.rules.get('avoid_single_char_names', {}).get('exceptions', [])
        results = []

        for var in data['variables']:
            if len(var) == 1 and var not in exceptions:
                results.append(CheckResult(
                    rule_id='avoid_single_char_names',
                    severity='info',
                    message=f'Single-character variable name "{var}" is not recommended',
                    location={'file': data['filepath'], 'line': 0, 'element': var},
                    suggestion='Use a descriptive name instead'
                ))

        for func in data['functions']:
            if len(func.name) == 1:
                results.append(CheckResult(
                    rule_id='avoid_single_char_names',
                    severity='warning',
                    message=f'Single-character function name "{func.name}" is not allowed',
                    location={
                        'file': data['filepath'],
                        'line': func.start_line,
                        'element': func.name
                    },
                    suggestion='Use a descriptive function name'
                ))

        return results
```

---

### 3.3 Reporters Module (`src/reporters/`)

**Purpose**: Format check results into different output formats.

#### Base Reporter Interface
```python
# base_reporter.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseReporter(ABC):
    """Abstract base class for all reporters"""

    @abstractmethod
    def generate(self, results: List[Dict[str, Any]], output_path: str = None) -> str:
        """Generate report from check results"""
        pass

    def _aggregate_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total = len(results)
        by_severity = {'error': 0, 'warning': 0, 'info': 0}
        by_file = {}

        for result in results:
            severity = result.get('severity', 'info')
            by_severity[severity] = by_severity.get(severity, 0) + 1

            filepath = result.get('location', {}).get('file', 'unknown')
            by_file[filepath] = by_file.get(filepath, 0) + 1

        return {
            'total_issues': total,
            'by_severity': by_severity,
            'by_file': by_file,
            'files_checked': len(by_file)
        }
```

#### JSON Reporter
```python
# json_reporter.py
import json
from typing import List, Dict, Any
from datetime import datetime

class JSONReporter(BaseReporter):
    """Generate JSON format reports"""

    def generate(self, results: List[Dict[str, Any]], output_path: str = None) -> str:
        """Generate JSON report"""
        stats = self._aggregate_stats(results)

        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'tool': 'code_quality_checker',
                'version': '1.0.0'
            },
            'summary': stats,
            'issues': [self._format_result(r) for r in results]
        }

        json_str = json.dumps(report, indent=2)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)

        return json_str

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single check result for JSON"""
        return {
            'rule_id': result.get('rule_id', 'unknown'),
            'severity': result.get('severity', 'info'),
            'message': result.get('message', ''),
            'location': result.get('location', {}),
            'suggestion': result.get('suggestion', '')
        }
```

#### Markdown Reporter
```python
# markdown_reporter.py
from typing import List, Dict, Any
from datetime import datetime

class MarkdownReporter(BaseReporter):
    """Generate Markdown format reports"""

    SEVERITY_EMOJI = {
        'error': '🔴',
        'warning': '⚠️',
        'info': 'ℹ️'
    }

    def generate(self, results: List[Dict[str, Any]], output_path: str = None) -> str:
        """Generate Markdown report"""
        stats = self._aggregate_stats(results)

        lines = [
            '# Code Quality Report',
            '',
            f'**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '',
            '## Summary',
            '',
            f'- **Total Issues**: {stats["total_issues"]}',
            f'- **Errors**: {stats["by_severity"]["error"]}',
            f'- **Warnings**: {stats["by_severity"]["warning"]}',
            f'- **Info**: {stats["by_severity"]["info"]}',
            f'- **Files Checked**: {stats["files_checked"]}',
            '',
            '## Issues by File',
            ''
        ]

        # Group by file
        by_file = self._group_by_file(results)

        for filepath, file_results in sorted(by_file.items()):
            lines.append(f'### `{filepath}`')
            lines.append('')

            for result in file_results:
                emoji = self.SEVERITY_EMOJI.get(result.get('severity', 'info'), '•')
                rule = result.get('rule_id', 'unknown')
                msg = result.get('message', '')
                loc = result.get('location', {})
                line_num = loc.get('line', '?')
                suggestion = result.get('suggestion', '')

                lines.append(f'{emoji} **[{rule}]** (line {line_num})')
                lines.append(f'  - {msg}')
                if suggestion:
                    lines.append(f'  - *Suggestion*: {suggestion}')
                lines.append('')

        markdown = '\n'.join(lines)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(markdown)

        return markdown

    def _group_by_file(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group results by file"""
        by_file = {}
        for result in results:
            filepath = result.get('location', {}).get('file', 'unknown')
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(result)
        return by_file
```

---

### 3.4 Utils Module (`src/utils/`)

#### Config Loader
```python
# config_loader.py
import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    """Load and validate configuration files"""

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / 'config' / 'default_rules.yml'

    @classmethod
    def load(cls, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        path = Path(config_path) if config_path else cls.DEFAULT_CONFIG_PATH

        if not path.exists():
            raise FileNotFoundError(f'Config file not found: {path}')

        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        return cls._merge_with_defaults(config)

    @classmethod
    def _merge_with_defaults(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
        # Implementation would merge complexity and naming defaults
        # with user-provided overrides
        return config
```

#### File Scanner
```python
# file_scanner.py
from pathlib import Path
from typing import List

class FileScanner:
    """Scan directories for Python and Shell files"""

    PYTHON_EXTENSIONS = {'.py'}
    SHELL_EXTENSIONS = {'.sh', '.bash'}

    @classmethod
    def scan(cls, target_path: str, recursive: bool = True) -> Dict[str, List[Path]]:
        """Scan for code files"""
        path = Path(target_path)

        if not path.exists():
            raise FileNotFoundError(f'Path not found: {target_path}')

        results = {'python': [], 'shell': []}

        if path.is_file():
            cls._classify_file(path, results)
        elif path.is_dir():
            pattern = '**/*' if recursive else '*'
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    cls._classify_file(file_path, results)

        return results

    @classmethod
    def _classify_file(cls, file_path: Path, results: Dict[str, List[Path]]):
        """Classify file by extension"""
        if file_path.suffix in cls.PYTHON_EXTENSIONS:
            results['python'].append(file_path)
        elif file_path.suffix in cls.SHELL_EXTENSIONS:
            results['shell'].append(file_path)
```

---

### 3.5 Main CLI (`src/main.py`)

```python
# main.py
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

from parsers.python_parser import PythonParser
from parsers.shell_parser import ShellParser
from checkers.complexity_checker import ComplexityChecker
from checkers.naming_checker import NamingChecker
from reporters.json_reporter import JSONReporter
from reporters.markdown_reporter import MarkdownReporter
from utils.config_loader import ConfigLoader
from utils.file_scanner import FileScanner

class CodeQualityChecker:
    """Main orchestrator for code quality checking"""

    def __init__(self, config_path: str = None):
        self.config = ConfigLoader.load(config_path)
        self.parsers = {
            'python': PythonParser(),
            'shell': ShellParser()
        }
        self.checkers = [
            ComplexityChecker(self.config.get('complexity', {})),
            NamingChecker(self.config.get('naming', {}))
        ]
        self.reporters = {
            'json': JSONReporter(),
            'markdown': MarkdownReporter()
        }

    def analyze(self, target_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """Analyze code quality for given path"""
        # Scan for files
        files = FileScanner.scan(target_path, recursive)

        all_results = []

        # Parse Python files
        for py_file in files['python']:
            parsed = self.parsers['python'].parse_file(str(py_file))
            for checker in self.checkers:
                results = checker.check(parsed)
                all_results.extend([vars(r) for r in results])

        # Parse Shell files
        for sh_file in files['shell']:
            parsed = self.parsers['shell'].parse_file(str(sh_file))
            for checker in self.checkers:
                results = checker.check(parsed)
                all_results.extend([vars(r) for r in results])

        return all_results

    def generate_report(self, results: List[Dict[str, Any]],
                       format: str = 'markdown',
                       output_path: str = None) -> str:
        """Generate report in specified format"""
        reporter = self.reporters.get(format)
        if not reporter:
            raise ValueError(f'Unsupported format: {format}')

        return reporter.generate(results, output_path)

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Code Quality Checker for Python and Shell scripts'
    )
    parser.add_argument('target', help='File or directory to analyze')
    parser.add_argument('-c', '--config', help='Path to rules.yml config file')
    parser.add_argument('-f', '--format', choices=['json', 'markdown'],
                       default='markdown', help='Output format')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-r', '--recursive', action='store_true',
                       default=True, help='Recursively scan directories')
    parser.add_argument('--no-recursive', dest='recursive',
                       action='store_false', help='Don\'t scan recursively')

    args = parser.parse_args()

    try:
        checker = CodeQualityChecker(args.config)
        results = checker.analyze(args.target, args.recursive)
        report = checker.generate_report(results, args.format, args.output)

        if not args.output:
            print(report)

        # Exit with error code if issues found
        error_count = sum(1 for r in results if r.get('severity') == 'error')
        sys.exit(1 if error_count > 0 else 0)

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
```

---

## 4. Configuration File Schema

### Default Rules YAML (`config/default_rules.yml`)

```yaml
# Code Quality Rules Configuration

version: "1.0"

complexity:
  max_function_lines:
    enabled: true
    threshold: 150
    severity: error
    description: "Maximum lines per function"

  max_nesting_depth:
    enabled: true
    threshold: 4
    severity: warning
    description: "Maximum nesting depth for control structures"

  max_file_lines:
    enabled: true
    threshold: 500
    severity: warning
    description: "Maximum lines per file"

  min_comment_ratio:
    enabled: true
    threshold: 0.1  # 10% of code lines should be comments
    severity: info
    description: "Minimum ratio of comments to code"

naming:
  python_function_naming:
    enabled: true
    pattern: "^[a-z_][a-z0-9_]*$"
    severity: warning
    description: "Python functions should use snake_case"

  python_variable_naming:
    enabled: true
    pattern: "^[a-z_][a-z0-9_]*$"
    severity: info
    description: "Python variables should use snake_case"

  shell_function_naming:
    enabled: true
    pattern: "^[a-z_][a-z0-9_]*$"
    severity: warning
    description: "Shell functions should use snake_case"

  avoid_single_char_names:
    enabled: true
    severity: info
    exceptions: ["i", "j", "k", "x", "y", "z"]
    description: "Avoid single-character names except loop counters"

# File exclusions
exclude_patterns:
  - "*/node_modules/*"
  - "*/.git/*"
  - "*/venv/*"
  - "*/__pycache__/*"
  - "*/dist/*"
  - "*/build/*"
```

### Rules Schema JSON (`config/rules_schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Code Quality Rules Schema",
  "type": "object",
  "required": ["version"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+$"
    },
    "complexity": {
      "type": "object",
      "properties": {
        "max_function_lines": {"$ref": "#/definitions/numericRule"},
        "max_nesting_depth": {"$ref": "#/definitions/numericRule"},
        "max_file_lines": {"$ref": "#/definitions/numericRule"},
        "min_comment_ratio": {"$ref": "#/definitions/numericRule"}
      }
    },
    "naming": {
      "type": "object",
      "properties": {
        "python_function_naming": {"$ref": "#/definitions/patternRule"},
        "python_variable_naming": {"$ref": "#/definitions/patternRule"},
        "shell_function_naming": {"$ref": "#/definitions/patternRule"},
        "avoid_single_char_names": {"$ref": "#/definitions/exceptionRule"}
      }
    },
    "exclude_patterns": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "definitions": {
    "numericRule": {
      "type": "object",
      "required": ["enabled", "threshold"],
      "properties": {
        "enabled": {"type": "boolean"},
        "threshold": {"type": "number"},
        "severity": {"enum": ["error", "warning", "info"]},
        "description": {"type": "string"}
      }
    },
    "patternRule": {
      "type": "object",
      "required": ["enabled", "pattern"],
      "properties": {
        "enabled": {"type": "boolean"},
        "pattern": {"type": "string", "format": "regex"},
        "severity": {"enum": ["error", "warning", "info"]},
        "description": {"type": "string"}
      }
    },
    "exceptionRule": {
      "type": "object",
      "required": ["enabled"],
      "properties": {
        "enabled": {"type": "boolean"},
        "severity": {"enum": ["error", "warning", "info"]},
        "exceptions": {
          "type": "array",
          "items": {"type": "string"}
        },
        "description": {"type": "string"}
      }
    }
  }
}
```

---

## 5. Shell Wrapper Script

### `scripts/check_code_quality.sh`

```bash
#!/usr/bin/env bash
# Code Quality Checker Bash Wrapper

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/src/main.py"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found" >&2
    exit 1
fi

# Check if virtual environment exists
VENV_PATH="$PROJECT_ROOT/venv"
if [[ ! -d "$VENV_PATH" ]]; then
    echo "Warning: Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    source "$VENV_PATH/bin/activate"
fi

# Run the Python script with all arguments
python3 "$PYTHON_SCRIPT" "$@"

# Exit with the same code as Python script
exit $?
```

---

## 6. Dependencies (`requirements.txt`)

```
PyYAML>=6.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## 7. Testing Strategy

### Unit Tests

**`tests/unit/test_parsers.py`**:
- Test Python parser with valid/invalid syntax
- Test Shell parser with various function formats
- Test line counting accuracy
- Test nesting depth calculation

**`tests/unit/test_checkers.py`**:
- Test complexity checker thresholds
- Test naming pattern matching
- Test rule enable/disable logic
- Test edge cases (empty files, no functions, etc.)

**`tests/unit/test_reporters.py`**:
- Test JSON format output
- Test Markdown format output
- Test statistics aggregation
- Test file grouping

### Integration Tests

**`tests/integration/test_e2e_workflow.py`**:
- Test complete workflow from file scan to report
- Test with mixed Python and Shell files
- Test custom configuration loading
- Test CLI argument parsing

### Test Fixtures

**`tests/fixtures/sample_python.py`**:
```python
# Good code
def calculate_sum(numbers):
    """Calculate sum of numbers."""
    return sum(numbers)

# Bad code - too long, bad naming
def x():
    # Simulate a very long function
    pass  # ... 200 lines ...
```

**`tests/fixtures/sample_shell.sh`**:
```bash
# Good function
calculate_total() {
    local sum=0
    for num in "$@"; do
        sum=$((sum + num))
    done
    echo "$sum"
}

# Bad function - deep nesting
process_data() {
    if [ -f "$1" ]; then
        if [ -r "$1" ]; then
            if grep -q "pattern" "$1"; then
                if [ -w "$1" ]; then
                    if [ -x "$1" ]; then
                        # Too deep!
                        echo "nested"
                    fi
                fi
            fi
        fi
    fi
}
```

---

## 8. Success Metrics

### Phase 0 Acceptance Checklist

- [ ] Architecture design completed and documented
- [ ] Directory structure created
- [ ] Core module interfaces defined
- [ ] Configuration schema designed
- [ ] Testing strategy planned
- [ ] All dependencies identified
- [ ] PLAN.md document generated
- [ ] Ready for Phase 1 implementation

### Quality Goals

- **Code Coverage**: ≥80%
- **Performance**: Process 100 files < 5 seconds
- **Accuracy**:
  - Complexity detection: 100% accurate for known patterns
  - Naming checks: 95% accuracy (regex-based)
- **Usability**: Single command execution via shell wrapper

---

## 9. Future Enhancements

### Phase 1 Enhancements (Not in Scope)
- Cyclomatic complexity calculation (requires AST analysis)
- Class complexity metrics
- Import dependency analysis
- Dead code detection

### Phase 2 Enhancements
- Plugin system for custom checkers
- IDE integration (VSCode extension)
- Git pre-commit hook integration
- HTML report format with charts

### Phase 3 Enhancements
- Support for more languages (JavaScript, Go, etc.)
- Machine learning-based code smell detection
- Historical trend analysis
- Team collaboration features

---

## 10. Implementation Roadmap

### Phase 1: Planning & Architecture (Current)
- ✅ Design directory structure
- ✅ Define module interfaces
- ✅ Create configuration schema
- ✅ Plan testing strategy
- ✅ Document architecture

### Phase 2: Implementation
- Implement parsers (Python, Shell)
- Implement checkers (Complexity, Naming)
- Implement reporters (JSON, Markdown)
- Implement utils (Config, Scanner)
- Implement main CLI

### Phase 3: Testing
- Write unit tests for all modules
- Write integration tests
- Create test fixtures
- Achieve 80% coverage
- Run static_checks.sh

### Phase 4: Review
- Code review for consistency
- Run pre_merge_audit.sh
- Verify against Phase 0 checklist
- Generate REVIEW.md

### Phase 5: Release & Monitor
- Update documentation
- Create usage examples
- Package for distribution
- Set up monitoring (if applicable)

---

## 11. Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Regex parsing limitations | Medium | Use AST for Python, accept limitations for Shell |
| Performance with large codebases | Medium | Implement file filtering, parallel processing |
| Configuration complexity | Low | Provide sensible defaults, clear examples |
| Shell script parsing edge cases | Medium | Focus on common patterns, document limitations |

### Dependency Risks

| Dependency | Risk | Mitigation |
|------------|------|-----------|
| PyYAML | Low | Stable, widely used |
| Python 3.8+ | Low | Industry standard |
| Bash 4.0+ | Low | Available on all target platforms |

---

## 12. Deliverables

### Code Deliverables
1. Complete source code in `tools/code_quality_checker/src/`
2. Comprehensive test suite in `tests/`
3. Configuration files in `config/`
4. Wrapper script in `scripts/`

### Documentation Deliverables
1. PLAN.md (this document)
2. README.md (user-facing quick start)
3. USER_GUIDE.md (detailed usage)
4. API_REFERENCE.md (module documentation)
5. ARCHITECTURE.md (technical details)

### Testing Deliverables
1. Unit test suite with ≥80% coverage
2. Integration test suite
3. Test fixtures and sample files
4. Test execution reports

---

**End of Architecture Plan**
