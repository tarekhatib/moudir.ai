"""
Touch MTC Productivity Monitor — Windows Tracking Agent.

Owner: Carla
Runs on the monitored PC. Collects activity data locally, buffers it,
and syncs to the backend ingestion endpoint on an interval.

Build order (see 12-day plan):
  Day 3 — login/logout events, active window/app tracking
  Day 4 — idle time detection, local SQLite buffering
  Day 5 — sync to backend over interval, basic error handling
  Day 6 — Outlook COM integration
  Day 7 — browser active-tab tracking
  Day 8 — crash recovery, retry-on-failed-sync, survive reboot
"""

import time
import os
from datetime import datetime, timezone

import psutil
import pygetwindow as gw
import requests
import win32api
import win32process
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AGENT_TOKEN = os.getenv("AGENT_TOKEN")
EMPLOYEE_ID = os.getenv("EMPLOYEE_ID", "1")
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))

POLL_INTERVAL_SECONDS = 2

_event_buffer = []


def collect_active_window():
    """Return {'app_name', 'window_title'} for the foreground window, or None."""
    window = gw.getActiveWindow()
    if window is None or not window.title:
        return None

    app_name = None
    try:
        _, pid = win32process.GetWindowThreadProcessId(window._hWnd)
        app_name = psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        pass

    return {"app_name": app_name, "window_title": window.title}


def collect_idle_time():
    """Milliseconds since the last keyboard/mouse input."""
    return win32api.GetTickCount() - win32api.GetLastInputInfo()


def record_event(event_type, detail=None):
    detail = detail or {}
    print(f"Event: {event_type} — {detail}")
    _event_buffer.append(
        {
            "employee_id": EMPLOYEE_ID,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": detail,
        }
    )


def sync_to_backend():
    """POST buffered events to {BACKEND_URL}/ingest. Keeps the buffer on failure so
    nothing is lost — it just gets retried on the next interval."""
    global _event_buffer
    if not _event_buffer:
        return

    headers = {"Authorization": f"Bearer {AGENT_TOKEN}"} if AGENT_TOKEN else {}
    try:
        response = requests.post(
            f"{BACKEND_URL}/ingest",
            json={"events": _event_buffer},
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        _event_buffer = []
    except requests.RequestException as exc:
        print(f"Sync failed, will retry next interval: {exc}")


def main_loop():
    print(f"Agent starting — syncing to {BACKEND_URL}")
    record_event("login")

    last_window = None
    last_sync = time.monotonic()

    try:
        while True:
            window = collect_active_window()
            if window is not None and window != last_window:
                record_event("app_focus", window)
                last_window = window

            if time.monotonic() - last_sync >= SYNC_INTERVAL_SECONDS:
                sync_to_backend()
                last_sync = time.monotonic()

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        record_event("logout")
        sync_to_backend()


if __name__ == "__main__":
    main_loop()
