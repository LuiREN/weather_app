import sqlite3
import os
import datetime
import logging
import json
from typing import List, Optional, Dict, Any
from . import models

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        source TEXT DEFAULT 'scraper',
        UNIQUE(city, date)
    )
    ''')
    
    # Создание индекса для ускорения поиска по городу и дате
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_weather_city_date ON weather_data (city, date)
    ''')
    
    # Создание таблицы для хранения моделей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metrics TEXT NOT NULL,
        file_path TEXT NOT NULL,
        UNIQUE(city)
    )
    ''')
    
    # Создание таблицы для хранения параметров конфигурации
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(key)
    )
    ''')
    
    # Создание таблицы для логов скрапинга
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scraping_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.info("База данных инициализирована")

def save_weather_data(data_list: List[models.WeatherData]) -> int:
    """Сохранение данных о погоде в БД."""
    if not data_list:
        logger.warning("Попытка сохранить пустой список данных о погоде")
        return 0
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Сохраняем данные, обрабатывая возможные дубликаты
    last_id = 0
    saved_count = 0
    
    for data in data_list:
        try:
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
            
            last_id = cursor.lastrowid
            saved_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных о погоде: {str(e)}")
    
    conn.commit()
    
    logger.info(f"Сохранено {saved_count} записей о погоде")
    
    conn.close()
    
    return last_id

def get_weather_data(city: Optional[str] = None, days: int = 7) -> List[models.WeatherData]:
    """
    Получение данных о погоде из БД с фильтрацией по городу и периоду.
    
    Args:
        city: Фильтр по городу (если None, берутся данные для всех городов)
        days: Количество дней, за которые нужны данные (от текущей даты)
        
    Returns:
        Список объектов WeatherData с данными о погоде
    """
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
    
    # Добавляем фильтр по дате, вместо ограничения количества записей
    if days > 0:
        cutoff_date = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        where_clauses.append("date >= ?")
        params.append(cutoff_date)
    
    if where_clauses:
        query += f" WHERE {' AND '.join(where_clauses)}"
    
    # Сортируем по дате, но уже не ограничиваем количество записей
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    
    # Преобразуем в объекты Pydantic
    weather_data = []
    for row in result:
        try:
            # Преобразуем строки дат в объекты datetime
            if isinstance(row['date'], str):
                row['date'] = datetime.date.fromisoformat(row['date'])
            if isinstance(row['created_at'], str):
                row['created_at'] = datetime.datetime.fromisoformat(row['created_at'])
                
            # Удаляем поля, которых нет в модели WeatherData (если такие есть)
            filtered_row = {k: v for k, v in row.items() if k in models.WeatherData.__annotations__}
            
            weather_data.append(models.WeatherData(**filtered_row))
        except Exception as e:
            print(f"Ошибка при преобразовании данных о погоде: {str(e)}")
    
    return weather_data

def get_all_cities() -> List[str]:
    """Получение списка всех городов в БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT city FROM weather_data")
    result = cursor.fetchall()
    conn.close()
    
    return [row['city'] for row in result]

def save_model_metrics(city: str, metrics: Dict[str, float], file_path: str) -> int:
    """Сохранение метрик модели в БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Сериализуем метрики в JSON
    metrics_json = json.dumps(metrics)
    
    cursor.execute('''
    INSERT OR REPLACE INTO models (city, metrics, file_path)
    VALUES (?, ?, ?)
    ''', (city, metrics_json, file_path))
    
    model_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    logger.info(f"Сохранены метрики модели для города {city}")
    
    return model_id

def get_model_metrics(city: str) -> Optional[Dict[str, float]]:
    """Получение метрик модели из БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT metrics FROM models WHERE city = ?", (city,))
    result = cursor.fetchone()
    conn.close()
    
    if result and 'metrics' in result:
        try:
            return json.loads(result['metrics'])
        except json.JSONDecodeError:
            logger.error(f"Ошибка при декодировании метрик модели для города {city}")
            return None
    
    return None

def save_scraping_log(
    city: str, 
    start_date: datetime.date, 
    end_date: datetime.date, 
    status: str, 
    message: Optional[str] = None
) -> int:
    """Сохранение лога скрапинга в БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO scraping_logs (city, start_date, end_date, status, message)
    VALUES (?, ?, ?, ?, ?)
    ''', (city, start_date, end_date, status, message))
    
    log_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    logger.info(f"Сохранен лог скрапинга для города {city}")
    
    return log_id

def get_scraping_logs(city: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Получение логов скрапинга из БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM scraping_logs"
    params = []
    
    if city:
        query += " WHERE city = ?"
        params.append(city)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    
    # Преобразуем даты в строках в объекты datetime
    for row in result:
        if isinstance(row['start_date'], str):
            row['start_date'] = datetime.date.fromisoformat(row['start_date'])
        if isinstance(row['end_date'], str):
            row['end_date'] = datetime.date.fromisoformat(row['end_date'])
        if isinstance(row['created_at'], str):
            row['created_at'] = datetime.datetime.fromisoformat(row['created_at'])
    
    return result

def get_data_availability(city: str) -> Dict[str, Any]:
    """Получение информации о доступности данных для города."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем самую раннюю и самую позднюю даты, а также количество записей
    cursor.execute('''
    SELECT 
        MIN(date) as min_date, 
        MAX(date) as max_date, 
        COUNT(*) as count 
    FROM weather_data 
    WHERE city = ?
    ''', (city,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {
            "available": False,
            "min_date": None,
            "max_date": None,
            "count": 0
        }
    
    # Преобразуем строки дат в объекты datetime
    min_date = None
    max_date = None
    
    if result['min_date']:
        min_date = datetime.date.fromisoformat(result['min_date']) if isinstance(result['min_date'], str) else result['min_date']
    
    if result['max_date']:
        max_date = datetime.date.fromisoformat(result['max_date']) if isinstance(result['max_date'], str) else result['max_date']
    
    return {
        "available": result['count'] > 0,
        "min_date": min_date,
        "max_date": max_date,
        "count": result['count']
    }

def get_missing_dates(city: str, start_date: datetime.date, end_date: datetime.date) -> List[datetime.date]:
    """Получение списка дат, для которых отсутствуют данные в указанном промежутке."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем все даты в промежутке
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date.isoformat())
        current_date += datetime.timedelta(days=1)
    
    # Получаем даты, для которых есть данные
    cursor.execute('''
    SELECT date FROM weather_data 
    WHERE city = ? AND date BETWEEN ? AND ?
    ''', (city, start_date.isoformat(), end_date.isoformat()))
    
    result = cursor.fetchall()
    conn.close()
    
    existing_dates = [row['date'] for row in result]
    
    # Находим отсутствующие даты
    missing_dates = set(all_dates) - set(existing_dates)
    
    # Преобразуем строки дат обратно в объекты datetime.date
    return [datetime.date.fromisoformat(date_str) for date_str in missing_dates]