#!/usr/bin/env python3
"""
Perfect21 架构质量门
===================

检查架构合规性和设计原则
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import re

from .models import GateResult, GateStatus, GateSeverity


class ArchitectureGate:
    """架构质量门"""

    def __init__(self, project_root: str, config):
        self.project_root = Path(project_root)
        self.config = config

        # Perfect21架构规则
        self.architecture_rules = {
            "layer_dependencies": {
                # 分层依赖规则：下层不能依赖上层
                "main": ["features", "modules", "core"],
                "features": ["modules", "core"],
                "modules": ["core"],
                "core": [],
                "api": ["features", "modules", "core"],
                "tests": ["main", "features", "modules", "core", "api"]
            },
            "forbidden_imports": [
                # 禁止的导入模式
                ("core", "features"),  # 核心不能依赖功能
                ("modules", "main"),   # 工具不能依赖主程序
                ("modules", "features"), # 工具不能依赖功能
            ],
            "required_patterns": {
                # 必需的设计模式
                "features": ["__init__.py"],  # 功能模块必须有初始化文件
                "main": ["cli.py", "perfect21.py"],  # 主程序必须有CLI和主文件
            }
        }

    async def check(self, context: str = "commit") -> GateResult:
        """执行架构检查"""
        start_time = datetime.now()
        violations = []
        details = {}
        suggestions = []

        try:
            # 1. 分层架构检查
            layer_analysis = await self._check_layer_dependencies()
            details["layer_dependencies"] = layer_analysis
            if layer_analysis["violations"]:
                for violation in layer_analysis["violations"]:
                    violations.append({
                        "type": "layer_dependency_violation",
                        "message": violation["message"],
                        "severity": "high",
                        "from_layer": violation["from_layer"],
                        "to_layer": violation["to_layer"],
                        "file": violation["file"]
                    })
                suggestions.append("修复分层依赖违规")

            # 2. 模块耦合度检查
            coupling_analysis = await self._analyze_coupling()
            details["coupling"] = coupling_analysis
            if coupling_analysis["coupling_score"] > self.config.max_coupling_score:
                violations.append({
                    "type": "high_coupling",
                    "message": f"模块耦合度过高: {coupling_analysis['coupling_score']:.2f} > {self.config.max_coupling_score}",
                    "severity": "medium",
                    "current": coupling_analysis["coupling_score"],
                    "threshold": self.config.max_coupling_score
                })
                suggestions.append("降低模块间耦合度")

            # 3. 内聚性检查
            cohesion_analysis = await self._analyze_cohesion()
            details["cohesion"] = cohesion_analysis
            if cohesion_analysis["cohesion_score"] < self.config.min_cohesion_score:
                violations.append({
                    "type": "low_cohesion",
                    "message": f"模块内聚性过低: {cohesion_analysis['cohesion_score']:.2f} < {self.config.min_cohesion_score}",
                    "severity": "medium",
                    "current": cohesion_analysis["cohesion_score"],
                    "threshold": self.config.min_cohesion_score
                })
                suggestions.append("提高模块内聚性")

            # 4. 循环依赖检查
            circular_deps = await self._check_circular_dependencies()
            details["circular_dependencies"] = circular_deps
            if circular_deps["cycles"]:
                violations.append({
                    "type": "circular_dependencies",
                    "message": f"发现 {len(circular_deps['cycles'])} 个循环依赖",
                    "severity": "high",
                    "cycles": circular_deps["cycles"]
                })
                suggestions.append("消除循环依赖")

            # 5. 接口设计检查
            interface_analysis = await self._check_interface_design()
            details["interface_design"] = interface_analysis
            if interface_analysis["violations"]:
                for violation in interface_analysis["violations"]:
                    violations.append({
                        "type": "interface_design_violation",
                        "message": violation["message"],
                        "severity": violation["severity"],
                        "file": violation["file"]
                    })

            # 6. 设计模式检查
            pattern_analysis = await self._check_design_patterns()
            details["design_patterns"] = pattern_analysis
            if pattern_analysis["missing_patterns"]:
                violations.append({
                    "type": "missing_design_patterns",
                    "message": f"缺少 {len(pattern_analysis['missing_patterns'])} 个推荐的设计模式",
                    "severity": "low",
                    "patterns": pattern_analysis["missing_patterns"]
                })
                suggestions.append("考虑使用适当的设计模式")

            # 7. 代码组织检查
            organization_analysis = await self._check_code_organization()
            details["code_organization"] = organization_analysis
            if organization_analysis["issues"]:
                for issue in organization_analysis["issues"]:
                    violations.append({
                        "type": "code_organization_issue",
                        "message": issue["message"],
                        "severity": issue["severity"],
                        "file": issue.get("file", "")
                    })

            # 计算架构分数
            score = self._calculate_architecture_score(details, violations)

            # 确定状态
            high_violations = len([v for v in violations if v.get("severity") == "high"])
            medium_violations = len([v for v in violations if v.get("severity") == "medium"])

            if high_violations > 0:
                status = GateStatus.FAILED
                severity = GateSeverity.HIGH
                message = f"架构问题严重: {high_violations} 个高危问题"
            elif medium_violations > 3:
                status = GateStatus.FAILED
                severity = GateSeverity.MEDIUM
                message = f"架构问题较多: {medium_violations} 个中等问题"
            elif violations:
                status = GateStatus.WARNING
                severity = GateSeverity.LOW
                message = f"发现 {len(violations)} 个架构问题"
            else:
                status = GateStatus.PASSED
                severity = GateSeverity.INFO
                message = "架构检查通过"

            # 添加架构改进建议
            if violations:
                suggestions.extend([
                    "遵循分层架构原则",
                    "减少模块间直接依赖",
                    "使用依赖注入减少耦合",
                    "定期进行架构评审"
                ])

            execution_time = (datetime.now() - start_time).total_seconds()

            return GateResult(
                gate_name="architecture",
                status=status,
                severity=severity,
                score=score,
                message=message,
                details=details,
                violations=violations,
                suggestions=list(set(suggestions)),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context, "modules_analyzed": details.get("coupling", {}).get("modules_count", 0)}
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name="architecture",
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"架构检查失败: {str(e)}",
                details={"error": str(e)},
                violations=[{"type": "check_error", "message": str(e), "severity": "high"}],
                suggestions=["检查项目结构和文件权限"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    async def _check_layer_dependencies(self) -> Dict[str, Any]:
        """检查分层依赖"""
        violations = []
        layer_map = {}

        # 扫描所有Python文件，确定其所属层
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git'])]

        for py_file in python_files:
            try:
                file_rel_path = str(py_file.relative_to(self.project_root))
                layer = self._determine_layer(file_rel_path)
                layer_map[file_rel_path] = layer

                # 分析导入语句
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    imports = self._extract_imports(tree)

                    for imported_module in imports:
                        imported_layer = self._determine_layer_from_import(imported_module)

                        if imported_layer and layer:
                            # 检查是否违反分层依赖规则
                            allowed_deps = self.architecture_rules["layer_dependencies"].get(layer, [])

                            if imported_layer not in allowed_deps and imported_layer != layer:
                                # 检查是否在禁止导入列表中
                                if (layer, imported_layer) in self.architecture_rules["forbidden_imports"]:
                                    violations.append({
                                        "file": file_rel_path,
                                        "from_layer": layer,
                                        "to_layer": imported_layer,
                                        "imported_module": imported_module,
                                        "message": f"{layer} 层不应该依赖 {imported_layer} 层 (导入: {imported_module})"
                                    })

                except SyntaxError:
                    continue

            except Exception:
                continue

        return {
            "violations": violations,
            "layer_map": layer_map,
            "total_files": len(python_files)
        }

    def _determine_layer(self, file_path: str) -> Optional[str]:
        """根据文件路径确定所属层"""
        if file_path.startswith('main/'):
            return 'main'
        elif file_path.startswith('features/'):
            return 'features'
        elif file_path.startswith('modules/'):
            return 'modules'
        elif file_path.startswith('core/'):
            return 'core'
        elif file_path.startswith('api/'):
            return 'api'
        elif file_path.startswith('tests/'):
            return 'tests'
        return None

    def _determine_layer_from_import(self, import_path: str) -> Optional[str]:
        """根据导入路径确定层"""
        if import_path.startswith('main'):
            return 'main'
        elif import_path.startswith('features'):
            return 'features'
        elif import_path.startswith('modules'):
            return 'modules'
        elif import_path.startswith('core'):
            return 'core'
        elif import_path.startswith('api'):
            return 'api'
        return None

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取AST中的导入语句"""
        imports = []

        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imports.append(alias.name)

            def visit_ImportFrom(self, node):
                if node.module:
                    imports.append(node.module)

        visitor = ImportVisitor()
        visitor.visit(tree)
        return imports

    async def _analyze_coupling(self) -> Dict[str, Any]:
        """分析模块耦合度"""
        try:
            # 构建依赖图
            dependency_graph = {}
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'tests'])]

            for py_file in python_files:
                try:
                    file_rel_path = str(py_file.relative_to(self.project_root))
                    module_name = file_rel_path.replace('/', '.').replace('.py', '')

                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)
                    imports = self._extract_imports(tree)

                    # 过滤内部导入
                    internal_imports = [imp for imp in imports
                                      if any(imp.startswith(layer) for layer in
                                            ['main', 'features', 'modules', 'core', 'api'])]

                    dependency_graph[module_name] = internal_imports

                except Exception:
                    continue

            # 计算耦合度指标
            total_dependencies = sum(len(deps) for deps in dependency_graph.values())
            total_modules = len(dependency_graph)
            coupling_score = total_dependencies / (total_modules * (total_modules - 1)) if total_modules > 1 else 0

            # 找出高耦合的模块
            high_coupling_modules = []
            for module, deps in dependency_graph.items():
                if len(deps) > 5:  # 依赖超过5个模块视为高耦合
                    high_coupling_modules.append({
                        "module": module,
                        "dependencies": len(deps),
                        "dependency_list": deps
                    })

            return {
                "coupling_score": coupling_score,
                "total_dependencies": total_dependencies,
                "modules_count": total_modules,
                "high_coupling_modules": high_coupling_modules,
                "dependency_graph": dependency_graph
            }

        except Exception as e:
            return {
                "coupling_score": 0,
                "error": str(e)
            }

    async def _analyze_cohesion(self) -> Dict[str, Any]:
        """分析模块内聚性"""
        try:
            cohesion_scores = []
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'tests'])]

            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)

                    # 分析类和函数的关联性
                    classes = []
                    functions = []
                    shared_variables = set()

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                        elif isinstance(node, ast.FunctionDef):
                            functions.append(node.name)
                        elif isinstance(node, ast.Name):
                            shared_variables.add(node.id)

                    # 简单的内聚性评分
                    total_items = len(classes) + len(functions)
                    if total_items > 0:
                        # 如果类和函数使用相同的变量，内聚性较高
                        cohesion = len(shared_variables) / total_items
                        cohesion_scores.append(min(cohesion, 1.0))

                except Exception:
                    continue

            average_cohesion = sum(cohesion_scores) / len(cohesion_scores) if cohesion_scores else 0.5

            return {
                "cohesion_score": average_cohesion,
                "files_analyzed": len(cohesion_scores),
                "cohesion_distribution": {
                    "high": len([s for s in cohesion_scores if s > 0.7]),
                    "medium": len([s for s in cohesion_scores if 0.3 <= s <= 0.7]),
                    "low": len([s for s in cohesion_scores if s < 0.3])
                }
            }

        except Exception as e:
            return {
                "cohesion_score": 0,
                "error": str(e)
            }

    async def _check_circular_dependencies(self) -> Dict[str, Any]:
        """检查循环依赖"""
        try:
            # 构建模块依赖图
            graph = {}
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git'])]

            for py_file in python_files:
                try:
                    file_rel_path = str(py_file.relative_to(self.project_root))
                    module_name = file_rel_path.replace('/', '.').replace('.py', '')

                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)
                    imports = self._extract_imports(tree)

                    # 过滤内部导入
                    internal_imports = [imp.replace('/', '.').replace('.py', '') for imp in imports
                                      if any(imp.startswith(layer) for layer in
                                            ['main', 'features', 'modules', 'core', 'api'])]

                    graph[module_name] = internal_imports

                except Exception:
                    continue

            # 检测循环依赖
            cycles = self._detect_cycles(graph)

            return {
                "cycles": cycles,
                "modules_checked": len(graph)
            }

        except Exception as e:
            return {
                "cycles": [],
                "error": str(e)
            }

    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """检测图中的循环"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    async def _check_interface_design(self) -> Dict[str, Any]:
        """检查接口设计"""
        violations = []
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'tests'])]

        for py_file in python_files:
            try:
                file_rel_path = str(py_file.relative_to(self.project_root))

                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                # 检查类设计
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 检查类方法数量
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 20:  # 方法过多
                            violations.append({
                                "file": file_rel_path,
                                "message": f"类 {node.name} 方法过多 ({len(methods)} 个)",
                                "severity": "medium",
                                "line": node.lineno
                            })

                        # 检查是否有公共接口
                        public_methods = [m for m in methods if not m.name.startswith('_')]
                        if len(public_methods) == 0 and len(methods) > 0:
                            violations.append({
                                "file": file_rel_path,
                                "message": f"类 {node.name} 没有公共接口",
                                "severity": "low",
                                "line": node.lineno
                            })

                    elif isinstance(node, ast.FunctionDef):
                        # 检查函数参数数量
                        if len(node.args.args) > 7:  # 参数过多
                            violations.append({
                                "file": file_rel_path,
                                "message": f"函数 {node.name} 参数过多 ({len(node.args.args)} 个)",
                                "severity": "medium",
                                "line": node.lineno
                            })

            except Exception:
                continue

        return {
            "violations": violations,
            "files_checked": len(python_files)
        }

    async def _check_design_patterns(self) -> Dict[str, Any]:
        """检查设计模式使用"""
        patterns_found = []
        missing_patterns = []

        # 检查单例模式
        singleton_found = await self._check_singleton_pattern()
        if singleton_found:
            patterns_found.append("Singleton")

        # 检查工厂模式
        factory_found = await self._check_factory_pattern()
        if factory_found:
            patterns_found.append("Factory")

        # 检查观察者模式
        observer_found = await self._check_observer_pattern()
        if observer_found:
            patterns_found.append("Observer")

        # 推荐的模式
        recommended_patterns = ["Singleton", "Factory", "Observer", "Strategy"]
        missing_patterns = [p for p in recommended_patterns if p not in patterns_found]

        return {
            "patterns_found": patterns_found,
            "missing_patterns": missing_patterns,
            "pattern_usage_score": len(patterns_found) / len(recommended_patterns)
        }

    async def _check_singleton_pattern(self) -> bool:
        """检查是否使用了单例模式"""
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if '_instance' in content and '__new__' in content:
                    return True
            except Exception:
                continue
        return False

    async def _check_factory_pattern(self) -> bool:
        """检查是否使用了工厂模式"""
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'Factory' in content or 'create_' in content:
                    return True
            except Exception:
                continue
        return False

    async def _check_observer_pattern(self) -> bool:
        """检查是否使用了观察者模式"""
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'observer' in content.lower() or 'notify' in content:
                    return True
            except Exception:
                continue
        return False

    async def _check_code_organization(self) -> Dict[str, Any]:
        """检查代码组织"""
        issues = []

        # 检查必需的文件是否存在
        for layer, required_files in self.architecture_rules["required_patterns"].items():
            layer_path = self.project_root / layer
            if layer_path.exists():
                for required_file in required_files:
                    file_path = layer_path / required_file
                    if not file_path.exists():
                        issues.append({
                            "message": f"{layer} 层缺少必需文件: {required_file}",
                            "severity": "medium",
                            "file": f"{layer}/{required_file}"
                        })

        # 检查文件命名规范
        python_files = list(self.project_root.rglob("*.py"))
        for py_file in python_files:
            file_name = py_file.name
            if not re.match(r'^[a-z_][a-z0-9_]*\.py$', file_name):
                issues.append({
                    "message": f"文件命名不符合规范: {file_name}",
                    "severity": "low",
                    "file": str(py_file.relative_to(self.project_root))
                })

        return {
            "issues": issues,
            "files_checked": len(python_files)
        }

    def _calculate_architecture_score(self, details: Dict[str, Any], violations: List[Dict[str, Any]]) -> float:
        """计算架构分数"""
        base_score = 100.0

        # 分层依赖违规扣分
        layer_violations = len(details.get("layer_dependencies", {}).get("violations", []))
        base_score -= min(layer_violations * 10, 30)

        # 耦合度扣分
        coupling_score = details.get("coupling", {}).get("coupling_score", 0)
        if coupling_score > self.config.max_coupling_score:
            excess = coupling_score - self.config.max_coupling_score
            base_score -= min(excess * 50, 25)

        # 内聚性扣分
        cohesion_score = details.get("cohesion", {}).get("cohesion_score", 1.0)
        if cohesion_score < self.config.min_cohesion_score:
            deficit = self.config.min_cohesion_score - cohesion_score
            base_score -= min(deficit * 30, 20)

        # 循环依赖扣分
        cycles_count = len(details.get("circular_dependencies", {}).get("cycles", []))
        base_score -= min(cycles_count * 15, 25)

        # 接口设计问题扣分
        interface_violations = len(details.get("interface_design", {}).get("violations", []))
        base_score -= min(interface_violations * 2, 15)

        # 代码组织问题扣分
        organization_issues = len(details.get("code_organization", {}).get("issues", []))
        base_score -= min(organization_issues * 3, 15)

        # 设计模式使用加分
        pattern_score = details.get("design_patterns", {}).get("pattern_usage_score", 0)
        base_score += pattern_score * 5

        # 确保分数在0-100范围内
        return max(0.0, min(100.0, base_score))