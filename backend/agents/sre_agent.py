"""
SRE / production operations agent.

Validates deployments, defines SLOs and alerting, and defines operational
visibility (health dashboards) so releases are observable and supportable.
"""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.core.memory import get_working_memory
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class SREAgent(BaseAgent):
    """Production operations: deployment validation, SLOs, alerts, dashboards."""

    agent_type = AgentType.SRE
    stage = SDLCStage.MONITORING
    output_event_topic = "sdlc.deployment.validated"
    system_prompt = (
        "You are an SRE and production operations specialist. Your job is to:\n"
        "- Validate that deployments meet production readiness (rollout strategy, "
        "rollback, health checks, canaries where appropriate).\n"
        "- Configure SLOs and error budgets tied to user-facing reliability.\n"
        "- Define concrete alert rules (symptoms over causes), routing, and severity.\n"
        "- Specify health dashboards and golden signals (latency, traffic, errors, saturation).\n"
        "Use prior workflow artifacts and context. Respond with structured JSON only: "
        "clear sections for deployment_validation, slo_monitoring, alert_rules, "
        "health_dashboards, and risks_or_followups. Include a short reasoning or summary field."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        wm = get_working_memory()
        memory = wm.get_all(workflow.id)
        return (
            f"Project: {context['project_name']}\n"
            f"Workflow ID: {workflow.id}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Working memory snapshot:\n{json.dumps(memory, indent=2, default=str)}\n\n"
            f"Prior artifacts:\n{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Execute the {self.stage.value} stage per your system role. "
            "Produce structured JSON as specified."
        )
