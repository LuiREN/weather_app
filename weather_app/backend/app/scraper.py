import requests
import datetime
import time
import random
from typing import List, Dict, Any, Optional
from backend.app import models

# API ключ для OpenWeatherMap (нужно будет заменить на ваш собственный)
OPENWEATHER_API_KEY = "ваш_api_ключ"  # Замените на свой ключ

def get_weather_from_api(city: str, date: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """
    Получение данных о погоде через OpenWeatherMap API.
    
    Args:
        city: Название города
        date: Дата для которой нужны данные (если None, берется текущая дата)
        
    Returns:
        Словарь с данными о погоде или None в случае ошибки
    """
    try:
        # Если дата не указана, используем текущую
        if not date:
            date = datetime.date.today()
        
        # Первым шагом получаем координаты города
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {
            "q": city,
            "limit": 1,
            "appid": OPENWEATHER_API_KEY
        }
        
        geo_response = requests.get(geo_url, params=geo_params)
        geo_response.raise_for_status()
        
        locations = geo_response.json()
        if not locations:
            print(f"Город {city} не найден в API")
            return None
            
        # Получаем координаты
        lat = locations[0]["lat"]
        lon = locations[0]["lon"]
        
        # Запрашиваем текущую погоду, если дата - сегодня
        if date == datetime.date.today():
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                "lat": lat,
                "lon": lon,
                "units": "metric",  # Для получения температуры в Цельсиях
                "appid": OPENWEATHER_API_KEY
            }
            
            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            # Формируем данные в нужном формате
            result = {
                "temperature": weather_data["main"]["temp"],
                "humidity": weather_data["main"]["humidity"],
                "pressure": weather_data["main"]["pressure"],
                "wind_speed": weather_data["wind"]["speed"],
                "precipitation": weather_data.get("rain", {}).get("1h", 0) if "rain" in weather_data else 0,
                "weather_condition": get_weather_condition(weather_data["weather"][0]["id"])
            }
            
            return result
            
        else:
            # Для получения исторических данных используем OpenWeatherMap History API
            # Однако этот API платный, поэтому для демонстрации генерируем случайные данные
            # В реальном проекте здесь был бы запрос к API
            
            # Генерируем случайные данные для демонстрации
            return generate_weather_data(city, date)
            
    except Exception as e:
        print(f"Ошибка при получении данных о погоде через API: {str(e)}")
        return None

def get_weather_condition(weather_id: int) -> str:
    """
    Преобразование кода погоды из API в текстовое описание.
    
    Args:
        weather_id: Код погоды из OpenWeatherMap API
        
    Returns:
        Текстовое описание погоды
    """
    # Маппинг кодов погоды на наши категории
    if weather_id >= 800 and weather_id < 900:
        if weather_id == 800:
            return "Ясно"
        else:
            return "Облачно"
    elif weather_id >= 700:
        return "Туман"
    elif weather_id >= 600:
        return "Снег"
    elif weather_id >= 500:
        return "Дождь"
    elif weather_id >= 300:
        return "Дождь"
    elif weather_id >= 200:
        return "Гроза"
    else:
        return "Неизвестно"

def generate_weather_data(city: str, date: datetime.date) -> Dict[str, Any]:
    """
    Генерация случайных данных о погоде для демонстрации.
    В реальном проекте здесь был бы запрос к API для исторических данных.
    
    Args:
        city: Название города
        date: Дата для которой нужны данные
        
    Returns:
        Словарь с данными о погоде
    """
    # Базовые значения для города
    base_temperature = {
        "Москва": 15.0,
        "Санкт-Петербург": 12.0,
        "Новосибирск": 10.0,
        "Екатеринбург": 11.0,
        "Казань": 14.0,
        "Тверь": 13.0,
        "Владивосток": 12.0,
        "Сочи": 22.0,
        "Калининград": 13.0,
        "Мурманск": 5.0
    }.get(city, 15.0)  # По умолчанию 15 градусов
    
    # Учитываем сезонность
    month = date.month
    if month in [12, 1, 2]:  # Зима
        base_temperature -= 15
    elif month in [3, 4, 5]:  # Весна
        base_temperature -= 5
    elif month in [6, 7, 8]:  # Лето
        base_temperature += 10
    else:  # Осень
        base_temperature += 0
    
    # Добавляем случайные колебания
    temp_variation = random.uniform(-5.0, 5.0)
    humidity_variation = random.uniform(-10.0, 10.0)
    base_humidity = random.uniform(50.0, 70.0)
    base_pressure = random.uniform(1000.0, 1020.0)
    pressure_variation = random.uniform(-10.0, 10.0)
    
    # Определяем состояние погоды
    effective_temp = base_temperature + temp_variation
    
    if effective_temp > 20:
        condition_probability = [0.7, 0.2, 0.05, 0.03, 0.01, 0.01]
    elif effective_temp > 10:
        condition_probability = [0.4, 0.3, 0.1, 0.1, 0.05, 0.05]
    else:
        condition_probability = [0.2, 0.3, 0.2, 0.2, 0.05, 0.05]
    
    conditions = ["Ясно", "Облачно", "Дождь", "Пасмурно", "Гроза", "Туман"]
    condition = random.choices(conditions, weights=condition_probability)[0]
    
    # Определяем осадки в зависимости от условия погоды
    precipitation = {
        "Ясно": random.uniform(0, 0.5),
        "Облачно": random.uniform(0, 2),
        "Дождь": random.uniform(2, 10),
        "Пасмурно": random.uniform(0, 5),
        "Гроза": random.uniform(5, 20),
        "Туман": random.uniform(0, 1)
    }[condition]
    
    # Скорость ветра
    wind_speed = random.uniform(1.0, 10.0)
    
    return {
        "temperature": round(effective_temp, 1),
        "humidity": round(base_humidity + humidity_variation, 1),
        "pressure": round(base_pressure + pressure_variation, 1),
        "wind_speed": round(wind_speed, 1),
        "precipitation": round(precipitation, 1),
        "weather_condition": condition
    }

def scrape_weather_data(
    city: str,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    disable_limit: bool = True  # По умолчанию лимит отключен
) -> List[models.WeatherData]:
    """
    Получение данных о погоде для указанного города и периода.
    
    Args:
        city: Название города
        start_date: Начальная дата периода (включительно)
        end_date: Конечная дата периода (включительно)
        disable_limit: Отключить ограничение на количество дней
    
    Returns:
        Список объектов WeatherData с данными о погоде
    """
    # Установка значений по умолчанию
    if not end_date:
        end_date = datetime.date.today()
    if not start_date:
        start_date = end_date - datetime.timedelta(days=9)  # По умолчанию 10 дней
    
    # Проверка корректности дат
    if start_date > end_date:
        raise ValueError("Начальная дата не может быть позже конечной")
    
    # Убираем проверку на максимальное количество дней
    days_diff = (end_date - start_date).days + 1  # +1 чтобы включить конечную дату
    
    print(f"Сбор данных о погоде для города {city} за период с {start_date} по {end_date} ({days_diff} дней)")
    
    # Собираем данные за указанный период
    weather_data_list = []
    
    current_date = start_date
    while current_date <= end_date:
        # Генерируем данные для текущей даты
        data = generate_weather_data(city, current_date)
        
        # Создаем объект WeatherData
        weather_data = models.WeatherData(
            city=city,
            date=current_date,
            temperature=data["temperature"],
            humidity=data["humidity"],
            pressure=data["pressure"],
            wind_speed=data["wind_speed"],
            precipitation=data["precipitation"],
            weather_condition=data["weather_condition"]
        )
        
        weather_data_list.append(weather_data)
        
        # Переходим к следующей дате
        current_date += datetime.timedelta(days=1)
        
        # Небольшая задержка, чтобы не перегружать систему
        # при очень больших периодах
        if days_diff > 100 and (current_date - start_date).days % 50 == 0:
            print(f"Обработано {(current_date - start_date).days} дней из {days_diff}...")
            time.sleep(0.5)  # Пауза каждые 50 дней
        else:
            time.sleep(0.05)  # Небольшая пауза для остальных дней
    
    print(f"Завершен сбор данных о погоде для города {city}. Получено {len(weather_data_list)} записей.")
    return weather_data_list