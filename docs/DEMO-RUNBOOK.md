# Moudir.ai Local Demo Runbook

A walkthrough of Moudir running on your own machine: sign in, look at a team with five weeks of
history, add an employee, send them activity as the agent would, and export a PDF.

You need Python 3.13, Node 22 and two terminals.

## 1. Start the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python scripts/seed_mock_data.py
uvicorn app.main:app --reload --port 8000
```

`seed_mock_data.py` creates the **Moudir Demo** company with nine employees and five weeks of
activity, and prints the sign-in details. Rerun it with `--reset` to regenerate the data or
`--remove` to delete the demo company. It never touches other companies and refuses to run with
`ENVIRONMENT=production`.

Check the API: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## 2. Start the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173 and sign in with `demo@demo.moudir.example` / `moudir-demo-password`.

## 3. Tour

1. **Team overview** — switch between daily, weekly and monthly. Sort by any column. Karim
   (support, often idle) scores lowest; Lina's monthly score is lower than her weekly one
   because she has been improving.
2. Click an employee for their **report**, 14-day trend and most-used apps.
3. **Settings** tab — change the app and category weights; the report updates when you save.
4. **Account** — as the owner, add a second manager, then sign in as them in a private window.
   They see the same employees but can't manage accounts.

## 4. Add an employee and send activity

1. **Employees → Add employee**, e.g. `Alex Rivers`, then **Create employee**.
2. Their score shows **No data** — nothing has been recorded yet.
3. **Desktop agent → Generate token** and copy the token.
4. Send some events as the agent would:

```bash
TOKEN=mdr_paste_the_token_here
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: $TOKEN" \
  -d '{"events": [
    {"event_type": "login", "timestamp": "'$NOW'"},
    {"event_type": "app_focus", "timestamp": "'$NOW'", "detail": {"app_name": "VS Code", "window_title": "app/main.py"}},
    {"event_type": "app_focus", "timestamp": "'$NOW'", "detail": {"app_name": "Terminal", "window_title": "pytest"}},
    {"event_type": "browser_tab", "timestamp": "'$NOW'", "detail": {"tab_title": "FastAPI docs"}},
    {"event_type": "idle_start", "timestamp": "'$NOW'"}
  ]}'
# {"status":"success","events_stored":5,"events_rejected":0}
```

5. Refresh the report. To run the real agent instead, see [agent/README.md](../agent/README.md)
   with `BACKEND_URL=http://localhost:8000`.

## 5. Export a PDF

On an employee's report, click **Download PDF**.

## Troubleshooting

- **"Can't connect to Moudir right now"** — the backend isn't running on port 8000. If you run it
  elsewhere, start the dashboard with `VITE_BACKEND_URL=http://localhost:8001 npm run dev`.
- **Agent gets `401`** — the token was regenerated or revoked; generate a new one.
- **Sign-in says "Too many sign-in attempts"** — wait 15 minutes or restart the backend.
- **Schema errors after pulling changes** — run `alembic upgrade head`.
