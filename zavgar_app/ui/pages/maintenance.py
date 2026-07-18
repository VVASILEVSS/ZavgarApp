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
        
        add_schedule_btn = QPushButton("➕")
        add_schedule_btn.setObjectName("primaryBtn")
        add_schedule_btn.setToolTip("Добавить график ТО")
        add_schedule_btn.clicked.connect(self._add_schedule)
        header.addWidget(add_schedule_btn)
        
        edit_schedule_btn = QPushButton("✏️")
        edit_schedule_btn.setObjectName("actionBtn")
        edit_schedule_btn.setToolTip("Редактировать график")
        edit_schedule_btn.clicked.connect(self._edit_schedule)
        header.addWidget(edit_schedule_btn)
        
        del_schedule_btn = QPushButton("🗑️")
        del_schedule_btn.setObjectName("actionDelete")
        del_schedule_btn.setToolTip("Удалить (в корзину)")
        del_schedule_btn.clicked.connect(self._delete_schedule)
        header.addWidget(del_schedule_btn)

        print_schedule_btn = QPushButton("🖨️")
        print_schedule_btn.setObjectName("ghostBtn")
        print_schedule_btn.setToolTip("Печать")
        print_schedule_btn.clicked.connect(self._print_schedule)
        header.addWidget(print_schedule_btn)

        schedules_layout.addLayout(header)

        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(7)
        self.schedules_table.setHorizontalHeaderLabels([
            "ID", "Автомобиль", "Тип ТО", "Интервал (км)", "Последнее ТО",
            "Следующее ТО", "Статус"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.schedules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.schedules_table.setColumnWidth(0, 50)
        self.schedules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedules_table.setAlternatingRowColors(True)
        self.schedules_table.verticalHeader().setVisible(False)
        self.schedules_table.verticalHeader().setDefaultSectionSize(44)
        self.schedules_table.setShowGrid(False)
        self.schedules_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schedules_table.customContextMenuRequested.connect(self._schedule_context_menu)
        self.schedules_table.selectionModel().selectionChanged.connect(
            lambda *_: self._update_toolbar())
        self.schedules_table.doubleClicked.connect(self._edit_schedule_selected)
        schedules_layout.addWidget(self.schedules_table)

        self.tabs.addTab(schedules_tab, "Графики ТО")

        # Таб 2: История ТО
        records_tab = QWidget()
        records_layout = QVBoxLayout(records_tab)

        header2 = QHBoxLayout()
        header2.addStretch()
        
        add_record_btn = QPushButton("➕")
        add_record_btn.setObjectName("primaryBtn")
        add_record_btn.setToolTip("Добавить запись ТО")
        add_record_btn.clicked.connect(self._add_record)
        header2.addWidget(add_record_btn)
        
        edit_record_btn = QPushButton("✏️")
        edit_record_btn.setObjectName("actionBtn")
        edit_record_btn.setToolTip("Редактировать запись")
        edit_record_btn.clicked.connect(self._edit_record)
        header2.addWidget(edit_record_btn)
        
        del_record_btn = QPushButton("🗑️")
        del_record_btn.setObjectName("actionDelete")
        del_record_btn.setToolTip("Удалить (в корзину)")
        del_record_btn.clicked.connect(self._delete_record)
        header2.addWidget(del_record_btn)

        print_record_btn = QPushButton("🖨️")
        print_record_btn.setObjectName("ghostBtn")
        print_record_btn.setToolTip("Печать")
        print_record_btn.clicked.connect(self._print_record)
        header2.addWidget(print_record_btn)

        records_layout.addLayout(header2)

        self.records_table = QTableWidget()
        self.records_table.setColumnCount(7)
        self.records_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Автомобиль", "Тип ТО", "Пробег", "Стоимость", "Примечания"
        ])
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.records_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.verticalHeader().setDefaultSectionSize(44)
        self.records_table.setShowGrid(False)
        self.records_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.records_table.customContextMenuRequested.connect(self._record_context_menu)
        self.records_table.selectionModel().selectionChanged.connect(
            lambda *_: self._update_toolbar())
        records_layout.addWidget(self.records_table)

        self.tabs.addTab(records_tab, "История ТО")

    def _load_data(self):
        """Загрузить графики и записи ТО."""
        # Графики
        schedules = db.list_maintenance_schedules(self.conn)
        vehicles = {v.id: v for v in db.list_vehicles(self.conn)}

        # Проверка просроченных ТО
        overdue_count = sum(
            1 for s in schedules
            if vehicles.get(s.vehicle_id) and s.is_overdue(vehicles[s.vehicle_id].current_mileage)
        )
        if overdue_count > 0:
            QMessageBox.warning(
                self,
                "⚠️ Просроченное ТО",
                f"Найдено {overdue_count} просроченных графиков ТО!\nПроверьте раздел 'Графики ТО'."
            )

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

    def _update_toolbar(self):
        """Обновить состояние кнопок тулбара."""
        pass  # Кнопки всегда активны, логика обработки пустого выбора внутри методов

    def _schedule_context_menu(self, pos):
        """Контекстное меню для графиков ТО."""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Редактировать")
        del_action = menu.addAction("🗑️ Удалить")
        menu.addSeparator()
        print_action = menu.addAction("🖨️ Печать")
        action = menu.exec(self.schedules_table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._edit_schedule()
        elif action == del_action:
            self._delete_schedule()
        elif action == print_action:
            self._print_schedule()

    def _record_context_menu(self, pos):
        """Контекстное меню для записей ТО."""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Редактировать")
        del_action = menu.addAction("🗑️ Удалить")
        menu.addSeparator()
        print_action = menu.addAction("🖨️ Печать")
        action = menu.exec(self.records_table.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._edit_record()
        elif action == del_action:
            self._delete_record()
        elif action == print_action:
            self._print_record()

    def _print_schedule(self):
        """Печать графика ТО."""
        row = self.schedules_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Печать", "Выберите график ТО")
            return
        data = [self.schedules_table.item(row, c).text() for c in range(7)]
        QMessageBox.information(self, "Печать графика ТО",
            f"ID: {data[0]}\nАвто: {data[1]}\nТип: {data[2]}\n"
            f"Интервал: {data[3]} км\nПоследнее: {data[4]}\n"
            f"Следующее: {data[5]}\nСтатус: {data[6]}")

    def _print_record(self):
        """Печать записи ТО."""
        row = self.records_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Печать", "Выберите запись ТО")
            return
        data = [self.records_table.item(row, c).text() for c in range(7)]
        QMessageBox.information(self, "Печать записи ТО",
            f"ID: {data[0]}\nДата: {data[1]}\nАвто: {data[2]}\n"
            f"Тип: {data[3]}\nПробег: {data[4]}\nСтоимость: {data[5]}\n"
            f"Примечания: {data[6]}")

    def _add_schedule(self):
        """Открыть диалог добавления графика ТО."""
        dialog = ScheduleDialog(self.conn, parent=self)
        if dialog.exec():
            self._load_data()

    def _edit_schedule_selected(self, index):
        """Редактировать график ТО (двойной клик)."""
        row = index.row()
        schedules = db.list_maintenance_schedules(self.conn)
        if 0 <= row < len(schedules):
            self._edit_schedule_item(schedules[row])

    def _show_schedule_details(self, index):
        """Показать детали графика ТО при двойном клике."""
        row = index.row()
        schedule_id = int(self.schedules_table.item(row, 0).text())
        
        # Получить данные
        vehicles = {v.id: v for v in db.list_vehicles(self.conn)}
        schedules = db.list_maintenance_schedules(self.conn)
        schedule = next((s for s in schedules if s.id == schedule_id), None)
        
        if not schedule:
            return
        
        vehicle = vehicles.get(schedule.vehicle_id)
        vehicle_name = vehicle.full_name() if vehicle else "Неизвестно"
        type_name = MAINTENANCE_TYPES.get(schedule.maintenance_type, schedule.maintenance_type)
        
        # Проверить просрочку
        is_overdue = vehicle and schedule.is_overdue(vehicle.current_mileage)
        
        details = f"""
Автомобиль: {vehicle_name}
Тип ТО: {type_name}
Интервал: {schedule.interval_km:,} км
Последнее ТО: {schedule.last_done_date or '—'} ({schedule.last_done_km:,} км)
Следующее ТО: {schedule.next_due_date or '—'} ({schedule.next_due_km:,} км)

{f"⚠️ ПРОСРОЧЕНО! Текущий пробег: {vehicle.current_mileage:,} км" if is_overdue else "✅ В срок"}

{f"Примечания: {schedule.notes}" if schedule.notes else ""}
"""
        QMessageBox.information(self, f"График ТО #{schedule_id}", details)

    def _edit_schedule(self):
        """Редактировать график ТО."""
        rows = self.schedules_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Подсказка", "Выберите график в таблице")
            return
        row = rows[0].row()
        sid = int(self.schedules_table.item(row, 0).text())
        # TODO: реализовать редактирование
        QMessageBox.information(self, "Info", f"Редактирование графика #{sid}")

    def _edit_schedule_item(self, schedule):
        """Редактировать график ТО (из кнопки действий)."""
        dialog = ScheduleDialog(self.conn, schedule=schedule, parent=self)
        if dialog.exec():
            self._load_data()

    def _delete_schedule_item(self, schedule_id: int):
        """Удалить график ТО (из кнопки действий)."""
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить выбранный график ТО?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.conn.execute("DELETE FROM maintenance_schedules WHERE id = ?", (schedule_id,))
            self.conn.commit()
            self._load_data()

    def _delete_schedule(self):
        """Удалить график ТО."""
        rows = self.schedules_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Подсказка", "Выберите график в таблице")
            return
        row = rows[0].row()
        sid = int(self.schedules_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить выбранный график ТО?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # TODO: soft-delete вместо hard-delete
            self.conn.execute("DELETE FROM maintenance_schedules WHERE id = ?", (sid,))
            self.conn.commit()
            self._load_data()

    def _add_record(self):
        """Открыть диалог добавления записи ТО."""
        dialog = RecordDialog(self.conn, parent=self)
        if dialog.exec():
            self._load_data()

    def _edit_record(self):
        """Редактировать запись ТО."""
        rows = self.records_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Подсказка", "Выберите запись в таблице")
            return
        row = rows[0].row()
        rid = int(self.records_table.item(row, 0).text())
        # TODO: реализовать редактирование
        QMessageBox.information(self, "Info", f"Редактирование записи #{rid}")

    def _edit_record_item(self, record):
        """Редактировать запись ТО (из кнопки действий)."""
        QMessageBox.information(self, "Info", f"Редактирование записи #{record.id}")

    def _delete_record_item(self, record_id: int):
        """Удалить запись ТО (из кнопки действий)."""
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить выбранную запись ТО?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.conn.execute("DELETE FROM maintenance_records WHERE id = ?", (record_id,))
            self.conn.commit()
            self._load_data()

    def _delete_record(self):
        """Удалить запись ТО."""
        rows = self.records_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Подсказка", "Выберите запись в таблице")
            return
        row = rows[0].row()
        rid = int(self.records_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "Удаление",
            "Удалить выбранную запись ТО?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # TODO: soft-delete вместо hard-delete
            self.conn.execute("DELETE FROM maintenance_records WHERE id = ?", (rid,))
            self.conn.commit()
            self._load_data()


class ScheduleDialog(QDialog):
    """Диалог добавления графика ТО."""

    # Шаблоны: (название, тип, интервал_км)
    TEMPLATES = [
        ("— Без шаблона —",       None,        None),
        ("Масло ДВС (бензин)",    'oil',       10000),
        ("Масло ДВС (дизель)",    'oil',       8000),
        ("Фильтры",               'filter',    15000),
        ("Тормозная жидкость",    'brake',     40000),
        ("Шины (сезонная)",       'tire',      30000),
        ("Полная диагностика",    'diagnostic', 20000),
    ]

    def __init__(self, conn, schedule=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.schedule = schedule  # None для создания, объект для редактирования
        self.setWindowTitle("Редактировать график ТО" if schedule else "Добавить график ТО")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Шаблон
        self.template_combo = QComboBox()
        for name, _, _ in self.TEMPLATES:
            self.template_combo.addItem(name)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        form.addRow("Шаблон:", self.template_combo)

        # Автомобиль
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setEditable(True)
        self.vehicle_combo.setInsertPolicy(QComboBox.NoInsert)
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

        # Заполнить данные если редактирование
        if self.schedule:
            self._fill_from_schedule()

    def _fill_from_schedule(self):
        """Заполнить форму данными существующего графика."""
        # Автомобиль
        for i in range(self.vehicle_combo.count()):
            if self.vehicle_combo.itemData(i) == self.schedule.vehicle_id:
                self.vehicle_combo.setCurrentIndex(i)
                break
        # Тип ТО
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.schedule.maintenance_type:
                self.type_combo.setCurrentIndex(i)
                break
        # Интервал
        self.interval_spin.setValue(self.schedule.interval_km)
        # Пробег
        self.last_km_spin.setValue(self.schedule.last_done_km)
        # Дата
        if self.schedule.last_done_date:
            self.last_date_edit.setDate(QDate.fromString(self.schedule.last_done_date, "yyyy-MM-dd"))
        # Заметки
        if self.schedule.notes:
            self.notes_edit.setPlainText(self.schedule.notes)

    def _on_template_changed(self, index):
        """Автозаполнение при выборе шаблона."""
        if index <= 0:
            return
        _, mtype, interval = self.TEMPLATES[index]
        if mtype:
            # Найти индекс типа в combo
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == mtype:
                    self.type_combo.setCurrentIndex(i)
                    break
        if interval:
            self.interval_spin.setValue(interval)

    def _save(self):
        """Сохранить график ТО."""
        vehicle_id = self.vehicle_combo.currentData()
        if not vehicle_id:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль")
            return

        interval = self.interval_spin.value()
        last_km = self.last_km_spin.value()
        next_km = last_km + interval

        if self.schedule:
            # Редактирование
            self.schedule.vehicle_id = vehicle_id
            self.schedule.maintenance_type = self.type_combo.currentData()
            self.schedule.interval_km = interval
            self.schedule.last_done_km = last_km
            self.schedule.last_done_date = self.last_date_edit.date().toString("yyyy-MM-dd")
            self.schedule.next_due_km = next_km
            self.schedule.notes = self.notes_edit.toPlainText().strip()
            db.update_maintenance_schedule(self.conn, self.schedule)
        else:
            # Создание
            schedule = MaintenanceSchedule(
                vehicle_id=vehicle_id,
                maintenance_type=self.type_combo.currentData(),
                interval_km=interval,
                last_done_km=last_km,
                last_done_date=self.last_date_edit.date().toString("yyyy-MM-dd"),
                next_due_km=next_km,
                next_due_date=None,
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
        self.vehicle_combo.setEditable(True)
        self.vehicle_combo.setInsertPolicy(QComboBox.NoInsert)
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
