"""
ui/theme.py — Система тем ZavgarApp (dark + light)
===================================================

Два стиля:
- DarkTheme  — glassmorphism, indigo акцент (#6366f1), вдохновлён Linear/Vercel
- LightTheme — чистая светлая тема (Notion/Linear Light), мягкие тени

Обе темы используют objectName-селекторы (QFrame#card, QPushButton#primaryBtn).
Переключение: theme_manager.apply_theme('dark') или 'light'.
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QPushButton, QGraphicsDropShadowEffect, QFrame,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QBrush


# ════════════════════════════════════════════════════════════════════
# ТЁМНАЯ ТЕМА
# ════════════════════════════════════════════════════════════════════

DARK_QSS = """
/* Global */
QMainWindow { background-color: #0a0a0f; color: #e4e4e7; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #e4e4e7; }

/* Sidebar */
QFrame#sidebar {
    background-color: #11111b;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.06);
}

QFrame#sidebarSeparator {
    background-color: rgba(255,255,255,0.08);
}

/* Sidebar nav items */
QPushButton#navItem {
    background-color: transparent;
    color: #71717a;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}
QPushButton#navItem:hover {
    background-color: rgba(255,255,255,0.06);
    color: #e4e4e7;
}
QPushButton#navItem[active="true"],
QPushButton#navItem:checked {
    background-color: rgba(99,102,241,0.15);
    color: #a5b4fc;
    font-weight: 600;
}

/* Glass cards */
QFrame#card {
    background-color: rgba(30,30,46,180);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px;
}
QFrame#card:hover {
    border: 1px solid rgba(99,102,241,0.25);
}

/* Stat card */
QFrame#statCard {
    background-color: rgba(24,24,37,220);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 20px;
}

/* Buttons */
QPushButton {
    background-color: rgba(39,39,56,200);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background-color: rgba(55,55,80,220);
    border: 1px solid rgba(255,255,255,0.20);
}
QPushButton:pressed {
    background-color: rgba(45,45,68,255);
}
QPushButton:disabled {
    background-color: rgba(30,30,42,100);
    color: rgba(228,228,231,0.4);
}

QPushButton#primaryBtn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #818cf8; }
QPushButton#primaryBtn:pressed { background-color: #4f46e5; }

/* Plus/add icons — always white text on primary buttons */
QPushButton#primaryBtn {
    color: #ffffff !important;
}

QPushButton#dangerBtn {
    background-color: rgba(239,68,68,0.15);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.30);
    border-radius: 10px;
}
QPushButton#dangerBtn:hover {
    background-color: rgba(239,68,68,0.30);
    color: #fecaca;
}

QPushButton#ghostBtn {
    background-color: transparent;
    color: #a1a1aa;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
}
QPushButton#ghostBtn:hover {
    background-color: rgba(255,255,255,0.06);
    color: #e4e4e7;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit, QTextEdit, QPlainTextEdit {
    background-color: rgba(24,24,37,200);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 10px 14px;
    selection-background-color: rgba(99,102,241,0.5);
}
QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    padding-right: 44px;
    color: #e4e4e7;
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border: 1px solid rgba(99,102,241,0.15);
}
QLineEdit:hover, QDateEdit:hover, QTimeEdit:hover { border: 1px solid rgba(255,255,255,0.18); }

/* QSpinBox стрелки вверх/вниз — только треугольники, без подложек */
QAbstractSpinBox::up-button, QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    height: 50%;
    border: 0px;
    border-image: none;
    background: transparent;
    image: none;
    margin: 0;
}
QAbstractSpinBox::down-button, QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: padding;
    subcontrol-position: bottom right;
    width: 18px;
    height: 50%;
    border: 0px;
    border-image: none;
    background: transparent;
    image: none;
    margin: 0;
}
QAbstractSpinBox::up-arrow, QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid rgba(255,255,255,0.8);
    image: none;
    background: none;
}
QAbstractSpinBox::down-arrow, QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid rgba(255,255,255,0.8);
    image: none;
    background: none;
}

QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QDateEdit::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid rgba(255,255,255,0.8);
    background: none;
    image: none;
}
/* QTimeEdit/QDateEdit up/down кнопки — убрать подложки */
QTimeEdit::up-button, QDateEdit::up-button, QDateTimeEdit::up-button {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    height: 50%;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QTimeEdit::down-button, QDateEdit::down-button, QDateTimeEdit::down-button {
    subcontrol-origin: padding;
    subcontrol-position: bottom right;
    width: 18px;
    height: 50%;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QTimeEdit::up-arrow, QDateEdit::up-arrow, QDateTimeEdit::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid rgba(255,255,255,0.8);
    image: none;
    background: none;
}
QTimeEdit::down-arrow, QDateEdit::down-arrow, QDateTimeEdit::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid rgba(255,255,255,0.8);
    image: none;
    background: none;
}
/* Calendar popup */
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: rgba(24,24,37,240);
    color: #e4e4e7;
}
QCalendarWidget { outline: none; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; }
QCalendarWidget QAbstractItemView:focus { outline: none; border: none; }
QCalendarWidget QAbstractItemView::item:selected { background-color: rgba(99,102,241,0.40); }

/* Context menus */
QMenu {
    background-color: #1e1e2e;
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 4px 0;
}
QMenu::item {
    padding: 8px 24px;
    background-color: transparent;
}
QMenu::item:selected {
    background-color: rgba(99,102,241,0.40);
}
QMenu::separator {
    height: 1px;
    background-color: rgba(255,255,255,0.1);
    margin: 4px 0;
}

QCalendarWidget QToolButton {
    color: #ffffff;
    background-color: transparent;
    border: none;
    padding: 4px 8px;
}
QCalendarWidget QToolButton:hover {
    background-color: rgba(99,102,241,0.3);
    border-radius: 4px;
}
QCalendarWidget QToolButton::menu-indicator { image: none; }
/* Стрелки навигации — иконки ставятся программно */
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    min-width: 24px;
    min-height: 24px;
    padding: 0;
    background: transparent;
    border: none;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth::left-arrow,
QCalendarWidget QToolButton#qt_calendar_nextmonth::right-arrow {
    image: none;
    width: 0; height: 0;
}
QCalendarWidget QSpinBox {
    background-color: rgba(24,24,37,240);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    padding: 2px 8px;
    min-width: 60px;
}
QCalendarWidget QSpinBox::up-arrow, QCalendarWidget QSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
}
QCalendarWidget QSpinBox::up-arrow {
    border-bottom: 5px solid #ffffff;
}
QCalendarWidget QSpinBox::down-arrow {
    border-top: 5px solid #ffffff;
}
QCalendarWidget QAbstractItemView {
    background-color: rgba(24,24,37,240);
    color: #e4e4e7;
    selection-background-color: rgba(99,102,241,0.5);
    selection-color: #ffffff;
    alternate-background-color: rgba(39,39,56,200);
}

/* Combobox */
QComboBox {
    background-color: rgba(24,24,37,200);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 10px 14px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a1a1aa;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: rgba(24,24,37,240);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 4px;
    selection-background-color: rgba(99,102,241,0.40);
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 6px;
    min-height: 24px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: rgba(17,17,27,180);
    alternate-background-color: rgba(24,24,37,100);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    gridline-color: rgba(255,255,255,0.04);
    selection-background-color: rgba(99,102,241,0.25);
    selection-color: #ffffff;
}
QTableWidget::item, QTableView::item {
    padding: 10px 12px;
    border: none;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: rgba(99,102,241,0.18);
    color: #ffffff;
}
QTableWidget::item:focus, QTableView::item:focus {
    outline: none;
    border: none;
}
QTableWidget::item:focus:!active, QTableView::item:focus:!active {
    outline: none;
    border: none;
}
}
QHeaderView::section {
    background-color: rgba(17,17,27,220);
    color: #a1a1aa;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* Focus — убрать пунктирную рамку */
*:focus { outline: none; }
QTableWidget::item:focus, QTableView::item:focus { outline: none; border: none; }
QTableWidget::item:focus:!active { outline: none; border: none; }

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.30); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.30); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* Tabs */
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab {
    background: transparent;
    color: #71717a;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 500;
}
QTabBar::tab:hover { color: #e4e4e7; }
QTabBar::tab:selected { color: #ffffff; border-bottom: 2px solid #6366f1; }

/* Labels */
QLabel { background: transparent; }
QLabel#title { font-size: 24px; font-weight: 700; color: #f9fafb; }
QLabel#subtitle { font-size: 14px; color: #9ca3af; }
QLabel#statValue { font-size: 32px; font-weight: 700; }
QLabel#statLabel { font-size: 13px; color: #9ca3af; }
QLabel#hintText { font-size: 12px; color: #9ca3af; }
QLabel#versionText { font-size: 11px; color: #9ca3af; }

/* Tooltip */
QToolTip {
    background-color: rgba(24,24,37,240);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Progress */
QProgressBar {
    background-color: rgba(39,39,56,150);
    border: none;
    border-radius: 4px;
    text-align: center;
    font-size: 0;
    min-height: 6px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
    border-radius: 4px;
}

/* GroupBox */
QGroupBox {
    background-color: rgba(24,24,37,150);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px;
    padding-top: 28px;
    font-weight: 600;
}

/* Action buttons (edit / delete) */
QPushButton#actionBtn {
    background-color: transparent;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
}
QPushButton#actionBtn:hover {
    background-color: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.4);
}
QPushButton#actionDelete {
    background-color: transparent;
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #ffffff;
}
QPushButton#actionDelete:hover {
    background-color: rgba(239,68,68,0.2);
    border: 1px solid rgba(239,68,68,0.5);
    color: #ffffff;
}
QPushButton#actionRestore {
    background-color: transparent;
    border: 1px solid rgba(16,185,129,0.25);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #6ee7b7;
}
QPushButton#actionRestore:hover {
    background-color: rgba(16,185,129,0.2);
    border: 1px solid rgba(16,185,129,0.5);
}

/* Tree widget — dark theme */
QTreeWidget {
    background-color: rgba(17,17,27,180);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    selection-background-color: rgba(99,102,241,0.25);
    selection-color: #ffffff;
    alternate-background-color: rgba(24,24,37,100);
}
QTreeWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #e4e4e7;
}
QTreeWidget::item:hover {
    background-color: rgba(255,255,255,0.06);
}
QTreeWidget::item:selected {
    background-color: rgba(99,102,241,0.25);
    color: #ffffff;
}
QTreeWidget::branch {
    background-color: transparent;
}
QTreeWidget QHeaderView::section {
    background-color: rgba(17,17,27,220);
    color: #a1a1aa;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* List items */
QListWidget {
    background-color: rgba(17,17,27,180);
    alternate-background-color: rgba(24,24,37,100);
    color: #e4e4e7;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
}
QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: rgba(99,102,241,0.25);
}

/* Dialogs and message boxes */
QDialog, QMessageBox {
    background-color: rgba(24,24,37,240);
    color: #e4e4e7;
}
QDialog QLabel, QMessageBox QLabel {
    color: #e4e4e7;
    background: transparent;
}
QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

/* Form labels in dialogs */
QFormLayout QLabel {
    color: #e4e4e7;
    font-weight: 500;
}

/* Table item text color enforcement */
QTableWidget::item, QTableView::item {
    color: #e4e4e7;
}
"""


# ════════════════════════════════════════════════════════════════════
# СВЕТЛАЯ ТЕМА
# ════════════════════════════════════════════════════════════════════

LIGHT_QSS = """
/* Global */
QMainWindow { background-color: #ffffff; color: #18181b; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #18181b; }

/* Sidebar */
QFrame#sidebar {
    background-color: #f8f9fa;
    border: none;
    border-right: 1px solid #e5e7eb;
}

QFrame#sidebarSeparator {
    background-color: #e5e7eb;
}

/* Sidebar nav items */
QPushButton#navItem {
    background-color: transparent;
    color: #6b7280;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}
QPushButton#navItem:hover {
    background-color: #f3f4f6;
    color: #18181b;
}
QPushButton#navItem[active="true"],
QPushButton#navItem:checked {
    background-color: #ede9fe;
    color: #6d28d9;
    font-weight: 600;
}

/* Cards */
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 20px;
}
QFrame#card:hover {
    border: 1px solid #c4b5fd;
}

/* Stat card */
QFrame#statCard {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #f9fafb;
    border: 1px solid #9ca3af;
}
QPushButton:pressed { background-color: #f3f4f6; }
QPushButton:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
    border: 1px solid #e5e7eb;
}

QPushButton#primaryBtn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #818cf8; }
QPushButton#primaryBtn:pressed { background-color: #4f46e5; }

/* Plus/add icons — always white text on primary buttons */
QPushButton#primaryBtn {
    color: #ffffff !important;
}

/* Action buttons (edit / delete) — light theme */
QPushButton#actionBtn {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
}
QPushButton#actionBtn:hover {
    background-color: #ede9fe;
    border: 1px solid #c4b5fd;
}
QPushButton#actionDelete {
    background-color: #ffffff;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #ffffff;
}
QPushButton#actionDelete:hover {
    background-color: #fee2e2;
    border: 1px solid #fca5a5;
    color: #ffffff;
}
QPushButton#actionRestore {
    background-color: #ffffff;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #059669;
}
QPushButton#actionRestore:hover {
    background-color: #d1fae5;
    border: 1px solid #6ee7b7;
}

/* Tree widget — light theme */
QTreeWidget {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    selection-background-color: #ede9fe;
    selection-color: #18181b;
}
QTreeWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #18181b;
}
QTreeWidget::item:hover {
    background-color: #f3f4f6;
}
QTreeWidget::item:selected {
    background-color: #ede9fe;
    color: #18181b;
}
QTreeWidget::branch {
    background-color: transparent;
}
QTreeWidget QHeaderView::section {
    background-color: #f9fafb;
    color: #6b7280;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton#dangerBtn {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    border-radius: 10px;
}
QPushButton#dangerBtn:hover {
    background-color: #fee2e2;
    border-color: #f87171;
}

QPushButton#ghostBtn {
    background-color: transparent;
    color: #6b7280;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
}
QPushButton#ghostBtn:hover {
    background-color: #f3f4f6;
    color: #18181b;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 10px 14px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}
QDateEdit, QTimeEdit { padding-right: 44px; color: #18181b; }
QSpinBox, QDoubleSpinBox {
    padding-right: 44px;
    color: #18181b;
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border: 1px solid #6366f1;
}
QLineEdit:hover, QDateEdit:hover, QTimeEdit:hover { border: 1px solid #9ca3af; }

/* QSpinBox стрелки вверх/вниз — только треугольники, без подложек */
QAbstractSpinBox::up-button, QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    height: 50%;
    border: 0px;
    border-image: none;
    background: transparent;
    image: none;
    margin: 0;
}
QAbstractSpinBox::down-button, QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: padding;
    subcontrol-position: bottom right;
    width: 18px;
    height: 50%;
    border: 0px;
    border-image: none;
    background: transparent;
    image: none;
    margin: 0;
}
QAbstractSpinBox::up-arrow, QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #18181b;
    image: none;
    background: none;
}
QAbstractSpinBox::down-arrow, QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #18181b;
    image: none;
    background: none;
}

QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QDateEdit::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #18181b;
    background: none;
    image: none;
}
/* QTimeEdit/QDateEdit up/down кнопки — убрать подложки */
QTimeEdit::up-button, QDateEdit::up-button, QDateTimeEdit::up-button {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    height: 50%;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QTimeEdit::down-button, QDateEdit::down-button, QDateTimeEdit::down-button {
    subcontrol-origin: padding;
    subcontrol-position: bottom right;
    width: 18px;
    height: 50%;
    border: none;
    border-image: none;
    background: none;
    image: none;
    margin: 0;
}
QTimeEdit::up-arrow, QDateEdit::up-arrow, QDateTimeEdit::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #18181b;
    image: none;
    background: none;
}
QTimeEdit::down-arrow, QDateEdit::down-arrow, QDateTimeEdit::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #18181b;
    image: none;
    background: none;
}

/* Combobox */
QComboBox {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 10px 14px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6b7280;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 4px;
    selection-background-color: #ede9fe;
    selection-color: #18181b;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 6px;
    min-height: 24px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #f9fafb;
    color: #18181b;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    gridline-color: #f3f4f6;
    selection-background-color: #ede9fe;
    selection-color: #18181b;
}
QTableWidget::item, QTableView::item {
    padding: 10px 12px;
    border: none;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #ede9fe;
    color: #18181b;
    border: none;
}
QTableWidget::item:focus, QTableView::item:focus {
    outline: none;
    border: none;
}
QTableWidget::item:focus:!active, QTableView::item:focus:!active {
    outline: none;
    border: none;
}
QHeaderView::section {
    background-color: #f9fafb;
    color: #6b7280;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #d1d5db;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #9ca3af; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* Tabs */
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab {
    background: transparent;
    color: #6b7280;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 500;
}
QTabBar::tab:hover { color: #18181b; }
QTabBar::tab:selected { color: #18181b; border-bottom: 2px solid #6366f1; }

/* Labels */
QLabel { background: transparent; }
QLabel#title { font-size: 24px; font-weight: 700; color: #18181b; }
QLabel#subtitle { font-size: 14px; color: #6b7280; }
QLabel#statValue { font-size: 32px; font-weight: 700; }
QLabel#statLabel { font-size: 13px; color: #6b7280; }
QLabel#hintText { font-size: 12px; color: #6b7280; }
QLabel#versionText { font-size: 11px; color: #6b7280; }

/* Tooltip */
QToolTip {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Progress */
QProgressBar {
    background-color: #e5e7eb;
    border: none;
    border-radius: 4px;
    text-align: center;
    font-size: 0;
    min-height: 6px;
}
QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 4px;
}

/* GroupBox */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px;
    padding-top: 28px;
    font-weight: 600;
}

/* Dialogs and message boxes */
QDialog, QMessageBox {
    background-color: #ffffff;
    color: #18181b;
}
QDialog QLabel, QMessageBox QLabel {
    color: #18181b;
    background: transparent;
}
QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

/* Form labels in dialogs */
QFormLayout QLabel {
    color: #18181b;
    font-weight: 500;
}

/* Focus — убрать жирные рамки в таблицах */
*:focus { outline: none; }
QTableWidget::item:focus, QTableView::item:focus { outline: none; border: none; }
QTableWidget::item:focus:!active { outline: none; border: none; }

/* Context menus */
QMenu {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px 0;
}
QMenu::item {
    padding: 8px 24px;
    background-color: transparent;
    color: #18181b;
}
QMenu::item:selected {
    background-color: #ede9fe;
    color: #18181b;
}
QMenu::separator {
    height: 1px;
    background-color: #e5e7eb;
    margin: 4px 0;
}

/* Calendar popup — light theme */
QCalendarWidget { outline: none; border: 1px solid #e5e7eb; border-radius: 10px; }
QCalendarWidget QAbstractItemView:focus { outline: none; border: none; }
QCalendarWidget QAbstractItemView::item:selected { background-color: #ede9fe; }
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f9fafb;
    color: #18181b;
}
QCalendarWidget QToolButton {
    color: #18181b;
    background-color: transparent;
    border: none;
    padding: 4px 8px;
}
QCalendarWidget QToolButton:hover {
    background-color: #ede9fe;
    border-radius: 4px;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    min-width: 24px;
    min-height: 24px;
    padding: 0;
    background: transparent;
    border: none;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth {
    qproperty-icon: url(D:/PROJECTS/ZavgarApp/zavgar_app/ui/icons/calendar_prev_dark.png);
    qproperty-iconSize: 12px 16px;
}
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    qproperty-icon: url(D:/PROJECTS/ZavgarApp/zavgar_app/ui/icons/calendar_next_dark.png);
    qproperty-iconSize: 12px 16px;
}
QCalendarWidget QAbstractItemView {
    background-color: #ffffff;
    color: #18181b;
    selection-background-color: #ede9fe;
    selection-color: #18181b;
    alternate-background-color: #f9fafb;
}

/* List widget — light theme */
QListWidget {
    background-color: #ffffff;
    alternate-background-color: #f9fafb;
    color: #18181b;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
    color: #18181b;
}
QListWidget::item:selected {
    background-color: #ede9fe;
    color: #18181b;
}

/* Focus — remove dotted outline (light theme) */
*:focus { outline: none; }
QTableWidget::item:focus, QTableView::item:focus { outline: none; border: none; }
QTableWidget::item, QTableView::item {
    color: #18181b;
    border: none;
}

/* Table item text color enforcement — light */
QComboBox QAbstractItemView::item {
    color: #18181b;
}
"""


# ════════════════════════════════════════════════════════════════════
# THEME MANAGER
# ════════════════════════════════════════════════════════════════════

class ThemeManager:
    """Переключатель тем."""

    def __init__(self):
        self.current = 'dark'

    def apply_theme(self, app, theme: str = 'dark') -> None:
        """Применить тему ко всему приложению."""
        self.current = theme
        if theme == 'light':
            app.setStyleSheet(LIGHT_QSS)
        else:
            app.setStyleSheet(DARK_QSS)

    def toggle(self, app) -> str:
        """Переключить тему. Возвращает новое имя."""
        new = 'light' if self.current == 'dark' else 'dark'
        self.apply_theme(app, new)
        return new


theme_manager = ThemeManager()


# ════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════

def add_shadow(widget: QWidget, blur: int = 20, opacity: int = 40, y_offset: int = 4) -> None:
    """Добавить мягкую тень к виджету."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, y_offset)
    widget.setGraphicsEffect(shadow)


def make_card(title: str = '', parent: Optional[QWidget] = None) -> QFrame:
    """Создать карточку с тенью."""
    from PySide6.QtWidgets import QVBoxLayout, QLabel
    card = QFrame(parent)
    card.setObjectName('card')
    add_shadow(card, blur=24, opacity=35)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    if title:
        lbl = QLabel(title)
        lbl.setObjectName('title')
        layout.addWidget(lbl)

    return card


def make_button(text: str, variant: str = 'primary', parent=None) -> QPushButton:
    """
    Создать кнопку.
    variant: 'primary', 'danger', 'ghost', 'default'
    """
    btn = QPushButton(text, parent)
    if variant != 'default':
        btn.setObjectName(f'{variant}Btn')
    add_shadow(btn, blur=12, opacity=25, y_offset=3)
    return btn


class AnimatedButton(QPushButton):
    """Кнопка с анимацией тени при hover."""

    def __init__(self, text: str, variant: str = 'primary', parent=None):
        super().__init__(text, parent)
        self.setObjectName(f'{variant}Btn')

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(15)
        self._shadow.setColor(QColor(99, 102, 241, 80))
        self._shadow.setOffset(0, 4)
        self.setGraphicsEffect(self._shadow)

        self._anim = QPropertyAnimation(self._shadow, b"blurRadius")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event):
        self._anim.setStartValue(15)
        self._anim.setEndValue(28)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.setStartValue(28)
        self._anim.setEndValue(15)
        self._anim.start()
        super().leaveEvent(event)
