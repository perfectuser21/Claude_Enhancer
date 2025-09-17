#!/usr/bin/env python3
"""
Perfect21与Claude Code耦合点分析
识别紧耦合关系并提出松耦合方案
"""

import os
import re
import ast
import sys
from typing import Dict, List, Set, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CouplingPoint:
    """耦合点"""
    file_path: str
    line_number: int
    coupling_type: str  # 'import', 'call', 'inheritance', 'data_dependency'
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'

class ClaudeCodeCouplingAnalyzer:
    """Claude Code耦合分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.coupling_patterns = {
            'claude_code_direct_call': r'claude_code\.|claude\.code\.',
            'orchestrator_dependency': r'orchestrator\.|Orchestrator\(',
            'subagent_direct_call': r'@[a-zA-Z-]+|Task\(',
            'core_agent_import': r'from core\.claude-code-unified-agents',
            'perfect21_internal': r'from features\.|import features\.',
            'config_dependency': r'from modules\.config|config\.',
            'git_workflow_coupling': r'git_hooks\.|GitHooks\(',
        }

    def analyze_project_coupling(self) -> Dict[str, Any]:
        """分析整个项目的耦合情况"""
        print("🔍 分析Perfect21与Claude Code的耦合关系...")

        coupling_points = []
        file_stats = {}

        # 扫描所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            file_coupling = self.analyze_file_coupling(py_file)
            if file_coupling:
                coupling_points.extend(file_coupling)
                file_stats[str(py_file.relative_to(self.project_root))] = len(file_coupling)

        # 分析耦合程度
        coupling_analysis = self.categorize_coupling(coupling_points)

        # 生成解耦方案
        decoupling_plan = self.generate_decoupling_plan(coupling_analysis)

        return {
            'total_coupling_points': len(coupling_points),
            'files_analyzed': len(file_stats),
            'high_coupling_files': {k: v for k, v in file_stats.items() if v > 5},
            'coupling_by_type': coupling_analysis,
            'decoupling_recommendations': decoupling_plan,
            'detailed_coupling_points': [
                {
                    'file': cp.file_path,
                    'line': cp.line_number,
                    'type': cp.coupling_type,
                    'description': cp.description,
                    'severity': cp.severity
                } for cp in coupling_points
            ]
        }

    def analyze_file_coupling(self, file_path: Path) -> List[CouplingPoint]:
        """分析单个文件的耦合情况"""
        coupling_points = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 分析每一行
            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern in self.coupling_patterns.items():
                    if re.search(pattern, line):
                        severity = self.assess_coupling_severity(pattern_name, line)
                        coupling_points.append(CouplingPoint(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            coupling_type=pattern_name,
                            description=line.strip(),
                            severity=severity
                        ))

            # AST分析 - 检查类继承和函数调用
            try:
                tree = ast.parse(content)
                ast_coupling = self.analyze_ast_coupling(tree, file_path)
                coupling_points.extend(ast_coupling)
            except:
                pass

        except Exception as e:
            print(f"分析文件失败 {file_path}: {e}")

        return coupling_points

    def analyze_ast_coupling(self, tree: ast.AST, file_path: Path) -> List[CouplingPoint]:
        """通过AST分析更深层的耦合"""
        coupling_points = []

        class CouplingVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                # 检查类继承
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        if 'Manager' in base.id or 'Agent' in base.id:
                            coupling_points.append(CouplingPoint(
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=node.lineno,
                                coupling_type='inheritance_coupling',
                                description=f"Class {node.name} inherits from {base.id}",
                                severity='medium'
                            ))
                self.generic_visit(node)

            def visit_Call(self, node):
                # 检查函数调用
                if isinstance(node.func, ast.Attribute):
                    if hasattr(node.func.value, 'id'):
                        if 'claude' in node.func.value.id.lower():
                            coupling_points.append(CouplingPoint(
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=node.lineno,
                                coupling_type='claude_code_call',
                                description=f"Direct Claude Code call: {node.func.value.id}.{node.func.attr}",
                                severity='high'
                            ))
                self.generic_visit(node)

        visitor = CouplingVisitor()
        visitor.visit(tree)

        return coupling_points

    def assess_coupling_severity(self, pattern_name: str, line: str) -> str:
        """评估耦合严重程度"""
        severity_map = {
            'claude_code_direct_call': 'critical',
            'orchestrator_dependency': 'high',
            'subagent_direct_call': 'medium',
            'core_agent_import': 'high',
            'perfect21_internal': 'low',
            'config_dependency': 'medium',
            'git_workflow_coupling': 'medium'
        }

        base_severity = severity_map.get(pattern_name, 'low')

        # 根据上下文调整严重程度
        if 'import' in line.lower() and 'claude' in line.lower():
            return 'critical'
        elif 'def ' in line and ('claude' in line.lower() or 'orchestrator' in line.lower()):
            return 'high'

        return base_severity

    def categorize_coupling(self, coupling_points: List[CouplingPoint]) -> Dict[str, Any]:
        """分类分析耦合点"""
        by_type = {}
        by_severity = {}

        for cp in coupling_points:
            # 按类型分类
            if cp.coupling_type not in by_type:
                by_type[cp.coupling_type] = []
            by_type[cp.coupling_type].append(cp)

            # 按严重程度分类
            if cp.severity not in by_severity:
                by_severity[cp.severity] = []
            by_severity[cp.severity].append(cp)

        return {
            'by_type': {k: len(v) for k, v in by_type.items()},
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'critical_files': list(set([cp.file_path for cp in coupling_points if cp.severity == 'critical'])),
            'high_coupling_areas': [k for k, v in by_type.items() if len(v) > 10]
        }

    def generate_decoupling_plan(self, coupling_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成解耦方案"""
        recommendations = []

        # 1. 接口层方案
        if coupling_analysis['by_severity'].get('critical', 0) > 0:
            recommendations.append({
                'priority': 'P0',
                'title': '实现抽象接口层',
                'description': '创建IClaudeCodeAdapter接口，将Perfect21与Claude Code解耦',
                'implementation': '''
# 创建抽象接口
class IClaudeCodeAdapter(ABC):
    @abstractmethod
    def execute_subagent(self, agent_type: str, prompt: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_available_agents(self) -> List[str]:
        pass

# Perfect21通过接口调用
class Perfect21Core:
    def __init__(self, claude_adapter: IClaudeCodeAdapter):
        self.claude_adapter = claude_adapter
''',
                'benefits': ['完全解耦', '易于测试', '支持不同实现']
            })

        # 2. 事件驱动方案
        if coupling_analysis['by_type'].get('orchestrator_dependency', 0) > 5:
            recommendations.append({
                'priority': 'P1',
                'title': '引入事件驱动架构',
                'description': '使用事件总线替代直接调用，实现松耦合',
                'implementation': '''
# 事件总线
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def publish(self, event_type: str, data: Any):
        for handler in self.subscribers.get(event_type, []):
            handler(data)

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

# Perfect21作为事件发布者
class Perfect21EventPublisher:
    def request_agent_execution(self, agent_type: str, prompt: str):
        self.event_bus.publish('agent_execution_requested', {
            'agent_type': agent_type,
            'prompt': prompt
        })
''',
                'benefits': ['松耦合', '异步执行', '易于扩展']
            })

        # 3. 插件机制方案
        if coupling_analysis['by_type'].get('perfect21_internal', 0) > 10:
            recommendations.append({
                'priority': 'P2',
                'title': '模块化插件系统',
                'description': '将功能模块设计为可插拔的插件',
                'implementation': '''
# 插件基类
class Perfect21Plugin(ABC):
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        pass

# 插件管理器
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def load_plugin(self, name: str, plugin: Perfect21Plugin):
        self.plugins[name] = plugin
        plugin.initialize(self.get_context())

    def execute_plugin(self, name: str, request: Dict[str, Any]):
        return self.plugins[name].execute(request)
''',
                'benefits': ['模块化', '按需加载', '独立开发']
            })

        # 4. 配置驱动方案
        recommendations.append({
            'priority': 'P2',
            'title': '配置驱动的适配器模式',
            'description': '通过配置文件定义Claude Code集成方式',
            'implementation': '''
# 配置文件 claude_code_adapter.yaml
claude_code:
  adapter_type: "direct"  # direct, proxy, mock
  agent_mapping:
    backend-architect: "core.agents.backend_architect"
    frontend-specialist: "core.agents.frontend_specialist"

# 配置驱动适配器
class ConfigDrivenAdapter:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)

    def execute_subagent(self, agent_type: str, prompt: str):
        adapter_type = self.config['claude_code']['adapter_type']
        if adapter_type == 'direct':
            return self.direct_execution(agent_type, prompt)
        elif adapter_type == 'proxy':
            return self.proxy_execution(agent_type, prompt)
''',
            'benefits': ['灵活配置', '环境适配', '零代码切换']
        })

        return recommendations

def main():
    """主函数"""
    analyzer = ClaudeCodeCouplingAnalyzer('/home/xx/dev/Perfect21')

    print("🚀 Perfect21 与 Claude Code 耦合分析")
    print("=" * 80)

    # 运行分析
    result = analyzer.analyze_project_coupling()

    # 打印结果
    print(f"\n📊 耦合点分析结果:")
    print(f"  总耦合点: {result['total_coupling_points']}")
    print(f"  分析文件: {result['files_analyzed']}")
    print(f"  高耦合文件: {len(result['high_coupling_files'])}")

    print(f"\n🎯 按严重程度分布:")
    for severity, count in result['coupling_by_type']['by_severity'].items():
        print(f"  {severity}: {count}")

    print(f"\n🔗 按类型分布:")
    for coupling_type, count in result['coupling_by_type']['by_type'].items():
        print(f"  {coupling_type}: {count}")

    if result['high_coupling_files']:
        print(f"\n⚠️ 高耦合文件:")
        for file_path, count in result['high_coupling_files'].items():
            print(f"  • {file_path}: {count}个耦合点")

    print(f"\n💡 解耦方案建议:")
    for i, rec in enumerate(result['decoupling_recommendations'], 1):
        print(f"\n{i}. [{rec['priority']}] {rec['title']}")
        print(f"   描述: {rec['description']}")
        print(f"   收益: {', '.join(rec['benefits'])}")

    # 保存详细报告
    import json
    with open('claude_code_coupling_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n📄 详细报告已保存到: claude_code_coupling_analysis.json")

if __name__ == "__main__":
    main()