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
    assert 'class="stats-grid"' not in response.text
    assert 'id="stat-total"' not in response.text


def test_only_the_configured_host_is_accepted(client):
    accepted = client.get("/", headers={"Host": "127.0.0.1:8000"})
    rejected = client.get("/", headers={"Host": "localhost:8000"})

    assert accepted.status_code == 200
    assert rejected.status_code == 400


def test_security_headers_allow_only_the_required_google_maps_origins(client):
    response = client.get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-frame-options"] == "DENY"
    policy = response.headers["content-security-policy"]
    assert "default-src 'self'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    assert "https://*.googleapis.com" in policy
    assert "https://*.gstatic.com" in policy
    assert "https://*.google.com" in policy
    assert "https://*.googleusercontent.com" in policy
    assert "img-src 'self' data: http: https:" in policy
    assert "*;" not in policy


def test_terms_and_privacy_pages_are_accessible_and_linked(client):
    home = client.get("/")
    terms = client.get("/terms.html")
    privacy = client.get("/privacy.html")

    assert terms.status_code == 200
    assert privacy.status_code == 200
    assert '<html lang="es">' in terms.text
    assert '<html lang="es">' in privacy.text
    assert '<main class="legal-main">' in terms.text
    assert '<main class="legal-main">' in privacy.text
    assert 'href="/terms.html"' in home.text
    assert 'href="/privacy.html"' in home.text
    assert 'href="/privacy.html"' in terms.text
    assert 'href="/terms.html"' in privacy.text
    assert "Auth0" in privacy.text
    assert "Google Maps" in privacy.text
    assert "ubicación" in privacy.text.lower()
    assert "fotografías" in privacy.text.lower()
    assert "contacto@" not in terms.text + privacy.text


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
    assert "chart-grid-line" in dashboard_module.text
    assert "chart-month-label" in dashboard_module.text
    assert "chart-value-label" in dashboard_module.text
    assert "chart-summary" in dashboard_module.text
    assert "chart-legend" in dashboard_module.text
    assert "chart-empty" in dashboard_module.text
    assert "data-month" in dashboard_module.text
    assert "data-count" in dashboard_module.text
    assert "innerHTML" not in dashboard_module.text
    assert "getDashboard" in api_module.text
    assert "getNeighborhoods" in api_module.text
    assert 'neighborhoodGroup("Barrios oficiales"' in ui_module.text
    assert 'neighborhoodGroup("Valores históricos"' in ui_module.text
    assert "getStats" not in api_module.text
    assert "getStats" not in app_module.text
    assert "renderStats" not in ui_module.text
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
