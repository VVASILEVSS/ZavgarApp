"""
ui/pages/calendar_page.py — Интерактивный календарь табеля учёта
================================================================

Компактный календарь + статистика-шапка + детали по ширине + праздники.
"""
from __future__ import annotations
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget,
    QListWidget, QListWidgetItem, QFrame, QComboBox, QSizePolicy,
    QPushButton, QDialog, QFormLayout, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QBrush, QFont

from zavgar_app import db
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QFrame


class _NoFocusDelegate(QStyledItemDelegate):
    """Убирает нативную рамку фокуса Windows на ячейках."""
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.state &= ~QStyle.State_HasFocus


class CalendarPage(QWidget):
    """Интерактивный календарь табеля учёта рабочего времени."""

    STATUS_MAP = {
        'work':          ('Работа',       '#10b981', '✓'),
        'day_off':       ('Выходной',     '#6b7280', '○'),
        'sick':          ('Больничный',   '#ef4444', '✗'),
        'vacation':      ('Отпуск',       '#f59e0b', '⊘'),
        'business_trip': ('Командировка', '#3b82f6', '→'),
    }

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._holidays = {}  # {date_str: name}
        self._setup_ui()
        self._load_drivers()
        self._load_holidays()
        self._update_view()

    # ───────────────────────── UI ─────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # ═══ ШАПКА: статистика + фильтр водителя ═══
        header = QHBoxLayout()
        header.setSpacing(20)

        title = QLabel("📅 Табель учёта")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        header.addWidget(title)

        header.addSpacing(16)

        # 4 карточки-метрики
        self.total_hours_lbl = self._metric('#6366f1')
        self.work_days_lbl   = self._metric('#10b981')
        self.avg_hours_lbl   = self._metric('#f59e0b')
        self.sick_days_lbl   = self._metric('#ef4444')

        for lbl, sub in [
            (self.total_hours_lbl, 'Часов'),
            (self.work_days_lbl,   'Рабочих'),
            (self.avg_hours_lbl,   'Средний'),
            (self.sick_days_lbl,   'Больничных'),
        ]:
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(lbl, 0, Qt.AlignHCenter)
            s = QLabel(sub)
            s.setObjectName("hintText")
            col.addWidget(s, 0, Qt.AlignHCenter)
            header.addLayout(col)

        header.addStretch()

        # Фильтр водителя
        fl = QLabel("Водитель:")
        fl.setStyleSheet("font-weight: 500;")
        header.addWidget(fl)

        self.driver_combo = QComboBox()
        self.driver_combo.setMinimumWidth(220)
        self.driver_combo.currentIndexChanged.connect(self._update_view)
        header.addWidget(self.driver_combo)

        # Кнопка управления праздниками
        holidays_btn = QPushButton('📅 Праздники')
        holidays_btn.setToolTip('Управление праздничными днями')
        holidays_btn.clicked.connect(self._manage_holidays)
        header.addWidget(holidays_btn)

        root.addLayout(header, 0)  # Шапка не растягивается

        # ═══ НИЖНЯЯ ЧАСТЬ: календарь + детали ═══
        body = QHBoxLayout()
        body.setSpacing(16)

        # Календарь компактный
        cal_frame = QFrame()
        cal_frame.setFixedWidth(380)
        cal_layout = QVBoxLayout(cal_frame)
        cal_layout.setContentsMargins(0, 0, 0, 0)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setFixedHeight(320)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        self.calendar.currentPageChanged.connect(self._update_view)
        cal_layout.addWidget(self.calendar)

        # Легенда
        legend = QHBoxLayout()
        legend.setSpacing(10)
        legend.setContentsMargins(4, 8, 4, 0)
        for status, (text, color, _) in self.STATUS_MAP.items():
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 12px;")
            legend.addWidget(dot)
            t = QLabel(text)
            t.setObjectName("hintText")
            legend.addWidget(t)
        legend.addStretch()
        cal_layout.addLayout(legend)

        body.addWidget(cal_frame)

        # Детали — занимает всё свободное место
        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(6)

        self.date_label = QLabel("Выберите дату")
        self.date_label.setStyleSheet("font-size: 16px; font-weight: 600; padding: 4px 0;")
        details_layout.addWidget(self.date_label)

        self.details_list = QListWidget()
        self.details_list.setWordWrap(True)
        self.details_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.details_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; }
            QListWidget::item { padding: 10px 12px; border-radius: 6px; }
        """)
        details_layout.addWidget(self.details_list)

        body.addWidget(details_frame, 1)
        root.addLayout(body, 1)

    def _metric(self, color) -> QLabel:
        lbl = QLabel("0")
        lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {color};")
        return lbl

    # ───────────────────── логика ──────────────────────

    def _load_drivers(self):
        self.driver_combo.clear()
        self.driver_combo.addItem("Все водители", None)
        for d in db.list_drivers(self.conn):
            self.driver_combo.addItem(d.fio, d.id)

    def _current_month(self) -> str:
        return f"{self.calendar.yearShown():04d}-{self.calendar.monthShown():02d}"

    def _get_timesheets(self, driver_id=None, month=None):
        ts = db.list_timesheets(self.conn)
        if driver_id:
            ts = [t for t in ts if t.driver_id == driver_id]
        if month:
            ts = [t for t in ts if t.work_date.startswith(month)]
        return ts

    def _update_view(self):
        self._highlight_days()
        self._update_stats()
        self._on_date_selected()

    def _highlight_days(self):
        driver_id = self.driver_combo.currentData()
        month = self._current_month()
        timesheets = self._get_timesheets(driver_id, month)

        # Сброс
        for day in range(1, 32):
            qdate = QDate(self.calendar.yearShown(), self.calendar.monthShown(), day)
            if qdate.isValid():
                self.calendar.setDateTextFormat(qdate, QTextCharFormat())

        # Подсветка
        for ts in timesheets:
            qdate = QDate.fromString(ts.work_date, "yyyy-MM-dd")
            if not qdate.isValid() or qdate.month() != self.calendar.monthShown():
                continue
            fmt = QTextCharFormat()
            _, color, _ = self.STATUS_MAP.get(ts.status, ('?', '#6b7280', '?'))
            fmt.setBackground(QBrush(QColor(color)))
            fmt.setForeground(QBrush(QColor("#ffffff")))
            fmt.setFontWeight(QFont.Bold)
            self.calendar.setDateTextFormat(qdate, fmt)

    def _update_stats(self):
        driver_id = self.driver_combo.currentData()
        month = self._current_month()
        ts = self._get_timesheets(driver_id, month)

        total = sum(t.hours for t in ts if t.status == 'work')
        work  = sum(1 for t in ts if t.status == 'work')
        sick  = sum(1 for t in ts if t.status == 'sick')
        avg   = total / work if work else 0

        self.total_hours_lbl.setText(f"{total:.0f}")
        self.work_days_lbl.setText(str(work))
        self.avg_hours_lbl.setText(f"{avg:.1f}")
        self.sick_days_lbl.setText(str(sick))

    def _on_date_selected(self):
        qdate = self.calendar.selectedDate()
        date_str = qdate.toString("yyyy-MM-dd")

        self.date_label.setText(f"📆 {qdate.toString('dd.MM.yyyy')}")
        self.details_list.clear()

        driver_id = self.driver_combo.currentData()
        ts_all = self._get_timesheets(driver_id)
        drivers = {d.id: d.fio for d in db.list_drivers(self.conn)}

        items = [t for t in ts_all if t.work_date == date_str]

        for ts in items:
            name = drivers.get(ts.driver_id, "?")
            status_text, color, sym = self.STATUS_MAP.get(ts.status, ('?', '#6b7280', '?'))

            parts = [f"{sym} {name} — {status_text}"]
            if ts.start_time and ts.end_time:
                parts.append(f"⏱ {ts.start_time}–{ts.end_time}")
            if ts.status == 'work':
                parts.append(f"• {ts.hours:.1f}ч")
            if ts.notes:
                parts.append(f"💬 {ts.notes}")

            item = QListWidgetItem("   ".join(parts))
            item.setForeground(QColor(color))
            self.details_list.addItem(item)

        if not items:
            # Проверить, является ли это праздником
            if date_str in self._holidays:
                holiday_name = self._holidays[date_str]
                item = QListWidgetItem(f"🎉 {holiday_name}")
                item.setForeground(QColor("#f59e0b"))
                self.details_list.addItem(item)
                item = QListWidgetItem("Оплата в двойном размере")
                item.setForeground(QColor("#9ca3af"))
                self.details_list.addItem(item)
            else:
                item = QListWidgetItem("Нет записей на эту дату")
                item.setForeground(QColor("#9ca3af"))
                self.details_list.addItem(item)

    def _load_holidays(self):
        """Загрузить праздники из БД."""
        try:
            cursor = self.conn.execute("SELECT holiday_date, name FROM holidays")
            self._holidays = {row[0]: row[1] for row in cursor.fetchall()}
        except Exception:
            # Таблица может не существовать
            self._holidays = {}

    def _manage_holidays(self):
        """Открыть диалог управления праздниками."""
        dialog = HolidayDialog(self.conn, self._holidays, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_holidays()
            self._update_view()


class HolidayDialog(QDialog):
    """Диалог управления праздничными днями."""

    # Стандартные праздники РК
    DEFAULT_HOLIDAYS = [
        ("01-01", "Новый год"),
        ("01-02", "Второй день Нового года"),
        ("03-08", "Международный женский день"),
        ("03-22", "Наурыз мейрамы"),
        ("05-01", "Праздник единства народа Казахстана"),
        ("05-07", "День защитника Отечества"),
        ("05-09", "День Победы"),
        ("07-06", "День столицы"),
        ("08-30", "День Конституции"),
        ("12-01", "День Первого Президента"),
        ("12-16", "День Независимости"),
        ("12-17", "День Независимости"),
    ]

    def __init__(self, conn, holidays: dict, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.holidays = holidays.copy()
        self.setWindowTitle("Управление праздниками")
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Таблица праздников
        self.table = QTableWidget()
        # Убрать рамку виджета (border вокруг таблицы)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Дата", "Название"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setItemDelegate(_NoFocusDelegate(self.table))
        self.table.doubleClicked.connect(self._edit_holiday_popup)
        layout.addWidget(self.table)

        self._refresh_table()

        # Кнопки
        btn_layout = QHBoxLayout()

        add_default_btn = QPushButton("Добавить стандартные РК")
        add_default_btn.clicked.connect(self._add_default_holidays)
        btn_layout.addWidget(add_default_btn)

        add_custom_btn = QPushButton("Добавить свой")
        add_custom_btn.clicked.connect(self._add_custom_holiday)
        btn_layout.addWidget(add_custom_btn)

        del_selected_btn = QPushButton("🗑️ Удалить выбранный")
        del_selected_btn.setObjectName("actionDelete")
        del_selected_btn.clicked.connect(self._delete_selected_holiday)
        btn_layout.addWidget(del_selected_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _refresh_table(self):
        """Обновить таблицу праздников."""
        sorted_holidays = sorted(self.holidays.items())
        self.table.setRowCount(len(sorted_holidays))

        for row, (date_str, name) in enumerate(sorted_holidays):
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(name))

    def _add_default_holidays(self):
        """Добавить стандартные праздники РК для текущего года."""
        year = QDate.currentDate().year()
        for month_day, name in self.DEFAULT_HOLIDAYS:
            date_str = f"{year}-{month_day}"
            if date_str not in self.holidays:
                self.holidays[date_str] = name
        self._refresh_table()

    def _edit_holiday_popup(self, index):
        """Открыть popup для редактирования праздника при двойном клике."""
        row = index.row()
        date_str = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        
        from PySide6.QtWidgets import QDialog as QD
        dialog = QD(self)
        dialog.setWindowTitle("Редактировать праздник")
        layout = QVBoxLayout(dialog)
        
        from PySide6.QtWidgets import QLineEdit
        name_edit = QLineEdit()
        name_edit.setText(name)
        name_edit.setPlaceholderText("Название праздника")
        layout.addWidget(name_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QD.Accepted:
            new_name = name_edit.text().strip()
            if new_name:
                self.holidays[date_str] = new_name
                self._refresh_table()

    def _add_custom_holiday(self):
        """Добавить свой праздник."""
        from PySide6.QtWidgets import QDialog as QD
        dialog = QD(self)
        dialog.setWindowTitle("Добавить праздник")
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        form.addRow("Дата:", date_edit)

        from PySide6.QtWidgets import QLineEdit
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Название праздника")
        form.addRow("Название:", name_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Добавить")
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QD.Accepted:
            date_str = date_edit.date().toString("yyyy-MM-dd")
            name = name_edit.text().strip()
            if name:
                self.holidays[date_str] = name
                self._refresh_table()

    def _delete_holiday(self, date_str: str):
        """Удалить праздник."""
        if date_str in self.holidays:
            del self.holidays[date_str]
            self._refresh_table()

    def _delete_selected_holiday(self):
        """Удалить выбранный праздник из таблицы."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Удаление", "Выберите праздник для удаления")
            return
        date_str = self.table.item(row, 0).text()
        if date_str in self.holidays:
            del self.holidays[date_str]
            self._refresh_table()

    def _save(self):
        """Сохранить праздники в БД."""
        try:
            # Создать таблицу если не существует
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    holiday_date TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)

            # Удалить все и добавить заново
            self.conn.execute("DELETE FROM holidays")
            for date_str, name in self.holidays.items():
                self.conn.execute(
                    "INSERT INTO holidays (holiday_date, name) VALUES (?, ?)",
                    (date_str, name)
                )
            self.conn.commit()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")
