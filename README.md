# ⚡ Tier-2 Autonomous Support & Root-Cause Diagnostic AI Agent

An enterprise-grade **Tier-2 Autonomous Customer Support & Diagnostic AI Agent** powered by **LangGraph**, **Google Gemini**, **Neon Cloud PostgreSQL**, and a standalone **Next.js 16 Operator Dashboard** ([support-agent-ui](https://github.com/Nijanthan-v/support-agent-ui)).

Built with a **deterministic anti-hallucination circuit breaker** and a **Human-in-the-Loop (HITL) 1-Click approval gate** to safely resolve customer billing, webhook failure, and account suspension issues without unverified database writes.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client["🖥️ Operator Portal (support-agent-ui)"]
        UI["Support Dashboard\n(Next.js 16 + React 19)"]
        HITL["1-Click Operator Gate\n(Approve / Veto / Reject)"]
    end

    subgraph Backend["⚡ Microservice API (server.py)"]
        API["FastAPI Async Endpoints\n(/diagnose, /approve, /reject, /tickets, /health)"]
        Pool["ThreadedConnectionPool\n(Min 2, Max 20)"]
    end

    subgraph LangGraph["🤖 LangGraph Diagnostic Engine (agent.py)"]
        N1["1. node_fetch_context\n(Parse User & Escalation Metadata)"]
        N2["2. node_execute_tools\n(Query DB Account, Charges & Log Traces)"]
        N3["3. node_analyze_root_cause\n(Gemini / OpenAI Structured Reasoning)"]
        N4["4. node_audit_verification\n(🛡️ Deterministic Circuit Breaker)"]
        N5["5. node_human_approval_gate\n(Pause State: awaiting_approval)"]

        N1 --> N2 --> N3 --> N4 --> N5
    end

    subgraph Storage["🐘 Data & External Services"]
        NeonDB[("Neon Cloud PostgreSQL\n(users, logs, charges, tickets)")]
        Stripe["Stripe Gateway Mock & Live SQL"]
        LLM["Google Gemini / OpenAI\n(gemini-flash-lite / 2.5-flash / gpt-4o-mini)"]
    end

    UI -->|HTTP REST| API
    HITL -->|POST /approve or /reject| API
    API -->|asyncio.to_thread| N1
    N2 <-->|get_db_cursor| Pool
    Pool <--> NeonDB
    N2 --> Stripe
    N3 <--> LLM
    API -->|save_ticket_tool / execute_resolution_action| Pool
```

---

## 🚀 Key Production Features

* **LangGraph Deterministic Workflow**: Structured state machine graph with automatic multi-model fallback (`gemini-flash-lite-latest` ➔ `gemini-2.5-flash` ➔ `gpt-4o-mini` ➔ dynamic rule synthesis).
* **Deterministic Anti-Hallucination Circuit Breaker**: Pure-Python verification node (`node_audit_verification`) that validates LLM proposals against ground-truth database state before operator review:
  * **Tier Upgrade**: Blocked if customer is already on `pro` or `enterprise`, or if payment did not succeed.
  * **Invoice Refund**: Blocked unless duplicate charges with exact amounts are verified in database.
  * **Account Unlock**: Blocked if user status is not explicitly `suspended`.
* **Human-in-the-Loop (HITL) Gate**: High-risk mutations are held in `awaiting_approval`. Operators execute live database upgrades or refunds with 1 click, or veto and escalate to Tier-3.
* **High-Concurrency PostgreSQL Pooling**: `ThreadedConnectionPool` manages persistent SSL connections to Neon Cloud, eliminating per-query TLS handshakes and connection leaks.
* **Non-Blocking Async Event Loop**: All FastAPI endpoints are asynchronous; blocking AI/database operations run in worker thread pools via `asyncio.to_thread`.
* **Hardened Docker Container**: Runs under an unprivileged non-root user (`appuser`), includes active healthcheck probes, and supports configurable workers.

---

## 📂 Repository Structure

```
.
├── agent.py            # LangGraph workflow, multi-model fallbacks, & circuit breaker
├── server.py           # FastAPI microservice with async event loop offloading & pool management
├── tools.py            # ThreadedConnectionPool, context managers, & idempotent SQL executors
├── setup_db.py         # Automated database schema migration script
├── seed_database.sql   # Complete SQL schema (users, system_logs, stripe_charges, tickets)
├── test_agent.py       # Headless CLI testing script (1-second dry run)
├── requirements.txt    # Pinned Python dependencies
├── Dockerfile          # Production Dockerfile (non-root appuser, healthcheck probe)
├── docker-compose.yml  # Docker orchestration for agent API
├── .env.example        # Environment variable template
└── .gitignore          # Multi-layer secret protection
```

> **Operator Dashboard**: The Next.js 16 frontend is decoupled into **[support-agent-ui](https://github.com/Nijanthan-v/support-agent-ui)**.

---

## 🛠️ Quickstart (Local Development)

### Prerequisites
* Python 3.10+
* Google Gemini API Key (or OpenAI API Key)
* Neon Cloud PostgreSQL account (or local SQLite fallback)

### 1. Setup & Environment
```bash
git clone https://github.com/Nijanthan-v/AI-Agent.git
cd AI-Agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Populate `.env`:
```env
GEMINI_API_KEY="your-google-gemini-api-key"
DATABASE_URL="postgresql://user:password@ep-cool-service.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
PORT=8000
```

### 2. Initialize Database & Run Server
```bash
# Initialize schema and seed sample customer records
python setup_db.py

# Start the agent microservice
python server.py
```
* **API URL**: `http://localhost:8000`
* **Interactive Docs (Swagger UI)**: `http://localhost:8000/docs`
* **Health Endpoint**: `http://localhost:8000/health`

### 3. Headless Dry Run
Test the agent logic, circuit breaker, and database fallback in 1 second directly from your terminal:
```bash
python test_agent.py
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck reporting database connectivity, engine type, and pool state. |
| `GET` | `/tickets` | Retrieves live ingested tickets, optionally filtered by status (`?status=awaiting_approval`). |
| `GET` | `/tickets/{id}` | Retrieves full diagnostic details and audit trail for a specific ticket. |
| `POST` | `/diagnose` | Ingests customer complaint, compiles FactSheet, runs diagnosis, and saves ticket. |
| `POST` | `/approve` | 1-Click execution: applies tier upgrade, issues refund, or unlocks account in database. |
| `POST` | `/reject` | Operator veto: cancels automated action and escalates to Tier-3 queue. |

---

## 🐳 Docker Deployment

### Run Container Locally
```bash
# Build production image
docker build -t support-agent-api .

# Run with environment variables
docker run -p 8000:8000 \
  -e GEMINI_API_KEY="your-key" \
  -e DATABASE_URL="your-db-url" \
  support-agent-api
```

### Run with Docker Compose
```bash
docker compose up -d --build
```

---

## 📄 License

MIT License. Free to use and modify for enterprise support automation workflows.
