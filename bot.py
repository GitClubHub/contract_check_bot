"""
bot.py - Telegram бот для проверки договоров через YandexGPT
ВСЁ В ОДНОМ ФАЙЛЕ: бот + парсинг + ИИ
"""

import os
import logging
import tempfile
import requests
import sqlite3
from datetime import datetime

# ========== ВАШИ НАСТРОЙКИ ==========
BOT_TOKEN = "7840984761:AAEba5khaFEQ80LPIqT34QVJ84tTxQRlIMk"
YC_API_KEY = "AQVNw1vfsx6MXgs3I-cmowKh2ZCD1xSHktDdW0ln"
YC_FOLDER_ID = "b1g4dtdoatk25ohp8m0u"
YC_AGENT_ID = "fvt3629n2tdfefsjct9d"

# ========== ЦЕНЫ И ЛИМИТЫ ==========
FREE_CHECKS = 1                    # Бесплатных проверок
SINGLE_CHECK_PRICE = 69            # 69 рублей за проверку (НОВАЯ ЦЕНА)
MAX_FILE_SIZE_MB = 15              # Максимальный размер файла
SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']

# ========== ИМПОРТЫ TELEGRAM ==========
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КЛАСС ДЛЯ YANDEX GPT ==========
class YandexGPTAnalyzer:
    """Работа с YandexGPT Agent API"""
    
    def __init__(self):
        self.api_url = f"https://agent.llm.api.cloud.yandex.net/llm/v2/folders/{YC_FOLDER_ID}/agents/{YC_AGENT_ID}:chat"
        self.headers = {
            "Authorization": f"Api-Key {YC_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def analyze(self, text):
        """Анализ текста договора"""
        
        # Обрезаем слишком длинные тексты
        if len(text) > 80000:
            text = text[:80000] + "\n\n[Текст сокращен для анализа]"
        
        # Промпт для анализа
        prompt = f"""
Ты — опытный юрист. Проанализируй договор и выдели:

1. ОСНОВНЫЕ РИСКИ (Высокий/Средний/Низкий)
2. НЕЯСНЫЕ ФОРМУЛИРОВКИ  
3. ЧТО РЕКОМЕНДУЕШЬ ИЗМЕНИТЬ
4. ВОПРОСЫ К ВТОРОЙ СТОРОНЕ

ДОГОВОР:
{text}

Отвечай четко, по пунктам. Не выдумывай.
"""
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "generationOptions": {"maxTokens": 1500, "temperature": 0.1}
        }
        
        try:
            response = requests.post(self.api_url, json=data, headers=self.headers, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                # Пытаемся извлечь ответ разными способами
                if 'message' in result and 'content' in result['message']:
                    return result['message']['content']
                elif 'choices' in result and result['choices']:
                    return result['choices'][0].get('message', {}).get('content', 'Нет ответа')
                else:
                    return str(result)[:1000]
            else:
                return f"❌ Ошибка API: {response.status_code}\n{response.text[:500]}"
                
        except Exception as e:
            return f"⚠️ Ошибка связи: {str(e)}"

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ ==========
def extract_text_from_pdf(file_path):
    """Извлечение текста из PDF"""
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text if text else "Не удалось извлечь текст из PDF"
    except Exception as e:
        return f"Ошибка PDF: {str(e)}"

def extract_text_from_docx(file_path):
    """Извлечение текста из DOCX"""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Ошибка DOCX: {str(e)}"

def extract_text_from_file(file_path, file_ext):
    """Определяет тип файла и извлекает текст"""
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "Неподдерживаемый формат"

# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def get_user_checks(user_id):
    """Получить количество использованных проверок"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT checks_used FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_check_to_db(user_id, filename, result):
    """Сохранить проверку в БД"""
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Добавляем или обновляем пользователя
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, checks_used, last_check_time) 
        VALUES (?, COALESCE((SELECT checks_used FROM users WHERE user_id = ?), 0) + 1, CURRENT_TIMESTAMP)
    ''', (user_id, user_id))
    
    # Сохраняем историю
    cursor.execute('''
        INSERT INTO checks (user_id, filename, result) 
        VALUES (?, ?, ?)
    ''', (user_id, filename, result[:300]))
    
    conn.commit()
    conn.close()

# ========== ОБРАБОТЧИКИ TELEGRAM ==========
async def start_command(update: Update, context: CallbackContext):
    """Команда /start"""
    user = update.effective_user
    checks_used = get_user_checks(user.id)
    checks_left = FREE_CHECKS - checks_used
    
    text = f"""
👋 *Привет, {user.first_name}!*

Я — бот для проверки договоров.
Отправь мне договор в формате *PDF* или *DOCX*.

📊 *Ваши проверки:*
• Использовано: {checks_used}
• Бесплатных осталось: {checks_left}
• Цена после: *{SINGLE_CHECK_PRICE}₽* за проверку

📌 *Как работает:*
1. Отправь договор
2. Получи анализ рисков
3. Используй в переговорах

⚠️ *Важно:* Я не заменяю юриста!
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_command(update: Update, context: CallbackContext):
    """Команда /help"""
    text = """
📖 *Помощь*

*Что умею:*
• Анализировать договоры (PDF, DOCX, DOC, TXT)
• Находить скрытые риски
• Давать рекомендации

*Как использовать:*
1. Отправьте договор файлом
2. Подождите 20-60 секунд
3. Получите анализ

*Форматы:* PDF, DOCX, DOC, TXT
*Максимальный размер:* 15 MB

*Тарифы:*
• Первая проверка — бесплатно
• Последующие — 69₽ за штуку

*Поддержка:* @ваш_ник (укажите свой)
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_document(update: Update, context: CallbackContext):
    """Обработка загруженного документа"""
    user = update.effective_user
    document = update.message.document
    
    # Проверка лимитов
    checks_used = get_user_checks(user.id)
    if checks_used >= FREE_CHECKS:
        await update.message.reply_text(
            f"❌ *Бесплатные проверки закончились*\n\n"
            f"Для продолжения нужно оплатить проверку:\n"
            f"• Цена: *{SINGLE_CHECK_PRICE}₽*\n"
            f"• Реквизиты: 2200 1234 5678 9012\n"
            f"• В комментарии: ID:{user.id}\n\n"
            f"После оплаты отправьте скриншот чека.",
            parse_mode='Markdown'
        )
        return
    
    # Проверка формата
    file_name = document.file_name or "document"
    file_ext = os.path.splitext(file_name)[1].lower()
    
    if file_ext not in SUPPORTED_FORMATS:
        await update.message.reply_text(
            f"❌ *Неподдерживаемый формат*\n\n"
            f"Поддерживаю: {', '.join(SUPPORTED_FORMATS)}\n"
            f"Ваш файл: {file_ext}",
            parse_mode='Markdown'
        )
        return
    
    # Проверка размера
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    if document.file_size > max_size:
        await update.message.reply_text(
            f"❌ *Файл слишком большой*\n\n"
            f"Максимум: {MAX_FILE_SIZE_MB} MB\n"
            f"Ваш файл: {document.file_size // (1024*1024)} MB",
            parse_mode='Markdown'
        )
        return
    
    # Начинаем обработку
    status_msg = await update.message.reply_text("📥 *Скачиваю файл...*", parse_mode='Markdown')
    
    try:
        # Шаг 1: Скачивание
        await status_msg.edit_text("📥 *Скачиваю файл...*")
        file = await document.get_file()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp_path = tmp.name
            await file.download_to_drive(tmp_path)
        
        # Шаг 2: Извлечение текста
        await status_msg.edit_text("🔍 *Извлекаю текст...*")
        text = extract_text_from_file(tmp_path, file_ext)
        
        if len(text) < 100:
            await status_msg.edit_text(
                "❌ *Не удалось извлечь текст*\n\n"
                "Возможные причины:\n"
                "• Файл поврежден\n"
                "• Это скан (нужен OCR)\n"
                "• Файл пустой\n\n"
                "Попробуйте текстовый PDF или DOCX."
            )
            os.unlink(tmp_path)
            return
        
        # Шаг 3: Анализ ИИ
        await status_msg.edit_text("🤖 *Анализирую договор...*")
        analyzer = YandexGPTAnalyzer()
        result = analyzer.analyze(text)
        
        # Шаг 4: Сохранение в БД
        add_check_to_db(user.id, file_name, result)
        
        # Шаг 5: Отправка результата
        checks_left = FREE_CHECKS - (checks_used + 1)
        
        response_text = f"""
📋 *Анализ договора: {file_name}*

{result[:3500]}

📊 *Ваши проверки:*
• Использовано: {checks_used + 1}
• Бесплатных осталось: {checks_left}

💸 *После окончания:* {SINGLE_CHECK_PRICE}₽ за проверку

⚠️ *Это не юридическая консультация.*
Для важных договоров обратитесь к юристу.
        """
        
        await status_msg.edit_text(response_text[:4096], parse_mode='Markdown')
        
        # Если результат длинный, отправляем вторую часть
        if len(result) > 3500:
            await update.message.reply_text(
                f"*Продолжение анализа:*\n\n{result[3500:7000]}",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        logger.error(f"Ошибка обработки документа: {e}")
        await status_msg.edit_text(f"❌ *Ошибка обработки:*\n\n{str(e)[:500]}")
    
    finally:
        # Удаляем временный файл
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

async def handle_text(update: Update, context: CallbackContext):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text.startswith('/'):
        return
    
    await update.message.reply_text(
        "📎 *Отправьте договор файлом*\n\n"
        "Я анализирую только файлы:\n"
        "• PDF (текстовый)\n"
        "• DOCX / DOC\n"
        "• TXT\n\n"
        "Напишите /help для подробностей.",
        parse_mode='Markdown'
    )

# ========== ЗАПУСК БОТА ==========
def main():
    """Запуск бота"""
    
    # Проверяем наличие библиотек
    try:
        import PyPDF2
        import docx
    except ImportError:
        print("❌ Установите зависимости:")
        print("pip install python-telegram-bot PyPDF2 python-docx requests")
        return
    
    # Инициализируем БД
    if not os.path.exists('bot.db'):
        import database
        database.init_db()
        print("✅ База данных создана")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем
    logger.info("🤖 Бот запущен...")
    print("=" * 50)
    print("Contract Check Bot")
    print(f"Бесплатных проверок: {FREE_CHECKS}")
    print(f"Цена за проверку: {SINGLE_CHECK_PRICE}₽")
    print("=" * 50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
