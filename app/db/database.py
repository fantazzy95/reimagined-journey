from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "inventory.db") -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS currencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    is_base INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS currency_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency_id INTEGER NOT NULL,
                    rate_to_uah REAL NOT NULL,
                    rate_date TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(currency_id) REFERENCES currencies(id)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_currency_rates_unique
                    ON currency_rates(currency_id, rate_date);

                CREATE TABLE IF NOT EXISTS warehouses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(parent_id) REFERENCES categories(id)
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sku TEXT,
                    barcode TEXT,
                    internal_code TEXT,
                    category_id INTEGER,
                    unit TEXT NOT NULL DEFAULT 'шт',
                    brand TEXT,
                    sale_price REAL NOT NULL DEFAULT 0,
                    sale_currency_id INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(category_id) REFERENCES categories(id),
                    FOREIGN KEY(sale_currency_id) REFERENCES currencies(id)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);

                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    movement_type TEXT NOT NULL,
                    warehouse_from_id INTEGER,
                    warehouse_to_id INTEGER,
                    quantity REAL NOT NULL,
                    note TEXT,
                    document_date TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES products(id),
                    FOREIGN KEY(warehouse_from_id) REFERENCES warehouses(id),
                    FOREIGN KEY(warehouse_to_id) REFERENCES warehouses(id)
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_type TEXT NOT NULL,
                    doc_number TEXT,
                    doc_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    currency_id INTEGER,
                    currency_rate REAL,
                    total_amount REAL DEFAULT 0,
                    total_amount_uah REAL DEFAULT 0,
                    note TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(currency_id) REFERENCES currencies(id)
                );

                CREATE TABLE IF NOT EXISTS document_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    currency_id INTEGER NOT NULL,
                    currency_rate REAL NOT NULL,
                    price_uah REAL NOT NULL,
                    line_total REAL NOT NULL,
                    line_total_uah REAL NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id),
                    FOREIGN KEY(currency_id) REFERENCES currencies(id)
                );
                """
            )

            conn.execute(
                "INSERT OR IGNORE INTO currencies(code, name, is_base) VALUES (?, ?, ?)",
                ("UAH", "Гривня", 1),
            )
            conn.execute(
                "INSERT OR IGNORE INTO currencies(code, name, is_base) VALUES (?, ?, ?)",
                ("USD", "Долар США", 0),
            )
            conn.execute(
                "INSERT OR IGNORE INTO currencies(code, name, is_base) VALUES (?, ?, ?)",
                ("EUR", "Євро", 0),
            )
