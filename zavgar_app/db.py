"""
db.py — База данных ZavgarApp (SQLite)
========================================

Схема БД для управления автопарком:
- vehicles (автомобили)
- drivers (водители)
- parts (запчасти на складе)
- part_transactions (приход/расход)
- maintenance_schedules (график ТО)
- maintenance_records (записи ТО)
"""

from __future__ import annotations

import sqlite3
import logging
from pathlib import Path
from typing import Optional

from .models import Vehicle, Driver, Part, PartTransaction, MaintenanceSchedule, MaintenanceRecord, Timesheet, TripLog

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2


def open_db(db_path: str | Path) -> sqlite3.Connection:
    """Открыть БД и применить миграции."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _run_migrations(conn)
    return conn


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Применить миграции."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        )
    """)
    
    cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
    row = cursor.fetchone()
    
    if row is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (0,))
        conn.commit()
        current = 0
    else:
        current = row[0]
    
    if current < SCHEMA_VERSION:
        if current < 1:
            _migrate_v0_to_v1(conn)
        if current < 2:
            _migrate_v1_to_v2(conn)
        conn.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))
        conn.commit()


def _migrate_v0_to_v1(conn: sqlite3.Connection) -> None:
    """Начальная схема."""
    
    # Автомобили
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marka TEXT NOT NULL DEFAULT '',
            model TEXT NOT NULL DEFAULT '',
            year INTEGER,
            vin TEXT,
            gosnomer TEXT NOT NULL DEFAULT '',
            vehicle_type TEXT NOT NULL DEFAULT 'car',
            status TEXT NOT NULL DEFAULT 'active',
            purchase_date TEXT,
            purchase_price REAL,
            current_mileage INTEGER NOT NULL DEFAULT 0,
            last_maintenance_date TEXT,
            last_maintenance_mileage INTEGER,
            assigned_driver_id INTEGER REFERENCES drivers(id),
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Водители
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            license_number TEXT,
            license_category TEXT,
            license_expiry TEXT,
            hire_date TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Запчасти
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            article TEXT,
            category TEXT,
            unit TEXT NOT NULL DEFAULT 'шт',
            quantity REAL NOT NULL DEFAULT 0,
            min_quantity REAL NOT NULL DEFAULT 0,
            avg_price REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Транзакции запчастей
    conn.execute("""
        CREATE TABLE IF NOT EXISTS part_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL REFERENCES parts(id),
            transaction_type TEXT NOT NULL DEFAULT 'in',
            quantity REAL NOT NULL DEFAULT 0,
            price REAL,
            vehicle_id INTEGER REFERENCES vehicles(id),
            notes TEXT,
            transaction_date TEXT NOT NULL,
            created_by TEXT
        )
    """)
    
    # График ТО
    conn.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            maintenance_type TEXT NOT NULL DEFAULT 'oil',
            interval_km INTEGER NOT NULL DEFAULT 10000,
            last_done_km INTEGER NOT NULL DEFAULT 0,
            last_done_date TEXT,
            next_due_km INTEGER,
            next_due_date TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Записи ТО
    conn.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            maintenance_type TEXT NOT NULL DEFAULT 'oil',
            mileage INTEGER NOT NULL DEFAULT 0,
            service_date TEXT NOT NULL,
            cost REAL,
            parts_used TEXT,
            service_provider TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Индексы
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_gosnomer ON vehicles(gosnomer)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_parts_name ON parts(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_maint_schedules_vehicle ON maintenance_schedules(vehicle_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_maint_records_vehicle ON maintenance_records(vehicle_id)")
    
    logger.info("Migration v0→v1 completed")


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Добавить табель учёта и путевые листы."""
    
    # Табель учёта рабочего времени
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL REFERENCES drivers(id),
            work_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'work',
            start_time TEXT,
            end_time TEXT,
            hours REAL NOT NULL DEFAULT 8.0,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Путевые листы
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trip_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL REFERENCES drivers(id),
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
            trip_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            start_mileage INTEGER NOT NULL DEFAULT 0,
            end_mileage INTEGER,
            distance_km INTEGER,
            route_from TEXT NOT NULL DEFAULT '',
            route_to TEXT NOT NULL DEFAULT '',
            purpose TEXT NOT NULL DEFAULT '',
            passengers TEXT,
            cargo TEXT,
            status TEXT NOT NULL DEFAULT 'planned',
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Индексы
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_driver ON timesheets(driver_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(work_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trip_logs_driver ON trip_logs(driver_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trip_logs_vehicle ON trip_logs(vehicle_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_trip_logs_date ON trip_logs(trip_date)")
    
    logger.info("Migration v1→v2 completed")


# ════════════════════════════════════════════════════════════════════
# CRUD: Автомобили
# ════════════════════════════════════════════════════════════════════

def create_vehicle(conn: sqlite3.Connection, vehicle: Vehicle) -> int:
    """Создать автомобиль. Возвращает id."""
    cursor = conn.execute("""
        INSERT INTO vehicles (marka, model, year, vin, gosnomer, vehicle_type, status,
            purchase_date, purchase_price, current_mileage, last_maintenance_date,
            last_maintenance_mileage, assigned_driver_id, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle.marka, vehicle.model, vehicle.year, vehicle.vin, vehicle.gosnomer,
        vehicle.vehicle_type, vehicle.status, vehicle.purchase_date, vehicle.purchase_price,
        vehicle.current_mileage, vehicle.last_maintenance_date, vehicle.last_maintenance_mileage,
        vehicle.assigned_driver_id, vehicle.notes, vehicle.created_at, vehicle.updated_at,
    ))
    conn.commit()
    return cursor.lastrowid


def get_vehicle(conn: sqlite3.Connection, vehicle_id: int) -> Optional[Vehicle]:
    """Получить автомобиль по id."""
    cursor = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    return Vehicle.from_db_row(tuple(row)) if row else None


def list_vehicles(conn: sqlite3.Connection, status: Optional[str] = None) -> list[Vehicle]:
    """Список автомобилей (опционально по статусу)."""
    if status:
        cursor = conn.execute("SELECT * FROM vehicles WHERE status = ? ORDER BY marka, model", (status,))
    else:
        cursor = conn.execute("SELECT * FROM vehicles ORDER BY marka, model")
    return [Vehicle.from_db_row(tuple(row)) for row in cursor.fetchall()]


def count_vehicles(conn: sqlite3.Connection) -> int:
    """Количество автомобилей."""
    cursor = conn.execute("SELECT COUNT(*) FROM vehicles")
    return cursor.fetchone()[0]


def update_vehicle(conn: sqlite3.Connection, vehicle: Vehicle) -> None:
    """Обновить автомобиль."""
    conn.execute("""
        UPDATE vehicles SET marka=?, model=?, year=?, vin=?, gosnomer=?, vehicle_type=?,
            status=?, purchase_date=?, purchase_price=?, current_mileage=?,
            last_maintenance_date=?, last_maintenance_mileage=?, assigned_driver_id=?,
            notes=?, updated_at=?
        WHERE id=?
    """, (
        vehicle.marka, vehicle.model, vehicle.year, vehicle.vin, vehicle.gosnomer,
        vehicle.vehicle_type, vehicle.status, vehicle.purchase_date, vehicle.purchase_price,
        vehicle.current_mileage, vehicle.last_maintenance_date, vehicle.last_maintenance_mileage,
        vehicle.assigned_driver_id, vehicle.notes, vehicle.updated_at, vehicle.id,
    ))
    conn.commit()


def delete_vehicle(conn: sqlite3.Connection, vehicle_id: int) -> None:
    """Удалить автомобиль."""
    conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    conn.commit()


# ════════════════════════════════════════════════════════════════════
# CRUD: Водители
# ════════════════════════════════════════════════════════════════════

def create_driver(conn: sqlite3.Connection, driver: Driver) -> int:
    """Создать водителя. Возвращает id."""
    cursor = conn.execute("""
        INSERT INTO drivers (fio, phone, license_number, license_category, license_expiry,
            hire_date, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        driver.fio, driver.phone, driver.license_number, driver.license_category,
        driver.license_expiry, driver.hire_date, driver.status, driver.notes, driver.created_at,
    ))
    conn.commit()
    return cursor.lastrowid


def get_driver(conn: sqlite3.Connection, driver_id: int) -> Optional[Driver]:
    """Получить водителя по id."""
    cursor = conn.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
    row = cursor.fetchone()
    return Driver.from_db_row(tuple(row)) if row else None


def list_drivers(conn: sqlite3.Connection) -> list[Driver]:
    """Список водителей."""
    cursor = conn.execute("SELECT * FROM drivers ORDER BY fio")
    return [Driver.from_db_row(tuple(row)) for row in cursor.fetchall()]


def count_drivers(conn: sqlite3.Connection) -> int:
    """Количество водителей."""
    cursor = conn.execute("SELECT COUNT(*) FROM drivers")
    return cursor.fetchone()[0]


def update_driver(conn: sqlite3.Connection, driver: Driver) -> None:
    """Обновить водителя."""
    conn.execute("""
        UPDATE drivers SET fio=?, phone=?, license_number=?, license_category=?,
            license_expiry=?, hire_date=?, status=?, notes=?
        WHERE id=?
    """, (
        driver.fio, driver.phone, driver.license_number, driver.license_category,
        driver.license_expiry, driver.hire_date, driver.status, driver.notes, driver.id,
    ))
    conn.commit()


def delete_driver(conn: sqlite3.Connection, driver_id: int) -> None:
    """Удалить водителя."""
    conn.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))
    conn.commit()


# ════════════════════════════════════════════════════════════════════
# CRUD: Запчасти
# ════════════════════════════════════════════════════════════════════

def create_part(conn: sqlite3.Connection, part: Part) -> int:
    """Создать запчасть. Возвращает id."""
    cursor = conn.execute("""
        INSERT INTO parts (name, article, category, unit, quantity, min_quantity, avg_price, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        part.name, part.article, part.category, part.unit, part.quantity,
        part.min_quantity, part.avg_price, part.notes, part.created_at, part.updated_at,
    ))
    conn.commit()
    return cursor.lastrowid


def get_part(conn: sqlite3.Connection, part_id: int) -> Optional[Part]:
    """Получить запчасть по id."""
    cursor = conn.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
    row = cursor.fetchone()
    return Part.from_db_row(tuple(row)) if row else None


def list_parts(conn: sqlite3.Connection, category: Optional[str] = None) -> list[Part]:
    """Список запчастей."""
    if category:
        cursor = conn.execute("SELECT * FROM parts WHERE category = ? ORDER BY name", (category,))
    else:
        cursor = conn.execute("SELECT * FROM parts ORDER BY name")
    return [Part.from_db_row(tuple(row)) for row in cursor.fetchall()]


def count_parts(conn: sqlite3.Connection) -> int:
    """Количество запчастей."""
    cursor = conn.execute("SELECT COUNT(*) FROM parts")
    return cursor.fetchone()[0]


def update_part_quantity(conn: sqlite3.Connection, part_id: int, new_quantity: float) -> None:
    """Обновить количество запчасти."""
    conn.execute("UPDATE parts SET quantity = ?, updated_at = date('now') WHERE id = ?", (new_quantity, part_id))
    conn.commit()


# ════════════════════════════════════════════════════════════════════
# CRUD: Транзакции запчастей
# ════════════════════════════════════════════════════════════════════

def create_part_transaction(conn: sqlite3.Connection, tx: PartTransaction) -> int:
    """Создать транзакцию. Возвращает id."""
    cursor = conn.execute("""
        INSERT INTO part_transactions (part_id, transaction_type, quantity, price, vehicle_id, notes, transaction_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx.part_id, tx.transaction_type, tx.quantity, tx.price,
        tx.vehicle_id, tx.notes, tx.transaction_date, tx.created_by,
    ))
    conn.commit()
    return cursor.lastrowid


def list_part_transactions(conn: sqlite3.Connection, part_id: Optional[int] = None) -> list[PartTransaction]:
    """Список транзакций."""
    if part_id:
        cursor = conn.execute("SELECT * FROM part_transactions WHERE part_id = ? ORDER BY transaction_date DESC", (part_id,))
    else:
        cursor = conn.execute("SELECT * FROM part_transactions ORDER BY transaction_date DESC")
    return [PartTransaction.from_db_row(tuple(row)) for row in cursor.fetchall()]


# ════════════════════════════════════════════════════════════════════
# CRUD: График ТО
# ════════════════════════════════════════════════════════════════════

def create_maintenance_schedule(conn: sqlite3.Connection, schedule: MaintenanceSchedule) -> int:
    """Создать график ТО."""
    cursor = conn.execute("""
        INSERT INTO maintenance_schedules (vehicle_id, maintenance_type, interval_km,
            last_done_km, last_done_date, next_due_km, next_due_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        schedule.vehicle_id, schedule.maintenance_type, schedule.interval_km,
        schedule.last_done_km, schedule.last_done_date, schedule.next_due_km,
        schedule.next_due_date, schedule.notes, schedule.created_at,
    ))
    conn.commit()
    return cursor.lastrowid


def list_maintenance_schedules(conn: sqlite3.Connection, vehicle_id: Optional[int] = None) -> list[MaintenanceSchedule]:
    """Список графиков ТО."""
    if vehicle_id:
        cursor = conn.execute("SELECT * FROM maintenance_schedules WHERE vehicle_id = ?", (vehicle_id,))
    else:
        cursor = conn.execute("SELECT * FROM maintenance_schedules ORDER BY next_due_km")
    return [MaintenanceSchedule.from_db_row(tuple(row)) for row in cursor.fetchall()]


# ════════════════════════════════════════════════════════════════════
# CRUD: Записи ТО
# ════════════════════════════════════════════════════════════════════

def create_maintenance_record(conn: sqlite3.Connection, record: MaintenanceRecord) -> int:
    """Создать запись ТО."""
    cursor = conn.execute("""
        INSERT INTO maintenance_records (vehicle_id, maintenance_type, mileage, service_date,
            cost, parts_used, service_provider, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.vehicle_id, record.maintenance_type, record.mileage, record.service_date,
        record.cost, record.parts_used, record.service_provider, record.notes, record.created_at,
    ))
    conn.commit()
    return cursor.lastrowid


def list_maintenance_records(conn: sqlite3.Connection, vehicle_id: Optional[int] = None) -> list[MaintenanceRecord]:
    """Список записей ТО."""
    if vehicle_id:
        cursor = conn.execute("SELECT * FROM maintenance_records WHERE vehicle_id = ? ORDER BY service_date DESC", (vehicle_id,))
    else:
        cursor = conn.execute("SELECT * FROM maintenance_records ORDER BY service_date DESC")
    return [MaintenanceRecord.from_db_row(tuple(row)) for row in cursor.fetchall()]


# ════════════════════════════════════════════════════════════════════
# CRUD: Табель учёта рабочего времени
# ════════════════════════════════════════════════════════════════════

def create_timesheet(conn: sqlite3.Connection, timesheet: Timesheet) -> int:
    """Создать запись в табеле."""
    cursor = conn.execute("""
        INSERT INTO timesheets (driver_id, work_date, status, start_time, end_time, hours, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timesheet.driver_id, timesheet.work_date, timesheet.status,
        timesheet.start_time, timesheet.end_time, timesheet.hours,
        timesheet.notes, timesheet.created_at,
    ))
    conn.commit()
    return cursor.lastrowid


def list_timesheets(conn: sqlite3.Connection, driver_id: Optional[int] = None, 
                    month: Optional[str] = None) -> list[Timesheet]:
    """Список записей табеля. month формат: 'YYYY-MM'."""
    if driver_id and month:
        cursor = conn.execute(
            "SELECT * FROM timesheets WHERE driver_id = ? AND work_date LIKE ? ORDER BY work_date",
            (driver_id, f"{month}%")
        )
    elif driver_id:
        cursor = conn.execute(
            "SELECT * FROM timesheets WHERE driver_id = ? ORDER BY work_date DESC",
            (driver_id,)
        )
    elif month:
        cursor = conn.execute(
            "SELECT * FROM timesheets WHERE work_date LIKE ? ORDER BY work_date",
            (f"{month}%",)
        )
    else:
        cursor = conn.execute("SELECT * FROM timesheets ORDER BY work_date DESC")
    return [Timesheet.from_row(tuple(row)) for row in cursor.fetchall()]


def update_timesheet(conn: sqlite3.Connection, timesheet: Timesheet) -> None:
    """Обновить запись в табеле."""
    conn.execute("""
        UPDATE timesheets SET driver_id=?, work_date=?, status=?, start_time=?, 
            end_time=?, hours=?, notes=?
        WHERE id=?
    """, (
        timesheet.driver_id, timesheet.work_date, timesheet.status,
        timesheet.start_time, timesheet.end_time, timesheet.hours,
        timesheet.notes, timesheet.id,
    ))
    conn.commit()


def delete_timesheet(conn: sqlite3.Connection, timesheet_id: int) -> None:
    """Удалить запись из табеля."""
    conn.execute("DELETE FROM timesheets WHERE id = ?", (timesheet_id,))
    conn.commit()


# ════════════════════════════════════════════════════════════════════
# CRUD: Путевые листы
# ════════════════════════════════════════════════════════════════════

def create_trip_log(conn: sqlite3.Connection, trip: TripLog) -> int:
    """Создать путевой лист."""
    cursor = conn.execute("""
        INSERT INTO trip_logs (driver_id, vehicle_id, trip_date, start_time, end_time,
            start_mileage, end_mileage, distance_km, route_from, route_to, purpose,
            passengers, cargo, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trip.driver_id, trip.vehicle_id, trip.trip_date, trip.start_time, trip.end_time,
        trip.start_mileage, trip.end_mileage, trip.distance_km, trip.route_from, trip.route_to,
        trip.purpose, trip.passengers, trip.cargo, trip.status, trip.notes, trip.created_at,
    ))
    conn.commit()
    return cursor.lastrowid


def get_trip_log(conn: sqlite3.Connection, trip_id: int) -> Optional[TripLog]:
    """Получить путевой лист по id."""
    cursor = conn.execute("SELECT * FROM trip_logs WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    return TripLog.from_row(tuple(row)) if row else None


def list_trip_logs(conn: sqlite3.Connection, driver_id: Optional[int] = None,
                   vehicle_id: Optional[int] = None, month: Optional[str] = None) -> list[TripLog]:
    """Список путевых листов."""
    query = "SELECT * FROM trip_logs WHERE 1=1"
    params = []
    
    if driver_id:
        query += " AND driver_id = ?"
        params.append(driver_id)
    if vehicle_id:
        query += " AND vehicle_id = ?"
        params.append(vehicle_id)
    if month:
        query += " AND trip_date LIKE ?"
        params.append(f"{month}%")
    
    query += " ORDER BY trip_date DESC, start_time DESC"
    cursor = conn.execute(query, params)
    return [TripLog.from_row(tuple(row)) for row in cursor.fetchall()]


def update_trip_log(conn: sqlite3.Connection, trip: TripLog) -> None:
    """Обновить путевой лист."""
    conn.execute("""
        UPDATE trip_logs SET driver_id=?, vehicle_id=?, trip_date=?, start_time=?, end_time=?,
            start_mileage=?, end_mileage=?, distance_km=?, route_from=?, route_to=?, purpose=?,
            passengers=?, cargo=?, status=?, notes=?
        WHERE id=?
    """, (
        trip.driver_id, trip.vehicle_id, trip.trip_date, trip.start_time, trip.end_time,
        trip.start_mileage, trip.end_mileage, trip.distance_km, trip.route_from, trip.route_to,
        trip.purpose, trip.passengers, trip.cargo, trip.status, trip.notes, trip.id,
    ))
    conn.commit()


def delete_trip_log(conn: sqlite3.Connection, trip_id: int) -> None:
    """Удалить путевой лист."""
    conn.execute("DELETE FROM trip_logs WHERE id = ?", (trip_id,))
    conn.commit()

