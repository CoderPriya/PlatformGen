"""
Database layer using synchronous SQLite via SQLAlchemy.

For the POC, we use synchronous SQLAlchemy with SQLite to avoid greenlet
DLL issues on Windows. In production, switch to async PostgreSQL.
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent.parent / "platformgen.db"
_engine = None
_session_factory = None


class Base(DeclarativeBase):
    pass


class WorkflowRecord(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    business_brief = Column(Text, default="")
    project_name = Column(String, default="default-project")
    status = Column(String, default="pending")
    current_stage = Column(String, default="requirements")
    artifacts_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def artifacts(self) -> dict:
        return json.loads(self.artifacts_json or "{}")

    @artifacts.setter
    def artifacts(self, value: dict):
        self.artifacts_json = json.dumps(value, default=str)


class AgentOutputRecord(Base):
    __tablename__ = "agent_outputs"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=False, index=True)
    agent_type = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    artifacts_json = Column(Text, default="{}")
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=False, index=True)
    stage = Column(String, nullable=False)
    gate_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    context_json = Column(Text, default="{}")
    artifacts_json = Column(Text, default="{}")
    reviewer_notes = Column(Text, default="")
    decided_by = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)


class EventRecord(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False, index=True)
    source_agent = Column(String, nullable=False)
    workflow_id = Column(String, nullable=False, index=True)
    payload_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)


def get_db() -> Session:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
