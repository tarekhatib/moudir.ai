# Moudir.ai (مدير)

Moudir.ai is an employee productivity intelligence platform designed for engineering and business managers. It aggregates endpoint activity telemetry, computes role-aware productivity scores, and provides visual reporting dashboards and PDF summaries.

---

## Architecture & Directory Layout

```
Moudir/
├── archive/
│   ├── backend/             # FastAPI backend service & SQLite persistence
│   │   ├── app/             # Application source (main.py, models.py, database.py)
│   │   ├── data/            # Local SQLite database storage (moudir.db)
│   │   ├── docs/reports/    # Generated PDF export artifacts
│   │   ├── tests/           # Automated pytest test suite
│   │   ├── requirements.txt # Python dependencies
│   │   └── .env.example     # Backend environment variable template
│   └── docs/                # Project & API technical documentation
│       ├── API.md           # REST API reference and contracts
│       ├── SCORING.md       # Productivity scoring algorithm & weights
│       ├── PRIVACY.md       # Data collection, privacy model & exclusions
│       ├── DEMO-RUNBOOK.md  # End-to-end local demo runbook
│       └── KNOWN-ISSUES.md  # Pilot limitations and security considerations
├── dashboard/               # Frontend manager web dashboard (React + TS + Vite)
│   ├── src/                 # Dashboard UI source code and API client
│   ├── package.json         # Node.js dependencies and scripts
│   └── index.html           # Web entry point
└── agent/                   # Background activity capture agent (separate system)
```

> **Note on Backend Location:** The active backend service resides in `archive/backend/`. All backend operations, tests, and configurations run from this directory.

---

## Prerequisites

- **Python**: 3.11+ (Python 3.13 recommended)
- **Node.js**: 18+ (Node 20+ recommended) and `npm`
- **Operating System**: macOS or Linux (Windows supported with POSIX shell tools)

---

## Environment Setup

### 1. Backend Environment

In `archive/backend/`:
```bash
cp archive/backend/.env.example archive/backend/.env
```

Default values in `.env`:
```env
AGENT_TOKEN=pilot_secret_agent_token_123
DATABASE_URL=sqlite:///./data/moudir.db
```

### 2. Dashboard Environment (Optional)

In `dashboard/`:
If running on non-default ports, create `dashboard/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## Local Startup Instructions

### 1. Start the Backend Service

1. Navigate to the backend directory and set up a Python virtual environment:
   ```bash
   cd archive/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the FastAPI server with Uvicorn:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - API Base URL: `http://localhost:8000`
   - Interactive OpenAPI Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

### 2. Start the Manager Dashboard

1. In a new terminal window, navigate to `dashboard/`:
   ```bash
   cd dashboard
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - Dashboard UI: `http://localhost:5173`

---

## Running Tests & Builds

### Backend Test Suite (Pytest)

Run all unit and integration tests from `archive/backend/`:
```bash
cd archive/backend
source .venv/bin/activate
pytest tests/ -v
```

### Dashboard Production Build

Verify TypeScript compilation and frontend bundle build:
```bash
cd dashboard
npm run build
```

---

## Quick Demo Flow

1. **Start Services**: Launch the backend on port 8000 and dashboard on port 5173 as described above.
2. **Open Dashboard**: Open `http://localhost:5173` in your browser. Ensure the top bar displays `Backend: ok`.
3. **Add Employee**:
   - Click **Add employee** in the left sidebar.
   - Enter name (e.g. `Jane Doe`), role (`Lead Engineer`), and email (`jane.doe@example.com`).
   - Click **Save employee**.
4. **Ingest Activity Events**:
   Send sample telemetry events for Jane Doe (employee ID `1`):
   ```bash
   curl -X POST http://localhost:8000/ingest \
     -H "Content-Type: application/json" \
     -H "X-Agent-Token: pilot_secret_agent_token_123" \
     -d '{
       "events": [
         {"employee_id": 1, "event_type": "login", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "detail": {}},
         {"employee_id": 1, "event_type": "app_focus", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "detail": {"app_name": "VS Code", "window_title": "app.py"}},
         {"employee_id": 1, "event_type": "browser_tab", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "detail": {"tab_title": "GitHub Pull Request"}},
         {"employee_id": 1, "event_type": "idle_start", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "detail": {}}
       ]
     }'
   ```
5. **View Reports**: Switch between `daily`, `weekly`, and `monthly` period views in the dashboard to see updated scores, productive hours, and activity event distributions.
6. **Export PDF**: Click **Download PDF** to export and view the generated PDF report.
