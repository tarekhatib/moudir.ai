# API Contract (draft — finalize Day 2)

Fill this in together before splitting into Days 3-5. Keep it short — this is
the thing that lets Carla and [You] build in parallel without guessing at each
other's payloads.

## Agent → Backend

### POST /ingest
Payload shape: TBD (event_type, timestamp, employee_id, detail)

## Dashboard → Backend

### GET /config/{employee_id}
### POST /config/{employee_id}
### GET /reports/{employee_id}?period=daily|weekly|monthly
### GET /reports/{employee_id}/pdf?period=...

## Auth
TBD — token-based for agent, session/token for dashboard admin
