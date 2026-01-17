import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from yt_dlp import YoutubeDL


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in Render Environment Variables")


DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot is running!\n\nSend me any video link (YouTube / Instagram etc.)"
    )


def download_video(url: str) -> str:
    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "format": "best",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    await update.message.reply_text("⏳ Downloading... Please wait")

    try:
        loop = asyncio.get_event_loop()
        filename = await loop.run_in_executor(None, download_video, url)

        await update.message.reply_document(document=open(filename, "rb"))
        await update.message.reply_text("✅ Done!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("✅ Bot started successfully")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
