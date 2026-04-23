from __future__ import annotations

from datetime import datetime

from app.core.money import money_round
from app.services.pricing_service import PricingService


class PriceDocumentService:
    def __init__(self, db):
        self.db = db
        self.pricing_service = PricingService(db)

    def create_document(self, source_type: str = "manual", source_document_id: int | None = None, note: str | None = None) -> int:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO price_documents(doc_date, source_type, source_document_id, note) VALUES (?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d"), source_type, source_document_id, note),
            )
            return cursor.lastrowid

    def add_item(
        self,
        document_id: int,
        product_id: int,
        purchase_price: float,
        markup_percent: float,
        mode: str,
        supplier_price: float | None = None,
        currency_id: int | None = None,
        apply: bool = True,
    ) -> int:
        with self.db.connect() as conn:
            product = conn.execute(
                "SELECT sale_price, sale_currency_id FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
            if not product:
                raise ValueError(f"Product {product_id} not found")

            old_price = product["sale_price"]
            new_price = self.pricing_service.choose_price(
                mode=mode,
                purchase_price=purchase_price,
                markup_percent=markup_percent,
                supplier_price=supplier_price,
            )
            target_currency_id = currency_id or product["sale_currency_id"]

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO price_document_items(document_id, product_id, old_price, new_price, currency_id, applied)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, product_id, old_price, new_price, target_currency_id, 1 if apply else 0),
            )
            return cursor.lastrowid

    def get_document_items(self, document_id: int) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT pdi.id, pdi.document_id, pdi.product_id, p.name AS product_name, p.sku,
                       pdi.old_price, pdi.new_price, pdi.currency_id, pdi.applied
                FROM price_document_items pdi
                JOIN products p ON p.id = pdi.product_id
                WHERE pdi.document_id = ?
                ORDER BY p.name
                """,
                (document_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def apply_document(self, document_id: int) -> int:
        applied_count = 0
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, product_id, new_price, currency_id, applied
                FROM price_document_items
                WHERE document_id = ?
                """,
                (document_id,),
            ).fetchall()

            for row in rows:
                if not row["applied"]:
                    continue

                new_price = money_round(row["new_price"])
                conn.execute(
                    "UPDATE products SET sale_price = ?, sale_currency_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_price, row["currency_id"], row["product_id"]),
                )
                conn.execute(
                    "INSERT INTO price_history(product_id, price, currency_id, source) VALUES (?, ?, ?, ?)",
                    (row["product_id"], new_price, row["currency_id"], f"price_document:{document_id}"),
                )
                applied_count += 1

        return applied_count
