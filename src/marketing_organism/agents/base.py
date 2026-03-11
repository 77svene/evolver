from abc import ABC, abstractmethod
import asyncio
from typing import Dict, Any, List
import uuid

class BaseAgent(ABC):
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.memory: Dict[str, Any] = {}
        self.state: str = "initialized"
        self._running = False
        self._task = None
        self.event_queue = asyncio.Queue()

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

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in agent loop for {self.agent_id}: {e}")
                # Fallback to prevent tight loop errors
                await asyncio.sleep(1)

    def _process_event(self, event):
        """Internal method to update memory based on perceived event."""
        # Derived classes can override to format event for memory
        if "recent_events" not in self.memory:
            self.memory["recent_events"] = []
        self.memory["recent_events"].append(event)
        # Keep last 100 events
        self.memory["recent_events"] = self.memory["recent_events"][-100:]

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
