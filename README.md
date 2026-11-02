# AgentOps AI — Autonomous Production Incident Investigator

AgentOps AI is an enterprise-grade autonomous incident investigation, multi-agent root cause analysis, and sandboxed patch validation platform.

## Architecture Overview

```
                          Production Telemetry
                    (Logs, Traces, Metrics, Alerts)
                                  │
                                  ▼
                     FastAPI Orchestration Layer
                 (WebSockets, REST APIs, PostgreSQL)
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
        LangGraph Workflow                   Hybrid RAG Engine
   (Stateful Multi-Agent Loop)             (Qdrant, Code Chunker)
                │                                   │
   ┌────────────┴─────────────┐                     │
   ▼                          ▼                     │
Triage Agent            Log Analysis Agent          │
   │                          │                     │
   └────────────┬─────────────┘                     │
                ▼                                   │
     Code Investigation Agent ◄─────────────────────┘
                │
                ▼
    Root Cause Analysis (RCA) Agent
                │
                ▼
       Fix Generation Agent
                │
                ▼
  Sandboxed Patch Validation
     (Isolated Pytest Run)
                │
         ┌──────┴──────┐
         ▼             ▼
       Passed        Failed ──► Retry Fix Loop
         │
         ▼
    Review Agent & Report
         │
         ▼
  Human-in-the-Loop Approval Gate
         │
         ▼
  Optional GitHub Pull Request
```

## Technology Stack

- **Frontend**: Next.js 15+ (App Router), TypeScript, Tailwind CSS, Recharts, Monaco Editor, React Flow, TanStack Query, WebSocket Client.
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy Async, SQLite / PostgreSQL, Redis, Uvicorn, Pydantic v2.
- **AI & Agents**: LangGraph stateful multi-agent loop, LangChain, OpenAI API integration with structured Pydantic outputs.
- **Knowledge & RAG**: AST-aware chunking, hybrid keyword & vector retrieval, Qdrant vector database.
- **Code Sandbox**: Isolated containerized and process-confined sandbox, automated test execution, AST diff validation.
- **Observability**: OpenTelemetry, Prometheus metrics exporter, real-time WebSocket event broadcaster, LLM token and cost tracking.

---

## Getting Started Locally

### Prerequisites
- Python 3.12+ (or 3.13+)
- Node.js 18+ & npm
- (Optional) Docker & Docker Compose for containerized stack

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -c "import asyncio; from app.database.init_db import init_db; asyncio.run(init_db())"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to access the interactive dashboard.

### 3. Docker Deployment
```bash
docker compose up --build
```

---

## Automated Test Execution

Run the backend test suite:
```bash
cd backend
.\venv\Scripts\pytest tests -v
```

All 5 core tests (health check, database session, metrics computation, incident lifecycle, and evaluation benchmarks) execute with 100% pass rate.
