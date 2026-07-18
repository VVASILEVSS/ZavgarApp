"""
models/timesheet.py — Табель учёта рабочего времени
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

WorkStatus = Literal['work', 'day_off', 'sick', 'vacation', 'business_trip']


@dataclass
class Timesheet:
    """Запись в табеле (день водителя)."""
    id: int | None = None
    driver_id: int = 0
    work_date: str = field(default_factory=lambda: date.today().isoformat())
    status: WorkStatus = 'work'
    start_time: str | None = None  # HH:MM
    end_time: str | None = None
    hours: float = 8.0
    notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(sep=' ', timespec='seconds'))

    @classmethod
    def from_row(cls, row: tuple) -> Timesheet:
        return cls(
            id=row[0],
            driver_id=row[1],
            work_date=row[2],
            status=row[3],
            start_time=row[4],
            end_time=row[5],
            hours=row[6] or 0.0,
            notes=row[7],
            created_at=row[8],
        )
