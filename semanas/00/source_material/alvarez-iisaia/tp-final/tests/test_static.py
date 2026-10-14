def test_home_is_served_by_fastapi(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Coffee Atlas" in response.text


def test_fastapi_documentation_is_registered_before_static_files(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
