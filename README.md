# ✈️ TripMate AI

> **Production-grade multi-agent AI travel planner** — MCP servers, Supervisor Agent, Input Guardrails, Human-in-the-Loop review, RAG knowledge base, LiteLLM model routing, JWT auth with per-user thread history.

---

## Architecture Overview

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│  INPUT GUARDRAIL  (keyword + LLM check)     │
│  PASS ✓  or  BLOCK ✗                        │
└──────────────────────┬──────────────────────┘
                       │ PASS
                       ▼
┌─────────────────────────────────────────────┐
│         SUPERVISOR AGENT  (GPT-4o)          │
│  • Parses intent → TripConstraints          │
│  • Selects specialist agents dynamically    │
└──┬────┬────┬────┬───────────────────────────┘
   │    │    │    │
   ▼    ▼    ▼    ▼
  ✈️   🏨   ☀️   💰    🗺️
Flight Hotel Weather Budget  Itinerary
Agent  Agent  Agent  Agent    Agent
  │    │    │    │         │
  └────┴────┴────┴─────────┘
                │ Shared TravelState
                ▼
     ┌─────────────────────┐
     │  RAG CONTEXT  inject │  ← ChromaDB knowledge base
     └──────────┬──────────┘
                ▼
     ┌─────────────────────┐
     │  HITL REVIEW GATE   │  ← User: Approve / Change / Reject
     └──────────┬──────────┘
                │ Approved
                ▼
     ┌─────────────────────┐
     │  FINAL RESPONSE     │  ← Markdown travel plan
     │  AGENT  (GPT-4o)    │
     └──────────┬──────────┘
                ▼
         PostgreSQL  ←  Thread + Message history per user
```

### What's New in Part 3
| Feature | Details |
|---------|---------|
| **Input Guardrails** | Keyword check + LLM classifier — blocks irrelevant/harmful requests |
| **Supervisor Agent** | Understands intent, selects required agents, no manual workflow definition |
| **Human-in-the-Loop** | User reviews itinerary → Approve / Request Changes / Reject |
| **MCP Servers** | AviationStack (flights), Tavily (hotels), OpenWeatherMap, Budget — all local |
| **RAG** | ChromaDB vector store with destination knowledge, injected before itinerary planning |
| **User Accounts** | JWT auth, per-user threads, full message history with thread IDs |
| **LiteLLM** | Unified model routing — swap GPT-4o for Llama, Claude, Gemini via one config line |

---

## Project Structure

```
end-to-end-ai-agent-workflow-part2/
├── backend/
│   ├── app/
│   │   ├── agents/              # All AI agents
│   │   │   ├── state.py         # TravelState (shared context)
│   │   │   ├── base_agent.py    # Abstract base
│   │   │   ├── supervisor_agent.py
│   │   │   ├── flight_agent.py
│   │   │   ├── hotel_agent.py
│   │   │   ├── weather_agent.py
│   │   │   ├── budget_agent.py
│   │   │   ├── itinerary_agent.py
│   │   │   └── final_agent.py
│   │   ├── clients/
│   │   │   ├── llm_client.py    # LiteLLM wrapper + tool-call loop
│   │   │   └── mcp_client.py    # MCP HTTP client
│   │   ├── config/
│   │   │   ├── settings.py      # Pydantic Settings (env vars)
│   │   │   ├── system_prompts.py # All agent system prompts
│   │   │   └── logging_config.py
│   │   ├── db/
│   │   │   ├── base.py          # Async SQLAlchemy engine
│   │   │   └── migrations/      # Alembic migrations
│   │   ├── guardrails/
│   │   │   └── input_guardrail.py
│   │   ├── hitl/
│   │   │   └── hitl_service.py
│   │   ├── mcp_servers/         # FastMCP servers (run as separate processes)
│   │   │   ├── flight_mcp.py    # AviationStack  (port 8001)
│   │   │   ├── hotel_mcp.py     # Tavily          (port 8002)
│   │   │   ├── weather_mcp.py   # OpenWeatherMap  (port 8003)
│   │   │   └── budget_mcp.py    # ExchangeRate    (port 8004)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── rag/                 # ChromaDB + embeddings
│   │   ├── routes/              # FastAPI routers
│   │   ├── services/            # Business logic services
│   │   ├── tools/               # Agent tool wrappers + LiteLLM schemas
│   │   └── main.py              # FastAPI app entry point
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── Dockerfile
│   └── Dockerfile.mcp
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # Navbar, LoadingSpinner, AgentProgressBar
│   │   │   ├── trip/            # TripForm, FlightCard, HotelCard, etc.
│   │   │   └── hitl/            # HITLReviewPanel
│   │   ├── pages/               # HomePage, HistoryPage, LoginPage, etc.
│   │   ├── services/            # API clients (axios)
│   │   ├── stores/              # Zustand state stores
│   │   ├── types/               # TypeScript interfaces
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml           # Production
├── docker-compose.dev.yml       # Development overrides
└── README.md
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2
- An OpenAI API key (minimum — others are optional)

### 1. Clone & configure

```bash
git clone <repo-url>
cd end-to-end-ai-agent-workflow-part2

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum set OPENAI_API_KEY
```

### 2. Run with Docker Compose

```bash
# Pull images + build
docker compose build

# Run database migrations first
docker compose --profile migrate run --rm migrate

# Start all services
docker compose up -d

# Tail logs
docker compose logs -f backend
```

Services started:
| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MCP Flight | http://localhost:8001 |
| MCP Hotel | http://localhost:8002 |
| MCP Weather | http://localhost:8003 |
| MCP Budget | http://localhost:8004 |
| ChromaDB | http://localhost:8005 |

### 3. Local development (hot reload)

```bash
# Terminal 1 — infrastructure only
docker compose up postgres redis chromadb -d

# Terminal 2 — MCP servers
cd backend
pip install -r requirements.txt
python -m app.mcp_servers.flight_mcp &
python -m app.mcp_servers.hotel_mcp &
python -m app.mcp_servers.weather_mcp &
python -m app.mcp_servers.budget_mcp &

# Terminal 3 — FastAPI backend
uvicorn app.main:app --reload --port 8000

# Terminal 4 — React frontend
cd frontend
npm install
npm run dev
```

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Revoke all tokens |
| GET | `/api/v1/auth/me` | Get current user |
| PATCH | `/api/v1/auth/me` | Update profile |

### Trip Planning
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/trips/plan` | Start planning (returns hitl_payload) |
| POST | `/api/v1/trips/hitl` | Submit review decision |
| GET | `/api/v1/trips/stream/{thread_id}` | SSE stream for live progress |

### Thread History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/threads` | List all threads (paginated) |
| GET | `/api/v1/threads/{id}` | Get thread with messages |
| GET | `/api/v1/threads/{id}/messages` | Get thread messages |
| DELETE | `/api/v1/threads/{id}` | Delete thread |

### RAG (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rag/ingest` | Add document to knowledge base |
| POST | `/api/v1/rag/ingest/seed` | Seed built-in knowledge |
| POST | `/api/v1/rag/query` | Search knowledge base |
| GET | `/api/v1/rag/stats` | Document count |

---

## Configuration Guide

### Model Routing via LiteLLM

Change models without touching agent code — just update `.env`:

```bash
# Use Groq Llama3 for cheap agents (free tier)
FLIGHT_AGENT_MODEL=groq/llama3-70b-8192
HOTEL_AGENT_MODEL=groq/llama3-70b-8192
WEATHER_AGENT_MODEL=groq/llama3-70b-8192
BUDGET_AGENT_MODEL=groq/llama3-70b-8192

# Keep GPT-4o for reasoning-heavy agents
SUPERVISOR_MODEL=gpt-4o
ITINERARY_AGENT_MODEL=gpt-4o
FINAL_AGENT_MODEL=gpt-4o
```

### API Keys (all optional — mock data used if not set)

| Key | Source | Cost |
|-----|--------|------|
| `OPENAI_API_KEY` | platform.openai.com | Pay-per-use |
| `AVIATIONSTACK_API_KEY` | aviationstack.com | Free: 500/month |
| `TAVILY_API_KEY` | tavily.com | Free: 1000/month |
| `OPENWEATHER_API_KEY` | openweathermap.org | Free tier |
| `EXCHANGERATE_API_KEY` | exchangerate-api.com | Free: 1500/month |

### Adding Fine-tuned Models

To plug in a fine-tuned model (e.g. a travel-specific Llama fine-tune):

1. Host it via Ollama or vLLM
2. Set in `.env`:
   ```bash
   ITINERARY_AGENT_MODEL=ollama/your-fine-tuned-model
   ```
3. LiteLLM routes the call automatically — no code changes needed.

---

## HITL Workflow

```
POST /api/v1/trips/plan
    → status: "awaiting_review"
    → hitl_payload: { itinerary, flights, hotels, weather, budget }

User reviews in frontend review panel
    ↓
POST /api/v1/trips/hitl  { decision: "approve" }
    → status: "completed"
    → final_response: "# ✈️ Your Trip to Dubai..."

POST /api/v1/trips/hitl  { decision: "request_changes", feedback: "Find cheaper hotels" }
    → Supervisor.replan() called with hotel_agent re-run
    → status: "awaiting_review" (new review round)

POST /api/v1/trips/hitl  { decision: "reject" }
    → status: "rejected"
```

---

## Thread History

Every trip planning session creates a **Thread** with a unique UUID.  
Each thread stores:
- Full message history (user → agent → assistant → HITL)
- Complete `TravelState` snapshot (all agent outputs)
- HITL status and feedback
- Agent checkpoints (for resume/rollback)

Users can view all their threads on the `/history` page, click into any thread to see the full conversation with thread IDs, and delete threads they no longer need.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Orchestration | Custom LangGraph-style supervisor pattern |
| LLM Router | LiteLLM (OpenAI / Anthropic / Groq / Gemini) |
| MCP Servers | FastMCP (local SSE transport) |
| RAG | ChromaDB + OpenAI text-embedding-3-small |
| Backend | FastAPI + SQLAlchemy (async) + Alembic |
| Database | PostgreSQL 16 |
| Cache/Pub-Sub | Redis 7 |
| Auth | JWT (access + refresh token rotation) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| State | Zustand |
| Containers | Docker + Docker Compose |

---

## Development Notes

- **Mock data fallback**: All external API calls fall back to realistic mock data when API keys are not configured, so the full pipeline runs in dev without any paid API access.
- **Guardrail fail-open**: If the guardrail LLM is unavailable, requests pass with a warning log rather than blocking all traffic.
- **HITL timeout**: Configurable via `HITL_TIMEOUT_SECONDS`. Set `HITL_AUTO_APPROVE_AFTER_TIMEOUT=true` for unattended pipelines.
- **RAG seeding**: The knowledge base is auto-seeded on startup with built-in destination guides. Add custom documents via `POST /api/v1/rag/ingest`.

---

## License

MIT — see [LICENSE](LICENSE)
