from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


@dataclass
class ImportFieldRule:
    source_key: str | None = None
    force_value: Any | None = None
    default_value: Any | None = None

    def resolve(self, row: dict[str, Any]) -> Any:
        if self.force_value is not None:
            return self.force_value
        if self.source_key:
            value = row.get(self.source_key)
            if value not in (None, ""):
                return value
        return self.default_value


class ImportService:
    def __init__(self, db):
        self.db = db

    def parse_csv(self, file_path: str, delimiter: str = ",", encoding: str = "utf-8") -> list[dict[str, Any]]:
        with open(file_path, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return [dict(row) for row in reader]

    def parse_yml(self, file_path: str) -> list[dict[str, Any]]:
        tree = ET.parse(file_path)
        root = tree.getroot()
        offers = []
        for offer in root.findall('.//offer'):
            item = {
                'id': offer.get('id'),
                'name': self._text(offer, 'name'),
                'sku': self._text(offer, 'vendorCode'),
                'price': self._text(offer, 'price'),
                'currency': self._text(offer, 'currencyId'),
                'barcode': self._text(offer, 'barcode'),
                'description': self._text(offer, 'description'),
            }
            offers.append(item)
        return offers

    def parse_excel_placeholder(self, file_path: str) -> list[dict[str, Any]]:
        raise NotImplementedError('Excel parser will be added with openpyxl integration')

    def transform_rows(
        self,
        rows: list[dict[str, Any]],
        mapping: dict[str, ImportFieldRule],
    ) -> list[dict[str, Any]]:
        transformed = []
        for row in rows:
            item = {}
            for target_field, rule in mapping.items():
                item[target_field] = rule.resolve(row)
            transformed.append(item)
        return transformed

    def preview_rows(self, rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
        return rows[:limit]

    def normalize_currency(self, raw_value: str | None) -> str:
        if not raw_value:
            return 'UAH'
        value = str(raw_value).strip().lower()
        aliases = {
            'грн': 'UAH',
            'грн.': 'UAH',
            'uah': 'UAH',
            'hrn': 'UAH',
            '$': 'USD',
            'usd': 'USD',
            'долар': 'USD',
            'дол': 'USD',
            'eur': 'EUR',
            '€': 'EUR',
            'євро': 'EUR',
        }
        return aliases.get(value, str(raw_value).upper())

    def import_products_stub(self, items: list[dict[str, Any]]) -> dict[str, int]:
        created = 0
        updated = 0
        skipped = 0
        with self.db.connect() as conn:
            for item in items:
                sku = item.get('sku')
                barcode = item.get('barcode')
                name = item.get('name')
                existing = None
                if sku:
                    existing = conn.execute('SELECT id FROM products WHERE sku = ?', (sku,)).fetchone()
                if not existing and barcode:
                    existing = conn.execute('SELECT id FROM products WHERE barcode = ?', (barcode,)).fetchone()

                if existing:
                    conn.execute(
                        'UPDATE products SET name = COALESCE(?, name), updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                        (name, existing['id']),
                    )
                    updated += 1
                elif name:
                    currency_code = self.normalize_currency(item.get('sale_currency') or item.get('currency'))
                    currency = conn.execute('SELECT id FROM currencies WHERE code = ?', (currency_code,)).fetchone()
                    currency_id = currency['id'] if currency else 1
                    conn.execute(
                        'INSERT INTO products(name, sku, barcode, sale_price, sale_currency_id) VALUES (?, ?, ?, ?, ?)',
                        (
                            name,
                            sku,
                            barcode,
                            float(item.get('sale_price') or item.get('price') or 0),
                            currency_id,
                        ),
                    )
                    created += 1
                else:
                    skipped += 1
        return {'created': created, 'updated': updated, 'skipped': skipped}

    def _text(self, node, tag: str) -> str | None:
        found = node.find(tag)
        if found is None:
            return None
        return found.text
