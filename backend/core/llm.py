"""
LLM integration layer via LiteLLM for provider abstraction.

Supports OpenAI, Anthropic, Azure, and any LiteLLM-compatible provider.
Falls back to a mock mode when no API key is configured.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.config import get_settings

logger = logging.getLogger(__name__)

_MOCK_MODE = False


def _check_mock_mode() -> bool:
    settings = get_settings()
    has_key = bool(settings.openai_api_key or settings.anthropic_api_key)
    return not has_key


async def llm_completion(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    response_format: str = "text",
) -> str:
    """Call the LLM. Falls back to mock responses if no API key is set."""
    settings = get_settings()
    model = model or settings.llm_model

    if _check_mock_mode():
        return _mock_response(system_prompt, user_prompt)

    try:
        import litellm

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning("LLM call failed (%s), using mock response", e)
        return _mock_response(system_prompt, user_prompt)


async def llm_json_completion(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Call LLM and parse the response as JSON."""
    full_system = system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation."
    raw = await llm_completion(full_system, user_prompt, model=model, temperature=temperature)

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response, wrapping in object")
        return {"raw_response": raw}


def _mock_response(system_prompt: str, user_prompt: str) -> str:
    """Generate a plausible mock response for demo/testing without an API key."""
    prompt_lower = (system_prompt + user_prompt).lower()

    if "requirement" in prompt_lower:
        return json.dumps({
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "User Authentication",
                    "description": "System shall support secure user authentication via OAuth 2.0",
                    "priority": "high",
                    "type": "functional",
                    "acceptance_criteria": ["Users can login with email/password", "OAuth 2.0 flow supported", "Session timeout after 30 min inactivity"],
                },
                {
                    "id": "REQ-002",
                    "title": "Data Validation",
                    "description": "All user inputs shall be validated against defined schemas",
                    "priority": "high",
                    "type": "functional",
                    "acceptance_criteria": ["Input validation on all forms", "Server-side validation on all API endpoints"],
                },
                {
                    "id": "REQ-003",
                    "title": "API Rate Limiting",
                    "description": "API endpoints shall enforce rate limiting per user/IP",
                    "priority": "medium",
                    "type": "non_functional",
                    "acceptance_criteria": ["Rate limit of 100 req/min per user", "429 response on limit breach"],
                },
            ],
            "ambiguities": ["Specific OAuth providers not specified", "Rate limit thresholds need confirmation"],
            "open_questions": ["Which identity provider should be integrated?", "What is the expected peak concurrent users?"],
        }, indent=2)

    if "business" in prompt_lower and ("analysis" in prompt_lower or "brd" in prompt_lower):
        return json.dumps({
            "brd_summary": "Business Requirements Document for the requested feature set.",
            "user_stories": [
                {"id": "US-001", "title": "As a user, I want to register an account", "acceptance_criteria": ["Form validates email format", "Password meets strength requirements", "Confirmation email sent"], "story_points": 5},
                {"id": "US-002", "title": "As a user, I want to login securely", "acceptance_criteria": ["OAuth 2.0 login flow", "MFA support", "Session management"], "story_points": 8},
                {"id": "US-003", "title": "As an admin, I want to manage users", "acceptance_criteria": ["CRUD operations on user accounts", "Role-based access control", "Audit logging"], "story_points": 8},
            ],
            "business_rules": ["All PII must be encrypted at rest", "User sessions expire after 30 minutes of inactivity", "Failed login attempts locked after 5 tries"],
            "non_functional_requirements": ["99.9% uptime SLA", "P99 latency < 200ms", "Support 10K concurrent users"],
        }, indent=2)

    if "architect" in prompt_lower or "adr" in prompt_lower:
        return json.dumps({
            "architecture_decisions": [
                {"id": "ADR-001", "title": "Use microservices architecture", "status": "proposed", "context": "System requires independent scaling and deployment of components", "decision": "Adopt microservices with REST APIs and event-driven communication", "consequences": ["Increased operational complexity", "Better scalability and fault isolation"]},
                {"id": "ADR-002", "title": "PostgreSQL as primary database", "status": "proposed", "context": "Need ACID compliance with JSON support", "decision": "Use PostgreSQL 16 with pgvector extension", "consequences": ["Mature ecosystem", "Supports vector search for future RAG needs"]},
            ],
            "api_contracts": [
                {"endpoint": "POST /api/v1/users", "description": "Create new user", "request_schema": {"email": "string", "password": "string", "name": "string"}, "response_schema": {"id": "uuid", "email": "string", "created_at": "datetime"}},
                {"endpoint": "POST /api/v1/auth/login", "description": "Authenticate user", "request_schema": {"email": "string", "password": "string"}, "response_schema": {"access_token": "string", "expires_in": "integer"}},
            ],
            "system_components": ["API Gateway", "Auth Service", "User Service", "Notification Service", "Message Queue"],
            "technology_stack": {"language": "Python 3.12", "framework": "FastAPI", "database": "PostgreSQL 16", "cache": "Redis", "queue": "RabbitMQ", "container": "Docker + Kubernetes"},
        }, indent=2)

    if "code" in prompt_lower and ("generat" in prompt_lower or "implement" in prompt_lower):
        return json.dumps({
            "files_generated": [
                {"path": "src/api/routes/users.py", "description": "User CRUD API endpoints", "loc": 145},
                {"path": "src/api/routes/auth.py", "description": "Authentication endpoints", "loc": 98},
                {"path": "src/models/user.py", "description": "User SQLAlchemy model", "loc": 42},
                {"path": "src/services/user_service.py", "description": "User business logic", "loc": 87},
                {"path": "tests/test_users.py", "description": "Unit tests for user endpoints", "loc": 120},
            ],
            "total_loc": 492,
            "test_count": 12,
            "dependencies_added": ["passlib", "python-jose", "python-multipart"],
            "summary": "Generated user authentication and management module with REST API, service layer, and unit tests.",
        }, indent=2)

    if "review" in prompt_lower:
        return json.dumps({
            "review_decision": "approve_with_comments",
            "quality_score": 0.82,
            "comments": [
                {"file": "src/api/routes/users.py", "line": 45, "severity": "medium", "comment": "Missing input validation on email field. Add email format check."},
                {"file": "src/services/user_service.py", "line": 23, "severity": "low", "comment": "Consider extracting password hashing to a utility module for reuse."},
                {"file": "src/api/routes/auth.py", "line": 67, "severity": "high", "comment": "JWT secret should not be hardcoded. Use environment variable."},
            ],
            "summary": "Code is well-structured overall. Three issues found: one high-severity (hardcoded secret), one medium (missing validation), one low (refactoring suggestion).",
        }, indent=2)

    if "security" in prompt_lower or "vulnerab" in prompt_lower:
        return json.dumps({
            "scan_summary": {"total_findings": 3, "critical": 0, "high": 1, "medium": 1, "low": 1},
            "findings": [
                {"id": "SEC-001", "severity": "high", "type": "hardcoded_secret", "location": "src/api/routes/auth.py:67", "description": "JWT secret key hardcoded in source code", "remediation": "Move to environment variable or Vault"},
                {"id": "SEC-002", "severity": "medium", "type": "missing_rate_limit", "location": "src/api/routes/auth.py:15", "description": "Login endpoint missing rate limiting", "remediation": "Add rate limiter middleware (e.g. slowapi)"},
                {"id": "SEC-003", "severity": "low", "type": "verbose_error", "location": "src/api/routes/users.py:89", "description": "Stack trace exposed in error response", "remediation": "Use generic error messages in production"},
            ],
            "compliance_status": {"OWASP_Top10": "2 findings mapped", "GDPR": "PII handling review needed"},
            "merge_decision": "block",
            "block_reason": "High severity finding SEC-001 must be resolved before merge.",
        }, indent=2)

    if "test" in prompt_lower or "qa" in prompt_lower:
        return json.dumps({
            "test_suites": [
                {"type": "unit", "tests_generated": 15, "coverage": 84.2},
                {"type": "integration", "tests_generated": 6, "coverage": 72.1},
            ],
            "total_tests": 21,
            "overall_coverage": 79.5,
            "coverage_threshold": 80.0,
            "coverage_met": False,
            "gaps": ["Missing tests for error handling in auth flow", "Edge case: concurrent registration with same email"],
            "regression_risk": "low",
            "summary": "Generated 21 tests. Coverage at 79.5% — slightly below 80% threshold. Two coverage gaps identified.",
        }, indent=2)

    if "deploy" in prompt_lower or "devops" in prompt_lower or "ci/cd" in prompt_lower:
        return json.dumps({
            "pipeline_status": "success",
            "stages": [
                {"name": "build", "status": "passed", "duration_seconds": 45},
                {"name": "unit_tests", "status": "passed", "duration_seconds": 120},
                {"name": "integration_tests", "status": "passed", "duration_seconds": 180},
                {"name": "security_scan", "status": "passed", "duration_seconds": 60},
                {"name": "container_build", "status": "passed", "duration_seconds": 90},
            ],
            "artifacts": {"docker_image": "registry.example.com/service:v1.2.3", "helm_chart": "charts/service-1.2.3.tgz"},
            "deployment_target": "staging",
            "deployment_strategy": "rolling",
            "smoke_tests": "passed",
        }, indent=2)

    if "monitor" in prompt_lower or "sre" in prompt_lower or "slo" in prompt_lower:
        return json.dumps({
            "deployment_health": "healthy",
            "slo_status": [
                {"sli": "availability", "target": 99.9, "current": 99.95, "status": "met"},
                {"sli": "latency_p99", "target_ms": 500, "current_ms": 180, "status": "met"},
                {"sli": "error_rate", "target_pct": 0.1, "current_pct": 0.02, "status": "met"},
            ],
            "alert_rules_created": 4,
            "dashboards_created": 1,
            "monitoring_summary": "All SLOs met. Service healthy post-deployment. 4 alert rules and 1 dashboard configured.",
        }, indent=2)

    if "document" in prompt_lower or "docs" in prompt_lower:
        return json.dumps({
            "documents_generated": [
                {"type": "api_reference", "title": "API Documentation v1.0", "sections": 5},
                {"type": "runbook", "title": "Service Operational Runbook", "sections": 8},
                {"type": "changelog", "title": "Release Changelog v1.2.3", "entries": 12},
                {"type": "architecture_overview", "title": "Architecture Overview", "sections": 4},
            ],
            "total_pages": 24,
            "summary": "Generated 4 documentation artifacts covering API reference, operations runbook, changelog, and architecture overview.",
        }, indent=2)

    return json.dumps({
        "status": "completed",
        "summary": "Agent task processed successfully.",
        "details": "This is a mock response. Configure an LLM API key for real agent intelligence.",
    }, indent=2)
