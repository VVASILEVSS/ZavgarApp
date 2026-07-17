"""
ui/pages/maintenance.py — Раздел "ТО и обслуживание"
====================================================

Планирование ТО по пробегу + история выполненных работ.
"""

from __future__ import annotations

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QMessageBox, QTabWidget,
)
from PySide6.QtCore import Qt, QDate

from ... import db
from ...models import MaintenanceSchedule, MaintenanceRecord, Vehicle


MAINTENANCE_TYPES = {
    'oil': 'Замена масла',
    'filter': 'Замена фильтров',
    'brake': 'Тормозная система',
    'tire': 'Шины',
    'diagnostic': 'Диагностика',
    'repair': 'Ремонт',
    'other': 'Другое',
}


class MaintenancePage(QWidget):
    """Страница управления ТО."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🛠️ ТО и обслуживание")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Табы
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Таб 1: Графики ТО
        schedules_tab = QWidget()
        schedules_layout = QVBoxLayout(schedules_tab)

        header = QHBoxLayout()
        header.addStretch()
        add_schedule_btn = QPushButton("➕ Добавить график")
        add_schedule_btn.setObjectName("primaryBtn")
        add_schedule_btn.clicked.connect(self._add_schedule)
        header.addWidget(add_schedule_btn)
        schedules_layout.addLayout(header)

        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(7)
        self.schedules_table.setHorizontalHeaderLabels([
            "ID", "Автомобиль", "Тип ТО", "Интервал (км)", "Последнее ТО",
            "Следующее ТО", "Статус"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.schedules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedules_table.setAlternatingRowColors(True)
        schedules_layout.addWidget(self.schedules_table)

        self.tabs.addTab(schedules_tab, "Графики ТО")

        # Таб 2: История ТО
        records_tab = QWidget()
        records_layout = QVBoxLayout(records_tab)

        header2 = QHBoxLayout()
        header2.addStretch()
        add_record_btn = QPushButton("➕ Добавить запись")
        add_record_btn.setObjectName("primaryBtn")
        add_record_btn.clicked.connect(self._add_record)
        header2.addWidget(add_record_btn)
        records_layout.addLayout(header2)

        self.records_table = QTableWidget()
        self.records_table.setColumnCount(7)
        self.records_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Автомобиль", "Тип ТО", "Пробег", "Стоимость", "Примечания"
        ])
        self.records_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.records_table.setAlternatingRowColors(True)
        records_layout.addWidget(self.records_table)

        self.tabs.addTab(records_tab, "История ТО")

    def _load_data(self):
        """Загрузить графики и записи ТО."""
        # Графики
        schedules = db.list_maintenance_schedules(self.conn)
        vehicles = {v.id: v for v in db.list_vehicles(self.conn)}

        self.schedules_table.setRowCount(len(schedules))
        for row, schedule in enumerate(schedules):
            self.schedules_table.setItem(row, 0, QTableWidgetItem(str(schedule.id)))

            vehicle = vehicles.get(schedule.vehicle_id)
            vehicle_name = vehicle.full_name() if vehicle else "Неизвестно"
            self.schedules_table.setItem(row, 1, QTableWidgetItem(vehicle_name))

            type_name = MAINTENANCE_TYPES.get(schedule.maintenance_type, schedule.maintenance_type)
            self.schedules_table.setItem(row, 2, QTableWidgetItem(type_name))

            self.schedules_table.setItem(row, 3, QTableWidgetItem(f"{schedule.interval_km:,}"))
            self.schedules_table.setItem(row, 4, QTableWidgetItem(schedule.last_done_date or "—"))

            next_due = schedule.next_due_date or "—"
            self.schedules_table.setItem(row, 5, QTableWidgetItem(next_due))

            # Статус
            if vehicle and schedule.is_overdue(vehicle.current_mileage):
                status = "⚠️ Просрочено"
            else:
                status = "✅ В срок"
            self.schedules_table.setItem(row, 6, QTableWidgetItem(status))

        # Записи
        records = db.list_maintenance_records(self.conn)
        self.records_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.records_table.setItem(row, 0, QTableWidgetItem(str(record.id)))
            self.records_table.setItem(row, 1, QTableWidgetItem(record.service_date))

            vehicle = vehicles.get(record.vehicle_id)
            vehicle_name = vehicle.full_name() if vehicle else "Неизвестно"
            self.records_table.setItem(row, 2, QTableWidgetItem(vehicle_name))

            type_name = MAINTENANCE_TYPES.get(record.maintenance_type, record.maintenance_type)
            self.records_table.setItem(row, 3, QTableWidgetItem(type_name))

            self.records_table.setItem(row, 4, QTableWidgetItem(f"{record.mileage:,}"))
            cost = f"{record.cost:.2f}" if record.cost else "—"
            self.records_table.setItem(row, 5, QTableWidgetItem(cost))
            self.records_table.setItem(row, 6, QTableWidgetItem(record.notes or ""))

    def _add_schedule(self):
        """Открыть диалог добавления графика ТО."""
        dialog = ScheduleDialog(self.conn, parent=self)
        if dialog.exec():
            self._load_data()

    def _add_record(self):
        """Открыть диалог добавления записи ТО."""
        dialog = RecordDialog(self.conn, parent=self)
        if dialog.exec():
            self._load_data()


class ScheduleDialog(QDialog):
    """Диалог добавления графика ТО."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Добавить график ТО")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Автомобиль
        self.vehicle_combo = QComboBox()
        vehicles = db.list_vehicles(self.conn)
        for v in vehicles:
            self.vehicle_combo.addItem(v.full_name(), v.id)
        form.addRow("Автомобиль:", self.vehicle_combo)

        # Тип ТО
        self.type_combo = QComboBox()
        for key, name in MAINTENANCE_TYPES.items():
            self.type_combo.addItem(name, key)
        form.addRow("Тип ТО:", self.type_combo)

        # Интервал
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1000, 100000)
        self.interval_spin.setValue(10000)
        self.interval_spin.setSuffix(" км")
        form.addRow("Интервал:", self.interval_spin)

        # Последнее ТО (пробег)
        self.last_km_spin = QSpinBox()
        self.last_km_spin.setRange(0, 1000000)
        self.last_km_spin.setSuffix(" км")
        form.addRow("Последнее ТО (пробег):", self.last_km_spin)

        # Последнее ТО (дата)
        self.last_date_edit = QDateEdit()
        self.last_date_edit.setCalendarPopup(True)
        self.last_date_edit.setDate(QDate.currentDate())
        self.last_date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Последнее ТО (дата):", self.last_date_edit)

        # Заметки
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
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

    def _save(self):
        """Сохранить график ТО."""
        vehicle_id = self.vehicle_combo.currentData()
        if not vehicle_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль")
            return

        interval = self.interval_spin.value()
        last_km = self.last_km_spin.value()
        next_km = last_km + interval

        schedule = MaintenanceSchedule(
            vehicle_id=vehicle_id,
            maintenance_type=self.type_combo.currentData(),
            interval_km=interval,
            last_done_km=last_km,
            last_done_date=self.last_date_edit.date().toString("yyyy-MM-dd"),
            next_due_km=next_km,
            next_due_date=None,  # можно рассчитать по средней скорости
            notes=self.notes_edit.toPlainText().strip(),
        )
        db.create_maintenance_schedule(self.conn, schedule)
        self.accept()


class RecordDialog(QDialog):
    """Диалог добавления записи ТО."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Добавить запись ТО")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Дата
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Дата:", self.date_edit)

        # Автомобиль
        self.vehicle_combo = QComboBox()
        vehicles = db.list_vehicles(self.conn)
        for v in vehicles:
            self.vehicle_combo.addItem(v.full_name(), v.id)
        form.addRow("Автомобиль:", self.vehicle_combo)

        # Тип ТО
        self.type_combo = QComboBox()
        for key, name in MAINTENANCE_TYPES.items():
            self.type_combo.addItem(name, key)
        form.addRow("Тип ТО:", self.type_combo)

        # Пробег
        self.mileage_spin = QSpinBox()
        self.mileage_spin.setRange(0, 1000000)
        self.mileage_spin.setSuffix(" км")
        form.addRow("Пробег:", self.mileage_spin)

        # Стоимость
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 1000000)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setPrefix("₽ ")
        form.addRow("Стоимость:", self.cost_spin)

        # Примечания
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form.addRow("Примечания:", self.notes_edit)

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

    def _save(self):
        """Сохранить запись ТО."""
        vehicle_id = self.vehicle_combo.currentData()
        if not vehicle_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль")
            return

        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            maintenance_type=self.type_combo.currentData(),
            mileage=self.mileage_spin.value(),
            service_date=self.date_edit.date().toString("yyyy-MM-dd"),
            cost=self.cost_spin.value() if self.cost_spin.value() > 0 else None,
            notes=self.notes_edit.toPlainText().strip(),
        )
        db.create_maintenance_record(self.conn, record)
        self.accept()
