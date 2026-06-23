def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parse_endpoint(client):
    response = client.post(
        "/api/v1/parse",
        json={
            "message": "ভাই blue color এর XL shirt দুইটা কালকে আগের address এ পাঠাবেন",
            "parser_mode": "rule",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "shirt"
    assert data["quantity"] == 2
    assert data["missing_fields"] == []


def test_process_order_preview(client):
    response = client.post(
        "/api/v1/orders/process",
        json={
            "message": "blue XL shirt 2টা আগের address",
            "parser_mode": "rule",
            "commit": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready_to_create"


def test_process_order_create(client):
    response = client.post(
        "/api/v1/orders/process",
        json={
            "message": "blue XL shirt 2টা আগের address",
            "parser_mode": "rule",
            "commit": True,
            "idempotency_key": "api-order-1",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["order_id"] == 1
    assert len(data["tool_trace"]) == 4


def test_duplicate_response(client):
    payload = {
        "message": "blue XL shirt 2টা আগের address",
        "parser_mode": "rule",
        "commit": True,
        "idempotency_key": "same-key",
    }
    first = client.post("/api/v1/orders/process", json=payload)
    second = client.post("/api/v1/orders/process", json=payload)
    assert first.json()["status"] == "created"
    assert second.json()["status"] == "duplicate"
    assert second.json()["order_id"] == first.json()["order_id"]


def test_needs_information(client):
    response = client.post(
        "/api/v1/orders/process",
        json={"message": "কালকে পাঠাবেন", "parser_mode": "rule", "commit": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "needs_information"


def test_out_of_stock(client):
    response = client.post(
        "/api/v1/orders/process",
        json={
            "message": "hoodie 99টা address: Dhaka",
            "parser_mode": "rule",
            "commit": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "out_of_stock"


def test_list_orders(client):
    client.post(
        "/api/v1/orders/process",
        json={
            "message": "shirt 1টা address: Dhaka",
            "parser_mode": "rule",
            "commit": True,
            "idempotency_key": "list-order",
        },
    )
    response = client.get("/api/v1/orders")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_invoice_endpoint(client):
    created = client.post(
        "/api/v1/orders/process",
        json={
            "message": "shirt 1টা address: Dhaka",
            "parser_mode": "rule",
            "commit": True,
            "idempotency_key": "invoice-api",
        },
    ).json()
    response = client.get(f"/api/v1/invoices/{created['order_id']}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
