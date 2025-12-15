"""
Contract Check Bot - Автономная версия
Автоматически устанавливает зависимости при запуске
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

print("=" * 60)
print("🤖 CONTRACT CHECK BOT - ЗАПУСК")
print("=" * 60)

# ========== АВТОМАТИЧЕСКАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ ==========
def install_dependencies():
    """Автоматическая установка зависимостей"""
    print("📦 Проверяю зависимости...")
    
    dependencies = [
        "python-telegram-bot==13.15",
        "requests==2.31.0"
    ]
    
    for dep in dependencies:
        try:
            # Пробуем импорт
            if "telegram" in dep:
                __import__('telegram')
                print(f"✅ {dep.split('==')[0]} уже установлен")
            elif "requests" in dep:
                __import__('requests')
                print(f"✅ {dep.split('==')[0]} уже установлен")
        except ImportError:
            # Устанавливаем если нет
            print(f"⬇️ Устанавливаю {dep}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
                print(f"✅ {dep} установлен")
            except Exception as e:
                print(f"❌ Ошибка установки {dep}: {e}")
                return False
    
    return True

# Устанавливаем зависимости
if not install_dependencies():
    print("❌ Не удалось установить зависимости")
    sys.exit(1)

# ========== ИМПОРТ ПОСЛЕ УСТАНОВКИ ==========
try:
    import requests
    import telegram
    from telegram import Update
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
    print("✅ Все библиотеки загружены")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# ========== ВАШИ КЛЮЧИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk")
YC_API_KEY = os.environ.get("YC_API_KEY", "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln")
YC_FOLDER_ID = os.environ.get("YC_FOLDER_ID", "b1g4dtdoatk25ohp8m0u")
YC_AGENT_ID = os.environ.get("YC_AGENT_ID", "fvt3629n2tdfefsjct9d")

# ========== НАСТРОЙКИ ==========
FREE_CHECKS = 1
PRICE_PER_CHECK = 69

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПРОСТАЯ БАЗА ДАННЫХ ==========
class SimpleDB:
    def __init__(self):
        self.data = {}
        print("💾 База данных инициализирована")
    
    def get_user(self, user_id):
        if user_id not in self.data:
            self.data[user_id] = {'checks': 0, 'last_check': None}
        return self.data[user_id]
    
    def add_check(self, user_id):
        user = self.get_user(user_id)
        user['checks'] += 1
        user['last_check'] = datetime.now()
        return user['checks']

db = SimpleDB()

# ========== ПРОСТОЙ АНАЛИЗАТОР (БЕЗ ЯНДЕКС ДЛЯ НАЧАЛА) ==========
class ContractAnalyzer:
    """Простой анализатор договоров"""
    
    def analyze(self, text):
        """Базовый анализ текста"""
        if len(text) < 100:
            return "❌ Текст слишком короткий для анализа"
        
        # Простые правила анализа
        warnings = []
        tips = []
        
        # Проверка длины
        if len(text) > 10000:
            warnings.append("⚠️ Договор очень длинный, могут быть скрытые условия")
        elif len(text) < 500:
            tips.append("💡 Договор очень короткий, возможно, не все условия прописаны")
        
        # Поиск ключевых слов
        text_lower = text.lower()
        
        keywords = {
            'односторонн': '⚠️ Проверьте условия одностороннего расторжения',
            'штраф': '⚠️ Обратите внимание на размер штрафных санкций',
            'пеня': '⚠️ Проверьте условия начисления пени',
            'неустойк': '⚠️ Уточните размер неустойки',
            'ответственност': '⚠️ Проверьте раздел об ответственности',
            'конфиденциальн': '💡 Есть пункт о конфиденциальности',
            'форс-мажор': '💡 Есть условие о форс-мажоре',
            'арбитраж': '⚠️ Проверьте условия рассмотрения споров',
            'юр. адрес': '✅ Указаны юридические адреса',
            'паспорт': '✅ Указаны паспортные данные',
        }
        
        for keyword, message in keywords.items():
            if keyword in text_lower:
                if '⚠️' in message:
                    warnings.append(message)
                else:
                    tips.append(message)
        
        # Формируем ответ
        result = "📋 *Результат проверки*\n\n"
        
        if warnings:
            result += "*Внимание на эти пункты:*\n"
            for w in warnings[:5]:
                result += f"• {w}\n"
            result += "\n"
        
        if tips:
            result += "*Что хорошо:*\n"
            for t in tips[:5]:
                result += f"• {t}\n"
            result += "\n"
        
        if not warnings and not tips:
            result += "✅ По базовым проверкам проблем не обнаружено\n\n"
        
        result += "*Общие рекомендации:*\n"
        result += "1. Проверьте все суммы и сроки\n"
        result += "2. Убедитесь, что понимаете все условия\n"
        result += "3. Покажите договор юристу для важных сделок\n"
        result += "4. Сохраните копию подписанного договора\n\n"
        
        result += f"*Статистика:* Текст {len(text)} символов, найдено {len(warnings)} предупреждений"
        
        return result
    
    def test_yandex(self):
        """Проверка подключения к Яндекс GPT"""
        if not all([YC_API_KEY, YC_FOLDER_ID, YC_AGENT_ID]):
            return "❌ Не настроены ключи Яндекс"
        
        url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        headers = {"Authorization": f"Api-Key {YC_API_KEY}", "Content-Type": "application/json"}
        
        data = {
            "messages": [{"role": "user", "content": "Привет"}],
            "generationOptions": {"maxTokens": 10}
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                return "✅ Яндекс GPT доступен"
            else:
                return f"❌ Яндекс GPT ошибка: {response.status_code}"
        except Exception as e:
            return f"❌ Яндекс GPT недоступен: {str(e)[:100]}"

# ========== TELEGRAM КОМАНДЫ ==========
def start_command(update, context):
    """Обработчик /start"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    text = f"""🤖 *Добро пожаловать!*

Я помогу проверить договор на основные риски.

*Ваша статистика:*
✓ Проверок: {user_data['checks']}
✓ Бесплатных осталось: {max(0, FREE_CHECKS - user_data['checks'])}
✓ Цена после: {PRICE_PER_CHECK}₽

*Как использовать:*
1. Отправьте текст договора
2. Получите анализ
3. Используйте рекомендации

Просто отправьте текст договора..."""
    
    update.message.reply_text(text, parse_mode='Markdown')

def help_command(update, context):
    """Обработчик /help"""
    text = """📋 *Помощь*

*Что умеет бот:*
• Базовая проверка договоров
• Поиск рискованных формулировок
• Общие рекомендации

*Тарифы:*
• Первая проверка — бесплатно
• Последующие — 69₽

*Важно:*
Это базовая проверка, не заменяющая юриста!
Для важных сделок обратитесь к специалисту."""
    
    update.message.reply_text(text, parse_mode='Markdown')

def check_command(update, context):
    """Обработчик /check"""
    text = """Чтобы проверить договор:
1. Скопируйте текст договора
2. Отправьте его мне сообщением
3. Я проанализирую и дам рекомендации

Примеры что искать:
• Скрытые условия
• Неясные формулировки  
• Рискованные пункты"""
    
    update.message.reply_text(text, parse_mode='Markdown')

def stats_command(update, context):
    """Обработчик /stats"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    analyzer = ContractAnalyzer()
    yandex_status = analyzer.test_yandex()
    
    text = f"""📊 *Ваша статистика*

*Проверки:*
• Выполнено: {user_data['checks']}
• Бесплатных осталось: {max(0, FREE_CHECKS - user_data['checks'])}
• Последняя проверка: {user_data['last_check'] or 'еще не было'}

*Система:*
• Яндекс GPT: {yandex_status}
• База данных: {len(db.data)} пользователей

*Тарифы:*
• Текущая цена: {PRICE_PER_CHECK}₽ за проверку
• Бесплатный лимит: {FREE_CHECKS} проверка"""
    
    update.message.reply_text(text, parse_mode='Markdown')

def handle_text(update, context):
    """Обработка текстовых сообщений"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    text = update.message.text
    
    # Игнорируем короткие сообщения и команды
    if len(text) < 30 or text.startswith('/'):
        return
    
    # Проверка лимитов
    if user_data['checks'] >= FREE_CHECKS:
        update.message.reply_text(
            f"""❌ *Лимит проверок исчерпан*

Вы использовали {user_data['checks']} проверок.

Для продолжения оплатите {PRICE_PER_CHECK}₽:

*Реквизиты:*
💳 Карта: `2200 1234 5678 9012`
📝 Комментарий: `ID:{user.id}`

После оплаты отправьте скриншот.""",
            parse_mode='Markdown'
        )
        return
    
    # Начинаем анализ
    msg = update.message.reply_text("🔍 *Анализирую текст...*", parse_mode='Markdown')
    
    try:
        # Анализируем
        analyzer = ContractAnalyzer()
        result = analyzer.analyze(text)
        
        # Сохраняем
        db.add_check(user.id)
        
        # Формируем итоговое сообщение
        final_result = f"""{result}

📈 *Ваша статистика:*
• Проверок выполнено: {user_data['checks'] + 1}
• Бесплатных осталось: {max(0, FREE_CHECKS - (user_data['checks'] + 1))}
• Следующая проверка: {"бесплатна" if user_data['checks'] + 1 < FREE_CHECKS else f"{PRICE_PER_CHECK}₽"}"""
        
        # Отправляем
        msg.edit_text(final_result, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        msg.edit_text(f"❌ *Ошибка анализа:*\n\n{str(e)[:200]}")

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция"""
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК БОТА")
    print("=" * 60)
    
    # Проверяем токен
    if not BOT_TOKEN or "ваш_токен" in BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не настроен!")
        print("Добавьте в Railway Variables:")
        print("BOT_TOKEN = 7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk")
        return
    
    print(f"✅ BOT_TOKEN: {'Настроен' if BOT_TOKEN else 'Нет'}")
    print(f"✅ YC_API_KEY: {'Настроен' if YC_API_KEY else 'Нет'}")
    print(f"✅ YC_FOLDER_ID: {'Настроен' if YC_FOLDER_ID else 'Нет'}")
    print(f"✅ YC_AGENT_ID: {'Настроен' if YC_AGENT_ID else 'Нет'}")
    
    # Проверяем Яндекс
    analyzer = ContractAnalyzer()
    yandex_status = analyzer.test_yandex()
    print(f"🌐 Яндекс GPT: {yandex_status}")
    
    print(f"\n💰 Цена за проверку: {PRICE_PER_CHECK}₽")
    print(f"🎁 Бесплатных проверок: {FREE_CHECKS}")
    print("=" * 60)
    
    # Запускаем бота
    try:
        print("🤖 Запускаю Telegram бота...")
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем команды
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("check", check_command))
        dispatcher.add_handler(CommandHandler("stats", stats_command))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        
        print("✅ Бот запущен!")
        print("⏳ Ожидаю сообщений...")
        print("\nДля остановки: Ctrl+C")
        
        # Стартуем
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("\nПопробуйте:")
        print("1. Проверить BOT_TOKEN")
        print("2. Перезапустить Railway")
        print("3. Использовать другой хостинг")

# ========== ТОЧКА ВХОДА ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        print("Перезапускаюсь через 5 секунд...")
        import time
        time.sleep(5)
        main()
