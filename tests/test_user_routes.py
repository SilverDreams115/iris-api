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


def get_user(email: str):
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def test_admin_can_get_users_list(client):
    register_user(client, "users_admin@example.com", "Password123", "Users Admin")
    set_user_role("users_admin@example.com", "admin")
    admin_token = login_user(client, "users_admin@example.com", "Password123")

    register_user(client, "users_list_1@example.com", "Password123", "User List 1")
    register_user(client, "users_list_2@example.com", "Password123", "User List 2")

    response = client.get("/users/", headers=auth_headers(admin_token))
    assert response.status_code == 200, response.text

    emails = {item["email"] for item in response.json()}
    assert "users_admin@example.com" in emails
    assert "users_list_1@example.com" in emails
    assert "users_list_2@example.com" in emails


def test_admin_can_get_user_by_id(client):
    register_user(
        client, "users_admin_get@example.com", "Password123", "Users Admin Get"
    )
    set_user_role("users_admin_get@example.com", "admin")
    admin_token = login_user(client, "users_admin_get@example.com", "Password123")

    register_user(
        client, "target_user_get@example.com", "Password123", "Target User Get"
    )
    target = get_user("target_user_get@example.com")
    assert target is not None

    response = client.get(f"/users/{target.id}", headers=auth_headers(admin_token))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "target_user_get@example.com"


def test_admin_get_user_by_id_not_found(client):
    register_user(client, "users_admin_nf@example.com", "Password123", "Users Admin NF")
    set_user_role("users_admin_nf@example.com", "admin")
    admin_token = login_user(client, "users_admin_nf@example.com", "Password123")

    response = client.get("/users/999999", headers=auth_headers(admin_token))
    assert response.status_code == 404, response.text


def test_admin_can_update_user(client):
    register_user(
        client, "users_admin_update@example.com", "Password123", "Users Admin Update"
    )
    set_user_role("users_admin_update@example.com", "admin")
    admin_token = login_user(client, "users_admin_update@example.com", "Password123")

    register_user(client, "target_user_update@example.com", "Password123", "Old Name")
    target = get_user("target_user_update@example.com")
    assert target is not None

    response = client.patch(
        f"/users/{target.id}",
        json={"name": "Updated Name"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Name"


def test_admin_update_user_not_found(client):
    register_user(
        client,
        "users_admin_update_nf@example.com",
        "Password123",
        "Users Admin Update NF",
    )
    set_user_role("users_admin_update_nf@example.com", "admin")
    admin_token = login_user(client, "users_admin_update_nf@example.com", "Password123")

    response = client.patch(
        "/users/999999",
        json={"name": "Missing"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404, response.text


def test_admin_can_change_user_role(client):
    register_user(
        client, "users_admin_role@example.com", "Password123", "Users Admin Role"
    )
    set_user_role("users_admin_role@example.com", "admin")
    admin_token = login_user(client, "users_admin_role@example.com", "Password123")

    register_user(
        client, "target_user_role@example.com", "Password123", "Target User Role"
    )
    target = get_user("target_user_role@example.com")
    assert target is not None

    response = client.patch(
        f"/users/{target.id}/role",
        json={"role": "admin"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["role"] == "admin"


def test_admin_can_delete_user(client):
    register_user(
        client, "users_admin_delete@example.com", "Password123", "Users Admin Delete"
    )
    set_user_role("users_admin_delete@example.com", "admin")
    admin_token = login_user(client, "users_admin_delete@example.com", "Password123")

    register_user(
        client, "target_user_delete@example.com", "Password123", "Target User Delete"
    )
    target = get_user("target_user_delete@example.com")
    assert target is not None

    response = client.delete(
        f"/users/{target.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 204, response.text

    missing = client.get(f"/users/{target.id}", headers=auth_headers(admin_token))
    assert missing.status_code == 404, missing.text


def test_non_admin_cannot_manage_users(client):
    register_user(client, "normal_manager@example.com", "Password123", "Normal Manager")
    normal_token = login_user(client, "normal_manager@example.com", "Password123")

    register_user(client, "normal_target@example.com", "Password123", "Normal Target")
    target = get_user("normal_target@example.com")
    assert target is not None

    response_get = client.get(f"/users/{target.id}", headers=auth_headers(normal_token))
    assert response_get.status_code == 403, response_get.text

    response_patch = client.patch(
        f"/users/{target.id}",
        json={"name": "Nope"},
        headers=auth_headers(normal_token),
    )
    assert response_patch.status_code == 403, response_patch.text

    response_role = client.patch(
        f"/users/{target.id}/role",
        json={"role": "admin"},
        headers=auth_headers(normal_token),
    )
    assert response_role.status_code == 403, response_role.text

    response_delete = client.delete(
        f"/users/{target.id}",
        headers=auth_headers(normal_token),
    )
    assert response_delete.status_code == 403, response_delete.text
