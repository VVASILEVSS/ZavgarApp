"""
ui/pages/reports.py — Раздел "Отчёты"
=====================================

Аналитика: затраты, статистика, графики.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDateEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, QDate

from ... import db


class ReportsPage(QWidget):
    """Страница отчётов и аналитики."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()
        self._load_summary()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("📈 Отчёты")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Карточки статистики
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # Считаем данные
        vehicles = db.list_vehicles(self.conn)
        drivers = db.list_drivers(self.conn)
        parts = db.list_parts(self.conn)
        records = db.list_maintenance_records(self.conn)

        total_cost = sum(r.cost or 0 for r in records)
        low_stock = sum(1 for p in parts if p.is_low_stock())

        cards = [
            ("🚗 Авто в парке", str(len(vehicles)), "#6366f1"),
            ("👤 Водители", str(len(drivers)), "#10b981"),
            ("🔧 Запчасти", str(len(parts)), "#8b5cf6"),
            ("💰 Затраты на ТО", f"{total_cost:,.0f} ₽", "#f59e0b"),
            ("⚠️ Мало на складе", str(low_stock), "#ef4444" if low_stock > 0 else "#10b981"),
        ]

        for label, value, color in cards:
            card = self._make_stat_card(label, value, color)
            stats_row.addWidget(card)

        layout.addLayout(stats_row)

        # Таблица затрат по автомобилям
        layout.addSpacing(20)
        cost_label = QLabel("Затраты по автомобилям")
        cost_label.setObjectName("sectionTitle")
        layout.addWidget(cost_label)

        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(4)
        self.cost_table.setHorizontalHeaderLabels([
            "Автомобиль", "Кол-во ТО", "Общая стоимость", "Средняя стоимость"
        ])
        self.cost_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cost_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cost_table.setAlternatingRowColors(True)
        layout.addWidget(self.cost_table)

        layout.addStretch()

    def _make_stat_card(self, label: str, value: str, color: str) -> QFrame:
        """Создать карточку со статистикой."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        val_label = QLabel(value)
        val_label.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {color};")
        val_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(val_label)

        text_label = QLabel(label)
        text_label.setObjectName("statLabel")
        text_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(text_label)

        return card

    def _load_summary(self):
        """Загрузить сводку по затратам."""
        vehicles = db.list_vehicles(self.conn)
        records = db.list_maintenance_records(self.conn)

        # Группируем затраты по авто
        vehicle_costs = {}
        vehicle_counts = {}
        for record in records:
            vid = record.vehicle_id
            if vid not in vehicle_costs:
                vehicle_costs[vid] = 0
                vehicle_counts[vid] = 0
            vehicle_costs[vid] += record.cost or 0
            vehicle_counts[vid] += 1

        # Заполняем таблицу
        rows = []
        for vehicle in vehicles:
            cost = vehicle_costs.get(vehicle.id, 0)
            count = vehicle_counts.get(vehicle.id, 0)
            avg = cost / count if count > 0 else 0
            rows.append((vehicle.full_name(), count, cost, avg))

        # Сортируем по затратам
        rows.sort(key=lambda x: x[2], reverse=True)

        self.cost_table.setRowCount(len(rows))
        for i, (name, count, total, avg) in enumerate(rows):
            self.cost_table.setItem(i, 0, QTableWidgetItem(name))
            self.cost_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.cost_table.setItem(i, 2, QTableWidgetItem(f"{total:,.2f} ₽"))
            self.cost_table.setItem(i, 3, QTableWidgetItem(f"{avg:,.2f} ₽"))
