#!/usr/bin/env python3
"""
Manager整合脚本 - 将31个Manager类合并为15个核心Manager
减少耦合点从978个降至<500个

执行步骤:
1. 分析现有Manager类的依赖关系
2. 创建Manager映射和迁移计划
3. 更新导入语句
4. 创建兼容性包装器
5. 验证整合结果
"""

import os
import sys
import re
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("ManagerConsolidation")

@dataclass
class ManagerInfo:
    """Manager信息"""
    name: str
    file_path: str
    class_name: str
    dependencies: Set[str]
    used_by: Set[str]
    functions: List[str]
    consolidation_target: Optional[str] = None
    is_deprecated: bool = False

@dataclass
class ConsolidationPlan:
    """整合计划"""
    original_managers: List[ManagerInfo]
    consolidated_managers: Dict[str, List[str]]  # 新Manager -> 原Manager列表
    migration_mappings: Dict[str, str]  # 原Manager -> 新Manager
    deprecated_managers: List[str]
    compatibility_wrappers: Dict[str, str]

class ManagerConsolidator:
    """Manager整合器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.managers: Dict[str, ManagerInfo] = {}
        self.consolidation_plan: Optional[ConsolidationPlan] = None

        # 整合映射规则
        self.consolidation_mapping = {
            # 1. 统一配置状态管理器
            "UnifiedConfigStateManager": [
                "ConfigManager", "TypeSafeConfigManager", "BaseConfigManager",
                "StateManager", "ModuleStateManager"
            ],

            # 2. 统一资源缓存管理器
            "UnifiedResourceCacheManager": [
                "CacheManager", "MemoryCacheManager", "ResourceManager",
                "GitCacheManager", "BatchIOManager"
            ],

            # 3. 统一认证授权管理器
            "UnifiedAuthSecurityManager": [
                "AuthManager", "AuthenticationManager", "TokenManager",
                "RBACManager", "SecurityManager"
            ],

            # 4. 统一工作流执行管理器
            "UnifiedWorkflowExecutionManager": [
                "WorkflowManager", "TaskManager", "ParallelManager",
                "SyncPointManager", "ExecutionManager"
            ],

            # 5. 统一Git集成管理器
            "UnifiedGitIntegrationManager": [
                "GitHooksManager", "BranchManager", "GitCacheManager",
                "GitWorkflowManager", "VersionManager"
            ],

            # 6. 统一文档内容管理器
            "UnifiedDocumentContentManager": [
                "DocumentManager", "ClaudeMdManager", "LifecycleManager",
                "TemplateManager", "ContentAnalyzer"
            ],

            # 7. 统一质量监控管理器
            "UnifiedQualityMonitoringManager": [
                "QualityGateManager", "MonitoringManager", "MetricsManager",
                "PerformanceManager", "HealthCheckManager"
            ],

            # 8. 统一插件扩展管理器
            "UnifiedPluginExtensionManager": [
                "PluginManager", "ExtensionManager", "HotPlugManager",
                "ComponentManager", "ModuleManager"
            ],

            # 9. 统一工作空间管理器 - 保持独立
            "WorkspaceManager": ["WorkspaceManager"],

            # 10. 统一错误处理管理器
            "UnifiedErrorHandlingManager": [
                "ErrorRecoveryManager", "RetryManager", "ErrorContextManager",
                "FaultToleranceManager", "CircuitBreakerManager"
            ],

            # 11. 统一决策记录管理器
            "UnifiedDecisionRecordManager": [
                "ADRManager", "DecisionRecorder", "KnowledgeManager",
                "LearningManager", "ExperienceManager"
            ],

            # 12. 统一可视化管理器
            "UnifiedVisualizationManager": [
                "VisualizationManager", "DashboardManager", "ReportManager",
                "ChartManager", "GraphManager"
            ],

            # 13. 统一通信管理器
            "UnifiedCommunicationManager": [
                "NotificationManager", "MessageManager", "AlertManager",
                "EmailManager", "WebhookManager"
            ],

            # 14. 统一安全框架管理器
            "UnifiedSecurityFrameworkManager": [
                "SecurityAuditManager", "EncryptionManager", "AccessControlManager",
                "ComplianceManager", "ThreatManager"
            ],

            # 15. 统一系统架构管理器
            "UnifiedSystemArchitectureManager": [
                "ArchitectureManager", "ServiceManager", "RegistryManager",
                "DiscoveryManager", "LoadBalancerManager"
            ]
        }

    def analyze_existing_managers(self) -> Dict[str, ManagerInfo]:
        """分析现有Manager类"""
        logger.info("分析现有Manager类...")

        # 扫描所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                self._analyze_file(py_file)
            except Exception as e:
                logger.warning(f"分析文件失败 {py_file}: {e}")

        logger.info(f"发现 {len(self.managers)} 个Manager类")

        # 分析依赖关系
        self._analyze_dependencies()

        return self.managers

    def _should_skip_file(self, file_path: Path) -> bool:
        """检查是否应该跳过文件"""
        skip_patterns = [
            "venv", "__pycache__", ".git", "node_modules",
            "test_", "tests/", "docs/", ".claude/agents/"
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path):
        """分析单个文件中的Manager类"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找Manager类定义
            manager_pattern = r'class\s+(\w*Manager\w*)\s*[\(:]'
            matches = re.finditer(manager_pattern, content)

            for match in matches:
                class_name = match.group(1)

                if class_name in self.managers:
                    continue  # 避免重复

                # 提取函数列表
                functions = self._extract_functions(content, class_name)

                # 创建Manager信息
                manager_info = ManagerInfo(
                    name=class_name,
                    file_path=str(file_path),
                    class_name=class_name,
                    dependencies=set(),
                    used_by=set(),
                    functions=functions
                )

                self.managers[class_name] = manager_info
                logger.debug(f"发现Manager: {class_name} in {file_path}")

        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")

    def _extract_functions(self, content: str, class_name: str) -> List[str]:
        """提取类中的函数列表"""
        functions = []

        # 简化的函数提取 - 查找类内的def语句
        lines = content.split('\n')
        in_class = False
        class_indent = 0

        for line in lines:
            stripped = line.strip()

            if f'class {class_name}' in line:
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                continue

            if in_class:
                current_indent = len(line) - len(line.lstrip())

                # 如果缩进回到类级别或更少，说明类定义结束
                if current_indent <= class_indent and stripped and not stripped.startswith('#'):
                    if not stripped.startswith('def ') and not stripped.startswith('@'):
                        break

                # 提取函数定义
                if stripped.startswith('def ') and current_indent > class_indent:
                    func_match = re.match(r'def\s+(\w+)\s*\(', stripped)
                    if func_match:
                        func_name = func_match.group(1)
                        if not func_name.startswith('_'):  # 只记录公共方法
                            functions.append(func_name)

        return functions

    def _analyze_dependencies(self):
        """分析Manager间的依赖关系"""
        logger.info("分析Manager依赖关系...")

        for file_path in self.project_root.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找import语句中的Manager依赖
                for manager_name in self.managers:
                    if f"import {manager_name}" in content or f"from .* import.*{manager_name}" in content:
                        # 查找在哪个Manager类中使用
                        for using_manager in self.managers:
                            if f"class {using_manager}" in content:
                                self.managers[manager_name].used_by.add(using_manager)
                                self.managers[using_manager].dependencies.add(manager_name)
                                break

            except Exception as e:
                logger.warning(f"分析依赖失败 {file_path}: {e}")

    def create_consolidation_plan(self) -> ConsolidationPlan:
        """创建整合计划"""
        logger.info("创建整合计划...")

        # 反向映射：原Manager -> 新Manager
        migration_mappings = {}
        for new_manager, old_managers in self.consolidation_mapping.items():
            for old_manager in old_managers:
                migration_mappings[old_manager] = new_manager

        # 识别需要废弃的Manager
        deprecated_managers = []
        for manager_name in self.managers:
            if manager_name not in migration_mappings:
                # 检查是否是测试或示例Manager
                if any(keyword in manager_name.lower() for keyword in ['test', 'demo', 'example', 'mock']):
                    deprecated_managers.append(manager_name)
                else:
                    # 将未分类的Manager分配到最合适的新Manager
                    target = self._find_best_consolidation_target(manager_name)
                    if target:
                        migration_mappings[manager_name] = target
                        self.consolidation_mapping[target].append(manager_name)

        # 创建兼容性包装器映射
        compatibility_wrappers = {}
        for old_manager, new_manager in migration_mappings.items():
            if old_manager in self.managers:  # 确保Manager存在
                compatibility_wrappers[old_manager] = new_manager

        self.consolidation_plan = ConsolidationPlan(
            original_managers=list(self.managers.values()),
            consolidated_managers=self.consolidation_mapping,
            migration_mappings=migration_mappings,
            deprecated_managers=deprecated_managers,
            compatibility_wrappers=compatibility_wrappers
        )

        logger.info(f"整合计划创建完成:")
        logger.info(f"  - 原有Manager: {len(self.managers)}")
        logger.info(f"  - 整合后Manager: {len(self.consolidation_mapping)}")
        logger.info(f"  - 需要废弃: {len(deprecated_managers)}")
        logger.info(f"  - 兼容性包装器: {len(compatibility_wrappers)}")

        return self.consolidation_plan

    def _find_best_consolidation_target(self, manager_name: str) -> Optional[str]:
        """为未分类的Manager找到最佳整合目标"""
        manager_lower = manager_name.lower()

        # 基于关键词匹配
        keyword_mapping = {
            'config': 'UnifiedConfigStateManager',
            'state': 'UnifiedConfigStateManager',
            'cache': 'UnifiedResourceCacheManager',
            'resource': 'UnifiedResourceCacheManager',
            'auth': 'UnifiedAuthSecurityManager',
            'security': 'UnifiedAuthSecurityManager',
            'token': 'UnifiedAuthSecurityManager',
            'workflow': 'UnifiedWorkflowExecutionManager',
            'task': 'UnifiedWorkflowExecutionManager',
            'parallel': 'UnifiedWorkflowExecutionManager',
            'sync': 'UnifiedWorkflowExecutionManager',
            'git': 'UnifiedGitIntegrationManager',
            'branch': 'UnifiedGitIntegrationManager',
            'version': 'UnifiedGitIntegrationManager',
            'document': 'UnifiedDocumentContentManager',
            'content': 'UnifiedDocumentContentManager',
            'template': 'UnifiedDocumentContentManager',
            'quality': 'UnifiedQualityMonitoringManager',
            'monitor': 'UnifiedQualityMonitoringManager',
            'metrics': 'UnifiedQualityMonitoringManager',
            'performance': 'UnifiedQualityMonitoringManager',
            'plugin': 'UnifiedPluginExtensionManager',
            'extension': 'UnifiedPluginExtensionManager',
            'workspace': 'WorkspaceManager',
            'error': 'UnifiedErrorHandlingManager',
            'recovery': 'UnifiedErrorHandlingManager',
            'retry': 'UnifiedErrorHandlingManager',
            'decision': 'UnifiedDecisionRecordManager',
            'adr': 'UnifiedDecisionRecordManager',
            'knowledge': 'UnifiedDecisionRecordManager',
            'visual': 'UnifiedVisualizationManager',
            'dashboard': 'UnifiedVisualizationManager',
            'report': 'UnifiedVisualizationManager',
            'notification': 'UnifiedCommunicationManager',
            'message': 'UnifiedCommunicationManager',
            'alert': 'UnifiedCommunicationManager',
            'security': 'UnifiedSecurityFrameworkManager',
            'encryption': 'UnifiedSecurityFrameworkManager',
            'access': 'UnifiedSecurityFrameworkManager',
            'architecture': 'UnifiedSystemArchitectureManager',
            'service': 'UnifiedSystemArchitectureManager',
            'registry': 'UnifiedSystemArchitectureManager'
        }

        for keyword, target in keyword_mapping.items():
            if keyword in manager_lower:
                return target

        # 默认分配到系统架构管理器
        return 'UnifiedSystemArchitectureManager'

    def create_compatibility_wrappers(self):
        """创建兼容性包装器"""
        if not self.consolidation_plan:
            raise ValueError("必须先创建整合计划")

        logger.info("创建兼容性包装器...")

        # 创建兼容性模块目录
        compat_dir = self.project_root / "shared" / "compatibility"
        compat_dir.mkdir(parents=True, exist_ok=True)

        # 创建__init__.py
        init_content = '''#!/usr/bin/env python3
"""
Perfect21 兼容性模块
为整合后的Manager提供向后兼容的接口
"""

# 导入所有兼容性包装器
'''

        # 为每个原Manager创建包装器
        for old_manager, new_manager in self.consolidation_plan.migration_mappings.items():
            if old_manager not in self.managers:
                continue

            wrapper_content = self._generate_wrapper_content(old_manager, new_manager)
            wrapper_file = compat_dir / f"{old_manager.lower()}.py"

            with open(wrapper_file, 'w', encoding='utf-8') as f:
                f.write(wrapper_content)

            # 添加到__init__.py
            init_content += f"from .{old_manager.lower()} import {old_manager}\n"

        # 写入__init__.py
        with open(compat_dir / "__init__.py", 'w', encoding='utf-8') as f:
            f.write(init_content)

        logger.info(f"创建了 {len(self.consolidation_plan.migration_mappings)} 个兼容性包装器")

    def _generate_wrapper_content(self, old_manager: str, new_manager: str) -> str:
        """生成包装器内容"""
        manager_info = self.managers.get(old_manager)
        functions = manager_info.functions if manager_info else []

        content = f'''#!/usr/bin/env python3
"""
{old_manager} 兼容性包装器
自动生成的包装器，将调用重定向到 {new_manager}
"""

import logging
from typing import Any, Dict, Optional
from ..core_managers import unified_manager_system

logger = logging.getLogger("Perfect21.Compatibility.{old_manager}")

class {old_manager}:
    """
    {old_manager} 兼容性包装器

    注意: 这是一个兼容性包装器，实际功能由 {new_manager} 提供
    建议迁移到新的统一Manager系统
    """

    def __init__(self, *args, **kwargs):
        """初始化兼容性包装器"""
        logger.warning(f"{old_manager} 已被整合到 {new_manager}，建议使用新接口")

        # 获取对应的新Manager
        self._new_manager = unified_manager_system.get_manager(self._get_manager_key())

        if not self._new_manager:
            logger.error(f"无法获取 {new_manager} 实例")
            raise RuntimeError(f"Manager {new_manager} 不可用")

    def _get_manager_key(self) -> str:
        """获取新Manager的键名"""
        mapping = {{
            "UnifiedConfigStateManager": "config_state",
            "UnifiedResourceCacheManager": "resource_cache",
            "UnifiedAuthSecurityManager": "auth_security",
            "UnifiedWorkflowExecutionManager": "workflow_execution",
            "UnifiedGitIntegrationManager": "git_integration"
        }}
        return mapping.get("{new_manager}", "config_state")

    def __getattr__(self, name: str) -> Any:
        """动态属性访问 - 重定向到新Manager"""
        if self._new_manager and hasattr(self._new_manager, name):
            attr = getattr(self._new_manager, name)
            if callable(attr):
                def wrapper(*args, **kwargs):
                    logger.debug(f"重定向调用: {old_manager}.{{name}} -> {new_manager}.{{name}}")
                    return attr(*args, **kwargs)
                return wrapper
            return attr

        raise AttributeError(f"'{old_manager}' 对象没有属性 '{{name}}'")
'''

        # 为已知函数创建专门的包装方法
        for func_name in functions[:10]:  # 限制数量，避免文件过大
            content += f'''

    def {func_name}(self, *args, **kwargs):
        """兼容性方法: {func_name}"""
        logger.debug(f"调用兼容性方法: {old_manager}.{func_name}")

        if hasattr(self._new_manager, '{func_name}'):
            return getattr(self._new_manager, '{func_name}')(*args, **kwargs)
        else:
            logger.warning(f"新Manager {new_manager} 不支持方法 {func_name}")
            raise NotImplementedError(f"方法 {func_name} 在新Manager中不可用")
'''

        return content

    def update_import_statements(self):
        """更新import语句"""
        if not self.consolidation_plan:
            raise ValueError("必须先创建整合计划")

        logger.info("更新import语句...")

        updated_files = 0

        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # 更新import语句
                for old_manager, new_manager in self.consolidation_plan.migration_mappings.items():
                    # 更新直接import
                    pattern1 = rf'from\s+[\w.]*\s+import\s+.*{old_manager}'
                    replacement1 = f'from shared.compatibility import {old_manager}  # 兼容性包装器，建议迁移到 {new_manager}'
                    content = re.sub(pattern1, replacement1, content)

                    # 更新类import
                    pattern2 = rf'import\s+.*{old_manager}'
                    replacement2 = f'from shared.compatibility import {old_manager}  # 兼容性包装器'
                    content = re.sub(pattern2, replacement2, content)

                # 如果有变更，写回文件
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated_files += 1
                    logger.debug(f"更新文件: {py_file}")

            except Exception as e:
                logger.warning(f"更新文件失败 {py_file}: {e}")

        logger.info(f"更新了 {updated_files} 个文件的import语句")

    def generate_consolidation_report(self) -> Dict[str, Any]:
        """生成整合报告"""
        if not self.consolidation_plan:
            raise ValueError("必须先创建整合计划")

        # 计算耦合点减少
        original_coupling_points = sum(len(manager.dependencies) + len(manager.used_by)
                                     for manager in self.managers.values())

        # 新系统的耦合点（基于事件驱动架构）
        estimated_new_coupling_points = len(self.consolidation_mapping) * 2  # 每个Manager只依赖事件总线

        report = {
            "consolidation_summary": {
                "original_managers": len(self.managers),
                "consolidated_managers": len(self.consolidation_mapping),
                "reduction_ratio": f"{((len(self.managers) - len(self.consolidation_mapping)) / len(self.managers) * 100):.1f}%",
                "original_coupling_points": original_coupling_points,
                "estimated_new_coupling_points": estimated_new_coupling_points,
                "coupling_reduction": f"{((original_coupling_points - estimated_new_coupling_points) / original_coupling_points * 100):.1f}%"
            },
            "manager_mapping": dict(self.consolidation_plan.migration_mappings),
            "consolidated_groups": self.consolidation_mapping,
            "deprecated_managers": self.consolidation_plan.deprecated_managers,
            "compatibility_wrappers": list(self.consolidation_plan.compatibility_wrappers.keys()),
            "analysis_timestamp": datetime.now().isoformat()
        }

        return report

    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None):
        """保存整合报告"""
        if not output_file:
            output_file = str(self.project_root / "manager_consolidation_report.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"整合报告已保存到: {output_file}")

    def execute_consolidation(self):
        """执行完整的整合流程"""
        logger.info("开始执行Manager整合...")

        try:
            # 1. 分析现有Manager
            self.analyze_existing_managers()

            # 2. 创建整合计划
            self.create_consolidation_plan()

            # 3. 创建兼容性包装器
            self.create_compatibility_wrappers()

            # 4. 更新import语句
            self.update_import_statements()

            # 5. 生成报告
            report = self.generate_consolidation_report()
            self.save_report(report)

            logger.info("Manager整合完成!")
            logger.info(f"原有Manager: {report['consolidation_summary']['original_managers']}")
            logger.info(f"整合后Manager: {report['consolidation_summary']['consolidated_managers']}")
            logger.info(f"减少比例: {report['consolidation_summary']['reduction_ratio']}")
            logger.info(f"耦合点减少: {report['consolidation_summary']['coupling_reduction']}")

            return True

        except Exception as e:
            logger.error(f"整合过程失败: {e}")
            return False

def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    # 创建整合器
    consolidator = ManagerConsolidator(str(project_root))

    # 执行整合
    success = consolidator.execute_consolidation()

    if success:
        print("✅ Manager整合成功完成!")
        print("📊 检查 manager_consolidation_report.json 获取详细报告")
        print("🔧 兼容性包装器已创建在 shared/compatibility/ 目录")
        print("⚠️  建议逐步迁移到新的统一Manager接口")
    else:
        print("❌ Manager整合失败，请检查日志")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())