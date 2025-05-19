import sqlite3
import os
import datetime
from typing import List, Optional, Dict, Any
from . import models

# Путь к файлу БД
DATABASE_PATH = "/app/database/weather.db"

def dict_factory(cursor, row):
    """Преобразование строк в словари для удобной работы с данными."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Создание соединения с БД с настройкой конвертации типов."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = dict_factory
    
    # Настройка для правильной работы с датами
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Конвертация строк в даты и обратно
    sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())
    sqlite3.register_adapter(datetime.datetime, lambda val: val.isoformat())
    sqlite3.register_converter("DATE", lambda val: datetime.date.fromisoformat(val.decode()))
    sqlite3.register_converter("TIMESTAMP", lambda val: datetime.datetime.fromisoformat(val.decode()))
    
    return conn

def init_db():
    """Инициализация базы данных при первом запуске."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создание таблицы с погодными данными
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        date DATE NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        pressure REAL NOT NULL,
        wind_speed REAL NOT NULL,
        precipitation REAL NOT NULL,
        weather_condition TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(city, date)
    )
    ''')
    
    # Создание индекса для ускорения поиска по городу и дате
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_weather_city_date ON weather_data (city, date)
    ''')
    
    conn.commit()
    conn.close()

def save_weather_data(data_list: List[models.WeatherData]) -> int:
    """Сохранение данных о погоде в БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Сохраняем данные, обрабатывая возможные дубликаты
    for data in data_list:
        cursor.execute('''
        INSERT OR REPLACE INTO weather_data
        (city, date, temperature, humidity, pressure, wind_speed, precipitation, weather_condition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.city,
            data.date,
            data.temperature,
            data.humidity,
            data.pressure,
            data.wind_speed,
            data.precipitation,
            data.weather_condition
        ))
    
    conn.commit()
    # Получаем ID последнего добавленного элемента
    last_id = cursor.lastrowid
    conn.close()
    
    return last_id

def get_weather_data(city: Optional[str] = None, days: int = 7) -> List[models.WeatherData]:
    """Получение данных о погоде из БД с фильтрацией по городу и ограничением по дням."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT * FROM weather_data
    '''
    
    params = []
    where_clauses = []
    
    if city:
        where_clauses.append("city = ?")
        params.append(city)
    
    if where_clauses:
        query += f" WHERE {' AND '.join(where_clauses)}"
    
    query += f" ORDER BY date DESC LIMIT {days}"
    
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    
    # Преобразуем в объекты Pydantic
    weather_data = []
    for row in result:
        # Преобразуем строки дат в объекты datetime
        if isinstance(row['date'], str):
            row['date'] = datetime.date.fromisoformat(row['date'])
        if isinstance(row['created_at'], str):
            row['created_at'] = datetime.datetime.fromisoformat(row['created_at'])
            
        weather_data.append(models.WeatherData(**row))
    
    return weather_data

def get_all_cities() -> List[str]:
    """Получение списка всех городов в БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT city FROM weather_data")
    result = cursor.fetchall()
    conn.close()
    
    return [row['city'] for row in result]
