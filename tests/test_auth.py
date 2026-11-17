def test_register_and_me(client, alice):
    response = client.get("/api/v1/auth/me", headers=alice["headers"])
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_register_duplicate_username(client, alice):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "otra@example.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_register_invalid_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "carla", "email": "carla@example.com", "password": "corta"},
    )
    assert response.status_code == 422


def test_login_wrong_password(client, alice):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "incorrecta"},
    )
    assert response.status_code == 401


def test_protected_route_without_token(client):
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_protected_route_with_invalid_token(client):
    response = client.get("/api/v1/projects", headers={"Authorization": "Bearer token-falso"})
    assert response.status_code == 401
