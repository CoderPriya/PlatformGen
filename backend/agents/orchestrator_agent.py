"""
Program manager / orchestrator agent.

Meta-coordinator at the feedback stage: synthesizes the full workflow into
completion reporting, metrics, improvement backlog, and retrospective insights.
"""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.core.memory import get_working_memory
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class OrchestratorAgent(BaseAgent):
    """Coordinates narrative closure: sprint-style reporting and continuous improvement."""

    agent_type = AgentType.ORCHESTRATOR
    stage = SDLCStage.FEEDBACK
    output_event_topic = "sdlc.workflow.completed"
    system_prompt = (
        "You are a program manager and delivery orchestrator at the final feedback stage. "
        "Synthesize the entire workflow into:\n"
        "- A sprint (or phase) completion report: goals, outcomes, blockers, carry-over.\n"
        "- Velocity-style metrics where inferable from artifacts (throughput, rework, quality signals); "
        "state assumptions if data is missing.\n"
        "- A prioritized improvement backlog (process, tooling, skills, technical debt).\n"
        "- Retrospective insights: what went well, what to change, experiments to try.\n"
        "Respond with structured JSON only: sprint_completion_report, velocity_metrics, "
        "improvement_backlog, retro_insights, and reasoning or summary."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        wm = get_working_memory()
        stage_memory = wm.get_all(workflow.id)
        prior = json.dumps(context["prior_artifacts"], indent=2, default=str)
        mem = json.dumps(stage_memory, indent=2, default=str)
        outputs = [
            {
                "agent_type": o.agent_type.value,
                "stage": o.stage.value,
                "confidence": o.confidence,
                "reasoning": o.reasoning,
                "artifacts": o.artifacts,
            }
            for o in workflow.agent_outputs
        ]
        serialized_outputs = json.dumps(outputs, indent=2, default=str)
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow ID: {workflow.id}\n"
            f"Title: {workflow.title}\n"
            f"Description: {workflow.description}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            "=== Working memory (per-stage scratch keys and values) ===\n"
            f"{mem}\n\n"
            "=== Consolidated artifacts keyed by stage ===\n"
            f"{prior}\n\n"
            "=== Chronological agent outputs (full pipeline history) ===\n"
            f"{serialized_outputs}\n\n"
            "Summarize all prior stage outputs above for the feedback stage. "
            "Produce structured JSON per your system instructions."
        )
