from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging
from telegram import ReactionTypeEmoji

def react(reaction: str):
    async def react_to_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        این تابع هر وقت پستی در کانال گذاشته شود اجرا می‌شود.
        """
        try:
            # گرفتن آیدی چت و آیدی پیام
            chat_id = update.effective_chat.id
            message_id = update.effective_message.message_id

            # کمی تاخیر برای طبیعی‌تر شدن (اختیاری)
            await asyncio.sleep(1)

            # ارسال ری‌اکشن
            # نکته: لیست ایموجی‌ها را می‌توانید تغییر دهید
            await context.bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message_id,
                reaction=[ReactionTypeEmoji(emoji=reaction)],
                is_big=False 
            )
            
            logging.info(f"Reacted to message {message_id} in chat {chat_id}")

        except Exception as e:
            logging.error(f"Error in reaction: {e}")
    return react_to_post