
import sqlite3
from flask import Blueprint, request, jsonify

menu_bp = Blueprint("menu", __name__)


# Add a menu item
@menu_bp.route("/menu", methods=["POST"])
def add_menu_item():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Please provide menu details"}), 400

    name = data.get("name")
    price = data.get("price")
    category = data.get("category")

    if isinstance(name, str):
        name = name.strip()

    if isinstance(category, str):
        category = category.strip()

    if not name or price is None or not category:
        return jsonify({
            "error": "Name, price and category are required"
        }), 400

    if (
        not isinstance(price, (int, float))
        or isinstance(price, bool)
        or price <= 0
    ):
        return jsonify({"error": "Price must be a positive number"}), 400

    conn = sqlite3.connect("kitchen.db")

    conn.execute(
        """
        INSERT INTO menu_items (name, price, category)
        VALUES (?, ?, ?)
        """,
        (name, price, category)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Menu item added successfully"
    }), 201



# Get all menu items
@menu_bp.route("/menu", methods=["GET"])
def get_menu():
    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    items = conn.execute(
        "SELECT * FROM menu_items ORDER BY id ASC"
    ).fetchall()

    conn.close()

    menu = [dict(item) for item in items]

    return jsonify(menu), 200


# Get only available menu items
@menu_bp.route("/menu/active", methods=["GET"])
def get_active_menu():
    conn = sqlite3.connect("kitchen.db")
    conn.row_factory = sqlite3.Row

    items = conn.execute(
        "SELECT * FROM menu_items WHERE available = 1 ORDER BY id ASC"
    ).fetchall()

    conn.close()

    menu = [dict(item) for item in items]

    return jsonify(menu), 200

# Update menu item availability
@menu_bp.route("/menu/<int:item_id>/availability", methods=["PATCH"])
def update_menu_availability(item_id):
    data = request.get_json()

    if not data or "available" not in data:
        return jsonify({"error": "Please provide availability"}), 400

    available = data["available"]

    if not isinstance(available, bool):
        return jsonify({
            "error": "Availability must be true or false"
        }), 400

    conn = sqlite3.connect("kitchen.db")

    item = conn.execute(
        "SELECT id FROM menu_items WHERE id = ?", (item_id,)
    ).fetchone()

    if item is None:
        conn.close()
        return jsonify({"error": "Menu item not found"}), 404

    conn.execute(
        "UPDATE menu_items SET available = ? WHERE id = ?",
        (int(available), item_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Availability updated successfully",
        "available": available
    }), 200

