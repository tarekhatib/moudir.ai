# Moudir.ai Backend API Reference

This document provides a comprehensive technical specification for the Moudir.ai REST API endpoints exposed by the FastAPI backend (`backend/`).

---

## Overview & Conventions

- **Base URL**: `http://localhost:8000` (configurable via `VITE_API_URL` on the frontend)
- **Data Format**: `application/json` (unless requesting binary media like PDFs)
- **Standard Error Format**:
  ```json
  {
    "detail": "Error description or validation issues"
  }
  ```

---

## Authentication & Authorization

| Context | Header | Description |
| :--- | :--- | :--- |
| **Agent Ingestion** | `X-Agent-Token: <token>` | Required on `POST /ingest`. Validated against `AGENT_TOKEN` environment variable. |
| **Dashboard API** | None (Pilot stage) | All employee, config, and reporting endpoints operate in open pilot mode without user auth. |

---

## Endpoint Specifications

### 1. Health Check

#### `GET /health`
Verifies backend connectivity and operational status.

- **Authentication**: None
- **Request Body**: None
- **Responses**:
  - `200 OK`:
    ```json
    {
      "status": "ok"
    }
    ```

---

### 2. Activity Ingestion

#### `POST /ingest`
Ingests a batch of activity events logged by the desktop agent.

- **Authentication**: `X-Agent-Token` header required.
- **Request Headers**:
  - `Content-Type: application/json`
  - `X-Agent-Token: <AGENT_TOKEN>`
- **Request Body**:
  ```json
  {
    "events": [
      {
        "employee_id": 1,
        "event_type": "app_focus",
        "timestamp": "2026-08-26T10:30:00Z",
        "detail": {
          "app_name": "VS Code",
          "window_title": "main.py"
        }
      },
      {
        "employee_id": 1,
        "event_type": "browser_tab",
        "timestamp": "2026-08-26T10:35:00Z",
        "detail": {
          "tab_title": "FastAPI Documentation"
        }
      }
    ]
  }
  ```
- **Supported `event_type` values**:
  - `login` — detail: `{}`
  - `logout` — detail: `{}`
  - `app_focus` — detail: `{"app_name": string, "window_title": string}`
  - `idle_start` — detail: `{}`
  - `idle_end` — detail: `{"duration_seconds": number}`
  - `browser_tab` — detail: `{"tab_title": string}` *(no full URLs)*
  - `outlook_activity` — detail: `{"activity_type": string}`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "status": "success",
      "events_stored": 2
    }
    ```
  - `401 Unauthorized`:
    ```json
    {
      "detail": "Invalid or missing X-Agent-Token"
    }
    ```
  - `422 Unprocessable Entity`: Validation failure on payload schema or event timestamp format.

---

### 3. Employee Management

#### `GET /employees`
Returns a list of all registered employees with their associated job descriptions and role tags.

- **Authentication**: None
- **Responses**:
  - `200 OK`:
    ```json
    [
      {
        "id": 1,
        "name": "Jane Doe",
        "role": "Software Engineer",
        "email": "jane.doe@example.com",
        "job_description": "Full stack web development",
        "role_tag": "engineering"
      }
    ]
    ```

---

#### `POST /employees`
Creates a new employee profile and initializes a default scoring configuration record.

- **Authentication**: None
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "role": "Software Engineer",
    "email": "jane.doe@example.com",
    "job_description": "Full stack web development",
    "role_tag": "engineering"
  }
  ```
  - `name` *(required, non-empty string)*: Stripped of leading/trailing whitespace.
  - `role`, `email`, `job_description`, `role_tag` *(optional)*: Whitespace trimmed; empty strings stored as `null`.
- **Responses**:
  - `200 OK`: Returns the created employee record with assigned `id`.
  - `409 Conflict`:
    ```json
    {
      "detail": "An employee with this email already exists"
    }
    ```
  - `422 Unprocessable Entity`: Empty or missing `name` field.

---

#### `GET /employees/{employee_id}`
Retrieves profile and config summary for a single employee.

- **Authentication**: None
- **Responses**:
  - `200 OK`:
    ```json
    {
      "id": 1,
      "name": "Jane Doe",
      "role": "Software Engineer",
      "email": "jane.doe@example.com",
      "job_description": "Full stack web development",
      "role_tag": "engineering"
    }
    ```
  - `404 Not Found`:
    ```json
    {
      "detail": "Employee not found"
    }
    ```

---

#### `PUT /employees/{employee_id}`
Updates an existing employee's profile and configuration fields.

- **Authentication**: None
- **Request Body**: Same schema as `POST /employees`.
- **Responses**:
  - `200 OK`: Returns the updated employee record.
  - `404 Not Found`: If `employee_id` does not exist.
  - `409 Conflict`: If the email is changed to an email already in use by another employee.
  - `422 Unprocessable Entity`: Invalid payload or empty `name`.

---

### 4. Configuration Management

#### `GET /config/{employee_id}`
Retrieves scoring parameters, software weights, category weights, and schedule for an employee.

- **Authentication**: None
- **Responses**:
  - `200 OK`:
    ```json
    {
      "employee_id": 1,
      "job_description": "Full stack web development",
      "role_tag": "engineering",
      "software_weights": {
        "VS Code": "high",
        "Slack": "medium"
      },
      "category_weights": {
        "app_usage": 0.4,
        "browser": 0.2,
        "punctuality": 0.2,
        "idle": 0.2
      },
      "schedule": {
        "mon": [["09:00", "13:00"], ["14:00", "18:00"]]
      },
      "min_productive_hours": 6.0,
      "max_idle_minutes": 60
    }
    ```
  - `404 Not Found`: If `employee_id` does not exist or config row is missing.

---

#### `POST /config/{employee_id}`
Updates scoring parameters, category weights, software weights, and schedule for an employee.

- **Authentication**: None
- **Request Body**:
  ```json
  {
    "job_description": "Full stack web development",
    "role_tag": "engineering",
    "software_weights": {
      "VS Code": "high",
      "YouTube": "low"
    },
    "category_weights": {
      "app_usage": 0.5,
      "browser": 0.2,
      "punctuality": 0.2,
      "idle": 0.1
    },
    "schedule": {
      "mon": [["09:00", "17:00"]]
    },
    "min_productive_hours": 7.0,
    "max_idle_minutes": 45
  }
  ```
- **Responses**:
  - `200 OK`: Returns the updated configuration object.
  - `404 Not Found`: If `employee_id` does not exist (prevents orphan config rows).
  - `422 Unprocessable Entity`: Validation failure on payload structure.

---

### 5. Reporting & Analytics

#### `GET /reports/{employee_id}`
Computes productivity score and event summaries over a specified time window.

- **Authentication**: None
- **Query Parameters**:
  - `period` *(optional, default: `daily`)*: One of `daily`, `weekly`, `monthly`.
- **Responses**:
  - `200 OK`:
    ```json
    {
      "employee_id": 1,
      "period": "daily",
      "average_score": 0.85,
      "total_productive_hours": 4.5,
      "total_idle_minutes": 30,
      "event_summary": {
        "app_focus": 45,
        "browser_tab": 18,
        "idle_start": 2,
        "login": 1,
        "outlook_activity": 0
      },
      "app_weights": {
        "VS Code": "high"
      }
    }
    ```
  - `404 Not Found`: If `employee_id` does not exist.
  - `422 Unprocessable Entity`: If `period` is not one of `daily`, `weekly`, `monthly`.

---

#### `GET /reports/{employee_id}/pdf`
Generates and serves a formatted PDF document containing the employee's productivity report.

- **Authentication**: None
- **Query Parameters**:
  - `period` *(optional, default: `daily`)*: One of `daily`, `weekly`, `monthly`.
- **Responses**:
  - `200 OK`: Binary PDF file stream with `Content-Type: application/pdf` and `Content-Disposition: inline; filename="report_{id}_{period}.pdf"`.
  - `404 Not Found`: If `employee_id` does not exist.
  - `422 Unprocessable Entity`: If `period` parameter is invalid.
  - `500 Internal Server Error`: If no PDF generation backend (WeasyPrint / ReportLab) is available.
