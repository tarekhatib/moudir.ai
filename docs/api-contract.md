## Agent → Backend

### POST /ingest

Headers: `X-Agent-Token: <shared secret from .env>`

Payload (batched events):

```json
{
  "events": [
    {
      "employee_id": 1,
      "event_type": "app_focus",
      "timestamp": "2026-08-18T14:32:00Z",
      "detail": {
        "app_name": "VS Code",
        "window_title": "models.py — moudir-ai"
      }
    }
  ]
}
```

`event_type` values (fixed list):

- `login`
- `logout`
- `app_focus` — detail: `{app_name, window_title}`
- `idle_start` — detail: `{}`
- `idle_end` — detail: `{duration_seconds}`
- `browser_tab` — detail: `{tab_title}` (no full URL, per scope)
- `outlook_activity` — detail: `{activity_type}` (e.g. email_sent, meeting_joined)

Agent buffers locally, then syncs on an interval by sending a batch in the format above.

## Dashboard → Backend

### GET /config/{employee_id}

### POST /config/{employee_id}

Payload:

```json
{
  "job_description": "string",
  "role_tag": "string",
  "software_weights": {"vs code": "high", "facebook": "low"},
  "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
  "schedule": {"mon": [["09:00","13:00"],["14:00","18:00"]], "tue": [...]},
  "min_productive_hours": 6,
  "max_idle_minutes": 60
}
```

### GET /reports/{employee_id}?period=daily|weekly|monthly

### GET /reports/{employee_id}/pdf?period=daily|weekly|monthly

## Auth

Shared token via `X-Agent-Token` header, sourced from `.env` on both sides. Non-negotiable even at pilot stage. Dashboard admin auth: TBD Day 9 (not needed for Days 3–5 backend/agent work).
