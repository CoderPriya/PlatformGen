# PlatformGen : Autonomous Multi-Agent SDLC Platform
PlatformGen is an enterprised multi-agent AI platform designed to accelerate the complete software development lifecycle through intelligent automation, agentic workflows, and enterprise-grade governance. It helps transform business ideas into production-ready software by assisting with requirements analysis, architecture design, task planning, code generation, testing, security validation, deployment workflows, and operational feedback loops. PlatformGen is built to combine developer productivity, platform engineering discipline, and autonomous AI capabilities in a controlled, auditable, and scalable way.


A proof-of-concept implementation of an **Autonomous Multi-Agent System for End-to-End Enterprise SDLC**, based on the architecture design document.

## What This Is

An orchestrated network of 11 purpose-built AI agents, each owning a specific domain of the software delivery lifecycle — from business requirements to production monitoring. The platform demonstrates:

- **Full SDLC pipeline**: Requirements → Business Analysis → Architecture → Code Generation → Code Review → QA Testing → Security Scan → CI/CD → Deployment → Monitoring → Documentation → Feedback
- **Human-in-the-loop approval gates** at critical decision boundaries (Requirements, BRD, Architecture Review Board, Production Deploy)
- **Event-driven architecture** with an in-memory event bus (simulating Apache Kafka)
- **Three-tier memory**: Working memory (per-workflow), Episodic memory (persistent), Long-term memory (cross-project knowledge)
- **Tool API Gateway** enforcing per-agent tool manifests with full audit logging
- **Confidence scoring** on every agent output (High/Medium/Low/Very Low bands)
- **Web dashboard** for workflow monitoring, approvals, agent status, and event log

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           HUMAN LAYER (Dashboard / Approvals)        │
├─────────────────────────────────────────────────────┤
│           ORCHESTRATION (Workflow Engine)             │
├─────────────────────────────────────────────────────┤
│                 AGENT LAYER (11 Agents)               │
│  Requirements │ BA │ Architect │ CodeGen │ Reviewer   │
│  QA │ Security │ DevOps │ SRE │ Docs │ Orchestrator  │
├─────────────────────────────────────────────────────┤
│           EVENT BUS (In-Memory / Kafka-like)          │
├─────────────────────────────────────────────────────┤
│  MEMORY: Working (Dict) │ Episodic (SQLite) │ LTM    │
├─────────────────────────────────────────────────────┤
│           TOOL GATEWAY (Manifest-enforced)            │
├─────────────────────────────────────────────────────┤
│           LLM LAYER (LiteLLM → OpenAI/Anthropic)     │
└─────────────────────────────────────────────────────┘
```

## The 11 Agents

| Agent | Stage | Role |
|-------|-------|------|
| Requirements Agent | Requirements | Parses business inputs into structured requirement catalogs |
| Business Analyst Agent | Business Analysis | Generates BRDs, user stories, acceptance criteria |
| Architect Agent | Architecture | Produces ADRs, API contracts (OpenAPI), data schemas |
| Code Generation Agent | Code Generation | Generates code, unit test scaffolding, PRs |
| Code Reviewer Agent | Code Review | Reviews PRs for quality, standards, anti-patterns |
| QA Agent | Testing | Generates test suites, reports coverage, regression risk |
| Security Agent | Security Scan | SAST/DAST scanning, CVE detection, compliance checks |
| DevOps Agent | CI/CD | Pipeline execution, container builds, deployments |
| SRE Agent | Monitoring | SLO validation, alert rules, health dashboards |
| Documentation Agent | Documentation | API docs, runbooks, changelogs, architecture overviews |
| Orchestrator Agent | Feedback | Sprint reports, velocity metrics, retrospective insights |

## Quick Start

### Prerequisites

- Python 3.11+
- (Optional) An OpenAI or Anthropic API key for real LLM responses

### Setup

```bash
# 1. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional — works without API key using mock responses)
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 4. Run the platform
python -m backend.main
```

### Access

- **Dashboard**: http://localhost:8000
- **API Docs** (Swagger): http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

### Via Dashboard

1. Open http://localhost:8000 in your browser
2. Go to **Workflows** tab
3. Fill in a business brief (e.g., "Build a customer onboarding service that collects KYC data and sends welcome emails")
4. Click **Create & Run Workflow**
5. Watch the pipeline progress through all 13 SDLC stages
6. Review agent outputs, approval gates, and generated artifacts

### Via API

```bash
# Create a workflow
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{"title":"Onboarding Service","project_name":"onboarding-svc","business_brief":"Build a customer onboarding service with KYC validation and welcome emails.","description":""}'

# Run the workflow (replace {id} with the workflow ID from above)
curl -X POST http://localhost:8000/api/workflows/{id}/run

# Check workflow status
curl http://localhost:8000/api/workflows/{id}

# View all events
curl http://localhost:8000/api/events

# View agent statuses
curl http://localhost:8000/api/agents

# Test tool gateway (manifest enforcement)
curl -X POST http://localhost:8000/api/gateway/invoke \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"requirements","tool_name":"jira.create_epic","parameters":{"summary":"Test epic"}}'
```

## Project Structure

```
PlatformGen/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (Pydantic)
│   ├── agents/
│   │   ├── base.py                # Base agent contract
│   │   ├── requirements_agent.py  # Requirements Agent
│   │   ├── ba_agent.py            # Business Analyst Agent
│   │   ├── architect_agent.py     # Architect Agent
│   │   ├── codegen_agent.py       # Code Generation Agent
│   │   ├── reviewer_agent.py      # Code Reviewer Agent
│   │   ├── qa_agent.py            # QA/Testing Agent
│   │   ├── security_agent.py      # Security Agent
│   │   ├── devops_agent.py        # DevOps/Release Agent
│   │   ├── sre_agent.py           # SRE Agent
│   │   ├── docs_agent.py          # Documentation Agent
│   │   └── orchestrator_agent.py  # Orchestrator Agent
│   ├── core/
│   │   ├── event_bus.py           # In-memory event bus (Kafka-like)
│   │   ├── memory.py              # Three-tier memory layer
│   │   ├── llm.py                 # LLM integration (LiteLLM)
│   │   └── workflow.py            # Workflow engine (DAG execution)
│   ├── models/
│   │   ├── schemas.py             # Pydantic models
│   │   └── database.py            # SQLAlchemy models + SQLite
│   ├── api/
│   │   ├── workflows.py           # Workflow CRUD + execution
│   │   ├── approvals.py           # Human-in-the-loop gates
│   │   └── agents.py              # Agent status + dashboard
│   └── gateway/
│       └── tool_gateway.py        # Tool API gateway + audit
├── frontend/
│   ├── index.html                 # Dashboard SPA
│   ├── styles.css                 # Dark theme styles
│   └── app.js                     # Dashboard logic
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Key Design Decisions (from Architecture Document)

| Decision | POC Implementation | Production Target |
|----------|-------------------|-------------------|
| Agent Orchestration | Async workflow engine | LangGraph + Temporal |
| Event Bus | In-memory pub/sub | Apache Kafka |
| Working Memory | Python dict | Redis |
| Episodic Memory | SQLite | PostgreSQL + pgvector |
| Long-Term Memory | In-memory keyword search | Pinecone / Weaviate |
| Knowledge Graph | Not included in POC | Neo4j |
| LLM Access | LiteLLM (mock fallback) | LiteLLM → GPT-4o / Claude |
| Tool Gateway | FastAPI + manifest enforcement | Same (production-grade) |
| Security | Simplified | SPIFFE/SPIRE + Vault + OPA |
| Deployment | Local Python | Kubernetes with namespace isolation |

## Mock Mode

When no LLM API key is configured, the platform runs in **mock mode** — generating realistic but pre-defined responses for each agent stage. This lets you explore the full workflow, dashboard, and architecture without any external dependencies.

## License

Confidential — Internal use only.
>>>>>>> 21465e5 (Initial Commit for POC)
