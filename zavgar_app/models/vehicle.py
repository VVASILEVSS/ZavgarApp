"""
models/vehicle.py — Автомобили автопарка
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

VehicleType = Literal['car', 'truck', 'van', 'bus', 'special']
VehicleStatus = Literal['active', 'maintenance', 'decommissioned', 'sold']


def _today_iso() -> str:
    """Текущая дата в ISO формате."""
    return date.today().isoformat()


@dataclass
class Vehicle:
    """Автомобиль автопарка."""
    id: int | None = None
    marka: str = ''
    model: str = ''
    year: int | None = None
    vin: str | None = None
    gosnomer: str = ''
    vehicle_type: VehicleType = 'car'
    status: VehicleStatus = 'active'
    purchase_date: str | None = None
    purchase_price: float | None = None
    current_mileage: int = 0
    last_maintenance_date: str | None = None
    last_maintenance_mileage: int | None = None
    assigned_driver_id: int | None = None
    notes: str | None = None
    created_at: str = field(default_factory=_today_iso)
    updated_at: str = field(default_factory=_today_iso)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Vehicle:
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})

    @classmethod
    def from_db_row(cls, row: tuple) -> Vehicle:
        """row — кортеж из SELECT в порядке колонок таблицы vehicles."""
        return cls(
            id=row[0], marka=row[1], model=row[2], year=row[3], vin=row[4],
            gosnomer=row[5], vehicle_type=row[6], status=row[7],
            purchase_date=row[8], purchase_price=row[9], current_mileage=row[10],
            last_maintenance_date=row[11], last_maintenance_mileage=row[12],
            assigned_driver_id=row[13], notes=row[14],
            created_at=row[15], updated_at=row[16],
        )

    def full_name(self) -> str:
        """Полное название: марка модель год."""
        parts = [self.marka, self.model]
        if self.year:
            parts.append(str(self.year))
        return ' '.join(parts)
