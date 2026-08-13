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
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SYNC_INTERVAL_SECONDS = 60


def collect_active_window():
    """TODO (Day 3): use pygetwindow / pywin32 to get active app + window title."""
    raise NotImplementedError


def collect_idle_time():
    """TODO (Day 4): use win32api.GetLastInputInfo() to compute idle duration."""
    raise NotImplementedError


def sync_to_backend(payload):
    """TODO (Day 5): POST buffered events to {BACKEND_URL}/ingest, handle retries."""
    raise NotImplementedError


def main_loop():
    print(f"Agent starting — syncing to {BACKEND_URL}")
    while True:
        # TODO: collect events, buffer locally, sync on interval
        time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    main_loop()
