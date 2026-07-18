"""
ui/pages/trash.py — Корзина (soft-delete)
=========================================

Восстановление или полное удаление записей из корзины.
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Тип', 'Описание', 'Удалено', 'Таблица'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
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
        hint.setStyleSheet("color: #9ca3af; font-size: 12px; padding: 8px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        self.refresh()

    def refresh(self):
        """Перезагрузить список удалённых записей."""
        deleted = []
        
        # Авто
        vehicles = db.list_vehicles(self.conn, include_deleted=True)
        for v in vehicles:
            if v.deleted_at:
                deleted.append((v.id, 'Авто', f"{v.marka} {v.model} ({v.gosnomer})", v.deleted_at, 'vehicles'))
        
        # Водители
        drivers = db.list_drivers(self.conn, include_deleted=True)
        for d in drivers:
            if d.deleted_at:
                deleted.append((d.id, 'Водитель', d.fio, d.deleted_at, 'drivers'))
        
        # Запчасти
        parts = db.list_parts(self.conn, include_deleted=True)
        for p in parts:
            if p.deleted_at:
                deleted.append((p.id, 'Запчасть', p.name, p.deleted_at, 'parts'))

        self.table.setRowCount(len(deleted))

        for row, (item_id, item_type, description, deleted_at, table_name) in enumerate(deleted):
            self.table.setItem(row, 0, QTableWidgetItem(str(item_id)))
            self.table.setItem(row, 1, QTableWidgetItem(item_type))
            self.table.setItem(row, 2, QTableWidgetItem(description))
            self.table.setItem(row, 3, QTableWidgetItem(deleted_at[:16] if deleted_at else ''))
            self.table.setItem(row, 4, QTableWidgetItem(table_name))

    def _get_selected_item(self) -> tuple[int, str] | None:
        """Получить ID и таблицу выбранной записи."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item_id = self.table.item(row, 0).text()
        table_name = self.table.item(row, 4).text()
        return int(item_id), table_name

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
        selected = self._get_selected_item()
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
            QMessageBox.information(self, "Успех", "Запись восстановлена")

    def _delete_permanently(self):
        """Удалить запись полностью (без возможности восстановления)."""
        selected = self._get_selected_item()
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
            QMessageBox.information(self, "Успех", "Запись удалена полностью")

    def _clear_all(self):
        """Очистить всю корзину."""
        reply = QMessageBox.warning(
            self, 'Очистка корзины',
            'Удалить ВСЕ записи из корзины? Это действие необратимо!',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Очистить все таблицы
            for table in ['vehicles', 'drivers', 'parts']:
                deleted = []
                if table == 'vehicles':
                    items = db.list_vehicles(self.conn, include_deleted=True)
                    deleted = [v.id for v in items if v.deleted_at]
                elif table == 'drivers':
                    items = db.list_drivers(self.conn, include_deleted=True)
                    deleted = [d.id for d in items if d.deleted_at]
                elif table == 'parts':
                    items = db.list_parts(self.conn, include_deleted=True)
                    deleted = [p.id for p in items if p.deleted_at]
                
                for item_id in deleted:
                    db.hard_delete(self.conn, table, item_id)
            
            self.refresh()
            QMessageBox.information(self, "Успех", "Корзина очищена")
