"""
Business Analyst Agent: shapes approved requirements into a BRD, user stories,
business rules, and non-functional requirements for downstream design.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class BusinessAnalystAgent(BaseAgent):
    """Converts structured requirements into BRD-style outputs and agile artifacts."""

    agent_type = AgentType.BUSINESS_ANALYST
    stage = SDLCStage.BUSINESS_ANALYSIS
    output_event_topic = "sdlc.brd.ready"
    system_prompt = (
        "You are the Business Analyst Agent. "
        "Using the requirements catalog and brief, produce one JSON object with: "
        "(1) brd—executive summary, scope in/out, stakeholders, glossary; "
        "(2) user_stories—each with id, role, goal, benefit, and acceptance_criteria (Given/When/Then or checklist); "
        "(3) business_rules—id, statement, triggers, and enforcement notes; "
        "(4) non_functional_requirements—categories such as performance, security, availability, "
        "compliance, usability, with measurable targets where possible. "
        "Align stories and rules to requirement IDs when available. "
        "Respond with valid JSON only."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        mem = context.get("workflow_memory") or {}
        req_key = f"{SDLCStage.REQUIREMENTS.value}_output"
        requirements_artifact = mem.get(req_key)
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow title: {workflow.title}\n\n"
            "Business brief:\n"
            f"{context['business_brief']}\n\n"
            "Prior artifacts (workflow.artifacts):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            "Structured requirements from working memory "
            f"({req_key})—use as primary input:\n"
            f"{json.dumps(requirements_artifact, indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage: produce BRD, user stories, "
            "business rules, and NFRs as JSON."
        )

    def _requires_approval(self) -> bool:
        return True

    def _approval_gate_name(self) -> str:
        return "BRD Sign-off"
