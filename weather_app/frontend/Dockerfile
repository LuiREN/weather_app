FROM python:3.11-slim

# Установка необходимых системных пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app.py .

# Открытие порта
EXPOSE 8501

# Проверка здоровья приложения
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Запуск приложения
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]