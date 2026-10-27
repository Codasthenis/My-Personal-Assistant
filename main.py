import os

token = os.getenv("TOKEN")

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

app = Application.builder().token(token).build()

@app.command("start")
def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("Hello, world!")

app.run_polling()