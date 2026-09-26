from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings
from tests.conftest import PASSWORD


def test_signup_creates_owner_and_signs_in(anon_client):
    response = anon_client.post(
        "/auth/signup",
        json={"organization_name": " Acme ", "name": "Rana", "email": "Rana@Acme.example", "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["organization"]["name"] == "Acme"
    assert body["user"] == {"id": body["user"]["id"], "name": "Rana", "email": "rana@acme.example", "role": "owner"}

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert anon_client.get("/auth/me").json()["user"]["email"] == "rana@acme.example"


def test_signup_validation_and_duplicates(anon_client, make_client):
    make_client(email="taken@acme.example")
    base = {"organization_name": "Other", "name": "Someone", "password": PASSWORD}
    assert anon_client.post("/auth/signup", json={**base, "email": "taken@acme.example"}).status_code == 409
    assert anon_client.post("/auth/signup", json={**base, "email": "not-an-email"}).status_code == 422
    assert anon_client.post("/auth/signup", json={**base, "email": "new@x.example", "password": "short"}).status_code == 422
    assert anon_client.post("/auth/signup", json={**base, "email": "new@x.example", "organization_name": "  "}).status_code == 422


def test_signup_can_be_disabled(anon_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "allow_signup", False)
    response = anon_client.post(
        "/auth/signup",
        json={"organization_name": "Acme", "name": "Rana", "email": "rana@acme.example", "password": PASSWORD},
    )
    assert response.status_code == 403


def test_login_logout(make_client, anon_client):
    make_client(email="owner@acme.example")

    wrong = anon_client.post("/auth/login", json={"email": "owner@acme.example", "password": "wrong-password"})
    assert wrong.status_code == 401
    unknown = anon_client.post("/auth/login", json={"email": "nobody@acme.example", "password": PASSWORD})
    assert unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]

    ok = anon_client.post("/auth/login", json={"email": " OWNER@acme.example ", "password": PASSWORD})
    assert ok.status_code == 200
    assert anon_client.get("/employees").status_code == 200

    assert anon_client.post("/auth/logout").status_code == 204
    assert anon_client.get("/employees").status_code == 401


def test_logout_revokes_session_server_side(client):
    token = client.cookies.get("moudir_session")
    client.post("/auth/logout")
    with TestClient(app, cookies={"moudir_session": token}) as replay:
        assert replay.get("/auth/me").status_code == 401


def test_login_rate_limited(make_client, anon_client):
    make_client(email="owner@acme.example")
    for _ in range(get_settings().login_max_failures):
        anon_client.post("/auth/login", json={"email": "owner@acme.example", "password": "wrong-password"})
    blocked = anon_client.post("/auth/login", json={"email": "owner@acme.example", "password": PASSWORD})
    assert blocked.status_code == 429


def test_protected_endpoints_require_sign_in(anon_client):
    for method, path in [
        ("get", "/employees"),
        ("post", "/employees"),
        ("get", "/employees/1"),
        ("put", "/employees/1"),
        ("delete", "/employees/1"),
        ("post", "/employees/1/agent-token"),
        ("get", "/config/1"),
        ("post", "/config/1"),
        ("get", "/reports/1"),
        ("get", "/reports/1/trend"),
        ("get", "/reports/1/pdf"),
        ("get", "/team/summary"),
        ("get", "/auth/me"),
        ("get", "/organization/users"),
    ]:
        assert getattr(anon_client, method)(path).status_code == 401, (method, path)

    with TestClient(app, cookies={"moudir_session": "forged"}) as forged:
        assert forged.get("/employees").status_code == 401


def test_change_password_signs_out_other_sessions(client, anon_client):
    anon_client.post("/auth/login", json={"email": "owner@acme.example", "password": PASSWORD})
    assert anon_client.get("/auth/me").status_code == 200

    bad = client.post("/auth/password", json={"current_password": "nope", "new_password": "another-long-password"})
    assert bad.status_code == 400
    ok = client.post("/auth/password", json={"current_password": PASSWORD, "new_password": "another-long-password"})
    assert ok.status_code == 204

    assert client.get("/auth/me").status_code == 200
    assert anon_client.get("/auth/me").status_code == 401
    assert anon_client.post("/auth/login", json={"email": "owner@acme.example", "password": "another-long-password"}).status_code == 200


def test_owner_manages_managers(client, anon_client):
    created = client.post(
        "/organization/users", json={"name": "Mia", "email": "mia@acme.example", "password": PASSWORD}
    )
    assert created.status_code == 201
    assert created.json()["role"] == "manager"
    assert client.post(
        "/organization/users", json={"name": "Mia", "email": "mia@acme.example", "password": PASSWORD}
    ).status_code == 409
    assert [u["email"] for u in client.get("/organization/users").json()] == ["owner@acme.example", "mia@acme.example"]

    # Managers see the same employees but can't manage accounts.
    client.post("/employees", json={"name": "Shared Employee"})
    anon_client.post("/auth/login", json={"email": "mia@acme.example", "password": PASSWORD})
    assert [e["name"] for e in anon_client.get("/employees").json()] == ["Shared Employee"]
    assert anon_client.post(
        "/organization/users", json={"name": "X", "email": "x@acme.example", "password": PASSWORD}
    ).status_code == 403
    owner_id = client.get("/auth/me").json()["user"]["id"]
    assert anon_client.delete(f"/organization/users/{owner_id}").status_code == 403

    assert client.delete(f"/organization/users/{owner_id}").status_code == 400
    assert client.delete(f"/organization/users/{created.json()['id']}").status_code == 204
    assert anon_client.get("/employees").status_code == 401
