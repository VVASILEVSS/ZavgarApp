"""
ui/pages/timesheets.py — Табель учёта рабочего времени
"""
from __future__ import annotations
from datetime import datetime, date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDateEdit,
    QTimeEdit, QComboBox, QDoubleSpinBox, QTextEdit, QMessageBox, QSpinBox,
    QMenu
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor, QAction

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
        self.driver_combo.setEditable(True)
        self.driver_combo.setInsertPolicy(QComboBox.NoInsert)
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

        # Toolbar действий
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.setObjectName("actionBtn")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_selected_toolbar)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.setObjectName("actionDelete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected_toolbar)
        toolbar.addWidget(self.delete_btn)

        self.print_btn = QPushButton("🖨️ Печать")
        self.print_btn.setObjectName("actionBtn")
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(self._print_selected)
        toolbar.addWidget(self.print_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Водитель", "Статус", "Начало", "Окончание", "Часов"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_selected)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._update_toolbar)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        """Обновить таблицу."""
        timesheets = db.list_timesheets(self.conn)
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
        
        self.table.setRowCount(len(timesheets))
        
        for row, ts in enumerate(timesheets):
            # Store timesheet ID in first column item for retrieval
            date_item = QTableWidgetItem(ts.work_date)
            date_item.setData(Qt.UserRole, ts.id)
            self.table.setItem(row, 0, date_item)
            self.table.setItem(row, 1, QTableWidgetItem(drivers.get(ts.driver_id, "?")))
            
            status_item = QTableWidgetItem(TimesheetDialog.STATUS_MAP.get(ts.status, ts.status))
            color = self.STATUS_COLORS.get(ts.status, '#6b7280')
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 2, status_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(ts.start_time or ""))
            self.table.setItem(row, 4, QTableWidgetItem(ts.end_time or ""))
            self.table.setItem(row, 5, QTableWidgetItem(f"{ts.hours:.1f}"))

        self._update_toolbar()

    def _get_selected_timesheet(self) -> Timesheet | None:
        """Получить Timesheet по выбранной строке."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        timesheets = db.list_timesheets(self.conn)
        if 0 <= row < len(timesheets):
            return timesheets[row]
        return None

    def _get_selected_timesheet_ids(self) -> list[int]:
        """Получить ID всех выбранных строк."""
        rows = sorted(set(idx.row() for idx in self.table.selectionModel().selectedRows()))
        timesheets = db.list_timesheets(self.conn)
        return [timesheets[r].id for r in rows if 0 <= r < len(timesheets)]

    def _update_toolbar(self):
        """Обновить состояние кнопок toolbar."""
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.print_btn.setEnabled(has_selection)

    def _show_context_menu(self, pos):
        """Контекстное меню по правому клику на строке."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)

        menu = QMenu(self)
        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(self._edit_selected_toolbar)
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self._delete_selected_toolbar)
        menu.addAction(delete_action)

        menu.addSeparator()

        print_action = QAction("🖨️ Печать", self)
        print_action.triggered.connect(self._print_selected)
        menu.addAction(print_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

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

    def _edit_selected(self, index):
        """Редактировать выбранную запись (двойной клик)."""
        row = index.row()
        timesheets = db.list_timesheets(self.conn)
        if 0 <= row < len(timesheets):
            self._edit_timesheet(timesheets[row])

    def _edit_selected_toolbar(self):
        """Редактировать выбранную запись (toolbar/контекстное меню)."""
        ts = self._get_selected_timesheet()
        if ts:
            self._edit_timesheet(ts)

    def _delete_selected_toolbar(self):
        """Удалить выбранные записи (toolbar/контекстное меню)."""
        ids = self._get_selected_timesheet_ids()
        if not ids:
            return
        count = len(ids)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить {count} запис{'ь' if count == 1 else 'и'} из табеля?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for tid in ids:
                db.delete_timesheet(self.conn, tid)
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

    def _print_selected(self):
        """Печать выбранных записей табеля."""
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QTextDocument

        ids = self._get_selected_timesheet_ids()
        if not ids:
            return

        timesheets = db.list_timesheets(self.conn)
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}
        selected = [ts for ts in timesheets if ts.id in ids]

        # Build HTML table for printing
        rows_html = ""
        for ts in selected:
            status_label = TimesheetDialog.STATUS_MAP.get(ts.status, ts.status)
            rows_html += (
                f"<tr>"
                f"<td>{ts.work_date}</td>"
                f"<td>{drivers.get(ts.driver_id, '?')}</td>"
                f"<td>{status_label}</td>"
                f"<td>{ts.start_time or ''}</td>"
                f"<td>{ts.end_time or ''}</td>"
                f"<td>{ts.hours:.1f}</td>"
                f"</tr>"
            )

        html = f"""
        <h2>Табель учёта рабочего времени</h2>
        <p>Дата печати: {date.today().strftime('%d.%m.%Y')}</p>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%;">
            <thead>
                <tr style="background:#f0f0f0;">
                    <th>Дата</th><th>Водитель</th><th>Статус</th>
                    <th>Начало</th><th>Окончание</th><th>Часов</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """

        doc = QTextDocument()
        doc.setHtml(html)

        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.Accepted:
            doc.print_(printer)
