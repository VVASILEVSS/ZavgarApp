"""
models/trip_log.py — Путевой лист
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

TripStatus = Literal['planned', 'in_progress', 'completed', 'cancelled']


@dataclass
class TripLog:
    """Запись о поездке."""
    id: int | None = None
    driver_id: int = 0
    vehicle_id: int = 0
    trip_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    start_time: str | None = None  # HH:MM
    end_time: str | None = None
    start_mileage: int = 0
    end_mileage: int | None = None
    distance_km: int | None = None
    route_from: str = ""
    route_to: str = ""
    purpose: str = ""  # цель поездки
    passengers: str | None = None  # JSON список пассажиров
    cargo: str | None = None  # груз
    status: TripStatus = 'planned'
    notes: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(sep=' ', timespec='seconds'))

    @classmethod
    def from_row(cls, row: tuple) -> TripLog:
        return cls(
            id=row[0],
            driver_id=row[1],
            vehicle_id=row[2],
            trip_date=row[3],
            start_time=row[4],
            end_time=row[5],
            start_mileage=row[6] or 0,
            end_mileage=row[7],
            distance_km=row[8],
            route_from=row[9] or "",
            route_to=row[10] or "",
            purpose=row[11] or "",
            passengers=row[12],
            cargo=row[13],
            status=row[14] or 'planned',
            notes=row[15],
            created_at=row[16],
        )
