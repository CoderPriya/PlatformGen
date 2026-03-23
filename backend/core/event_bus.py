"""
In-memory event bus simulating Apache Kafka topic-based messaging.

Agents publish events to topics; subscribers receive them asynchronously.
In production, swap this for a real Kafka client.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Awaitable, Callable

from backend.models.schemas import Event

logger = logging.getLogger(__name__)

Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    """Async in-memory pub/sub event bus (Kafka-like topic model)."""

    # Well-known topic names mirroring the architecture doc
    TOPICS = {
        "sdlc.requirements.ready",
        "sdlc.brd.ready",
        "sdlc.brd.approved",
        "sdlc.architecture.ready",
        "sdlc.architecture.approved",
        "sdlc.code.pr_opened",
        "sdlc.review.completed",
        "sdlc.security.completed",
        "sdlc.qa.completed",
        "sdlc.build.completed",
        "sdlc.deployment.staging",
        "sdlc.deployment.production",
        "sdlc.deployment.validated",
        "sdlc.docs.updated",
        "sdlc.alert.fired",
        "sdlc.approval.requested",
        "sdlc.approval.granted",
        "sdlc.approval.rejected",
        "sdlc.workflow.started",
        "sdlc.workflow.completed",
        "sdlc.workflow.failed",
        "sdlc.rework.requested",
    }

    def __init__(self):
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._event_log: list[Event] = []
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, handler: Subscriber):
        self._subscribers[topic].append(handler)
        logger.info("Subscriber registered for topic=%s", topic)

    async def publish(self, event: Event):
        async with self._lock:
            self._event_log.append(event)
        logger.info(
            "Event published: topic=%s source=%s workflow=%s",
            event.topic,
            event.source_agent,
            event.workflow_id,
        )
        for handler in self._subscribers.get(event.topic, []):
            try:
                await handler(event)
            except Exception:
                logger.exception("Subscriber error on topic=%s", event.topic)

    def get_events(self, workflow_id: str | None = None, limit: int = 50) -> list[Event]:
        events = self._event_log
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        return events[-limit:]

    def clear(self):
        self._event_log.clear()
        self._subscribers.clear()


# Singleton
_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
