import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

app = Application.builder().token(token).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Hello, world!")

app.add_handler(CommandHandler("start", start))

app.run_polling()