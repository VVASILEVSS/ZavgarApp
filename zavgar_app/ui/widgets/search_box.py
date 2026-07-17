"""
ui/widgets/search_box.py — Поле поиска с фильтрацией
"""

from __future__ import annotations

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal, QTimer


class SearchBox(QLineEdit):
    """Поле поиска с debounce (задержка перед отправкой сигнала)."""
    
    search_changed = Signal(str)
    
    def __init__(self, placeholder: str = "Поиск...", debounce_ms: int = 300, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        
        # Debounce timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(lambda: self.search_changed.emit(self.text()))
        
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self, text: str):
        """Перезапустить таймер при изменении текста."""
        self._timer.start()
