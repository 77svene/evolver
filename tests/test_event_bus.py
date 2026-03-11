import pytest
import asyncio
from src.marketing_organism.event_bus.bus import EventBus
from src.marketing_organism.event_bus.events import BaseEvent

class CustomTestEvent(BaseEvent):
    metric: str = "test"
    value: float = 1.0

@pytest.mark.asyncio
async def test_event_bus():
    bus = EventBus()
    bus.start()

    received_events = []

    async def callback(topic, event):
        received_events.append((topic, event))

    bus.subscribe("test.*", callback)

    event1 = CustomTestEvent(source="test", metadata={})
    await bus.publish("test.event1", event1)

    # Wait for processing
    await asyncio.sleep(0.1)

    await bus.stop()

    assert len(received_events) == 1
    assert received_events[0][0] == "test.event1"
    assert received_events[0][1].id == event1.id
