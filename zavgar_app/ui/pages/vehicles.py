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
    QMessageBox, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from zavgar_app.models import Vehicle
from zavgar_app import db
from zavgar_app.ui.theme import add_shadow


class VehicleDialog(QDialog):
    """Диалог добавления/редактирования авто."""

    def __init__(self, vehicle: Optional[Vehicle] = None, conn=None, parent=None):
        super().__init__(parent)
        self.vehicle = vehicle
        self.conn = conn
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

        # Водитель
        self.driver_combo = QComboBox()
        self.driver_combo.addItem('— Не назначен —', None)
        drivers = db.list_drivers(self.conn) if self.conn else []
        for d in drivers:
            self.driver_combo.addItem(d.fio, d.id)
        form.addRow('Водитель:', self.driver_combo)

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

            # Выбрать водителя
            if vehicle.assigned_driver_id:
                idx = self.driver_combo.findData(vehicle.assigned_driver_id)
                if idx >= 0:
                    self.driver_combo.setCurrentIndex(idx)

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
            assigned_driver_id=self.driver_combo.currentData(),
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
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок + поиск
        header = QHBoxLayout()
        title = QLabel("🚗 Автопарк")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        # Поиск
        from ..widgets import SearchBox
        self.search_box = SearchBox("Поиск по марке, модели, госномеру...")
        self.search_box.setFixedWidth(300)
        self.search_box.search_changed.connect(self._filter_table)
        header.addWidget(self.search_box)

        add_btn = QPushButton("+ Добавить авто")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_vehicle)
        header.addWidget(add_btn)

        edit_btn = QPushButton('✏️')
        edit_btn.setObjectName('actionBtn')
        edit_btn.setToolTip('Редактировать выбранное авто')
        edit_btn.clicked.connect(self._edit_vehicle)
        header.addWidget(edit_btn)

        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('actionDelete')
        del_btn.setToolTip('Удалить (в корзину)')
        del_btn.clicked.connect(self._delete_vehicle)
        header.addWidget(del_btn)

        print_btn = QPushButton('🖨️')
        print_btn.setObjectName('ghostBtn')
        print_btn.setToolTip('Печать')
        print_btn.clicked.connect(self._print_vehicle)
        header.addWidget(print_btn)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Марка/Модель', 'Год', 'Госномер', 'Тип', 'Пробег', 'Водитель', 'Статус'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.horizontalHeader().sectionResized.connect(self._on_column_resized)
        layout.addWidget(self.table)
        
        # Восстановить ширины столбцов
        from zavgar_app.utils.column_settings import restore_column_widths
        restore_column_widths(self.table, "vehicles")

        self.refresh()
    
    def _on_column_resized(self, col, old_width, new_width):
        """Сохранить ширину столбца при изменении."""
        from zavgar_app.utils.column_settings import save_column_widths
        save_column_widths(self.table, "vehicles")

    def refresh(self):
        """Перезагрузить данные."""
        self._all_vehicles = db.list_vehicles(self.conn)
        self._drivers_map = {d.id: d.fio for d in db.list_drivers(self.conn)}
        self._filter_table("")

    def _filter_table(self, search_text: str):
        """Фильтровать таблицу по поисковому запросу."""
        search = search_text.lower()
        
        filtered = []
        for v in self._all_vehicles:
            if not search:
                filtered.append(v)
                continue
            
            # Поиск по марке, модели, госномеру, VIN
            if (search in (v.marka or "").lower() or
                search in (v.model or "").lower() or
                search in (v.gosnomer or "").lower() or
                search in (v.vin or "").lower()):
                filtered.append(v)
        
        self.table.setRowCount(len(filtered))

        for row, v in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(v.id)))
            self.table.setItem(row, 1, QTableWidgetItem(f'{v.marka} {v.model}'))
            self.table.setItem(row, 2, QTableWidgetItem(str(v.year or '')))
            self.table.setItem(row, 3, QTableWidgetItem(v.gosnomer))
            self.table.setItem(row, 4, QTableWidgetItem(self.TYPE_LABELS.get(v.vehicle_type, v.vehicle_type)))
            self.table.setItem(row, 5, QTableWidgetItem(f'{v.current_mileage:,} км'))

            driver_name = self._drivers_map.get(v.assigned_driver_id, '—') if v.assigned_driver_id else '—'
            self.table.setItem(row, 6, QTableWidgetItem(driver_name))

            status_item = QTableWidgetItem(self.STATUS_LABELS.get(v.status, v.status))
            color = self.STATUS_COLORS.get(v.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 7, status_item)

    def _get_selected_vehicle_id(self) -> Optional[int]:
        """Получить ID выбранного авто."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)  # ID в колонке 0
        return int(item.text()) if item else None

    def _add_vehicle(self):
        """Добавить авто."""
        dlg = VehicleDialog(conn=self.conn, parent=self)
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

        dlg = VehicleDialog(vehicle=vehicle, conn=self.conn, parent=self)
        if dlg.exec() == QDialog.Accepted:
            v = dlg.get_vehicle()
            db.update_vehicle(self.conn, v)
            self.refresh()

    def _show_context_menu(self, pos):
        """Контекстное меню по правому клику."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)
        menu = QMenu(self)
        menu.addAction('✏️ Редактировать', self._edit_vehicle)
        menu.addAction('🗑️ Удалить', self._delete_vehicle)
        menu.addSeparator()
        menu.addAction('🖨️ Печать', self._print_vehicle)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _print_vehicle(self):
        """Печать данных авто через QPrinter."""
        from zavgar_app.utils.print_utils import print_document
        vid = self._get_selected_vehicle_id()
        if not vid:
            QMessageBox.information(self, 'Печать', 'Выберите авто в таблице')
            return
        row = self.table.currentRow()
        data = [self.table.item(row, c).text() for c in range(8)]
        print_document("Автомобиль",
            ['ID', 'Марка/Модель', 'Год', 'Госномер', 'Тип', 'Пробег', 'Водитель', 'Статус'],
            [data], self)

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
