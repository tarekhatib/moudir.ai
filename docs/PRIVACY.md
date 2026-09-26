# Moudir.ai Privacy & Data Protection Model

This document outlines the telemetry data collected by Moudir.ai, explicit data exclusions, and how access and retention work.

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
| `outlook_activity` | `{"activity_type": string}` | High-level collaboration signal (currently `window_focused` when Outlook is in the foreground) |

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

## Access & Retention Model

1. **Who can see the data**:
   - Each company is a separate organization. Managers sign in with email and password and can
     only see employees and activity in their own organization; requests for another
     organization's employees return `404`.
   - Passwords are hashed with Argon2. Sessions are random tokens in `HttpOnly` cookies, stored
     server-side only as hashes, and are revoked on sign-out or password change.

2. **How the agent authenticates**:
   - Every employee has their own agent token, issued from the dashboard and stored only as a
     hash. A token can only add events for its own employee, and can be rotated or revoked at
     any time.
   - Events are sent over HTTPS in production.

3. **Data minimisation on ingest**:
   - The backend accepts only the event types listed above, keeps at most 10 scalar `detail`
     fields per event and truncates text to 500 characters.

4. **Storage & retention**:
   - Data is stored in PostgreSQL in production.
   - Activity is kept until the employee or organization is deleted. Deleting an employee in the
     dashboard permanently removes their settings and all their activity. There is no automatic
     retention limit yet (see [KNOWN-ISSUES.md](KNOWN-ISSUES.md)).

---

## Disclaimer

> [!NOTE]
> The measures described here are technical design choices. They do **not** constitute legal certification or compliance with GDPR, CCPA, HIPAA, SOC 2 or regional workplace-monitoring laws. Employers using Moudir are responsible for informing employees and having a lawful basis for monitoring in their jurisdiction.
