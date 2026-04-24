from __future__ import annotations


class ProductService:
    def __init__(self, db):
        self.db = db

    def list_products(self, query: str = "") -> list[dict]:
        pattern = f"%{query.strip()}%"
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.sku, p.barcode, p.unit, p.sale_price,
                       c.code AS currency_code, p.is_active
                FROM products p
                JOIN currencies c ON c.id = p.sale_currency_id
                WHERE ? = ''
                   OR p.name LIKE ?
                   OR COALESCE(p.sku, '') LIKE ?
                   OR COALESCE(p.barcode, '') LIKE ?
                ORDER BY p.name
                LIMIT 500
                """,
                (query.strip(), pattern, pattern, pattern),
            ).fetchall()
            return [dict(row) for row in rows]

    def create_product(
        self,
        name: str,
        sku: str | None = None,
        barcode: str | None = None,
        sale_price: float = 0,
        currency_code: str = "UAH",
        unit: str = "шт",
    ) -> int:
        with self.db.connect() as conn:
            currency = conn.execute("SELECT id FROM currencies WHERE code = ?", (currency_code,)).fetchone()
            currency_id = currency["id"] if currency else 1
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO products(name, sku, barcode, unit, sale_price, sale_currency_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, sku or None, barcode or None, unit or "шт", sale_price, currency_id),
            )
            return cursor.lastrowid

    def list_currencies(self) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT id, code, name FROM currencies WHERE is_active = 1 ORDER BY code").fetchall()
            return [dict(row) for row in rows]
