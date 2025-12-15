import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import tempfile

from config import BOT_TOKEN, FREE_CHECKS, MAX_FILE_SIZE_MB, SUPPORTED_FORMATS
from database import get_user, add_check
from parser import extract_text
from yandex_agent import YandexAgent

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация анализатора
analyzer = YandexAgent()

async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    db_user = get_user(user.id)
    
    text = f"""
👋 Привет, {user.first_name}!

Я бот для проверки договоров. 
Отправь мне договор (PDF или DOCX), и я найду риски.

Бесплатных проверок осталось: {FREE_CHECKS - db_user['free_checks_used']}
    """
    
    await update.message.reply_text(text)

async def handle_document(update: Update, context: CallbackContext):
    """Обработка загруженного документа"""
    user = update.effective_user
    document = update.message.document
    
    # Проверяем лимиты
    db_user = get_user(user.id)
    if db_user['free_checks_used'] >= FREE_CHECKS:
        await update.message.reply_text(
            "❌ Бесплатные проверки закончились. "
            "Для продолжения нужна оплата."
        )
        return
    
    # Проверяем формат
    file_ext = os.path.splitext(document.file_name)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        await update.message.reply_text(
            f"❌ Неподдерживаемый формат. Используйте: {', '.join(SUPPORTED_FORMATS)}"
        )
        return
    
    # Проверяем размер
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    if document.file_size > max_size:
        await update.message.reply_text(
            f"❌ Файл слишком большой. Максимум: {MAX_FILE_SIZE_MB}MB"
        )
        return
    
    # Скачиваем файл
    await update.message.reply_text("📥 Скачиваю файл...")
    
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            file = await document.get_file()
            await file.download_to_drive(tmp_file.name)
            
            # Извлекаем текст
            await update.message.reply_text("🔍 Извлекаю текст...")
            text = extract_text(tmp_file.name, file_ext[1:])  # Убираем точку
            
            if len(text) < 100:
                await update.message.reply_text(
                    "❌ Не удалось извлечь текст. Возможно, файл поврежден или это скан."
                )
                return
            
            # Анализируем
            await update.message.reply_text("🤖 Анализирую договор...")
            analysis = analyzer.analyze_contract(text)
            
            # Сохраняем в БД
            add_check(user.id, document.file_name, analysis[:1000])  # Сохраняем часть
            
            # Отправляем результат
            result_text = f"""
📋 *Результат анализа:*

{analysis}

⚠️ *Важно:* Это не юридическая консультация.
Для важных договоров обратитесь к юристу.
            """
            
            await update.message.reply_text(result_text[:4000], parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        
    finally:
        # Удаляем временный файл
        if 'tmp_file' in locals():
            try:
                os.unlink(tmp_file.name)
            except:
                pass

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """
📖 *Как пользоваться:*
1. Отправьте договор в формате PDF или DOCX
2. Дождитесь анализа (1-2 минуты)
3. Получите отчет о рисках

📌 *Что умеет бот:*
• Находить скрытые условия
• Выделять риски
• Давать рекомендации

💸 *Тарифы:*
• 1 проверка бесплатно
• Дальше 299₽ за проверку
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Документы
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Запуск
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
