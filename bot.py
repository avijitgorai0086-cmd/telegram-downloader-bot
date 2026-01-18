import os
import threading
from flask import Flask

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app_flask = Flask(__name__)

# ✅ Web route so Render doesn't show Not Found
@app_flask.route("/")
def home():
    return "✅ Bot is alive!", 200


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running on Render!")


def run_bot():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in Render env vars.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("✅ Bot started...")
    app.run_polling()


if __name__ == "__main__":
    # ✅ Run bot in background thread
    threading.Thread(target=run_bot).start()

    # ✅ Flask runs on Render PORT
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
