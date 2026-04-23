from __future__ import annotations

from datetime import datetime

from app.core.money import money_round


class InventoryService:
    def __init__(self, db):
        self.db = db

    def get_currency_rate(self, currency_id: int, date: str) -> float:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT rate_to_uah
                FROM currency_rates
                WHERE currency_id = ? AND rate_date <= ?
                ORDER BY rate_date DESC
                LIMIT 1
                """,
                (currency_id, date),
            ).fetchone()

            if not row:
                return 1.0

            return row["rate_to_uah"]

    def calculate_price_uah(self, price: float, currency_id: int, date: str) -> float:
        rate = self.get_currency_rate(currency_id, date)
        return money_round(price * rate)

    def search_products(self, query: str = "") -> list[dict]:
        pattern = f"%{query.strip()}%"
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.sku, p.barcode, p.sale_price, c.code AS currency_code
                FROM products p
                JOIN currencies c ON c.id = p.sale_currency_id
                WHERE p.is_active = 1
                  AND (
                        ? = ''
                        OR p.name LIKE ?
                        OR COALESCE(p.sku, '') LIKE ?
                        OR COALESCE(p.barcode, '') LIKE ?
                      )
                ORDER BY p.name
                LIMIT 200
                """,
                (query.strip(), pattern, pattern, pattern),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_product(self, product_id: int) -> dict | None:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT p.id, p.name, p.sku, p.barcode, p.sale_price, p.sale_currency_id, c.code AS currency_code
                FROM products p
                JOIN currencies c ON c.id = p.sale_currency_id
                WHERE p.id = ?
                """,
                (product_id,),
            ).fetchone()
            return dict(row) if row else None

    def create_sale_document(self, items: list[dict], doc_date: str | None = None):
        doc_date = doc_date or datetime.now().strftime("%Y-%m-%d")

        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO documents(doc_type, doc_date) VALUES (?, ?)",
                ("sale", doc_date),
            )
            doc_id = cursor.lastrowid

            total_uah = 0.0

            for item in items:
                price = item["price"]
                currency_id = item["currency_id"]
                quantity = item["quantity"]

                rate = self.get_currency_rate(currency_id, doc_date)
                price_uah = money_round(price * rate)
                line_total = money_round(price * quantity)
                line_total_uah = money_round(price_uah * quantity)

                total_uah = money_round(total_uah + line_total_uah)

                cursor.execute(
                    """
                    INSERT INTO document_items(
                        document_id, product_id, quantity,
                        price, currency_id, currency_rate,
                        price_uah, line_total, line_total_uah
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        item["product_id"],
                        quantity,
                        price,
                        currency_id,
                        rate,
                        price_uah,
                        line_total,
                        line_total_uah,
                    ),
                )

            cursor.execute(
                "UPDATE documents SET total_amount_uah = ? WHERE id = ?",
                (total_uah, doc_id),
            )

            return doc_id
