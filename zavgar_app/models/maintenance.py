"""
models/maintenance.py — Техническое обслуживание
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

MaintenanceType = Literal['oil', 'filter', 'brake', 'tire', 'diagnostic', 'repair', 'other']


def _today_iso() -> str:
    return date.today().isoformat()


@dataclass
class MaintenanceSchedule:
    """График ТО (планирование по пробегу)."""
    id: int | None = None
    vehicle_id: int = 0
    maintenance_type: MaintenanceType = 'oil'
    interval_km: int = 10000  # интервал в км
    last_done_km: int = 0
    last_done_date: str | None = None
    next_due_km: int | None = None
    next_due_date: str | None = None
    notes: str | None = None
    created_at: str = field(default_factory=_today_iso)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> MaintenanceSchedule:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> MaintenanceSchedule:
        return cls(
            id=row[0], vehicle_id=row[1], maintenance_type=row[2],
            interval_km=row[3], last_done_km=row[4], last_done_date=row[5],
            next_due_km=row[6], next_due_date=row[7], notes=row[8], created_at=row[9],
        )

    def is_overdue(self, current_mileage: int) -> bool:
        """Проверка: просрочено по пробегу."""
        if self.next_due_km is None:
            return False
        return current_mileage >= self.next_due_km


@dataclass
class MaintenanceRecord:
    """Запись о проведённом ТО."""
    id: int | None = None
    vehicle_id: int = 0
    maintenance_type: MaintenanceType = 'oil'
    mileage: int = 0
    service_date: str = field(default_factory=_today_iso)
    cost: float | None = None
    parts_used: str | None = None  # JSON: список запчастей
    service_provider: str | None = None  # кто выполнял
    notes: str | None = None
    created_at: str = field(default_factory=_today_iso)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> MaintenanceRecord:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> MaintenanceRecord:
        return cls(
            id=row[0], vehicle_id=row[1], maintenance_type=row[2],
            mileage=row[3], service_date=row[4], cost=row[5],
            parts_used=row[6], service_provider=row[7], notes=row[8], created_at=row[9],
        )
