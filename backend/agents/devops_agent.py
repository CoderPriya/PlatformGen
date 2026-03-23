"""
DevOps / release agent: CI/CD, builds, deployments, and smoke-test outcomes.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


class DevOpsAgent(BaseAgent):
    """Reports pipeline and deployment status; requires production deploy approval."""

    agent_type = AgentType.DEVOPS
    stage = SDLCStage.CI_CD
    output_event_topic = "sdlc.build.completed"
    system_prompt = (
        "You are a DevOps agent responsible for CI/CD and releases. Given workflow context, "
        "describe or infer pipeline actions: build, container image, environment promotion, and smoke tests. "
        "Output strict JSON with: "
        "`pipeline_status` (string: success|failed|partial), "
        "`pipeline_steps` (list of step name, status, duration_or_notes), "
        "`artifacts` (images, packages, build IDs, URLs), "
        "`deployment_target` (environment name, region/cluster if applicable), "
        "`smoke_tests` (results summary), "
        "`blockers` (list), and `summary`. "
        "Be consistent with supplied artifacts; flag failures clearly."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        artifacts = json.dumps(workflow.artifacts, indent=2, default=str)
        return (
            f"Project: {context['project_name']}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"CI/CD stage — workflow.artifacts (pipeline defs, build logs pointers, release params):\n{artifacts}\n\n"
            f"Prior aggregated artifacts (reference):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Workflow memory snapshot:\n"
            f"{json.dumps(context['workflow_memory'], indent=2, default=str)}\n\n"
            f"Execute DevOps and release responsibilities for the {self.stage.value} stage. "
            f"Produce structured output as JSON."
        )

    def _requires_approval(self) -> bool:
        return True

    def _approval_gate_name(self) -> str:
        return "Production Deploy Approval"
