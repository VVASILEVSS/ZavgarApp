"""
ui/pages/__init__.py
"""

from .vehicles import VehiclesPage
from .parts import PartsPage
from .maintenance import MaintenancePage
from .drivers import DriversPage
from .reports import ReportsPage
from .timesheets import TimesheetsPage
from .trip_logs import TripLogsPage
from .calendar_page import CalendarPage

__all__ = [
    'VehiclesPage', 
    'PartsPage',
    'MaintenancePage',
    'DriversPage',
    'ReportsPage',
    'TimesheetsPage',
    'TripLogsPage',
    'CalendarPage'
]
