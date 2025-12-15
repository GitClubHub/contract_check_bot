"""
Telegram бот для проверки договоров
ВСЁ В ОДНОМ ФАЙЛЕ - для Railway
"""

import os
import logging
import tempfile
import requests
import sqlite3
import asyncio
from datetime import datetime

# ========== ВАШИ КЛЮЧИ ==========
BOT_TOKEN = "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk"
YC_API_KEY = "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln"
YC_FOLDER_ID = "b1g4dtdoatk25ohp8m0u"
YC_AGENT_ID = "fvt3629n2tdfefsjct9d"

# ========== НАСТРОЙКИ ==========
FREE_CHECKS = 1
PRICE_PER_CHECK = 69
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

# ========== TELEGRAM ИМПОРТ ==========
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
    TELEGRAM_OK = True
except ImportError:
    TELEGRAM_OK = False
    print("⚠️ Установите: pip install python-telegram-bot")

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== БАЗА ДАННЫХ (В ПАМЯТИ ДЛЯ RAILWAY) ==========
user_checks = {}  # {user_id: checks_count}

def get_checks(user_id):
    """Получить количество проверок пользователя"""
    return user_checks.get(user_id, 0)

def add_check(user_id):
    """Добавить проверку"""
    user_checks[user_id] = user_checks.get(user_id, 0) + 1

# ========== YANDEX GPT АНАЛИЗ ==========
class SimpleAnalyzer:
    def __init__(self):
        self.api_url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        self.headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def analyze(self, text):
        """Простой анализ текста"""
        if len(text) > 30000:
            text = text[:30000] + "... [текст сокращен]"
        
        prompt = f"""Проанализируй этот договор как юрист. Ответь кратко по пунктам:

1. ОСНОВНЫЕ РИСКИ (высокий/средний/низкий)
2. ЧТО НЕЯСНО ИЛИ ДВУСМЫСЛЕННО
3. ЧТО РЕКОМЕНДУЕШЬ ИЗМЕНИТЬ
4. КАКИЕ ВОПРОСЫ ЗАДАТЬ ВТОРОЙ СТОРОНЕ

Договор: {text}"""
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "generationOptions": {"maxTokens": 1000, "temperature": 0.1}
        }
        
        try:
            response = requests.post(self.api_url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Пробуем разные форматы ответа
                if isinstance(result, dict):
                    if 'message' in result and 'content' in result['message']:
                        return result['message']['content']
                    elif 'choices' in result and result['choices']:
                        return result['choices'][0].get('message', {}).get('content', 'Нет ответа')
                    elif 'content' in result:
                        return result['content']
                
                return str(result)[:2000]
            else:
                return f"Ошибка API ({response.status_code}): {response.text[:200]}"
                
        except Exception as e:
            return f"Ошибка: {str(e)}"

# ========== ОБРАБОТКА ТЕКСТА ИЗ ФАЙЛОВ ==========
def read_text_file(file_path):
    """Чтение текстовых файлов"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(file_path, 'r', encoding='cp1251') as f:
                return f.read()
        except Exception as e:
            return f"Ошибка чтения: {str(e)}"

# ========== TELEGRAM КОМАНДЫ ==========
async def start(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    checks = get_checks(user.id)
    
    text = f"""👋 Привет, {user.first_name}!

Я бот для проверки договоров.
Отправь мне текст договора или файл (.txt).

📊 Проверок использовано: {checks}
🎁 Бесплатных осталось: {FREE_CHECKS - checks}
💸 После: {PRICE_PER_CHECK}₽ за проверку

Просто отправь текст договора или файл .txt"""
    
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: CallbackContext):
    """Команда /help"""
    text = """📖 Помощь:

1. Отправьте текст договора сообщением
2. Или отправьте файл .txt с договором
3. Получите анализ рисков

⚠️ Пока поддерживается только текст
💸 Цена: 69₽ за проверку (первая бесплатно)"""
    
    await update.message.reply_text(text)

async def handle_text(update: Update, context: CallbackContext):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    text = update.message.text
    
    if text.startswith('/'):
        return
    
    # Проверка лимитов
    checks = get_checks(user.id)
    if checks >= FREE_CHECKS:
        await update.message.reply_text(
            f"❌ Бесплатные проверки закончились.\n"
            f"Оплатите {PRICE_PER_CHECK}₽ на карту: 2200 1234 5678 9012\n"
            f"В комментарии: ID:{user.id}"
        )
        return
    
    # Анализ
    msg = await update.message.reply_text("🤖 Анализирую...")
    
    analyzer = SimpleAnalyzer()
    result = analyzer.analyze(text)
    
    # Сохраняем
    add_check(user.id)
    
    # Отправляем результат
    response = f"""📋 Результат анализа:

{result[:3000]}

✅ Проверок использовано: {checks + 1}
🎁 Бесплатных осталось: {FREE_CHECKS - (checks + 1)}"""
    
    await msg.edit_text(response)

async def handle_document(update: Update, context: CallbackContext):
    """Обработка документов (только .txt)"""
    user = update.effective_user
    document = update.message.document
    
    # Проверка лимитов
    checks = get_checks(user.id)
    if checks >= FREE_CHECKS:
        await update.message.reply_text(
            f"❌ Бесплатные проверки закончились.\n"
            f"Оплатите {PRICE_PER_CHECK}₽ на карту: 2200 1234 5678 9012\n"
            f"В комментарии: ID:{user.id}"
        )
        return
    
    # Проверка размера
    if document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text("❌ Файл слишком большой (макс 15MB)")
        return
    
    # Проверка формата
    file_name = document.file_name or "document.txt"
    if not file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ Поддерживаются только .txt файлы")
        return
    
    msg = await update.message.reply_text("📥 Загружаю файл...")
    
    try:
        # Скачиваем
        file = await document.get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as tmp:
            tmp_path = tmp.name
        
        await file.download_to_drive(tmp_path)
        
        # Читаем
        await msg.edit_text("📖 Читаю текст...")
        text = read_text_file(tmp_path)
        
        if len(text) < 50:
            await msg.edit_text("❌ Файл слишком короткий или пустой")
            return
        
        # Анализируем
        await msg.edit_text("🤖 Анализирую...")
        analyzer = SimpleAnalyzer()
        result = analyzer.analyze(text)
        
        # Сохраняем
        add_check(user.id)
        
        # Отправляем результат
        response = f"""📋 Анализ файла: {file_name}

{result[:3000]}

✅ Проверок использовано: {checks + 1}
🎁 Бесплатных осталось: {FREE_CHECKS - (checks + 1)}"""
        
        await msg.edit_text(response)
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")
    finally:
        # Удаляем временный файл
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    
    if not TELEGRAM_OK:
        print("❌ Установите python-telegram-bot:")
        print("pip install python-telegram-bot")
        return
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Запускаем
    print("=" * 50)
    print("🤖 Contract Check Bot запущен!")
    print(f"💰 Цена за проверку: {PRICE_PER_CHECK}₽")
    print(f"🎁 Бесплатных: {FREE_CHECKS}")
    print("=" * 50)
    
    app.run_polling(allowed_updates="all")

# ========== ДЛЯ RAILWAY ==========
if __name__ == "__main__":
    # Проверяем переменные окружения Railway
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        print("🚂 Запуск на Railway...")
        
        # Railway может передать токен через переменные
        railway_token = os.environ.get("BOT_TOKEN")
        if railway_token and railway_token != BOT_TOKEN:
            BOT_TOKEN = railway_token
            print("✅ Использую токен из Railway")
    
    # Запускаем бота
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        # Перезапуск через 5 секунд
        import time
        time.sleep(5)
        main()
