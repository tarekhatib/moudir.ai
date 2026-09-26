# Moudir.ai API Reference

The FastAPI backend in [`backend/`](../backend). In production it is served under
`https://<your-domain>/api`; in development it runs on `http://localhost:8000` and the
dashboard reaches it through the Vite proxy at `/api`. Paths below are relative to that base.

- JSON in and out (except the PDF export).
- Errors: `{"detail": "message"}`, or for validation errors (`422`) `{"detail": [{"msg": …}, …]}`.
- All timestamps are UTC. Report periods and trend days use UTC day boundaries.
- Interactive docs are at `/docs` in development (hidden in production).

## Authentication

| Caller | How | Scope |
| :--- | :--- | :--- |
| **Dashboard (managers)** | `moudir_session` cookie set by `/auth/signup` or `/auth/login` (`HttpOnly`, `SameSite=Lax`, `Secure` in production) | Everything in the manager's organization |
| **Desktop agent** | `X-Agent-Token: <token>` or `Authorization: Bearer <token>` | Writing events for the one employee the token was issued to |

Without a valid session, dashboard endpoints return `401`. Employees and users of other
organizations always return `404`, never `403`, so IDs from other tenants are not revealed.

## Health

`GET /health` → `200 {"status": "ok"}` when the database is reachable. No auth.

## Accounts

| Method & path | Body | Result |
| :--- | :--- | :--- |
| `POST /auth/signup` | `{organization_name, name, email, password}` (password ≥ 10 chars) | `201` + session cookie + `Me`. Creates an organization with the caller as **owner**. `409` if the email has an account, `403` if sign-up is disabled |
| `POST /auth/login` | `{email, password}` | `200` + session cookie + `Me`. `401` on wrong credentials, `429` after too many failures |
| `POST /auth/logout` | — | `204`; the session is deleted server-side |
| `GET /auth/me` | — | `Me` |
| `POST /auth/password` | `{current_password, new_password}` | `204`; signs out the user's other sessions. `400` if the current password is wrong |

`Me` is `{"user": {"id", "name", "email", "role": "owner" | "manager"}, "organization": {"id", "name"}}`.

### Manager accounts

| Method & path | Who | Result |
| :--- | :--- | :--- |
| `GET /organization/users` | any manager | List of users in the organization |
| `POST /organization/users` | owner | Body `{name, email, password}` → `201` new manager. `409` if the email is taken |
| `DELETE /organization/users/{id}` | owner | `204`. `400` for your own account |

## Employees

Employee object:

```json
{
  "id": 1,
  "name": "Jane Doe",
  "role": "Software Engineer",
  "email": "jane.doe@example.com",
  "job_description": "Full stack web development",
  "role_tag": "engineering",
  "agent_token_created_at": "2026-09-26T08:30:00Z"
}
```

| Method & path | Result |
| :--- | :--- |
| `GET /employees` | Employees in your organization, by ID |
| `POST /employees` | Body `{name, role?, email?, job_description?, role_tag?}` → `201`. Strings are trimmed; blanks become `null`; emails are lower-cased. `409` if the email is already used in your organization |
| `GET /employees/{id}` | One employee |
| `PUT /employees/{id}` | Same body as create |
| `DELETE /employees/{id}` | `204`; also deletes their settings and all activity |
| `POST /employees/{id}/agent-token` | `{"employee_id", "agent_token": "mdr_…", "created_at"}`. **The token is only returned here**; only its hash is stored. Issuing a new token invalidates the previous one |
| `DELETE /employees/{id}/agent-token` | `204`; the agent can no longer send events |

## Scoring settings

`GET /config/{employee_id}` and `POST /config/{employee_id}` read and replace:

```json
{
  "employee_id": 1,
  "job_description": "Full stack web development",
  "role_tag": "engineering",
  "software_weights": {"VS Code": "high", "YouTube": "low"},
  "category_weights": {"app_usage": 0.5, "browser": 0.2, "punctuality": 0.2, "idle": 0.1},
  "schedule": {"mon": [["09:00", "13:00"], ["14:00", "18:00"]]},
  "min_productive_hours": 6.0,
  "max_idle_minutes": 60
}
```

Validation (`422` otherwise): software weights are `high|medium|low` with unique names;
category weights use only the four keys shown, each 0–1, summing to 1; schedule days are
`mon`–`sun` with `HH:MM` ranges that don't overlap; `min_productive_hours` 0–24;
`max_idle_minutes` 0–1440.

## Reports

`period` is `daily`, `weekly` (Monday–Sunday) or `monthly`, for the current UTC day/week/month.

### `GET /reports/{employee_id}?period=daily`

```json
{
  "employee_id": 1,
  "period": "weekly",
  "period_start": "2026-09-21",
  "period_end": "2026-09-27",
  "average_score": 0.86,
  "days_active": 5,
  "total_productive_hours": 27.4,
  "total_idle_minutes": 90,
  "event_summary": {"app_focus": 274, "browser_tab": 81, "idle_start": 6, "login": 5, "outlook_activity": 0},
  "app_weights": {"VS Code": "high"},
  "top_apps": [{"app_name": "VS Code", "focus_events": 150}]
}
```

`average_score` is the mean of the daily scores on days with activity, or `null` when there was
no activity in the period. See [SCORING.md](SCORING.md). `top_apps` lists up to 8 apps by focus events.

### `GET /reports/{employee_id}/trend?days=14`

Per-day points for the last `days` (1–90) days, oldest first, ending today. Days without events
have `has_activity: false` and `average_score: null`.

### `GET /reports/{employee_id}/pdf?period=daily`

The report as a PDF attachment (`report_{id}_{period}.pdf`).

### `GET /team/summary?period=daily`

The report for every employee in your organization, each with `id`, `name` and `role` added.

## Agent ingestion

### `POST /ingest`

Headers: `X-Agent-Token: mdr_…`

```json
{
  "events": [
    {"event_type": "app_focus", "timestamp": "2026-09-26T10:30:00Z", "detail": {"app_name": "VS Code", "window_title": "main.py"}},
    {"event_type": "browser_tab", "timestamp": "2026-09-26T10:35:00+03:00", "detail": {"tab_title": "FastAPI docs"}}
  ]
}
```

Response: `{"status": "success", "events_stored": 2, "events_rejected": 0}`

- The token decides which employee the events belong to. `employee_id` on an event is optional;
  if present it must match, or the event is rejected.
- `event_type` is one of `login`, `logout`, `app_focus`, `idle_start`, `idle_end`,
  `browser_tab`, `outlook_activity`.
- Timestamps may carry any UTC offset and are stored in UTC. Events more than an hour in the
  future are rejected.
- Invalid events are **skipped and counted** in `events_rejected` instead of failing the batch.
  `detail` keeps at most 10 scalar fields; strings are cut to 500 characters.
- At most `MAX_INGEST_EVENTS` (default 1000) events per request, otherwise `413`.
- `401` if the token is missing, wrong, or revoked.
