"""
models/driver.py — Модель "Водитель"
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

DriverStatus = Literal['active', 'vacation', 'sick_leave', 'business_trip', 'suspended', 'fired']


@dataclass
class Driver:
    id: int | None = None
    fio: str = ""
    phone: str = ""
    license_number: str = ""
    license_category: str = ""  # B, C, D, E
    license_expiry: str = ""
    hire_date: str = ""
    status: str = "active"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'fio': self.fio,
            'phone': self.phone,
            'license_number': self.license_number,
            'license_category': self.license_category,
            'license_expiry': self.license_expiry,
            'hire_date': self.hire_date,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> Driver:
        return cls(
            id=row[0],
            fio=row[1] or "",
            phone=row[2] or "",
            license_number=row[3] or "",
            license_category=row[4] or "",
            license_expiry=row[5] or "",
            hire_date=row[6] or "",
            status=row[7] or "active",
            notes=row[8] or "",
            created_at=row[9] or "",
        )

    @classmethod
    def from_db_row(cls, row: tuple) -> Driver:
        """Алиас для from_row."""
        return cls.from_row(row)
