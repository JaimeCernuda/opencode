"""Unit tests for event bus."""

import pytest
import asyncio
from opencode_tui_adapter.events.bus import EventBus
from opencode_tui_adapter.events.models import Event


@pytest.mark.asyncio
async def test_subscribe_unsubscribe():
    """Test subscribing and unsubscribing."""
    bus = EventBus()

    queue_id, queue = bus.subscribe()

    assert queue_id in bus.queues
    assert queue is not None

    bus.unsubscribe(queue_id)
    assert queue_id not in bus.queues


@pytest.mark.asyncio
async def test_broadcast_event():
    """Test broadcasting an event."""
    bus = EventBus()

    queue_id, queue = bus.subscribe()

    event = Event(
        type="session.updated",
        properties={"test": "data"}
    )

    await bus.broadcast(event)

    # Event should be in the queue
    received_event = await asyncio.wait_for(queue.get(), timeout=1.0)

    assert received_event.type == "session.updated"
    assert received_event.properties["test"] == "data"

    bus.unsubscribe(queue_id)


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test broadcasting to multiple subscribers."""
    bus = EventBus()

    queue_id_1, queue_1 = bus.subscribe()
    queue_id_2, queue_2 = bus.subscribe()

    event = Event(
        type="message.updated",
        properties={"message": "test"}
    )

    await bus.broadcast(event)

    # Both queues should receive the event
    event_1 = await asyncio.wait_for(queue_1.get(), timeout=1.0)
    event_2 = await asyncio.wait_for(queue_2.get(), timeout=1.0)

    assert event_1.type == "message.updated"
    assert event_2.type == "message.updated"

    bus.unsubscribe(queue_id_1)
    bus.unsubscribe(queue_id_2)
