# Moudir.ai Known Issues & Pilot Limitations

This document tracks identified constraints, architectural limitations, and security considerations in the current Moudir.ai pilot release.

---

## 1. Authentication & Access Control

- **Unauthenticated Dashboard & Management API**:
  - The pilot API endpoints (`/employees`, `/config`, `/reports`) do not currently enforce authentication, session cookies, or JWT verification.
  - Anyone with network access to the backend host can view employee records and modify configurations.
  - **Security Mandate**: This API is designed strictly for local demonstration and isolated network testing. It must **not** be deployed to public internet environments or exposed directly to end-user employees without introducing an authentication gateway and RBAC layer.

- **ID-Only Access**:
  - Reports and configs are addressed by incremental integer employee IDs (`/reports/{employee_id}`). In production, employee-facing access requires scoped credentials, tenant isolation, and hashed identifiers.

---

## 2. Telemetry & Scoring Heuristics

- **Heuristic-Only Productivity Signals**:
  - "Productive hours" and "Productivity scores" are linear heuristics derived from event frequency (`app_focus`, `browser_tab`, `idle_start`, `login`).
  - They do not account for passive work (e.g. paper review, phone calls, whiteboard meetings) and are not verified timesheets.
  - Scores should be treated as high-level indicators rather than definitive performance ratings.

- **Fixed Time Bucketing**:
  - Daily, weekly, and monthly calculations use UTC midnight boundaries. Shifts spanning midnight or cross-timezone teams may require timezone-aware bucketing in future iterations.

---

## 3. Storage & Concurrency

- **SQLite Single-Writer Concurrency**:
  - SQLite is used for lightweight zero-dependency local pilot setup. Under high-frequency concurrent telemetry ingestion from hundreds of client agents, database lock contention (`database is locked`) may occur.
  - Migration to PostgreSQL or a distributed time-series store is recommended for production scale.

---

## 4. PDF Generation Dependencies

- **System Rendering Libraries**:
  - WeasyPrint requires native system libraries (Cairo, Pango, GDK-Pixbuf). If these libraries are missing from the host environment, the backend falls back to ReportLab.
  - If both WeasyPrint and ReportLab fail to load, the PDF export endpoint returns `500 Internal Server Error`.

---

## 5. Desktop Agent & Platform Boundaries

- **Agent Scope & Desktop Platforms**:
  - Windows-specific telemetry hooks, system service daemons, and agent packaging reside in `agent/` and are maintained as a separate subsystem.
  - macOS and Linux background agent setups are owned independently from this backend and dashboard repository scope.
