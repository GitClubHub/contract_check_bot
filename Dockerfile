# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements
COPY requirements/requirements.txt /app/requirements.txt

# Обновляем pip и ставим зависимости
RUN pip install --upgrade pip \
    && pip uninstall -y python-telegram-bot || true \
    && pip install -r requirements.txt

# Копируем основной код
COPY bot.py /app/bot.py

# Указываем переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python3", "bot.py"]
