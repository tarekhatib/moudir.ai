"""
Moudir.ai — Windows Tracking Agent.

Owner: Carla (now TK, building both tracks)
Runs on the monitored PC. Collects activity data locally, buffers it,
and syncs to the backend ingestion endpoint on an interval.

Day 3 scope:
  - Login/logout events (agent start/stop)
  - Active window/app tracking via polling
  - In-memory event buffer
  - Console logging for verification

Day 4+: idle detection, local SQLite buffering, backend sync
"""

import os
import json
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

try:
    import win32gui
    import win32process
    import psutil

    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("⚠️  Windows APIs not available (OK for Mac prototyping, will fail on Day 4+)")

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AGENT_TOKEN = os.getenv("AGENT_TOKEN")
EMPLOYEE_ID = int(os.getenv("EMPLOYEE_ID", "1"))
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
POLL_INTERVAL_SECONDS = 2

event_buffer = []


def log_event(event_type: str, detail: dict = None) -> dict:
    """Create and buffer an event."""
    event = {
        "employee_id": EMPLOYEE_ID,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detail": detail or {},
    }
    event_buffer.append(event)
    print(f"[{event['timestamp']}] Event: {event_type} — {event.get('detail', {})}")
    return event


def get_active_window():
    """Return the currently focused app name and window title."""
    if not WINDOWS_AVAILABLE:
        return ("finder", "Macintosh HD")

    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            app_name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            app_name = "unknown"

        return app_name, window_title
    except Exception as e:
        print(f"Error getting active window: {e}")
        return None, None


def poll_active_window():
    """Emit app_focus events when the active window changes."""
    last_app = None
    last_title = None

    print(f"Starting active window polling (interval: {POLL_INTERVAL_SECONDS}s)...")

    while True:
        app_name, window_title = get_active_window()

        if app_name and (app_name != last_app or window_title != last_title):
            log_event(
                "app_focus",
                {"app_name": app_name, "window_title": window_title or ""},
            )
            last_app = app_name
            last_title = window_title

        time.sleep(POLL_INTERVAL_SECONDS)


def main_loop():
    """Log the session start, poll active windows, and log shutdown."""
    print(f"\n{'='*60}")
    print("Moudir.ai Agent Starting")
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Employee ID: {EMPLOYEE_ID}")
    print(f"  Polling interval: {POLL_INTERVAL_SECONDS}s")
    print(f"  Sync interval: {SYNC_INTERVAL_SECONDS}s")
    print(f"{'='*60}\n")

    log_event("login")

    try:
        poll_active_window()
    except KeyboardInterrupt:
        print("\n\nAgent shutting down...")
        log_event("logout")

        print(f"\n{'='*60}")
        print(f"Buffered events ({len(event_buffer)} total):")
        print(f"{'='*60}")
        for i, event in enumerate(event_buffer, 1):
            print(f"{i}. {json.dumps(event, indent=2)}")
        print(f"{'='*60}\n")

        sys.exit(0)


if __name__ == "__main__":
    main_loop()
