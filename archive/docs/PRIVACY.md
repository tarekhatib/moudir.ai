# Moudir.ai Privacy & Data Protection Model

This document outlines the telemetry data collected by Moudir.ai, explicit data exclusions, and the privacy and retention model implemented during the pilot stage.

---

## Data Collection Scope

Moudir.ai operates on high-level activity telemetry rather than intrusive surveillance. The client agent collects only the following event types:

| Event Type | Detail Payload | Purpose |
| :--- | :--- | :--- |
| `login` | `{}` | Record session start for punctuality calculation |
| `logout` | `{}` | Record session termination |
| `app_focus` | `{"app_name": string, "window_title": string}` | Detect active foreground applications (e.g., IDE, terminal, office tools) |
| `browser_tab` | `{"tab_title": string}` | Measure web-based research and tool usage by page title |
| `idle_start` | `{}` | Mark beginning of user inactivity (no mouse/keyboard input) |
| `idle_end` | `{"duration_seconds": number}` | Record duration of user inactivity |
| `outlook_activity` | `{"activity_type": string}` | High-level collaboration events (e.g., `email_sent`, `meeting_joined`) |

---

## Explicit Data Exclusions

Per the Moudir.ai technical architecture and API contract, the following categories of data are **strictly excluded** from collection:

> [!IMPORTANT]
> - **No Full Browser URLs**: Only sanitized window/tab titles are captured (e.g., `"Pull Request #42 · GitHub"`). Full URLs, domains with path parameters, authentication tokens, or query strings are never collected or transmitted.
> - **No Keystroke Logging**: The agent does not record keystroke sequences, input text, or typing content.
> - **No Screen Recording / Screenshots**: No desktop video feeds, periodical screen grabs, or OCR of display pixels are taken.
> - **No Message / Email Content**: No email bodies, instant message conversations, attachments, or file contents are read.
> - **No Audio / Video Surveillance**: No microphone, camera, or peripheral recording capabilities exist.
> - **No Local File System Scraping**: The agent does not scan or upload user documents or file system directories.

---

## Access & Retention Model (Pilot Stage)

1. **Access Control**:
   - Telemetry ingestion (`POST /ingest`) requires a pre-shared secret token passed via `X-Agent-Token`.
   - The manager dashboard and backend REST API currently operate in an open pilot mode on `localhost` without individual user authentication or role-based access control (RBAC).
   - Endpoints are intended solely for local network evaluation and internal demonstration.

2. **Data Storage & Retention**:
   - Activity events and computed reports are persisted in the local SQLite database (`data/moudir.db`).
   - In the pilot implementation, events are retained indefinitely until the database file is manually reset or deleted.

---

## Pilot Disclaimer

> [!NOTE]
> Moudir.ai is currently a **pilot demonstration platform**. The documentation and privacy measures described herein reflect technical design choices of the pilot implementation and do **not** constitute formal legal certifications or compliance guarantees under GDPR, CCPA, HIPAA, SOC 2, or regional workplace monitoring laws.
