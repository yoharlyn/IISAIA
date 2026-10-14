def test_home_is_served_by_fastapi(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Coffee Atlas" in response.text
    assert "<main" in response.text
    assert 'aria-live="polite"' in response.text
    assert '<dialog id="cafe-dialog"' in response.text
    assert '<dialog id="delete-dialog"' in response.text
    assert '<dialog id="visit-dialog"' in response.text
    assert 'id="visit-status"' in response.text
    assert 'aria-live="polite"' in response.text


def test_fastapi_documentation_is_registered_before_static_files(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_frontend_assets_are_served(client):
    stylesheet = client.get("/css/styles.css")
    api_module = client.get("/js/api.js")
    app_module = client.get("/js/app.js")
    ui_module = client.get("/js/ui.js")
    auth_module = client.get("/js/auth.js")
    map_module = client.get("/js/map.js")
    places_module = client.get("/js/places.js")
    recommendations_module = client.get("/js/recommendations.js")
    visits_module = client.get("/js/visits.js")
    dashboard_module = client.get("/js/dashboard.js")

    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert ":focus-visible" in stylesheet.text
    assert api_module.status_code == 200
    assert "export function listCafes" in api_module.text
    assert '"X-CSRF-Token"' in api_module.text
    assert auth_module.status_code == 200
    assert "initializeSession" in auth_module.text
    assert app_module.status_code == 200
    assert ui_module.status_code == 200
    assert "createCafe" in app_module.text
    assert "textContent" in ui_module.text
    assert map_module.status_code == 200
    assert "navigator.geolocation" in map_module.text
    assert "localStorage" not in map_module.text
    assert "sessionStorage" not in map_module.text
    assert 'id="atlas-map"' in client.get("/").text
    assert places_module.status_code == 200
    assert "PlaceAutocompleteElement" in places_module.text
    assert "gmp-select" in places_module.text
    assert "innerHTML" not in places_module.text
    assert recommendations_module.status_code == 200
    assert "textContent" in recommendations_module.text
    assert "Datos actuales de Google Maps" in recommendations_module.text
    assert "Cálculo para tu atlas" in recommendations_module.text
    assert "Antes de guardar" in recommendations_module.text
    assert "renderRecommendationsUnavailable" in recommendations_module.text
    assert "innerHTML" not in recommendations_module.text
    assert 'id="home-autocomplete"' in client.get("/").text
    assert 'id="cafe-autocomplete"' in client.get("/").text
    assert "provienen de Google Maps" in client.get("/").text
    assert "el cálculo determinístico" in client.get("/").text
    assert visits_module.status_code == 200
    assert "uploadVisitPhoto" in visits_module.text
    assert "textContent" in visits_module.text
    assert "innerHTML" not in visits_module.text
    assert "MAX_FILE_BYTES" in visits_module.text
    assert "MAX_PHOTOS" in visits_module.text
    assert "FormData" in api_module.text
    assert 'id="visit-form"' in client.get("/").text
    assert 'accept="image/jpeg,image/png,image/webp"' not in client.get("/").text
    assert dashboard_module.status_code == 200
    assert "createElementNS" in dashboard_module.text
    assert 'element("table"' in dashboard_module.text
    assert 'element("caption"' in dashboard_module.text
    assert "innerHTML" not in dashboard_module.text
    assert "getDashboard" in api_module.text
    assert 'id="dashboard-content"' in client.get("/").text
    assert 'aria-busy="true"' in client.get("/").text


def test_public_config_never_exposes_server_key(client, app):
    app.state.settings = app.state.settings.__class__(
        session_secret="t" * 32,
        google_maps_browser_key="browser-visible",
        google_maps_server_key="server-secret",
        google_map_id="map-id",
    ).validated()

    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {
        "google_maps_enabled": True,
        "google_maps_browser_key": "browser-visible",
        "google_map_id": "map-id",
    }
    assert "server-secret" not in response.text


def test_login_shell_contains_auth0_links_and_no_secrets(client):
    response = client.get("/")
    assert 'href="/auth/login"' in response.text
    assert 'href="/auth/signup"' in response.text
    assert 'id="logout-button"' in response.text
    assert "AUTH0_CLIENT_SECRET" not in response.text
    assert "SESSION_SECRET" not in response.text
