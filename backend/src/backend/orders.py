
import sqlite3
from flask import Blueprint, request, jsonify

orders_bp = Blueprint("orders", __name__)


# Place a new order
@orders_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Please provide valid JSON"}), 400

    if not isinstance(data.get("items"), list):
        return jsonify({"error": "Please provide order items"}), 400

    table_number = data.get("table_number")

    if (
        not isinstance(table_number, int)
        or isinstance(table_number, bool)
        or table_number <= 0
    ):
        return jsonify({
            "error": "Table number must be a positive integer"
        }), 400

    items = data["items"]

    if not items:
        return jsonify({
            "error": "Order must contain at least one item"
        }), 400

    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    try:
        total = 0
        order_items = []
        seen_menu_items = set()

        for item in items:
            if not isinstance(item, dict):
                return jsonify({
                    "error": "Each item must be an object"
                }), 400

            menu_item_id = item.get("menu_item_id")
            quantity = item.get("quantity")

            if (
                not isinstance(menu_item_id, int)
                or isinstance(menu_item_id, bool)
                or menu_item_id <= 0
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
                or quantity > 100
            ):
                return jsonify({
                    "error": (
                        "Each item needs a valid menu_item_id "
                        "and quantity between 1 and 100"
                    )
                }), 400

            if menu_item_id in seen_menu_items:
                return jsonify({
                    "error": "Duplicate menu items are not allowed"
                }), 400

            seen_menu_items.add(menu_item_id)

            menu_item = conn.execute(
                """
                SELECT * FROM menu_items
                WHERE id = ? AND available = 1
                """,
                (menu_item_id,)
            ).fetchone()

            if menu_item is None:
                return jsonify({
                    "error": (
                        f"Menu item {menu_item_id} is unavailable "
                        "or does not exist"
                    )
                }), 400

            price = menu_item["price"]
            total += price * quantity
            order_items.append((menu_item_id, quantity, price))

        cursor = conn.execute(
            """
            INSERT INTO orders (total, status, table_number)
            VALUES (?, ?, ?)
            """,
            (total, "Received", table_number)
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

        return jsonify({
            "message": "Order placed successfully",
            "order_id": order_id,
            "table_number": table_number,
            "total": round(total, 2),
            "status": "Received"
        }), 201

    except sqlite3.Error:
        conn.rollback()
        return jsonify({
            "error": "Unable to place order. Please try again."
        }), 500

    finally:
        conn.close()


# Get one order
@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if order is None:
            return jsonify({"error": "Order not found"}), 404

        items = conn.execute(
            """
            SELECT
                menu_items.name,
                order_items.quantity,
                order_items.price,
                order_items.quantity * order_items.price AS subtotal
            FROM order_items
            JOIN menu_items
                ON menu_items.id = order_items.menu_item_id
            WHERE order_items.order_id = ?
            """,
            (order_id,)
        ).fetchall()

        return jsonify({
            "order_id": order["id"],
            "table_number": order["table_number"],
            "total": order["total"],
            "status": order["status"],
            "items": [dict(item) for item in items]
        }), 200

    except sqlite3.Error:
        return jsonify({
            "error": "Unable to retrieve order details"
        }), 500

    finally:
        conn.close()


# Get all orders for the kitchen dashboard
@orders_bp.route("/orders", methods=["GET"])
def get_all_orders():
    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    try:
        orders = conn.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()

        result = []

        for order in orders:
            items = conn.execute(
                """
                SELECT
                    menu_items.name,
                    order_items.quantity,
                    order_items.price,
                    order_items.quantity * order_items.price AS subtotal
                FROM order_items
                JOIN menu_items
                    ON menu_items.id = order_items.menu_item_id
                WHERE order_items.order_id = ?
                """,
                (order["id"],)
            ).fetchall()

            result.append({
                "order_id": order["id"],
                "table_number": order["table_number"],
                "total": order["total"],
                "status": order["status"],
                "items": [dict(item) for item in items]
            })

        return jsonify(result), 200

    except sqlite3.Error:
        return jsonify({
            "error": "Unable to retrieve orders"
        }), 500

    finally:
        conn.close()


# Update order status
@orders_bp.route("/orders/<int:order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    conn = sqlite3.connect("kitchen.db")

    try:
        order = conn.execute(
            "SELECT status FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if order is None:
            return jsonify({"error": "Order not found"}), 404

        next_status = {
            "Received": "Cooking",
            "Cooking": "Served"
        }

        current_status = order[0]

        if current_status not in next_status:
            return jsonify({
                "error": "Order has already been served"
            }), 400

        new_status = next_status[current_status]

        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (new_status, order_id)
        )

        conn.commit()

        return jsonify({
            "message": "Order status updated successfully",
            "order_id": order_id,
            "status": new_status
        }), 200

    except sqlite3.Error:
        conn.rollback()
        return jsonify({
            "error": "Unable to update order status"
        }), 500

    finally:
        conn.close()
