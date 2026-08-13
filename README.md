# Touch MTC — Productivity Monitor

Internal AI-assisted employee productivity monitoring tool. Single-node pilot (1 Windows PC),
config-driven, rule-based scoring engine — built in-house, no external AI APIs.

## Structure

```
touch-mtc-monitor/
├── agent/       # Windows background tracking agent (Python)
├── backend/     # FastAPI backend — ingestion, config, scoring, reports
├── dashboard/   # React + TypeScript admin dashboard
└── docs/        # API contract, schema notes, planning docs
```

## Getting started

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Agent
```bash
cd agent
python -m venv .venv
.venv\Scripts\activate       # Windows only — agent is Windows-only by design
pip install -r requirements.txt
python main.py
```

### Dashboard
```bash
cd dashboard
npm install
npm run dev
```

## Branch strategy

- `main` — always working, protected
- `feature/<short-description>` — one branch per task, e.g. `feature/idle-detection`
- Open a PR into `main`, one review from the other person before merging
- Small, frequent commits > big infrequent ones — easier to review and to unblock each other

## Conventions

- Python: `black` + `ruff`
- TypeScript: `eslint` + `prettier`
- Commit messages: `<area>: short description` e.g. `agent: add idle time detection`

## Data & privacy note

No real employee activity data, screenshots, or generated reports should ever be committed —
see `.gitignore`. Use `/backend/data/` and `/agent/data/` locally only.

## Roadmap (post-pilot)

- Multi-device deployment (swap SQLite → Postgres, config already supports this via SQLAlchemy)
- Unsupervised anomaly detection once enough historical data exists per employee
- Full browser history tracking (currently active-tab-title only)
