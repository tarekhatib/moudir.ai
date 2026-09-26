# Moudir.ai Tracking Agent

The agent is a silent Windows background process that records activity events for one
employee and sends them to the Moudir backend. It can be prototyped on macOS with the
fallback in `main.py`; real active-window and idle tracking requires Windows and `pywin32`.

## Setup

1. In the dashboard, open **Employees → (employee) → Desktop agent** and click
   **Generate token**. The token is shown once; copy it.
2. On the employee's PC:

   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```

3. Edit `.env`:
   - `BACKEND_URL` — your Moudir URL followed by `/api`, e.g. `https://moudir.example.com/api`
     (or `http://localhost:8000` when running the backend directly in development).
   - `AGENT_TOKEN` — the token from step 1. It identifies the employee; keep it private.

4. Run it:

   ```bat
   python main.py
   ```

Generating a new token in the dashboard immediately invalidates the old one.

## Behaviour

- Logs login/logout, focused-app changes, browser tab titles (not URLs), Outlook focus,
  and idle periods longer than 60 seconds.
- Events are queued in a local SQLite file (`data/agent_queue.db`) so nothing is lost while
  offline, and synced every `SYNC_INTERVAL_SECONDS` in batches of 500.
