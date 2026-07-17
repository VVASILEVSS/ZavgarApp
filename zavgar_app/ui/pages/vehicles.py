"""
ui/pages/vehicles.py — Раздел "Автопарк"
=========================================

Таблица автомобилей + форма добавления/редактирования.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from zavgar_app.models import Vehicle
from zavgar_app import db
from zavgar_app.ui.theme import add_shadow


class VehicleDialog(QDialog):
    """Диалог добавления/редактирования авто."""

    def __init__(self, vehicle: Optional[Vehicle] = None, parent=None):
        super().__init__(parent)
        self.vehicle = vehicle
        self.setWindowTitle('Добавить авто' if not vehicle else 'Редактировать авто')
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Форма
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.marka_input = QLineEdit()
        self.marka_input.setPlaceholderText('Toyota')
        form.addRow('Марка:', self.marka_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText('Camry')
        form.addRow('Модель:', self.model_input)

        self.year_input = QSpinBox()
        self.year_input.setRange(1980, 2030)
        self.year_input.setValue(2020)
        form.addRow('Год:', self.year_input)

        self.gosnomer_input = QLineEdit()
        self.gosnomer_input.setPlaceholderText('K123ABC')
        form.addRow('Госномер:', self.gosnomer_input)

        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText('JTDKN3DU5A0123456')
        form.addRow('VIN:', self.vin_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Легковой', 'Грузовой', 'Спецтехника', 'Автобус'])
        form.addRow('Тип:', self.type_combo)

        self.mileage_input = QSpinBox()
        self.mileage_input.setRange(0, 999_999)
        self.mileage_input.setSuffix(' км')
        form.addRow('Пробег:', self.mileage_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Активен', 'На ремонте', 'Списан'])
        form.addRow('Статус:', self.status_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText('Заметки...')
        self.notes_input.setMaximumHeight(80)
        form.addRow('Заметки:', self.notes_input)

        layout.addLayout(form)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton('Сохранить')
        save_btn.setObjectName('primaryBtn')
        save_btn.clicked.connect(self.accept)
        add_shadow(save_btn, blur=10, opacity=20, y_offset=2)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Заполнение если редактирование
        if vehicle:
            self.marka_input.setText(vehicle.marka)
            self.model_input.setText(vehicle.model)
            self.year_input.setValue(vehicle.year or 2020)
            self.gosnomer_input.setText(vehicle.gosnomer)
            self.vin_input.setText(vehicle.vin or '')
            self.mileage_input.setValue(vehicle.current_mileage)
            self.notes_input.setPlainText(vehicle.notes or '')

            type_map = {'car': 0, 'truck': 1, 'special': 2, 'bus': 3}
            self.type_combo.setCurrentIndex(type_map.get(vehicle.vehicle_type, 0))

            status_map = {'active': 0, 'repair': 1, 'scrapped': 2}
            self.status_combo.setCurrentIndex(status_map.get(vehicle.status, 0))

    def get_vehicle(self) -> Vehicle:
        """Собрать данные из формы."""
        type_map = {0: 'car', 1: 'truck', 2: 'special', 3: 'bus'}
        status_map = {0: 'active', 1: 'repair', 2: 'scrapped'}

        now = datetime.now().isoformat(sep=' ', timespec='seconds')

        return Vehicle(
            id=self.vehicle.id if self.vehicle else None,
            marka=self.marka_input.text().strip(),
            model=self.model_input.text().strip(),
            year=self.year_input.value(),
            vin=self.vin_input.text().strip() or None,
            gosnomer=self.gosnomer_input.text().strip(),
            vehicle_type=type_map.get(self.type_combo.currentIndex(), 'car'),
            status=status_map.get(self.status_combo.currentIndex(), 'active'),
            current_mileage=self.mileage_input.value(),
            notes=self.notes_input.toPlainText().strip() or None,
            created_at=self.vehicle.created_at if self.vehicle else now,
            updated_at=now,
        )


class VehiclesPage(QWidget):
    """Раздел "Автопарк"."""

    STATUS_COLORS = {
        'active': '#10b981',
        'repair': '#f59e0b',
        'scrapped': '#6b7280',
    }

    TYPE_LABELS = {
        'car': 'Легковой',
        'truck': 'Грузовой',
        'special': 'Спецтехника',
        'bus': 'Автобус',
    }

    STATUS_LABELS = {
        'active': 'Активен',
        'repair': 'На ремонте',
        'scrapped': 'Списан',
    }

    def __init__(self, conn: sqlite3.Connection, parent=None):
        super().__init__(parent)
        self.conn = conn
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Заголовок + кнопки
        header = QHBoxLayout()
        title = QLabel('🚙 Автопарк')
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton('＋ Добавить авто')
        add_btn.setObjectName('primaryBtn')
        add_btn.clicked.connect(self._add_vehicle)
        add_shadow(add_btn, blur=10, opacity=20, y_offset=2)
        header.addWidget(add_btn)

        edit_btn = QPushButton('✏️ Редактировать')
        edit_btn.clicked.connect(self._edit_vehicle)
        header.addWidget(edit_btn)

        del_btn = QPushButton('🗑 Удалить')
        del_btn.setObjectName('dangerBtn')
        del_btn.clicked.connect(self._delete_vehicle)
        header.addWidget(del_btn)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'Марка/Модель', 'Год', 'Госномер', 'Тип', 'Пробег', 'Статус', 'ID'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 40)  # ID скрыт
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(self._edit_vehicle)

        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        """Перезагрузить данные."""
        vehicles = db.list_vehicles(self.conn)
        self.table.setRowCount(len(vehicles))

        for row, v in enumerate(vehicles):
            self.table.setItem(row, 0, QTableWidgetItem(f'{v.marka} {v.model}'))
            self.table.setItem(row, 1, QTableWidgetItem(str(v.year or '')))
            self.table.setItem(row, 2, QTableWidgetItem(v.gosnomer))
            self.table.setItem(row, 3, QTableWidgetItem(self.TYPE_LABELS.get(v.vehicle_type, v.vehicle_type)))
            self.table.setItem(row, 4, QTableWidgetItem(f'{v.current_mileage:,} км'))

            status_item = QTableWidgetItem(self.STATUS_LABELS.get(v.status, v.status))
            color = self.STATUS_COLORS.get(v.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 5, status_item)

            id_item = QTableWidgetItem(str(v.id))
            self.table.setItem(row, 6, id_item)

    def _get_selected_vehicle_id(self) -> Optional[int]:
        """Получить ID выбранного авто."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 6)
        return int(item.text()) if item else None

    def _add_vehicle(self):
        """Добавить авто."""
        dlg = VehicleDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            v = dlg.get_vehicle()
            if not v.marka and not v.gosnomer:
                QMessageBox.warning(self, 'Ошибка', 'Укажите марку или госномер')
                return
            db.create_vehicle(self.conn, v)
            self.refresh()

    def _edit_vehicle(self):
        """Редактировать авто."""
        vid = self._get_selected_vehicle_id()
        if not vid:
            QMessageBox.information(self, 'Подсказка', 'Выберите авто в таблице')
            return

        vehicle = db.get_vehicle(self.conn, vid)
        if not vehicle:
            return

        dlg = VehicleDialog(vehicle=vehicle, parent=self)
        if dlg.exec() == QDialog.Accepted:
            v = dlg.get_vehicle()
            db.update_vehicle(self.conn, v)
            self.refresh()

    def _delete_vehicle(self):
        """Удалить авто."""
        vid = self._get_selected_vehicle_id()
        if not vid:
            QMessageBox.information(self, 'Подсказка', 'Выберите авто в таблице')
            return

        reply = QMessageBox.question(
            self, 'Удаление',
            'Удалить выбранный автомобиль?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            db.delete_vehicle(self.conn, vid)
            self.refresh()
