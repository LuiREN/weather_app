FROM python:3.11-slim

# ������������� ����������� �����������
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ������� ������� ����������
WORKDIR /app

# �������� ���� ������������
COPY requirements.txt .

# ������������� �����������
RUN pip install --no-cache-dir -r requirements.txt

# �������� ��� ����������
COPY ./app ./app

# ������� ������������� ������ ��� ���������� ��������
RUN ln -s /app /usr/local/lib/python3.11/site-packages/backend

# ��������� ����
EXPOSE 8000

# ��������� ����������
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]