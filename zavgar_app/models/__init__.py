"""
models/__init__.py — дата-классы для ZavgarApp
"""

from .vehicle import Vehicle, VehicleType
from .driver import Driver
from .part import Part, PartTransaction
from .maintenance import MaintenanceSchedule, MaintenanceRecord

__all__ = [
    'Vehicle', 'VehicleType',
    'Driver',
    'Part', 'PartTransaction',
    'MaintenanceSchedule', 'MaintenanceRecord',
]
