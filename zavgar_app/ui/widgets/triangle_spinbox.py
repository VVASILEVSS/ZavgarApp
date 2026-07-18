"""
Кастомные виджеты с треугольными стрелками вместо стандартных кнопок
"""
from PySide6.QtWidgets import QTimeEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QToolButton, QHBoxLayout, QWidget, QDialog, QVBoxLayout, QPushButton, QLabel, QCalendarWidget, QDialog, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPolygon
from PySide6.QtCore import QPoint


class TriangleButton(QToolButton):
    """Кнопка с треугольной стрелкой"""
    def __init__(self, direction='up', parent=None):
        super().__init__(parent)
        self.direction = direction
        self.setFixedSize(18, 14)
        self.setAutoRepeat(True)
        self.setAutoRepeatInterval(100)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Треугольник
        w, h = self.width(), self.height()
        if self.direction == 'up':
            triangle = QPolygon([
                QPoint(w//2, 4),
                QPoint(w-4, h-4),
                QPoint(4, h-4)
            ])
        else:  # down
            triangle = QPolygon([
                QPoint(4, 4),
                QPoint(w-4, 4),
                QPoint(w//2, h-4)
            ])
        
        painter.setPen(Qt.NoPen)
        color = self.palette().text().color()
        painter.setBrush(color)
        painter.drawPolygon(triangle)


class TriangleTimeEdit(QTimeEdit):
    """QTimeEdit с треугольными кнопками вместо стандартных"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QTimeEdit.NoButtons)
        
        # Создаём контейнер для кнопок
        self._button_container = QWidget(self)
        btn_layout = QHBoxLayout(self._button_container)
        btn_layout.setContentsMargins(0, 0, 2, 0)
        btn_layout.setSpacing(0)
        
        self._up_btn = TriangleButton('up')
        self._down_btn = TriangleButton('down')
        
        btn_layout.addWidget(self._up_btn)
        btn_layout.addWidget(self._down_btn)
        
        # Подключаем к stepBy
        self._up_btn.clicked.connect(lambda: self.stepBy(1))
        self._down_btn.clicked.connect(lambda: self.stepBy(-1))
        
        # Позиционируем справа
        self._button_container.setParent(self)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Размещаем кнопки справа
        btn_width = self._button_container.sizeHint().width()
        self._button_container.move(self.width() - btn_width - 4, 
                                    (self.height() - self._button_container.sizeHint().height()) // 2)


class TriangleSpinBox(QSpinBox):
    """QSpinBox с треугольными кнопками"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QSpinBox.NoButtons)
        
        self._button_container = QWidget(self)
        btn_layout = QHBoxLayout(self._button_container)
        btn_layout.setContentsMargins(0, 0, 2, 0)
        btn_layout.setSpacing(0)
        
        self._up_btn = TriangleButton('up')
        self._down_btn = TriangleButton('down')
        
        btn_layout.addWidget(self._up_btn)
        btn_layout.addWidget(self._down_btn)
        
        self._up_btn.clicked.connect(lambda: self.stepBy(1))
        self._down_btn.clicked.connect(lambda: self.stepBy(-1))
        
        self._button_container.setParent(self)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_width = self._button_container.sizeHint().width()
        self._button_container.move(self.width() - btn_width - 4,
                                    (self.height() - self._button_container.sizeHint().height()) // 2)


class CalendarIconButton(QToolButton):
    """Кнопка с иконкой календаря (📅)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("📅")
        self.setFixedSize(28, 28)
        self.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
                font-size: 16px;
                padding: 0;
            }
            QToolButton:hover {
                background: rgba(99,102,241,0.15);
                border-radius: 6px;
            }
        """)


class TriangleDateEdit(QDateEdit):
    """QDateEdit с кастомной кнопкой календаря — открывает диалог с QCalendarWidget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDateEdit.NoButtons)
        self.setFixedWidth(160)
        
        self._cal_btn = CalendarIconButton(self)
        self._cal_btn.clicked.connect(self._open_calendar_dialog)
        self._cal_btn.setParent(self)
        
    def _open_calendar_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Выберите дату")
        dlg.setMinimumSize(450, 400)
        lay = QVBoxLayout(dlg)
        cal = QCalendarWidget()
        cal.setSelectedDate(self.date())
        cal.setGridVisible(True)
        cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal.setNavigationBarVisible(True)
        cal.setFirstDayOfWeek(Qt.Monday)
        cal.setMinimumHeight(320)
        lay.addWidget(cal)
        
        # Двойной клик = выбрать и закрыть
        cal.activated.connect(lambda: self._accept_date(dlg, cal))
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(lambda: self._accept_date(dlg, cal))
        cancel_btn.clicked.connect(dlg.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        lay.addLayout(btn_layout)
        
        dlg.exec()
        
    def _accept_date(self, dlg, cal):
        self.setDate(cal.selectedDate())
        dlg.accept()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        btn_w = self._cal_btn.sizeHint().width()
        self._cal_btn.move(self.width() - btn_w - 4,
                          (self.height() - self._cal_btn.sizeHint().height()) // 2)
