from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import datetime
from . import models, database, scraper, ml_model

app = FastAPI(title="Weather API", description="API для работы с погодными данными")

# Настройка CORS для взаимодействия с фронтендом Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД при запуске
@app.on_event("startup")
async def startup():
    database.init_db()

# Получение всех городов в базе
@app.get("/cities", response_model=List[str])
async def get_cities():
    return database.get_all_cities()

# Скрапинг данных о погоде для указанного города
@app.post("/scrape", response_model=models.ScrapingResponse)
async def scrape_weather(city: str = Query(..., description="Название города")):
    try:
        data = scraper.scrape_weather_data(city)
        weather_id = database.save_weather_data(data)
        return models.ScrapingResponse(
            success=True,
            city=city,
            data_points=len(data),
            weather_id=weather_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скрапинга: {str(e)}")

# Получение погодных данных из БД
@app.get("/weather", response_model=List[models.WeatherData])
async def get_weather_data(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    days: Optional[int] = Query(7, description="Количество дней для получения данных"),
):
    return database.get_weather_data(city, days)

# Получение прогноза погоды на основе исторических данных
@app.get("/forecast", response_model=List[models.WeatherForecast])
async def get_forecast(
    city: str = Query(..., description="Город для прогноза"),
    days: int = Query(5, description="Количество дней для прогноза"),
):
    # Проверка наличия достаточного количества данных
    data = database.get_weather_data(city, 30)  # Берем данные за 30 дней для обучения
    if len(data) < 5:
        raise HTTPException(status_code=400, detail="Недостаточно данных для прогноза. Сначала выполните скрапинг.")
    
    forecast = ml_model.make_forecast(data, days)
    return forecast

# Тренировка модели на основе собранных данных
@app.post("/train_model", response_model=models.TrainingResponse)
async def train_model(city: str = Query(..., description="Город для обучения модели")):
    try:
        data = database.get_weather_data(city, 30)  # Берем данные за 30 дней для обучения
        if len(data) < 5:
            raise HTTPException(status_code=400, detail="Недостаточно данных для обучения модели")
        
        metrics = ml_model.train_model(data)
        return models.TrainingResponse(
            success=True,
            city=city,
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обучении модели: {str(e)}")