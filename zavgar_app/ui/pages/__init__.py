"""
ui/pages/__init__.py
"""

from .vehicles import VehiclesPage
from .parts import PartsPage
from .maintenance import MaintenancePage
from .drivers import DriversPage
from .reports import ReportsPage

__all__ = [
    'VehiclesPage', 
    'PartsPage',
    'MaintenancePage',
    'DriversPage',
    'ReportsPage'
]
