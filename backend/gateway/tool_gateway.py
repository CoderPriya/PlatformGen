"""
Tool API Gateway — the trust boundary for all agent-to-tool interactions.

In the architecture document, this is the custom-built FastAPI gateway that:
- Enforces tool manifests per agent (declared permitted actions)
- Rate-limits agent tool calls
- Logs every tool invocation for audit
- Routes to external systems (Jira, GitHub, Confluence, etc.)

For the POC, we simulate external tool calls and demonstrate the governance model.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.schemas import AgentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gateway", tags=["tool-gateway"])


# ---------------------------------------------------------------------------
# Tool Manifest — declares which tools each agent may invoke
# ---------------------------------------------------------------------------

TOOL_MANIFESTS: dict[AgentType, set[str]] = {
    AgentType.ORCHESTRATOR: {"jira.create_epic", "jira.update_status", "confluence.create_page", "slack.send_message"},
    AgentType.REQUIREMENTS: {"jira.create_epic", "confluence.read_page", "slack.read_channel", "email.parse"},
    AgentType.BUSINESS_ANALYST: {"confluence.create_page", "confluence.read_page", "jira.create_story"},
    AgentType.ARCHITECT: {"confluence.create_page", "github.read_repo", "openapi.validate"},
    AgentType.CODE_GENERATOR: {"github.create_pr", "github.push_branch", "github.read_repo"},
    AgentType.CODE_REVIEWER: {"github.post_review", "github.read_pr"},
    AgentType.QA: {"github.read_pr", "ci.trigger_tests", "ci.read_results"},
    AgentType.SECURITY: {"sonarqube.scan", "snyk.scan", "github.read_pr", "jira.create_bug"},
    AgentType.DEVOPS: {"ci.trigger_pipeline", "k8s.apply", "terraform.plan", "terraform.apply", "github.read_repo"},
    AgentType.SRE: {"datadog.query", "pagerduty.create_incident", "k8s.scale", "k8s.restart"},
    AgentType.DOCUMENTATION: {"confluence.create_page", "confluence.update_page", "github.update_wiki"},
}


# ---------------------------------------------------------------------------
# Audit log (in-memory for POC)
# ---------------------------------------------------------------------------

_audit_log: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ToolInvocation(BaseModel):
    agent_type: AgentType
    tool_name: str
    parameters: dict[str, Any] = {}


class ToolResult(BaseModel):
    invocation_id: str
    tool_name: str
    status: str
    result: dict[str, Any]
    audit_logged: bool = True


# ---------------------------------------------------------------------------
# Simulated tool backends
# ---------------------------------------------------------------------------

def _simulate_tool(tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Return a plausible mock result for any supported tool."""
    return {
        "tool": tool_name,
        "status": "success",
        "message": f"Simulated execution of {tool_name}",
        "parameters_received": parameters,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/invoke", response_model=ToolResult)
async def invoke_tool(invocation: ToolInvocation):
    """Execute a tool call on behalf of an agent, enforcing the tool manifest."""

    permitted = TOOL_MANIFESTS.get(invocation.agent_type, set())
    if invocation.tool_name not in permitted:
        logger.warning(
            "BLOCKED: agent=%s attempted tool=%s (not in manifest)",
            invocation.agent_type.value,
            invocation.tool_name,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Agent '{invocation.agent_type.value}' is not permitted to call tool '{invocation.tool_name}'",
        )

    invocation_id = str(uuid.uuid4())
    result = _simulate_tool(invocation.tool_name, invocation.parameters)

    audit_entry = {
        "invocation_id": invocation_id,
        "agent": invocation.agent_type.value,
        "tool": invocation.tool_name,
        "parameters": invocation.parameters,
        "result_status": result["status"],
        "timestamp": datetime.utcnow().isoformat(),
    }
    _audit_log.append(audit_entry)
    logger.info("Tool invocation: %s -> %s [%s]", invocation.agent_type.value, invocation.tool_name, invocation_id)

    return ToolResult(
        invocation_id=invocation_id,
        tool_name=invocation.tool_name,
        status=result["status"],
        result=result,
    )


@router.get("/audit", response_model=list[dict[str, Any]])
async def get_audit_log(limit: int = 100):
    """Return recent tool invocation audit entries."""
    return _audit_log[-limit:]


@router.get("/manifests")
async def get_manifests():
    """Return the tool manifest for all agents."""
    return {agent.value: sorted(tools) for agent, tools in TOOL_MANIFESTS.items()}
