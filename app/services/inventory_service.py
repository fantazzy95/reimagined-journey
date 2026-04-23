from __future__ import annotations

from datetime import datetime


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
        return round(price * rate, 2)

    def create_sale_document(self, items: list[dict], doc_date: str | None = None):
        doc_date = doc_date or datetime.now().strftime("%Y-%m-%d")

        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO documents(doc_type, doc_date) VALUES (?, ?)",
                ("sale", doc_date),
            )
            doc_id = cursor.lastrowid

            total_uah = 0

            for item in items:
                price = item["price"]
                currency_id = item["currency_id"]
                quantity = item["quantity"]

                rate = self.get_currency_rate(currency_id, doc_date)
                price_uah = round(price * rate, 2)
                line_total = price * quantity
                line_total_uah = price_uah * quantity

                total_uah += line_total_uah

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
