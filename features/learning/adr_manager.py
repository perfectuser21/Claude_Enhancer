#!/usr/bin/env python3
"""
Perfect21 架构决策记录(ADR)管理器
自动记录和管理所有重要的架构决策
"""

import os
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("ADRManager")

class DecisionStatus(Enum):
    """决策状态"""
    PROPOSED = "提议"
    ACCEPTED = "已接受"
    DEPRECATED = "已弃用"
    SUPERSEDED = "已替代"

class TechnicalDomain(Enum):
    """技术领域"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DEVOPS = "devops"
    ARCHITECTURE = "architecture"
    API = "api"
    UI_UX = "ui_ux"
    TESTING = "testing"

@dataclass
class DecisionOption:
    """决策选项"""
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    cost_estimate: str
    implementation_effort: str

@dataclass
class ArchitecturalDecision:
    """架构决策记录"""
    id: str
    title: str
    status: DecisionStatus
    date: datetime
    deciders: List[str]  # 参与决策的agents
    technical_domain: TechnicalDomain

    # 决策内容
    context: str
    problem_statement: str
    decision_drivers: List[str]
    constraints: List[str]

    # 选项分析
    options_considered: List[DecisionOption]
    chosen_option: str
    rationale: str

    # 后果分析
    positive_consequences: List[str]
    negative_consequences: List[str]

    # 实施相关
    implementation_plan: List[str]
    validation_criteria: List[str]
    estimated_time: str
    responsible_agents: List[str]

    # 后续跟踪
    follow_up_actions: List[str]
    related_decisions: List[str]

    # 元数据
    execution_id: Optional[str] = None
    workflow_stage: Optional[str] = None
    quality_impact: Optional[str] = None
    risk_level: Optional[str] = None

class ADRManager:
    """架构决策记录管理器"""

    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.knowledge_path = os.path.join(self.base_path, "..", "knowledge")
        self.decisions_path = os.path.join(self.knowledge_path, "decisions")

        # 确保目录存在
        os.makedirs(self.decisions_path, exist_ok=True)

        # 加载现有决策
        self.decisions: Dict[str, ArchitecturalDecision] = {}
        self._load_existing_decisions()

        # 决策计数器
        self.decision_counter = self._get_next_decision_id()

        logger.info("ADR管理器初始化完成")

    def _load_existing_decisions(self):
        """加载现有的架构决策"""
        try:
            for filename in os.listdir(self.decisions_path):
                if filename.startswith("ADR-") and filename.endswith(".md"):
                    decision = self._parse_adr_file(
                        os.path.join(self.decisions_path, filename)
                    )
                    if decision:
                        self.decisions[decision.id] = decision

            logger.info(f"加载了 {len(self.decisions)} 个现有决策记录")
        except Exception as e:
            logger.error(f"加载现有决策记录失败: {e}")

    def _get_next_decision_id(self) -> int:
        """获取下一个决策ID"""
        if not self.decisions:
            return 1

        max_id = 0
        for decision_id in self.decisions.keys():
            try:
                # 从 "ADR-001" 格式中提取数字
                id_num = int(decision_id.split("-")[1])
                max_id = max(max_id, id_num)
            except (IndexError, ValueError):
                continue

        return max_id + 1

    def record_decision(self,
                       title: str,
                       context: str,
                       problem_statement: str,
                       options: List[Dict[str, Any]],
                       chosen_option: str,
                       rationale: str,
                       deciders: List[str],
                       technical_domain: str,
                       **kwargs) -> str:
        """
        记录一个新的架构决策

        Args:
            title: 决策标题
            context: 决策上下文
            problem_statement: 问题陈述
            options: 考虑的选项列表
            chosen_option: 选择的选项
            rationale: 选择理由
            deciders: 决策者(agents)列表
            technical_domain: 技术领域
            **kwargs: 其他可选参数

        Returns:
            决策ID
        """

        # 生成决策ID
        decision_id = f"ADR-{self.decision_counter:03d}"
        self.decision_counter += 1

        # 转换选项格式
        decision_options = []
        for opt in options:
            decision_options.append(DecisionOption(
                name=opt.get("name", ""),
                description=opt.get("description", ""),
                pros=opt.get("pros", []),
                cons=opt.get("cons", []),
                cost_estimate=opt.get("cost_estimate", "待评估"),
                implementation_effort=opt.get("implementation_effort", "待评估")
            ))

        # 创建决策记录
        decision = ArchitecturalDecision(
            id=decision_id,
            title=title,
            status=DecisionStatus.PROPOSED,
            date=datetime.now(),
            deciders=deciders,
            technical_domain=TechnicalDomain(technical_domain),
            context=context,
            problem_statement=problem_statement,
            decision_drivers=kwargs.get("decision_drivers", []),
            constraints=kwargs.get("constraints", []),
            options_considered=decision_options,
            chosen_option=chosen_option,
            rationale=rationale,
            positive_consequences=kwargs.get("positive_consequences", []),
            negative_consequences=kwargs.get("negative_consequences", []),
            implementation_plan=kwargs.get("implementation_plan", []),
            validation_criteria=kwargs.get("validation_criteria", []),
            estimated_time=kwargs.get("estimated_time", "待评估"),
            responsible_agents=kwargs.get("responsible_agents", deciders),
            follow_up_actions=kwargs.get("follow_up_actions", []),
            related_decisions=kwargs.get("related_decisions", []),
            execution_id=kwargs.get("execution_id"),
            workflow_stage=kwargs.get("workflow_stage"),
            quality_impact=kwargs.get("quality_impact", "medium"),
            risk_level=kwargs.get("risk_level", "medium")
        )

        # 保存决策
        self.decisions[decision_id] = decision
        self._save_decision_to_file(decision)

        logger.info(f"记录新的架构决策: {decision_id} - {title}")
        return decision_id

    def approve_decision(self, decision_id: str, approver: str) -> bool:
        """批准一个决策"""
        if decision_id not in self.decisions:
            logger.error(f"决策不存在: {decision_id}")
            return False

        decision = self.decisions[decision_id]
        decision.status = DecisionStatus.ACCEPTED

        # 添加批准者信息
        if approver not in decision.deciders:
            decision.deciders.append(f"{approver} (approver)")

        # 重新保存
        self._save_decision_to_file(decision)

        logger.info(f"决策 {decision_id} 已被 {approver} 批准")
        return True

    def deprecate_decision(self, decision_id: str, reason: str,
                          replacement_id: Optional[str] = None) -> bool:
        """废弃一个决策"""
        if decision_id not in self.decisions:
            logger.error(f"决策不存在: {decision_id}")
            return False

        decision = self.decisions[decision_id]

        if replacement_id:
            decision.status = DecisionStatus.SUPERSEDED
            if replacement_id not in decision.related_decisions:
                decision.related_decisions.append(f"被 {replacement_id} 替代")
        else:
            decision.status = DecisionStatus.DEPRECATED

        # 添加废弃原因
        decision.negative_consequences.append(f"废弃原因: {reason}")

        # 重新保存
        self._save_decision_to_file(decision)

        logger.info(f"决策 {decision_id} 已废弃: {reason}")
        return True

    def get_decision(self, decision_id: str) -> Optional[ArchitecturalDecision]:
        """获取决策详情"""
        return self.decisions.get(decision_id)

    def search_decisions(self,
                        domain: Optional[str] = None,
                        status: Optional[str] = None,
                        agent: Optional[str] = None,
                        keyword: Optional[str] = None) -> List[ArchitecturalDecision]:
        """搜索决策记录"""
        results = []

        for decision in self.decisions.values():
            # 按领域过滤
            if domain and decision.technical_domain.value != domain:
                continue

            # 按状态过滤
            if status and decision.status.value != status:
                continue

            # 按参与agent过滤
            if agent and agent not in decision.deciders and agent not in decision.responsible_agents:
                continue

            # 按关键词过滤
            if keyword:
                search_text = f"{decision.title} {decision.context} {decision.problem_statement}".lower()
                if keyword.lower() not in search_text:
                    continue

            results.append(decision)

        # 按日期排序
        results.sort(key=lambda d: d.date, reverse=True)
        return results

    def get_domain_decisions(self, domain: str) -> List[ArchitecturalDecision]:
        """获取特定技术领域的决策"""
        return self.search_decisions(domain=domain)

    def get_agent_decisions(self, agent: str) -> List[ArchitecturalDecision]:
        """获取特定agent参与的决策"""
        return self.search_decisions(agent=agent)

    def generate_decision_summary(self) -> Dict[str, Any]:
        """生成决策摘要统计"""
        summary = {
            "total_decisions": len(self.decisions),
            "by_status": {},
            "by_domain": {},
            "by_agent": {},
            "recent_decisions": [],
            "high_impact_decisions": []
        }

        # 按状态统计
        for decision in self.decisions.values():
            status = decision.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # 按领域统计
        for decision in self.decisions.values():
            domain = decision.technical_domain.value
            summary["by_domain"][domain] = summary["by_domain"].get(domain, 0) + 1

        # 按agent统计
        for decision in self.decisions.values():
            for agent in decision.deciders:
                summary["by_agent"][agent] = summary["by_agent"].get(agent, 0) + 1

        # 最近的决策（最近5个）
        recent = sorted(self.decisions.values(), key=lambda d: d.date, reverse=True)[:5]
        summary["recent_decisions"] = [
            {
                "id": d.id,
                "title": d.title,
                "domain": d.technical_domain.value,
                "date": d.date.isoformat()
            }
            for d in recent
        ]

        # 高影响决策
        high_impact = [
            d for d in self.decisions.values()
            if d.quality_impact == "high" or d.risk_level == "high"
        ]
        summary["high_impact_decisions"] = [
            {
                "id": d.id,
                "title": d.title,
                "quality_impact": d.quality_impact,
                "risk_level": d.risk_level
            }
            for d in high_impact
        ]

        return summary

    def auto_detect_decision_points(self, agent_output: str,
                                   agents_involved: List[str],
                                   execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        自动检测agent输出中的潜在决策点

        这是Perfect21的智能功能，可以自动识别需要记录的架构决策
        """
        decision_indicators = [
            "选择", "决定", "采用", "使用", "方案",
            "架构", "技术栈", "数据库", "缓存", "认证",
            "部署", "测试策略", "安全方案"
        ]

        potential_decisions = []

        # 分析输出文本
        lines = agent_output.split('\n')
        current_decision = None

        for line in lines:
            line_lower = line.lower()

            # 检测决策指示词
            if any(indicator in line_lower for indicator in decision_indicators):
                # 提取决策信息
                decision_info = self._extract_decision_info(line, agent_output)
                if decision_info:
                    decision_info.update({
                        "detected_agents": agents_involved,
                        "execution_context": execution_context,
                        "confidence": self._calculate_decision_confidence(line, agent_output)
                    })
                    potential_decisions.append(decision_info)

        return potential_decisions

    def _extract_decision_info(self, line: str, full_output: str) -> Optional[Dict[str, Any]]:
        """从文本中提取决策信息"""
        # 这里使用简单的规则，实际可以使用更复杂的NLP

        # 查找技术领域关键词
        domain_keywords = {
            "数据库": "database",
            "前端": "frontend",
            "后端": "backend",
            "API": "api",
            "安全": "security",
            "部署": "devops",
            "测试": "testing"
        }

        detected_domain = "architecture"  # 默认
        for keyword, domain in domain_keywords.items():
            if keyword.lower() in line.lower():
                detected_domain = domain
                break

        # 尝试提取选项和理由
        if "因为" in line or "由于" in line or "考虑到" in line:
            return {
                "title": line.strip(),
                "domain": detected_domain,
                "context": "从agent输出自动检测",
                "needs_review": True
            }

        return None

    def _calculate_decision_confidence(self, line: str, full_output: str) -> float:
        """计算决策置信度"""
        confidence = 0.5  # 基础置信度

        # 如果有明确的比较和理由，置信度更高
        if any(word in line.lower() for word in ["比较", "优于", "更好", "选择"]):
            confidence += 0.2

        if any(word in line.lower() for word in ["因为", "由于", "考虑到", "基于"]):
            confidence += 0.2

        # 如果在上下文中提到多个选项，置信度更高
        option_words = ["方案", "选项", "选择", "替代"]
        if sum(full_output.lower().count(word) for word in option_words) > 1:
            confidence += 0.1

        return min(confidence, 1.0)

    def _save_decision_to_file(self, decision: ArchitecturalDecision):
        """保存决策到文件"""
        filename = f"{decision.id}_{decision.title.replace(' ', '_')}.md"
        # 移除文件名中的特殊字符
        filename = re.sub(r'[^\w\-_.]', '', filename)

        filepath = os.path.join(self.decisions_path, filename)

        content = self._generate_adr_markdown(decision)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"ADR文件已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存ADR文件失败: {e}")

    def _generate_adr_markdown(self, decision: ArchitecturalDecision) -> str:
        """生成ADR的Markdown内容"""
        content = f"""# {decision.id}: {decision.title}

**状态**: {decision.status.value}
**日期**: {decision.date.strftime('%Y-%m-%d')}
**决策者**: {', '.join(decision.deciders)}
**技术领域**: {decision.technical_domain.value}

## 上下文和问题陈述

{decision.context}

{decision.problem_statement}

## 决策驱动因素

"""
        for driver in decision.decision_drivers:
            content += f"- {driver}\n"

        if decision.constraints:
            content += "\n## 约束条件\n\n"
            for constraint in decision.constraints:
                content += f"- {constraint}\n"

        content += "\n## 考虑的选项\n\n"
        for i, option in enumerate(decision.options_considered, 1):
            content += f"""### 选项{i}: {option.name}
**描述**: {option.description}
**优点**:
"""
            for pro in option.pros:
                content += f"- {pro}\n"

            content += "**缺点**:\n"
            for con in option.cons:
                content += f"- {con}\n"

            content += f"**成本**: {option.cost_estimate}\n"
            content += f"**实施工作量**: {option.implementation_effort}\n\n"

        content += f"""## 决策结果

**选择的选项**: {decision.chosen_option}

**理由**: {decision.rationale}

## 积极后果

"""
        for pos in decision.positive_consequences:
            content += f"- {pos}\n"

        content += "\n## 消极后果\n\n"
        for neg in decision.negative_consequences:
            content += f"- {neg}\n"

        if decision.implementation_plan:
            content += "\n## 实施计划\n\n"
            for i, step in enumerate(decision.implementation_plan, 1):
                content += f"{i}. {step}\n"

            content += f"\n**预计时间**: {decision.estimated_time}\n"
            content += f"**负责agents**: {', '.join(decision.responsible_agents)}\n"

        if decision.validation_criteria:
            content += "\n## 验证标准\n\n如何验证这个决策是否成功：\n"
            for criteria in decision.validation_criteria:
                content += f"- {criteria}\n"

        if decision.follow_up_actions:
            content += "\n## 后续行动\n\n"
            for action in decision.follow_up_actions:
                content += f"- [ ] {action}\n"

        if decision.related_decisions:
            content += "\n## 相关决策\n\n"
            for related in decision.related_decisions:
                content += f"- {related}\n"

        # 元数据
        content += "\n## 元数据\n\n"
        if decision.execution_id:
            content += f"- **执行ID**: {decision.execution_id}\n"
        if decision.workflow_stage:
            content += f"- **工作流阶段**: {decision.workflow_stage}\n"
        if decision.quality_impact:
            content += f"- **质量影响**: {decision.quality_impact}\n"
        if decision.risk_level:
            content += f"- **风险级别**: {decision.risk_level}\n"

        content += f"""
---

*此ADR由Perfect21 ADR管理器自动生成和维护*
"""
        return content

    def _parse_adr_file(self, filepath: str) -> Optional[ArchitecturalDecision]:
        """解析现有的ADR文件"""
        # 这里简化实现，实际可以用更复杂的解析逻辑
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 从文件名提取ID
            filename = os.path.basename(filepath)
            id_match = re.match(r'ADR-(\d+)', filename)
            if not id_match:
                return None

            decision_id = f"ADR-{id_match.group(1)}"

            # 简单解析标题
            title_match = re.search(r'# ADR-\d+: (.+)', content)
            title = title_match.group(1) if title_match else "未知决策"

            # 创建基本决策对象（简化版）
            decision = ArchitecturalDecision(
                id=decision_id,
                title=title,
                status=DecisionStatus.ACCEPTED,  # 默认
                date=datetime.now(),
                deciders=[],
                technical_domain=TechnicalDomain.ARCHITECTURE,
                context="从现有文件加载",
                problem_statement="",
                decision_drivers=[],
                constraints=[],
                options_considered=[],
                chosen_option="",
                rationale="",
                positive_consequences=[],
                negative_consequences=[],
                implementation_plan=[],
                validation_criteria=[],
                estimated_time="",
                responsible_agents=[],
                follow_up_actions=[],
                related_decisions=[]
            )

            return decision

        except Exception as e:
            logger.error(f"解析ADR文件失败 {filepath}: {e}")
            return None

# 全局实例
_adr_manager = None

def get_adr_manager() -> ADRManager:
    """获取ADR管理器实例"""
    global _adr_manager
    if _adr_manager is None:
        _adr_manager = ADRManager()
    return _adr_manager