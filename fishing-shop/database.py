import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "store.db"

DEFAULT_CATEGORIES = [
    ("Прикормки", "prikormky"),
    ("Ароматизатори", "aromatyzatory"),
    ("Добавки", "dobavky"),
    ("Набори", "nabory"),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            weight TEXT DEFAULT '',
            category_id INTEGER,
            is_active INTEGER DEFAULT 1,
            is_featured INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            icon TEXT DEFAULT '🔗',
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """
    )
    existing = {row[1] for row in conn.execute("PRAGMA table_info(categories)").fetchall()}
    if "sort_order" not in existing:
        conn.execute("ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0")
    for name, slug in DEFAULT_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, slug) VALUES (?, ?)",
            (name, slug),
        )
    conn.commit()
    conn.close()
