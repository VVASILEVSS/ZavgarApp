"""
ui/pages/calendar_page.py — Календарь событий
"""
from __future__ import annotations
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget,
    QListWidget, QListWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QBrush

from zavgar_app import db


class CalendarPage(QWidget):
    """Страница календаря с визуализацией событий."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Левая часть — календарь
        left = QVBoxLayout()
        
        title = QLabel("📅 Календарь событий")
        title.setObjectName("pageTitle")
        left.addWidget(title)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        left.addWidget(self.calendar)
        
        layout.addLayout(left, 2)

        # Правая часть — события за день
        right = QVBoxLayout()
        
        events_group = QGroupBox("События на выбранный день")
        events_layout = QVBoxLayout(events_group)
        
        self.events_list = QListWidget()
        self.events_list.setAlternatingRowColors(True)
        events_layout.addWidget(self.events_list)
        
        right.addWidget(events_group)
        right.addStretch()
        
        layout.addLayout(right, 1)

        # Подсветить дни с событиями
        self._highlight_event_days()
        self._on_date_selected()

    def _highlight_event_days(self):
        """Подсветить дни с событиями."""
        # Получить все даты с событиями
        timesheets = db.list_timesheets(self.conn)
        trips = db.list_trip_logs(self.conn)
        
        event_dates = set()
        for ts in timesheets:
            event_dates.add(ts.work_date)
        for trip in trips:
            event_dates.add(trip.trip_date)
        
        # Формат для дней с событиями
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("#6366f1")))
        fmt.setForeground(QBrush(QColor("#ffffff")))
        
        for date_str in event_dates:
            qdate = QDate.fromString(date_str, "yyyy-MM-dd")
            if qdate.isValid():
                self.calendar.setDateTextFormat(qdate, fmt)

    def _on_date_selected(self):
        """Обновить список событий при выборе даты."""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")
        
        self.events_list.clear()
        
        # Табель за этот день
        timesheets = db.list_timesheets(self.conn, month=date_str[:7])
        for ts in timesheets:
            if ts.work_date == date_str:
                drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
                driver_name = drivers.get(ts.driver_id, "?")
                
                status_map = {
                    'work': 'Работа',
                    'day_off': 'Выходной',
                    'sick': 'Больничный',
                    'vacation': 'Отпуск',
                    'business_trip': 'Командировка',
                }
                status_text = status_map.get(ts.status, ts.status)
                
                time_str = ""
                if ts.start_time and ts.end_time:
                    time_str = f" ({ts.start_time}-{ts.end_time})"
                
                item = QListWidgetItem(f"📋 {driver_name}: {status_text}{time_str}")
                self.events_list.addItem(item)
        
        # Путевые листы за этот день
        trips = db.list_trip_logs(self.conn, month=date_str[:7])
        for trip in trips:
            if trip.trip_date == date_str:
                drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
                vehicles = {v.id: f"{v.marka} {v.model}" for v in db.list_vehicles(self.conn)}
                
                driver_name = drivers.get(trip.driver_id, "?")
                vehicle_name = vehicles.get(trip.vehicle_id, "?")
                
                status_map = {
                    'planned': 'Запланирована',
                    'in_progress': 'В пути',
                    'completed': 'Завершена',
                    'cancelled': 'Отменена',
                }
                status_text = status_map.get(trip.status, trip.status)
                
                route = ""
                if trip.route_from and trip.route_to:
                    route = f" {trip.route_from} → {trip.route_to}"
                
                item = QListWidgetItem(f"🚗 {driver_name} ({vehicle_name}): {status_text}{route}")
                self.events_list.addItem(item)
        
        if self.events_list.count() == 0:
            item = QListWidgetItem("Нет событий")
            item.setForeground(QColor("#9ca3af"))
            self.events_list.addItem(item)
