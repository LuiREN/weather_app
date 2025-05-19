import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import json
from typing import List, Dict, Any

# URL бэкенда
BACKEND_URL = "http://backend:8000"

# Настройка страницы
st.set_page_config(
    page_title="Прогноз погоды",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def scrape_weather_data(city):
    """Запуск скрапинга данных о погоде."""
    try:
        response = requests.post(f"{BACKEND_URL}/scrape?city={city}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка при скрапинге данных: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка соединения с сервером: {str(e)}")
        return None

def get_weather_data(city=None, days=7):
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

# Функции для визуализации

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
        "Гроза": 6
    }
    
    df['condition_code'] = df['weather_condition'].map(condition_map)
    
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

# Интерфейс приложения

def main():
    st.title("🌤️ Система прогнозирования погоды")
    
    # Боковая панель
    with st.sidebar:
        st.header("Управление")
        
        # Ввод города для скрапинга
        st.subheader("Сбор данных")
        city_input = st.text_input("Введите название города", "Москва")
        
        if st.button("Собрать данные о погоде"):
            with st.spinner("Получение данных..."):
                result = scrape_weather_data(city_input)
                if result and result.get("success"):
                    st.success(f"Успешно собрано {result.get('data_points')} записей для города {result.get('city')}")
        
        # Выбор города для отображения
        st.subheader("Просмотр данных")
        cities = get_cities()
        if cities:
            selected_city = st.selectbox("Выберите город", cities)
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
                        st.success(f"Модель успешно обучена для города {result.get('city')}")
                        st.write("Метрики:")
                        metrics = result.get("metrics", {})
                        st.metric("RMSE температуры", f"{metrics.get('temp_rmse', 0):.2f} °C")
                        st.metric("RMSE влажности", f"{metrics.get('humidity_rmse', 0):.2f} %")
                        st.metric("RMSE осадков", f"{metrics.get('precip_rmse', 0):.2f} мм")
        
            forecast_days = st.slider("Дней для прогноза", 1, 10, 5)
    
    # Основное содержимое
    
    # Вкладки
    tab1, tab2 = st.tabs(["Исторические данные", "Прогноз"])
    
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
            else:
                st.info("Нет данных для отображения. Пожалуйста, соберите данные для выбранного города.")
        else:
            st.info("Пожалуйста, выберите город в боковой панели.")
    
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
                                "Гроза": "⛈️"
                            }
                            
                            st.markdown(f"<h1 style='text-align: center;'>{weather_icons.get(row['weather_condition'], '❓')}</h1>", unsafe_allow_html=True)
                            st.write(f"Влажность: {row['humidity']:.1f}%")
                            st.write(f"Осадки: {row['precipitation']:.1f} мм")
            else:
                st.warning("Невозможно получить прогноз. Пожалуйста, сначала обучите модель.")
        else:
            st.info("Пожалуйста, выберите город в боковой панели.")

    # Информация о приложении
    with st.expander("О приложении"):
        st.write("""
        ### Система прогнозирования погоды
        
        Это приложение позволяет собирать данные о погоде для различных городов, отображать исторические данные 
        и создавать прогнозы на основе машинного обучения.
        
        **Основные функции:**
        - Сбор данных о погоде для выбранных городов
        - Визуализация исторических данных
        - Обучение модели машинного обучения
        - Создание прогнозов погоды
        
        Приложение разработано с использованием:
        - FastAPI для бэкенда
        - Streamlit для фронтенда
        - SQLite для хранения данных
        - Scikit-learn для создания модели прогнозирования
        """)

if __name__ == "__main__":
    main()
