import asyncio
from typing import Callable, Dict, List
import fnmatch
from .events import BaseEvent

class TopicRouter:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, topic_pattern: str, callback: Callable):
        if topic_pattern not in self.subscriptions:
            self.subscriptions[topic_pattern] = []
        self.subscriptions[topic_pattern].append(callback)

    def unsubscribe(self, topic_pattern: str, callback: Callable):
        if topic_pattern in self.subscriptions:
            try:
                self.subscriptions[topic_pattern].remove(callback)
            except ValueError:
                pass

    def get_callbacks(self, topic: str) -> List[Callable]:
        callbacks = []
        for pattern, subs in self.subscriptions.items():
            if fnmatch.fnmatch(topic, pattern):
                callbacks.extend(subs)
        return callbacks

class EventBus:
    def __init__(self, dlq_max_size: int = 1000):
        self.router = TopicRouter()
        self.queue = asyncio.Queue()
        self.dlq = asyncio.Queue(maxsize=dlq_max_size)
        self._running = False
        self._task = None

    def subscribe(self, topic_pattern: str, callback: Callable):
        self.router.subscribe(topic_pattern, callback)

    def unsubscribe(self, topic_pattern: str, callback: Callable):
        self.router.unsubscribe(topic_pattern, callback)

    async def publish(self, topic: str, event: BaseEvent):
        await self.queue.put((topic, event))

    async def _process_events(self):
        while self._running:
            try:
                topic, event = await self.queue.get()
                callbacks = self.router.get_callbacks(topic)

                # Execute callbacks concurrently
                if callbacks:
                    tasks = []
                    for cb in callbacks:
                        if asyncio.iscoroutinefunction(cb):
                            # Wrap async callbacks to catch exceptions individually and send to DLQ
                            async def safe_cb(callback=cb, t=topic, e=event):
                                try:
                                    await callback(t, e)
                                except Exception as err:
                                    print(f"Error executing async callback for {t}: {err}")
                                    try:
                                        self.dlq.put_nowait((t, e, str(err)))
                                    except asyncio.QueueFull:
                                        pass
                            tasks.append(asyncio.create_task(safe_cb()))
                        else:
                            # If sync callback, just call it directly
                            try:
                                cb(topic, event)
                            except Exception as e:
                                print(f"Error executing sync callback for {topic}: {e}")
                                try:
                                    self.dlq.put_nowait((topic, event, str(e)))
                                except asyncio.QueueFull:
                                    pass

                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in event bus loop: {e}")
                # Send totally failed items to DLQ if possible
                try:
                    self.dlq.put_nowait(("unknown_topic", None, str(e)))
                except (asyncio.QueueFull, NameError):
                    pass

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_events())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
