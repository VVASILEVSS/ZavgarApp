"""
utils/column_settings.py — Сохранение/восстановление ширин столбцов таблиц
"""
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QTableWidget

SETTINGS_KEY = "ZavgarApp/TableColumnWidths"

def save_column_widths(table: QTableWidget, table_name: str):
    """Сохранить ширины столбцов таблицы в QSettings."""
    settings = QSettings(SETTINGS_KEY, table_name)
    widths = []
    for col in range(table.columnCount()):
        widths.append(table.columnWidth(col))
    settings.setValue("widths", widths)

def restore_column_widths(table: QTableWidget, table_name: str):
    """Восстановить ширины столбцов таблицы из QSettings."""
    settings = QSettings(SETTINGS_KEY, table_name)
    widths = settings.value("widths", None)
    if widths and isinstance(widths, list) and len(widths) == table.columnCount():
        for col, width in enumerate(widths):
            if isinstance(width, int) and width > 0:
                table.setColumnWidth(col, width)
