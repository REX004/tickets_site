# Используем базовый образ с Python
FROM python:3.11-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y libzbar0 libzbar-dev gcc

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Открываем порт для Railway
EXPOSE 5000

# Команда запуска
CMD ["python3", "app.py"]
