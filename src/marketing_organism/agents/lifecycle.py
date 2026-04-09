from typing import Dict, Type, Any, Optional
from .base import BaseAgent

class AgentManager:
    def __init__(self):
        self.active_agents: Dict[str, BaseAgent] = {}
        self.performance_metrics: Dict[str, float] = {}
        self.config: Dict[str, Any] = {}

    def spawn_agent(self, agent_class: Type[BaseAgent], agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """Dynamically instantiates and starts an agent."""
        agent = agent_class(agent_id=agent_id)
        if config:
            agent.memory.update(config)

        agent.start()
        self.active_agents[agent.agent_id] = agent
        self.performance_metrics[agent.agent_id] = 1.0 # default starting performance

        return agent

    async def retire_agent(self, agent_id: str):
        """Gracefully stops and removes an underperforming or obsolete agent."""
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            await agent.stop()
            del self.active_agents[agent_id]
            if agent_id in self.performance_metrics:
                del self.performance_metrics[agent_id]

    def evaluate_agents(self, threshold: float = 0.5):
        """Identify agents below the performance threshold for potential retirement."""
        underperforming = []
        for agent_id, metric in self.performance_metrics.items():
            if metric < threshold:
                underperforming.append(agent_id)
        return underperforming
