"""Event bus for SSE broadcasting."""

import asyncio
from typing import Dict, Set
import uuid

import structlog

from .models import Event
from ..logging.config import trace_function


logger = structlog.get_logger(__name__)


class EventBus:
    """Event bus for broadcasting events to SSE clients."""

    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        logger.debug("event_bus_initialized")

    @trace_function
    def subscribe(self) -> tuple[str, asyncio.Queue]:
        """Subscribe to events and return queue ID and queue."""
        queue_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        self.queues[queue_id] = queue

        logger.debug("event_bus_subscribe", queue_id=queue_id, total_subscribers=len(self.queues))
        return queue_id, queue

    @trace_function
    def unsubscribe(self, queue_id: str) -> None:
        """Unsubscribe from events."""
        if queue_id in self.queues:
            del self.queues[queue_id]
            logger.debug("event_bus_unsubscribe", queue_id=queue_id, remaining_subscribers=len(self.queues))
        else:
            logger.debug("event_bus_unsubscribe_not_found", queue_id=queue_id)

    @trace_function
    async def broadcast(self, event: Event) -> None:
        """Broadcast an event to all subscribers."""
        logger.debug("event_bus_broadcast_start", event_type=event.type, subscriber_count=len(self.queues))

        # Add event to all queues
        successful = 0
        failed = 0
        for queue_id, queue in list(self.queues.items()):
            try:
                await queue.put(event)
                successful += 1
                logger.debug("event_bus_event_queued", queue_id=queue_id, event_type=event.type)
            except Exception as e:
                failed += 1
                logger.warning(
                    "event_bus_broadcast_error",
                    queue_id=queue_id,
                    event_type=event.type,
                    error=str(e),
                    exception_type=type(e).__name__
                )

        logger.debug("event_bus_broadcast_complete", event_type=event.type, successful=successful, failed=failed)


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
