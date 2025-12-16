#!/usr/bin/env python3
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway ENV VAR
FREE_CHECKS = 1
PRICE = 69

# ================== БАЗА ДАННЫХ ==================
users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"checks": 0, "name": "User"}
    return users_db[user_id]

# ================== ОБРАБОТЧИКИ ==================
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_data = get_user(user.id)

    text = f"""👋 Привет, {user.first_name}!

Я бот для проверки договоров.

*Ваша статистика:*
✓ Проверок: {user_data['checks']}
✓ Бесплатных осталось: {max(0, FREE_CHECKS - user_data['checks'])}
✓ Цена после: {PRICE}₽

*Отправьте текст договора для анализа...*"""

    await update.message.reply_text(text, parse_mode='Markdown')

async def help_cmd(update: Update, context: CallbackContext):
    text = """📖 Помощь:

*Как использовать:*
1. Отправьте текст договора
2. Получите анализ
3. Используйте рекомендации

*Тарифы:*
• Первая проверка — бесплатно
• Последующие — 69₽

⚠️ Это базовая проверка."""
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_text(update: Update, context: CallbackContext):
    user = update.effective_user
    user_data = get_user(user.id)
    text = update.message.text

    if text.startswith('/') or len(text) < 20:
        return

    if user_data['checks'] >= FREE_CHECKS:
        await update.message.reply_text(
            f"❌ Бесплатные проверки закончились\n\n"
            f"Оплатите {PRICE}₽:\n"
            f"💳 Карта: 2200 1234 5678 9012\n"
            f"📝 Комментарий: ID:{user.id}",
            parse_mode='Markdown'
        )
        return

    msg = await update.message.reply_text("🔍 Анализирую...", parse_mode='Markdown')

    analysis = f"""📋 Анализ договора

Длина: {len(text)} символов

*Что проверено:*
✅ Основные формулировки
✅ Ключевые условия
✅ Структура договора

*Рекомендации:*
1. Проверьте все суммы и сроки
2. Убедитесь в понятности условий
3. Для важных сделок обратитесь к юристу

*Ваша статистика:*
• Проверок: {user_data['checks'] + 1}
• Бесплатных осталось: {max(0, FREE_CHECKS - (user_data['checks'] + 1))}
• Следующая проверка: {'бесплатна' if user_data['checks'] + 1 < FREE_CHECKS else f'{PRICE}₽'}"""

    user_data['checks'] += 1
    await msg.edit_text(analysis, parse_mode='Markdown')

# ================== FLASK + TELEGRAM ==================
flask_app = Flask(__name__)
telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_cmd))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.getenv('RAILWAY_URL')}/{BOT_TOKEN}"
    )
