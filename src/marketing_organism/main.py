import asyncio
import logging
from src.marketing_organism.event_bus.bus import EventBus
from src.marketing_organism.agents.lifecycle import AgentManager
from src.marketing_organism.agents.base import BaseAgent
from src.marketing_organism.evolution.selection import EvolutionarySelector
from src.marketing_organism.knowledge.graph import KnowledgeGraph
from src.marketing_organism.llm.reasoning import PromptChainer
from src.marketing_organism.tool_forge.generator import ToolGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("organism_main")

class OrchestratorAgent(BaseAgent):
    """A baseline agent to handle system orchestration tasks."""
    def __init__(self, *args, event_bus: EventBus = None, knowledge_graph: KnowledgeGraph = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_bus = event_bus
        self.knowledge_graph = knowledge_graph

    async def decide(self):
        # The orchestrator could check system health or DLQ here
        await asyncio.sleep(5)
        return "health_check"

    async def act(self, action):
        if action == "health_check":
            logger.info("Orchestrator Agent: System is healthy.")

async def main():
    logger.info("Starting Autonomous Adaptive Marketing Ecosystem Orchestrator...")

    # 1. Initialize Core Dependencies
    event_bus = EventBus(dlq_max_size=1000)
    event_bus.start()
    logger.info("Event Bus initialized.")

    knowledge_graph = KnowledgeGraph(in_memory=False, db_path="marketing_organism.db")
    logger.info("Knowledge Graph (SQLite) initialized.")

    prompt_chainer = PromptChainer(endpoint_url="http://127.0.0.1:8000")
    tool_generator = ToolGenerator(workspace_path="./generated_tools", prompt_chainer=prompt_chainer)
    logger.info("Tool Forge and LLM Integration initialized.")

    evolution_engine = EvolutionarySelector()
    logger.info("Evolution Engine initialized.")

    # 2. Initialize Agent Manager and spawn baseline agent using Dependency Injection
    agent_manager = AgentManager()
    orchestrator = agent_manager.spawn_agent(
        OrchestratorAgent,
        config={"role": "orchestrator"},
    )
    # Inject dependencies post-spawn or via a custom factory method in a real system
    orchestrator.event_bus = event_bus
    orchestrator.knowledge_graph = knowledge_graph
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