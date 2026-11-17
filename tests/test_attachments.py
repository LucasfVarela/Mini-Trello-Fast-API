from pathlib import Path

from app.core.config import settings


def _create_task(client, project_id, headers):
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Con adjunto"},
        headers=headers,
    )
    return response.json()


def _upload(client, task_id, headers, name="notas.txt", content=b"hola", content_type="text/plain"):
    return client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        files={"file": (name, content, content_type)},
        headers=headers,
    )


def test_upload_list_download_delete(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"])

    response = _upload(client, task["id"], alice["headers"])
    assert response.status_code == 201
    attachment = response.json()
    assert attachment["original_name"] == "notas.txt"
    assert attachment["size"] == 4

    listed = client.get(f"/api/v1/tasks/{task['id']}/attachments", headers=alice["headers"]).json()
    assert len(listed) == 1

    download = client.get(f"/api/v1/attachments/{attachment['id']}/download", headers=alice["headers"])
    assert download.status_code == 200
    assert download.content == b"hola"

    assert client.delete(f"/api/v1/attachments/{attachment['id']}", headers=alice["headers"]).status_code == 204
    assert list(Path(settings.upload_dir).iterdir()) == []


def test_rejects_unsupported_type(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"])
    response = _upload(client, task["id"], alice["headers"], name="virus.exe", content_type="application/x-msdownload")
    assert response.status_code == 415


def test_rejects_large_file(client, alice, project, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_mb", 1)
    task = _create_task(client, project["id"], alice["headers"])
    response = _upload(client, task["id"], alice["headers"], content=b"x" * (1024 * 1024 + 1))
    assert response.status_code == 413
    assert list(Path(settings.upload_dir).iterdir()) == []


def test_deleting_task_removes_files(client, alice, project):
    task = _create_task(client, project["id"], alice["headers"])
    _upload(client, task["id"], alice["headers"])
    assert len(list(Path(settings.upload_dir).iterdir())) == 1

    client.delete(f"/api/v1/tasks/{task['id']}", headers=alice["headers"])
    assert list(Path(settings.upload_dir).iterdir()) == []


def test_outsider_cannot_download(client, alice, bob, project):
    task = _create_task(client, project["id"], alice["headers"])
    attachment = _upload(client, task["id"], alice["headers"]).json()
    response = client.get(f"/api/v1/attachments/{attachment['id']}/download", headers=bob["headers"])
    assert response.status_code == 404
