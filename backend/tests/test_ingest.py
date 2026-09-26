from datetime import datetime, timedelta, timezone

from app.settings import get_settings
from tests.conftest import agent_headers


def _event(event_type="login", when=None, **extra):
    when = when or datetime.now(timezone.utc)
    return {"event_type": event_type, "timestamp": when.isoformat(), **extra}


def test_ingest_requires_valid_agent_token(client, anon_client):
    emp_id = client.post("/employees", json={"name": "Agent Target"}).json()["id"]
    payload = {"events": [_event()]}

    assert anon_client.post("/ingest", json=payload).status_code == 401
    assert anon_client.post("/ingest", json=payload, headers={"X-Agent-Token": "wrong"}).status_code == 401

    headers = agent_headers(client, emp_id)
    assert anon_client.post("/ingest", json=payload, headers=headers).json()["events_stored"] == 1

    bearer = {"Authorization": f"Bearer {headers['X-Agent-Token']}"}
    assert anon_client.post("/ingest", json=payload, headers=bearer).status_code == 200


def test_agent_token_rotation_and_revocation(client, anon_client):
    emp_id = client.post("/employees", json={"name": "Rotating"}).json()["id"]
    first = client.post(f"/employees/{emp_id}/agent-token").json()
    assert first["agent_token"].startswith("mdr_")
    assert client.get(f"/employees/{emp_id}").json()["agent_token_created_at"] is not None

    second = client.post(f"/employees/{emp_id}/agent-token").json()["agent_token"]
    payload = {"events": [_event()]}
    assert anon_client.post("/ingest", json=payload, headers={"X-Agent-Token": first["agent_token"]}).status_code == 401
    assert anon_client.post("/ingest", json=payload, headers={"X-Agent-Token": second}).status_code == 200

    assert client.delete(f"/employees/{emp_id}/agent-token").status_code == 204
    assert anon_client.post("/ingest", json=payload, headers={"X-Agent-Token": second}).status_code == 401
    assert client.get(f"/employees/{emp_id}").json()["agent_token_created_at"] is None


def test_invalid_events_are_skipped_not_fatal(client):
    emp_id = client.post("/employees", json={"name": "Messy Agent"}).json()["id"]
    now = datetime.now(timezone.utc)
    events = [
        _event("app_focus", detail={"app_name": "Code", "window_title": "x" * 2000, "nested": {"a": 1}}),
        _event("keylogger"),
        {"event_type": "login", "timestamp": "not a date"},
        _event("login", when=now + timedelta(days=2)),
        "not even an object",
        _event("idle_end", detail={"duration_seconds": 120}),
    ]
    result = client.post("/ingest", json={"events": events}, headers=agent_headers(client, emp_id)).json()
    assert result == {"status": "success", "events_stored": 2, "events_rejected": 4}


def test_ingest_stores_timestamps_in_utc(client, db_session):
    from app import models

    emp_id = client.post("/employees", json={"name": "Beirut Agent"}).json()["id"]
    beirut = timezone(timedelta(hours=3))
    local = datetime(2026, 9, 1, 10, 0, tzinfo=beirut)
    client.post("/ingest", json={"events": [_event(when=local)]}, headers=agent_headers(client, emp_id))
    stored = db_session.query(models.ActivityLog).filter_by(employee_id=emp_id).one()
    assert stored.timestamp == datetime(2026, 9, 1, 7, 0)


def test_ingest_batch_limits(client):
    emp_id = client.post("/employees", json={"name": "Chatty Agent"}).json()["id"]
    headers = agent_headers(client, emp_id)
    too_many = [_event()] * (get_settings().max_ingest_events + 1)
    assert client.post("/ingest", json={"events": too_many}, headers=headers).status_code == 413
    assert client.post("/ingest", json={"events": "nope"}, headers=headers).status_code == 422
