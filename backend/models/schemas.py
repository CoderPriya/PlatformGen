from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, enum.Enum):
    ORCHESTRATOR = "orchestrator"
    REQUIREMENTS = "requirements"
    BUSINESS_ANALYST = "business_analyst"
    ARCHITECT = "architect"
    CODE_GENERATOR = "code_generator"
    CODE_REVIEWER = "code_reviewer"
    QA = "qa"
    SECURITY = "security"
    DEVOPS = "devops"
    SRE = "sre"
    DOCUMENTATION = "documentation"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ConfidenceBand(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class SDLCStage(str, enum.Enum):
    REQUIREMENTS = "requirements"
    BUSINESS_ANALYSIS = "business_analysis"
    ARCHITECTURE = "architecture"
    TASK_BREAKDOWN = "task_breakdown"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    SECURITY_SCAN = "security_scan"
    CI_CD = "ci_cd"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"
    FEEDBACK = "feedback"


# ---------------------------------------------------------------------------
# Event Bus
# ---------------------------------------------------------------------------

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    source_agent: AgentType
    workflow_id: str
    payload: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Agent I/O
# ---------------------------------------------------------------------------

class AgentInput(BaseModel):
    workflow_id: str
    stage: SDLCStage
    context: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}


class AgentOutput(BaseModel):
    agent_type: AgentType
    workflow_id: str
    stage: SDLCStage
    artifacts: dict[str, Any] = {}
    confidence: float = 0.0
    confidence_band: ConfidenceBand = ConfidenceBand.MEDIUM
    reasoning: str = ""
    requires_approval: bool = False
    approval_gate_name: str = ""
    next_stage: SDLCStage | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

class WorkflowCreate(BaseModel):
    title: str
    description: str
    business_brief: str
    project_name: str = "default-project"


class WorkflowState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    business_brief: str
    project_name: str = "default-project"
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_stage: SDLCStage = SDLCStage.REQUIREMENTS
    artifacts: dict[str, Any] = {}
    agent_outputs: list[AgentOutput] = []
    approval_gates: list[ApprovalGate] = []
    events: list[Event] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalGate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    stage: SDLCStage
    gate_name: str
    agent_type: AgentType
    status: ApprovalStatus = ApprovalStatus.PENDING
    context: dict[str, Any] = {}
    artifacts_for_review: dict[str, Any] = {}
    reviewer_notes: str = ""
    decided_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = None


# ---------------------------------------------------------------------------
# API responses
# ---------------------------------------------------------------------------

class WorkflowSummary(BaseModel):
    id: str
    title: str
    project_name: str
    status: WorkflowStatus
    current_stage: SDLCStage
    created_at: datetime
    updated_at: datetime


class AgentStatus(BaseModel):
    agent_type: AgentType
    is_active: bool = True
    current_workflow_id: str | None = None
    tasks_completed: int = 0
    last_active: datetime | None = None


class DashboardData(BaseModel):
    workflows: list[WorkflowSummary] = []
    pending_approvals: list[ApprovalGate] = []
    agent_statuses: list[AgentStatus] = []
    recent_events: list[Event] = []
