
import sqlite3
import pytest

from backend.app import app
from backend.database import init_db




@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a separate database for every test
    monkeypatch.chdir(tmp_path)
    init_db()

    # Clear sample data from the test database
    conn = sqlite3.connect("kitchen.db")
    conn.execute("DELETE FROM order_items")
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM menu_items")
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name = 'menu_items'"
    )
    conn.commit()
    conn.close()

    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def add_menu_item(client, name="Paneer Tikka", price=180, category="Appetizer"):
    return client.post("/api/menu", json={
        "name": name,
        "price": price,
        "category": category
    })


def test_add_menu_item(client):
    response = add_menu_item(client)

    assert response.status_code == 201
    assert response.json["message"] == "Menu item added successfully"


def test_active_menu(client):
    add_menu_item(client)

    response = client.get("/api/menu/active")

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["name"] == "Paneer Tikka"


def test_order_total(client):
    add_menu_item(client)

    response = client.post("/api/orders", json={
        "items": [
            {"menu_item_id": 1, "quantity": 2}
        ]
    })

    assert response.status_code == 201
    assert response.json["total"] == 360
    assert response.json["status"] == "Received"


def test_reject_unavailable_item(client):
    add_menu_item(client)

    conn = sqlite3.connect("kitchen.db")
    conn.execute(
        "UPDATE menu_items SET available = 0 WHERE id = 1"
    )
    conn.commit()
    conn.close()

    response = client.post("/api/orders", json={
        "items": [
            {"menu_item_id": 1, "quantity": 1}
        ]
    })

    assert response.status_code == 400
    assert "error" in response.json


def test_order_status_progression(client):
    add_menu_item(client)

    response = client.post("/api/orders", json={
        "items": [
            {"menu_item_id": 1, "quantity": 1}
        ]
    })

    order_id = response.json["order_id"]

    # Received -> Cooking
    response = client.patch(
        f"/api/orders/{order_id}/status"
    )
    assert response.status_code == 200
    assert response.json["status"] == "Cooking"

    # Cooking -> Served
    response = client.patch(
        f"/api/orders/{order_id}/status"
    )
    assert response.status_code == 200
    assert response.json["status"] == "Served"

    # Served -> another status must be rejected
    response = client.patch(
        f"/api/orders/{order_id}/status"
    )
    assert response.status_code == 400


def test_update_menu_availability(client):
    add_menu_item(client)

    response = client.patch(
        "/api/menu/1/availability",
        json={"available": False}
    )

    assert response.status_code == 200
    assert response.json["available"] is False

    response = client.get("/api/menu/active")
    assert len(response.json) == 0


def test_reject_zero_quantity(client):
    add_menu_item(client)

    response = client.post("/api/orders", json={
        "items": [
            {"menu_item_id": 1, "quantity": 0}
        ]
    })

    assert response.status_code == 400
    assert "error" in response.json


def test_reject_duplicate_menu_items(client):
    add_menu_item(client)

    response = client.post("/api/orders", json={
        "items": [
            {"menu_item_id": 1, "quantity": 1},
            {"menu_item_id": 1, "quantity": 2}
        ]
    })

    assert response.status_code == 400
    assert response.json["error"] == "Duplicate menu items are not allowed"


def test_reject_missing_order_items(client):
    response = client.post("/api/orders", json={})

    assert response.status_code == 400
    assert response.json["error"] == "Please provide order items"


def test_reject_invalid_json(client):
    response = client.post(
        "/api/orders",
        data="invalid json",
        content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json["error"] == "Please provide valid JSON"

