from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QComboBox, QTableWidget,
    QTableWidgetItem, QListWidget, QListWidgetItem
)

from app.services.import_service import ImportService, ImportFieldRule


class ImportWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Імпорт товарів")
        self.resize(1100, 700)

        self.db = db
        self.service = ImportService(db)
        self.file_path: str | None = None
        self.rows: list[dict] = []
        self.headers: list[str] = []

        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.file_label = QLabel("Файл не вибрано")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "YML", "Excel"])

        btn_select = QPushButton("Вибрати файл")
        btn_select.clicked.connect(self.select_file)

        btn_preview = QPushButton("Попередній перегляд")
        btn_preview.clicked.connect(self.load_preview)

        btn_import = QPushButton("Імпортувати")
        btn_import.clicked.connect(self.run_import)

        top.addWidget(self.file_label)
        top.addWidget(self.format_combo)
        top.addWidget(btn_select)
        top.addWidget(btn_preview)
        top.addWidget(btn_import)

        mapping_bar = QHBoxLayout()
        self.source_column_combo = QComboBox()
        self.target_field_combo = QComboBox()
        self.target_field_combo.addItems([
            "name",
            "sku",
            "barcode",
            "price",
            "sale_price",
            "currency",
            "sale_currency",
            "description",
        ])
        self.force_value_combo = QComboBox()
        self.force_value_combo.setEditable(True)
        self.force_value_combo.addItems(["", "UAH", "USD", "EUR", "шт"])

        btn_add_mapping = QPushButton("Додати мапінг")
        btn_add_mapping.clicked.connect(self.add_mapping)

        mapping_bar.addWidget(QLabel("Колонка"))
        mapping_bar.addWidget(self.source_column_combo)
        mapping_bar.addWidget(QLabel("Поле"))
        mapping_bar.addWidget(self.target_field_combo)
        mapping_bar.addWidget(QLabel("Примусове значення"))
        mapping_bar.addWidget(self.force_value_combo)
        mapping_bar.addWidget(btn_add_mapping)

        self.mapping_list = QListWidget()
        self.preview_table = QTableWidget()

        layout.addLayout(top)
        layout.addLayout(mapping_bar)
        layout.addWidget(QLabel("Мапінг полів"))
        layout.addWidget(self.mapping_list)
        layout.addWidget(QLabel("Попередній перегляд"))
        layout.addWidget(self.preview_table)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть файл",
            "",
            "Data Files (*.csv *.yml *.xml *.xlsx);;All Files (*.*)",
        )
        if not file_path:
            return
        self.file_path = file_path
        self.file_label.setText(Path(file_path).name)

    def load_preview(self):
        if not self.file_path:
            QMessageBox.warning(self, "Помилка", "Спочатку виберіть файл")
            return

        fmt = self.format_combo.currentText()
        try:
            if fmt == "CSV":
                self.rows = self.service.parse_csv(self.file_path)
            elif fmt == "YML":
                self.rows = self.service.parse_yml(self.file_path)
            else:
                QMessageBox.information(self, "Інфо", "Excel буде підключено наступним кроком")
                return
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))
            return

        preview = self.service.preview_rows(self.rows)
        self.headers = list(preview[0].keys()) if preview else []
        self.source_column_combo.clear()
        self.source_column_combo.addItems(self.headers)
        self.fill_preview_table(preview)

    def fill_preview_table(self, rows: list[dict]):
        self.preview_table.clear()
        if not rows:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return

        headers = list(rows[0].keys())
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, header in enumerate(headers):
                self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(str(row.get(header, ""))))

    def add_mapping(self):
        source = self.source_column_combo.currentText() or None
        target = self.target_field_combo.currentText()
        force = self.force_value_combo.currentText().strip()
        rule_text = f"{target} <- {source or '-'}"
        if force:
            rule_text += f" | force={force}"
        item = QListWidgetItem(rule_text)
        item.setData(32, {
            "target": target,
            "source": source,
            "force": force,
        })
        self.mapping_list.addItem(item)

    def collect_mapping(self) -> dict[str, ImportFieldRule]:
        mapping: dict[str, ImportFieldRule] = {}
        for idx in range(self.mapping_list.count()):
            item = self.mapping_list.item(idx)
            data = item.data(32)
            mapping[data["target"]] = ImportFieldRule(
                source_key=data["source"],
                force_value=data["force"] or None,
                default_value=None,
            )
        return mapping

    def run_import(self):
        if not self.rows:
            QMessageBox.warning(self, "Помилка", "Немає даних для імпорту")
            return

        mapping = self.collect_mapping()
        if not mapping:
            QMessageBox.warning(self, "Помилка", "Спочатку задайте мапінг полів")
            return

        transformed = self.service.transform_rows(self.rows, mapping)
        result = self.service.import_products_stub(transformed)
        QMessageBox.information(
            self,
            "Імпорт завершено",
            f"Створено: {result['created']}\nОновлено: {result['updated']}\nПропущено: {result['skipped']}",
        )
