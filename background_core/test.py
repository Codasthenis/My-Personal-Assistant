from telegram.ext import ContextTypes

async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id  # آی‌دی کانال یا چت مقصد
    
    try:
        # اینجا بعداً می‌توانی متن یا محتوای مورد نظرت را از منبع دلخواهت بگیری
        message_text = "سلام! این یک پست خودکار است که از پس‌زمینه ارسال شده."
        
        # ارسال پیام به کانال
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        print("پست با موفقیت در کانال منتشر شد.")
        
    except Exception as e:
        print(f"خطا در ارسال پست خودکار: {e}")
