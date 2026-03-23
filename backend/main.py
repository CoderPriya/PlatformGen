"""
Autonomous Multi-Agent SDLC Platform — FastAPI application entry point.

Registers all agents, API routers, and serves the dashboard frontend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.agents import router as agents_router
from backend.api.approvals import router as approvals_router
from backend.api.workflows import router as workflows_router
from backend.gateway.tool_gateway import router as gateway_router
from backend.models.database import init_db
from backend.models.schemas import AgentType
from backend.core.workflow import get_workflow_engine

from backend.agents.requirements_agent import RequirementsAgent
from backend.agents.ba_agent import BusinessAnalystAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.codegen_agent import CodegenAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.security_agent import SecurityAgent
from backend.agents.devops_agent import DevOpsAgent
from backend.agents.sre_agent import SREAgent
from backend.agents.docs_agent import DocumentationAgent
from backend.agents.orchestrator_agent import OrchestratorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _register_agents():
    """Create and register all 11 SDLC agents with the workflow engine."""
    engine = get_workflow_engine()

    agents = [
        (AgentType.REQUIREMENTS, RequirementsAgent()),
        (AgentType.BUSINESS_ANALYST, BusinessAnalystAgent()),
        (AgentType.ARCHITECT, ArchitectAgent()),
        (AgentType.CODE_GENERATOR, CodegenAgent()),
        (AgentType.CODE_REVIEWER, ReviewerAgent()),
        (AgentType.QA, QAAgent()),
        (AgentType.SECURITY, SecurityAgent()),
        (AgentType.DEVOPS, DevOpsAgent()),
        (AgentType.SRE, SREAgent()),
        (AgentType.DOCUMENTATION, DocumentationAgent()),
        (AgentType.ORCHESTRATOR, OrchestratorAgent()),
    ]

    for agent_type, instance in agents:
        engine.register_agent(agent_type, instance)

    logger.info("All %d agents registered", len(agents))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Registering agents...")
    _register_agents()
    logger.info("Platform ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Autonomous Multi-Agent SDLC Platform",
    description="POC: Orchestrated AI agents for end-to-end enterprise software delivery lifecycle",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows_router)
app.include_router(approvals_router)
app.include_router(agents_router)
app.include_router(gateway_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "name": "Autonomous Multi-Agent SDLC Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "dashboard": "/static/index.html",
    }


@app.get("/health")
async def health():
    engine = get_workflow_engine()
    return {
        "status": "healthy",
        "agents_registered": len(engine._agents),
        "workflows_active": len(engine.list_workflows()),
    }


if __name__ == "__main__":
    import uvicorn
    from backend.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
