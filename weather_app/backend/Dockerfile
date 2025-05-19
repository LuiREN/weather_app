FROM python:3.11-slim

# Установка необходимых системных пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY ./app ./app

# Запуск приложения
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]