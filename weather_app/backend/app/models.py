from pydantic import BaseModel, validator
from typing import List, Dict, Optional
import datetime

class WeatherData(BaseModel):
    id: Optional[int] = None
    city: str
    date: datetime.date
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    precipitation: float
    weather_condition: str
    created_at: Optional[datetime.datetime] = None
    
    # Добавляем валидаторы для проверки данных
    @validator('temperature')
    def temperature_range(cls, v):
        if v < -100 or v > 100:
            raise ValueError('Температура должна быть в диапазоне от -100 до 100°C')
        return round(v, 1)
    
    @validator('humidity')
    def humidity_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Влажность должна быть в диапазоне от 0 до 100%')
        return round(v, 1)
    
    @validator('pressure')
    def pressure_range(cls, v):
        if v < 800 or v > 1200:
            raise ValueError('Давление должно быть в диапазоне от 800 до 1200 гПа')
        return round(v, 1)
    
    @validator('wind_speed')
    def wind_speed_positive(cls, v):
        if v < 0:
            raise ValueError('Скорость ветра не может быть отрицательной')
        return round(v, 1)
    
    @validator('precipitation')
    def precipitation_positive(cls, v):
        if v < 0:
            raise ValueError('Количество осадков не может быть отрицательным')
        return round(v, 1)
    
    @validator('weather_condition')
    def weather_condition_valid(cls, v):
        valid_conditions = [
            "Ясно", "Облачно", "Пасмурно", "Туман", 
            "Дождь", "Гроза", "Снег", "Неизвестно"
        ]
        if v not in valid_conditions:
            # Нормализуем условие погоды, если оно не входит в список допустимых
            for condition in valid_conditions:
                if condition.lower() in v.lower():
                    return condition
            return "Неизвестно"
        return v

class WeatherForecast(BaseModel):
    city: str
    date: datetime.date
    temperature: float
    humidity: float
    precipitation: float
    weather_condition: str
    
    # Добавляем валидаторы и для прогноза
    @validator('temperature')
    def temperature_range(cls, v):
        if v < -100 or v > 100:
            raise ValueError('Температура должна быть в диапазоне от -100 до 100°C')
        return round(v, 1)
    
    @validator('humidity')
    def humidity_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Влажность должна быть в диапазоне от 0 до 100%')
        return round(v, 1)
    
    @validator('precipitation')
    def precipitation_positive(cls, v):
        if v < 0:
            raise ValueError('Количество осадков не может быть отрицательным')
        return round(v, 1)

class ScrapingResponse(BaseModel):
    success: bool
    city: str
    data_points: int
    weather_id: int

class TrainingResponse(BaseModel):
    success: bool
    city: str
    metrics: Dict[str, float]

class ModelConfig(BaseModel):
    """Модель для настройки параметров модели прогнозирования"""
    n_estimators: int = 50
    random_state: int = 42
    max_depth: Optional[int] = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1