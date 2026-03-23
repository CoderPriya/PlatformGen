"""
Architect Agent: defines technical direction via ADRs, API contracts, data schemas,
component views, and technology stack choices for implementation.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class ArchitectAgent(BaseAgent):
    """Produces architecture artifacts consumable by codegen and review gates."""

    agent_type = AgentType.ARCHITECT
    stage = SDLCStage.ARCHITECTURE
    output_event_topic = "sdlc.architecture.ready"
    system_prompt = (
        "You are the Software Architect Agent. "
        "From requirements and BA outputs, emit one JSON object containing: "
        "(1) adrs—list of architecture decision records (title, status, context, decision, consequences); "
        "(2) openapi—OpenAPI 3.x document as a JSON object (info, paths, components/schemas as needed); "
        "(3) data_schemas—logical/physical models, key entities, relationships, and migration notes; "
        "(4) system_components—nodes, responsibilities, and interfaces (textual diagram or Mermaid in a string field); "
        "(5) technology_stack—languages, frameworks, data stores, messaging, hosting, with rationale. "
        "Keep contracts consistent with stories and business rules. "
        "Respond with valid JSON only."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        mem = context.get("workflow_memory") or {}
        req_out = mem.get(f"{SDLCStage.REQUIREMENTS.value}_output")
        ba_out = mem.get(f"{SDLCStage.BUSINESS_ANALYSIS.value}_output")
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow title: {workflow.title}\n\n"
            "Business brief (context):\n"
            f"{context['business_brief']}\n\n"
            "Prior artifacts (workflow.artifacts):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            "Requirements stage output (working memory):\n"
            f"{json.dumps(req_out, indent=2, default=str)}\n\n"
            "Business analysis / BRD output (working memory):\n"
            f"{json.dumps(ba_out, indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage: produce ADRs, OpenAPI, data schemas, "
            "component diagram description, and technology stack as JSON."
        )

    def _requires_approval(self) -> bool:
        return True

    def _approval_gate_name(self) -> str:
        return "Architecture Review Board"
