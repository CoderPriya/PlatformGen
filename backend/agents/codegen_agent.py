"""
Code Generation Agent: turns approved stories and architecture into implementable
artifacts—file layout, code, tests, and dependency declarations suitable for a PR.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class CodegenAgent(BaseAgent):
    """Generates production-oriented code and scaffolding from design artifacts."""

    agent_type = AgentType.CODE_GENERATOR
    stage = SDLCStage.CODE_GENERATION
    output_event_topic = "sdlc.code.pr_opened"
    system_prompt = (
        "You are the Code Generation Agent. "
        "Using user stories, ADRs, and API contracts, produce one JSON object with: "
        "(1) files—list of {path, language, content} for production code; "
        "(2) loc_summary—per-file and total line counts (approximate if embedded in content); "
        "(3) tests—test files or scaffolding (paths + content) aligned to acceptance criteria; "
        "(4) dependencies—declarations grouped by ecosystem "
        "(e.g. python: requirements-style list, node: package entries) plus brief rationale; "
        "(5) pr_description—summary of changes and how to run tests. "
        "Prioritize clarity, security basics, and consistency with the OpenAPI and schemas. "
        "Respond with valid JSON only."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        mem = context.get("workflow_memory") or {}
        stages_for_memory = (
            SDLCStage.REQUIREMENTS,
            SDLCStage.BUSINESS_ANALYSIS,
            SDLCStage.ARCHITECTURE,
            SDLCStage.TASK_BREAKDOWN,
        )
        prior_by_stage = {
            s.value: mem.get(f"{s.value}_output") for s in stages_for_memory
        }
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow title: {workflow.title}\n\n"
            "Business brief (context):\n"
            f"{context['business_brief']}\n\n"
            "Prior artifacts (workflow.artifacts):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            "Prior stage outputs from working memory (requirements, business_analysis, "
            "architecture, task_breakdown):\n"
            f"{json.dumps(prior_by_stage, indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage: generate file listings with content, "
            "LOC counts, test scaffolding, and dependency declarations as JSON."
        )
