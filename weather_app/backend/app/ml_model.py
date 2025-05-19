import numpy as np
import datetime
import joblib
import os
from typing import List, Dict, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from backend.app import models

# Путь для сохранения обученной модели
MODEL_PATH = "/app/database/weather_model.joblib"
SCALER_PATH = "/app/database/weather_scaler.joblib"
ENCODER_PATH = "/app/database/weather_encoder.joblib"

def prepare_data(data: List[models.WeatherData]):
    """Подготовка данных для обучения модели."""
    # Преобразуем данные в формат, подходящий для модели
    dates = []
    temps = []
    humidities = []
    pressures = []
    wind_speeds = []
    precipitations = []
    conditions = []
    
    for item in data:
        dates.append(item.date)
        temps.append(item.temperature)
        humidities.append(item.humidity)
        pressures.append(item.pressure)
        wind_speeds.append(item.wind_speed)
        precipitations.append(item.precipitation)
        conditions.append(item.weather_condition)
    
    # Создаем дополнительные признаки из даты
    day_of_year = [d.timetuple().tm_yday for d in dates]
    day_of_week = [d.weekday() for d in dates]
    month = [d.month for d in dates]
    
    X = np.column_stack([
        day_of_year, day_of_week, month,
        temps, humidities, pressures, wind_speeds, precipitations
    ])
    
    return X, conditions, dates

def train_model(data: List[models.WeatherData]) -> Dict[str, float]:
    """Обучение модели прогнозирования погоды."""
    if len(data) < 5:
        raise ValueError("Недостаточно данных для обучения модели")
    
    # Подготовка данных
    X, conditions, dates = prepare_data(data)
    
    # Создаем признаки для прогнозирования
    y_temp = np.array([item.temperature for item in data])
    y_humidity = np.array([item.humidity for item in data])
    y_precip = np.array([item.precipitation for item in data])
    
    # Масштабирование признаков
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Кодирование категориальных признаков - исправление предупреждения
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoded_conditions = encoder.fit_transform(np.array(conditions).reshape(-1, 1))
    
    # Сохраняем scaler и encoder для последующего использования
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(encoder, ENCODER_PATH)
    
    # Обучение моделей для разных целевых переменных
    model_temp = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=None)
    model_humidity = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=None)
    model_precip = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=None)
    
    model_temp.fit(X_scaled, y_temp)
    model_humidity.fit(X_scaled, y_humidity)
    model_precip.fit(X_scaled, y_precip)
    
    # Объединяем модели в один словарь и сохраняем
    models_dict = {
        'temperature': model_temp,
        'humidity': model_humidity,
        'precipitation': model_precip,
        'conditions_encoder': encoder
    }
    
    joblib.dump(models_dict, MODEL_PATH)
    
    # Оценка качества модели
    y_temp_pred = model_temp.predict(X_scaled)
    y_humidity_pred = model_humidity.predict(X_scaled)
    y_precip_pred = model_precip.predict(X_scaled)
    
    metrics = {
        'temp_rmse': float(np.sqrt(mean_squared_error(y_temp, y_temp_pred))),
        'temp_mae': float(mean_absolute_error(y_temp, y_temp_pred)),
        'temp_r2': float(r2_score(y_temp, y_temp_pred)),  # Добавляем R²
        'humidity_rmse': float(np.sqrt(mean_squared_error(y_humidity, y_humidity_pred))),
        'humidity_mae': float(mean_absolute_error(y_humidity, y_humidity_pred)),
        'humidity_r2': float(r2_score(y_humidity, y_humidity_pred)),  # Добавляем R²
        'precip_rmse': float(np.sqrt(mean_squared_error(y_precip, y_precip_pred))),
        'precip_mae': float(mean_absolute_error(y_precip, y_precip_pred)),
        'precip_r2': float(r2_score(y_precip, y_precip_pred))  # Добавляем R²
    }
    
    return metrics

def make_forecast(data: List[models.WeatherData], days: int = 5) -> List[models.WeatherForecast]:
    """Создание прогноза погоды на основе исторических данных."""
    # Проверяем, существует ли модель
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH) or not os.path.exists(ENCODER_PATH):
        # Если модели нет, обучаем новую
        train_model(data)
    
    # Загружаем сохраненные модели и преобразователи
    models_dict = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    encoder = joblib.load(ENCODER_PATH)
    
    model_temp = models_dict['temperature']
    model_humidity = models_dict['humidity']
    model_precip = models_dict['precipitation']
    
    # Создаем прогноз на указанное количество дней
    forecasts = []
    city = data[0].city
    last_date = max(item.date for item in data)
    
    for i in range(1, days + 1):
        forecast_date = last_date + datetime.timedelta(days=i)
        
        # Создаем признаки для прогноза
        day_of_year = forecast_date.timetuple().tm_yday
        day_of_week = forecast_date.weekday()
        month = forecast_date.month
        
        # Используем последние известные значения для создания начальных признаков
        last_item = data[0]  # Берем самую последнюю запись
        
        X = np.array([
            day_of_year, day_of_week, month,
            last_item.temperature, last_item.humidity, 
            last_item.pressure, last_item.wind_speed,
            last_item.precipitation
        ]).reshape(1, -1)
        
        # Масштабируем признаки
        X_scaled = scaler.transform(X)
        
        # Прогнозируем значения
        temp_pred = model_temp.predict(X_scaled)[0]
        humidity_pred = model_humidity.predict(X_scaled)[0]
        precip_pred = model_precip.predict(X_scaled)[0]
        
        # Определяем состояние погоды на основе прогнозируемых значений
        if precip_pred > 5:
            if temp_pred > 15:
                condition = "Гроза"
            else:
                condition = "Дождь"
        elif precip_pred > 1:
            condition = "Пасмурно"
        elif humidity_pred > 80:
            condition = "Туман"
        elif humidity_pred > 60:
            condition = "Облачно"
        else:
            condition = "Ясно"
        
        forecasts.append(models.WeatherForecast(
            city=city,
            date=forecast_date,
            temperature=round(float(temp_pred), 1),
            humidity=round(float(humidity_pred), 1),
            precipitation=round(float(precip_pred), 1),
            weather_condition=condition
        ))
    
    return forecasts