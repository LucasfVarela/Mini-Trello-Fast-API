from datetime import date, timedelta


def _create_task(client, project_id, headers, **data):
    payload = {"title": "Tarea", **data}
    response = client.post(f"/api/v1/projects/{project_id}/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_task_defaults(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"], title="Armar modelos")
    assert task["status"] == "todo"
    assert task["priority"] == "medium"
    assert task["created_by"]["username"] == "alice"


def test_assignee_must_be_member(client, alice, bob, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Tarea", "assignee_id": bob["id"]},
        headers=alice["headers"],
    )
    assert response.status_code == 400


def test_update_task_status(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"])
    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "in_progress"},
        headers=alice["headers"],
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_task_rejects_null_title(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"])
    response = client.patch(f"/api/v1/tasks/{task['id']}", json={"title": None}, headers=alice["headers"])
    assert response.status_code == 422


def test_filters_search_and_pagination(client, alice, project):
    pid = project["id"]
    headers = alice["headers"]
    _create_task(client, pid, headers, title="Diseñar base de datos", priority="high")
    _create_task(client, pid, headers, title="Escribir README", status="done")
    _create_task(client, pid, headers, title="Diseñar endpoints", priority="low")

    url = f"/api/v1/projects/{pid}/tasks"
    assert client.get(url, params={"status": "done"}, headers=headers).json()["total"] == 1
    assert client.get(url, params={"priority": "high"}, headers=headers).json()["total"] == 1
    assert client.get(url, params={"search": "diseñar"}, headers=headers).json()["total"] == 2

    page = client.get(url, params={"size": 2, "page": 2}, headers=headers).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1

    ordered = client.get(
        url, params={"order_by": "priority", "direction": "desc"}, headers=headers
    ).json()["items"]
    assert [t["priority"] for t in ordered] == ["high", "medium", "low"]


def test_overdue_filter(client, alice, project):
    pid = project["id"]
    headers = alice["headers"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    _create_task(client, pid, headers, title="Vencida", due_date=yesterday)
    _create_task(client, pid, headers, title="Vencida pero hecha", due_date=yesterday, status="done")
    _create_task(client, pid, headers, title="A tiempo", due_date=tomorrow)

    response = client.get(f"/api/v1/projects/{pid}/tasks", params={"overdue": True}, headers=headers)
    assert [t["title"] for t in response.json()["items"]] == ["Vencida"]


def test_board_groups_by_status(client, alice, project):
    pid = project["id"]
    headers = alice["headers"]
    _create_task(client, pid, headers, title="A")
    _create_task(client, pid, headers, title="B", status="in_progress")
    _create_task(client, pid, headers, title="C", status="done")
    _create_task(client, pid, headers, title="D", status="done")

    board = client.get(f"/api/v1/projects/{pid}/board", headers=headers).json()
    assert len(board["todo"]) == 1
    assert len(board["in_progress"]) == 1
    assert len(board["done"]) == 2


def test_my_tasks(client, alice, bob, project):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"username": "bob"},
        headers=alice["headers"],
    )
    _create_task(client, project["id"], alice["headers"], title="Para Bob", assignee_id=bob["id"])
    _create_task(client, project["id"], alice["headers"], title="Sin asignar")

    response = client.get("/api/v1/tasks/me", headers=bob["headers"])
    assert [t["title"] for t in response.json()] == ["Para Bob"]


def test_outsider_cannot_access_task(client, alice, bob, project):
    task = _create_task(client, project["id"], alice["headers"])
    assert client.get(f"/api/v1/tasks/{task['id']}", headers=bob["headers"]).status_code == 404


def test_only_creator_or_owner_can_delete(client, register_user, alice, bob, project):
    carla = register_user("carla")
    url = f"/api/v1/projects/{project['id']}/members"
    client.post(url, json={"username": "bob"}, headers=alice["headers"])
    client.post(url, json={"username": "carla"}, headers=alice["headers"])

    task = _create_task(client, project["id"], bob["headers"])
    assert client.delete(f"/api/v1/tasks/{task['id']}", headers=carla["headers"]).status_code == 403
    assert client.delete(f"/api/v1/tasks/{task['id']}", headers=alice["headers"]).status_code == 204
