"""
Claude Enhancer v2.0 - Agent Selector
======================================

Intelligent agent selection based on task analysis.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AgentSelector:
    """
    Selects appropriate agents for tasks

    Analyzes tasks and selects the optimal combination of
    specialized agents to handle the work.
    """

    # Agent definitions
    AGENTS = {
        "orchestrator": "Coordinates multi-agent workflows",
        "backend-architect": "Backend architecture and design",
        "fullstack-engineer": "Full-stack implementation",
        "test-engineer": "Testing and quality assurance",
        "technical-writer": "Documentation and guides",
        "code-reviewer": "Code review and quality",
        "security-auditor": "Security analysis",
        "devops-engineer": "DevOps and deployment",
        "python-pro": "Python expert",
        "typescript-pro": "TypeScript expert"
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize agent selector

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.task_agent_mapping = self._load_task_mappings()

    def _load_task_mappings(self) -> Dict[str, List[str]]:
        """Load task to agent mappings"""
        return {
            "architecture": ["backend-architect", "fullstack-engineer"],
            "implementation": ["fullstack-engineer", "python-pro"],
            "testing": ["test-engineer", "fullstack-engineer"],
            "documentation": ["technical-writer"],
            "review": ["code-reviewer", "security-auditor"],
            "deployment": ["devops-engineer"]
        }

    def select_agents(self, task: Dict[str, Any]) -> List[str]:
        """
        Select agents for a task

        Args:
            task: Task description dictionary

        Returns:
            List of agent names to use
        """
        task_type = task.get("type", "implementation")
        complexity = task.get("complexity", "standard")

        # Get base agents for task type
        agents = self.task_agent_mapping.get(task_type, ["fullstack-engineer"])

        # Add orchestrator for complex tasks
        if complexity in ["complex", "high"]:
            agents = ["orchestrator"] + agents

        # Ensure minimum agent count (4-6-8 principle)
        min_agents = {
            "simple": 4,
            "standard": 6,
            "complex": 8
        }.get(complexity, 6)

        # Add more agents if needed
        if len(agents) < min_agents:
            additional = [
                "test-engineer",
                "technical-writer",
                "code-reviewer",
                "security-auditor",
                "devops-engineer"
            ]
            for agent in additional:
                if agent not in agents:
                    agents.append(agent)
                    if len(agents) >= min_agents:
                        break

        return agents

    def get_agent_info(self, agent_name: str) -> str:
        """Get agent description"""
        return self.AGENTS.get(agent_name, "Unknown agent")


__all__ = ["AgentSelector"]
