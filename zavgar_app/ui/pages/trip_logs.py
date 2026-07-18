"""
ui/pages/trip_logs.py — Путевые листы
"""
from __future__ import annotations
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDateEdit,
    QTimeEdit, QComboBox, QSpinBox, QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from zavgar_app import db
from zavgar_app.models import TripLog, Driver, Vehicle


class TripLogDialog(QDialog):
    """Диалог добавления/редактирования путевого листа."""

    STATUS_MAP = {
        'planned': 'Запланирована',
        'in_progress': 'В пути',
        'completed': 'Завершена',
        'cancelled': 'Отменена',
    }

    def __init__(self, conn, drivers: list[Driver], vehicles: list[Vehicle], trip: TripLog = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.trip = trip
        self.drivers = drivers
        self.vehicles = vehicles
        
        self.setWindowTitle("Добавить путевой лист" if not trip else "Редактировать путевой лист")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Форма
        form = QFormLayout()
        
        # Водитель
        self.driver_combo = QComboBox()
        for d in drivers:
            self.driver_combo.addItem(d.fio, d.id)
        form.addRow("Водитель:", self.driver_combo)
        
        # Автомобиль
        self.vehicle_combo = QComboBox()
        for v in vehicles:
            self.vehicle_combo.addItem(f"{v.marka} {v.model} ({v.gosnomer})", v.id)
        form.addRow("Автомобиль:", self.vehicle_combo)
        
        # Дата
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Дата:", self.date_edit)
        
        # Время начала
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(8, 0))
        form.addRow("Начало:", self.start_time_edit)
        
        # Время окончания
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(17, 0))
        form.addRow("Окончание:", self.end_time_edit)
        
        # Пробег начальный
        self.start_mileage_spin = QSpinBox()
        self.start_mileage_spin.setRange(0, 999999)
        self.start_mileage_spin.setSuffix(" км")
        form.addRow("Пробег (начало):", self.start_mileage_spin)
        
        # Пробег конечный
        self.end_mileage_spin = QSpinBox()
        self.end_mileage_spin.setRange(0, 999999)
        self.end_mileage_spin.setSuffix(" км")
        form.addRow("Пробег (конец):", self.end_mileage_spin)
        
        # Откуда
        self.route_from_edit = QLineEdit()
        self.route_from_edit.setPlaceholderText("Адрес отправления")
        form.addRow("Откуда:", self.route_from_edit)
        
        # Куда
        self.route_to_edit = QLineEdit()
        self.route_to_edit.setPlaceholderText("Адрес назначения")
        form.addRow("Куда:", self.route_to_edit)
        
        # Цель
        self.purpose_edit = QLineEdit()
        self.purpose_edit.setPlaceholderText("Цель поездки")
        form.addRow("Цель:", self.purpose_edit)
        
        # Статус
        self.status_combo = QComboBox()
        for key, label in self.STATUS_MAP.items():
            self.status_combo.addItem(label, key)
        form.addRow("Статус:", self.status_combo)
        
        # Заметки
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        form.addRow("Заметки:", self.notes_edit)
        
        layout.addLayout(form)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Заполнение если редактирование
        if trip:
            driver_idx = self.driver_combo.findData(trip.driver_id)
            if driver_idx >= 0:
                self.driver_combo.setCurrentIndex(driver_idx)
            
            vehicle_idx = self.vehicle_combo.findData(trip.vehicle_id)
            if vehicle_idx >= 0:
                self.vehicle_combo.setCurrentIndex(vehicle_idx)
            
            self.date_edit.setDate(QDate.fromString(trip.trip_date, "yyyy-MM-dd"))
            
            if trip.start_time:
                self.start_time_edit.setTime(QTime.fromString(trip.start_time, "HH:mm"))
            if trip.end_time:
                self.end_time_edit.setTime(QTime.fromString(trip.end_time, "HH:mm"))
            
            self.start_mileage_spin.setValue(trip.start_mileage)
            if trip.end_mileage:
                self.end_mileage_spin.setValue(trip.end_mileage)
            
            self.route_from_edit.setText(trip.route_from)
            self.route_to_edit.setText(trip.route_to)
            self.purpose_edit.setText(trip.purpose)
            
            status_idx = self.status_combo.findData(trip.status)
            if status_idx >= 0:
                self.status_combo.setCurrentIndex(status_idx)
            
            self.notes_edit.setPlainText(trip.notes or "")
    
    def get_trip(self) -> TripLog:
        """Получить данные из формы."""
        start_mileage = self.start_mileage_spin.value()
        end_mileage = self.end_mileage_spin.value()
        distance = end_mileage - start_mileage if end_mileage > start_mileage else None
        
        return TripLog(
            id=self.trip.id if self.trip else None,
            driver_id=self.driver_combo.currentData(),
            vehicle_id=self.vehicle_combo.currentData(),
            trip_date=self.date_edit.date().toString("yyyy-MM-dd"),
            start_time=self.start_time_edit.time().toString("HH:mm"),
            end_time=self.end_time_edit.time().toString("HH:mm"),
            start_mileage=start_mileage,
            end_mileage=end_mileage if end_mileage > 0 else None,
            distance_km=distance,
            route_from=self.route_from_edit.text().strip(),
            route_to=self.route_to_edit.text().strip(),
            purpose=self.purpose_edit.text().strip(),
            status=self.status_combo.currentData(),
            notes=self.notes_edit.toPlainText().strip() or None,
            created_at=self.trip.created_at if self.trip else datetime.now().isoformat()
        )


class TripLogsPage(QWidget):
    """Страница путевых листов."""

    STATUS_COLORS = {
        'planned': '#6b7280',
        'in_progress': '#3b82f6',
        'completed': '#10b981',
        'cancelled': '#ef4444',
    }

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок
        header = QHBoxLayout()
        title = QLabel("🚗 Путевые листы")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("➕ Добавить путевой лист")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_trip)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Водитель", "Автомобиль", "Откуда", "Куда", "Пробег", "Статус", "Цель", "Действия"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 120)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        """Обновить таблицу."""
        trips = db.list_trip_logs(self.conn)
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
        vehicles = {v.id: f"{v.marka} {v.model}" for v in db.list_vehicles(self.conn)}
        
        self.table.setRowCount(len(trips))
        
        for row, trip in enumerate(trips):
            self.table.setItem(row, 0, QTableWidgetItem(trip.trip_date))
            self.table.setItem(row, 1, QTableWidgetItem(drivers.get(trip.driver_id, "?")))
            self.table.setItem(row, 2, QTableWidgetItem(vehicles.get(trip.vehicle_id, "?")))
            self.table.setItem(row, 3, QTableWidgetItem(trip.route_from))
            self.table.setItem(row, 4, QTableWidgetItem(trip.route_to))
            self.table.setItem(row, 5, QTableWidgetItem(f"{trip.distance_km or 0} км"))
            
            status_item = QTableWidgetItem(TripLogDialog.STATUS_MAP.get(trip.status, trip.status))
            color = self.STATUS_COLORS.get(trip.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 6, status_item)
            
            self.table.setItem(row, 7, QTableWidgetItem(trip.purpose))
            
            # Кнопки действий
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 32)
            edit_btn.clicked.connect(lambda checked, t=trip: self._edit_trip(t))
            actions_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(32, 32)
            del_btn.clicked.connect(lambda checked, tid=trip.id: self._delete_trip(tid))
            actions_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 8, actions_widget)

    def _add_trip(self):
        """Добавить путевой лист."""
        drivers = db.list_drivers(self.conn)
        vehicles = db.list_vehicles(self.conn)
        
        if not drivers:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте водителей")
            return
        if not vehicles:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобили")
            return
        
        dialog = TripLogDialog(self.conn, drivers, vehicles, parent=self)
        if dialog.exec() == QDialog.Accepted:
            trip = dialog.get_trip()
            db.create_trip_log(self.conn, trip)
            self.refresh()

    def _edit_trip(self, trip: TripLog):
        """Редактировать путевой лист."""
        drivers = db.list_drivers(self.conn)
        vehicles = db.list_vehicles(self.conn)
        dialog = TripLogDialog(self.conn, drivers, vehicles, trip, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated_trip = dialog.get_trip()
            db.update_trip_log(self.conn, updated_trip)
            self.refresh()

    def _delete_trip(self, trip_id: int):
        """Удалить путевой лист."""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить этот путевой лист?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_trip_log(self.conn, trip_id)
            self.refresh()
