"""
Code Reviewer agent: evaluates pull requests against standards, ADRs, and security policy.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class ReviewerAgent(BaseAgent):
    """Produces structured PR review output with decision and quality score."""

    agent_type = AgentType.CODE_REVIEWER
    stage = SDLCStage.CODE_REVIEW
    output_event_topic = "sdlc.review.completed"
    system_prompt = (
        "You are a senior code reviewer for an SDLC workflow. Review the supplied change "
        "(diff, files, or description) against: team coding standards, applicable "
        "Architecture Decision Records (ADRs), and organizational security policy. "
        "Respond with strict JSON containing: "
        "`review_comments` (list of structured items: path, line_or_range, severity, category, message), "
        "`decision` (string: approve or reject), "
        "`quality_score` (number 0–100), "
        "`standards_violations`, `adr_conflicts`, `security_concerns` (lists of short strings), "
        "and `summary` (concise rationale). "
        "Be specific and actionable; reject when blocking issues exist."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        artifacts = json.dumps(workflow.artifacts, indent=2, default=str)
        return (
            f"Project: {context['project_name']}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Code review stage — workflow.artifacts (PR/diff/context for this stage):\n{artifacts}\n\n"
            f"Prior aggregated artifacts (reference):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Workflow memory snapshot:\n"
            f"{json.dumps(context['workflow_memory'], indent=2, default=str)}\n\n"
            f"Execute code review for the {self.stage.value} stage. "
            f"Produce structured output as JSON."
        )
