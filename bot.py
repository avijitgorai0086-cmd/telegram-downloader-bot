import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running on Render!")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in Render env vars.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("✅ Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
