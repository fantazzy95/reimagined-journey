# Pricing UI Visibility Specification

## Модуль: Встановлення цін

### Принцип UI
Користувач бачить повний контроль над ціноутворенням, але інтерфейс не повинен бути перевантажений.

## Базова ідея
У таблиці документа `Встановлення цін` повинні бути:
- повний набір доступних колонок
- можливість показувати / приховувати колонки
- збереження наборів видимості
- швидке перемикання між пресетами вигляду

## Обов'язкові колонки (показувати за замовчуванням)
- apply
- product_name
- sku
- old_price
- new_price
- price_source
- markup_percent

## Додаткові колонки (можна увімкнути)
- purchase_price
- purchase_currency
- purchase_rate
- supplier_price
- supplier_currency
- supplier_name
- category
- brand
- formula_result
- difference_amount
- difference_percent
- source_type
- source_document_id
- note

## Пресети вигляду
Потрібно підтримати мінімум 4 пресети:

### 1. Базовий
Для швидкої ручної роботи:
- apply
- product_name
- sku
- old_price
- new_price

### 2. Закупівля
Для роботи від закупівельної ціни:
- apply
- product_name
- sku
- purchase_price
- purchase_currency
- purchase_rate
- markup_percent
- new_price

### 3. Постачальник
Для роботи від рекомендованих цін:
- apply
- product_name
- sku
- supplier_name
- supplier_price
- supplier_currency
- old_price
- new_price
- price_source

### 4. Повний контроль
Максимум полів для аналізу.

## UX-вимоги
- користувач може в будь-який момент натиснути `Колонки`
- у вікні вибрати, які поля показувати
- налаштування виду зберігаються
- має бути кнопка `Скинути до пресету`
- приховування колонок не впливає на розрахунок, тільки на відображення

## Архітектурний принцип
Логіка розрахунку і логіка відображення повинні бути розділені.

- `pricing_service` відповідає за ціну
- `price_document_service` відповідає за документ
- UI відповідає тільки за те, що показувати користувачу

## Технічна реалізація (рекомендовано)
Потрібно передбачити таблицю або JSON-конфіг для збереження:
- selected_columns
- active_preset
- order_of_columns
- widths_of_columns

Це може бути реалізовано як локальні налаштування користувача.
