"""
db/drivers.py — CRUD операции для водителей
"""
from __future__ import annotations
import sqlite3
from zavgar_app.models.driver import Driver


def create_drivers_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT NOT NULL,
            phone TEXT DEFAULT '',
            license_number TEXT DEFAULT '',
            license_category TEXT DEFAULT '',
            license_expiry TEXT DEFAULT '',
            hire_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def add_driver(conn: sqlite3.Connection, driver: Driver) -> int:
    cursor = conn.execute("""
        INSERT INTO drivers (fio, phone, license_number, license_category, 
                            license_expiry, hire_date, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (driver.fio, driver.phone, driver.license_number, driver.license_category,
          driver.license_expiry, driver.hire_date, driver.notes,
          driver.created_at, driver.updated_at))
    conn.commit()
    return cursor.lastrowid


def get_driver(conn: sqlite3.Connection, driver_id: int) -> Driver | None:
    cursor = conn.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
    row = cursor.fetchone()
    return Driver.from_row(row) if row else None


def get_all_drivers(conn: sqlite3.Connection) -> list[Driver]:
    cursor = conn.execute("SELECT * FROM drivers ORDER BY fio")
    return [Driver.from_row(row) for row in cursor.fetchall()]


def update_driver(conn: sqlite3.Connection, driver: Driver):
    conn.execute("""
        UPDATE drivers SET 
            fio=?, phone=?, license_number=?, license_category=?,
            license_expiry=?, hire_date=?, notes=?, updated_at=?
        WHERE id=?
    """, (driver.fio, driver.phone, driver.license_number, driver.license_category,
          driver.license_expiry, driver.hire_date, driver.notes,
          driver.updated_at, driver.id))
    conn.commit()


def delete_driver(conn: sqlite3.Connection, driver_id: int):
    conn.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))
    conn.commit()


def assign_driver_to_vehicle(conn: sqlite3.Connection, vehicle_id: int, driver_id: int):
    """Назначить водителя на автомобиль"""
    conn.execute("""
        UPDATE vehicles SET assigned_driver_id = ?, updated_at = ?
        WHERE id = ?
    """, (driver_id, datetime.now().isoformat(), vehicle_id))
    conn.commit()


def get_vehicle_driver(conn: sqlite3.Connection, vehicle_id: int) -> Driver | None:
    """Получить водителя, назначенного на автомобиль"""
    cursor = conn.execute("""
        SELECT d.* FROM drivers d
        INNER JOIN vehicles v ON v.assigned_driver_id = d.id
        WHERE v.id = ?
    """, (vehicle_id,))
    row = cursor.fetchone()
    return Driver.from_row(row) if row else None
