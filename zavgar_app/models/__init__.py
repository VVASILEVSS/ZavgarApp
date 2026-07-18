"""
models/__init__.py — дата-классы для ZavgarApp
"""

from .vehicle import Vehicle, VehicleType
from .driver import Driver
from .part import Part, PartTransaction
from .maintenance import MaintenanceSchedule, MaintenanceRecord
from .timesheet import Timesheet
from .trip_log import TripLog

__all__ = [
    'Vehicle', 'VehicleType',
    'Driver',
    'Part', 'PartTransaction',
    'MaintenanceSchedule', 'MaintenanceRecord',
    'Timesheet',
    'TripLog',
]
