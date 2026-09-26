"""Organizations must never see or change each other's data."""

from datetime import datetime, timezone

from tests.conftest import agent_headers


def test_organizations_are_isolated(make_client):
    acme = make_client("Acme", "owner@acme.example")
    globex = make_client("Globex", "owner@globex.example")

    acme_emp = acme.post("/employees", json={"name": "Acme Person", "email": "same@example.com"}).json()["id"]
    # The same employee email is fine in a different organization.
    assert globex.post("/employees", json={"name": "Globex Person", "email": "same@example.com"}).status_code == 201

    assert [e["name"] for e in globex.get("/employees").json()] == ["Globex Person"]
    assert [r["name"] for r in globex.get("/team/summary").json()] == ["Globex Person"]

    for method, path, body in [
        ("get", f"/employees/{acme_emp}", None),
        ("put", f"/employees/{acme_emp}", {"name": "Hijacked"}),
        ("delete", f"/employees/{acme_emp}", None),
        ("post", f"/employees/{acme_emp}/agent-token", None),
        ("delete", f"/employees/{acme_emp}/agent-token", None),
        ("get", f"/config/{acme_emp}", None),
        ("post", f"/config/{acme_emp}", {"min_productive_hours": 1}),
        ("get", f"/reports/{acme_emp}", None),
        ("get", f"/reports/{acme_emp}/trend", None),
        ("get", f"/reports/{acme_emp}/pdf", None),
    ]:
        kwargs = {"json": body} if body is not None else {}
        assert getattr(globex, method)(path, **kwargs).status_code == 404, (method, path)

    assert acme.get(f"/employees/{acme_emp}").json()["name"] == "Acme Person"


def test_manager_accounts_are_isolated(make_client):
    acme = make_client("Acme", "owner@acme.example")
    globex = make_client("Globex", "owner@globex.example")
    acme_owner_id = acme.get("/auth/me").json()["user"]["id"]

    assert [u["email"] for u in globex.get("/organization/users").json()] == ["owner@globex.example"]
    assert globex.delete(f"/organization/users/{acme_owner_id}").status_code == 404


def test_agent_token_only_writes_to_its_own_employee(make_client):
    acme = make_client("Acme", "owner@acme.example")
    globex = make_client("Globex", "owner@globex.example")
    acme_emp = acme.post("/employees", json={"name": "Acme Person"}).json()["id"]
    globex_emp = globex.post("/employees", json={"name": "Globex Person"}).json()["id"]

    now = datetime.now(timezone.utc).isoformat()
    result = globex.post(
        "/ingest",
        json={"events": [
            {"employee_id": acme_emp, "event_type": "login", "timestamp": now},
            {"event_type": "login", "timestamp": now},
        ]},
        headers=agent_headers(globex, globex_emp),
    ).json()
    assert result == {"status": "success", "events_stored": 1, "events_rejected": 1}

    assert acme.get(f"/reports/{acme_emp}").json()["event_summary"]["login"] == 0
    assert globex.get(f"/reports/{globex_emp}").json()["event_summary"]["login"] == 1
