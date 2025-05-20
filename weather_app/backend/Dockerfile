FROM python:3.11-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./app ./app

# Создаем символическую ссылку для разрешения импортов
RUN ln -s /app /usr/local/lib/python3.11/site-packages/backend

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]