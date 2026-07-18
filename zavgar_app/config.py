"""
config.py — Конфигурация ZavgarApp
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "db_path": "zavgar_data.db",
    "use_wal": True,  # False для сетевых дисков
    "timeout": 30.0,  # Таймаут блокировки БД (секунды)
}


def load_config(config_path: str | Path = "config.json") -> dict[str, Any]:
    """Загрузить конфигурацию из файла."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.info(f"Config file not found, creating default: {config_path}")
        save_config(config_path, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Объединить с дефолтами (на случай новых полей)
        merged = DEFAULT_CONFIG.copy()
        merged.update(config)
        
        logger.info(f"Config loaded: {config_path}")
        return merged
    
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config_path: str | Path, config: dict[str, Any]) -> None:
    """Сохранить конфигурацию в файл."""
    config_path = Path(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Config saved: {config_path}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise
