import requests
import datetime
import time
import random
from typing import List, Dict, Any
from . import models

# Для демонстрации используем API OpenWeatherMap, но в реальном приложении нужен API ключ
# В этом примере мы будем "симулировать" получение данных
def scrape_weather_data(city: str) -> List[models.WeatherData]:
    """
    Скрапит данные о погоде для указанного города.
    В реальном приложении здесь будет запрос к API погоды или парсинг сайта.
    """
    # Симулируем получение исторических данных за последние 10 дней
    today = datetime.date.today()
    weather_data = []
    
    # Базовые значения для города
    base_temperature = {
        "Москва": 15.0,
        "Санкт-Петербург": 12.0, 
        "Новосибирск": 10.0,
        "Екатеринбург": 11.0,
        "Казань": 14.0
    }.get(city, 15.0)  # По умолчанию 15 градусов
    
    base_humidity = random.uniform(50.0, 70.0)
    base_pressure = random.uniform(1000.0, 1020.0)
    
    conditions = ["Ясно", "Облачно", "Дождь", "Пасмурно", "Гроза", "Туман"]
    
    # Генерируем данные за последние 10 дней
    for i in range(10):
        date = today - datetime.timedelta(days=i)
        
        # Добавляем случайные колебания к базовым значениям
        temp_variation = random.uniform(-5.0, 5.0)
        humidity_variation = random.uniform(-10.0, 10.0)
        pressure_variation = random.uniform(-10.0, 10.0)
        
        # Выбираем условие погоды в зависимости от температуры
        if base_temperature + temp_variation > 20:
            condition_probability = [0.7, 0.2, 0.05, 0.03, 0.01, 0.01]
        elif base_temperature + temp_variation > 10:
            condition_probability = [0.4, 0.3, 0.1, 0.1, 0.05, 0.05]
        else:
            condition_probability = [0.2, 0.3, 0.2, 0.2, 0.05, 0.05]
        
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
        
        weather_data.append(models.WeatherData(
            city=city,
            date=date,
            temperature=round(base_temperature + temp_variation, 1),
            humidity=round(base_humidity + humidity_variation, 1),
            pressure=round(base_pressure + pressure_variation, 1),
            wind_speed=round(wind_speed, 1),
            precipitation=round(precipitation, 1),
            weather_condition=condition
        ))
        
        # Небольшая задержка для имитации реального скрапинга
        time.sleep(0.1)
    
    return weather_data

# В реальном проекте здесь был бы код для работы с реальным API
# например, OpenWeatherMap, Weather.com, или другим источником данных
"""
def get_real_weather_data(city: str, api_key: str) -> List[models.WeatherData]:
    # Пример использования API OpenWeatherMap
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # Обработка полученных данных...
    
    return weather_data
"""
