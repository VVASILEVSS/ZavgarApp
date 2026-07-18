"""
demo_data.py — Заполнение демо-данными для ZavgarApp
====================================================

Создаёт:
- 10 автомобилей
- 10 водителей
- Табель учёта за июль 2026 (реалистичные данные)
"""
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

from zavgar_app import db
from zavgar_app.models import Vehicle, Driver, Timesheet

# Демо автомобили
DEMO_VEHICLES = [
    ("Toyota", "Camry", 2020, "А123ВС77", "car", 45000),
    ("Hyundai", "Sonata", 2021, "В456ОР77", "car", 32000),
    ("KIA", "K5", 2022, "С789НМ77", "car", 18000),
    ("Ford", "Transit", 2019, "Т234ЕА77", "van", 87000),
    ("Mercedes", "Sprinter", 2020, "У567КР77", "van", 95000),
    ("ГАЗель", "Next", 2021, "Х890АВ77", "truck", 54000),
    ("Volvo", "XC90", 2023, "О123ТР77", "car", 12000),
    ("Volkswagen", "Crafter", 2020, "Л456СК77", "van", 110000),
    ("Renault", "Logan", 2018, "Д789ВН77", "car", 125000),
    ("Skoda", "Octavia", 2022, "П012МЗ77", "car", 28000),
]

# Демо водители
DEMO_DRIVERS = [
    ("Иванов Иван Иванович", "+7-916-123-45-67", "77 12 345678", "B", "2028-05-15"),
    ("Петров Пётр Петрович", "+7-926-234-56-78", "77 23 456789", "B", "2027-08-22"),
    ("Сидоров Сидор Сидорович", "+7-903-345-67-89", "77 34 567890", "B", "2029-03-10"),
    ("Козлов Алексей Николаевич", "+7-915-456-78-90", "77 45 678901", "B,C", "2026-12-05"),
    ("Новиков Дмитрий Сергеевич", "+7-926-567-89-01", "77 56 789012", "B", "2028-11-30"),
    ("Морозов Андрей Владимирович", "+7-903-678-90-12", "77 67 890123", "B,D", "2027-06-18"),
    ("Волков Сергей Александрович", "+7-916-789-01-23", "77 78 901234", "B", "2029-09-25"),
    ("Соловьёв Михаил Юрьевич", "+7-915-890-12-34", "77 89 012345", "B,C", "2026-10-12"),
    ("Васильев Николай Игоревич", "+7-903-901-23-45", "77 90 123456", "B", "2028-04-08"),
    ("Зайцев Артём Павлович", "+7-926-012-34-56", "77 01 234567", "B", "2027-12-20"),
]


def generate_july_timesheets(conn, driver_ids):
    """Генерация табеля за июль 2026."""
    timesheets = []
    
    # Июль 2026: 1 июля (среда) - 31 июля (пятница)
    july_start = date(2026, 7, 1)
    july_end = date(2026, 7, 31)
    
    # Выходные: 5-6, 12-13, 19-20, 26-27 (Сб-Вс)
    weekends = {5, 6, 12, 13, 19, 20, 26, 27}
    
    # Больничные дни (примеры)
    sick_days = {
        1: [3, 4, 5],  # Иванов болел 3-5 июля
        5: [10, 11],   # Новиков болел 10-11 июля
    }
    
    # Отпуска
    vacations = {
        3: list(range(15, 29)),  # Сидоров в отпуске 15-28 июля
        8: list(range(20, 29)),  # Соловьёв в отпуске 20-28 июля
    }
    
    current = july_start
    while current <= july_end:
        day_num = current.day
        
        for idx, driver_id in enumerate(driver_ids, 1):
            if day_num in weekends:
                status = 'day_off'
                hours = 0.0
                start_time = None
                end_time = None
            elif day_num in sick_days.get(idx, []):
                status = 'sick'
                hours = 0.0
                start_time = None
                end_time = None
            elif day_num in vacations.get(idx, []):
                status = 'vacation'
                hours = 0.0
                start_time = None
                end_time = None
            else:
                # Рабочий день
                status = 'work'
                # Разные графики для разных водителей
                if idx % 3 == 0:
                    # Ранняя смена
                    start_time = "06:00"
                    end_time = "14:00"
                    hours = 8.0
                elif idx % 3 == 1:
                    # Стандартная смена
                    start_time = "09:00"
                    end_time = "18:00"
                    hours = 8.0
                else:
                    # Поздняя смена
                    start_time = "12:00"
                    end_time = "20:00"
                    hours = 8.0
                
                # Иногда неполный день
                if day_num == 17 and idx == 2:
                    hours = 4.0
                    start_time = "09:00"
                    end_time = "13:00"
            
            ts = Timesheet(
                driver_id=driver_id,
                work_date=current.isoformat(),
                status=status,
                start_time=start_time,
                end_time=end_time,
                hours=hours,
                notes=None,
                created_at=datetime.now().isoformat(sep=' ', timespec='seconds')
            )
            timesheets.append(ts)
        
        current += timedelta(days=1)
    
    return timesheets


def main():
    db_path = Path('zavgar_data.db')
    conn = db.open_db(db_path)
    
    print("Создание демо-данных...")
    
    # Проверка существующих данных
    existing_vehicles = db.count_vehicles(conn)
    existing_drivers = db.count_drivers(conn)
    
    if existing_vehicles > 0 or existing_drivers > 0:
        print(f"⚠️  Уже есть данные: {existing_vehicles} авто, {existing_drivers} водителей")
        response = input("Очистить и создать заново? (y/n): ")
        if response.lower() != 'y':
            print("Отменено.")
            return
        
        # Очистка
        conn.execute("DELETE FROM timesheets")
        conn.execute("DELETE FROM trip_logs")
        conn.execute("DELETE FROM maintenance_records")
        conn.execute("DELETE FROM maintenance_schedules")
        conn.execute("DELETE FROM part_transactions")
        conn.execute("DELETE FROM parts")
        conn.execute("DELETE FROM vehicles")
        conn.execute("DELETE FROM drivers")
        conn.commit()
        print("Старые данные удалены.")
    
    # Создание автомобилей
    print(f"\nСоздание {len(DEMO_VEHICLES)} автомобилей...")
    vehicle_ids = []
    for marka, model, year, gosnomer, vtype, mileage in DEMO_VEHICLES:
        v = Vehicle(
            marka=marka,
            model=model,
            year=year,
            gosnomer=gosnomer,
            vehicle_type=vtype,
            status='active',
            current_mileage=mileage,
            created_at=date.today().isoformat(),
            updated_at=date.today().isoformat()
        )
        vid = db.create_vehicle(conn, v)
        vehicle_ids.append(vid)
        print(f"  ✓ {marka} {model} ({gosnomer})")
    
    # Создание водителей
    print(f"\nСоздание {len(DEMO_DRIVERS)} водителей...")
    driver_ids = []
    for fio, phone, license_num, category, expiry in DEMO_DRIVERS:
        d = Driver(
            fio=fio,
            phone=phone,
            license_number=license_num,
            license_category=category,
            license_expiry=expiry,
            hire_date="2024-01-15",
            status='active',
            notes=None,
            created_at=datetime.now().isoformat()
        )
        did = db.create_driver(conn, d)
        driver_ids.append(did)
        print(f"  ✓ {fio}")
    
    # Назначение водителей на автомобили (первые 10)
    print("\nНазначение водителей на автомобили...")
    for i, (vid, did) in enumerate(zip(vehicle_ids, driver_ids)):
        v = db.get_vehicle(conn, vid)
        v.assigned_driver_id = did
        v.updated_at = date.today().isoformat()
        db.update_vehicle(conn, v)
        print(f"  ✓ {DEMO_VEHICLES[i][0]} {DEMO_VEHICLES[i][1]} → {DEMO_DRIVERS[i][0].split()[0]}")
    
    # Создание табеля за июль 2026
    print("\nГенерация табеля за июль 2026...")
    timesheets = generate_july_timesheets(conn, driver_ids)
    for ts in timesheets:
        db.create_timesheet(conn, ts)
    print(f"  ✓ Создано {len(timesheets)} записей")
    
    # Статистика
    print("\n" + "="*60)
    print("Статистика за июль 2026:")
    print("="*60)
    
    all_timesheets = db.list_timesheets(conn, month="2026-07")
    
    for i, driver_id in enumerate(driver_ids, 1):
        driver_ts = [t for t in all_timesheets if t.driver_id == driver_id]
        work_hours = sum(t.hours for t in driver_ts if t.status == 'work')
        work_days = sum(1 for t in driver_ts if t.status == 'work')
        sick_days = sum(1 for t in driver_ts if t.status == 'sick')
        vacation_days = sum(1 for t in driver_ts if t.status == 'vacation')
        
        driver_name = DEMO_DRIVERS[i-1][0].split()[0]
        print(f"{driver_name:15} | Часы: {work_hours:5.1f} | Дней: {work_days:2} | Больн: {sick_days} | Отп: {vacation_days}")
    
    print("\n✅ Демо-данные успешно созданы!")
    print("Запустите приложение: python -m zavgar_app.main")
    
    conn.close()


if __name__ == '__main__':
    main()
