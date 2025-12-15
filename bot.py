"""
Telegram бот для проверки договоров через YandexGPT
ИСПРАВЛЕНО для Railway
"""

import os
import logging
import tempfile
import requests
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

# ========== ИМПОРТ С ПРОВЕРКОЙ ВЕРСИИ ==========
try:
    # Пробуем импорт для новой версии (20.x)
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
    print("✅ Использую python-telegram-bot 20.x")
    TELEGRAM_VERSION = 20
except ImportError:
    try:
        # Пробуем импорт для старой версии (13.x)
        import telegram
        from telegram import Update
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
        print("✅ Использую python-telegram-bot 13.x")
        TELEGRAM_VERSION = 13
    except ImportError:
        print("❌ Установите: pip install python-telegram-bot==13.15")
        TELEGRAM_VERSION = None

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПРОСТАЯ БАЗА ДАННЫХ ==========
class SimpleDB:
    def __init__(self):
        self.user_data = {}
    
    def get_checks(self, user_id):
        return self.user_data.get(user_id, {}).get('checks', 0)
    
    def add_check(self, user_id, filename=""):
        if user_id not in self.user_data:
            self.user_data[user_id] = {'checks': 0}
        self.user_data[user_id]['checks'] += 1
        return self.user_data[user_id]['checks']

db = SimpleDB()

# ========== YANDEX GPT АНАЛИЗ ==========
class YandexAnalyzer:
    def __init__(self):
        self.api_url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        self.headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def analyze(self, text):
        """Анализ текста договора"""
        if len(text) > 25000:
            text = text[:25000] + "... [текст сокращен]"
        
        prompt = f"""Ты опытный юрист. Проанализируй договор и выдели:

1. ГЛАВНЫЕ РИСКИ (высокий/средний/низкий)
2. НЕПОНЯТНЫЕ МОМЕНТЫ
3. ЧТО ЛУЧШЕ ИЗМЕНИТЬ
4. ВОПРОСЫ К КОНТРАГЕНТУ

Договор:
{text}

Ответь кратко и по делу. Указывай конкретные пункты."""
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "generationOptions": {"maxTokens": 1500, "temperature": 0.1}
        }
        
        try:
            response = requests.post(self.api_url, json=data, headers=self.headers, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                
                # Разные варианты извлечения ответа
                if isinstance(result, dict):
                    if 'message' in result and 'content' in result['message']:
                        return result['message']['content']
                    elif 'choices' in result and result['choices']:
                        choice = result['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            return choice['message']['content']
                    elif 'text' in result:
                        return result['text']
                
                # Если структура незнакомая
                import json
                return f"Ответ ИИ:\n{json.dumps(result, ensure_ascii=False, indent=2)[:2000]}"
                
            else:
                return f"⚠️ Ошибка API ({response.status_code})\nПопробуйте позже."
                
        except requests.exceptions.Timeout:
            return "⏱️ Время ожидания истекло. Попробуйте отправить текст покороче."
        except Exception as e:
            return f"❌ Ошибка: {str(e)[:200]}"

# ========== ФУНКЦИИ ДЛЯ ВЕРСИИ 13.x ==========
if TELEGRAM_VERSION == 13:
    def start_13(update, context):
        user = update.effective_user
        checks = db.get_checks(user.id)
        
        text = f"""👋 Привет, {user.first_name}!

Я бот для проверки договоров.
Просто отправь текст договора.

📊 Проверок: {checks}/{FREE_CHECKS}
💸 После: {PRICE_PER_CHECK}₽ за проверку

Отправь текст договора сообщением."""
        
        update.message.reply_text(text)
    
    def help_13(update, context):
        text = """📖 Помощь:

1. Отправьте текст договора
2. Получите анализ рисков
3. Используйте в переговорах

💰 Цена: 69₽ за проверку (первая бесплатно)
⚠️ Не заменяет юриста!"""
        
        update.message.reply_text(text)
    
    def handle_text_13(update, context):
        user = update.effective_user
        text = update.message.text
        
        if text.startswith('/'):
            return
        
        checks = db.get_checks(user.id)
        if checks >= FREE_CHECKS:
            update.message.reply_text(
                f"❌ Бесплатные проверки закончились.\n"
                f"Оплатите {PRICE_PER_CHECK}₽ на карту:\n"
                f"2200 1234 5678 9012\n"
                f"В комментарии: ID:{user.id}"
            )
            return
        
        msg = update.message.reply_text("🤖 Анализирую...")
        
        analyzer = YandexAnalyzer()
        result = analyzer.analyze(text)
        
        db.add_check(user.id)
        
        response = f"""📋 Результат анализа:

{result[:2500]}

✅ Проверок: {checks + 1}/{FREE_CHECKS}"""
        
        msg.edit_text(response)
    
    def main_13():
        """Запуск для версии 13.x"""
        updater = Updater(BOT_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start_13))
        dp.add_handler(CommandHandler("help", help_13))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_13))
        
        print("=" * 50)
        print("🤖 Бот запущен (версия 13.x)")
        print(f"💰 Цена: {PRICE_PER_CHECK}₽")
        print(f"🎁 Бесплатных: {FREE_CHECKS}")
        print("=" * 50)
        
        updater.start_polling()
        updater.idle()

# ========== ФУНКЦИИ ДЛЯ ВЕРСИИ 20.x ==========
elif TELEGRAM_VERSION == 20:
    async def start_20(update: Update, context: CallbackContext):
        user = update.effective_user
        checks = db.get_checks(user.id)
        
        text = f"""👋 Привет, {user.first_name}!

Я бот для проверки договоров.
Просто отправь текст договора.

📊 Проверок: {checks}/{FREE_CHECKS}
💸 После: {PRICE_PER_CHECK}₽ за проверку

Отправь текст договора сообщением."""
        
        await update.message.reply_text(text)
    
    async def help_20(update: Update, context: CallbackContext):
        text = """📖 Помощь:

1. Отправьте текст договора
2. Получите анализ рисков
3. Используйте в переговорах

💰 Цена: 69₽ за проверку (первая бесплатно)
⚠️ Не заменяет юриста!"""
        
        await update.message.reply_text(text)
    
    async def handle_text_20(update: Update, context: CallbackContext):
        user = update.effective_user
        text = update.message.text
        
        if text.startswith('/'):
            return
        
        checks = db.get_checks(user.id)
        if checks >= FREE_CHECKS:
            await update.message.reply_text(
                f"❌ Бесплатные проверки закончились.\n"
                f"Оплатите {PRICE_PER_CHECK}₽ на карту:\n"
                f"2200 1234 5678 9012\n"
                f"В комментарии: ID:{user.id}"
            )
            return
        
        msg = await update.message.reply_text("🤖 Анализирую...")
        
        analyzer = YandexAnalyzer()
        result = analyzer.analyze(text)
        
        db.add_check(user.id)
        
        response = f"""📋 Результат анализа:

{result[:2500]}

✅ Проверок: {checks + 1}/{FREE_CHECKS}"""
        
        await msg.edit_text(response)
    
    def main_20():
        """Запуск для версии 20.x"""
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start_20))
        app.add_handler(CommandHandler("help", help_20))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_20))
        
        print("=" * 50)
        print("🤖 Бот запущен (версия 20.x)")
        print(f"💰 Цена: {PRICE_PER_CHECK}₽")
        print(f"🎁 Бесплатных: {FREE_CHECKS}")
        print("=" * 50)
        
        app.run_polling()

# ========== ОСНОВНОЙ ЗАПУСК ==========
def main():
    """Определяем версию и запускаем"""
    if TELEGRAM_VERSION == 13:
        main_13()
    elif TELEGRAM_VERSION == 20:
        main_20()
    else:
        print("❌ Установите библиотеку:")
        print("pip install python-telegram-bot==13.15")
        print("или")
        print("pip install python-telegram-bot")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Проверяем Railway переменные
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        print("🚂 Railway обнаружен")
        # Используем токен из Railway если есть
        rail_token = os.environ.get("BOT_TOKEN")
        if rail_token:
            BOT_TOKEN = rail_token
            print("✅ Токен взят из Railway")
    
    # Проверяем ключи
    if not all([BOT_TOKEN, YC_API_KEY, YC_FOLDER_ID, YC_AGENT_ID]):
        print("❌ Не все ключи заполнены!")
        print("Проверьте: BOT_TOKEN, YC_API_KEY, YC_FOLDER_ID, YC_AGENT_ID")
        exit(1)
    
    # Проверяем подключение к Яндекс
    print("🔗 Проверяю подключение к Яндекс GPT...")
    analyzer = YandexAnalyzer()
    test_result = analyzer.analyze("Тестовый запрос")
    if "Ошибка" in test_result or "⚠️" in test_result:
        print(f"❌ Яндекс GPT: {test_result[:100]}")
    else:
        print("✅ Яндекс GPT подключен")
    
    # Запускаем бота
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("Попробуйте другую версию библиотеки")
        exit(1)
