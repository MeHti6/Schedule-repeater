import logging
import asyncio
import pytz
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session store and loop reference
user_sessions = {}
tehran_tz = pytz.timezone("Asia/Tehran")
event_loop = None  # For running async jobs from threads

# Initialize the scheduler
scheduler = BackgroundScheduler(timezone=tehran_tz)
scheduler.start()


# === Command Handlers ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /channel <channel_id> to begin.")


async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /channel <channel_id> (e.g., @mychannel or -1001234567890)")
        return

    channel_id = context.args[0]
    user_sessions[user_id] = {
        "channel_id": channel_id,
        "messages": [],
        "start_time": None
    }
    await update.message.reply_text(f"✅ Channel set to {channel_id}. Now use /time <date>, <HH:MM>")


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        await update.message.reply_text("❗ First set the channel with /channel")
        return

    try:
        date_str = " ".join(context.args)
        dt = datetime.strptime(date_str, "%b%d, %H:%M")  # e.g., Jul25, 13:20
        dt = dt.replace(year=datetime.now().year)
        dt = tehran_tz.localize(dt)

        user_sessions[user_id]["start_time"] = dt
        user_sessions[user_id]["messages"] = []

        await update.message.reply_text(
            f"⏰ Time set to {dt.strftime('%Y-%m-%d %H:%M')} Tehran time.\nNow send me the messages to schedule!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid time format. Use: /time Jul25, 13:20\nError: {e}")


async def timenow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(tehran_tz)
    await update.message.reply_text(now.strftime("🕒 Tehran time: %A, %Y-%m-%d %H:%M"))


# === Handle incoming messages to schedule ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_sessions or not user_sessions[user_id].get("start_time"):
        await update.message.reply_text("❗ Please use /channel and /time before sending messages.")
        return

    text = update.message.text
    session = user_sessions[user_id]
    session["messages"].append(text)

    index = len(session["messages"]) - 1
    send_time = session["start_time"] + timedelta(minutes=10 * index)

    # Schedule the message safely
    scheduler.add_job(
        run_async_job,
        'date',
        run_date=send_time,
        args=[context.application.bot, session["channel_id"], text]
    )

    await update.message.reply_text(
        f"📨 Message scheduled for {send_time.strftime('%Y-%m-%d %H:%M')} Tehran time."
    )


# === Async send logic ===

def run_async_job(bot, chat_id, message):
    if event_loop:
        asyncio.run_coroutine_threadsafe(
            send_scheduled_message(bot, chat_id, message),
            event_loop
        )


async def send_scheduled_message(bot, chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"✅ Sent message to {chat_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send message to {chat_id}: {e}")


# === Entry Point ===

def main():
    global event_loop
    TOKEN = "5767354546:AAHua7CauSmV_aOH9lAjxqayAyti8MXgocw"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("channel", set_channel))
    app.add_handler(CommandHandler("time", set_time))
    app.add_handler(CommandHandler("timenow", timenow))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot started...")

    # Save event loop so APScheduler jobs can use it
    event_loop = asyncio.get_event_loop()

    app.run_polling()


if __name__ == "__main__":
    main()
