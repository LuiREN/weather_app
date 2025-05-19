import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import json
from typing import List, Dict, Any, Optional

# URL бэкенда
BACKEND_URL = "http://backend:8000"

# Настройка страницы
st.set_page_config(
    page_title="Прогноз погоды",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Функции визуализации

def plot_temperature(data):
    """Создание графика температуры."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = px.line(
        df, 
        x='date', 
        y='temperature', 
        title="Температура",
        labels={"date": "Дата", "temperature": "Температура (°C)"},
        markers=True
    )
    fig.update_layout(height=400)
    return fig

def plot_humidity(data):
    """Создание графика влажности."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = px.line(
        df, 
        x='date', 
        y='humidity', 
        title="Влажность",
        labels={"date": "Дата", "humidity": "Влажность (%)"},
        markers=True
    )
    fig.update_layout(height=400)
    return fig

def plot_precipitation(data):
    """Создание графика осадков."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = px.bar(
        df, 
        x='date', 
        y='precipitation', 
        title="Осадки",
        labels={"date": "Дата", "precipitation": "Осадки (мм)"},
        color='precipitation',
        color_continuous_scale='blues'
    )
    fig.update_layout(height=400)
    return fig

def plot_weather_conditions(data):
    """Создание графика состояний погоды."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Создаем словарь для маппинга состояний погоды на числовые значения
    condition_map = {
        "Ясно": 1,
        "Облачно": 2,
        "Пасмурно": 3,
        "Туман": 4,
        "Дождь": 5,
        "Гроза": 6,
        "Снег": 7,
        "Неизвестно": 0
    }
    
    # Преобразуем текстовые условия в числовые коды
    df['condition_code'] = df['weather_condition'].map(lambda x: condition_map.get(x, 0))
    
    fig = px.scatter(
        df, 
        x='date', 
        y='condition_code', 
        title="Состояние погоды",
        labels={"date": "Дата", "condition_code": "Состояние"},
        color='weather_condition',
        symbol='weather_condition',
        size=[10] * len(df),
        category_orders={"condition_code": list(condition_map.values())}
    )
    
    # Настраиваем ось Y для отображения текстовых меток
    fig.update_layout(
        height=400,
        yaxis=dict(
            tickmode='array',
            tickvals=list(condition_map.values()),
            ticktext=list(condition_map.keys())
        )
    )
    
    return fig

def plot_model_metrics(metrics):
    """Создание графика метрик модели."""
    if not metrics:
        return None
    
    # Создаем данные для графика
    metrics_df = pd.DataFrame({
        'Метрика': ['RMSE температуры', 'MAE температуры', 'RMSE влажности', 'MAE влажности', 'RMSE осадков', 'MAE осадков'],
        'Значение': [
            metrics.get('temp_rmse', 0), 
            metrics.get('temp_mae', 0),
            metrics.get('humidity_rmse', 0), 
            metrics.get('humidity_mae', 0),
            metrics.get('precip_rmse', 0), 
            metrics.get('precip_mae', 0)
        ],
        'Категория': ['Температура', 'Температура', 'Влажность', 'Влажность', 'Осадки', 'Осадки']
    })
    
    fig = px.bar(
        metrics_df,
        x='Метрика',
        y='Значение',
        color='Категория',
        title="Метрики качества модели",
        barmode='group'
    )
    
    fig.update_layout(height=400)
    return fig

def plot_data_availability(city, start_date, end_date):
    """Создание графика доступности данных."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/data_availability",
            params={
                "city": city,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        if not data or not data.get("existing_dates"):
            return None
        
        # Получаем все даты в промежутке
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        # Получаем даты, для которых есть данные
        existing_dates = [datetime.datetime.fromisoformat(d).date() for d in data.get("existing_dates", [])]
        
        # Создаем DataFrame
        df = pd.DataFrame({
            'date': all_dates,
            'available': [1 if d in existing_dates else 0 for d in all_dates]
        })
        
        # Создаем график
        fig = px.bar(
            df,
            x='date',
            y='available',
            title="Доступность данных",
            labels={"date": "Дата", "available": "Доступность"},
            color='available',
            color_discrete_map={0: 'red', 1: 'green'}
        )
        
        fig.update_layout(
            height=200,
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1],
                ticktext=['Нет данных', 'Есть данные']
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Ошибка при построении графика доступности данных: {str(e)}")
        return None

# Функции для взаимодействия с API

def get_cities():
    """Получение списка городов из API."""
    try:
        response = requests.get(f"{BACKEND_URL}/cities")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при получении городов: {response.text}")
            return []
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return []

def scrape_weather_data(city, start_date=None, end_date=None):
    """Запуск скрапинга данных о погоде."""
    try:
        url = f"{BACKEND_URL}/scrape"
        params = {
            "city": city,
            "disable_limit": True
        }
        
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при скрапинге данных: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return None

def get_weather_data(city: Optional[str] = None, days: int = 7):
    """Получение данных о погоде из API."""
    try:
        url = f"{BACKEND_URL}/weather"
        params = {"days": days}
        if city:
            params["city"] = city
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при получении данных о погоде: {response.text}")
            return []
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return []

def train_model(city):
    """Обучение модели для прогнозирования погоды."""
    try:
        response = requests.post(f"{BACKEND_URL}/train_model?city={city}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при обучении модели: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return None

def get_forecast(city, days=5):
    """Получение прогноза погоды."""
    try:
        response = requests.get(f"{BACKEND_URL}/forecast?city={city}&days={days}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при получении прогноза: {response.text}")
            return []
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return []

def get_scraping_logs(city=None, limit=10):
    """Получение логов скрапинга."""
    try:
        url = f"{BACKEND_URL}/scraping_logs"
        params = {"limit": limit}
        if city:
            params["city"] = city
            
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при получении логов скрапинга: {response.text}")
            return []
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return []

def get_data_availability(city):
    """Получение информации о доступности данных."""
    try:
        response = requests.get(f"{BACKEND_URL}/data_availability?city={city}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при получении информации о доступности данных: {response.text}")
            return {"available": False}
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return {"available": False}

# Функция для автодополнения города
def city_autocomplete(input_text, cities_list):
    """Автодополнение для ввода города."""
    if not input_text:
        return []
    
    input_text = input_text.lower()
    return [city for city in cities_list if input_text in city.lower()]

# Основная функция интерфейса
def main():
    st.title("🌤️ Система прогнозирования погоды")
    
    # Получаем список городов для автодополнения
    all_cities = get_cities()
    popular_cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Тверь", "Владивосток", "Сочи", "Калининград", "Мурманск"]
    
    # Если у нас есть города в базе, то используем их для подсказок, иначе используем стандартный список
    if not all_cities:
        cities_for_autocomplete = popular_cities
    else:
        cities_for_autocomplete = list(set(all_cities + popular_cities))
    
    # Боковая панель
    with st.sidebar:
        st.header("Управление")
        
        # Ввод города для скрапинга с автодополнением
        st.subheader("Сбор данных")
        
        # Создаем текстовый ввод с автодополнением
        city_input = st.text_input("Введите название города", "Москва", key="city_input")
        
        # Показываем подсказки, если есть совпадения
        suggestions = city_autocomplete(city_input, cities_for_autocomplete)
        if suggestions and city_input and city_input.lower() != suggestions[0].lower():
            selected_suggestion = st.selectbox(
                "Возможно, вы имели в виду:", 
                suggestions,
                key="city_suggestions"
            )
            if st.button("Использовать это название"):
                city_input = selected_suggestion
                # Обновляем значение в text_input через session_state
                st.session_state['city_input'] = selected_suggestion
        
        # Добавляем выбор промежутка дат
        st.subheader("Период для сбора данных")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Начальная дата", 
                datetime.date.today() - datetime.timedelta(days=9),
                max_value=datetime.date.today()
            )
        with col2:
            end_date = st.date_input(
                "Конечная дата", 
                datetime.date.today(),
                max_value=datetime.date.today()
            )
        
        scrape_button = st.button("Собрать данные о погоде")
        
        if scrape_button:
            if start_date > end_date:
                st.error("Начальная дата не может быть позже конечной даты")
            else:
                # Вывод предупреждения для больших периодов, но не блокируем функциональность
                days_diff = (end_date - start_date).days + 1
                if days_diff > 30:
                    st.warning(f"Запрашиваемый период ({days_diff} дней) довольно большой. Сбор данных может занять продолжительное время.")
                
                with st.spinner("Получение данных о погоде..."):
                    st.info(f"Начинаем сбор данных о погоде для города {city_input} за период с {start_date} по {end_date}. Это может занять некоторое время, так как данные собираются из реальных источников.")
                    
                    # Если период очень большой, добавляем дополнительное сообщение
                    if days_diff > 100:
                        st.info("Для больших периодов данные собираются порциями. Пожалуйста, не закрывайте страницу до завершения процесса.")
                    
                    # Передаем параметр disable_limit=True на бэкенд
                    result = scrape_weather_data(city_input, start_date, end_date)
                    
                    if result and result.get("success"):
                        st.success(f"Успешно собрано {result.get('data_points')} записей для города {result.get('city')}")
                    elif result:
                        st.warning(f"Сбор данных завершен с предупреждениями: {result.get('message', 'Неизвестная ошибка')}")
                    else:
                        st.error("Не удалось собрать данные о погоде. Пожалуйста, попробуйте другой город или период.")
        
        # Выбор города для отображения
        st.subheader("Просмотр данных")
        
        if all_cities:
            selected_city = st.selectbox("Выберите город", all_cities, key="selected_city")
            days_to_show = st.slider("Количество дней для отображения", 1, 30, 7)
        else:
            st.warning("Нет доступных городов. Сначала соберите данные.")
            selected_city = None
            days_to_show = 7
            
        # Обучение модели
        st.subheader("Прогнозирование")
        if selected_city:
            if st.button("Обучить модель"):
                with st.spinner("Обучение модели..."):
                    result = train_model(selected_city)
                    if result and result.get("success"):
                        st.session_state['last_training_metrics'] = result.get("metrics", {})
                        st.success(f"Модель успешно обучена для города {result.get('city')}")
                        
                        # Отображаем метрики в виде чисел
                        metrics = result.get("metrics", {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("RMSE температуры", f"{metrics.get('temp_rmse', 0):.2f} °C")
                            st.metric("RMSE влажности", f"{metrics.get('humidity_rmse', 0):.2f} %")
                            st.metric("RMSE осадков", f"{metrics.get('precip_rmse', 0):.2f} мм")
                        with col2:
                            st.metric("MAE температуры", f"{metrics.get('temp_mae', 0):.2f} °C")
                            st.metric("MAE влажности", f"{metrics.get('humidity_mae', 0):.2f} %")
                            st.metric("MAE осадков", f"{metrics.get('precip_mae', 0):.2f} мм")
                    else:
                        st.error("Не удалось обучить модель. Убедитесь, что для выбранного города собрано достаточно данных (минимум 5 дней).")
            
            forecast_days = st.slider("Дней для прогноза", 1, 10, 5)
    
    # Основное содержимое
    
    # Вкладки
    tab1, tab2, tab3, tab4 = st.tabs(["Исторические данные", "Прогноз", "Метрики модели", "Журнал сбора данных"])
    
    with tab1:
        if selected_city:
            st.header(f"Исторические данные о погоде для города {selected_city}")
            
            # Получение данных
            weather_data = get_weather_data(selected_city, days_to_show)
            
            if weather_data:
                # Создаем DataFrame для отображения в таблице
                df = pd.DataFrame(weather_data)
                df['date'] = pd.to_datetime(df['date']).dt.date
                df = df.sort_values('date', ascending=False)
                
                # Отображаем таблицу
                st.subheader("Таблица данных")
                st.dataframe(
                    df[['date', 'temperature', 'humidity', 'pressure', 'wind_speed', 'precipitation', 'weather_condition']],
                    column_config={
                        "date": "Дата",
                        "temperature": "Температура (°C)",
                        "humidity": "Влажность (%)",
                        "pressure": "Давление (гПа)",
                        "wind_speed": "Скорость ветра (м/с)",
                        "precipitation": "Осадки (мм)",
                        "weather_condition": "Погодные условия"
                    },
                    hide_index=True
                )
                
                # Разделяем графики на две колонки
                col1, col2 = st.columns(2)
                
                with col1:
                    # График температуры
                    temp_fig = plot_temperature(weather_data)
                    if temp_fig:
                        st.plotly_chart(temp_fig, use_container_width=True)
                    
                    # График осадков
                    precip_fig = plot_precipitation(weather_data)
                    if precip_fig:
                        st.plotly_chart(precip_fig, use_container_width=True)
                
                with col2:
                    # График влажности
                    humidity_fig = plot_humidity(weather_data)
                    if humidity_fig:
                        st.plotly_chart(humidity_fig, use_container_width=True)
                    
                    # График погодных условий
                    conditions_fig = plot_weather_conditions(weather_data)
                    if conditions_fig:
                        st.plotly_chart(conditions_fig, use_container_width=True)
                
                # Возможность скачать данные
                st.download_button(
                    label="Скачать данные (CSV)",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f'weather_data_{selected_city}_{datetime.date.today()}.csv',
                    mime='text/csv',
                )
                
                # График доступности данных
                st.subheader("Доступность данных")
                # Используем даты на месяц назад для отображения
                month_ago = datetime.date.today() - datetime.timedelta(days=30)
                availability_fig = plot_data_availability(selected_city, month_ago, datetime.date.today())
                if availability_fig:
                    st.plotly_chart(availability_fig, use_container_width=True)
                    st.info("Зеленым отмечены даты, для которых есть данные о погоде. Красным - даты без данных.")
                else:
                    st.info("Информация о доступности данных не найдена.")
            else:
                st.info("Нет данных для отображения. Пожалуйста, соберите данные для выбранного города.")
        else:
            st.info("Пожалуйста, выберите город в боковой панели.")

    # Вкладка Прогноз
    with tab2:
        if selected_city:
            st.header(f"Прогноз погоды для города {selected_city}")
            
            forecast_data = get_forecast(selected_city, forecast_days)
            
            if forecast_data:
                # Создаем DataFrame для отображения в таблице
                df_forecast = pd.DataFrame(forecast_data)
                df_forecast['date'] = pd.to_datetime(df_forecast['date']).dt.date
                df_forecast = df_forecast.sort_values('date')
                
                # Отображаем таблицу
                st.subheader("Таблица прогноза")
                st.dataframe(
                    df_forecast[['date', 'temperature', 'humidity', 'precipitation', 'weather_condition']],
                    column_config={
                        "date": "Дата",
                        "temperature": "Температура (°C)",
                        "humidity": "Влажность (%)",
                        "precipitation": "Осадки (мм)",
                        "weather_condition": "Погодные условия"
                    },
                    hide_index=True
                )
                
                # Разделяем графики на две колонки
                col1, col2 = st.columns(2)
                
                with col1:
                    # График температуры
                    forecast_temp_fig = plot_temperature(forecast_data)
                    if forecast_temp_fig:
                        st.plotly_chart(forecast_temp_fig, use_container_width=True)
                    
                    # График осадков
                    forecast_precip_fig = plot_precipitation(forecast_data)
                    if forecast_precip_fig:
                        st.plotly_chart(forecast_precip_fig, use_container_width=True)
                
                with col2:
                    # График влажности
                    forecast_humidity_fig = plot_humidity(forecast_data)
                    if forecast_humidity_fig:
                        st.plotly_chart(forecast_humidity_fig, use_container_width=True)
                    
                    # График погодных условий
                    forecast_conditions_fig = plot_weather_conditions(forecast_data)
                    if forecast_conditions_fig:
                        st.plotly_chart(forecast_conditions_fig, use_container_width=True)
                
                # Визуализация сводки прогноза
                st.subheader("Сводка прогноза")
                
                # Создаем карточки для каждого дня прогноза
                cols = st.columns(min(5, len(forecast_data)))
                
                for i, (_, row) in enumerate(df_forecast.iterrows()):
                    if i < len(cols):
                        with cols[i]:
                            st.metric(
                                f"{row['date'].strftime('%d.%m')}",
                                f"{row['temperature']:.1f} °C",
                                f"{row['weather_condition']}"
                            )
                            
                            # Отображаем иконку в зависимости от состояния погоды
                            weather_icons = {
                                "Ясно": "☀️",
                                "Облачно": "🌤️",
                                "Пасмурно": "☁️",
                                "Туман": "🌫️",
                                "Дождь": "🌧️",
                                "Гроза": "⛈️",
                                "Снег": "❄️",
                                "Неизвестно": "❓"
                            }
                            
                            st.markdown(f"<h1 style='text-align: center;'>{weather_icons.get(row['weather_condition'], '❓')}</h1>", unsafe_allow_html=True)
                            st.write(f"Влажность: {row['humidity']:.1f}%")
                            st.write(f"Осадки: {row['precipitation']:.1f} мм")
            else:
                st.warning("Невозможно получить прогноз. Пожалуйста, сначала обучите модель.")
        else:
            st.info("Пожалуйста, выберите город в боковой панели.")

    # Вкладка Метрики модели
    with tab3:
        st.header("Метрики качества модели")
        
        if 'last_training_metrics' in st.session_state and st.session_state['last_training_metrics']:
            metrics = st.session_state['last_training_metrics']
            
            # Отображаем информацию о модели
            st.info(f"""
            ## Информация о модели
            
            **Метрики модели для прогнозирования погоды:**
            - RMSE (Root Mean Squared Error) - квадратный корень из среднеквадратичной ошибки, основной показатель точности прогноза.
            - MAE (Mean Absolute Error) - средняя абсолютная ошибка, показывает среднее отклонение прогноза от реальных значений.
            
            Чем ниже значения метрик, тем точнее модель.
            """)
            
            # Отображаем таблицу метрик
            metrics_df = pd.DataFrame({
                'Параметр': ['Температура', 'Влажность', 'Осадки'],
                'RMSE': [
                    f"{metrics.get('temp_rmse', 0):.2f} °C", 
                    f"{metrics.get('humidity_rmse', 0):.2f} %", 
                    f"{metrics.get('precip_rmse', 0):.2f} мм"
                ],
                'MAE': [
                    f"{metrics.get('temp_mae', 0):.2f} °C", 
                    f"{metrics.get('humidity_mae', 0):.2f} %", 
                    f"{metrics.get('precip_mae', 0):.2f} мм"
                ],
                'R²': [
                    f"{metrics.get('temp_r2', 0):.3f}", 
                    f"{metrics.get('humidity_r2', 0):.3f}", 
                    f"{metrics.get('precip_r2', 0):.3f}"
                ]
            })

            st.table(metrics_df)

            # Добавьте интерпретацию R² к существующей интерпретации результатов
            temp_r2 = metrics.get('temp_r2', 0)
            humidity_r2 = metrics.get('humidity_r2', 0)
            precip_r2 = metrics.get('precip_r2', 0)

            # Функция для интерпретации значения R²
            def interpret_r2(r2_value):
                if r2_value >= 0.9:
                    return "отличной"
                elif r2_value >= 0.7:
                    return "хорошей"
                elif r2_value >= 0.5:
                    return "средней"
                elif r2_value >= 0.3:
                    return "удовлетворительной"
                else:
                    return "низкой"

            temp_r2_quality = interpret_r2(temp_r2)
            humidity_r2_quality = interpret_r2(humidity_r2)
            precip_r2_quality = interpret_r2(precip_r2)

            # Добавьте эту информацию к интерпретации результатов
            st.write(f"""
            ### Качество прогнозов (R²):

            R² показывает, какую долю вариации данных объясняет модель:
            - R² = 1.0: модель идеально описывает данные
            - R² = 0.7: модель объясняет 70% вариации (хорошее качество)
            - R² = 0.5: модель объясняет 50% вариации (среднее качество)
            - R² < 0.3: модель объясняет менее 30% вариации (низкое качество)

            - Температура: модель обладает **{temp_r2_quality}** предсказательной способностью (R² = {temp_r2:.2f}).
            - Влажность: модель обладает **{humidity_r2_quality}** предсказательной способностью (R² = {humidity_r2:.2f}).
            - Осадки: модель обладает **{precip_r2_quality}** предсказательной способностью (R² = {precip_r2:.2f}).

            Для улучшения качества прогнозов рекомендуется собрать больше исторических данных и, возможно, 
            добавить дополнительные признаки, такие как данные о направлении ветра, атмосферном давлении или географическом расположении.
            """)
            
            st.table(metrics_df)
            
            # Визуализация метрик
            metrics_fig = plot_model_metrics(metrics)
            if metrics_fig:
                st.plotly_chart(metrics_fig, use_container_width=True)
                
            # Интерпретация результатов
            st.subheader("Интерпретация результатов")
            
            temp_rmse = metrics.get('temp_rmse', 0)
            humidity_rmse = metrics.get('humidity_rmse', 0)
            precip_rmse = metrics.get('precip_rmse', 0)
            
            temp_quality = "хорошей" if temp_rmse < 2 else "средней" if temp_rmse < 4 else "низкой"
            humidity_quality = "хорошей" if humidity_rmse < 10 else "средней" if humidity_rmse < 20 else "низкой"
            precip_quality = "хорошей" if precip_rmse < 3 else "средней" if precip_rmse < 7 else "низкой"
            
            st.write(f"""
            ### Качество прогнозов:
            
            - Температура: модель обладает **{temp_quality}** точностью. Среднее отклонение прогноза составляет около {metrics.get('temp_mae', 0):.2f}°C.
            - Влажность: модель обладает **{humidity_quality}** точностью. Среднее отклонение прогноза составляет около {metrics.get('humidity_mae', 0):.2f}%.
            - Осадки: модель обладает **{precip_quality}** точностью. Среднее отклонение прогноза составляет около {metrics.get('precip_mae', 0):.2f} мм.
            
            Для улучшения качества прогнозов рекомендуется собрать больше исторических данных.
            """)
        else:
            st.info("Сначала обучите модель, чтобы увидеть метрики качества.")

    # Вкладка Журнал сбора данных
    with tab4:
        st.header("Журнал сбора данных")
        
        # Получаем логи скрапинга
        logs = get_scraping_logs(selected_city, 20) if selected_city else []
        
        if logs:
            # Создаем DataFrame для отображения логов
            logs_df = pd.DataFrame(logs)
            logs_df['created_at'] = pd.to_datetime(logs_df['created_at'])
            logs_df['start_date'] = pd.to_datetime(logs_df['start_date']).dt.date
            logs_df['end_date'] = pd.to_datetime(logs_df['end_date']).dt.date
            logs_df = logs_df.sort_values('created_at', ascending=False)
            
            # Отображаем таблицу логов
            st.dataframe(
                logs_df[['created_at', 'city', 'start_date', 'end_date', 'status', 'message']],
                column_config={
                    "created_at": "Время операции",
                    "city": "Город",
                    "start_date": "Начальная дата",
                    "end_date": "Конечная дата",
                    "status": "Статус",
                    "message": "Сообщение"
                },
                hide_index=True
            )
            
            # Статистика по скрапингу
            st.subheader("Статистика по сбору данных")
            
            # Считаем количество успешных и неуспешных операций
            success_count = logs_df[logs_df['status'] == 'success'].shape[0]
            warning_count = logs_df[logs_df['status'] == 'warning'].shape[0]
            error_count = logs_df[logs_df['status'] == 'error'].shape[0]
            
            # Отображаем статистику в виде метрик
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Успешных операций", success_count)
            with col2:
                st.metric("Операций с предупреждениями", warning_count)
            with col3:
                st.metric("Ошибок", error_count)
        else:
            st.info("Нет данных о сборе погоды. Соберите данные о погоде, чтобы увидеть логи.")

    # Информация о приложении
    with st.expander("О приложении"):
        st.write("""
        ### Система прогнозирования погоды
        
        Это приложение позволяет собирать реальные данные о погоде для различных городов, отображать исторические данные 
        и создавать прогнозы на основе машинного обучения.
        
        **Основные функции:**
        - Сбор реальных данных о погоде для выбранных городов за указанный период
        - Визуализация исторических данных
        - Обучение модели машинного обучения
        - Анализ метрик качества модели
        - Создание прогнозов погоды
        
        Приложение разработано с использованием:
        - FastAPI для бэкенда
        - Streamlit для фронтенда
        - SQLite для хранения данных
        - Scikit-learn для создания модели прогнозирования
        - Beautiful Soup для скрапинга данных о погоде
        """)

if __name__ == "__main__":
    main()



