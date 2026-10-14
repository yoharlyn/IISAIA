from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import event

from backend.models import VisitPhoto
from backend.uploads import MAX_FILE_BYTES


def _login(client: TestClient, code: str):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )
    payload = client.get("/api/session").json()
    client.headers.update(
        {
            "Origin": "http://127.0.0.1:8000",
            "X-CSRF-Token": payload["csrf_token"],
        }
    )


def _visit(client: TestClient) -> tuple[int, int]:
    cafe_id = client.get("/api/cafes").json()[0]["id"]
    visit = client.post(
        f"/api/cafes/{cafe_id}/visits",
        json={"note": "Visita con fotos"},
    ).json()
    return cafe_id, visit["id"]


def _image_bytes(
    image_format: str = "PNG",
    *,
    size: tuple[int, int] = (32, 24),
    animated: bool = False,
) -> bytes:
    output = BytesIO()
    first = Image.new("RGB" if image_format != "PNG" else "RGBA", size, "#8f3e2e")
    if animated:
        second = Image.new("RGB", size, "#48533a")
        first.convert("RGB").save(
            output,
            format=image_format,
            save_all=True,
            append_images=[second],
            duration=100,
            loop=0,
        )
    else:
        first.save(output, format=image_format)
    return output.getvalue()


def _upload(client: TestClient, visit_id: int, *, name="photo.png", content=None, mime="image/png", caption="Mesa junto a la ventana"):
    return client.post(
        f"/api/visits/{visit_id}/photos",
        files={"file": (name, content or _image_bytes(), mime)},
        data={"caption": caption},
    )


def test_private_photo_upload_read_list_and_delete_use_generated_paths(client, app):
    cafe_id, visit_id = _visit(client)
    response = _upload(client, visit_id, name="../../escape.png")
    assert response.status_code == 201
    photo = response.json()
    assert photo["caption"] == "Mesa junto a la ventana"
    assert photo["mime_type"] == "image/png"
    assert photo["width"] == 32
    assert photo["height"] == 24
    assert "internal_name" not in photo
    assert "sha256" not in photo

    root = Path(app.state.upload_dir)
    stored = [path for path in root.rglob("*.png") if ".quarantine" not in path.parts]
    assert len(stored) == 1
    assert stored[0].parent == root / "1" / str(visit_id)
    assert stored[0].name != "escape.png"

    downloaded = client.get(photo["url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("image/png")
    assert downloaded.headers["cache-control"] == "private, no-store"

    visits = client.get(f"/api/cafes/{cafe_id}/visits").json()
    listed = next(row for row in visits if row["id"] == visit_id)
    assert listed["photos"] == [photo]

    assert client.delete(photo["url"]).status_code == 204
    assert client.get(photo["url"]).status_code == 404
    assert not stored[0].exists()


def test_photo_validation_limits_and_missing_file_fallback(client, app, monkeypatch):
    _, visit_id = _visit(client)
    assert _upload(client, visit_id, content=b"not-an-image").status_code == 422
    assert _upload(
        client,
        visit_id,
        name="mismatch.jpg",
        content=_image_bytes("PNG"),
        mime="image/jpeg",
    ).status_code == 422
    assert _upload(
        client,
        visit_id,
        content=b"x" * (MAX_FILE_BYTES + 1),
    ).status_code == 422
    assert _upload(
        client,
        visit_id,
        content=_image_bytes("PNG", size=(5000, 5000)),
    ).status_code == 422
    assert _upload(
        client,
        visit_id,
        name="animated.webp",
        content=_image_bytes("WEBP", animated=True),
        mime="image/webp",
    ).status_code == 422
    assert _upload(client, visit_id, caption="   ").status_code == 422

    monkeypatch.setattr("backend.photo_routes.MAX_VISIT_BYTES", 1)
    assert _upload(client, visit_id).status_code == 409
    monkeypatch.undo()

    created = _upload(client, visit_id).json()
    root = Path(app.state.upload_dir)
    stored = next(path for path in root.rglob("*.png") if ".quarantine" not in path.parts)
    stored.unlink()
    missing = client.get(created["url"])
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Archivo de fotografía no disponible."


def test_photo_count_ownership_and_upload_rollback(client, app):
    _, visit_id = _visit(client)
    created = [_upload(client, visit_id).json() for _ in range(5)]
    assert _upload(client, visit_id).status_code == 409

    with TestClient(app, base_url="http://127.0.0.1:8000") as second:
        _login(second, "second")
        assert second.get(created[0]["url"]).status_code == 404
        assert second.delete(created[0]["url"]).status_code == 404
        assert _upload(second, visit_id).status_code == 404

    _, rollback_visit = _visit(client)
    def fail_insert(_mapper, _connection, _target):
        raise RuntimeError("fallo simulado")

    event.listen(VisitPhoto, "before_insert", fail_insert)
    try:
        failed = _upload(client, rollback_visit)
    finally:
        event.remove(VisitPhoto, "before_insert", fail_insert)
    assert failed.status_code == 500
    rollback_dir = Path(app.state.upload_dir) / "1" / str(rollback_visit)
    assert not rollback_dir.exists() or not list(rollback_dir.iterdir())
