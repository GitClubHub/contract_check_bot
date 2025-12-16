import os
import telegram

print("PTB version:", telegram.__version__)

from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("Бот работает!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

app.run_polling()
