from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QInputDialog, QMessageBox
)

from app.services.inventory_service import InventoryService
from app.services.receipt_service import ReceiptService
from app.services.price_document_service import PriceDocumentService
from app.ui.pricing_window import PricingWindow


class ReceiptWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Надходження")
        self.resize(1000, 650)

        self.db = db
        self.inventory_service = InventoryService(db)
        self.receipt_service = ReceiptService(db)
        self.price_document_service = PriceDocumentService(db)
        self.document_id = self.receipt_service.create_receipt()

        layout = QVBoxLayout()
        actions = QHBoxLayout()

        btn_add_product = QPushButton("Додати товар")
        btn_add_product.clicked.connect(self.add_product)

        btn_post = QPushButton("Провести надходження")
        btn_post.clicked.connect(self.post_receipt)

        btn_set_prices = QPushButton("Встановити ціни")
        btn_set_prices.clicked.connect(self.open_pricing_from_receipt)

        actions.addWidget(btn_add_product)
        actions.addWidget(btn_post)
        actions.addWidget(btn_set_prices)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Товар",
            "SKU",
            "Кількість",
            "Ціна",
            "Валюта ID",
            "Сума",
        ])

        layout.addLayout(actions)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.refresh_table()

    def refresh_table(self):
        items = self.receipt_service.get_document_items(self.document_id)
        self.table.setRowCount(len(items))

        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item.get("sku") or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item["price"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(item["currency_id"])))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(item["line_total"])))

    def add_product(self):
        query, ok = QInputDialog.getText(self, "Пошук товару", "Введіть назву / SKU / штрихкод:")
        if not ok:
            return

        products = self.inventory_service.search_products(query)
        if not products:
            QMessageBox.information(self, "Інфо", "Товари не знайдені")
            return

        options = [f"{p['id']} | {p['name']} | {p.get('sku') or ''} | {p['sale_price']} {p['currency_code']}" for p in products]
        choice, ok = QInputDialog.getItem(self, "Вибір товару", "Оберіть товар:", options, 0, False)
        if not ok:
            return

        product_id = int(choice.split("|")[0].strip())
        product = self.inventory_service.get_product(product_id)
        if not product:
            QMessageBox.warning(self, "Помилка", "Товар не знайдено")
            return

        quantity, ok = QInputDialog.getDouble(self, "Кількість", "Введіть кількість:", 1.0, 0.001, 1000000.0, 3)
        if not ok:
            return

        price, ok = QInputDialog.getDouble(self, "Ціна закупки", "Введіть ціну закупки:", 0.0, 0.0, 100000000.0, 2)
        if not ok:
            return

        currency_id, ok = QInputDialog.getInt(self, "Валюта", "Введіть ID валюти:", product["sale_currency_id"], 1, 999999, 1)
        if not ok:
            return

        self.receipt_service.add_item(
            document_id=self.document_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
            currency_id=currency_id,
        )
        self.refresh_table()

    def post_receipt(self):
        count = self.receipt_service.post_receipt(self.document_id)
        QMessageBox.information(self, "Готово", f"Проведено позицій: {count}")

    def open_pricing_from_receipt(self):
        price_doc_id = self.price_document_service.create_document(source_type="receipt", source_document_id=self.document_id)
        self.price_document_service.add_items_from_existing_document(
            document_id=price_doc_id,
            source_document_id=self.document_id,
        )
        self.pricing_window = PricingWindow(self.db, document_id=price_doc_id)
        self.pricing_window.show()
