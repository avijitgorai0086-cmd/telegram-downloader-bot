import os
import asyncio
from yt_dlp import YoutubeDL

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in Render Environment Variables.")

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# yt-dlp config
YDL_OPTS = {
    "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
    "format": "mp4/bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}


# =====================
# COMMANDS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot Started!\n\nSend me any video link (YouTube etc.) and I'll download it."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Usage:\n"
        "/start - Start bot\n"
        "/help - Help\n\n"
        "Just send a video link."
    )


# =====================
# DOWNLOAD FUNCTION
# =====================
def download_video(url: str):
    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    url = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Downloading... wait...")

    try:
        # run download in thread (non-blocking)
        file_path = await asyncio.to_thread(download_video, url)

        await msg.edit_text("✅ Download complete! Uploading...")

        # send file
        if os.path.exists(file_path):
            await update.message.reply_document(document=open(file_path, "rb"))
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Download file not found!")

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error:\n{e}")


# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Any message treated as link
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("✅ Bot running...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
