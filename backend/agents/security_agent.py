"""
Security and compliance agent: vulnerability and policy assessment with merge guidance.
"""

from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentType, SDLCStage, WorkflowState


def _has_critical_finding(result: dict[str, Any]) -> bool:
    """Detect critical-severity items in common LLM output shapes."""
    if result.get("has_critical_findings") is True:
        return True
    if int(result.get("critical_count", 0) or 0) > 0:
        return True
    for key in ("sast_findings", "dast_findings", "findings", "vulnerabilities", "cve_findings"):
        items = result.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            sev = str(item.get("severity", item.get("level", ""))).lower()
            if sev in ("critical", "crit", "p0"):
                return True
    return False


class SecurityAgent(BaseAgent):
    """Scans for security issues and compliance gaps; recommends block or allow."""

    agent_type = AgentType.SECURITY
    stage = SDLCStage.SECURITY_SCAN
    output_event_topic = "sdlc.security.completed"
    system_prompt = (
        "You are a security and compliance agent. Analyze the supplied codebase/build context for: "
        "vulnerabilities (injection, authn/z, data exposure, etc.), policy violations, hardcoded secrets, "
        "and known CVEs where inferable. Output strict JSON with: "
        "`sast_findings` and `dast_findings` (lists of objects: id, title, severity, location, remediation), "
        "`secrets_scan` (findings list), `compliance_gaps` (framework/control references and gaps), "
        "`cve_summary` (relevant packages/issues), "
        "`merge_decision` (string: block or allow), "
        "`rationale`, and `summary`. "
        "Use severity labels including critical where appropriate. "
        "Prefer block when critical or exploitable issues are present."
    )

    def _build_prompt(self, workflow: WorkflowState, context: dict[str, Any]) -> str:
        artifacts = json.dumps(workflow.artifacts, indent=2, default=str)
        return (
            f"Project: {context['project_name']}\n\n"
            f"Business Brief:\n{context['business_brief']}\n\n"
            f"Security scan stage — workflow.artifacts (code, dependencies, configs, prior review):\n{artifacts}\n\n"
            f"Prior aggregated artifacts (reference):\n"
            f"{json.dumps(context['prior_artifacts'], indent=2, default=str)}\n\n"
            f"Workflow memory snapshot:\n"
            f"{json.dumps(context['workflow_memory'], indent=2, default=str)}\n\n"
            f"Execute security and compliance analysis for the {self.stage.value} stage. "
            f"Produce structured output as JSON."
        )

    def _assess_confidence(self, result: dict[str, Any]) -> float:
        base = super()._assess_confidence(result)
        if _has_critical_finding(result):
            return min(base, 0.40)
        return base
