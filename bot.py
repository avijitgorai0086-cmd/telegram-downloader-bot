import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from yt_dlp import YoutubeDL

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway Variable
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
# =========================================


def get_format(type_, quality):
    if type_ == "audio":
        return "bestaudio"
    if quality == "360p":
        return "bestvideo[height<=360]+bestaudio/best"
    if quality == "480p":
        return "bestvideo[height<=480]+bestaudio/best"
    if quality == "720p":
        return "bestvideo[height<=720]+bestaudio/best"
    return "best"


def ytdlp_download(link, type_, quality):
    options = {
        "format": get_format(type_, quality),
        "outtmpl": os.path.join(DOWNLOAD_PATH, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    # Audio -> MP3 conversion
    if type_ == "audio":
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(link, download=True)

        # ✅ correct output filename
        if type_ == "audio":
            filename = os.path.join(DOWNLOAD_PATH, f"{info['id']}.mp3")
        else:
            filename = ydl.prepare_filename(info)

    return filename


# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Link bhejo\n"
        "🎥 Video | 🎵 Audio (MP3)"
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link"] = update.message.text.strip()

    buttons = [
        [InlineKeyboardButton("🎥 Video", callback_data="type|video")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="type|audio")],
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

    if type_ == "audio":
        await query.edit_message_text("🎵 Downloading audio...")
        await download_file(query, context)
        return

    buttons = [
        [InlineKeyboardButton("360p", callback_data="quality|360p")],
        [InlineKeyboardButton("480p", callback_data="quality|480p")],
        [InlineKeyboardButton("720p", callback_data="quality|720p")],
        [InlineKeyboardButton("Best", callback_data="quality|best")],
    ]

    await query.edit_message_text(
        "Select video quality:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def select_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["quality"] = query.data.split("|")[1]
    await query.edit_message_text("🎥 Downloading video...")
    await download_file(query, context)


async def download_file(query, context):
    chat = query.message.chat
    filename = None

    try:
        filename = await asyncio.to_thread(
            ytdlp_download,
            context.user_data["link"],
            context.user_data.get("type", "video"),
            context.user_data.get("quality", "best"),
        )

        # ✅ Most stable: send by path (no read error)
        await chat.send_document(document=filename)
        await chat.send_message("✅ Download completed")

    except Exception as e:
        await chat.send_message(f"❌ Error:\n{e}")

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)


# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN missing. Set BOT_TOKEN in Railway Variables.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(select_type, r"^type\|"))
    app.add_handler(CallbackQueryHandler(select_quality, r"^quality\|"))

    print("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
