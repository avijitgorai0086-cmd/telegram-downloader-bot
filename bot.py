import os
import asyncio
from yt_dlp import YoutubeDL

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------- Configuration -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render/Env variable
DOWNLOAD_PATH = "downloads"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)


# ------------------- Helper Functions -------------------
def ytdlp_download(link: str, type_: str = "video", quality: str = "best"):
    """
    Download video/audio using yt_dlp
    Returns the final downloaded file path
    """

    # Formats
    if type_ == "audio":
        fmt = "bestaudio/best"
    else:
        if quality == "best":
            fmt = "bestvideo+bestaudio/best"
        else:
            # example: 720p => height<=720
            fmt = f"bestvideo[height<={quality}]+bestaudio/best"

    options = {
        "format": fmt,
        "outtmpl": os.path.join(DOWNLOAD_PATH, "%(title).200s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        # ensures best merge if possible
        "merge_output_format": "mp4",
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)

        # ✅ Sometimes yt-dlp downloads audio with different ext than prepared filename
        if not os.path.exists(filename):
            base = os.path.splitext(filename)[0]
            for ext in [".m4a", ".webm", ".mp3", ".opus", ".aac", ".ogg", ".mp4"]:
                if os.path.exists(base + ext):
                    filename = base + ext
                    break

    return filename


async def safe_reply(update: Update, text: str):
    if update.message:
        await update.message.reply_text(text)
    else:
        await update.effective_chat.send_message(text)


# ------------------- Bot Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(
        update,
        "✅ Welcome!\n\nSend me any link (YouTube / Instagram / Facebook / Terabox etc.)\n"
        "Then choose Video or Audio to download.",
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    # Save user link
    context.user_data["link"] = link
    context.user_data.pop("type", None)
    context.user_data.pop("quality", None)

    buttons = [
        [InlineKeyboardButton("🎥 Video", callback_data="type|video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="type|audio")],
    ]

    await update.message.reply_text(
        "Select download type:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    type_ = query.data.split("|")[1]
    context.user_data["type"] = type_

    if type_ == "video":
        buttons = [
            [InlineKeyboardButton("360p", callback_data="quality|360")],
            [InlineKeyboardButton("480p", callback_data="quality|480")],
            [InlineKeyboardButton("720p", callback_data="quality|720")],
            [InlineKeyboardButton("Best", callback_data="quality|best")],
        ]
        await query.edit_message_text(
            "Select video quality:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        await query.edit_message_text("🎵 Downloading audio...")
        await download_file(query, context)


async def select_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data.split("|")[1]
    context.user_data["quality"] = quality

    await query.edit_message_text(f"🎥 Downloading video in {quality}p...")
    await download_file(query, context)


async def download_file(query, context: ContextTypes.DEFAULT_TYPE):
    link = context.user_data.get("link")
    type_ = context.user_data.get("type", "video")
    quality = context.user_data.get("quality", "best")

    filename = None
    try:
        await query.message.chat.send_message("⏳ Please wait... Downloading started.")

        filename = await asyncio.to_thread(ytdlp_download, link, type_, quality)

        if not filename or not os.path.exists(filename):
            raise FileNotFoundError("Downloaded file not found.")

        # Send file
        if type_ == "video":
            await query.message.chat.send_video(video=open(filename, "rb"))
        else:
            await query.message.chat.send_audio(audio=open(filename, "rb"))

        await query.message.chat.send_message("✅ Download completed!")
    except Exception as e:
        await query.message.chat.send_message(f"❌ Error:\n{e}")
    finally:
        # Cleanup
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
        except:
            pass


# ------------------- Main Function -------------------
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing. Please set BOT_TOKEN in environment variables.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(select_type, pattern=r"^type\|"))
    app.add_handler(CallbackQueryHandler(select_quality, pattern=r"^quality\|"))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
