def test_create_and_list_projects(client, alice, project):
    response = client.get("/api/v1/projects", headers=alice["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["owner"]["username"] == "alice"


def test_other_user_cannot_see_project(client, bob, project):
    assert client.get("/api/v1/projects", headers=bob["headers"]).json() == []
    response = client.get(f"/api/v1/projects/{project['id']}", headers=bob["headers"])
    assert response.status_code == 404


def test_add_member_gives_access(client, alice, bob, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"username": "bob"},
        headers=alice["headers"],
    )
    assert response.status_code == 201
    assert [m["username"] for m in response.json()["members"]] == ["bob"]

    response = client.get(f"/api/v1/projects/{project['id']}", headers=bob["headers"])
    assert response.status_code == 200


def test_add_member_twice(client, alice, bob, project):
    url = f"/api/v1/projects/{project['id']}/members"
    client.post(url, json={"username": "bob"}, headers=alice["headers"])
    response = client.post(url, json={"username": "bob"}, headers=alice["headers"])
    assert response.status_code == 409


def test_add_unknown_member(client, alice, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"username": "nadie"},
        headers=alice["headers"],
    )
    assert response.status_code == 404


def test_member_cannot_edit_or_delete_project(client, alice, bob, project):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"username": "bob"},
        headers=alice["headers"],
    )
    url = f"/api/v1/projects/{project['id']}"
    assert client.patch(url, json={"name": "Otro"}, headers=bob["headers"]).status_code == 403
    assert client.delete(url, headers=bob["headers"]).status_code == 403


def test_update_and_delete_project(client, alice, project):
    url = f"/api/v1/projects/{project['id']}"
    response = client.patch(url, json={"name": "Nuevo nombre"}, headers=alice["headers"])
    assert response.status_code == 200
    assert response.json()["name"] == "Nuevo nombre"

    assert client.delete(url, headers=alice["headers"]).status_code == 204
    assert client.get(url, headers=alice["headers"]).status_code == 404


def test_remove_member_unassigns_tasks(client, alice, bob, project):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"username": "bob"},
        headers=alice["headers"],
    )
    task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Tarea de Bob", "assignee_id": bob["id"]},
        headers=alice["headers"],
    ).json()

    response = client.delete(
        f"/api/v1/projects/{project['id']}/members/{bob['id']}",
        headers=alice["headers"],
    )
    assert response.status_code == 200
    assert response.json()["members"] == []

    task = client.get(f"/api/v1/tasks/{task['id']}", headers=alice["headers"]).json()
    assert task["assignee"] is None
