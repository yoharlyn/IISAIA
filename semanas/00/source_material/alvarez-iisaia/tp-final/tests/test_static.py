def test_home_is_served_by_fastapi(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Coffee Atlas" in response.text
    assert "<main>" in response.text
    assert 'aria-live="polite"' in response.text
    assert '<dialog id="cafe-dialog"' in response.text
    assert '<dialog id="delete-dialog"' in response.text


def test_fastapi_documentation_is_registered_before_static_files(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_frontend_assets_are_served(client):
    stylesheet = client.get("/css/styles.css")
    api_module = client.get("/js/api.js")
    app_module = client.get("/js/app.js")
    ui_module = client.get("/js/ui.js")

    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert ":focus-visible" in stylesheet.text
    assert api_module.status_code == 200
    assert "export function listCafes" in api_module.text
    assert app_module.status_code == 200
    assert ui_module.status_code == 200
    assert "createCafe" in app_module.text
    assert "textContent" in ui_module.text
