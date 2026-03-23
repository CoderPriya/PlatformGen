"""Human-in-the-loop approval gate endpoints."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.core.workflow import get_workflow_engine
from backend.models.schemas import ApprovalGate, ApprovalStatus

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    decided_by: str
    notes: str = ""


@router.get("", response_model=list[ApprovalGate])
async def list_pending_approvals():
    """List all pending approval gates across workflows."""
    engine = get_workflow_engine()
    return engine.get_pending_approvals()


@router.get("/{workflow_id}", response_model=list[ApprovalGate])
async def get_workflow_approvals(workflow_id: str):
    """Get all approval gates for a specific workflow."""
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.approval_gates


@router.post("/{workflow_id}/{gate_id}/approve", response_model=ApprovalGate)
async def approve_gate(workflow_id: str, gate_id: str, decision: ApprovalDecision):
    """Approve an approval gate."""
    engine = get_workflow_engine()
    gate = await engine.approve_gate(workflow_id, gate_id, decision.decided_by, decision.notes)
    if not gate:
        raise HTTPException(status_code=404, detail="Gate not found")
    return gate


@router.post("/{workflow_id}/{gate_id}/reject", response_model=ApprovalGate)
async def reject_gate(workflow_id: str, gate_id: str, decision: ApprovalDecision):
    """Reject an approval gate, halting the workflow."""
    engine = get_workflow_engine()
    gate = await engine.reject_gate(workflow_id, gate_id, decision.decided_by, decision.notes)
    if not gate:
        raise HTTPException(status_code=404, detail="Gate not found")
    return gate
