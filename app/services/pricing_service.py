from __future__ import annotations


class PricingService:
    def __init__(self, db):
        self.db = db

    def calculate_from_purchase(self, purchase_price, markup_percent):
        return round(purchase_price * (1 + markup_percent / 100), 2)

    def choose_price(self, mode, purchase_price, markup_percent, supplier_price=None):
        """
        mode:
        - supplier
        - markup
        - mixed
        """

        if mode == "supplier" and supplier_price:
            return supplier_price

        if mode == "markup":
            return self.calculate_from_purchase(purchase_price, markup_percent)

        if mode == "mixed":
            if supplier_price:
                return supplier_price
            return self.calculate_from_purchase(purchase_price, markup_percent)

        return purchase_price
