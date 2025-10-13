#!/usr/bin/env python3
"""
Claude Enhancer智能文档加载器
根据任务类型和上下文智能加载所需文档，避免上下文污染
"""

import re
import os
import json
import hashlib
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    P0_CRITICAL = 0  # 必须加载
    P1_HIGH = 1  # 高概率加载
    P2_CONDITIONAL = 2  # 条件加载
    P3_RARE = 3  # 罕见加载


@dataclass
class DocumentInfo:
    path: str
    priority: Priority
    size_tokens: int
    categories: List[str]
    keywords: List[str]
    dependencies: List[str] = None


@dataclass
class LoadingPlan:
    phase: int
    task_type: str
    complexity: str
    tech_stack: List[str]
    documents: List[DocumentInfo]
    estimated_tokens: int


class SmartDocumentLoader:
    def __init__(self, claude_dir: str = "/home/xx/dev/Claude_Enhancer/.claude"):
        self.claude_dir = Path(claude_dir)
        self.cache = {}
        self.session_cache = {}
        self.document_registry = self._build_document_registry()
        self.usage_patterns = self._load_usage_patterns()

    def _build_document_registry(self) -> Dict[str, DocumentInfo]:
        """构建文档注册表，包含所有文档的元信息"""
        registry = {}

        # P0 - 核心文档（必须加载）
        core_docs = {
            "WORKFLOW.md": DocumentInfo(
                path="WORKFLOW.md",
                priority=Priority.P0_CRITICAL,
                size_tokens=2000,
                categories=["workflow", "core"],
                keywords=["phase", "工作流", "8阶段"],
            ),
            "AGENT_STRATEGY.md": DocumentInfo(
                path="AGENT_STRATEGY.md",
                priority=Priority.P0_CRITICAL,
                size_tokens=1500,
                categories=["agent", "strategy", "core"],
                keywords=["4-6-8", "agent", "并行", "策略"],
            ),
            "SAFETY_RULES.md": DocumentInfo(
                path="SAFETY_RULES.md",
                priority=Priority.P0_CRITICAL,
                size_tokens=1200,
                categories=["safety", "rules", "core"],
                keywords=["安全", "规则", "保护", "限制"],
            ),
        }

        # P1 - 高频文档
        high_freq_docs = {
            "PHASE_AGENT_STRATEGY.md": DocumentInfo(
                path="PHASE_AGENT_STRATEGY.md",
                priority=Priority.P1_HIGH,
                size_tokens=1800,
                categories=["phase", "agent", "mapping"],
                keywords=["phase映射", "agent组合", "阶段策略"],
            ),
            "SELF_CHECK_MECHANISM.md": DocumentInfo(
                path="SELF_CHECK_MECHANISM.md",
                priority=Priority.P1_HIGH,
                size_tokens=1000,
                categories=["quality", "check", "mechanism"],
                keywords=["自检", "质量", "验证", "检查"],
            ),
            "OUTPUT_CONTROL_STRATEGY.md": DocumentInfo(
                path="OUTPUT_CONTROL_STRATEGY.md",
                priority=Priority.P1_HIGH,
                size_tokens=800,
                categories=["output", "control", "length"],
                keywords=["输出", "控制", "长度", "格式"],
            ),
        }

        # P2 - 架构文档（条件加载）
        arch_docs = {
            "ARCHITECTURE/v2.0-FOUNDATION.md": DocumentInfo(
                path="ARCHITECTURE/v2.0-FOUNDATION.md",
                priority=Priority.P2_CONDITIONAL,
                size_tokens=3000,
                categories=["architecture", "foundation", "design"],
                keywords=["架构", "四层", "设计", "基础", "重构"],
            ),
            "ARCHITECTURE/LAYER-DEFINITION.md": DocumentInfo(
                path="ARCHITECTURE/LAYER-DEFINITION.md",
                priority=Priority.P2_CONDITIONAL,
                size_tokens=2500,
                categories=["architecture", "layers", "L0-L3"],
                keywords=["分层", "L0", "L1", "L2", "L3", "依赖"],
            ),
            "ARCHITECTURE/GROWTH-STRATEGY.md": DocumentInfo(
                path="ARCHITECTURE/GROWTH-STRATEGY.md",
                priority=Priority.P2_CONDITIONAL,
                size_tokens=2000,
                categories=["architecture", "growth", "features"],
                keywords=["新功能", "分级", "basic", "standard", "advanced"],
            ),
            "ARCHITECTURE/NAMING-CONVENTIONS.md": DocumentInfo(
                path="ARCHITECTURE/NAMING-CONVENTIONS.md",
                priority=Priority.P2_CONDITIONAL,
                size_tokens=1500,
                categories=["architecture", "naming", "conventions"],
                keywords=["命名", "规范", "约定", "文件名", "变量名"],
            ),
        }

        # P3 - 特殊文档（罕见加载）
        special_docs = {
            "ISSUES_AND_SOLUTIONS.md": DocumentInfo(
                path="ISSUES_AND_SOLUTIONS.md",
                priority=Priority.P3_RARE,
                size_tokens=1800,
                categories=["troubleshooting", "issues", "solutions"],
                keywords=["问题", "解决", "故障", "排查", "错误"],
            ),
            "CLEANUP_STRATEGY.md": DocumentInfo(
                path="CLEANUP_STRATEGY.md",
                priority=Priority.P3_RARE,
                size_tokens=1200,
                categories=["cleanup", "maintenance", "optimization"],
                keywords=["清理", "维护", "优化", "清理策略"],
            ),
        }

        # 合并所有文档
        registry.update(core_docs)
        registry.update(high_freq_docs)
        registry.update(arch_docs)
        registry.update(special_docs)

        # 添加Agent文档（动态生成）
        agent_docs = self._register_agent_documents()
        registry.update(agent_docs)

        return registry

    def _register_agent_documents(self) -> Dict[str, DocumentInfo]:
        """注册所有Agent文档"""
        agent_docs = {}
        agents_dir = self.claude_dir / "agents"

        if not agents_dir.exists():
            return agent_docs

        # 递归查找所有.md文件
        import glob

        agent_files = glob.glob(str(agents_dir / "**/*.md"), recursive=True)

        for agent_file in agent_files:
            relative_path = str(Path(agent_file).relative_to(self.claude_dir))
            file_name = Path(agent_file).name

            # 根据文件名和路径确定分类
            categories = ["agent"]
            keywords = [file_name.replace("-", " ").replace(".md", "")]

            # 基于文件名和路径的智能分类
            if any(
                keyword in file_name.lower()
                for keyword in ["backend", "python", "golang", "java", "api"]
            ):
                categories.append("backend")
            if any(
                keyword in file_name.lower()
                for keyword in ["frontend", "react", "vue", "angular", "ui"]
            ):
                categories.append("frontend")
            if any(
                keyword in file_name.lower()
                for keyword in ["test", "e2e", "performance"]
            ):
                categories.append("testing")
            if any(keyword in file_name.lower() for keyword in ["security", "audit"]):
                categories.append("security")
            if any(
                keyword in file_name.lower()
                for keyword in ["devops", "kubernetes", "docker", "deploy"]
            ):
                categories.append("devops")
            if any(
                keyword in file_name.lower() for keyword in ["data", "analytics", "ml"]
            ):
                categories.append("data")

            # 基于路径的分类
            if "development" in relative_path:
                if "frontend" not in categories:
                    categories.append("frontend")
            elif "quality" in relative_path:
                if "testing" not in categories:
                    categories.append("testing")
            elif "business" in relative_path:
                categories.append("business")

            agent_docs[relative_path] = DocumentInfo(
                path=relative_path,
                priority=Priority.P2_CONDITIONAL,
                size_tokens=800,  # 估算Agent文档大小
                categories=categories,
                keywords=keywords,
            )

        return agent_docs

    def analyze_task(self, user_request: str, current_phase: int = 0) -> Dict:
        """分析用户请求，提取任务信息"""
        analysis = {
            "task_type": self._classify_task_type(user_request),
            "complexity": self._assess_complexity(user_request),
            "tech_stack": self._detect_technology_stack(user_request),
            "keywords": self._extract_keywords(user_request),
            "phase": current_phase,
            "architecture_needs": self._detect_architecture_needs(user_request),
            "security_needs": self._detect_security_needs(user_request),
        }
        return analysis

    def _classify_task_type(self, request: str) -> str:
        """分类任务类型"""
        request_lower = request.lower()

        patterns = {
            "Bug修复": ["修复", "fix", "bug", "问题", "错误"],
            "重构优化": ["重构", "优化", "改进", "重写", "整理"],
            "架构设计": ["架构", "设计", "分层", "模块", "系统"],
            "测试相关": ["测试", "test", "单元测试", "集成测试"],
            "安全审计": ["安全", "审计", "权限", "认证", "加密"],
            "性能优化": ["性能", "优化", "缓存", "慢查询", "内存"],
            "文档更新": ["文档", "说明", "readme", "注释"],
            "部署运维": ["部署", "发布", "运维", "监控", "CI/CD"],
            "新功能开发": ["添加", "新功能", "实现", "开发", "创建", "购物车", "仪表板", "功能"],
        }

        for task_type, keywords in patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                return task_type

        return "通用开发"

    def _assess_complexity(self, request: str) -> str:
        """评估任务复杂度"""
        request_lower = request.lower()

        # 简单任务指标
        simple_indicators = ["修复", "fix", "小改", "格式化", "注释", "文档更新"]
        # 复杂任务指标
        complex_indicators = ["架构", "重构", "新系统", "微服务", "分布式", "复杂", "大型"]

        simple_score = sum(
            1 for indicator in simple_indicators if indicator in request_lower
        )
        complex_score = sum(
            1 for indicator in complex_indicators if indicator in request_lower
        )

        if complex_score > simple_score:
            return "复杂"
        elif simple_score > 0:
            return "简单"
        else:
            return "标准"

    def _detect_technology_stack(self, request: str) -> List[str]:
        """检测技术栈"""
        request_lower = request.lower()
        tech_stack = []

        tech_patterns = {
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "npm"],
            "react": ["react", "jsx", "redux"],
            "vue": ["vue", "vuex", "nuxt"],
            "angular": ["angular", "typescript", "ts"],
            "golang": ["go", "golang", "gin"],
            "java": ["java", "spring", "maven"],
            "database": ["数据库", "database", "sql", "mysql", "postgresql", "mongodb"],
            "docker": ["docker", "container", "containerize"],
            "kubernetes": ["kubernetes", "k8s", "helm"],
            "aws": ["aws", "s3", "ec2", "lambda"],
            "testing": ["测试", "test", "pytest", "jest"],
        }

        for tech, patterns in tech_patterns.items():
            if any(pattern in request_lower for pattern in patterns):
                tech_stack.append(tech)

        return tech_stack

    def _extract_keywords(self, request: str) -> List[str]:
        """提取关键词"""
        # 移除停用词，提取重要关键词
        stop_words = {"的", "是", "在", "有", "和", "或", "但", "然后", "这", "那", "我", "你", "它"}
        words = re.findall(r"\w+", request.lower())
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        return keywords[:10]  # 限制关键词数量

    def _detect_architecture_needs(self, request: str) -> bool:
        """检测是否需要架构文档"""
        arch_keywords = ["架构", "设计", "重构", "分层", "模块", "新功能", "系统", "添加", "创建", "微服务"]
        return any(keyword in request.lower() for keyword in arch_keywords)

    def _detect_security_needs(self, request: str) -> bool:
        """检测是否需要安全文档"""
        security_keywords = ["安全", "权限", "认证", "登录", "加密", "漏洞"]
        return any(keyword in request.lower() for keyword in security_keywords)

    def create_loading_plan(self, task_analysis: Dict) -> LoadingPlan:
        """创建文档加载计划"""
        documents = []

        # 1. 总是加载P0文档
        for doc_path, doc_info in self.document_registry.items():
            if doc_info.priority == Priority.P0_CRITICAL:
                documents.append(doc_info)

        # 2. 根据Phase加载P1文档
        if task_analysis["phase"] >= 1:
            for doc_path, doc_info in self.document_registry.items():
                if doc_info.priority == Priority.P1_HIGH:
                    documents.append(doc_info)

        # 3. 条件加载P2文档
        if task_analysis["architecture_needs"]:
            arch_docs = [
                doc
                for doc in self.document_registry.values()
                if "architecture" in doc.categories
            ]
            documents.extend(arch_docs)

        # 4. 根据技术栈加载Agent文档
        for tech in task_analysis["tech_stack"]:
            tech_docs = [
                doc
                for doc in self.document_registry.values()
                if tech in doc.categories or tech in doc.keywords
            ]
            documents.extend(tech_docs)

        # 5. 根据安全需求加载安全文档
        if task_analysis["security_needs"]:
            security_docs = [
                doc
                for doc in self.document_registry.values()
                if "security" in doc.categories
            ]
            documents.extend(security_docs)

        # 6. 根据任务类型加载特定文档
        task_type = task_analysis["task_type"]
        if task_type == "Bug修复" or "问题" in task_analysis["keywords"]:
            troubleshooting_docs = [
                doc
                for doc in self.document_registry.values()
                if "troubleshooting" in doc.categories
            ]
            documents.extend(troubleshooting_docs)

        # 7. 根据复杂度选择Agent数量
        complexity = task_analysis["complexity"]
        agent_count = {"简单": 4, "标准": 6, "复杂": 8}.get(complexity, 6)

        # 去重并计算总Token
        unique_docs = list({doc.path: doc for doc in documents}.values())
        estimated_tokens = sum(doc.size_tokens for doc in unique_docs)

        return LoadingPlan(
            phase=task_analysis["phase"],
            task_type=task_analysis["task_type"],
            complexity=task_analysis["complexity"],
            tech_stack=task_analysis["tech_stack"],
            documents=unique_docs,
            estimated_tokens=estimated_tokens,
        )

    def optimize_loading_plan(
        self, plan: LoadingPlan, max_tokens: int = 50000
    ) -> LoadingPlan:
        """优化加载计划，确保不超过Token限制"""
        if plan.estimated_tokens <= max_tokens:
            return plan

        # 按优先级排序
        sorted_docs = sorted(plan.documents, key=lambda d: d.priority.value)

        # 逐步添加文档直到达到限制
        optimized_docs = []
        current_tokens = 0

        for doc in sorted_docs:
            if current_tokens + doc.size_tokens <= max_tokens:
                optimized_docs.append(doc)
                current_tokens += doc.size_tokens
            elif doc.priority == Priority.P0_CRITICAL:
                pass  # Auto-fixed empty block
                # 关键文档必须加载，移除其他文档为其腾出空间
                optimized_docs = [
                    d for d in optimized_docs if d.priority == Priority.P0_CRITICAL
                ]
                optimized_docs.append(doc)
                current_tokens = sum(d.size_tokens for d in optimized_docs)

        plan.documents = optimized_docs
        plan.estimated_tokens = current_tokens
        return plan

    def execute_loading_plan(self, plan: LoadingPlan) -> Dict[str, str]:
        """执行加载计划，返回文档内容"""
        loaded_docs = {}

        for doc_info in plan.documents:
            doc_path = self.claude_dir / doc_info.path
            if doc_path.exists():
                try:
                    with open(doc_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        loaded_docs[doc_info.path] = content

                        # 缓存策略
                        if doc_info.priority == Priority.P0_CRITICAL:
                            self.cache[doc_info.path] = content
                        else:
                            self.session_cache[doc_info.path] = content

                except Exception as e:
                    print(f"Failed to load document {doc_path}: {e}")
            else:
                print(f"Document not found: {doc_path}")

        return loaded_docs

    def get_documents_for_task(
        self, user_request: str, current_phase: int = 0, max_tokens: int = 50000
    ) -> Tuple[Dict[str, str], LoadingPlan]:
        """主要接口：根据任务获取所需文档"""
        # 1. 分析任务
        task_analysis = self.analyze_task(user_request, current_phase)

        # 2. 创建加载计划
        plan = self.create_loading_plan(task_analysis)

        # 3. 优化计划
        optimized_plan = self.optimize_loading_plan(plan, max_tokens)

        # 4. 执行加载
        documents = self.execute_loading_plan(optimized_plan)

        # 5. 记录使用模式（用于后续优化）
        self._record_usage_pattern(task_analysis, optimized_plan)

        return documents, optimized_plan

    def _record_usage_pattern(self, task_analysis: Dict, plan: LoadingPlan):
        """记录使用模式，用于持续优化"""
        pattern = {
            "task_type": task_analysis["task_type"],
            "complexity": task_analysis["complexity"],
            "tech_stack": task_analysis["tech_stack"],
            "documents_loaded": [doc.path for doc in plan.documents],
            "total_tokens": plan.estimated_tokens,
            "timestamp": "2025-09-23",  # 实际环境中使用datetime
        }

        # 存储到使用模式历史中
        if task_analysis["task_type"] not in self.usage_patterns:
            self.usage_patterns[task_analysis["task_type"]] = []

        self.usage_patterns[task_analysis["task_type"]].append(pattern)

    def _load_usage_patterns(self) -> Dict:
        """加载历史使用模式"""
        patterns_file = self.claude_dir / "usage_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def clear_session_cache(self):
        """清理会话缓存"""
        self.session_cache.clear()

    def get_loading_statistics(self) -> Dict:
        """获取加载统计信息"""
        return {
            "cache_size": len(self.cache),
            "session_cache_size": len(self.session_cache),
            "total_documents": len(self.document_registry),
            "usage_patterns": len(self.usage_patterns),
        }


def main():
    """示例使用"""
    loader = SmartDocumentLoader()

    # 示例1：简单Bug修复
    print("=== 示例1：Bug修复任务 ===")
    docs, plan = loader.get_documents_for_task("修复用户登录的bug", current_phase=3)
    print(f"加载文档数量: {len(docs)}")
    print(f"预估Token数: {plan.estimated_tokens}")
    print(f"文档列表: {[doc.path for doc in plan.documents]}")

    # 示例2：新功能开发
    print("\n=== 示例2：新功能开发 ===")
    docs, plan = loader.get_documents_for_task("添加React组件的新功能，需要数据库支持", current_phase=2)
    print(f"加载文档数量: {len(docs)}")
    print(f"预估Token数: {plan.estimated_tokens}")
    print(f"文档列表: {[doc.path for doc in plan.documents]}")

    # 示例3：架构重构
    print("\n=== 示例3：架构重构 ===")
    docs, plan = loader.get_documents_for_task("重构系统架构，优化分层设计", current_phase=2)
    print(f"加载文档数量: {len(docs)}")
    print(f"预估Token数: {plan.estimated_tokens}")
    print(f"文档列表: {[doc.path for doc in plan.documents]}")


if __name__ == "__main__":
    main()
