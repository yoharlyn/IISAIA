from fastapi.testclient import TestClient


def test_products_only_include_active_and_serialize_implant(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/products?page_size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {"page": 1, "page_size": 1, "total_items": 2, "total_pages": 2}
    assert len(body["items"]) == 1
    assert {category["name"] for category in body["available_categories"]} == {
        "Implantes",
        "Instrumental",
    }
    all_items = authenticated_client.get("/api/v1/products?page_size=100").json()["items"]
    assert "Producto oculto" not in {item["name"] for item in all_items}
    implant = next(item for item in all_items if item["is_implant"])
    assert implant["price_cents"] == 120000
    assert implant["implant_specs"]["diameter_mm"] == "3.50"


def test_search_and_filters(authenticated_client: TestClient) -> None:
    search = authenticated_client.get("/api/v1/products?q=oraltech").json()
    assert [item["sku"] for item in search["items"]] == ["INS-001"]
    implants = authenticated_client.get("/api/v1/products?is_implant=true").json()
    assert implants["pagination"]["total_items"] == 1
    assert all(item["is_implant"] for item in implants["items"])
    category_id = next(
        category["id"]
        for category in implants["available_categories"]
        if category["name"] == "Instrumental"
    )
    filtered = authenticated_client.get(f"/api/v1/products?category_id={category_id}").json()
    assert [item["sku"] for item in filtered["items"]] == ["INS-001"]


def test_pagination_validation(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/api/v1/products?page=0&page_size=101")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
