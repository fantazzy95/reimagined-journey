from __future__ import annotations


class StockService:
    def __init__(self, db):
        self.db = db

    def get_stock_balances(self, query: str = "") -> list[dict]:
        pattern = f"%{query.strip()}%"
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id AS product_id,
                       p.name AS product_name,
                       p.sku,
                       COALESCE(SUM(
                           CASE
                               WHEN sm.movement_type IN ('receipt', 'stock_in') THEN sm.quantity
                               WHEN sm.movement_type IN ('sale', 'stock_out') THEN -sm.quantity
                               ELSE 0
                           END
                       ), 0) AS balance
                FROM products p
                LEFT JOIN stock_movements sm ON sm.product_id = p.id
                WHERE p.is_active = 1
                  AND (
                        ? = ''
                        OR p.name LIKE ?
                        OR COALESCE(p.sku, '') LIKE ?
                        OR COALESCE(p.barcode, '') LIKE ?
                      )
                GROUP BY p.id, p.name, p.sku
                ORDER BY p.name
                LIMIT 500
                """,
                (query.strip(), pattern, pattern, pattern),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_product_movements(self, product_id: int) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT movement_type, quantity, note, document_date, created_at
                FROM stock_movements
                WHERE product_id = ?
                ORDER BY document_date DESC, id DESC
                LIMIT 300
                """,
                (product_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_balance(self, product_id: int) -> float:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(
                    CASE
                        WHEN movement_type IN ('receipt', 'stock_in') THEN quantity
                        WHEN movement_type IN ('sale', 'stock_out') THEN -quantity
                        ELSE 0
                    END
                ), 0) AS balance
                FROM stock_movements
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchone()
            return float(row["balance"] if row else 0)
