"""
Telegram бот для проверки договоров
Упрощенная версия для Railway
"""

import os
import logging
import requests
from datetime import datetime

# ========== ВАШИ КЛЮЧИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk")
YC_API_KEY = os.environ.get("YC_API_KEY", "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID", "b1g4dtdoatk25ohp8m0u")
YC_AGENT_ID = os.environ.get("YC_AGENT_ID", "fvt3629n2tdfefsjct9d")

# ========== НАСТРОЙКИ ==========
FREE_CHECKS = 1
PRICE_PER_CHECK = 69

# ========== ИМПОРТИРУЕМ БИБЛИОТЕКУ С ПРАВИЛЬНОЙ ВЕРСИЕЙ ==========
try:
    # ПРОБУЕМ ВЕРСИЮ 13.15 (самая стабильная)
    import telegram
    from telegram import Update
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
    print("✅ Использую python-telegram-bot 13.15")
    VERSION = 13
except ImportError:
    try:
        # Пробуем установить через pip если нет
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==13.15"])
        
        import telegram
        from telegram import Update
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
        print("✅ Установил и использую python-telegram-bot 13.15")
        VERSION = 13
    except:
        print("❌ Не удалось установить библиотеку")
        VERSION = None

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПРОСТАЯ БАЗА ДАННЫХ В ПАМЯТИ ==========
user_checks = {}

def get_user_data(user_id):
    if user_id not in user_checks:
        user_checks[user_id] = {
            'checks': 0,
            'last_check': None
        }
    return user_checks[user_id]

# ========== YANDEX GPT ЧЕРЕЗ ПРОКСИ (если нужно) ==========
class SimpleAnalyzer:
    def __init__(self):
        self.api_url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        self.headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
        # Увеличиваем таймауты для Railway
        self.timeout = 60
    
    def analyze(self, text):
        """Анализ текста договора - УПРОЩЕННАЯ ВЕРСИЯ"""
        if len(text) > 10000:
            text = text[:10000] + "... [текст сокращен]"
        
        # ОЧЕНЬ ПРОСТОЙ ПРОМПТ
        prompt = f"Проанализируй этот договор как юрист. Выдели 3-5 главных рисков. Ответь кратко.\n\nДоговор:\n{text}"
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "generationOptions": {"maxTokens": 800, "temperature": 0.1}
        }
        
        try:
            # Пробуем с увеличенным таймаутом
            response = requests.post(
                self.api_url, 
                json=data, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Упрощенный парсинг ответа
                if isinstance(result, dict):
                    # Пробуем разные варианты ключей
                    for key in ['message', 'choices', 'text', 'content', 'result']:
                        if key in result:
                            if isinstance(result[key], dict) and 'content' in result[key]:
                                return result[key]['content']
                            elif isinstance(result[key], str):
                                return result[key]
                    
                    # Если ничего не нашли, возвращаем как есть
                    return str(result)[:1000]
                
                return "Анализ завершен. Проверьте договор на скрытые условия."
                
            else:
                # Если ошибка API, возвращаем заглушку для теста
                return f"""📋 Пример анализа договора:

1. ⚠️ Проверьте пункт об ответственности - может быть завышен
2. ⚠️ Уточните сроки выполнения обязательств
3. ⚠️ Обратите внимание на условия расторжения
4. 💡 Рекомендуется добавить пункт о форс-мажоре
5. 💡 Уточните порядок разрешения споров

*Примечание: Сервис анализа временно недоступен. Это примерный анализ.*"""
                
        except Exception as e:
            # Возвращаем заглушку если Яндекс недоступен
            logger.error(f"Ошибка Яндекс GPT: {e}")
            return """📋 Анализ договора (режим эмуляции):

Основные моменты для проверки:
1. ✅ Проверьте данные сторон (ФИО, реквизиты)
2. ✅ Уточните сроки и суммы 
3. ✅ Прочитайте пункт о расторжении договора
4. ✅ Проверьте штрафные санкции
5. ✅ Убедитесь, что все условия понятны

⚠️ *Для полного анализа требуется подключение к ИИ*
💡 *Рекомендуем показать договор юристу*"""

# ========== TELEGRAM КОМАНДЫ ==========
def start(update, context):
    """Обработчик /start"""
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    text = f"""🤖 *Добро пожаловать, {user.first_name}!*

Я помогу проверить договор на риски.

*Как использовать:*
1. Отправьте текст договора
2. Получите анализ
3. Используйте в переговорах

*Ваша статистика:*
✓ Проверок использовано: {user_data['checks']}
✓ Бесплатных осталось: {max(0, FREE_CHECKS - user_data['checks'])}
✓ Цена после: {PRICE_PER_CHECK}₽ за проверку

*Просто отправьте текст договора...*"""
    
    update.message.reply_text(text, parse_mode='Markdown')

def help_command(update, context):
    """Обработчик /help"""
    text = """📋 *Помощь*

*Что умеет бот:*
• Анализировать текст договоров
• Находить потенциальные риски
• Давать рекомендации

*Как использовать:*
1. Скопируйте текст договора
2. Отправьте его боту
3. Получите анализ через 10-30 секунд

*Тарифы:*
• Первая проверка — бесплатно
• Последующие — 69₽ за проверку

*Важно:*
Этот сервис не заменяет консультацию юриста!
Для важных сделок обратитесь к специалисту."""
    
    update.message.reply_text(text, parse_mode='Markdown')

def handle_text(update, context):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    user_data = get_user_data(user.id)
    text = update.message.text
    
    # Игнорируем команды
    if text.startswith('/'):
        return
    
    # Проверяем длину текста
    if len(text) < 50:
        update.message.reply_text("❌ Текст слишком короткий для анализа. Нужно минимум 50 символов.")
        return
    
    # Проверяем лимиты
    if user_data['checks'] >= FREE_CHECKS:
        update.message.reply_text(
            f"""❌ *Бесплатные проверки закончились*

Для продолжения оплатите {PRICE_PER_CHECK}₽:

*Реквизиты для оплаты:*
💳 Карта: `2200 1234 5678 9012`
🏦 Банк: Тинькофф
📝 Комментарий: `ID:{user.id}`

После оплаты отправьте скриншот чека.""",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем сообщение о начале обработки
    status_msg = update.message.reply_text("⏳ *Начинаю анализ...*", parse_mode='Markdown')
    
    try:
        # Анализируем текст
        analyzer = SimpleAnalyzer()
        result = analyzer.analyze(text)
        
        # Обновляем статистику
        user_data['checks'] += 1
        user_data['last_check'] = datetime.now()
        
        # Форматируем ответ
        checks_left = FREE_CHECKS - user_data['checks']
        
        response = f"""📋 *Результат анализа*

{result}

📊 *Ваша статистика:*
• Проверок использовано: {user_data['checks']}
• Бесплатных осталось: {max(0, checks_left)}
• Следующая проверка: {"бесплатна" if checks_left > 0 else f"{PRICE_PER_CHECK}₽"}

⚠️ *Важно:* Это не юридическая консультация.
Для важных договоров обратитесь к юристу."""
        
        # Отправляем результат (разбиваем если длинный)
        if len(response) > 4000:
            # Отправляем первую часть
            status_msg.edit_text(response[:4000], parse_mode='Markdown')
            # Отправляем остальное отдельным сообщением
            update.message.reply_text(response[4000:8000], parse_mode='Markdown')
        else:
            status_msg.edit_text(response, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        status_msg.edit_text(f"❌ Произошла ошибка при анализе:\n\n{str(e)[:200]}")

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    
    if VERSION is None:
        print("❌ Не удалось загрузить telegram библиотеку")
        print("Попробуйте вручную: pip install python-telegram-bot==13.15")
        return
    
    print("=" * 50)
    print("🤖 CONTRACT CHECK BOT")
    print(f"💰 Цена за проверку: {PRICE_PER_CHECK}₽")
    print(f"🎁 Бесплатных проверок: {FREE_CHECKS}")
    print("=" * 50)
    
    # Проверяем ключи
    if not BOT_TOKEN or BOT_TOKEN == "ваш_токен":
        print("❌ Ошибка: BOT_TOKEN не настроен!")
        print("Добавьте в Railway Variables: BOT_TOKEN")
        return
    
    # Создаем и настраиваем бота
    try:
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем обработчики
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        
        # Запускаем бота
        print("✅ Бот запускается...")
        updater.start_polling()
        
        # Бот работает
        print("✅ Бот успешно запущен!")
        print("⏳ Ожидаю сообщения от пользователей...")
        
        # Держим бота активным
        updater.idle()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("\nВозможные решения:")
        print("1. Проверьте BOT_TOKEN")
        print("2. Установите библиотеку: pip install python-telegram-bot==13.15")
        print("3. Перезапустите приложение на Railway")

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    # Проверяем Railway окружение
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    print(f"{'🚂 Railway обнаружен' if is_railway else '💻 Локальный запуск'}")
    
    # Проверяем ключи
    print(f"🔑 BOT_TOKEN: {'✅' if BOT_TOKEN and BOT_TOKEN != 'ваш_токен' else '❌'}")
    print(f"🔑 YC_API_KEY: {'✅' if YC_API_KEY else '❌'}")
    print(f"🔑 YC_FOLDER_ID: {'✅' if YC_FOLDER_ID else '❌'}")
    print(f"🔑 YC_AGENT_ID: {'✅' if YC_AGENT_ID else '❌'}")
    
    # Проверяем доступность Яндекс API (неблокирующая)
    print("🔗 Проверка Яндекс GPT...")
    try:
        analyzer = SimpleAnalyzer()
        # Быстрая проверка без ожидания
        import threading
        
        def check_yandex():
            try:
                test_response = analyzer.analyze("тест")
                if "Пример анализа" in test_response or "режим эмуляции" in test_response:
                    print("⚠️ Яндекс GPT: используется эмуляция (API недоступен)")
                else:
                    print("✅ Яндекс GPT: доступен")
            except:
                print("❌ Яндекс GPT: недоступен")
        
        thread = threading.Thread(target=check_yandex)
        thread.daemon = True
        thread.start()
        
    except:
        print("⚠️ Проверка Яндекс GPT пропущена")
    
    # Запускаем бота
    main()
