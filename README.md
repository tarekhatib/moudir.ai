# Moudir.ai

Moudir gives managers a daily, weekly and monthly view of how their team works: a lightweight
desktop agent records high-level activity (focused apps, browser tab titles, idle time), and the
dashboard turns it into productivity scores, trends and PDF reports.

It is multi-tenant: each company signs up, gets its own isolated data, and can add several
manager accounts.

```
Employee PC                        Your server
┌──────────────┐   HTTPS /api   ┌──────────────────────────────────────────┐
│ agent/       │ ─────────────▶ │ Caddy (web)  ──/api──▶  FastAPI (backend)│
│ (per-employee│                │   serves dashboard/        │             │
│  token)      │                │                            ▼             │
└──────────────┘                │                        PostgreSQL        │
       Manager's browser ──────▶│                                          │
                                └──────────────────────────────────────────┘
```

| Folder | What it is |
| :--- | :--- |
| [`backend/`](backend) | FastAPI API, SQLAlchemy models, Alembic migrations, tests |
| [`dashboard/`](dashboard) | React + TypeScript manager dashboard (Vite) |
| [`agent/`](agent) | Windows tracking agent (Python) |
| [`docs/`](docs) | API, scoring, privacy, deployment and demo docs |

## Run it locally

Requires Python 3.13 and Node 22.

```bash
# Terminal 1 — backend on :8000 (SQLite in backend/data/)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_mock_data.py      # optional demo company with 5 weeks of activity
uvicorn app.main:app --reload

# Terminal 2 — dashboard on :5173 (proxies /api to :8000)
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173 and either create a company account or sign in to the demo
company with `demo@demo.moudir.example` / `moudir-demo-password`.

To connect a real agent, see [agent/README.md](agent/README.md).

## Tests

```bash
cd backend && pytest            # API, auth, tenant isolation, ingestion, scoring
cd dashboard && npm run lint && npm run build
```

CI runs both, checks the migrations against PostgreSQL and builds the Docker images
([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Deploy

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): one `docker compose up -d` on a server with a
domain name gives you PostgreSQL, the API and the dashboard with automatic HTTPS.

## Docs

- [API reference](docs/API.md)
- [Scoring model](docs/SCORING.md)
- [Privacy & data collected](docs/PRIVACY.md)
- [Known limitations](docs/KNOWN-ISSUES.md)
- [Local demo walkthrough](docs/DEMO-RUNBOOK.md)
