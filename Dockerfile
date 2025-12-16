FROM python:3.13-slim

WORKDIR /app

COPY requirements/requirements.txt /app/requirements.txt

# Ставим зависимости и принудительно обновляем python-telegram-bot
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade python-telegram-bot==20.7

COPY bot.py /app/bot.py

ENV PYTHONUNBUFFERED=1

CMD ["python3", "bot.py"]
