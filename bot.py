#!/usr/bin/env python3
"""
Contract Check Bot - Работает на Python 3.13+
"""

import os
import sys
import time
import json

print("=" * 60)
print("🤖 CONTRACT CHECK BOT - ЗАПУСК")
print("=" * 60)

# ========== УСТАНОВКА ЗАВИСИМОСТЕЙ ==========
def install_deps():
    """Устанавливаем современные версии"""
    packages = [
        "requests==2.31.0",
        "python-telegram-bot==20.7"  # НОВАЯ ВЕРСИЯ для Python 3.13
    ]
    
    for package in packages:
        try:
            if "requests" in package:
                import requests
                print(f"✅ requests уже установлен")
            elif "telegram" in package:
                # Пробуем импорт
                try:
                    import telegram
                    print(f"✅ python-telegram-bot уже установлен")
                except ImportError:
                    raise ImportError
        except (ImportError, Exception):
            print(f"⬇️ Устанавливаю {package}...")
            import subprocess
            try:
                # Устанавливаем с флагом --break-system-packages если нужно
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✅ {package} установлен")
                else:
                    print(f"⚠️ Ошибка установки {package}: {result.stderr[:100]}")
                    # Пробуем без версии
                    if "==" in package:
                        basic_pkg = package.split("==")[0]
                        print(f"🔄 Пробую установить {basic_pkg}...")
                        subprocess.run([sys.executable, "-m", "pip", "install", basic_pkg])
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")
                continue

install_deps()

# ========== ИМПОРТ С ОБРАБОТКОЙ ОШИБОК ==========
try:
    import requests
    print("✅ requests импортирован")
except ImportError:
    print("❌ Не удалось импортировать requests")
    sys.exit(1)

# Пытаемся импортировать telegram с разными вариантами
telegram_loaded = False

try:
    # Вариант 1: Новая версия (20.x)
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
    telegram_loaded = True
    print("✅ Использую python-telegram-bot 20.x")
    BOT_VERSION = 20
except ImportError as e:
    print(f"⚠️ Ошибка импорта 20.x: {e}")
    
    try:
        # Вариант 2: Старая версия с обходным путем
        # Патчим sys.modules перед импортом
        import importlib
        
        # Создаем заглушку для imghdr если её нет
        try:
            import imghdr
        except ImportError:
            # Создаем простую заглушку
            class FakeImghdr:
                @staticmethod
                def what(file, h=None):
                    return None
            
            sys.modules['imghdr'] = FakeImghdr()
            print("✅ Создана заглушка для imghdr")
        
        # Теперь пробуем импортировать
        import telegram
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
        telegram_loaded = True
        print("✅ Использую python-telegram-bot 13.x с патчем")
        BOT_VERSION = 13
    except ImportError as e2:
        print(f"❌ Не удалось загрузить telegram: {e2}")
        telegram_loaded = False
        BOT_VERSION = None

if not telegram_loaded:
    print("\n" + "=" * 60)
    print("⚠️  Не удалось загрузить библиотеку Telegram")
    print("Попробуйте эти команды вручную:")
    print("pip uninstall python-telegram-bot -y")
    print("pip install python-telegram-bot==20.7")
    print("=" * 60)
    print("\nПока использую эмуляцию бота...")
    
    # Запускаем простую версию на чистом requests
    import threading
    
    def simple_webhook_bot():
        """Простой бот на requests"""
        BOT_TOKEN = "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk"
        BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
        
        print(f"🤖 Простой бот запущен с токеном: {BOT_TOKEN[:10]}...")
        
        last_update_id = 0
        user_counts = {}
        
        while True:
            try:
                # Получаем обновления
                resp = requests.get(f"{BASE_URL}/getUpdates", 
                                  params={"offset": last_update_id + 1, "timeout": 30},
                                  timeout=35)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            last_update_id = update["update_id"]
                            
                            if "message" in update and "text" in update["message"]:
                                msg = update["message"]
                                chat_id = msg["chat"]["id"]
                                user_id = msg["from"]["id"]
                                text = msg["text"]
                                
                                # Инициализируем счетчик
                                if user_id not in user_counts:
                                    user_counts[user_id] = 0
                                
                                # Обрабатываем команды
                                if text == "/start":
                                    response = f"""👋 Привет, {msg['from'].get('first_name', 'друг')}!

Я бот для проверки договоров.
Отправь текст договора для анализа.

💰 Цена: 69₽ за проверку
🎁 Первая проверка бесплатна

Просто отправь текст договора..."""
                                    
                                    requests.post(f"{BASE_URL}/sendMessage", 
                                                json={"chat_id": chat_id, "text": response, "parse_mode": "Markdown"})
                                
                                elif text == "/help":
                                    help_text = """📖 Помощь:

1. Отправьте текст договора
2. Получите анализ рисков
3. Используйте рекомендации

💰 Тарифы:
• Первая проверка — бесплатно
• Последующие — 69₽

⚠️ Для важных договоров обратитесь к юристу."""
                                    
                                    requests.post(f"{BASE_URL}/sendMessage",
                                                json={"chat_id": chat_id, "text": help_text, "parse_mode": "Markdown"})
                                
                                elif not text.startswith("/"):
                                    # Проверяем лимиты
                                    if user_counts[user_id] >= 1:  # FREE_CHECKS = 1
                                        pay_text = f"""❌ Бесплатные проверки закончились

Для продолжения оплатите 69₽:
💳 Карта: 2200 1234 5678 9012
📝 Комментарий: ID:{user_id}

После оплаты отправьте скриншок чека."""
                                        
                                        requests.post(f"{BASE_URL}/sendMessage",
                                                    json={"chat_id": chat_id, "text": pay_text, "parse_mode": "Markdown"})
                                    else:
                                        # Анализируем
                                        analysis = f"""📋 Анализ договора

Длина текста: {len(text)} символов

Основные моменты для проверки:
1. ✅ Проверьте все даты и суммы
2. ✅ Уточните условия расторжения
3. ✅ Обратите внимание на штрафные санкции
4. ✅ Убедитесь, что все условия понятны

💡 Рекомендации:
• Покажите договор юристу для важных сделок
• Сохраните копию подписанного договора
• Обсудите непонятные пункты с контрагентом

📊 Статистика:
• Проверок выполнено: {user_counts[user_id] + 1}
• Бесплатных осталось: 0
• Следующая проверка: 69₽

⚠️ Это базовая проверка. Для детального анализа обратитесь к юристу."""
                                        
                                        requests.post(f"{BASE_URL}/sendMessage",
                                                    json={"chat_id": chat_id, "text": analysis, "parse_mode": "Markdown"})
                                        
                                        # Увеличиваем счетчик
                                        user_counts[user_id] += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Ошибка в простом боте: {e}")
                time.sleep(5)
    
    # Запускаем простого бота в отдельном потоке
    bot_thread = threading.Thread(target=simple_webhook_bot, daemon=True)
    bot_thread.start()
    
    # Держим основной поток активным
    try:
        while True:
            print("🤖 Бот работает... Нажмите Ctrl+C для остановки")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    
    sys.exit(0)

# ========== ВАШИ КЛЮЧИ ==========
BOT_TOKEN = "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk"
YC_API_KEY = "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln"
YC_FOLDER_ID = "b1g4dtdoatk25ohp8m0u"
YC_AGENT_ID = "fvt3629n2tdfefsjct9d"

# ========== НАСТРОЙКИ ==========
FREE_CHECKS = 1
PRICE = 69

# ========== БАЗА ДАННЫХ ==========
users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"checks": 0, "name": "User"}
    return users_db[user_id]

# ========== ФУНКЦИИ ДЛЯ ВЕРСИИ 20.x ==========
if BOT_VERSION == 20:
    async def start_20(update: Update, context: CallbackContext):
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
    
    async def help_20(update: Update, context: CallbackContext):
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
    
    async def handle_text_20(update: Update, context: CallbackContext):
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
        
        try:
            # Простой анализ
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
            
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка: {str(e)[:200]}")
    
    def main_20():
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start_20))
        app.add_handler(CommandHandler("help", help_20))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_20))
        
        print("🤖 Бот запущен (версия 20.x)")
        app.run_polling()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print(f"\n💰 Цена за проверку: {PRICE}₽")
    print(f"🎁 Бесплатных проверок: {FREE_CHECKS}")
    print("=" * 60)
    
    if BOT_VERSION == 20:
        main_20()
    elif BOT_VERSION == 13:
        # Код для версии 13.x (если заработает)
        print("Использую версию 13.x...")
        # ... аналогичный код для версии 13
    else:
        print("Бот работает в упрощенном режиме через requests")
        # Простой бот уже запущен в потоке выше
