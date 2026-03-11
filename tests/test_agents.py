import pytest
import asyncio
from typing import Any
from src.marketing_organism.agents.base import BaseAgent
from src.marketing_organism.agents.lifecycle import AgentManager
from src.marketing_organism.event_bus.events import BaseEvent

class DummyAgent(BaseAgent):
    async def decide(self) -> Any:
        if self.memory.get("recent_events"):
            return "process_events"
        return None

    async def act(self, action: Any):
        if action == "process_events":
            self.memory["processed"] = True
            self.memory["recent_events"] = []

class CustomTestEvent(BaseEvent):
    metric: str = "test"
    value: float = 1.0

@pytest.mark.asyncio
async def test_agent_lifecycle():
    manager = AgentManager()

    agent = manager.spawn_agent(DummyAgent, config={"custom_var": 42})
    assert agent.state == "running"
    assert agent.memory.get("custom_var") == 42

    event = CustomTestEvent(source="test", metadata={})
    await agent.perceive(event)

    # Wait for the PDA loop to run
    await asyncio.sleep(0.1)

    assert agent.memory.get("processed") is True
    assert len(agent.memory.get("recent_events")) == 0

    await manager.retire_agent(agent.agent_id)
    assert agent.state == "stopped"
    assert agent.agent_id not in manager.active_agents

@pytest.mark.asyncio
async def test_evaluate_agents():
    manager = AgentManager()
    agent1 = manager.spawn_agent(DummyAgent)
    agent2 = manager.spawn_agent(DummyAgent)

    manager.performance_metrics[agent1.agent_id] = 0.8
    manager.performance_metrics[agent2.agent_id] = 0.2

    underperforming = manager.evaluate_agents(threshold=0.5)
    assert len(underperforming) == 1
    assert underperforming[0] == agent2.agent_id

    await manager.retire_agent(agent1.agent_id)
    await manager.retire_agent(agent2.agent_id)
