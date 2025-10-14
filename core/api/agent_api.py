"""
Claude Enhancer v2.0 - Agent API
=================================

Public API for agent operations.
"""

from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


class AgentAPI:
    """
    Public API for agent operations

    Version: 2.0.0
    """

    def __init__(self, selector):
        """
        Initialize agent API

        Args:
            selector: AgentSelector instance
        """
        self.selector = selector
        logger.info("AgentAPI initialized")

    def select_agents(self, task: Dict[str, Any], phase: str) -> List[Dict[str, Any]]:
        """
        Select agents for a task

        Args:
            task: Task dictionary with description and requirements
            phase: Current phase (e.g., "P3")

        Returns:
            List of selected agent dictionaries
        """
        from core.workflow.engine import Phase

        try:
            phase_enum = Phase(phase)
        except ValueError:
            raise ValueError(f"Invalid phase: {phase}")

        agents = self.selector.select(task, phase_enum)

        return [
            {
                'id': agent.id,
                'name': agent.name,
                'capabilities': agent.capabilities,
                'priority': agent.priority
            }
            for agent in agents
        ]

    def get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent profile

        Args:
            agent_id: Agent ID

        Returns:
            Agent profile dictionary
        """
        agent = self.selector.registry.get(agent_id)

        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        return {
            'id': agent.id,
            'name': agent.name,
            'capabilities': agent.capabilities,
            'domains': agent.domains,
            'priority': agent.priority,
            'concurrency_safe': agent.concurrency_safe
        }

    def list_available_agents(self) -> List[Dict[str, Any]]:
        """
        List all available agents

        Returns:
            List of agent dictionaries
        """
        agents = list(self.selector.registry.agents.values())

        return [
            {
                'id': agent.id,
                'name': agent.name,
                'capabilities': agent.capabilities,
                'domains': agent.domains
            }
            for agent in agents
        ]

    def find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Find agents by capability

        Args:
            capability: Capability to search for

        Returns:
            List of matching agent dictionaries
        """
        agents = self.selector.registry.find_by_capability(capability)

        return [
            {
                'id': agent.id,
                'name': agent.name,
                'capabilities': agent.capabilities
            }
            for agent in agents
        ]

    def find_agents_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Find agents by domain

        Args:
            domain: Domain to search for

        Returns:
            List of matching agent dictionaries
        """
        agents = self.selector.registry.find_by_domain(domain)

        return [
            {
                'id': agent.id,
                'name': agent.name,
                'domains': agent.domains
            }
            for agent in agents
        ]
