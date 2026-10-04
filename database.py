import sqlite3
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "food_expiry.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'Other',
                manufacturing_date TEXT,
                expiry_date TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                storage TEXT DEFAULT '',
                image_filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def add_product(name, category, manufacturing_date, expiry_date,
                quantity, storage, image_filename=None):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO products
            (name, category, manufacturing_date, expiry_date, quantity, storage, image_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, category, manufacturing_date, expiry_date, quantity, storage, image_filename),
        )
        conn.commit()


def get_products():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM products ORDER BY expiry_date ASC").fetchall()


def delete_product(product_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def product_status(expiry_date, reminder_days=7):
    expiry = date.fromisoformat(expiry_date)
    days = (expiry - date.today()).days
    if days < 0:
        return "Expired", days
    if days <= reminder_days:
        return "Near Expiry", days
    return "Fresh", days
