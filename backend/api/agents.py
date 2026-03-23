"""Agent status and event monitoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.core.event_bus import get_event_bus
from backend.core.workflow import get_workflow_engine
from backend.models.schemas import AgentStatus, AgentType, DashboardData, Event, WorkflowSummary

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents", response_model=list[AgentStatus])
async def list_agents():
    """Return the status of all registered agents."""
    engine = get_workflow_engine()
    statuses = []
    for agent_type in AgentType:
        agent_instance = engine._agents.get(agent_type)
        statuses.append(AgentStatus(
            agent_type=agent_type,
            is_active=agent_instance is not None,
            tasks_completed=getattr(agent_instance, "tasks_completed", 0),
            last_active=getattr(agent_instance, "last_active", None),
        ))
    return statuses


@router.get("/events", response_model=list[Event])
async def list_events(workflow_id: str | None = None, limit: int = 100):
    """List recent events, optionally filtered by workflow."""
    bus = get_event_bus()
    return bus.get_events(workflow_id=workflow_id, limit=limit)


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Aggregated dashboard data for the frontend."""
    engine = get_workflow_engine()
    bus = get_event_bus()

    workflows = engine.list_workflows()
    summaries = [
        WorkflowSummary(
            id=wf.id,
            title=wf.title,
            project_name=wf.project_name,
            status=wf.status,
            current_stage=wf.current_stage,
            created_at=wf.created_at,
            updated_at=wf.updated_at,
        )
        for wf in workflows
    ]

    agents_list = []
    for agent_type in AgentType:
        inst = engine._agents.get(agent_type)
        agents_list.append(AgentStatus(
            agent_type=agent_type,
            is_active=inst is not None,
            tasks_completed=getattr(inst, "tasks_completed", 0),
            last_active=getattr(inst, "last_active", None),
        ))

    return DashboardData(
        workflows=summaries,
        pending_approvals=engine.get_pending_approvals(),
        agent_statuses=agents_list,
        recent_events=bus.get_events(limit=50),
    )
