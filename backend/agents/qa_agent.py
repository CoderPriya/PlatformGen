"""
QA / testing agent: plans and reports tests, coverage, gaps, and regression risk.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class QAAgent(BaseAgent):
    """Generates test strategy output and assesses quality gates."""

    agent_type = AgentType.QA
    stage = SDLCStage.TESTING
    output_event_topic = "sdlc.qa.completed"
    system_prompt = (
        "You are a QA engineer agent in an automated SDLC pipeline. Given the implementation "
        "and requirements context, you design and reason about test coverage. Output strict JSON with: "
        "`unit_tests` (planned or described suites: name, targets, cases), "
        "`integration_tests`, `e2e_tests` (same structure), "
        "`execution_summary` (what would run, pass/fail assumptions if not executed), "
        "`coverage_report` (estimated or reported percentages by area, uncovered lines/modules), "
        "`gaps` (list of missing tests or weak areas), "
        "`regression_risk` (string: low|medium|high plus brief justification), "
        "`recommendations` (list of strings), and `summary`. "
        "Align tests with acceptance criteria and critical paths."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        artifacts = json.dumps(workflow.artifacts, indent=2, default=str)
        return (
            f"Project: {context['project_name']}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Testing stage — workflow.artifacts (features, builds, review output, etc.):\n{artifacts}\n\n"
            f"Prior aggregated artifacts (reference):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Workflow memory snapshot:\n"
            f"{json.dumps(context['workflow_memory'], indent=2, default=str)}\n\n"
            f"Execute QA and testing responsibilities for the {self.stage.value} stage. "
            f"Produce structured output as JSON."
        )
