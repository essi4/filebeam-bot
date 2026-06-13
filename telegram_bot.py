import logging
import requests
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def upload_to_catbox(file_bytes: bytes, filename: str) -> str:
    url = "https://catbox.moe/user/api.php"
    files = {"fileToUpload": (filename, file_bytes)}
    data = {"reqtype": "fileupload"}
    response = requests.post(url, files=files, data=data, timeout=60)
    response.raise_for_status()
    return response.text.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "هر فایلی برام بفرست تا لینک دانلود مستقیمش رو بهت بدم.\n\n"
        "📎 پشتیبانی از: تصویر، ویدیو، سند، صدا\n"
        "⚠️ حداکثر حجم: 200MB"
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message.document:
        file = message.document
        filename = file.file_name or "file"
    elif message.photo:
        file = message.photo[-1]
        filename = "photo.jpg"
    elif message.video:
        file = message.video
        filename = file.file_name or "video.mp4"
    elif message.audio:
        file = message.audio
        filename = file.file_name or "audio.mp3"
    elif message.voice:
        file = message.voice
        filename = "voice.ogg"
    else:
        await message.reply_text("❌ این نوع فایل پشتیبانی نمیشه.")
        return

    status_msg = await message.reply_text("⏳ در حال آپلود...")

    try:
        tg_file = await file.get_file()
        file_bytes = await tg_file.download_as_bytearray()
        link = upload_to_catbox(bytes(file_bytes), filename)
        await status_msg.edit_text(
            f"✅ آپلود شد!\n\n🔗 لینک دانلود:\n`{link}`\n\n📁 نام فایل: `{filename}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"خطا: {e}")
        await status_msg.edit_text("❌ خطایی پیش اومد. دوباره امتحان کن.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
        handle_file
    ))
    print("✅ ربات شروع به کار کرد...")
    app.run_polling()


if __name__ == "__main__":
    main()
