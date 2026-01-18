import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---- Flask web server (Render ke PORT ke liye) ----
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# ---- Telegram Bot ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running on Render!")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in Render env vars.")

    # Start Flask server in background
    threading.Thread(target=run_flask).start()

    # Start Telegram polling
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    print("✅ Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
