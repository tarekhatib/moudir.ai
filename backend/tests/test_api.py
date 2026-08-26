from datetime import datetime, timezone
import pytest


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_list_get_update_employee(client):
    # 1. Create employee
    create_payload = {
        "name": "  Alice Smith  ",
        "role": "  Frontend Engineer  ",
        "email": "  alice@example.com  ",
        "job_description": "  Build user interfaces  ",
        "role_tag": "  engineering  ",
    }
    response = client.post("/employees", json=create_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    employee_id = data["id"]
    # Verify values were trimmed
    assert data["name"] == "Alice Smith"
    assert data["role"] == "Frontend Engineer"
    assert data["email"] == "alice@example.com"
    assert data["job_description"] == "Build user interfaces"
    assert data["role_tag"] == "engineering"

    # 2. List employees
    list_response = client.get("/employees")
    assert list_response.status_code == 200
    employees = list_response.json()
    assert len(employees) == 1
    assert employees[0]["id"] == employee_id
    assert employees[0]["name"] == "Alice Smith"

    # 3. Get single employee
    get_response = client.get(f"/employees/{employee_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Alice Smith"

    # 4. Update employee
    update_payload = {
        "name": "Alice Johnson",
        "role": "Senior Engineer",
        "email": "alice.j@example.com",
        "job_description": "Lead frontend architecture",
        "role_tag": "engineering-lead",
    }
    put_response = client.put(f"/employees/{employee_id}", json=update_payload)
    assert put_response.status_code == 200
    updated_data = put_response.json()
    assert updated_data["name"] == "Alice Johnson"
    assert updated_data["email"] == "alice.j@example.com"
    assert updated_data["job_description"] == "Lead frontend architecture"


def test_employee_validation_empty_name(client):
    # Empty string name
    response = client.post("/employees", json={"name": ""})
    assert response.status_code == 422

    # Whitespace-only name
    response = client.post("/employees", json={"name": "   "})
    assert response.status_code == 422


def test_employee_normalization_optional_fields(client):
    # Empty optional fields should be normalized to None (null)
    payload = {
        "name": "Bob Doe",
        "role": "   ",
        "email": "",
        "job_description": "  ",
        "role_tag": None,
    }
    response = client.post("/employees", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bob Doe"
    assert data["role"] is None
    assert data["email"] is None
    assert data["job_description"] is None
    assert data["role_tag"] is None


def test_duplicate_email_conflict(client):
    # Create first employee with email
    client.post(
        "/employees",
        json={"name": "User One", "email": "unique@example.com"},
    )

    # Creating second employee with identical email must return 409 Conflict
    conflict_create = client.post(
        "/employees",
        json={"name": "User Two", "email": "unique@example.com"},
    )
    assert conflict_create.status_code == 409
    assert conflict_create.json()["detail"] == "An employee with this email already exists"

    # Create second employee with different email
    user2 = client.post(
        "/employees",
        json={"name": "User Two", "email": "user2@example.com"},
    ).json()

    # Updating second employee to first employee's email must return 409 Conflict
    conflict_update = client.put(
        f"/employees/{user2['id']}",
        json={"name": "User Two Updated", "email": "unique@example.com"},
    )
    assert conflict_update.status_code == 409
    assert conflict_update.json()["detail"] == "An employee with this email already exists"

    # Updating second employee keeping its own email should succeed
    self_update = client.put(
        f"/employees/{user2['id']}",
        json={"name": "User Two Updated", "email": "user2@example.com"},
    )
    assert self_update.status_code == 200


def test_multiple_employees_with_no_email_allowed(client):
    # Multiple employees without email (None or empty) should not conflict
    res1 = client.post("/employees", json={"name": "User NoEmail 1", "email": None})
    res2 = client.post("/employees", json={"name": "User NoEmail 2", "email": ""})
    assert res1.status_code == 200
    assert res2.status_code == 200


def test_unknown_employee_returns_404(client):
    unknown_id = 99999

    # GET employee
    assert client.get(f"/employees/{unknown_id}").status_code == 404
    # PUT employee
    assert client.put(f"/employees/{unknown_id}", json={"name": "Ghost"}).status_code == 404
    # GET config
    assert client.get(f"/config/{unknown_id}").status_code == 404
    # POST config
    assert client.post(f"/config/{unknown_id}", json={"min_productive_hours": 7.0}).status_code == 404
    # GET reports
    assert client.get(f"/reports/{unknown_id}").status_code == 404
    # GET reports PDF
    assert client.get(f"/reports/{unknown_id}/pdf").status_code == 404


def test_config_operations(client):
    emp = client.post("/employees", json={"name": "Config Test Emp"}).json()
    emp_id = emp["id"]

    # Initial config should exist due to auto-creation during employee creation
    cfg_res = client.get(f"/config/{emp_id}")
    assert cfg_res.status_code == 200
    cfg = cfg_res.json()
    assert cfg["employee_id"] == emp_id

    # Update config with custom weights and schedule
    save_payload = {
        "job_description": "Full Stack Dev",
        "role_tag": "core-team",
        "software_weights": {"VS Code": "high", "YouTube": "low"},
        "category_weights": {"app_usage": 0.5, "browser": 0.2, "punctuality": 0.2, "idle": 0.1},
        "schedule": {"mon": [["09:00", "17:00"]]},
        "min_productive_hours": 7.5,
        "max_idle_minutes": 45,
    }
    save_res = client.post(f"/config/{emp_id}", json=save_payload)
    assert save_res.status_code == 200
    saved = save_res.json()
    assert saved["job_description"] == "Full Stack Dev"
    assert saved["min_productive_hours"] == 7.5
    assert saved["software_weights"]["VS Code"] == "high"


def test_ingest_auth_and_activity(client):
    emp = client.post("/employees", json={"name": "Ingest Target"}).json()
    emp_id = emp["id"]

    events_payload = {
        "events": [
            {
                "employee_id": emp_id,
                "event_type": "login",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detail": {},
            },
            {
                "employee_id": emp_id,
                "event_type": "app_focus",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detail": {"app_name": "VS Code", "window_title": "main.py"},
            },
            {
                "employee_id": emp_id,
                "event_type": "browser_tab",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detail": {"tab_title": "FastAPI Docs"},
            },
            {
                "employee_id": emp_id,
                "event_type": "idle_start",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "detail": {},
            },
        ]
    }

    # Missing auth header
    unauth_res = client.post("/ingest", json=events_payload)
    assert unauth_res.status_code == 401

    # Invalid auth header
    bad_auth_res = client.post(
        "/ingest",
        json=events_payload,
        headers={"X-Agent-Token": "wrong-token"},
    )
    assert bad_auth_res.status_code == 401

    # Valid auth header
    success_res = client.post(
        "/ingest",
        json=events_payload,
        headers={"X-Agent-Token": "test-secret-token"},
    )
    assert success_res.status_code == 200
    assert success_res.json() == {"status": "success", "events_stored": 4}


def test_reports_daily_weekly_monthly(client):
    emp = client.post("/employees", json={"name": "Report Subject"}).json()
    emp_id = emp["id"]

    # Ingest mock events
    now_iso = datetime.now(timezone.utc).isoformat()
    client.post(
        "/ingest",
        json={
            "events": [
                {"employee_id": emp_id, "event_type": "login", "timestamp": now_iso, "detail": {}},
                {"employee_id": emp_id, "event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": "Code"}},
                {"employee_id": emp_id, "event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": "Terminal"}},
                {"employee_id": emp_id, "event_type": "browser_tab", "timestamp": now_iso, "detail": {"tab_title": "GitHub"}},
                {"employee_id": emp_id, "event_type": "idle_start", "timestamp": now_iso, "detail": {}},
            ]
        },
        headers={"X-Agent-Token": "test-secret-token"},
    )

    # Daily report
    daily_res = client.get(f"/reports/{emp_id}?period=daily")
    assert daily_res.status_code == 200
    daily_data = daily_res.json()
    assert daily_data["employee_id"] == emp_id
    assert daily_data["period"] == "daily"
    assert "average_score" in daily_data
    assert daily_data["event_summary"]["app_focus"] == 2
    assert daily_data["event_summary"]["browser_tab"] == 1
    assert daily_data["event_summary"]["idle_start"] == 1
    assert daily_data["event_summary"]["login"] == 1
    assert daily_data["total_productive_hours"] == 0.2  # 2 events * 0.1
    assert daily_data["total_idle_minutes"] == 15      # 1 event * 15

    # Weekly report
    weekly_res = client.get(f"/reports/{emp_id}?period=weekly")
    assert weekly_res.status_code == 200
    assert weekly_res.json()["period"] == "weekly"

    # Monthly report
    monthly_res = client.get(f"/reports/{emp_id}?period=monthly")
    assert monthly_res.status_code == 200
    assert monthly_res.json()["period"] == "monthly"

    # Invalid period
    invalid_period_res = client.get(f"/reports/{emp_id}?period=yearly")
    assert invalid_period_res.status_code == 422


def test_pdf_export(client):
    emp = client.post("/employees", json={"name": "PDF Subject"}).json()
    emp_id = emp["id"]

    pdf_res = client.get(f"/reports/{emp_id}/pdf?period=daily")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
