from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout

from app.ui.pricing_window import PricingWindow


class MainWindow(QMainWindow):
    def __init__(self, inventory_service):
        super().__init__()
        self.setWindowTitle("Inventory App")
        self.resize(800, 600)

        central = QWidget()
        layout = QVBoxLayout()

        btn_pricing = QPushButton("Встановлення цін")
        btn_pricing.clicked.connect(self.open_pricing)

        layout.addWidget(btn_pricing)
        central.setLayout(layout)

        self.setCentralWidget(central)
        self.inventory_service = inventory_service

    def open_pricing(self):
        self.pricing_window = PricingWindow(self.inventory_service.db)
        self.pricing_window.show()
