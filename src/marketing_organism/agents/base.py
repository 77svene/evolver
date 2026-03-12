from abc import ABC, abstractmethod
import asyncio
from typing import Dict, Any, List
import uuid
import logging

from src.marketing_organism.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str = None, max_memory_events: int = 100):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.memory: Dict[str, Any] = {}
        self.state: str = "initialized"
        self._running = False
        self._task = None
        self.event_queue = asyncio.Queue()
        self.max_memory_events = max_memory_events
        self._consecutive_errors = 0

    async def perceive(self, event):
        """Called by event bus when subscribed events occur."""
        await self.event_queue.put(event)

    @abstractmethod
    async def decide(self) -> Any:
        """Evaluate internal state and memory to decide next action."""
        pass

    @abstractmethod
    async def act(self, action: Any):
        """Execute the decided action."""
        pass

    async def _loop(self):
        """Main agent perception-decision-action loop."""
        while self._running:
            try:
                # Perceive: fetch new events
                # Use a timeout to ensure we periodically evaluate state
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    self._process_event(event)
                    self.event_queue.task_done()
                except asyncio.TimeoutError:
                    pass

                # Decide
                action = await self.decide()

                # Act
                if action:
                    await self.act(action)

                self._consecutive_errors = 0  # reset on success

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_errors += 1
                backoff_time = min(60, (2 ** self._consecutive_errors))
                logger.error(
                    f"AgentExecutionError: Error in agent loop for {self.agent_id}: {e}. Backing off for {backoff_time}s",
                    exc_info=True
                )
                await asyncio.sleep(backoff_time)

    def _process_event(self, event):
        """Internal method to update memory based on perceived event."""
        # Derived classes can override to format event for memory
        if "recent_events" not in self.memory:
            self.memory["recent_events"] = []
        self.memory["recent_events"].append(event)

        # Enforce memory eviction policy (FIFO based on configured limit)
        if len(self.memory["recent_events"]) > self.max_memory_events:
            self.memory["recent_events"] = self.memory["recent_events"][-self.max_memory_events:]

    def start(self):
        if not self._running:
            self.state = "running"
            self._running = True
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self.state = "stopped"
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
