# Moudir.ai Tracking Agent

The agent is a silent Windows background process that records activity events for the
pilot employee. Day 3 can be prototyped on macOS with the fallback in `main.py`; the
real active-window tracking requires Windows and `pywin32`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` manually with `BACKEND_URL`, `AGENT_TOKEN`, `EMPLOYEE_ID`, and
`SYNC_INTERVAL_SECONDS` before starting the agent. Keep `.env` private.

```bat
python main.py
```

## Current scope

- Day 3: login/logout events and active-window tracking with an in-memory buffer.
- Day 4: idle detection and local SQLite buffering.
- Day 5: backend synchronization and retry handling.
- Later: Outlook activity, browser tab titles, and crash recovery.
