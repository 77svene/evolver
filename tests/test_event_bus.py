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

@pytest.mark.asyncio
async def test_dlq_on_error():
    bus = EventBus()
    bus.start()

    async def failing_callback(topic, event):
        raise ValueError("Simulated failure")

    bus.subscribe("error.*", failing_callback)

    event1 = CustomTestEvent(source="test", metadata={})
    await bus.publish("error.event1", event1)

    await asyncio.sleep(0.1)

    assert bus.dlq.qsize() == 1
    dlq_item = await bus.dlq.get()

    assert dlq_item[0] == "error.event1"
    assert dlq_item[1].id == event1.id
    assert "Simulated failure" in dlq_item[2]

    await bus.stop()
