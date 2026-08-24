# Moudir Project 48-Hour Execution Plan

## Goal

Ship a focused Day 12-ready pilot with two workstreams only:

- Dashboard ownership: Tarek
- Agentic ownership: Carla

## Scope Lock (No New Features)

- Keep and polish only `dashboard/` and `agent/`.
- No backend rewrites in this 48-hour window.
- No schema or architecture expansion.

## Team Split

- Tarek (Dashboard): UX flow, employee profile management, report rendering, demo polish.
- Carla (Agentic): event capture stability, local buffering, sync reliability, runbook for Windows setup.

## 48-Hour Timeline

### Block 1 (Hour 0-6): Stabilize

- Tarek:
  - Verify dashboard loads without runtime errors.
  - Remove/disable broken flows and dead buttons.
  - Add clear empty/error states.
- Carla:
  - Verify agent starts on Windows and logs events locally.
  - Confirm AGENT_TOKEN + backend URL alignment.
  - Validate queue file is created and events are buffered.

Exit criteria:

- Dashboard boots cleanly.
- Agent runs for 15+ minutes without crash.

### Block 2 (Hour 6-16): Integration Reliability

- Tarek:
  - Validate employee list and profile edit UX.
  - Verify report period switching (daily/weekly/monthly).
  - Ensure PDF button behavior is clear (success/failure feedback).
- Carla:
  - Validate sync loop retries and backoff behavior.
  - Confirm event payload consistency for all tracked activity types.
  - Test offline -> online recovery and flush.

Exit criteria:

- End-to-end report fetch works.
- Agent can recover after temporary network failure.

### Block 3 (Hour 16-28): Acceptance Tests

- Tarek + Carla pair-test:
  - Test Case A: Fresh start + one employee report generation.
  - Test Case B: Duplicate employee input handling.
  - Test Case C: Agent run for 30 minutes then report output check.
  - Test Case D: PDF export and file validity check.

Exit criteria:

- All 4 test cases pass.
- No unhandled 500 errors in expected user flows.

### Block 4 (Hour 28-38): Fix Window

- Prioritize defects by severity:
  - P0: crash, data loss, auth/token mismatch.
  - P1: incorrect report output, broken core flow.
  - P2: UX polish and messaging.
- Apply only high-confidence fixes.

Exit criteria:

- Zero P0.
- P1 reduced to acceptable demo risk.

### Block 5 (Hour 38-44): Demo Preparation

- Tarek:
  - Final dashboard walkthrough script.
  - Final screenshots for core flows.
- Carla:
  - Agent startup and sync runbook (copy-paste commands).
  - Known issues list + mitigations.

Exit criteria:

- Demo can be run by either teammate from clean machine state.

### Block 6 (Hour 44-48): Release Handoff

- Freeze changes.
- Final smoke test:
  - health endpoint
  - employees list/create/update
  - report fetch
  - PDF export
- Tag and push final checkpoint.

Exit criteria:

- Repo ready for submission/demo.
- Clear ownership notes and rollback notes documented.

## Daily Command Checklist

- Backend start (if needed):
  - `cd backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Port conflict resolution:
  - `lsof -nP -iTCP:8000 -sTCP:LISTEN`
  - `kill -9 <ACTUAL_PID>`
- Dashboard:
  - `cd dashboard && npm install && npm run dev`
- Agent:
  - `cd agent && pip install -r requirements.txt && python main.py`

## Risks and Controls

- Risk: Duplicate employee email causes 500.
  - Control: handle as conflict response and show user-friendly error.
- Risk: stale process on port 8000.
  - Control: enforce single backend terminal policy.
- Risk: token mismatch between machines.
  - Control: one shared AGENT_TOKEN source of truth before every test.

## Done Definition (Final)

- Dashboard and agentic flows are stable.
- Core acceptance tests pass.
- Known issues are documented with workaround.
- Demo script and runbook are complete.
