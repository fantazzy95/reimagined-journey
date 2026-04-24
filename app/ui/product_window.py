from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox
)

from app.services.product_service import ProductService


class ProductWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Товари")
        self.resize(900, 600)

        self.service = ProductService(db)

        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук...")
        self.search.textChanged.connect(self.refresh)

        btn_add = QPushButton("Додати")
        btn_add.clicked.connect(self.add_product)

        top.addWidget(self.search)
        top.addWidget(btn_add)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Назва", "SKU", "Ціна", "Валюта", "Активний"])

        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        items = self.service.list_products(self.search.text())
        self.table.setRowCount(len(items))
        for i, p in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(p["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(p.get("sku") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(p["sale_price"])))
            self.table.setItem(i, 3, QTableWidgetItem(p["currency_code"]))
            self.table.setItem(i, 4, QTableWidgetItem("✔" if p["is_active"] else ""))

    def add_product(self):
        name, ok = QInputDialog.getText(self, "Назва", "Назва товару:")
        if not ok or not name:
            return
        self.service.create_product(name=name)
        QMessageBox.information(self, "OK", "Товар додано")
        self.refresh()
