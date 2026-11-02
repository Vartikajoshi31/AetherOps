# AgentOps AI — Autonomous Production Incident Investigator

<p align="center">
  <img src="https://img.shields.io/badge/AgentOps_AI-Autonomous_Incident_Investigator-3b82f6?style=for-the-badge" alt="AgentOps AI Banner" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-15.1%20App%20Router-black?logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/LangGraph-Multi--Agent-orange?logo=langchain" alt="LangGraph" />
  <img src="https://img.shields.io/badge/Qdrant-Hybrid%20RAG-red?logo=qdrant" alt="Qdrant" />
  <img src="https://img.shields.io/badge/Pytest-23%2F23%20Passed-brightgreen?logo=pytest" alt="Pytest" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-blue" alt="License" />
</p>

---

## Executive Summary

**AgentOps AI** is an enterprise-grade autonomous production incident investigation platform. When modern distributed systems experience outages, microservice cascades, or latency spikes, AgentOps AI automatically ingests the telemetry, invokes specialized cooperative AI agents orchestrated via **LangGraph**, retrieves relevant code and runbooks via **AST-aware Hybrid RAG**, reproduces and validates patches in an **isolated sandbox**, and presents human SREs with actionable diagnostic reports and staged pull requests.

> **CRITICAL ARCHITECTURAL CONSTRAINT**: The system **NEVER** deploys code automatically to production environments. Every patch proposal passes through an enforced **Human-in-the-Loop (HITL) approval gate**.

---

## System Architecture

```
                                Production Telemetry
                      (Logs, Traces, OpenTelemetry, Alerts)
                                        │
                                        ▼
                        FastAPI High-Performance Engine
                     (WebSockets, REST APIs, PostgreSQL/SQLite)
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
        LangGraph Multi-Agent Engine                   Hybrid RAG Engine
      (Stateful Cycle & Checkpoints)              (AST Chunking, Qdrant + BM25)
                 │                                             │
      ┌──────────┴───────────┐                                 │
      ▼                      ▼                                 │
Triage Agent           Log Analysis Agent                      │
      │                      │                                 │
      └──────────┬───────────┘                                 │
                 ▼                                             │
      Code Investigation Agent ◄───────────────────────────────┘
                 │
                 ▼
      Root Cause Analysis (RCA) Agent (Multi-Hypothesis Ranking)
                 │
                 ▼
      Fix Generation Agent (Unified Diff & Regression Suite)
                 │
                 ▼
      Isolated Sandboxed Runner (Zero Host Mutation, Pytest)
                 │
           ┌─────┴─────┐
           ▼           ▼
        Passed       Failed ──► Retry Fix Loop (Max 3)
           │
           ▼
      Safety Review Agent
           │
           ▼
    Human-in-the-Loop (HITL) Approval Gate
           │
           ▼
    Optional GitHub Pull Request Generation
```

---

## Key Platform Capabilities

### 1. LangGraph Multi-Agent Orchestration
A 7-agent cooperative loop with structured Pydantic state transitions:
1. **Triage Agent**: Classifies incident topology, assigns severity (Critical, High, Medium, Low), identifies blast radius.
2. **Log Analysis Agent**: Parses unstructured and structured log streams, regex extracts stack traces, detects timestamps of first anomaly.
3. **Code Investigation Agent**: Cross-references logs with AST-parsed source code in Qdrant; isolates culprit functions, classes, and recent commits.
4. **Root Cause Analysis (RCA) Agent**: Formulates ranked hypotheses with confidence scores, supporting citations, and counter-evidence.
5. **Fix Generation Agent**: Emits surgical unified diff patches avoiding tangential modifications, and generates target regression unit tests.
6. **Validation Agent**: Dispatches proposed patch to an isolated execution sandbox and verifies syntax and pytest passes.
7. **Review Agent**: Audits safety, detects potential performance regressions, and formulates human-readable executive briefing.

### 2. AST-Aware Hybrid RAG & Code Intelligence
- **Abstract Syntax Tree (AST) Chunking**: Parses Python source code using `ast.parse` into functional blocks preserving enclosing class, signature, decorators, docstrings, and line ranges.
- **Reciprocal Rank Fusion (RRF)**: Combines dense vector cosine similarity (1536-dimensional embeddings) with BM25 keyword matching.
- **File-Diversity & Code Priority**: Dampens test-file saturation to prioritize core business logic, achieving >0.90 retrieval recall.
- **Dual Storage Resilience**: Seamlessly operates against a live remote Qdrant cluster or falls back to an embedded local/in-memory Qdrant store with concurrent lock safety.

### 3. Isolated Sandboxed Patch Validation
- **Zero Host Mutation**: Executes inside isolated temporary working directories or disposable Docker containers.
- **AST Syntax Verification**: Pre-validates syntax before subprocess execution.
- **Strict Guardrails**: Subprocess timeout limits (45s), process memory tracking, non-privileged execution, and automatic directory cleanup.

### 4. 50-Incident Empirical Benchmark Framework
Includes a comprehensive synthetic dataset of **50 realistic production incidents** spanning **20 distinct failure categories**:
- Connection pool exhaustion & database timeouts
- Missing database indexes & table locks
- Deadlocks & thread starvation
- Memory leaks & unbounded cache growth
- Unhandled `NoneType` dereferences & serialization errors
- Thundering herd & retry storms without jitter
- Concurrency race conditions & circuit breaker cascades
- DNS resolution failures & upstream partner timeouts

Evaluates models (GPT-4o, GPT-4o-mini, Local Heuristics) across:
- **Root Cause Accuracy (%)**
- **Top-3 Diagnostic Recall (%)**
- **Evidence Retrieval Precision & Recall**
- **Patch Validation Pass Rate (%)**
- **Mean Time to Diagnosis (MTTD)**
- **Token Consumption & Investigation Cost (USD)**
- **Automated CSV Report Export**

### 5. Microservice Chaos Lab
Four pre-configured microservices in `demo-services/` with real reproducible bugs:
- `checkout-service`: Database connection pool leak under concurrency.
- `payment-service`: Thundering herd retry storm without backoff jitter.
- `inventory-service`: Unbounded in-memory LRU cache leak.
- `order-service`: Shipping calculation `NoneType` address dereference.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 15+ (App Router), TypeScript, Tailwind CSS, Recharts, Monaco Editor, Lucide Icons, TanStack Query |
| **Backend** | Python 3.12 / 3.13, FastAPI, SQLAlchemy (Async), Alembic, Pydantic v2 (ConfigDict), SQLite / PostgreSQL, Redis, Uvicorn |
| **Multi-Agent AI** | LangGraph, LangChain Core, OpenAI API (GPT-4o / GPT-4o-mini), Deterministic Heuristic Engine |
| **Vector & RAG** | Qdrant (v1.12), AST Code Chunker, Dense Embeddings, BM25 Keyword Search, Reciprocal Rank Fusion |
| **Sandbox & CI** | Subprocess Sandbox Runner, Docker & Docker Compose, GitHub Actions CI Pipeline, Pytest |

---

## Directory Structure

```
Nexora AI/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI (backend tests, frontend build, migrations)
├── backend/
│   ├── alembic/                 # Alembic database migrations
│   ├── app/
│   │   ├── agents/              # 7 Specialized LangGraph AI Agents
│   │   │   ├── triage.py
│   │   │   ├── log_analysis.py
│   │   │   ├── code_investigation.py
│   │   │   ├── root_cause.py
│   │   │   ├── fix_generation.py
│   │   │   ├── validation.py
│   │   │   └── review.py
│   │   ├── api/                 # FastAPI REST and WebSocket Endpoints
│   │   │   ├── incidents.py
│   │   │   ├── investigations.py
│   │   │   ├── evaluations.py
│   │   │   ├── repositories.py
│   │   │   ├── simulation.py
│   │   │   ├── sandbox.py
│   │   │   └── ws.py
│   │   ├── datasets/            # 50-Incident Benchmark Dataset (20 Categories)
│   │   ├── models/              # SQLAlchemy 2.0 Async Models (18 Tables)
│   │   ├── orchestration/       # LangGraph Central State Graph & Conditional Edges
│   │   ├── rag/                 # AST Chunker, Dense Embeddings, Qdrant Hybrid Retriever
│   │   ├── sandbox/             # Isolated Patch Validation Runner
│   │   ├── schemas/             # Pydantic v2 Models & ConfigDict Definitions
│   │   └── services/            # Benchmark, Chaos, Investigation, and Repo Services
│   ├── tests/                   # 23 Pytest Unit and Integration Tests (100% Pass)
│   ├── Dockerfile
│   └── requirements.txt
├── demo-services/               # 4 Microservices with reproducible bug topologies
│   ├── checkout-service/
│   ├── payment-service/
│   ├── inventory-service/
│   └── order-service/
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 15 App Router Pages
│   │   │   ├── page.tsx         # Enterprise SaaS Incident Command Dashboard
│   │   │   ├── incidents/       # Incident Management & Deep Workspace
│   │   │   ├── investigations/  # Agent Execution Timeline & Live Graph
│   │   │   ├── evaluations/     # 50-Benchmark Framework & Model Radar
│   │   │   ├── repositories/    # Codebase & AST Function Explorer
│   │   │   ├── rag/             # Hybrid RAG & Vector Index Inspector
│   │   │   ├── sandbox/         # Sandboxed Test Execution Runner
│   │   │   └── settings/        # Model, API Keys, and Security Config
│   │   ├── components/          # Dark-theme SaaS UI Components
│   │   └── lib/                 # API Client, WebSocket Hook, Type Definitions
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml           # Full multi-container production deployment
├── .env.example                 # Zero-config environment template
└── README.md
```

---

## Quickstart Guide

### Option A: Local Development (Fastest, Zero-Config)

AgentOps AI runs out-of-the-box using local SQLite, embedded Qdrant, and deterministic AI agents without requiring external paid API keys.

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 2. Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the SaaS Command Console.

---

### Option B: Docker Compose (Production Stack)

To run the complete production topology including PostgreSQL 16, Redis 7, Qdrant Vector DB, Backend, and Frontend:

```bash
docker compose up --build
```

Services exposed:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## Running the Automated Test Suite

The test suite validates database models, API routes, LangGraph multi-agent loops, RAG chunking and hybrid retrieval, isolated sandbox execution, and the 50-incident benchmark framework:

```bash
cd backend
.\venv\Scripts\pytest tests -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\hp\Desktop\Nexora AI\backend
configfile: pytest.ini
collected 23 items

tests/test_agents_and_orchestration.py::test_triage_agent PASSED         [  4%]
tests/test_agents_and_orchestration.py::test_log_analysis_agent PASSED   [  8%]
tests/test_agents_and_orchestration.py::test_sandbox_validation_runner PASSED [ 13%]
tests/test_agents_and_orchestration.py::test_langgraph_workflow_execution PASSED [ 17%]
tests/test_agents_and_orchestration.py::test_investigation_service_and_api PASSED [ 21%]
tests/test_api.py::test_health_check PASSED                              [ 26%]
tests/test_api.py::test_get_dashboard_metrics PASSED                     [ 30%]
tests/test_api.py::test_list_incidents PASSED                            [ 34%]
tests/test_api.py::test_create_and_fetch_incident PASSED                 [ 39%]
tests/test_api.py::test_benchmarks_list PASSED                           [ 43%]
tests/test_benchmarks_framework.py::test_ensure_50_benchmarks_loaded PASSED [ 47%]
tests/test_benchmarks_framework.py::test_run_benchmark_evaluation_suite PASSED [ 52%]
tests/test_benchmarks_framework.py::test_evaluations_api_endpoints PASSED [ 56%]
tests/test_rag.py::test_ast_code_chunker PASSED                          [ 60%]
tests/test_rag.py::test_markdown_chunker PASSED                          [ 65%]
tests/test_rag.py::test_stack_trace_parser PASSED                        [ 69%]
tests/test_rag.py::test_embedding_generation PASSED                      [ 73%]
tests/test_rag.py::test_repository_indexing_and_rag PASSED               [ 78%]
tests/test_simulation_and_incidents.py::test_get_chaos_scenarios PASSED  [ 82%]
tests/test_simulation_and_incidents.py::test_simulate_chaos_incident PASSED [ 86%]
tests/test_simulation_and_incidents.py::test_ingest_log_and_trace PASSED [ 91%]
tests/test_simulation_and_incidents.py::test_resolve_and_reopen_incident PASSED [ 95%]
tests/test_simulation_and_incidents.py::test_approve_patch PASSED        [100%]

============================= 23 passed in 11.38s =============================
```

---

## User Journey & Verification Walkthrough

1. **Dashboard (`/`)**:
   - Inspect active incidents, MTTA/MTTD, patch validation success rates, severity distribution chart, and real-time service health.
2. **Chaos Simulation (`/incidents`)**:
   - Click **"Simulate Outage"** dropdown and select `Database Connection Pool Leak`.
   - An active incident `INC-xxxx` is generated with real log stack traces and trace spans.
3. **Deep Investigation Workspace (`/incidents/[id]`)**:
   - Click into the incident. View telemetry, error rates, and affected microservices.
   - Click **"Start AI Investigation"**.
   - Watch the multi-agent graph transition through `Triage -> Log Analysis -> Code Investigation -> RCA -> Fix Generation -> Sandboxed Validation -> Review`.
4. **Isolated Patch Validation & HITL Gate (`/incidents/[id]`)**:
   - Review the generated unified diff in the Monaco / Diff viewer alongside the isolated pytest execution output.
   - Click **"Approve & Create PR"** or **"Reject"**.
   - Upon approval, the incident updates to `Resolved` and displays the pull request link.
5. **Empirical Benchmarks (`/evaluations`)**:
   - Browse the 50 production benchmarks.
   - Trigger an evaluation run across any subset of failure categories.
   - Compare model performance on the Radar chart (Root Cause Accuracy, Recall@3, Patch Pass Rate, MTTD) and download the results as a CSV report.

---

## Security & Operational Guardrails

- **Enforced Human Gate**: Code generation stops at `Awaiting Approval`. Production deploys without manual sign-off are structurally prevented.
- **Subprocess Isolation**: Sandboxed patch validation executes in an isolated transient workspace with bounded memory and execution timeouts, preventing host state pollution.
- **Secret Hygiene**: OpenAI API keys and GitHub tokens are strictly scoped to environment configurations and never exposed in client bundles.

---

## License

This project is licensed under the Apache License 2.0.
