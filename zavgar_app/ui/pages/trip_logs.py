"""
ui/pages/trip_logs.py — Путевые листы
"""
from __future__ import annotations
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QTimeEdit, QComboBox, QSpinBox, QLineEdit, QTextEdit, QMessageBox,
    QMenu, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QDate, QTime
from zavgar_app.utils.column_settings import save_column_widths, restore_column_widths
from PySide6.QtGui import QColor, QAction
from zavgar_app.ui.widgets.triangle_spinbox import TriangleTimeEdit, TriangleSpinBox, TriangleDateEdit

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
        self.date_edit = TriangleDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Дата:", self.date_edit)
        
        # Время начала
        self.start_time_edit = TriangleTimeEdit()
        self.start_time_edit.setTime(QTime(8, 0))
        form.addRow("Начало:", self.start_time_edit)
        
        # Время окончания
        self.end_time_edit = TriangleTimeEdit()
        self.end_time_edit.setTime(QTime(17, 0))
        form.addRow("Окончание:", self.end_time_edit)
        
        # Пробег начальный
        self.start_mileage_spin = TriangleSpinBox()
        self.start_mileage_spin.setRange(0, 999999)
        self.start_mileage_spin.setSuffix(" км")
        form.addRow("Пробег (начало):", self.start_mileage_spin)
        
        # Пробег конечный
        self.end_mileage_spin = TriangleSpinBox()
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

        add_btn = QPushButton("+ Добавить путевой лист")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_trip)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Панель инструментов
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.setObjectName("actionBtn")
        self.edit_btn.clicked.connect(self._edit_selected_toolbar)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.setObjectName("actionDelete")
        self.delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(self.delete_btn)

        self.print_btn = QPushButton("🖨️ Печать")
        self.print_btn.setObjectName("ghostBtn")
        self.print_btn.clicked.connect(self._print_selected)
        toolbar.addWidget(self.print_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Водитель", "Автомобиль", "Откуда", "Куда", "Пробег", "Статус", "Цель"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_selected)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._update_toolbar)
        self.table.horizontalHeader().sectionResized.connect(self._on_column_resized)
        layout.addWidget(self.table)
        
        # Восстановить ширины столбцов
        from zavgar_app.utils.column_settings import restore_column_widths
        restore_column_widths(self.table, "trip_logs")

        self._update_toolbar()
        self.refresh()
    
    def _on_column_resized(self, col, old_width, new_width):
        """Сохранить ширину столбца при изменении."""
        from zavgar_app.utils.column_settings import save_column_widths
        save_column_widths(self.table, "trip_logs")

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

        self._update_toolbar()

    def _get_selected_trip(self):
        """Получить выбранный путевой лист из таблицы."""
        row = self.table.currentRow()
        if row < 0:
            return None
        trips = db.list_trip_logs(self.conn)
        if 0 <= row < len(trips):
            return trips[row]
        return None

    def _edit_selected(self, index):
        """Редактировать выбранную запись (двойной клик)."""
        row = index.row()
        trips = db.list_trip_logs(self.conn)
        if 0 <= row < len(trips):
            self._edit_trip(trips[row])

    def _edit_selected_toolbar(self):
        """Редактировать выбранную запись (кнопка тулбара)."""
        trip = self._get_selected_trip()
        if trip:
            self._edit_trip(trip)
        else:
            QMessageBox.information(self, "Информация", "Выберите запись для редактирования")

    def _delete_selected(self):
        """Удалить выбранную запись."""
        trip = self._get_selected_trip()
        if trip:
            self._delete_trip(trip.id)
        else:
            QMessageBox.information(self, "Информация", "Выберите запись для удаления")

    def _show_context_menu(self, position):
        """Показать контекстное меню при правом клике."""
        index = self.table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)

        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(self._edit_selected_toolbar)
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)

        menu.addSeparator()

        print_action = QAction("🖨️ Печать", self)
        print_action.triggered.connect(self._print_selected)
        menu.addAction(print_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _update_toolbar(self):
        """Обновить состояние кнопок панели инструментов."""
        has_selection = self.table.currentRow() >= 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.print_btn.setEnabled(has_selection)

    def _print_selected(self):
        """Печать выбранного путевого листа (форма РК)."""
        trip = self._get_selected_trip()
        if not trip:
            QMessageBox.information(self, "Информация", "Выберите запись для печати")
            return

        # Получить данные водителя и авто
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
        vehicles = {v.id: v for v in db.list_vehicles(self.conn)}
        driver_name = drivers.get(trip.driver_id, '—')
        vehicle = vehicles.get(trip.vehicle_id)
        vehicle_info = f"{vehicle.marka} {vehicle.model}, {vehicle.gosnomer}" if vehicle else '—'

        from zavgar_app.utils.print_utils import print_raw_html
        html = f"""
        <div style="font-family: 'Times New Roman', serif; font-size: 12pt;">
            <h2 style="text-align: center; margin-bottom: 5px;">ПУТЕВОЙ ЛИСТ</h2>
            <p style="text-align: center; margin-top: 0;">Форма № 3 (Республика Казахстан)</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr>
                    <td style="width: 50%; padding: 5px; border: 1px solid #000;">
                        <b>Организация:</b> _______________________
                    </td>
                    <td style="width: 50%; padding: 5px; border: 1px solid #000;">
                        <b>Дата:</b> {trip.trip_date}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Номер путевого листа:</b> {trip.id:06d}
                    </td>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Срок действия:</b> 1 день
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <tr>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Водитель:</b> {driver_name}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Автомобиль:</b> {vehicle_info}
                    </td>
                </tr>
            </table>

            <h3 style="margin-top: 20px; margin-bottom: 10px;">Задание на перевозку</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px; border: 1px solid #000; width: 30%;">
                        <b>Откуда:</b>
                    </td>
                    <td style="padding: 5px; border: 1px solid #000;">
                        {trip.route_from or '—'}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Куда:</b>
                    </td>
                    <td style="padding: 5px; border: 1px solid #000;">
                        {trip.route_to or '—'}
                    </td>
                </tr>
            </table>

            <h3 style="margin-top: 20px; margin-bottom: 10px;">Движение горючего (литров)</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 5px; border: 1px solid #000;">Остаток при выезде</th>
                    <th style="padding: 5px; border: 1px solid #000;">Выдано</th>
                    <th style="padding: 5px; border: 1px solid #000;">Остаток при возвращении</th>
                    <th style="padding: 5px; border: 1px solid #000;">Расход по норме</th>
                </tr>
                <tr>
                    <td style="padding: 5px; border: 1px solid #000; text-align: center;">—</td>
                    <td style="padding: 5px; border: 1px solid #000; text-align: center;">—</td>
                    <td style="padding: 5px; border: 1px solid #000; text-align: center;">—</td>
                    <td style="padding: 5px; border: 1px solid #000; text-align: center;">—</td>
                </tr>
            </table>

            <h3 style="margin-top: 20px; margin-bottom: 10px;">Пробег</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px; border: 1px solid #000; width: 50%;">
                        <b>Спидометр при выезде:</b> {trip.start_mileage or '—'} км
                    </td>
                    <td style="padding: 5px; border: 1px solid #000;">
                        <b>Спидометр при возвращении:</b> {trip.end_mileage or '—'} км
                    </td>
                </tr>
                <tr>
                    <td colspan="2" style="padding: 5px; border: 1px solid #000;">
                        <b>Общий пробег:</b> {(trip.end_mileage or 0) - trip.start_mileage} км
                    </td>
                </tr>
            </table>

            <table style="width: 100%; margin-top: 30px; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #000; width: 50%;">
                        <b>Выезд:</b><br/>
                        Время: {trip.start_time or '—'}<br/>
                        Подпись водителя: ___________
                    </td>
                    <td style="padding: 10px; border: 1px solid #000;">
                        <b>Возвращение:</b><br/>
                        Время: {trip.end_time or '—'}<br/>
                        Подпись водителя: ___________
                    </td>
                </tr>
            </table>

            <p style="margin-top: 30px; text-align: center; font-size: 10pt;">
                <i>Подпись диспетчера: _______________ Подпись механика: _______________</i>
            </p>
        </div>
        """
        print_raw_html(html, "Путевой лист", self)

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
