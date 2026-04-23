from __future__ import annotations

from datetime import datetime

from app.core.money import money_round


class ReceiptService:
    def __init__(self, db):
        self.db = db

    def create_receipt(self, doc_date: str | None = None, note: str | None = None, currency_id: int | None = None) -> int:
        doc_date = doc_date or datetime.now().strftime("%Y-%m-%d")
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents(doc_type, doc_date, status, currency_id, note)
                VALUES (?, ?, 'draft', ?, ?)
                """,
                ("receipt", doc_date, currency_id, note),
            )
            return cursor.lastrowid

    def add_item(self, document_id: int, product_id: int, quantity: float, price: float, currency_id: int, document_date: str | None = None) -> int:
        document_date = document_date or datetime.now().strftime("%Y-%m-%d")
        rate = self._get_currency_rate(currency_id, document_date)
        price_uah = money_round(price * rate)
        line_total = money_round(price * quantity)
        line_total_uah = money_round(price_uah * quantity)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO document_items(
                    document_id, product_id, quantity,
                    price, currency_id, currency_rate,
                    price_uah, line_total, line_total_uah
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    product_id,
                    quantity,
                    price,
                    currency_id,
                    rate,
                    price_uah,
                    line_total,
                    line_total_uah,
                ),
            )
            self._recalculate_document_totals(document_id)
            return cursor.lastrowid

    def get_document_items(self, document_id: int) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT di.id, di.product_id, p.name AS product_name, p.sku,
                       di.quantity, di.price, di.currency_id, di.line_total, di.line_total_uah
                FROM document_items di
                JOIN products p ON p.id = di.product_id
                WHERE di.document_id = ?
                ORDER BY di.id
                """,
                (document_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def post_receipt(self, document_id: int) -> int:
        moved = 0
        with self.db.connect() as conn:
            items = conn.execute(
                "SELECT product_id, quantity FROM document_items WHERE document_id = ?",
                (document_id,),
            ).fetchall()
            doc = conn.execute(
                "SELECT doc_date FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
            doc_date = doc["doc_date"] if doc else datetime.now().strftime("%Y-%m-%d")

            for item in items:
                conn.execute(
                    """
                    INSERT INTO stock_movements(product_id, movement_type, warehouse_to_id, quantity, note, document_date)
                    VALUES (?, 'receipt', NULL, ?, ?, ?)
                    """,
                    (item["product_id"], item["quantity"], f"receipt:{document_id}", doc_date),
                )
                moved += 1

            conn.execute("UPDATE documents SET status = 'posted' WHERE id = ?", (document_id,))
        return moved

    def _get_currency_rate(self, currency_id: int, date: str) -> float:
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
            return row["rate_to_uah"] if row else 1.0

    def _recalculate_document_totals(self, document_id: int) -> None:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(line_total), 0) AS total_amount,
                       COALESCE(SUM(line_total_uah), 0) AS total_amount_uah
                FROM document_items
                WHERE document_id = ?
                """,
                (document_id,),
            ).fetchone()
            conn.execute(
                "UPDATE documents SET total_amount = ?, total_amount_uah = ? WHERE id = ?",
                (money_round(row["total_amount"]), money_round(row["total_amount_uah"]), document_id),
            )
