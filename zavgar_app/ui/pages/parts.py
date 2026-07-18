"""
ui/pages/parts.py — Раздел "Склад запчастей"
=============================================

Таблица запчастей + приход/расход.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit,
    QMessageBox, QAbstractItemView, QTabWidget, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QAction

from zavgar_app.models import Part, PartTransaction
from zavgar_app import db
from zavgar_app.ui.theme import add_shadow


class PartDialog(QDialog):
    """Диалог добавления запчасти."""

    def __init__(self, part: Optional[Part] = None, parent=None):
        super().__init__(parent)
        self.part = part
        self.setWindowTitle('Добавить запчасть' if not part else 'Редактировать запчасть')
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Масло моторное 5W-30')
        form.addRow('Название:', self.name_input)

        self.article_input = QLineEdit()
        self.article_input.setPlaceholderText('OIL-5W30')
        form.addRow('Артикул:', self.article_input)

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText('Масла, фильтры, тормоза...')
        form.addRow('Категория:', self.category_input)

        self.unit_input = QLineEdit()
        self.unit_input.setText('шт')
        self.unit_input.setMaximumWidth(100)
        form.addRow('Единица:', self.unit_input)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0, 99_999)
        self.quantity_input.setDecimals(2)
        form.addRow('Количество:', self.quantity_input)

        self.min_quantity_input = QDoubleSpinBox()
        self.min_quantity_input.setRange(0, 99_999)
        self.min_quantity_input.setDecimals(2)
        form.addRow('Мин. остаток:', self.min_quantity_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999_999)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix('₸ ')
        form.addRow('Ср. цена:', self.price_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText('Заметки...')
        self.notes_input.setMaximumHeight(60)
        form.addRow('Заметки:', self.notes_input)

        layout.addLayout(form)

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

        if part:
            self.name_input.setText(part.name)
            self.article_input.setText(part.article or '')
            self.category_input.setText(part.category or '')
            self.unit_input.setText(part.unit)
            self.quantity_input.setValue(part.quantity)
            self.min_quantity_input.setValue(part.min_quantity)
            self.price_input.setValue(part.avg_price)
            self.notes_input.setPlainText(part.notes or '')

    def get_part(self) -> Part:
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        return Part(
            id=self.part.id if self.part else None,
            name=self.name_input.text().strip(),
            article=self.article_input.text().strip() or None,
            category=self.category_input.text().strip() or None,
            unit=self.unit_input.text().strip() or 'шт',
            quantity=self.quantity_input.value(),
            min_quantity=self.min_quantity_input.value(),
            avg_price=self.price_input.value(),
            notes=self.notes_input.toPlainText().strip() or None,
            created_at=self.part.created_at if self.part else now,
            updated_at=now,
        )


class TransactionDialog(QDialog):
    """Диалог прихода/расхода запчасти."""

    def __init__(self, part: Part, parent=None):
        super().__init__(parent)
        self.part = part
        self.setWindowTitle(f'{part.name} — Приход/Расход')
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        info = QLabel(f'Текущий остаток: **{part.quantity} {part.unit}**')
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Приход (＋)', 'Расход (－)'])
        form.addRow('Тип:', self.type_combo)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 99_999)
        self.quantity_input.setDecimals(2)
        form.addRow('Количество:', self.quantity_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999_999)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix('₸ ')
        form.addRow('Цена:', self.price_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText('Причина, номер заявки...')
        self.notes_input.setMaximumHeight(60)
        form.addRow('Заметки:', self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton('Провести')
        save_btn.setObjectName('primaryBtn')
        save_btn.clicked.connect(self.accept)
        add_shadow(save_btn, blur=10, opacity=20, y_offset=2)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_transaction(self) -> tuple[PartTransaction, float]:
        """Вернуть транзакцию и новый остаток."""
        is_incoming = self.type_combo.currentIndex() == 0
        qty = self.quantity_input.value()
        new_qty = self.part.quantity + qty if is_incoming else self.part.quantity - qty

        tx = PartTransaction(
            part_id=self.part.id,
            transaction_type='in' if is_incoming else 'out',
            quantity=qty,
            price=self.price_input.value(),
            notes=self.notes_input.toPlainText().strip() or None,
            transaction_date=datetime.now().isoformat(sep=' ', timespec='seconds'),
        )
        return tx, new_qty


class PartsPage(QWidget):
    """Раздел "Склад запчастей"."""

    def __init__(self, conn: sqlite3.Connection, parent=None):
        super().__init__(parent)
        self.conn = conn
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # Заголовок + кнопки
        header = QHBoxLayout()
        title = QLabel('🔧 Склад запчастей')
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton('＋')
        add_btn.setObjectName('primaryBtn')
        add_btn.setToolTip('Добавить запчасть')
        add_btn.clicked.connect(self._add_part)
        add_shadow(add_btn, blur=10, opacity=20, y_offset=2)
        header.addWidget(add_btn)

        edit_btn = QPushButton('✏️')
        edit_btn.setObjectName('actionBtn')
        edit_btn.setToolTip('Редактировать запчасть')
        edit_btn.clicked.connect(self._edit_part)
        header.addWidget(edit_btn)

        del_btn = QPushButton('🗑️')
        del_btn.setObjectName('actionDelete')
        del_btn.setToolTip('Удалить (в корзину)')
        del_btn.clicked.connect(self._delete_part)
        header.addWidget(del_btn)

        tx_btn = QPushButton('💰')
        tx_btn.setObjectName('actionBtn')
        tx_btn.setToolTip('Приход/Расход')
        tx_btn.clicked.connect(self._add_transaction)
        header.addWidget(tx_btn)

        print_btn = QPushButton('🖨️')
        print_btn.setObjectName('ghostBtn')
        print_btn.setToolTip('Печать')
        print_btn.clicked.connect(self._print_part)
        header.addWidget(print_btn)

        layout.addLayout(header)

        # Табы: Остатки | История
        self.tabs = QTabWidget()

        # Таблица остатков
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(7)
        self.parts_table.setHorizontalHeaderLabels([
            'Название', 'Артикул', 'Категория', 'Остаток', 'Мин.', 'Ср. цена', 'ID'
        ])
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.parts_table.setColumnWidth(6, 40)
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parts_table.verticalHeader().setVisible(False)
        self.parts_table.setShowGrid(False)
        self.parts_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.parts_table.customContextMenuRequested.connect(self._show_context_menu)
        self.parts_table.doubleClicked.connect(self._edit_part)
        self.tabs.addTab(self.parts_table, 'Остатки')

        # Таблица транзакций
        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(6)
        self.tx_table.setHorizontalHeaderLabels([
            'Дата', 'Запчасть', 'Тип', 'Кол-во', 'Цена', 'Заметки'
        ])
        self.tx_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tx_table.setAlternatingRowColors(True)
        self.tx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tx_table.verticalHeader().setVisible(False)
        self.tx_table.setShowGrid(False)
        self.tabs.addTab(self.tx_table, 'История')

        layout.addWidget(self.tabs)

        self.refresh()

    def refresh(self):
        """Перезагрузить данные."""
        parts = db.list_parts(self.conn)
        self.parts_table.setRowCount(len(parts))

        for row, p in enumerate(parts):
            name_item = QTableWidgetItem(p.name)
            name_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 0, name_item)
            
            article_item = QTableWidgetItem(p.article or '')
            article_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 1, article_item)
            
            category_item = QTableWidgetItem(p.category or '')
            category_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 2, category_item)

            qty_item = QTableWidgetItem(f'{p.quantity:.2f} {p.unit}')
            qty_item.setForeground(QColor('#ef4444' if p.quantity <= p.min_quantity else '#e4e4e7'))
            self.parts_table.setItem(row, 3, qty_item)

            min_qty_item = QTableWidgetItem(f'{p.min_quantity:.2f}')
            min_qty_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 4, min_qty_item)
            
            price_item = QTableWidgetItem(f'₸ {p.avg_price:,.2f}')
            price_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 5, price_item)
            
            id_item = QTableWidgetItem(str(p.id))
            id_item.setForeground(QColor('#e4e4e7'))
            self.parts_table.setItem(row, 6, id_item)

        # Транзакции
        transactions = db.list_part_transactions(self.conn)
        self.tx_table.setRowCount(len(transactions))

        for row, tx in enumerate(transactions):
            self.tx_table.setItem(row, 0, QTableWidgetItem(tx.transaction_date[:16]))
            
            part = db.get_part(self.conn, tx.part_id)
            self.tx_table.setItem(row, 1, QTableWidgetItem(part.name if part else f'ID {tx.part_id}'))
            
            type_text = '＋ Приход' if tx.transaction_type == 'in' else '－ Расход'
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor('#10b981' if tx.transaction_type == 'in' else '#ef4444'))
            self.tx_table.setItem(row, 2, type_item)

            self.tx_table.setItem(row, 3, QTableWidgetItem(f'{tx.quantity:.2f}'))
            self.tx_table.setItem(row, 4, QTableWidgetItem(f'₸ {tx.price:,.2f}'))
            self.tx_table.setItem(row, 5, QTableWidgetItem(tx.notes or ''))

    def _get_selected_part_id(self) -> Optional[int]:
        rows = self.parts_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.parts_table.item(row, 6)
        return int(item.text()) if item else None

    def _show_context_menu(self, pos):
        """Контекстное меню по правому клику."""
        row = self.parts_table.rowAt(pos.y())
        if row < 0:
            return
        self.parts_table.selectRow(row)
        menu = QMenu(self)
        menu.addAction('✏️ Редактировать', self._edit_part)
        menu.addAction('🗑️ Удалить', self._delete_part)
        menu.addAction('💰 Приход/Расход', self._add_transaction)
        menu.addSeparator()
        menu.addAction('🖨️ Печать', self._print_part)
        menu.exec(self.parts_table.viewport().mapToGlobal(pos))

    def _print_part(self):
        """Печать данных запчасти."""
        pid = self._get_selected_part_id()
        if not pid:
            QMessageBox.information(self, 'Печать', 'Выберите запчасть в таблице')
            return
        row = self.parts_table.currentRow()
        data = [self.parts_table.item(row, c).text() for c in range(7)]
        QMessageBox.information(self, 'Печать запчасти',
            f"Название: {data[0]}\nАртикул: {data[1]}\nКатегория: {data[2]}\n"
            f"Остаток: {data[3]}\nМин.: {data[4]}\nСр. цена: {data[5]}")

    def _add_part(self):
        dlg = PartDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            p = dlg.get_part()
            if not p.name:
                QMessageBox.warning(self, 'Ошибка', 'Укажите название запчасти')
                return
            db.create_part(self.conn, p)
            self.refresh()

    def _edit_part(self):
        pid = self._get_selected_part_id()
        if not pid:
            QMessageBox.information(self, 'Подсказка', 'Выберите запчасть в таблице')
            return

        part = db.get_part(self.conn, pid)
        if not part:
            return

        dlg = PartDialog(part=part, parent=self)
        if dlg.exec() == QDialog.Accepted:
            p = dlg.get_part()
            # Обновляем все поля через прямые SQL
            self.conn.execute("""
                UPDATE parts SET name=?, article=?, category=?, unit=?, quantity=?,
                    min_quantity=?, avg_price=?, notes=?, updated_at=?
                WHERE id=?
            """, (p.name, p.article, p.category, p.unit, p.quantity,
                  p.min_quantity, p.avg_price, p.notes, p.updated_at, p.id))
            self.conn.commit()
            self.refresh()

    def _delete_part(self):
        pid = self._get_selected_part_id()
        if not pid:
            QMessageBox.information(self, 'Подсказка', 'Выберите запчасть в таблице')
            return
        reply = QMessageBox.question(self, 'Удаление', 'Удалить запчасть в корзину?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_part(self.conn, pid)
            self.refresh()

    def _add_transaction(self):
        pid = self._get_selected_part_id()
        if not pid:
            QMessageBox.information(self, 'Подсказка', 'Выберите запчасть для проведения операции')
            return

        part = db.get_part(self.conn, pid)
        if not part:
            return

        dlg = TransactionDialog(part, parent=self)
        if dlg.exec() == QDialog.Accepted:
            tx, new_qty = dlg.get_transaction()
            if new_qty < 0:
                QMessageBox.warning(self, 'Ошибка', f'Недостаточно остатка (текущий: {part.quantity})')
                return

            db.create_part_transaction(self.conn, tx)
            db.update_part_quantity(self.conn, pid, new_qty)
            self.refresh()
