from datetime import datetime, timedelta, timezone

from tests.conftest import agent_headers


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest(client, employee_id: int, events: list[dict]):
    response = client.post("/ingest", json={"events": events}, headers=agent_headers(client, employee_id))
    assert response.status_code == 200, response.text
    return response.json()


def test_health_check(anon_client):
    response = anon_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_list_get_update_employee(client):
    create_payload = {
        "name": "  Alice Smith  ",
        "role": "  Frontend Engineer  ",
        "email": "  Alice@Example.com  ",
        "job_description": "  Build user interfaces  ",
        "role_tag": "  engineering  ",
    }
    response = client.post("/employees", json=create_payload)
    assert response.status_code == 201
    data = response.json()
    employee_id = data["id"]
    assert data["name"] == "Alice Smith"
    assert data["role"] == "Frontend Engineer"
    assert data["email"] == "alice@example.com"
    assert data["job_description"] == "Build user interfaces"
    assert data["role_tag"] == "engineering"
    assert data["agent_token_created_at"] is None

    employees = client.get("/employees").json()
    assert [e["id"] for e in employees] == [employee_id]

    assert client.get(f"/employees/{employee_id}").json()["name"] == "Alice Smith"

    update_payload = {
        "name": "Alice Johnson",
        "role": "Senior Engineer",
        "email": "alice.j@example.com",
        "job_description": "Lead frontend architecture",
        "role_tag": "engineering-lead",
    }
    updated = client.put(f"/employees/{employee_id}", json=update_payload)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Alice Johnson"
    assert updated.json()["job_description"] == "Lead frontend architecture"


def test_employee_validation(client):
    assert client.post("/employees", json={"name": ""}).status_code == 422
    assert client.post("/employees", json={"name": "   "}).status_code == 422
    assert client.post("/employees", json={"name": "Bad Email", "email": "not-an-email"}).status_code == 422
    assert client.post("/employees", json={"name": "x" * 201}).status_code == 422


def test_employee_normalization_optional_fields(client):
    payload = {"name": "Bob Doe", "role": "   ", "email": "", "job_description": "  ", "role_tag": None}
    data = client.post("/employees", json=payload).json()
    assert data["role"] is None
    assert data["email"] is None
    assert data["job_description"] is None
    assert data["role_tag"] is None


def test_duplicate_email_conflict(client):
    client.post("/employees", json={"name": "User One", "email": "unique@example.com"})

    conflict_create = client.post("/employees", json={"name": "User Two", "email": "UNIQUE@example.com"})
    assert conflict_create.status_code == 409
    assert conflict_create.json()["detail"] == "An employee with this email already exists"

    user2 = client.post("/employees", json={"name": "User Two", "email": "user2@example.com"}).json()
    conflict_update = client.put(f"/employees/{user2['id']}", json={"name": "User Two", "email": "unique@example.com"})
    assert conflict_update.status_code == 409

    self_update = client.put(f"/employees/{user2['id']}", json={"name": "User Two Updated", "email": "user2@example.com"})
    assert self_update.status_code == 200


def test_multiple_employees_with_no_email_allowed(client):
    assert client.post("/employees", json={"name": "No Email 1", "email": None}).status_code == 201
    assert client.post("/employees", json={"name": "No Email 2", "email": ""}).status_code == 201


def test_unknown_employee_returns_404(client):
    unknown_id = 99999
    assert client.get(f"/employees/{unknown_id}").status_code == 404
    assert client.put(f"/employees/{unknown_id}", json={"name": "Ghost"}).status_code == 404
    assert client.get(f"/config/{unknown_id}").status_code == 404
    assert client.post(f"/config/{unknown_id}", json={"min_productive_hours": 7.0}).status_code == 404
    assert client.get(f"/reports/{unknown_id}").status_code == 404
    assert client.get(f"/reports/{unknown_id}/pdf").status_code == 404
    assert client.get(f"/reports/{unknown_id}/trend").status_code == 404
    assert client.post(f"/employees/{unknown_id}/agent-token").status_code == 404


def test_config_operations(client):
    emp_id = client.post("/employees", json={"name": "Config Test Emp"}).json()["id"]

    cfg = client.get(f"/config/{emp_id}")
    assert cfg.status_code == 200
    assert cfg.json()["employee_id"] == emp_id

    save_payload = {
        "job_description": "Full Stack Dev",
        "role_tag": "core-team",
        "software_weights": {"VS Code": "high", "YouTube": "low"},
        "category_weights": {"app_usage": 0.5, "browser": 0.2, "punctuality": 0.2, "idle": 0.1},
        "schedule": {"mon": [["14:00", "18:00"], ["09:00", "13:00"]]},
        "min_productive_hours": 7.5,
        "max_idle_minutes": 45,
    }
    saved = client.post(f"/config/{emp_id}", json=save_payload)
    assert saved.status_code == 200
    body = saved.json()
    assert body["job_description"] == "Full Stack Dev"
    assert body["min_productive_hours"] == 7.5
    assert body["software_weights"]["VS Code"] == "high"
    assert body["schedule"]["mon"] == [["09:00", "13:00"], ["14:00", "18:00"]]


def test_config_validation(client):
    emp_id = client.post("/employees", json={"name": "Validated"}).json()["id"]
    bad_payloads = [
        {"category_weights": {"app_usage": 0.5, "browser": 0.2, "punctuality": 0.2, "idle": 0.3}},
        {"category_weights": {"typing_speed": 1.0}},
        {"software_weights": {"VS Code": "extreme"}},
        {"software_weights": {"Slack": "high", "slack": "low"}},
        {"schedule": {"mon": [["17:00", "09:00"]]}},
        {"schedule": {"mon": [["09:00", "13:00"], ["12:00", "15:00"]]}},
        {"schedule": {"funday": [["09:00", "13:00"]]}},
        {"schedule": {"mon": [["9am", "5pm"]]}},
        {"min_productive_hours": 25},
        {"max_idle_minutes": -1},
    ]
    for payload in bad_payloads:
        assert client.post(f"/config/{emp_id}", json=payload).status_code == 422, payload


def test_reports_daily_weekly_monthly(client):
    emp_id = client.post("/employees", json={"name": "Report Subject"}).json()["id"]
    now_iso = _now_iso()
    ingest(client, emp_id, [
        {"event_type": "login", "timestamp": now_iso},
        {"event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": "Code"}},
        {"event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": "Terminal"}},
        {"event_type": "browser_tab", "timestamp": now_iso, "detail": {"tab_title": "GitHub"}},
        {"event_type": "idle_start", "timestamp": now_iso},
    ])

    daily = client.get(f"/reports/{emp_id}?period=daily").json()
    assert daily["employee_id"] == emp_id
    assert daily["period"] == "daily"
    assert daily["days_active"] == 1
    assert daily["event_summary"] == {"app_focus": 2, "browser_tab": 1, "idle_start": 1, "login": 1, "outlook_activity": 0}
    assert daily["total_productive_hours"] == 0.2
    assert daily["total_idle_minutes"] == 15
    # 0.4 * 2/20 + 0.2 * 1/15 + 0.2 * 1 + 0.2 * 0.85
    assert abs(daily["average_score"] - (0.04 + 0.2 / 15 + 0.2 + 0.17)) < 1e-9

    assert client.get(f"/reports/{emp_id}?period=weekly").json()["period"] == "weekly"
    assert client.get(f"/reports/{emp_id}?period=monthly").json()["period"] == "monthly"
    assert client.get(f"/reports/{emp_id}?period=yearly").status_code == 422


def test_pdf_export(client):
    emp_id = client.post("/employees", json={"name": "PDF <Subject>"}).json()["id"]
    ingest(client, emp_id, [{"event_type": "app_focus", "timestamp": _now_iso(), "detail": {"app_name": "Code & Co"}}])

    pdf_res = client.get(f"/reports/{emp_id}/pdf?period=daily")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    empty_id = client.post("/employees", json={"name": "No Activity"}).json()["id"]
    assert client.get(f"/reports/{empty_id}/pdf?period=weekly").status_code == 200


def test_delete_employee_removes_related_data(client, db_session):
    from app import models

    emp_id = client.post("/employees", json={"name": "To Delete", "email": "gone@example.com"}).json()["id"]
    ingest(client, emp_id, [{"event_type": "login", "timestamp": _now_iso()}])

    assert client.delete(f"/employees/{emp_id}").status_code == 204
    assert client.get(f"/employees/{emp_id}").status_code == 404
    assert client.get("/employees").json() == []
    assert db_session.query(models.ActivityLog).filter_by(employee_id=emp_id).count() == 0
    assert db_session.query(models.Config).filter_by(employee_id=emp_id).count() == 0

    assert client.delete(f"/employees/{emp_id}").status_code == 404
    assert client.post("/employees", json={"name": "New Person", "email": "gone@example.com"}).status_code == 201


def test_team_summary(client):
    first = client.post("/employees", json={"name": "First", "role": "Engineer"}).json()["id"]
    second = client.post("/employees", json={"name": "Second"}).json()["id"]
    now_iso = _now_iso()
    ingest(client, first, [
        {"event_type": "login", "timestamp": now_iso},
        {"event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": "Code"}},
    ])

    rows = client.get("/team/summary?period=weekly").json()
    assert [row["id"] for row in rows] == [first, second]
    assert rows[0]["name"] == "First"
    assert rows[0]["role"] == "Engineer"
    assert rows[0]["period"] == "weekly"
    assert rows[0]["event_summary"]["app_focus"] == 1
    assert rows[0]["average_score"] is not None
    assert rows[1]["average_score"] is None
    assert rows[1]["days_active"] == 0

    assert client.get("/team/summary?period=yearly").status_code == 422


def test_report_includes_top_apps(client):
    emp_id = client.post("/employees", json={"name": "App User"}).json()["id"]
    now_iso = _now_iso()
    ingest(client, emp_id, [
        {"event_type": "app_focus", "timestamp": now_iso, "detail": {"app_name": name}}
        for name in ["VS Code", "Slack", "VS Code", "VS Code", "Slack", "Figma"]
    ])

    assert client.get(f"/reports/{emp_id}?period=daily").json()["top_apps"] == [
        {"app_name": "VS Code", "focus_events": 3},
        {"app_name": "Slack", "focus_events": 2},
        {"app_name": "Figma", "focus_events": 1},
    ]


def test_report_trend(client):
    emp_id = client.post("/employees", json={"name": "Trend Subject"}).json()["id"]
    now = datetime.now(timezone.utc)
    two_days_ago = (now - timedelta(days=2)).isoformat()
    ingest(client, emp_id, [
        {"event_type": "login", "timestamp": now.isoformat()},
        {"event_type": "app_focus", "timestamp": two_days_ago, "detail": {"app_name": "Code"}},
        {"event_type": "app_focus", "timestamp": two_days_ago, "detail": {"app_name": "Code"}},
    ])

    body = client.get(f"/reports/{emp_id}/trend?days=7").json()
    assert body["days"] == 7
    points = body["points"]
    assert len(points) == 7
    assert points[-1]["date"] == now.date().isoformat()
    assert points[-1]["event_summary"]["login"] == 1
    assert points[-3]["event_summary"]["app_focus"] == 2
    assert points[-3]["has_activity"] is True
    assert points[0]["has_activity"] is False
    assert points[0]["average_score"] is None

    assert client.get(f"/reports/{emp_id}/trend?days=0").status_code == 422
    assert client.get(f"/reports/{emp_id}/trend?days=91").status_code == 422
