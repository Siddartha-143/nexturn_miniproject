
import sqlite3


def init_db():
    conn = sqlite3.connect("kitchen.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Received'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
    """)

    # Add sample menu items if the menu is empty
    menu_count = conn.execute(
        "SELECT COUNT(*) FROM menu_items"
    ).fetchone()[0]

    if menu_count == 0:
        menu_items = [
            ("Paneer Tikka", 180, "Appetizer"),
            ("Chicken Biryani", 250, "Main Course"),
            ("Vegetable Samosa", 60, "Appetizer"),
            ("Masala Dosa", 120, "Main Course"),
            ("Gulab Jamun", 80, "Dessert"),
            ("Lime Soda", 50, "Beverage"),
        ]

        conn.executemany("""
            INSERT INTO menu_items (name, price, category)
            VALUES (?, ?, ?)
        """, menu_items)

    conn.commit()
    conn.close()

    print("Database created successfully")
