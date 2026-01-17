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

# ------------------- Configuration -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # token Render env variable se aayega
DOWNLOAD_PATH = "downloads"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ------------------- Helper Functions -------------------
async def send_error(update: Update, message: str):
    if update.message:
        await update.message.reply_text(f"❌ Failed:\n{message}")
    else:
        await update.effective_chat.send_message(f"❌ Failed:\n{message}")

def ytdlp_download(link: str, type_: str = "video", quality: str = "best"):
    options = {
        "format": quality if type_ == "video" else "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_PATH, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(link, download=True)

        # ✅ audio me yt-dlp filename kabhi kabhi change karta hai
        file_path = ydl.prepare_filename(info)

        # agar audio hai to possible ext detect
        if type_ == "audio":
            # ytdlp kabhi .webm/.m4a etc de sakta hai
            if not os.path.exists(file_path):
                # try common extensions
                base = os.path.splitext(file_path)[0]
                for ext in [".m4a", ".webm", ".mp3", ".opus"]:
                    if os.path.exists(base + ext):
                        file_path = base + ext
                        break

    return file_path

# ------------------- Bot Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Welcome!\nSend me a link (YouTube/Instagram/Facebook etc.)\nI'll download Video or Audio."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    buttons = [
        [InlineKeyboardButton("🎥 Video", callback_data="type|video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="type|audio")],
    ]
    await update.message.reply_text(
        "Select download type:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    context.user_data["link"] = link

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
        await query.edit_message_text("Downloading audio...")
        await download_file(query, context)

async def select_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data.split("|")[1]
    context.user_data["quality"] = quality

    await query.edit_message_text(
        f"Downloading video in {quality}...",
    )
    await download_file(query, context)

async def download_file(query, context: ContextTypes.DEFAULT_TYPE):
    link = context.user_data.get("link")
    type_ = context.user_data.get("type", "video")
    quality = context.user_data.get("quality", "best")

    filename = None
    try:
        if type_ == "video":
            if quality == "best":
                fmt = "bestvideo+bestaudio/best"
            else:
                # height filter
                fmt = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
        else:
            fmt = "bestaudio/best"

        filename = await asyncio.to_thread(ytdlp_download, link, type_, fmt)

        if type_ == "video":
            await query.message.chat.send_video(video=open(filename, "rb"))
        else:
            await query.message.chat.send_audio(audio=open(filename, "rb"))

        await query.message.chat.send_message("✅ Download completed!")
    except Exception as e:
        await query.message.chat.send_message(f"❌ Error: {e}")
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# ------------------- Main Function -------------------
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing. Set BOT_TOKEN in Environment Variables.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(select_type, pattern=r"^type\|"))
    app.add_handler(CallbackQueryHandler(select_quality, pattern=r"^quality\|"))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
