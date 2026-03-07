from conftest import TestingSessionLocal, auth_headers, login_user, register_user

import app.main as main_module
from app.models.user import User


def set_user_role(email: str, role: str) -> None:
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.role = role
        db.commit()
    finally:
        db.close()


def create_portfolio(
    client, token, name="Main Portfolio", description="Test portfolio"
):
    response = client.post(
        "/portfolios/",
        json={
            "name": name,
            "description": description,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_broker_account(
    client,
    token,
    broker_name="Demo Broker",
    account_label="Primary",
    account_type="demo",
):
    response = client.post(
        "/broker-accounts/",
        json={
            "broker_name": broker_name,
            "account_label": account_label,
            "account_type": account_type,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "message" in data
    assert "IRIS API" in data["message"]
    assert "running" in data["message"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"
    assert response.json()["app_name"] == "IRIS API"


def test_ready_endpoint_ok(client):
    response = client.get("/ready")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "ok"


def test_ready_endpoint_db_failure(client, monkeypatch):
    class FailingSessionLocal:
        def __call__(self):
            return self

        def __enter__(self):
            raise RuntimeError("db down")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(main_module, "SessionLocal", FailingSessionLocal())

    response = client.get("/ready")
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "error"
    assert detail["checks"]["database"].startswith("error:")
    assert detail["checks"]["redis"] == "ok"


def test_ready_endpoint_redis_failure(client, monkeypatch):
    class FailingRedisClient:
        def ping(self):
            raise RuntimeError("redis down")

    monkeypatch.setattr(main_module, "redis_client", FailingRedisClient())

    response = client.get("/ready")
    assert response.status_code == 503, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "error"
    assert detail["checks"]["database"] == "ok"
    assert detail["checks"]["redis"].startswith("error:")


def test_portfolio_crud_flow_for_owner(client):
    register_user(
        client, "portfolio_owner@example.com", "Password123", "Portfolio Owner"
    )
    token = login_user(client, "portfolio_owner@example.com", "Password123")

    created = create_portfolio(client, token)
    portfolio_id = created["id"]

    listed = client.get("/portfolios/", headers=auth_headers(token))
    assert listed.status_code == 200, listed.text
    listed_data = listed.json()
    assert len(listed_data) == 1
    assert listed_data[0]["id"] == portfolio_id

    fetched = client.get(f"/portfolios/{portfolio_id}", headers=auth_headers(token))
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["name"] == "Main Portfolio"

    updated = client.patch(
        f"/portfolios/{portfolio_id}",
        json={"name": "Updated Portfolio", "description": "Updated description"},
        headers=auth_headers(token),
    )
    assert updated.status_code == 200, updated.text
    updated_data = updated.json()
    assert updated_data["name"] == "Updated Portfolio"
    assert updated_data["description"] == "Updated description"

    deleted = client.delete(f"/portfolios/{portfolio_id}", headers=auth_headers(token))
    assert deleted.status_code == 204, deleted.text

    missing = client.get(f"/portfolios/{portfolio_id}", headers=auth_headers(token))
    assert missing.status_code == 404, missing.text
    assert missing.json()["detail"] == "Portfolio not found"


def test_other_user_cannot_access_foreign_portfolio(client):
    register_user(client, "portfolio_a@example.com", "Password123", "Portfolio A")
    owner_token = login_user(client, "portfolio_a@example.com", "Password123")
    portfolio = create_portfolio(client, owner_token, name="Private Portfolio")

    register_user(client, "portfolio_b@example.com", "Password123", "Portfolio B")
    intruder_token = login_user(client, "portfolio_b@example.com", "Password123")

    response_get = client.get(
        f"/portfolios/{portfolio['id']}",
        headers=auth_headers(intruder_token),
    )
    assert response_get.status_code == 403, response_get.text
    assert response_get.json()["detail"] == "Not enough permissions"

    response_patch = client.patch(
        f"/portfolios/{portfolio['id']}",
        json={"name": "Hacked"},
        headers=auth_headers(intruder_token),
    )
    assert response_patch.status_code == 403, response_patch.text
    assert response_patch.json()["detail"] == "Not enough permissions"

    response_delete = client.delete(
        f"/portfolios/{portfolio['id']}",
        headers=auth_headers(intruder_token),
    )
    assert response_delete.status_code == 403, response_delete.text
    assert response_delete.json()["detail"] == "Not enough permissions"


def test_portfolio_not_found_paths(client):
    register_user(client, "portfolio_nf@example.com", "Password123", "Portfolio NF")
    token = login_user(client, "portfolio_nf@example.com", "Password123")

    response_get = client.get("/portfolios/999999", headers=auth_headers(token))
    assert response_get.status_code == 404, response_get.text

    response_patch = client.patch(
        "/portfolios/999999",
        json={"name": "Missing"},
        headers=auth_headers(token),
    )
    assert response_patch.status_code == 404, response_patch.text

    response_delete = client.delete("/portfolios/999999", headers=auth_headers(token))
    assert response_delete.status_code == 404, response_delete.text


def test_admin_can_list_all_portfolios(client):
    register_user(
        client, "portfolio_user1@example.com", "Password123", "Portfolio User 1"
    )
    token_user1 = login_user(client, "portfolio_user1@example.com", "Password123")
    create_portfolio(client, token_user1, name="Portfolio 1")

    register_user(
        client, "portfolio_admin@example.com", "Password123", "Portfolio Admin"
    )
    set_user_role("portfolio_admin@example.com", "admin")
    admin_token = login_user(client, "portfolio_admin@example.com", "Password123")
    create_portfolio(client, admin_token, name="Portfolio 2")

    response = client.get("/portfolios/", headers=auth_headers(admin_token))
    assert response.status_code == 200, response.text
    names = {item["name"] for item in response.json()}
    assert "Portfolio 1" in names
    assert "Portfolio 2" in names


def test_broker_account_crud_flow_for_owner(client):
    register_user(client, "broker_owner@example.com", "Password123", "Broker Owner")
    token = login_user(client, "broker_owner@example.com", "Password123")

    created = create_broker_account(client, token)
    broker_id = created["id"]

    listed = client.get("/broker-accounts/", headers=auth_headers(token))
    assert listed.status_code == 200, listed.text
    listed_data = listed.json()
    assert len(listed_data) == 1
    assert listed_data[0]["id"] == broker_id

    fetched = client.get(f"/broker-accounts/{broker_id}", headers=auth_headers(token))
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["broker_name"] == "Demo Broker"

    updated = client.patch(
        f"/broker-accounts/{broker_id}",
        json={
            "account_label": "Updated Label",
            "status": "inactive",
        },
        headers=auth_headers(token),
    )
    assert updated.status_code == 200, updated.text
    updated_data = updated.json()
    assert updated_data["account_label"] == "Updated Label"
    assert updated_data["status"] == "inactive"

    deleted = client.delete(
        f"/broker-accounts/{broker_id}", headers=auth_headers(token)
    )
    assert deleted.status_code == 204, deleted.text

    missing = client.get(f"/broker-accounts/{broker_id}", headers=auth_headers(token))
    assert missing.status_code == 404, missing.text
    assert missing.json()["detail"] == "Broker account not found"


def test_other_user_cannot_access_foreign_broker_account(client):
    register_user(client, "broker_a@example.com", "Password123", "Broker A")
    owner_token = login_user(client, "broker_a@example.com", "Password123")
    broker_account = create_broker_account(client, owner_token)

    register_user(client, "broker_b@example.com", "Password123", "Broker B")
    intruder_token = login_user(client, "broker_b@example.com", "Password123")

    response_get = client.get(
        f"/broker-accounts/{broker_account['id']}",
        headers=auth_headers(intruder_token),
    )
    assert response_get.status_code == 403, response_get.text
    assert response_get.json()["detail"] == "Not enough permissions"

    response_patch = client.patch(
        f"/broker-accounts/{broker_account['id']}",
        json={"account_label": "Hacked Label"},
        headers=auth_headers(intruder_token),
    )
    assert response_patch.status_code == 403, response_patch.text
    assert response_patch.json()["detail"] == "Not enough permissions"

    response_delete = client.delete(
        f"/broker-accounts/{broker_account['id']}",
        headers=auth_headers(intruder_token),
    )
    assert response_delete.status_code == 403, response_delete.text
    assert response_delete.json()["detail"] == "Not enough permissions"


def test_broker_account_not_found_paths(client):
    register_user(client, "broker_nf@example.com", "Password123", "Broker NF")
    token = login_user(client, "broker_nf@example.com", "Password123")

    response_get = client.get("/broker-accounts/999999", headers=auth_headers(token))
    assert response_get.status_code == 404, response_get.text

    response_patch = client.patch(
        "/broker-accounts/999999",
        json={"account_label": "Missing"},
        headers=auth_headers(token),
    )
    assert response_patch.status_code == 404, response_patch.text

    response_delete = client.delete(
        "/broker-accounts/999999",
        headers=auth_headers(token),
    )
    assert response_delete.status_code == 404, response_delete.text


def test_admin_can_list_all_broker_accounts(client):
    register_user(client, "broker_user1@example.com", "Password123", "Broker User 1")
    token_user1 = login_user(client, "broker_user1@example.com", "Password123")
    create_broker_account(client, token_user1, account_label="Broker One")

    register_user(client, "broker_admin@example.com", "Password123", "Broker Admin")
    set_user_role("broker_admin@example.com", "admin")
    admin_token = login_user(client, "broker_admin@example.com", "Password123")
    create_broker_account(client, admin_token, account_label="Broker Two")

    response = client.get("/broker-accounts/", headers=auth_headers(admin_token))
    assert response.status_code == 200, response.text
    labels = {item["account_label"] for item in response.json()}
    assert "Broker One" in labels
    assert "Broker Two" in labels
