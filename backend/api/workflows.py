"""Workflow management API endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from backend.core.workflow import get_workflow_engine
from backend.models.schemas import (
    WorkflowCreate,
    WorkflowState,
    WorkflowSummary,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowState)
async def create_workflow(request: WorkflowCreate):
    """Create a new SDLC workflow from a business brief."""
    engine = get_workflow_engine()
    workflow = await engine.create_workflow(request)
    return workflow


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    """Start executing the full SDLC pipeline for a workflow.

    Returns immediately with the workflow state; execution continues in the background.
    """
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    asyncio.create_task(engine.run_workflow(workflow_id))

    return {"status": "started", "workflow_id": workflow_id, "message": "Workflow execution started in background"}


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows():
    """List all workflows with summary info."""
    engine = get_workflow_engine()
    workflows = engine.list_workflows()
    return [
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


@router.get("/{workflow_id}", response_model=WorkflowState)
async def get_workflow(workflow_id: str):
    """Get full workflow state including all artifacts and agent outputs."""
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
