"""
ui/pages/timesheets.py — Табель учёта рабочего времени
"""
from __future__ import annotations
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDateEdit,
    QTimeEdit, QComboBox, QDoubleSpinBox, QTextEdit, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from zavgar_app import db
from zavgar_app.models import Timesheet, Driver


class TimesheetDialog(QDialog):
    """Диалог добавления/редактирования записи в табеле."""

    STATUS_MAP = {
        'work': 'Работа',
        'day_off': 'Выходной',
        'sick': 'Больничный',
        'vacation': 'Отпуск',
        'business_trip': 'Командировка',
    }

    def __init__(self, conn, drivers: list[Driver], timesheet: Timesheet = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.timesheet = timesheet
        self.drivers = drivers
        
        self.setWindowTitle("Добавить запись" if not timesheet else "Редактировать запись")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Форма
        form = QFormLayout()
        
        # Водитель
        self.driver_combo = QComboBox()
        for d in drivers:
            self.driver_combo.addItem(d.fio, d.id)
        form.addRow("Водитель:", self.driver_combo)
        
        # Дата
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Дата:", self.date_edit)
        
        # Статус
        self.status_combo = QComboBox()
        for key, label in self.STATUS_MAP.items():
            self.status_combo.addItem(label, key)
        form.addRow("Статус:", self.status_combo)
        
        # Время начала
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(8, 0))
        form.addRow("Начало:", self.start_time_edit)
        
        # Время окончания
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(17, 0))
        form.addRow("Окончание:", self.end_time_edit)
        
        # Часы
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 24)
        self.hours_spin.setValue(8.0)
        self.hours_spin.setSingleStep(0.5)
        form.addRow("Часов:", self.hours_spin)
        
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
        if timesheet:
            idx = self.driver_combo.findData(timesheet.driver_id)
            if idx >= 0:
                self.driver_combo.setCurrentIndex(idx)
            
            self.date_edit.setDate(QDate.fromString(timesheet.work_date, "yyyy-MM-dd"))
            
            status_idx = self.status_combo.findData(timesheet.status)
            if status_idx >= 0:
                self.status_combo.setCurrentIndex(status_idx)
            
            if timesheet.start_time:
                self.start_time_edit.setTime(QTime.fromString(timesheet.start_time, "HH:mm"))
            if timesheet.end_time:
                self.end_time_edit.setTime(QTime.fromString(timesheet.end_time, "HH:mm"))
            
            self.hours_spin.setValue(timesheet.hours)
            self.notes_edit.setPlainText(timesheet.notes or "")
    
    def get_timesheet(self) -> Timesheet:
        """Получить данные из формы."""
        return Timesheet(
            id=self.timesheet.id if self.timesheet else None,
            driver_id=self.driver_combo.currentData(),
            work_date=self.date_edit.date().toString("yyyy-MM-dd"),
            status=self.status_combo.currentData(),
            start_time=self.start_time_edit.time().toString("HH:mm"),
            end_time=self.end_time_edit.time().toString("HH:mm"),
            hours=self.hours_spin.value(),
            notes=self.notes_edit.toPlainText().strip() or None,
            created_at=self.timesheet.created_at if self.timesheet else datetime.now().isoformat()
        )


class TimesheetsPage(QWidget):
    """Страница табеля учёта рабочего времени."""

    STATUS_COLORS = {
        'work': '#10b981',
        'day_off': '#6b7280',
        'sick': '#ef4444',
        'vacation': '#f59e0b',
        'business_trip': '#3b82f6',
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
        title = QLabel("📅 Табель учёта")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("➕ Добавить запись")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_timesheet)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Водитель", "Статус", "Начало", "Окончание", "Часов", "Действия"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 120)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        """Обновить таблицу."""
        timesheets = db.list_timesheets(self.conn)
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
        
        self.table.setRowCount(len(timesheets))
        
        for row, ts in enumerate(timesheets):
            self.table.setItem(row, 0, QTableWidgetItem(ts.work_date))
            self.table.setItem(row, 1, QTableWidgetItem(drivers.get(ts.driver_id, "?")))
            
            status_item = QTableWidgetItem(TimesheetDialog.STATUS_MAP.get(ts.status, ts.status))
            color = self.STATUS_COLORS.get(ts.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 2, status_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(ts.start_time or ""))
            self.table.setItem(row, 4, QTableWidgetItem(ts.end_time or ""))
            self.table.setItem(row, 5, QTableWidgetItem(f"{ts.hours:.1f}"))
            
            # Кнопки действий
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 32)
            edit_btn.clicked.connect(lambda checked, t=ts: self._edit_timesheet(t))
            actions_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(32, 32)
            del_btn.clicked.connect(lambda checked, tid=ts.id: self._delete_timesheet(tid))
            actions_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 6, actions_widget)

    def _add_timesheet(self):
        """Добавить запись."""
        drivers = db.list_drivers(self.conn)
        if not drivers:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте водителей")
            return
        
        dialog = TimesheetDialog(self.conn, drivers, parent=self)
        if dialog.exec() == QDialog.Accepted:
            ts = dialog.get_timesheet()
            db.create_timesheet(self.conn, ts)
            self.refresh()

    def _edit_timesheet(self, timesheet: Timesheet):
        """Редактировать запись."""
        drivers = db.list_drivers(self.conn)
        dialog = TimesheetDialog(self.conn, drivers, timesheet, parent=self)
        if dialog.exec() == QDialog.Accepted:
            ts = dialog.get_timesheet()
            db.update_timesheet(self.conn, ts)
            self.refresh()

    def _delete_timesheet(self, timesheet_id: int):
        """Удалить запись."""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить эту запись из табеля?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_timesheet(self.conn, timesheet_id)
            self.refresh()
