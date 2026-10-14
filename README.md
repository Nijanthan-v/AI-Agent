# ⚡ Tier-2 Autonomous Support & Root-Cause Diagnostic AI Agent

An end-to-end, production-grade **Tier-2 Autonomous Customer Support & Diagnostic AI Agent** powered by **LangGraph**, **Google Gemini**, **Neon Cloud PostgreSQL**, and a **Next.js 16 Operator Dashboard**.

Built with a **deterministic anti-hallucination circuit breaker** and a **Human-in-the-Loop (HITL) 1-Click approval gate** to safely resolve customer billing, webhook failure, and account suspension issues.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Frontend["🖥️ Operator Portal (Next.js 16 + React 19)"]
        UI["Support Operator Dashboard\n(Glassmorphism Dark Mode)"]
        Queue["Real-time Ticket Queue"]
        Inspector["Evidence & Root Cause Inspector"]
        HITL["1-Click Approval / Veto Gate"]
    end

    subgraph Backend["⚡ Microservice (FastAPI + LangGraph)"]
        API["FastAPI Endpoints\n(/diagnose, /approve, /reject, /tickets)"]
        
        subgraph Graph["LangGraph Diagnostic Workflow"]
            N1["node_extract_context"] --> N2["node_query_tools"]
            N2 --> N3["node_reason_root_cause"]
            N3 --> N4["node_audit_verification\n(Deterministic Circuit Breaker)"]
            N4 --> N5["node_draft_resolution"]
        end
    end

    subgraph DataLayer["🐘 Data & External Services"]
        NeonDB[("Neon Cloud PostgreSQL\n(AWS Singapore)")]
        Stripe["Stripe Gateway Mock & Live SQL"]
        LLM["Google Gemini\n(gemini-3.8-flash / 3.6-flash fallback)"]
    end

    UI --> API
    API --> Graph
    N2 --> NeonDB
    N2 --> Stripe
    N3 --> LLM
    N5 --> NeonDB
    HITL -->|POST /approve or /reject| API
```

---

## 🚀 Key Features

* **LangGraph Multi-Agent Orchestration**: Structured state machine graph with automatic multi-model fallback (`gemini-3.8-flash` ➔ `gemini-3.6-flash`), request timeout safeguards, and retry handling.
* **Deterministic Anti-Hallucination Circuit Breaker**: Pure Python deterministic verification node (`node_audit_verification`) that validates LLM proposals against ground-truth database state. Prevents illegal double refunds, unearned upgrades, and improper suspensions before reaching the operator.
* **Human-in-the-Loop (HITL) Approval Gate**: Autonomous resolution drafting with mandatory human operator sign-off (`/approve` to execute live database/billing changes, or `/reject` to veto and escalate to Tier-3).
* **Live Neon Cloud PostgreSQL**: Real serverless PostgreSQL connection with connection pooling and SSL encryption, tracking users, system logs, Stripe charges, and tickets.
* **Modern Operator Dashboard**: Next.js 16 (React 19) interface featuring dark-mode glassmorphism, real-time ticket queue, root-cause inspector, and 1-click simulation modal.

---

## 📂 Repository Structure

```
.
├── agent.py                 # LangGraph workflow, model fallbacks & audit circuit breaker
├── server.py                # FastAPI microservice REST API
├── tools.py                 # Neon PostgreSQL queries & action executors
├── setup_db.py              # Database table migration & seeding script
├── seed_database.sql        # Reference SQL schema and seed records
├── test_agent.py            # Headless 1-second CLI agent testing script
├── requirements.txt         # Python backend dependencies
├── Dockerfile               # Production Dockerfile for FastAPI microservice
├── docker-compose.yml       # Full-stack Docker orchestration
├── .env.example             # Template for required environment variables
├── .gitignore               # Multi-layer secret & build artifact protection
└── dashboard/               # Next.js 16 Operator Dashboard
    ├── Dockerfile           # Next.js production Dockerfile
    ├── package.json         # Node.js dependencies
    └── src/
        └── app/
            ├── page.tsx     # Operator Dashboard UI
            ├── globals.css  # Dark-mode glassmorphism styles
            └── layout.tsx   # Root layout & Google typography
```

---

## 🛠️ Quickstart (Local Development)

### Prerequisites
* Python 3.10+
* Node.js 18+ & npm
* Google Gemini API Key

### 1. Clone the Repository
```bash
git clone https://github.com/Nijanthan-v/AI-Agent.git
cd AI-Agent
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Populate `.env` with your credentials:
```env
GEMINI_API_KEY="your-google-gemini-api-key"
DATABASE_URL="postgresql://user:password@ep-cool-service.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
```

### 3. Set Up & Run the Backend (FastAPI + LangGraph)
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Seed Neon PostgreSQL tables
python setup_db.py

# Start the agent microservice
python server.py
```
* **API URL**: `http://localhost:8000`
* **Swagger UI / Interactive API Docs**: `http://localhost:8000/docs`

### 4. Start the Operator Dashboard (Next.js 16)
In a new terminal:
```bash
cd dashboard
npm install
npm run dev
```
* **Dashboard URL**: `http://localhost:3000`

---

## 🧪 Headless Testing
Test the agent logic and circuit breaker directly from your terminal in 1 second without opening the browser:
```bash
source venv/bin/activate
python test_agent.py
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/diagnose` | Ingests customer issue, queries DB logs/Stripe, runs LangGraph diagnosis, and stores ticket. |
| `POST` | `/approve` | Operator 1-click execution: applies database tier upgrade, issues refund, or unlocks account. |
| `POST` | `/reject` | Operator veto: cancels automated action and routes ticket to manual Tier-3 engineering queue. |
| `GET` | `/tickets` | Retrieves live ingested tickets ordered by most recent first. |
| `GET` | `/tickets/{ticket_id}` | Retrieves full diagnostic data and audit status for a specific ticket. |

---

## 🚢 Production Deployment

### Option A: Free Cloud Deployment
1. **Database**: Hosted on [Neon.tech](https://neon.tech) (PostgreSQL serverless cloud).
2. **Backend**: Deploy to [Render.com](https://render.com) as a Web Service (`uvicorn server:app --host 0.0.0.0 --port $PORT`).
3. **Frontend**: Deploy `dashboard/` to [Vercel](https://vercel.com) with environment variable `NEXT_PUBLIC_API_URL` pointing to your Render backend.

### Option B: Docker Compose
```bash
docker compose up -d --build
```
* Backend runs on `:8000`
* Frontend runs on `:3000`

---

## 🛡️ Deterministic Safety Rules
1. **Tier Upgrade**: Blocked if customer is already on `pro` or `enterprise` tier.
2. **Refunds**: Blocked unless duplicate charges with exact identical amounts are confirmed via SQL in Stripe records.
3. **Account Unlock**: Blocked if account is not in `suspended` or `locked` state.

---

## 📄 License
MIT License. Free to use and modify for enterprise support workflows.
