"""
Moudir.ai — Windows Tracking Agent.

Owner: Carla (now TK, building both tracks)
Runs on the monitored PC, collects activity data locally, buffers it,
and syncs the backend ingestion endpoint on an interval.

Day 3-7 scope:
  - Login/logout events
  - Active window/app tracking
  - Idle detection
  - Local SQLite buffering
  - Backend sync
  - Browser tab capture
  - Outlook activity capture

Configure with BACKEND_URL and AGENT_TOKEN (generated per employee in the dashboard).
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

if sys.platform == "win32":
    import ctypes
    import psutil
    import win32api
    import win32gui
    import win32process

    WINDOWS_AVAILABLE = True
else:
    WINDOWS_AVAILABLE = False
    print("⚠️  Windows APIs not available (OK for Mac prototyping)")

    class _MissingWindowsModule:
        def __getattr__(self, name):
            raise RuntimeError("Windows-only module used outside Windows runtime")

    ctypes = _MissingWindowsModule()
    psutil = _MissingWindowsModule()
    win32api = _MissingWindowsModule()
    win32gui = _MissingWindowsModule()
    win32process = _MissingWindowsModule()

try:
    import requests
except ImportError:  # pragma: no cover - only needed when not installed in the active env
    requests = None

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AGENT_TOKEN = os.getenv("AGENT_TOKEN")
SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
POLL_INTERVAL_SECONDS = 2
IDLE_THRESHOLD_SECONDS = 60
SYNC_BATCH_SIZE = 500

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DB_PATH = BASE_DIR / "data" / "agent_queue.db"
QUEUE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_queue_db():
    connection = sqlite3.connect(QUEUE_DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    connection.close()


def log_event(event_type: str, detail: dict = None) -> dict:
    """Create and buffer an event."""
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detail": detail or {},
    }
    connection = sqlite3.connect(QUEUE_DB_PATH)
    connection.execute(
        "INSERT INTO queue (payload, created_at) VALUES (?, ?)",
        (json.dumps(event), datetime.now(timezone.utc).isoformat()),
    )
    connection.commit()
    connection.close()

    print(f"[{event['timestamp']}] Event: {event_type} — {event.get('detail', {})}")
    return event


def get_active_window():
    """Return the currently focused app name and window title."""
    if not WINDOWS_AVAILABLE:
        return ("finder", "Macintosh HD")

    assert win32gui is not None
    assert win32process is not None
    assert psutil is not None

    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            app_name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            app_name = "unknown"

        return app_name.lower(), window_title
    except Exception as e:
        print(f"Error getting active window: {e}")
        return None, None


def get_idle_seconds():
    """Return user idle duration in seconds for Windows-only use."""
    if not WINDOWS_AVAILABLE:
        return 0.0

    assert ctypes is not None
    assert win32api is not None

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        idle_ms = win32api.GetTickCount() - lii.dwTime
        return max(0.0, idle_ms / 1000.0)
    return 0.0


def maybe_emit_browser_event(app_name: str, window_title: str):
    """Emit a browser_tab event when the active app is a browser."""
    browser_names = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"}
    if app_name in browser_names and window_title:
        log_event("browser_tab", {"tab_title": window_title})


def maybe_emit_outlook_event(app_name: str):
    """Emit Outlook activity when Outlook is active."""
    if app_name and "outlook" in app_name:
        log_event("outlook_activity", {"activity_type": "window_focused"})


def sync_buffer_to_backend():
    """Send queued events to the backend in batches, deleting each batch once it's accepted.

    The agent token identifies the employee, so events carry no employee ID.
    """
    if requests is None:
        print("Sync skipped: requests is not installed in the active environment.")
        return
    if not AGENT_TOKEN:
        print("Sync skipped: AGENT_TOKEN is not set. Generate one in the dashboard.")
        return

    total = 0
    while True:
        connection = sqlite3.connect(QUEUE_DB_PATH)
        rows = connection.execute(
            "SELECT id, payload FROM queue ORDER BY id ASC LIMIT ?", (SYNC_BATCH_SIZE,)
        ).fetchall()
        connection.close()
        if not rows:
            break

        try:
            response = requests.post(
                f"{BACKEND_URL}/ingest",
                json={"events": [json.loads(payload) for _, payload in rows]},
                headers={"X-Agent-Token": AGENT_TOKEN},
                timeout=10,
            )
        except Exception as exc:
            print(f"Sync error: {exc}")
            break

        if response.status_code == 401:
            print("Sync failed: the agent token was rejected. Generate a new one in the dashboard.")
            break
        if response.status_code != 200:
            print(f"Sync failed: {response.status_code} — {response.text}")
            break

        # Only delete what was sent; events logged during the upload stay queued.
        connection = sqlite3.connect(QUEUE_DB_PATH)
        connection.execute("DELETE FROM queue WHERE id <= ?", (rows[-1][0],))
        connection.commit()
        connection.close()
        total += len(rows)

    if total:
        print(f"Synced {total} event(s) to backend.")


def main_loop():
    """Log the session start, poll active windows, and synchronize queued events."""
    init_queue_db()
    print(f"\n{'='*60}")
    print("Moudir.ai Agent Starting")
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Polling interval: {POLL_INTERVAL_SECONDS}s")
    print(f"  Sync interval: {SYNC_INTERVAL_SECONDS}s")
    print(f"{'='*60}\n")

    last_sync = time.time()
    last_app = None
    last_title = None
    idle_start_ts = None
    log_event("login", {})

    try:
        while True:
            app_name, window_title = get_active_window()
            if app_name and (app_name != last_app or window_title != last_title):
                log_event(
                    "app_focus",
                    {"app_name": app_name, "window_title": window_title or ""},
                )
                maybe_emit_browser_event(app_name, window_title)
                maybe_emit_outlook_event(app_name)
                last_app = app_name
                last_title = window_title

            if WINDOWS_AVAILABLE:
                idle_seconds = get_idle_seconds()
                if idle_seconds >= IDLE_THRESHOLD_SECONDS and idle_start_ts is None:
                    log_event("idle_start", {})
                    idle_start_ts = datetime.now(timezone.utc)
                elif idle_seconds < IDLE_THRESHOLD_SECONDS and idle_start_ts is not None:
                    duration_seconds = int(
                        (datetime.now(timezone.utc) - idle_start_ts).total_seconds()
                    )
                    log_event("idle_end", {"duration_seconds": duration_seconds})
                    idle_start_ts = None

            if time.time() - last_sync >= SYNC_INTERVAL_SECONDS:
                sync_buffer_to_backend()
                last_sync = time.time()

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n\nAgent shutting down...")
        log_event("logout", {})
        sync_buffer_to_backend()
        sys.exit(0)


if __name__ == "__main__":
    main_loop()
