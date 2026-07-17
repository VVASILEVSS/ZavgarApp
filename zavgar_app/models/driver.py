"""
models/driver.py — Водители
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

DriverStatus = Literal['active', 'vacation', 'sick', 'fired']


def _today_iso() -> str:
    return date.today().isoformat()


@dataclass
class Driver:
    """Водитель автопарка."""
    id: int | None = None
    fio: str = ''
    phone: str = ''
    license_number: str | None = None
    license_category: str | None = None
    license_expiry: str | None = None
    hire_date: str | None = None
    status: DriverStatus = 'active'
    notes: str | None = None
    created_at: str = field(default_factory=_today_iso)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Driver:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> Driver:
        return cls(
            id=row[0], fio=row[1], phone=row[2], license_number=row[3],
            license_category=row[4], license_expiry=row[5], hire_date=row[6],
            status=row[7], notes=row[8], created_at=row[9],
        )
