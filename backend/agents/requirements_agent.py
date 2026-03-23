"""
Requirements Agent: turns business inputs into a structured requirements catalog
with priorities, acceptance criteria, ambiguity analysis, and open questions.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class RequirementsAgent(BaseAgent):
    """Parses business briefs and produces structured, review-ready requirements."""

    agent_type = AgentType.REQUIREMENTS
    stage = SDLCStage.REQUIREMENTS
    output_event_topic = "sdlc.requirements.ready"
    system_prompt = (
        "You are the Requirements Agent in a multi-agent SDLC pipeline. "
        "Parse the business brief and any prior notes into a single JSON object. "
        "Include: (1) a requirements catalog—each item with id, title, description, "
        "priority (e.g. must/should/could), and dependencies if any; "
        "(2) acceptance criteria per requirement or grouped by theme; "
        "(3) an ambiguity_report listing vague terms, missing scope, conflicting statements, "
        "and assumptions you had to make; "
        "(4) open_questions for stakeholders. "
        "Be precise and structured; prefer explicit IDs and traceability to the brief. "
        "Respond with valid JSON only."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        mem = context.get("workflow_memory") or {}
        prior_snippets = {
            k: v
            for k, v in mem.items()
            if k.endswith("_output") and k != f"{self.stage.value}_output"
        }
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow title: {workflow.title}\n"
            f"Workflow description: {workflow.description}\n\n"
            "Business brief:\n"
            f"{context['business_brief']}\n\n"
            "Prior artifacts (workflow.artifacts):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            "Additional working-memory artifact outputs (if any):\n"
            f"{json.dumps(prior_snippets, indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage: produce the requirements catalog JSON "
            "as described in your system instructions."
        )

    def _requires_approval(self) -> bool:
        return True

    def _approval_gate_name(self) -> str:
        return "Requirements Approval"
