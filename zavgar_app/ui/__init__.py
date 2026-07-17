"""
ui/__init__.py — UI модули ZavgarApp
"""

from .theme import theme_manager, add_shadow, make_card, make_button, AnimatedButton
from .main_window import MainWindow

__all__ = [
    'theme_manager', 'add_shadow', 'make_card', 'make_button', 'AnimatedButton',
    'MainWindow',
]
