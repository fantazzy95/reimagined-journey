from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

from app.ui.product_window import ProductWindow
from app.ui.import_window import ImportWindow
from app.ui.receipt_window import ReceiptWindow
from app.ui.pricing_window import PricingWindow
from app.ui.stock_window import StockWindow


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("ERP Lite")
        self.resize(400, 500)

        self.db = db

        central = QWidget()
        layout = QVBoxLayout()

        btn_products = QPushButton("Товари")
        btn_products.clicked.connect(self.open_products)

        btn_import = QPushButton("Імпорт")
        btn_import.clicked.connect(self.open_import)

        btn_receipt = QPushButton("Надходження")
        btn_receipt.clicked.connect(self.open_receipt)

        btn_pricing = QPushButton("Ціни")
        btn_pricing.clicked.connect(self.open_pricing)

        btn_stock = QPushButton("Склад")
        btn_stock.clicked.connect(self.open_stock)

        layout.addWidget(btn_products)
        layout.addWidget(btn_import)
        layout.addWidget(btn_receipt)
        layout.addWidget(btn_pricing)
        layout.addWidget(btn_stock)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def open_products(self):
        self.w = ProductWindow(self.db)
        self.w.show()

    def open_import(self):
        self.w = ImportWindow(self.db)
        self.w.show()

    def open_receipt(self):
        self.w = ReceiptWindow(self.db)
        self.w.show()

    def open_pricing(self):
        self.w = PricingWindow(self.db)
        self.w.show()

    def open_stock(self):
        self.w = StockWindow(self.db)
        self.w.show()
