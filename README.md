# 📅 Telegram Channel Scheduler Bot

This Telegram bot allows you to schedule multiple messages to be sent in your Telegram **channel** at regular 10-minute intervals, using simple `/channel`, `/time`, and plain text messages.

It is designed to run 24/7 on [PythonAnywhere](https://www.pythonanywhere.com/) with minimal setup.

---

## ✅ Features

- `/channel <channel_id>` — Set the target channel  
- `/time <MonthDay, HH:MM>` — Set the start time in Tehran timezone (e.g., `Jul25, 14:00`)  
- `/timenow` — Show the current time and day in Tehran  
- 📨 Send messages after `/time` — they will be scheduled 10 minutes apart  
- 🕒 Works 24/7 using PythonAnywhere's **Always-on Task**  

---

## ⚙️ Setup Instructions (PythonAnywhere, Bash)

> 🐍 Requires Python 3.10  
> 📍 These steps assume you're running this bot on PythonAnywhere

### 1. Install required packages

```bash
python3.10 -m pip install --user python-telegram-bot==20.7 APScheduler pytz
```
2. Replace the bot token
Open your bot.py file and replace this line:

```
TOKEN = "YOUR_BOT_TOKEN_HERE"
```

3. Run the bot manually (for testing)
```
python3.10 bot.py
```
💬 Example Usage
In your Telegram chat with the bot, send the following:

```
/channel @your_channel_username
/time Jul25, 14:00
This is message 1
This is message 2
/timenow
```
🕐 The bot will schedule the messages at:

Jul 25, 14:00

Jul 25, 14:10

Jul 25, 14:20

...

Each new message is delayed 10 minutes from the previous one.
