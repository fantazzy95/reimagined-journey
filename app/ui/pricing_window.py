from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QInputDialog, QMessageBox
)

from app.services.price_document_service import PriceDocumentService


class PricingWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Встановлення цін")
        self.resize(900, 600)

        self.service = PriceDocumentService(db)
        self.document_id = self.service.create_document()

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "✔",
            "Товар",
            "Стара ціна",
            "Нова ціна",
            "SKU",
        ])

        btn_add_from_doc = QPushButton("Додати з документа")
        btn_add_from_doc.clicked.connect(self.add_from_document)

        btn_apply = QPushButton("Провести документ")
        btn_apply.clicked.connect(self.apply)

        layout.addWidget(btn_add_from_doc)
        layout.addWidget(self.table)
        layout.addWidget(btn_apply)

        self.setLayout(layout)

    def refresh_table(self):
        items = self.service.get_document_items(self.document_id)
        self.table.setRowCount(len(items))

        for row_idx, item in enumerate(items):
            self.table.setItem(row_idx, 0, QTableWidgetItem("✔" if item.get("applied") else ""))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(item["old_price"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item["new_price"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(item.get("sku") or ""))

    def add_from_document(self):
        source_type_map = {
            "Всі": None,
            "Надходження": "receipt",
            "Замовлення постачальнику": "supplier_order",
            "Продаж": "sale",
        }

        source_type_label, ok = QInputDialog.getItem(
            self,
            "Тип документа",
            "Оберіть тип документа:",
            list(source_type_map.keys()),
            0,
            False,
        )
        if not ok:
            return

        docs = self.service.list_source_documents(source_type_map[source_type_label])

        if not docs:
            QMessageBox.information(self, "Інфо", "Немає документів цього типу")
            return

        options = [
            f"{d['id']} | {d['doc_type']} | {d['doc_date']} | {d.get('doc_number', '')} | {d.get('note', '')}"
            for d in docs
        ]

        choice, ok = QInputDialog.getItem(
            self,
            "Вибір документа",
            "Оберіть документ:",
            options,
            0,
            False,
        )

        if not ok:
            return

        doc_id = int(choice.split("|")[0].strip())

        added = self.service.add_items_from_existing_document(
            document_id=self.document_id,
            source_document_id=doc_id,
        )

        QMessageBox.information(self, "Готово", f"Додано позицій: {added}")
        self.refresh_table()

    def apply(self):
        count = self.service.apply_document(self.document_id)
        QMessageBox.information(self, "Готово", f"Оновлено товарів: {count}")
