from fastapi import FastAPI, HTTPException, Query, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import datetime
import json
from . import models, database, scraper, ml_model

router = APIRouter()

# Получение всех городов в базе
@router.get("/cities", response_model=List[str])
async def get_cities():
    return database.get_all_cities()

# Скрапинг данных о погоде для указанного города
@router.post("/scrape", response_model=models.ScrapingResponse)
async def scrape_weather(
    city: str = Query(..., description="Название города"),
    start_date: Optional[datetime.date] = Query(None, description="Начальная дата для сбора данных"),
    end_date: Optional[datetime.date] = Query(None, description="Конечная дата для сбора данных"),
    disable_limit: bool = Query(True, description="Отключить ограничение на количество дней")
):
    try:
        
        log_id = database.save_scraping_log(
            city=city,
            start_date=start_date or (datetime.date.today() - datetime.timedelta(days=9)),
            end_date=end_date or datetime.date.today(),
            status="pending",
            message="Начало сбора данных"
        )
        
        # Выполняем скрапинг
        try:
            data = scraper.scrape_weather_data(
                city=city, 
                start_date=start_date, 
                end_date=end_date, 
                disable_limit=disable_limit
            )
            
            # Если нет данных, возвращаем ошибку
            if not data:
                database.save_scraping_log(
                    city=city,
                    start_date=start_date or (datetime.date.today() - datetime.timedelta(days=9)),
                    end_date=end_date or datetime.date.today(),
                    status="error",
                    message=f"Не удалось получить данные о погоде для города {city}"
                )
                raise HTTPException(status_code=404, detail=f"Не удалось получить данные о погоде для города {city}")
            
            # Сохраняем полученные данные в базу
            weather_id = database.save_weather_data(data)
            
            # Регистрируем успешное завершение операции
            database.save_scraping_log(
                city=city,
                start_date=start_date or (datetime.date.today() - datetime.timedelta(days=9)),
                end_date=end_date or datetime.date.today(),
                status="success",
                message=f"Успешно собрано {len(data)} записей"
            )
            
            return models.ScrapingResponse(
                success=True,
                city=city,
                data_points=len(data),
                weather_id=weather_id,
                message=f"Успешно собрано {len(data)} записей"
            )
            
        except Exception as e:
          
            database.save_scraping_log(
                city=city,
                start_date=start_date or (datetime.date.today() - datetime.timedelta(days=9)),
                end_date=end_date or datetime.date.today(),
                status="error",
                message=f"Ошибка: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=f"Ошибка скрапинга: {str(e)}")
            
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Ошибка скрапинга: {str(e)}")

# Получение погодных данных из БД
@router.get("/weather", response_model=List[models.WeatherData])
async def get_weather_data(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    days: Optional[int] = Query(7, description="Количество дней для получения данных"),
):
    return database.get_weather_data(city, days)


@router.get("/forecast", response_model=List[models.WeatherForecast])
async def get_forecast(
    city: str = Query(..., description="Город для прогноза"),
    days: int = Query(5, description="Количество дней для прогноза"),
):
    
    data = database.get_weather_data(city, 30)  
    if len(data) < 5:
        raise HTTPException(status_code=400, detail="Недостаточно данных для прогноза. Сначала выполните скрапинг.")
    
    forecast = ml_model.make_forecast(data, days)
    return forecast


@router.post("/train_model", response_model=models.TrainingResponse)
async def train_model(city: str = Query(..., description="Город для обучения модели")):
    try:
        data = database.get_weather_data(city, 30)  # Берем данные за 30 дней для обучения
        if len(data) < 5:
            raise HTTPException(status_code=400, detail="Недостаточно данных для обучения модели")
        
        metrics = ml_model.train_model(data)
        
        # Сохраняем метрики модели в БД
        database.save_model_metrics(city, metrics, ml_model.MODEL_PATH)
        
        return models.TrainingResponse(
            success=True,
            city=city,
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обучении модели: {str(e)}")

# Получение логов скрапинга
@router.get("/scraping_logs", response_model=List[Dict])
async def get_scraping_logs(
    city: Optional[str] = Query(None, description="Фильтр по городу"),
    limit: int = Query(10, description="Ограничение количества возвращаемых записей")
):
    try:
        logs = database.get_scraping_logs(city, limit)
        
        # Преобразуем объекты datetime в строки для JSON
        for log in logs:
            if 'created_at' in log and isinstance(log['created_at'], datetime.datetime):
                log['created_at'] = log['created_at'].isoformat()
            if 'start_date' in log and isinstance(log['start_date'], datetime.date):
                log['start_date'] = log['start_date'].isoformat()
            if 'end_date' in log and isinstance(log['end_date'], datetime.date):
                log['end_date'] = log['end_date'].isoformat()
                
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении логов: {str(e)}")

# Получение информации о доступности данных
@router.get("/data_availability")
async def get_data_availability(
    city: str = Query(..., description="Город для проверки доступности данных"),
    start_date: Optional[datetime.date] = Query(None, description="Начальная дата для проверки"),
    end_date: Optional[datetime.date] = Query(None, description="Конечная дата для проверки")
):
    try:
   
        if not start_date:
            start_date = datetime.date.today() - datetime.timedelta(days=29)
        if not end_date:
            end_date = datetime.date.today()
            
        
        availability = database.get_data_availability(city)
        
        
        existing_dates = []
        
        
        weather_data = database.get_weather_data(city, 100)  
        
        for data in weather_data:
            if start_date <= data.date <= end_date:
                existing_dates.append(data.date.isoformat())
        
      
        missing_dates = database.get_missing_dates(city, start_date, end_date)
        missing_dates_iso = [d.isoformat() for d in missing_dates]
        
        return {
            "available": availability["available"],
            "min_date": availability["min_date"].isoformat() if availability["min_date"] else None,
            "max_date": availability["max_date"].isoformat() if availability["max_date"] else None,
            "count": availability["count"],
            "existing_dates": existing_dates,
            "missing_dates": missing_dates_iso,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации о доступности данных: {str(e)}")

# Создание приложения FastAPI
app = FastAPI(title="Weather API", description="API для работы с погодными данными")

# Настройка CORS для взаимодействия с фронтендом Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    database.init_db()


app.include_router(router)