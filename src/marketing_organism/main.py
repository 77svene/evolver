import asyncio
import logging
from src.marketing_organism.event_bus.bus import EventBus
from src.marketing_organism.agents.lifecycle import AgentManager
from src.marketing_organism.agents.base import BaseAgent
from src.marketing_organism.evolution.selection import EvolutionarySelector
from src.marketing_organism.knowledge.graph import KnowledgeGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("organism_main")

class OrchestratorAgent(BaseAgent):
    """A baseline agent to handle system orchestration tasks."""
    async def decide(self):
        # The orchestrator could check system health or DLQ here
        await asyncio.sleep(5)
        return "health_check"

    async def act(self, action):
        if action == "health_check":
            logger.info("Orchestrator Agent: System is healthy.")

async def main():
    logger.info("Starting Autonomous Adaptive Marketing Ecosystem Orchestrator...")

    # 1. Initialize Event Bus
    event_bus = EventBus(dlq_max_size=1000)
    event_bus.start()

    # 2. Initialize Knowledge Graph
    knowledge_graph = KnowledgeGraph(in_memory=False, db_path="marketing_organism.db")
    logger.info("Knowledge Graph initialized.")

    # 3. Initialize Evolution Engine
    evolution_engine = EvolutionarySelector()
    logger.info("Evolution Engine initialized.")

    # 4. Initialize Agent Manager and spawn baseline agent
    agent_manager = AgentManager()
    orchestrator = agent_manager.spawn_agent(OrchestratorAgent, config={"role": "orchestrator"})
    logger.info(f"Orchestrator Agent spawned with ID: {orchestrator.agent_id}")

    try:
        # Keep the main loop alive
        while True:
            await asyncio.sleep(60)

            # Periodically evaluate agents
            underperforming = agent_manager.evaluate_agents(threshold=0.3)
            for agent_id in underperforming:
                logger.info(f"Retiring underperforming agent: {agent_id}")
                await agent_manager.retire_agent(agent_id)

    except asyncio.CancelledError:
        logger.info("Shutting down ecosystem...")
    finally:
        await event_bus.stop()
        for agent_id in list(agent_manager.active_agents.keys()):
            await agent_manager.retire_agent(agent_id)
        logger.info("Ecosystem shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")