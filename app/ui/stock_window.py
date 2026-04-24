from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem
)

from app.services.stock_service import StockService


class StockWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Склад")
        self.resize(900, 600)

        self.service = StockService(db)

        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук...")
        self.search.textChanged.connect(self.refresh)

        top.addWidget(self.search)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Товар", "SKU", "Залишок"])

        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        items = self.service.get_stock_balances(self.search.text())
        self.table.setRowCount(len(items))
        for i, p in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(p["product_name"]))
            self.table.setItem(i, 1, QTableWidgetItem(p.get("sku") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(p["balance"])))
