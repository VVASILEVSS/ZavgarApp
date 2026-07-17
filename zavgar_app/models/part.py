"""
models/part.py — Запчасти (склад)
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

TransactionType = Literal['in', 'out']


def _today_iso() -> str:
    return date.today().isoformat()


@dataclass
class Part:
    """Запчасть на складе."""
    id: int | None = None
    name: str = ''
    article: str | None = None  # артикул
    category: str | None = None
    unit: str = 'шт'  # единица измерения
    quantity: float = 0.0
    min_quantity: float = 0.0  # минимальный остаток
    avg_price: float = 0.0
    notes: str | None = None
    created_at: str = field(default_factory=_today_iso)
    updated_at: str = field(default_factory=_today_iso)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Part:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> Part:
        return cls(
            id=row[0], name=row[1], article=row[2], category=row[3],
            unit=row[4], quantity=row[5], min_quantity=row[6],
            avg_price=row[7], notes=row[8], created_at=row[9], updated_at=row[10],
        )

    def is_low_stock(self) -> bool:
        """Проверка: остаток ниже минимального."""
        return self.quantity < self.min_quantity


@dataclass
class PartTransaction:
    """Транзакция по запчастям (приход/расход)."""
    id: int | None = None
    part_id: int = 0
    transaction_type: TransactionType = 'in'
    quantity: float = 0.0
    price: float | None = None
    vehicle_id: int | None = None  # если расход на авто
    notes: str | None = None
    transaction_date: str = field(default_factory=_today_iso)
    created_by: str | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> PartTransaction:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> PartTransaction:
        return cls(
            id=row[0], part_id=row[1], transaction_type=row[2],
            quantity=row[3], price=row[4], vehicle_id=row[5],
            notes=row[6], transaction_date=row[7], created_by=row[8],
        )
