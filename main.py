import sys
from PySide6.QtWidgets import QApplication
from app.db.database import Database
from app.services.inventory_service import InventoryService
from app.ui.main_window import MainWindow


def main():
    db = Database()
    db.initialize()
    service = InventoryService(db)

    app = QApplication(sys.argv)
    window = MainWindow(service)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
