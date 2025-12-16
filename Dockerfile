FROM python:3.13-slim

WORKDIR /app

COPY requirements/requirements.txt /app/requirements.txt

# Удаляем все следы старого PTB и ставим заново
RUN pip install --upgrade pip \
    && pip uninstall -y python-telegram-bot telegram || true \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade python-telegram-bot==20.7

COPY bot.py /app/bot.py

ENV PYTHONUNBUFFERED=1

CMD ["python3", "bot.py"]
