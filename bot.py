import logging
import pytz
from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import asyncio

# --- Config ---
TOKEN = "5767354546:AAHua7CauSmV_aOH9lAjxqayAyti8MXgocw"
tehran = pytz.timezone("Asia/Tehran")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Globals ---
channel_id = None
start_time = None
messages_queue = []
scheduled_jobs = []

# --- Caption State ---
caption_enabled = False
caption_text = ""

# --- APScheduler ---
scheduler = BackgroundScheduler(timezone=tehran)
scheduler.start()

# --- Async helper to send scheduled message ---
async def send_scheduled_message(bot, chat_id, msg):
    await bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)

# --- Sync wrapper for scheduler ---
def schedule_job(bot, chat_id, msg):
    asyncio.create_task(send_scheduled_message(bot, chat_id, msg))

# --- Commands ---

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global channel_id
    if context.args:
        channel_id = context.args[0]
        await update.message.reply_text(f"Channel set to {channel_id}")
    else:
        await update.message.reply_text("Usage: /channel @channel_username_or_id")

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global start_time, messages_queue, scheduled_jobs
    if not context.args:
        await update.message.reply_text("Usage: /time Jul25, 13:20")
        return
    try:
        user_input = " ".join(context.args)
        date_part, time_part = user_input.split(",")
        now = datetime.now(tehran)
        full_str = f"{now.year} {date_part.strip()} {time_part.strip()}"
        start_time = datetime.strptime(full_str, "%Y %b%d %H:%M")
        start_time = tehran.localize(start_time)
        messages_queue.clear()
        scheduled_jobs.clear()
        await update.message.reply_text(f"Start time set to {start_time.strftime('%Y-%m-%d %H:%M %Z')}")
    except Exception as e:
        await update.message.reply_text(f"Error parsing time: {e}")

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global start_time, messages_queue, scheduled_jobs
    if not channel_id or not start_time:
        await update.message.reply_text("Please set /channel and /time first.")
        return
    text = update.message.text

    # Add caption if enabled
    if caption_enabled and caption_text:
        text += f"\n\n{caption_text}"

    index = len(messages_queue)
    delay = timedelta(minutes=10 * index)
    scheduled_time = start_time + delay
    job_id = f"{update.message.message_id}-{int(scheduled_time.timestamp())}"

    job = scheduler.add_job(schedule_job, 'date',
                            run_date=scheduled_time,
                            args=[context.bot, channel_id, text],
                            id=job_id)

    scheduled_jobs.append(job)
    messages_queue.append(text)
    await update.message.reply_text(f"Message scheduled at {scheduled_time.strftime('%H:%M')}")

async def timenow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(tehran).strftime("%b%d, %H:%M")
    await update.message.reply_text(f"/time {now}")

async def remain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remaining = [job for job in scheduled_jobs if job.next_run_time and job.next_run_time > datetime.now(tehran)]
    await update.message.reply_text(f"{len(remaining)} messages remaining to send.")

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scheduled_jobs, messages_queue
    count = 0
    for job in list(scheduled_jobs):
        try:
            scheduler.remove_job(job.id)
            scheduled_jobs.remove(job)
            count += 1
        except JobLookupError:
            pass  # Already run
    messages_queue.clear()
    await update.message.reply_text(f"{count} scheduled message(s) deleted.")

async def caption_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global caption_enabled
    caption_enabled = True
    await update.message.reply_text("✅ Captioning is now ON.")

async def caption_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global caption_enabled
    caption_enabled = False
    await update.message.reply_text("❌ Captioning is now OFF.")

async def caption_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global caption_text
    caption_text = " ".join(context.args)
    await update.message.reply_text(f"✏️ Caption set to:\n{caption_text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling update:", exc_info=context.error)

# --- Main ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("channel", set_channel))
    app.add_handler(CommandHandler("time", set_time))
    app.add_handler(CommandHandler("timenow", timenow))
    app.add_handler(CommandHandler("remain", remain))
    app.add_handler(CommandHandler("delete", delete_all))
    app.add_handler(CommandHandler("caption", caption_on))
    app.add_handler(CommandHandler("captionoff", caption_off))
    app.add_handler(CommandHandler("captionset", caption_set))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))
    app.add_error_handler(error_handler)

    print("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
