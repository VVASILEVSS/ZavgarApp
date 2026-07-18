"""
ui/pages/drivers.py — Раздел "Водители"
=======================================

Таблица водителей + форма добавления/редактирования.
Toolbar-based actions (add/edit/delete/print) + right-click context menu.
"""

from __future__ import annotations

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QMenu,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QAction
from zavgar_app.ui.widgets.triangle_spinbox import TriangleDateEdit

from ... import db
from ...models import Driver


class DriversPage(QWidget):
    """Страница управления водителями."""

    STATUS_LABELS = {
        'active': 'Активен',
        'vacation': 'Отпуск',
        'sick_leave': 'Больничный',
        'business_trip': 'Командировка',
        'suspended': 'Отстранён',
        'fired': 'Уволен',
    }

    STATUS_COLORS = {
        'active': '#10b981',
        'vacation': '#f59e0b',
        'sick_leave': '#ef4444',
        'business_trip': '#3b82f6',
        'suspended': '#6b7280',
        'fired': '#6b7280',
    }

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок + тулбар
        header = QHBoxLayout()
        title = QLabel("👤 Водители")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        # Toolbar buttons
        self.btn_add = QPushButton("+ Добавить")
        self.btn_add.setObjectName("primaryBtn")
        self.btn_add.clicked.connect(self._add_driver)
        header.addWidget(self.btn_add)

        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.setObjectName("actionBtn")
        self.btn_edit.clicked.connect(self._edit_selected_row)
        header.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.setObjectName("actionDelete")
        self.btn_delete.clicked.connect(self._delete_selected_row)
        header.addWidget(self.btn_delete)

        self.btn_print = QPushButton("🖨️ Печать")
        self.btn_print.setObjectName("ghostBtn")
        self.btn_print.clicked.connect(self._print_selected)
        header.addWidget(self.btn_print)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ФИО", "Телефон", "Водительское удостоверение", "Статус"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self._edit_selected)

        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Selection-based toolbar updates
        self.table.selectionModel().selectionChanged.connect(self._update_toolbar)
        self.table.horizontalHeader().sectionResized.connect(self._on_column_resized)

        layout.addWidget(self.table)

        # Восстановить ширины столбцов
        from zavgar_app.utils.column_settings import restore_column_widths
        restore_column_widths(self.table, "drivers")

        # Initial toolbar state (no selection)
        self._update_toolbar()

    def _on_column_resized(self, col, old_width, new_width):
        """Сохранить ширину столбца при изменении."""
        from zavgar_app.utils.column_settings import save_column_widths
        save_column_widths(self.table, "drivers")

    def refresh(self):
        """Перезагрузить данные."""
        drivers = db.list_drivers(self.conn)
        self.table.setRowCount(len(drivers))

        for row, driver in enumerate(drivers):
            self.table.setItem(row, 0, QTableWidgetItem(driver.fio))
            self.table.setItem(row, 1, QTableWidgetItem(driver.phone or ""))
            self.table.setItem(row, 2, QTableWidgetItem(driver.license_number or ""))

            # Статус с цветом
            status_item = QTableWidgetItem(self.STATUS_LABELS.get(driver.status, driver.status))
            color = self.STATUS_COLORS.get(driver.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 3, status_item)

    def _get_selected_driver(self) -> Driver | None:
        """Вернуть Driver для выбранной строки или None."""
        row = self.table.currentRow()
        if row < 0:
            return None
        drivers = db.list_drivers(self.conn)
        if 0 <= row < len(drivers):
            return drivers[row]
        return None

    def _edit_selected(self, index):
        """Редактировать выбранную запись (двойной клик)."""
        row = index.row()
        drivers = db.list_drivers(self.conn)
        if 0 <= row < len(drivers):
            self._edit_driver(drivers[row])

    def _edit_selected_row(self):
        """Редактировать выбранную запись (toolbar / context menu)."""
        driver = self._get_selected_driver()
        if driver:
            self._edit_driver(driver)

    def _delete_selected_row(self):
        """Удалить выбранную запись (toolbar / context menu)."""
        driver = self._get_selected_driver()
        if driver:
            self._delete_driver(driver)

    def _add_driver(self):
        """Открыть диалог добавления водителя."""
        dialog = DriverDialog(self.conn, parent=self)
        if dialog.exec():
            self.refresh()

    def _edit_driver(self, driver: Driver):
        """Открыть диалог редактирования водителя."""
        dialog = DriverDialog(self.conn, driver=driver, parent=self)
        if dialog.exec():
            self.refresh()

    def _delete_driver(self, driver: Driver):
        """Удалить водителя."""
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить водителя {driver.fio}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_driver(self.conn, driver.id)
            self.refresh()

    def _update_toolbar(self):
        """Включить/выключить кнопки тулбара в зависимости от выделения."""
        has_selection = self.table.currentRow() >= 0
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_print.setEnabled(has_selection)

    def _show_context_menu(self, pos):
        """Показать контекстное меню при правом клике на строку."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)

        menu = QMenu(self)

        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(self._edit_selected_row)
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)

        menu.addSeparator()

        print_action = QAction("🖨️ Печать", self)
        print_action.triggered.connect(self._print_selected)
        menu.addAction(print_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _print_selected(self):
        """Печать данных выбранного водителя."""
        driver = self._get_selected_driver()
        if not driver:
            QMessageBox.information(self, "Подсказка", "Выберите водителя для печати")
            return
        
        from zavgar_app.utils import print_single_record
        
        fields = [
            ("ФИО", driver.fio),
            ("Телефон", driver.phone or "—"),
            ("Водительское удостоверение", driver.license_number or "—"),
            ("Категория", driver.license_category or "—"),
            ("Срок действия прав", driver.license_expiry or "—"),
            ("Дата найма", driver.hire_date or "—"),
            ("Статус", self.STATUS_LABELS.get(driver.status, driver.status)),
            ("Заметки", driver.notes or "—"),
        ]
        
        print_single_record(f"Водитель: {driver.fio}", fields, self)


class DriverDialog(QDialog):
    """Диалог добавления/редактирования водителя."""

    def __init__(self, conn, driver: Driver = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.driver = driver
        self.setWindowTitle("Редактировать водителя" if driver else "Добавить водителя")
        self.setMinimumWidth(500)
        self._setup_ui()
        if driver:
            self._populate(driver)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # ФИО
        self.fio_edit = QLineEdit()
        self.fio_edit.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:", self.fio_edit)

        # Телефон
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (999) 123-45-67")
        form.addRow("Телефон:", self.phone_edit)

        # Номер прав
        self.license_number_edit = QLineEdit()
        self.license_number_edit.setPlaceholderText("77 AA 123456")
        form.addRow("№ прав:", self.license_number_edit)

        # Категория
        self.category_combo = QComboBox()
        self.category_combo.addItems(["", "A", "B", "C", "D", "E", "BE", "CE", "DE"])
        form.addRow("Категория:", self.category_combo)

        # Срок действия прав
        self.license_expiry_edit = TriangleDateEdit()
        self.license_expiry_edit.setDate(QDate.currentDate().addYears(10))
        form.addRow("Срок прав:", self.license_expiry_edit)

        # Дата найма
        self.hire_date_edit = TriangleDateEdit()
        self.hire_date_edit.setDate(QDate.currentDate())
        form.addRow("Дата найма:", self.hire_date_edit)
        
        # Статус
        self.status_combo = QComboBox()
        for key, label in DriversPage.STATUS_LABELS.items():
            self.status_combo.addItem(label, key)
        form.addRow("Статус:", self.status_combo)

        # Заметки
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Дополнительная информация...")
        form.addRow("Заметки:", self.notes_edit)

        layout.addLayout(form)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _populate(self, driver: Driver):
        """Заполнить форму данными водителя."""
        self.fio_edit.setText(driver.fio)
        self.phone_edit.setText(driver.phone or "")
        self.license_number_edit.setText(driver.license_number or "")

        idx = self.category_combo.findText(driver.license_category or "")
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        if driver.license_expiry:
            self.license_expiry_edit.setDate(QDate.fromString(driver.license_expiry, "yyyy-MM-dd"))

        if driver.hire_date:
            self.hire_date_edit.setDate(QDate.fromString(driver.hire_date, "yyyy-MM-dd"))
        
        status_idx = self.status_combo.findData(driver.status)
        if status_idx >= 0:
            self.status_combo.setCurrentIndex(status_idx)

        self.notes_edit.setPlainText(driver.notes or "")

    def _save(self):
        """Сохранить водителя."""
        fio = self.fio_edit.text().strip()
        if not fio:
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
            return

        now = datetime.now().isoformat()

        if self.driver:
            # Обновление
            updated = Driver(
                id=self.driver.id,
                fio=fio,
                phone=self.phone_edit.text().strip(),
                license_number=self.license_number_edit.text().strip(),
                license_category=self.category_combo.currentText(),
                license_expiry=self.license_expiry_edit.date().toString("yyyy-MM-dd"),
                hire_date=self.hire_date_edit.date().toString("yyyy-MM-dd"),
                status=self.status_combo.currentData() or "active",
                notes=self.notes_edit.toPlainText().strip(),
                created_at=self.driver.created_at,
            )
            db.update_driver(self.conn, updated)
        else:
            # Создание
            driver = Driver(
                fio=fio,
                phone=self.phone_edit.text().strip(),
                license_number=self.license_number_edit.text().strip(),
                license_category=self.category_combo.currentText(),
                license_expiry=self.license_expiry_edit.date().toString("yyyy-MM-dd"),
                hire_date=self.hire_date_edit.date().toString("yyyy-MM-dd"),
                status=self.status_combo.currentData() or "active",
                notes=self.notes_edit.toPlainText().strip(),
                created_at=now,
            )
            db.create_driver(self.conn, driver)

        self.accept()
