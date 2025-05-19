from pydantic import BaseModel
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

class WeatherForecast(BaseModel):
    city: str
    date: datetime.date
    temperature: float
    humidity: float
    precipitation: float
    weather_condition: str

class ScrapingResponse(BaseModel):
    success: bool
    city: str
    data_points: int
    weather_id: int

class TrainingResponse(BaseModel):
    success: bool
    city: str
    metrics: Dict[str, float]