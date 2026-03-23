"""
Base agent class implementing the common agent contract from the architecture document.

Every agent:
- Has a defined type, role, and system prompt
- Receives structured input and produces structured output
- Carries a confidence score on every output
- Logs reasoning traces for auditability
- Publishes events to the event bus
- Reads/writes working memory for inter-agent context passing
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from backend.config import get_settings
from backend.core.event_bus import get_event_bus
from backend.core.llm import llm_json_completion
from backend.core.memory import get_episodic_memory, get_working_memory
from backend.models.schemas import (
    AgentOutput,
    AgentType,
    ConfidenceBand,
    Event,
    SDLCStage,
    WorkflowState,
)

logger = logging.getLogger(__name__)


class BaseAgent:
    """Abstract base for all SDLC agents."""

    agent_type: AgentType
    stage: SDLCStage
    system_prompt: str = ""
    output_event_topic: str = ""

    def __init__(self):
        self._tasks_completed = 0
        self._last_active: datetime | None = None

    @property
    def tasks_completed(self) -> int:
        return self._tasks_completed

    @property
    def last_active(self) -> datetime | None:
        return self._last_active

    async def execute(self, workflow: WorkflowState) -> AgentOutput:
        """Run the agent for a given workflow stage."""
        logger.info(
            "[%s] Executing for workflow=%s stage=%s",
            self.agent_type.value,
            workflow.id,
            self.stage.value,
        )
        self._last_active = datetime.utcnow()

        context = self._build_context(workflow)
        user_prompt = self._build_prompt(workflow, context)

        result = await llm_json_completion(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
        )

        confidence = self._assess_confidence(result)
        band = self._confidence_band(confidence)

        output = AgentOutput(
            agent_type=self.agent_type,
            workflow_id=workflow.id,
            stage=self.stage,
            artifacts=result,
            confidence=confidence,
            confidence_band=band,
            reasoning=self._extract_reasoning(result),
            requires_approval=self._requires_approval(),
            approval_gate_name=self._approval_gate_name(),
            next_stage=self._next_stage(),
        )

        wm = get_working_memory()
        wm.set(workflow.id, f"{self.stage.value}_output", result)
        wm.set(workflow.id, f"{self.stage.value}_confidence", confidence)

        em = get_episodic_memory()
        em.save_agent_output(output.model_dump())

        if self.output_event_topic:
            bus = get_event_bus()
            await bus.publish(Event(
                topic=self.output_event_topic,
                source_agent=self.agent_type,
                workflow_id=workflow.id,
                payload={"stage": self.stage.value, "confidence": confidence},
            ))

        self._tasks_completed += 1
        logger.info(
            "[%s] Completed: confidence=%.2f band=%s",
            self.agent_type.value,
            confidence,
            band.value,
        )
        return output

    def _build_context(self, workflow: WorkflowState) -> dict[str, Any]:
        """Gather context from working memory and prior artifacts."""
        wm = get_working_memory()
        return {
            "business_brief": wm.get(workflow.id, "business_brief", workflow.business_brief),
            "project_name": wm.get(workflow.id, "project_name", workflow.project_name),
            "prior_artifacts": workflow.artifacts,
            "workflow_memory": wm.get_all(workflow.id),
        }

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        """Build the user prompt. Override in subclasses for specialization."""
        return (
            f"Project: {context['project_name']}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Prior Artifacts:\n{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Execute your role for the {self.stage.value} stage. "
            f"Produce structured output as JSON."
        )

    def _assess_confidence(self, result: dict[str, Any]) -> float:
        """Heuristic confidence scoring. Override for domain-specific logic."""
        if "error" in result or "raw_response" in result:
            return 0.3
        keys = len(result)
        if keys >= 3:
            return 0.85
        if keys >= 2:
            return 0.70
        return 0.50

    def _confidence_band(self, score: float) -> ConfidenceBand:
        settings = get_settings()
        if score >= settings.high_confidence_threshold:
            return ConfidenceBand.HIGH
        if score >= settings.medium_confidence_threshold:
            return ConfidenceBand.MEDIUM
        if score >= settings.low_confidence_threshold:
            return ConfidenceBand.LOW
        return ConfidenceBand.VERY_LOW

    def _extract_reasoning(self, result: dict[str, Any]) -> str:
        if "reasoning" in result:
            return str(result["reasoning"])
        if "summary" in result:
            return str(result["summary"])
        return f"Agent {self.agent_type.value} produced {len(result)} artifact keys."

    def _requires_approval(self) -> bool:
        return False

    def _approval_gate_name(self) -> str:
        return ""

    def _next_stage(self) -> SDLCStage | None:
        from backend.core.workflow import STAGE_TRANSITIONS
        return STAGE_TRANSITIONS.get(self.stage)
