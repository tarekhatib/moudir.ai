# Tracking Agent

Windows-only. Must be developed and tested on the Lenovo (or any Windows machine) —
`pywin32` and `pygetwindow` won't install on macOS/Linux.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## Transparency / consent

Per the open question from planning: decide whether this runs with a visible tray
icon/notification (recommended for consent/transparency) or fully silent, before
building the service wrapper on Day 8. This affects whether we need a small tray UI
component in addition to the background service.

## Notes

- Idle detection: `win32api.GetLastInputInfo()` gives milliseconds since last
  keyboard/mouse input — no actual keystrokes are captured or stored, matching
  the "activity level, not keylogging" approach from the original scoping.
- Outlook: `win32com.client.Dispatch("Outlook.Application")` — requires Outlook
  installed and the desktop (not just web) client running.
- Browser tracking: reading the active window title only for now (e.g. tab title
  in Chrome/Edge's title bar) — no browser extension, no full URL history. That's
  a possible post-pilot addition, not in scope for the 12 days.
