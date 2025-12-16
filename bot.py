#!/usr/bin/env python3
"""
Contract Check Bot - УЛЬТРАМИНИМАЛЬНАЯ ВЕРСИЯ
Работает на любом Python 3.7+
"""

import os
import sys
import time
import json

print("=" * 60)
print("🤖 CONTRACT CHECK BOT - ЗАПУСК")
print("=" * 60)

# ========== УСТАНОВКА ЗАВИСИМОСТЕЙ ==========
def install_packages():
    """Устанавливаем только необходимые пакеты"""
    required = ["requests", "python-telegram-bot==13.15"]
    
    for package in required:
        try:
            if package == "requests":
                import requests
                print(f"✅ requests уже установлен")
            elif "telegram" in package:
                import telegram
                print(f"✅ python-telegram-bot уже установлен")
        except ImportError:
            print(f"⬇️ Устанавливаю {package}...")
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} установлен")
            except:
                print(f"⚠️ Не удалось установить {package}")
                # Продолжаем без него
                continue

install_packages()

# ========== ИМПОРТ ПОСЛЕ УСТАНОВКИ ==========
try:
    import requests
    print("✅ requests загружен")
except ImportError:
    print("❌ requests не установлен")
    sys.exit(1)

try:
    # Импортируем только самое необходимое
    import telegram
    from telegram import Update
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
    print("✅ telegram загружен")
except ImportError as e:
    print(f"❌ Ошибка импорта telegram: {e}")
    print("Пробую альтернативный импорт...")
    
    try:
        # Альтернативный импорт для старых версий
        import telegram
        from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
        print("✅ telegram загружен (альтернативный путь)")
    except ImportError:
        print("❌ Не удалось загрузить telegram")
        print("Попробуйте вручную: pip install python-telegram-bot==13.15")
        sys.exit(1)

# ========== ВАШИ КЛЮЧИ ==========
BOT_TOKEN = "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk"
YC_API_KEY = "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln"
YC_FOLDER_ID = "b1g4dtdoatk25ohp8m0u"
YC_AGENT_ID = "fvt3629n2tdfefsjct9d"

# ========== НАСТРОЙКИ ==========
FREE_CHECKS = 1
PRICE = 69

# ========== ПРОСТАЯ БАЗА ДАННЫХ ==========
users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"checks": 0, "name": "User"}
    return users_db[user_id]

# ========== ПРОСТОЙ АНАЛИЗАТОР ==========
class SimpleAnalyzer:
    def analyze(self, text):
        """Простой анализ текста"""
        
        if len(text) < 50:
            return "❌ Текст слишком короткий. Нужно минимум 50 символов."
        
        # Базовые проверки
        checks = []
        text_lower = text.lower()
        
        # Проверяем ключевые слова
        if "односторонн" in text_lower:
            checks.append("⚠️ Проверьте условия одностороннего расторжения")
        
        if "штраф" in text_lower or "пеня" in text_lower:
            checks.append("⚠️ Обратите внимание на штрафные санкции")
        
        if "ответственност" in text_lower:
            checks.append("⚠️ Проверьте раздел об ответственности")
        
        if "юр. адрес" in text_lower or "паспорт" in text_lower:
            checks.append("✅ Указаны реквизиты сторон")
        
        # Формируем ответ
        result = f"📋 *Анализ договора*\n\n"
        result += f"Длина текста: {len(text)} символов\n\n"
        
        if checks:
            result += "*Обнаружено:*\n"
            for check in checks[:5]:
                result += f"• {check}\n"
        else:
            result += "✅ По базовым проверкам проблем не найдено\n"
        
        result += "\n*Рекомендации:*\n"
        result += "1. Проверьте все даты и суммы\n"
        result += "2. Убедитесь, что понимаете каждый пункт\n"
        result += "3. Для важных сделок покажите договор юристу\n"
        
        return result

# ========== TELEGRAM КОМАНДЫ ==========
def start(update, context):
    user = update.effective_user
    user_data = get_user(user.id)
    
    text = f"""👋 *Привет, {user.first_name}!*

Я помогу проверить договор.

*Как использовать:*
Отправьте текст договора — я проанализирую его.

*Ваша статистика:*
✓ Проверок: {user_data['checks']}
✓ Бесплатных осталось: {max(0, FREE_CHECKS - user_data['checks'])}
✓ Цена после: {PRICE}₽

*Просто отправьте текст договора...*"""
    
    update.message.reply_text(text, parse_mode='Markdown')

def help_cmd(update, context):
    text = """📖 *Помощь*

*Что делает бот:*
• Анализирует текст договоров
• Ищет рискованные формулировки
• Дает рекомендации

*Тарифы:*
• Первая проверка — бесплатно
• Последующие — 69₽

*Важно:* Это базовая проверка.
Для важных договоров обратитесь к юристу."""
    
    update.message.reply_text(text, parse_mode='Markdown')

def handle_text(update, context):
    user = update.effective_user
    user_data = get_user(user.id)
    text = update.message.text
    
    # Игнорируем команды и короткие сообщения
    if text.startswith('/') or len(text) < 20:
        return
    
    # Проверяем лимиты
    if user_data['checks'] >= FREE_CHECKS:
        update.message.reply_text(
            f"❌ *Бесплатные проверки закончились*\n\n"
            f"Для продолжения оплатите {PRICE}₽:\n"
            f"💳 Карта: 2200 1234 5678 9012\n"
            f"📝 Комментарий: ID:{user.id}\n\n"
            f"После оплаты отправьте скриншок чека.",
            parse_mode='Markdown'
        )
        return
    
    # Анализируем
    msg = update.message.reply_text("🔍 *Анализирую...*", parse_mode='Markdown')
    
    try:
        analyzer = SimpleAnalyzer()
        result = analyzer.analyze(text)
        
        # Сохраняем
        user_data['checks'] += 1
        
        # Добавляем статистику
        checks_left = FREE_CHECKS - user_data['checks']
        result += f"\n\n📊 *Статистика:*\n"
        result += f"• Проверок выполнено: {user_data['checks']}\n"
        result += f"• Бесплатных осталось: {max(0, checks_left)}\n"
        result += f"• Следующая проверка: {'бесплатна' if checks_left > 0 else f'{PRICE}₽'}"
        
        msg.edit_text(result, parse_mode='Markdown')
        
    except Exception as e:
        msg.edit_text(f"❌ Ошибка: {str(e)[:200]}")

# ========== ЗАПУСК БОТА ==========
def main():
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК БОТА")
    print("=" * 60)
    
    print(f"🤖 Токен бота: {'✅' if BOT_TOKEN else '❌'}")
    print(f"💰 Цена за проверку: {PRICE}₽")
    print(f"🎁 Бесплатных проверок: {FREE_CHECKS}")
    
    try:
        print("\n🤖 Создаю Updater...")
        updater = Updater(BOT_TOKEN, use_context=True)
        
        print("✅ Updater создан")
        print("📝 Регистрирую команды...")
        
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_cmd))
        dp.add_handler(MessageHandler(Filters.text, handle_text))
        
        print("✅ Команды зарегистрированы")
        print("🚀 Запускаю бота...")
        
        updater.start_polling()
        
        print("=" * 60)
        print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
        print("=" * 60)
        print("\n📱 Теперь вы можете:")
        print("1. Открыть Telegram")
        print("2. Найти бота по ID: 7840984761")
        print("3. Написать /start")
        print("4. Отправить текст договора для анализа")
        print("\n⏳ Бот работает и ждет сообщений...")
        
        # Держим бота активным
        updater.idle()
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\nВозможные решения:")
        print("1. Проверьте BOT_TOKEN")
        print("2. Перезапустите Railway: нажмите Redeploy")
        print("3. Попробуйте локальный запуск:")

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        print("Попробую перезапуститься...")
        time.sleep(5)
        main()
