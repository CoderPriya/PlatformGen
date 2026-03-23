"""
Workflow engine that orchestrates the SDLC pipeline.

Implements the workflow DAG from the architecture document:
  Requirements → BA → Architecture → CodeGen → Review/Security/QA → DevOps → SRE → Docs

Uses an async state machine. In production, back this with Temporal + LangGraph.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from backend.core.event_bus import get_event_bus
from backend.core.memory import get_episodic_memory, get_working_memory
from backend.models.schemas import (
    AgentOutput,
    AgentType,
    ApprovalGate,
    ApprovalStatus,
    ConfidenceBand,
    Event,
    SDLCStage,
    WorkflowCreate,
    WorkflowState,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

# Stage → next stage mapping (the DAG)
STAGE_TRANSITIONS: dict[SDLCStage, SDLCStage | None] = {
    SDLCStage.REQUIREMENTS: SDLCStage.BUSINESS_ANALYSIS,
    SDLCStage.BUSINESS_ANALYSIS: SDLCStage.ARCHITECTURE,
    SDLCStage.ARCHITECTURE: SDLCStage.TASK_BREAKDOWN,
    SDLCStage.TASK_BREAKDOWN: SDLCStage.CODE_GENERATION,
    SDLCStage.CODE_GENERATION: SDLCStage.CODE_REVIEW,
    SDLCStage.CODE_REVIEW: SDLCStage.TESTING,
    SDLCStage.TESTING: SDLCStage.SECURITY_SCAN,
    SDLCStage.SECURITY_SCAN: SDLCStage.CI_CD,
    SDLCStage.CI_CD: SDLCStage.DEPLOYMENT,
    SDLCStage.DEPLOYMENT: SDLCStage.MONITORING,
    SDLCStage.MONITORING: SDLCStage.DOCUMENTATION,
    SDLCStage.DOCUMENTATION: SDLCStage.FEEDBACK,
    SDLCStage.FEEDBACK: None,
}

# Which stages require a human approval gate
APPROVAL_GATES: dict[SDLCStage, str] = {
    SDLCStage.REQUIREMENTS: "Requirements Approval",
    SDLCStage.BUSINESS_ANALYSIS: "BRD Sign-off",
    SDLCStage.ARCHITECTURE: "Architecture Review Board",
    SDLCStage.DEPLOYMENT: "Production Deploy Approval",
}

# Stage → responsible agent(s)
STAGE_AGENTS: dict[SDLCStage, AgentType] = {
    SDLCStage.REQUIREMENTS: AgentType.REQUIREMENTS,
    SDLCStage.BUSINESS_ANALYSIS: AgentType.BUSINESS_ANALYST,
    SDLCStage.ARCHITECTURE: AgentType.ARCHITECT,
    SDLCStage.TASK_BREAKDOWN: AgentType.ORCHESTRATOR,
    SDLCStage.CODE_GENERATION: AgentType.CODE_GENERATOR,
    SDLCStage.CODE_REVIEW: AgentType.CODE_REVIEWER,
    SDLCStage.TESTING: AgentType.QA,
    SDLCStage.SECURITY_SCAN: AgentType.SECURITY,
    SDLCStage.CI_CD: AgentType.DEVOPS,
    SDLCStage.DEPLOYMENT: AgentType.DEVOPS,
    SDLCStage.MONITORING: AgentType.SRE,
    SDLCStage.DOCUMENTATION: AgentType.DOCUMENTATION,
    SDLCStage.FEEDBACK: AgentType.ORCHESTRATOR,
}


class WorkflowEngine:
    """Manages workflow lifecycle and stage transitions."""

    def __init__(self):
        self._workflows: dict[str, WorkflowState] = {}
        self._agents: dict[AgentType, Any] = {}

    def register_agent(self, agent_type: AgentType, agent_instance: Any):
        self._agents[agent_type] = agent_instance
        logger.info("Registered agent: %s", agent_type.value)

    async def create_workflow(self, request: WorkflowCreate) -> WorkflowState:
        workflow = WorkflowState(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            business_brief=request.business_brief,
            project_name=request.project_name,
        )
        self._workflows[workflow.id] = workflow

        wm = get_working_memory()
        wm.set(workflow.id, "business_brief", request.business_brief)
        wm.set(workflow.id, "title", request.title)
        wm.set(workflow.id, "project_name", request.project_name)

        em = get_episodic_memory()
        em.save_workflow(workflow.model_dump())

        bus = get_event_bus()
        await bus.publish(Event(
            topic="sdlc.workflow.started",
            source_agent=AgentType.ORCHESTRATOR,
            workflow_id=workflow.id,
            payload={"title": request.title, "project": request.project_name},
        ))

        return workflow

    async def run_workflow(self, workflow_id: str):
        """Execute the workflow through all stages sequentially."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.status = WorkflowStatus.RUNNING
        self._persist_workflow(workflow)

        current_stage = workflow.current_stage
        while current_stage is not None:
            logger.info("Workflow %s entering stage: %s", workflow_id, current_stage.value)
            workflow.current_stage = current_stage
            self._persist_workflow(workflow)

            agent_type = STAGE_AGENTS.get(current_stage)
            agent = self._agents.get(agent_type) if agent_type else None

            if agent:
                try:
                    output = await agent.execute(workflow)
                    workflow.agent_outputs.append(output)
                    self._merge_artifacts(workflow, output)
                    self._persist_workflow(workflow)

                    if current_stage in APPROVAL_GATES:
                        gate = ApprovalGate(
                            workflow_id=workflow_id,
                            stage=current_stage,
                            gate_name=APPROVAL_GATES[current_stage],
                            agent_type=agent_type,
                            artifacts_for_review=output.artifacts,
                            context={"reasoning": output.reasoning, "confidence": output.confidence},
                        )
                        workflow.approval_gates.append(gate)
                        workflow.status = WorkflowStatus.AWAITING_APPROVAL

                        bus = get_event_bus()
                        await bus.publish(Event(
                            topic="sdlc.approval.requested",
                            source_agent=agent_type,
                            workflow_id=workflow_id,
                            payload={
                                "gate_id": gate.id,
                                "gate_name": gate.gate_name,
                                "stage": current_stage.value,
                            },
                        ))
                        self._persist_workflow(workflow)

                        # Auto-approve for POC demo flow
                        await self.approve_gate(workflow_id, gate.id, "auto-poc", "Auto-approved for POC demo")
                        workflow.status = WorkflowStatus.RUNNING

                except Exception as e:
                    logger.exception("Agent %s failed at stage %s", agent_type, current_stage)
                    workflow.status = WorkflowStatus.FAILED
                    self._persist_workflow(workflow)

                    bus = get_event_bus()
                    await bus.publish(Event(
                        topic="sdlc.workflow.failed",
                        source_agent=AgentType.ORCHESTRATOR,
                        workflow_id=workflow_id,
                        payload={"stage": current_stage.value, "error": str(e)},
                    ))
                    return workflow

            current_stage = STAGE_TRANSITIONS.get(current_stage)

        workflow.status = WorkflowStatus.COMPLETED
        workflow.updated_at = datetime.utcnow()
        self._persist_workflow(workflow)

        bus = get_event_bus()
        await bus.publish(Event(
            topic="sdlc.workflow.completed",
            source_agent=AgentType.ORCHESTRATOR,
            workflow_id=workflow_id,
            payload={"title": workflow.title},
        ))

        return workflow

    async def approve_gate(
        self, workflow_id: str, gate_id: str, decided_by: str, notes: str = ""
    ) -> ApprovalGate | None:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None

        for gate in workflow.approval_gates:
            if gate.id == gate_id:
                gate.status = ApprovalStatus.APPROVED
                gate.decided_by = decided_by
                gate.reviewer_notes = notes
                gate.decided_at = datetime.utcnow()

                bus = get_event_bus()
                await bus.publish(Event(
                    topic="sdlc.approval.granted",
                    source_agent=AgentType.ORCHESTRATOR,
                    workflow_id=workflow_id,
                    payload={"gate_id": gate_id, "gate_name": gate.gate_name},
                ))
                return gate
        return None

    async def reject_gate(
        self, workflow_id: str, gate_id: str, decided_by: str, notes: str = ""
    ) -> ApprovalGate | None:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None

        for gate in workflow.approval_gates:
            if gate.id == gate_id:
                gate.status = ApprovalStatus.REJECTED
                gate.decided_by = decided_by
                gate.reviewer_notes = notes
                gate.decided_at = datetime.utcnow()
                workflow.status = WorkflowStatus.FAILED

                bus = get_event_bus()
                await bus.publish(Event(
                    topic="sdlc.approval.rejected",
                    source_agent=AgentType.ORCHESTRATOR,
                    workflow_id=workflow_id,
                    payload={"gate_id": gate_id, "reason": notes},
                ))
                return gate
        return None

    def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowState]:
        return list(self._workflows.values())

    def get_pending_approvals(self) -> list[ApprovalGate]:
        gates = []
        for wf in self._workflows.values():
            for gate in wf.approval_gates:
                if gate.status == ApprovalStatus.PENDING:
                    gates.append(gate)
        return gates

    def _merge_artifacts(self, workflow: WorkflowState, output: AgentOutput):
        stage_key = output.stage.value
        workflow.artifacts[stage_key] = output.artifacts

    def _persist_workflow(self, workflow: WorkflowState):
        em = get_episodic_memory()
        em.save_workflow({
            "id": workflow.id,
            "title": workflow.title,
            "description": workflow.description,
            "business_brief": workflow.business_brief,
            "project_name": workflow.project_name,
            "status": workflow.status.value,
            "current_stage": workflow.current_stage.value,
            "artifacts": workflow.artifacts,
        })


# Singleton
_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
