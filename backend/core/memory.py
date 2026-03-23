"""
Three-tier memory layer matching the architecture document:

- Working Memory  – per-workflow scratch-pad (dict, simulates Redis)
- Episodic Memory – per-project persistent store (SQLite, simulates PostgreSQL)
- Long-Term Memory – cross-project knowledge (in-memory list, simulates Vector DB)

In production, replace with Redis / PostgreSQL+pgvector / Pinecone.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from backend.models.database import (
    AgentOutputRecord,
    EventRecord,
    WorkflowRecord,
    get_session_factory,
)

logger = logging.getLogger(__name__)


class WorkingMemory:
    """Per-workflow in-memory context (simulates Redis)."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, workflow_id: str, key: str, default: Any = None) -> Any:
        return self._store[workflow_id].get(key, default)

    def set(self, workflow_id: str, key: str, value: Any):
        self._store[workflow_id][key] = value

    def get_all(self, workflow_id: str) -> dict[str, Any]:
        return dict(self._store[workflow_id])

    def delete_workflow(self, workflow_id: str):
        self._store.pop(workflow_id, None)


class EpisodicMemory:
    """Persistent per-project store (simulates PostgreSQL)."""

    def save_workflow(self, workflow_state: dict):
        factory = get_session_factory()
        with factory() as session:
            existing = session.get(WorkflowRecord, workflow_state["id"])
            if existing:
                existing.title = workflow_state["title"]
                existing.description = workflow_state.get("description", "")
                existing.business_brief = workflow_state.get("business_brief", "")
                existing.project_name = workflow_state.get("project_name", "default-project")
                existing.status = workflow_state.get("status", "pending")
                existing.current_stage = workflow_state.get("current_stage", "requirements")
                existing.artifacts_json = json.dumps(workflow_state.get("artifacts", {}), default=str)
                existing.updated_at = datetime.utcnow()
            else:
                record = WorkflowRecord(
                    id=workflow_state["id"],
                    title=workflow_state["title"],
                    description=workflow_state.get("description", ""),
                    business_brief=workflow_state.get("business_brief", ""),
                    project_name=workflow_state.get("project_name", "default-project"),
                    status=workflow_state.get("status", "pending"),
                    current_stage=workflow_state.get("current_stage", "requirements"),
                    artifacts_json=json.dumps(workflow_state.get("artifacts", {}), default=str),
                )
                session.add(record)
            session.commit()

    def save_agent_output(self, output: dict):
        factory = get_session_factory()
        with factory() as session:
            record = AgentOutputRecord(
                id=str(uuid.uuid4()),
                workflow_id=output["workflow_id"],
                agent_type=output["agent_type"],
                stage=output["stage"],
                artifacts_json=json.dumps(output.get("artifacts", {}), default=str),
                confidence=output.get("confidence", 0.0),
                reasoning=output.get("reasoning", ""),
            )
            session.add(record)
            session.commit()

    def save_event(self, event: dict):
        factory = get_session_factory()
        with factory() as session:
            record = EventRecord(
                id=event.get("id", str(uuid.uuid4())),
                topic=event["topic"],
                source_agent=event["source_agent"],
                workflow_id=event["workflow_id"],
                payload_json=json.dumps(event.get("payload", {}), default=str),
            )
            session.add(record)
            session.commit()


class LongTermMemory:
    """Cross-project knowledge store (simulates Vector DB / knowledge graph).

    Stores patterns, coding standards, past ADRs, RCAs, etc.
    """

    def __init__(self):
        self._knowledge: list[dict[str, Any]] = []

    def store(self, entry: dict[str, Any]):
        entry.setdefault("id", str(uuid.uuid4()))
        entry.setdefault("timestamp", datetime.utcnow().isoformat())
        self._knowledge.append(entry)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Naive keyword search. Replace with vector similarity in production."""
        query_lower = query.lower()
        scored = []
        for entry in self._knowledge:
            text = json.dumps(entry).lower()
            score = sum(1 for word in query_lower.split() if word in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._knowledge)


# Singletons
_working: WorkingMemory | None = None
_episodic: EpisodicMemory | None = None
_longterm: LongTermMemory | None = None


def get_working_memory() -> WorkingMemory:
    global _working
    if _working is None:
        _working = WorkingMemory()
    return _working


def get_episodic_memory() -> EpisodicMemory:
    global _episodic
    if _episodic is None:
        _episodic = EpisodicMemory()
    return _episodic


def get_long_term_memory() -> LongTermMemory:
    global _longterm
    if _longterm is None:
        _longterm = LongTermMemory()
    return _longterm
