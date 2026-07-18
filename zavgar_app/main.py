"""
main.py — Точка входа ZavgarApp
"""

from __future__ import annotations

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from zavgar_app import __version__, __app_name__
from zavgar_app.ui import MainWindow
from zavgar_app.ui.theme import theme_manager
from zavgar_app import db


def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'zavgar.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f'Starting {__app_name__} v{__version__}')

    # БД
    db_path = Path('zavgar_data.db')
    conn = db.open_db(db_path)
    logger.info(f'Database opened: {db_path}')
    
    # Автоочистка корзины (старше 6 месяцев)
    deleted_count = db.cleanup_old_trash(conn, months=6)
    if deleted_count > 0:
        logger.info(f"Auto-cleaned {deleted_count} old trash records")

    # Qt
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)

    # Тема (dark по умолчанию)
    theme_manager.apply_theme(app, 'dark')

    # Окно
    window = MainWindow(conn=conn)
    window.show()

    logger.info('Application started successfully')
    exit_code = app.exec()
    conn.close()
    logger.info('Application closed')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
