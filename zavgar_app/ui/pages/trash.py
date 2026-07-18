"""
ui/pages/trash.py — Корзина (soft-delete)
=========================================

Восстановление или полное удаление записей из корзины.
Использует прямые SQL-запросы (модели не содержат deleted_at).
"""

from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from zavgar_app import db


# Таблицы и их описания для корзины
TRASH_TABLES = {
    'vehicles':  {'label': 'Авто',      'desc_col': "marka || ' ' || model || ' (' || gosnomer || ')'"},
    'drivers':   {'label': 'Водитель',  'desc_col': 'fio'},
    'parts':     {'label': 'Запчасть',  'desc_col': 'name'},
    'maintenance_schedules': {'label': 'ТО (план)', 'desc_col': "maintenance_type || ' — ' || interval_km || ' км'"},
    'maintenance_records':   {'label': 'ТО (факт)', 'desc_col': "maintenance_type || ' (' || mileage || ' км)'"},
    'timesheets': {'label': 'Табель',   'desc_col': "work_date || ' — ' || status"},
    'trip_logs':  {'label': 'Путевой',  'desc_col': "trip_date || ' — маршрут'"},
    'write_offs': {'label': 'Списание', 'desc_col': "act_number || ' от ' || act_date"},
}


class TrashPage(QWidget):
    """Страница корзины с возможностью восстановления или полного удаления."""

    def __init__(self, conn: sqlite3.Connection, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Заголовок
        header = QHBoxLayout()
        title = QLabel("🗑️ Корзина")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        # Toolbar
        restore_btn = QPushButton("♻️")
        restore_btn.setObjectName("actionBtn")
        restore_btn.setToolTip("Восстановить выбранное")
        restore_btn.clicked.connect(self._restore_selected)
        header.addWidget(restore_btn)

        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("actionDelete")
        delete_btn.setToolTip("Удалить полностью")
        delete_btn.clicked.connect(self._delete_permanently)
        header.addWidget(delete_btn)

        clear_btn = QPushButton("🧹")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.setToolTip("Очистить корзину")
        clear_btn.clicked.connect(self._clear_all)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Тип', 'Описание', 'Удалено'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 140)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

        # Подсказка
        hint = QLabel("💡 Записи хранятся в корзине 6 месяцев, затем удаляются автоматически")
        hint.setObjectName("hintText")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        self.refresh()

    def refresh(self):
        """Перезагрузить список удалённых записей через SQL."""
        rows = []
        for table, info in TRASH_TABLES.items():
            try:
                cur = self.conn.execute(
                    f"SELECT id, {info['desc_col']}, deleted_at "
                    f"FROM {table} WHERE deleted_at IS NOT NULL AND deleted_at != '' "
                    f"ORDER BY deleted_at DESC"
                )
                for r in cur.fetchall():
                    rows.append((r[0], info['label'], r[1] or '', r[2], table))
            except Exception:
                continue

        self.table.setRowCount(len(rows))
        for i, (item_id, item_type, desc, deleted_at, tbl) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(item_id)))
            self.table.setItem(i, 1, QTableWidgetItem(item_type))
            self.table.setItem(i, 2, QTableWidgetItem(desc))
            self.table.setItem(i, 3, QTableWidgetItem(deleted_at[:16] if deleted_at else ''))
            # Сохраняем имя таблицы в скрытой колонке
            hidden = QTableWidgetItem(tbl)
            hidden.setFlags(hidden.flags() & ~Qt.ItemIsSelectable)
            # Используем UserRole в колонке 0
            self.table.item(i, 0).setData(Qt.UserRole, tbl)

    def _get_selected(self) -> tuple[int, str] | None:
        """Получить (ID, table_name) выбранной записи."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item_id = int(self.table.item(row, 0).text())
        table_name = self.table.item(row, 0).data(Qt.UserRole)
        return item_id, table_name

    def _show_context_menu(self, pos):
        """Контекстное меню по правому клику."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)
        menu = QMenu(self)
        menu.addAction("♻️ Восстановить", self._restore_selected)
        menu.addAction("🗑️ Удалить полностью", self._delete_permanently)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _restore_selected(self):
        """Восстановить выбранную запись."""
        selected = self._get_selected()
        if not selected:
            QMessageBox.information(self, "Подсказка", "Выберите запись для восстановления")
            return

        item_id, table_name = selected
        reply = QMessageBox.question(
            self, 'Восстановление',
            'Восстановить эту запись?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            db.restore_from_trash(self.conn, table_name, item_id)
            self.refresh()

    def _delete_permanently(self):
        """Удалить запись полностью."""
        selected = self._get_selected()
        if not selected:
            QMessageBox.information(self, "Подсказка", "Выберите запись для удаления")
            return

        item_id, table_name = selected
        reply = QMessageBox.warning(
            self, 'Полное удаление',
            'Удалить запись полностью? Это действие необратимо!',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            db.hard_delete(self.conn, table_name, item_id)
            self.refresh()

    def _clear_all(self):
        """Очистить всю корзину."""
        reply = QMessageBox.warning(
            self, 'Очистка корзины',
            'Удалить ВСЕ записи из корзины? Это действие необратимо!',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for table in TRASH_TABLES:
                try:
                    self.conn.execute(
                        f"DELETE FROM {table} WHERE deleted_at IS NOT NULL AND deleted_at != ''"
                    )
                except Exception:
                    continue
            self.conn.commit()
            self.refresh()
