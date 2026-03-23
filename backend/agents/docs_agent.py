"""
Documentation agent.

Turns accumulated SDLC artifacts into consumable docs: API references, runbooks,
changelogs, architecture overviews, and onboarding material.
"""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.core.memory import get_working_memory
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class DocumentationAgent(BaseAgent):
    """Generates and updates documentation from all prior workflow outputs."""

    agent_type = AgentType.DOCUMENTATION
    stage = SDLCStage.DOCUMENTATION
    output_event_topic = "sdlc.docs.updated"
    system_prompt = (
        "You are a technical documentation lead. From all prior SDLC artifacts and "
        "working memory, produce:\n"
        "- API reference documentation (endpoints, schemas, auth, examples).\n"
        "- Operational runbooks (deploy, rollback, incident response, common failures).\n"
        "- Changelog-style release notes aligned to delivered scope.\n"
        "- Architecture overview diagrams described in text (components, data flows, boundaries).\n"
        "- Onboarding guides for developers and operators.\n"
        "Respond with structured JSON only: api_reference, runbooks, changelog, "
        "architecture_overview, onboarding_guides, and a reasoning or summary field. "
        "Be accurate to the inputs; flag gaps explicitly."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        wm = get_working_memory()
        memory = wm.get_all(workflow.id)
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow ID: {workflow.id}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Full working memory (all keys):\n{json.dumps(memory, indent=2, default=str)}\n\n"
            f"Prior consolidated artifacts:\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage. Produce structured JSON as specified."
        )
