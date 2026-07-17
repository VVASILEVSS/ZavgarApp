"""
ui/main_window.py — Главное окно ZavgarApp
============================================

Боковая панель + контент (QStackedWidget).
Переключение dark/light через кнопку в sidebar.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QApplication,
)
from PySide6.QtCore import Qt

from .theme import theme_manager, add_shadow


class SidebarButton(QPushButton):
    """Кнопка боковой навигации (использует objectName navItem)."""

    def __init__(self, text: str, icon_text: str = '', parent=None):
        super().__init__(parent)
        self.setObjectName('navItem')
        self.setText(f'  {icon_text}  {text}')
        self.setCheckable(True)


class Sidebar(QFrame):
    """Боковая панель."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Логотип
        logo = QLabel('🚗 ZavgarApp')
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet('font-size: 20px; font-weight: 700; padding: 16px 0;')
        layout.addWidget(logo)

        # Разделитель
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background-color: #e5e7eb;')
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Навигация
        self.buttons = []
        nav_items = [
            ('Панель управления', '📊'),
            ('Автопарк', '🚙'),
            ('Водители', '👤'),
            ('Склад запчастей', '🔧'),
            ('ТО и обслуживание', '🛠️'),
            ('Отчёты', '📈'),
        ]
        for text, icon in nav_items:
            btn = SidebarButton(text, icon)
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Кнопка переключения темы
        self.theme_btn = QPushButton('🌙 Тёмная тема')
        self.theme_btn.setObjectName('ghostBtn')
        self.theme_btn.setStyleSheet('text-align: center; padding: 10px;')
        layout.addWidget(self.theme_btn)

        # Версия
        ver = QLabel('v0.1.0')
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet('color: #9ca3af; font-size: 11px; padding: 8px;')
        layout.addWidget(ver)

    def set_active(self, index: int):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
            btn.setProperty('active', 'true' if i == index else 'false')
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class DashboardPage(QWidget):
    """Панель управления — карточки со статистикой."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel('Панель управления')
        title.setObjectName('title')
        layout.addWidget(title)

        sub = QLabel('Обзор автопарка')
        sub.setObjectName('subtitle')
        layout.addWidget(sub)

        # Карточки
        cards = QHBoxLayout()
        cards.setSpacing(16)
        for label, val, color in [
            ('Авто в парке', '0', '#6366f1'),
            ('На ТО', '0', '#f59e0b'),
            ('Запчасти', '0', '#8b5cf6'),
            ('Водители', '0', '#10b981'),
        ]:
            cards.addWidget(self._stat_card(label, val, color))
        layout.addLayout(cards)
        layout.addStretch()

    @staticmethod
    def _stat_card(label: str, value: str, accent: str) -> QFrame:
        from PySide6.QtWidgets import QVBoxLayout as VL
        card = QFrame()
        card.setObjectName('statCard')
        add_shadow(card, blur=22, opacity=30, y_offset=4)

        vl = VL(card)
        vl.setContentsMargins(22, 22, 22, 22)

        v = QLabel(value)
        v.setObjectName('statValue')
        v.setStyleSheet(f'color: {accent};')
        vl.addWidget(v)

        l = QLabel(label)
        l.setObjectName('statLabel')
        vl.addWidget(l)

        return card


class PlaceholderPage(QWidget):
    """Заглушка."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        t = QLabel(title)
        t.setObjectName('title')
        layout.addWidget(t)

        h = QLabel('Раздел в разработке...')
        h.setObjectName('subtitle')
        layout.addWidget(h)
        layout.addStretch()


class MainWindow(QMainWindow):
    """Главное окно."""

    def __init__(self, conn=None):
        super().__init__()
        self.conn = conn
        self.setWindowTitle('ZavgarApp — Управление автопарком')
        self.setMinimumSize(1100, 750)
        self.resize(1360, 880)
        self.setObjectName('mainWindow')

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # Content
        from zavgar_app.ui.pages import VehiclesPage
        from zavgar_app.ui.pages.parts import PartsPage
        from zavgar_app.ui.pages.drivers import DriversPage
        from zavgar_app.ui.pages.maintenance import MaintenancePage
        from zavgar_app.ui.pages.reports import ReportsPage

        self.content = QStackedWidget()
        self.pages = [
            DashboardPage(),
            VehiclesPage(conn) if conn else PlaceholderPage('🚙 Автопарк'),
            DriversPage(conn) if conn else PlaceholderPage('👤 Водители'),
            PartsPage(conn) if conn else PlaceholderPage('🔧 Склад запчастей'),
            MaintenancePage(conn) if conn else PlaceholderPage('🛠️ ТО и обслуживание'),
            ReportsPage(conn) if conn else PlaceholderPage('📈 Отчёты'),
        ]
        for p in self.pages:
            self.content.addWidget(p)
        main_layout.addWidget(self.content)

        # Навигация
        for i, btn in enumerate(self.sidebar.buttons):
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))

        # Переключение темы
        self.sidebar.theme_btn.clicked.connect(self._toggle_theme)

        self.sidebar.set_active(0)

    def _navigate(self, index: int):
        self.content.setCurrentIndex(index)
        self.sidebar.set_active(index)

    def _toggle_theme(self):
        app = QApplication.instance()
        new_theme = theme_manager.toggle(app)
        text = '☀️ Светлая тема' if new_theme == 'dark' else '🌙 Тёмная тема'
        self.sidebar.theme_btn.setText(text)
