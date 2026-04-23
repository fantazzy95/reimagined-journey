from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton

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

        btn_apply = QPushButton("Провести документ")
        btn_apply.clicked.connect(self.apply)

        layout.addWidget(self.table)
        layout.addWidget(btn_apply)

        self.setLayout(layout)

    def apply(self):
        self.service.apply_document(self.document_id)
