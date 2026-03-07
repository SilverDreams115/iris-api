from conftest import TestingSessionLocal, auth_headers, login_user, register_user

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


def get_user_by_email(email: str):
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def test_register_user_success(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "auth_register@example.com",
            "password": "Password123",
            "name": "Auth Register",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "auth_register@example.com"
    assert data["name"] == "Auth Register"
    assert data["is_active"] is True
    assert data["role"] == "user"


def test_register_duplicate_user_fails(client):
    register_user(client, "auth_duplicate@example.com", "Password123", "Dup User")

    response = client.post(
        "/auth/register",
        json={
            "email": "auth_duplicate@example.com",
            "password": "Password123",
            "name": "Dup User Again",
        },
    )
    assert response.status_code in (400, 409), response.text


def test_login_success(client):
    register_user(client, "auth_login@example.com", "Password123", "Auth Login")

    response = client.post(
        "/auth/login",
        data={
            "username": "auth_login@example.com",
            "password": "Password123",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"


def test_login_invalid_password_fails(client):
    register_user(client, "auth_bad_login@example.com", "Password123", "Bad Login")

    response = client.post(
        "/auth/login",
        data={
            "username": "auth_bad_login@example.com",
            "password": "WrongPassword123",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in (400, 401), response.text


def test_get_current_user_me(client):
    register_user(client, "auth_me@example.com", "Password123", "Auth Me")
    token = login_user(client, "auth_me@example.com", "Password123")

    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "auth_me@example.com"
    assert data["name"] == "Auth Me"


def test_get_current_user_me_without_token_fails(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403), response.text


def test_get_current_user_me_with_invalid_token_fails(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code in (401, 403), response.text


def test_change_password_success(client):
    register_user(
        client,
        "auth_password_change@example.com",
        "Password123",
        "Password Change",
    )
    token = login_user(client, "auth_password_change@example.com", "Password123")

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Password123",
            "new_password": "NewPassword456",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text

    relogin = client.post(
        "/auth/login",
        data={
            "username": "auth_password_change@example.com",
            "password": "NewPassword456",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert relogin.status_code == 200, relogin.text

    user = get_user_by_email("auth_password_change@example.com")
    assert user is not None


def test_change_password_wrong_current_password_fails(client):
    register_user(
        client,
        "auth_wrong_current@example.com",
        "Password123",
        "Wrong Current",
    )
    token = login_user(client, "auth_wrong_current@example.com", "Password123")

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "DefinitelyWrong",
            "new_password": "NewPassword456",
        },
        headers=auth_headers(token),
    )
    assert response.status_code in (400, 401), response.text


def test_change_password_without_token_fails(client):
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Password123",
            "new_password": "NewPassword456",
        },
    )
    assert response.status_code in (401, 403), response.text


def test_non_admin_cannot_access_admin_user_list(client):
    register_user(client, "auth_normal_user@example.com", "Password123", "Normal User")
    token = login_user(client, "auth_normal_user@example.com", "Password123")

    response = client.get("/users/", headers=auth_headers(token))
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not enough permissions"


def test_admin_can_access_admin_user_list(client):
    register_user(client, "auth_admin@example.com", "Password123", "Auth Admin")
    set_user_role("auth_admin@example.com", "admin")
    token = login_user(client, "auth_admin@example.com", "Password123")

    response = client.get("/users/", headers=auth_headers(token))
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_inactive_user_cannot_use_protected_route_if_supported(client):
    register_user(client, "auth_inactive@example.com", "Password123", "Inactive User")
    token = login_user(client, "auth_inactive@example.com", "Password123")

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "auth_inactive@example.com").first()
        assert user is not None
        user.is_active = False
        db.commit()
    finally:
        db.close()

    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code in (401, 403), response.text
