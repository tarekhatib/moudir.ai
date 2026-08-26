# Moudir.ai Local Demo Runbook

This guide provides a step-by-step walkthrough for running an end-to-end local demonstration of Moudir.ai, from spinning up services to creating employee profiles, simulating activity telemetry, viewing dashboard analytics, and exporting PDF reports.

---

## 1. Prerequisites Checklist

- Python 3.11+ installed.
- Node.js 18+ and `npm` installed.
- Two terminal windows ready.

---

## 2. Step-by-Step Demo Procedure

### Step 1: Start the Backend Service

In **Terminal 1**:
```bash
# Navigate to the active backend directory
cd backend

# Create and activate virtual environment (if not already done)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ensure .env is present
cp .env.example .env

# Launch FastAPI server
uvicorn app.main:app --reload --port 8000
```

Verify backend is healthy:
```bash
curl http://localhost:8000/health
# Expected output: {"status": "ok"}
```

---

### Step 2: Start the Manager Dashboard

In **Terminal 2**:
```bash
# Navigate to the dashboard directory
cd dashboard

# Install npm dependencies
npm install

# Launch Vite dev server
npm run dev
```

Open your web browser and navigate to:
```
http://localhost:5173
```
Confirm the top navigation bar displays a green badge: `Backend: ok`.

---

### Step 3: Create an Employee Profile

1. In the dashboard left panel (**Employees**), click the **Add employee** button.
2. In the **Employee profile** form on the right, fill in:
   - **Full name**: `Alex Rivers`
   - **Role**: `Lead Software Engineer`
   - **Email**: `alex.rivers@example.com`
   - **Role tag**: `engineering`
   - **Job description**: `Architecture design and full-stack backend development`
3. Click **Save employee**.
4. Alex Rivers will appear in the employee list with an assigned ID (e.g., `#1`).

---

### Step 4: Ingest Activity Events

Simulate telemetry sent by the desktop agent for Alex Rivers (`employee_id: 1`):

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: pilot_secret_agent_token_123" \
  -d '{
    "events": [
      {
        "employee_id": 1,
        "event_type": "login",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "detail": {}
      },
      {
        "employee_id": 1,
        "event_type": "app_focus",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "detail": {"app_name": "VS Code", "window_title": "app/main.py"}
      },
      {
        "employee_id": 1,
        "event_type": "app_focus",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "detail": {"app_name": "Terminal", "window_title": "zsh — pytest"}
      },
      {
        "employee_id": 1,
        "event_type": "browser_tab",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "detail": {"tab_title": "FastAPI Dependency Injection Guide"}
      },
      {
        "employee_id": 1,
        "event_type": "idle_start",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "detail": {}
      }
    ]
  }'
```

Output:
```json
{"status": "success", "events_stored": 5}
```

---

### Step 5: View Real-Time Reports

1. Switch back to the dashboard at `http://localhost:5173`.
2. Click on **Alex Rivers** in the sidebar.
3. Toggle between **daily**, **weekly**, and **monthly** periods using the top selector.
4. Observe the dynamically updated metrics:
   - **Average score**: Computed weighted index based on active app focus, browser tabs, login status, and idle penalties.
   - **Productive hours**: Calculated focus hour estimates.
   - **Idle minutes**: Estimated idle duration.
   - **Event summary breakdown**: Counts for App focus, Browser tabs, Idle starts, and Logins.

---

### Step 6: Export & Verify PDF Report

1. Click the **Download PDF** button in the top-right corner of the dashboard.
2. A PDF named `report-1-daily.pdf` will download to your machine.
3. Open the PDF to inspect the generated layout, employee details, productivity metrics, and activity summary.

---

## 3. Troubleshooting

### Port Conflicts (8000 or 5173 occupied)
- **Backend**: If port 8000 is occupied, start Uvicorn on another port (e.g. 8001):
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```
  Set `VITE_API_URL=http://localhost:8001` in `dashboard/.env` and restart the dashboard.
- **Frontend**: If port 5173 is in use, Vite will automatically offer port 5174.

### Missing `AGENT_TOKEN` (401 Unauthorized)
- Ensure `backend/.env` exists and contains `AGENT_TOKEN=pilot_secret_agent_token_123`.
- Ensure requests to `POST /ingest` include the header `X-Agent-Token: pilot_secret_agent_token_123`.

### Backend Unreachable / CORS Issues
- Check that the backend is running and responds to `curl http://localhost:8000/health`.
- If running on a custom host or port, ensure CORS origins in `backend/app/main.py` include your dashboard URL.

### PDF Generator Unavailable (500 Error on PDF export)
- Ensure `weasyprint` or `reportlab` is installed in your backend Python environment:
  ```bash
  pip install reportlab weasyprint
  ```
- The backend automatically uses ReportLab if system WeasyPrint libraries (Cairo/Pango) are not present.
