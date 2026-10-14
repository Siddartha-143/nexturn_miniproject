
import sqlite3
from flask import Blueprint, request, jsonify

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json()

    if not data or not isinstance(data.get("items"), list):
        return jsonify({"error": "Please provide order items"}), 400

    items = data["items"]

    if not items:
        return jsonify({"error": "Order must contain at least one item"}), 400

    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    total = 0
    order_items = []

    for item in items:
        if not isinstance(item, dict):
            conn.close()
            return jsonify({"error": "Each item must be an object"}), 400

        menu_item_id = item.get("menu_item_id")
        quantity = item.get("quantity")

        if (
            not isinstance(menu_item_id, int)
            or isinstance(menu_item_id, bool)
            or not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            conn.close()
            return jsonify({
                "error": "Each item needs a valid menu_item_id and positive quantity"
            }), 400

        menu_item = conn.execute(
            "SELECT * FROM menu_items WHERE id = ? AND available = 1",
            (menu_item_id,)
        ).fetchone()

        if menu_item is None:
            conn.close()
            return jsonify({
                "error": f"Menu item {menu_item_id} is unavailable or does not exist"
            }), 400

        price = menu_item["price"]
        total += price * quantity

        order_items.append((menu_item_id, quantity, price))

    cursor = conn.execute(
        "INSERT INTO orders (total, status) VALUES (?, ?)",
        (total, "Received")
    )

    order_id = cursor.lastrowid

    for menu_item_id, quantity, price in order_items:
        conn.execute(
            """
            INSERT INTO order_items
            (order_id, menu_item_id, quantity, price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, menu_item_id, quantity, price)
        )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order_id,
        "total": round(total, 2),
        "status": "Received"
    }), 201


# Get order details
@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if order is None:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    items = conn.execute("""
        SELECT menu_items.name, order_items.quantity, order_items.price
        FROM order_items
        JOIN menu_items ON menu_items.id = order_items.menu_item_id
        WHERE order_items.order_id = ?
    """, (order_id,)).fetchall()

    conn.close()

    return jsonify({
        "order_id": order["id"],
        "total": order["total"],
        "status": order["status"],
        "items": [dict(item) for item in items]
    }), 200


# Update order status
@orders_bp.route("/orders/<int:order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    conn = sqlite3.connect("kitchen.db")

    order = conn.execute(
        "SELECT status FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if order is None:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    next_status = {
        "Received": "Cooking",
        "Cooking": "Served"
    }

    current_status = order[0]

    if current_status not in next_status:
        conn.close()
        return jsonify({
            "error": "Order has already been served"
        }), 400

    new_status = next_status[current_status]

    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (new_status, order_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order status updated successfully",
        "order_id": order_id,
        "status": new_status
    }), 200
