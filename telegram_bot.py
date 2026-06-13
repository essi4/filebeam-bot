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

# --- تنظیمات ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # توکن ربات از BotFather

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- آپلود به Catbox ---
def upload_to_catbox(file_bytes: bytes, filename: str) -> str:
    """فایل رو به Catbox.moe آپلود میکنه و لینک برمیگردونه"""
    url = "https://catbox.moe/user/api.php"
    files = {
        "fileToUpload": (filename, file_bytes),
    }
    data = {
        "reqtype": "fileupload",
    }
    response = requests.post(url, files=files, data=data, timeout=60)
    response.raise_for_status()
    return response.text.strip()


# --- هندلر /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "هر فایلی برام بفرست تا لینک دانلود مستقیمش رو بهت بدم.\n\n"
        "📎 فایل‌های پشتیبانی‌شده: تصویر، ویدیو، سند، صدا و هر فایل دیگه‌ای\n"
        "⚠️ حداکثر حجم: 200MB"
    )


# --- هندلر فایل ---
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # تشخیص نوع فایل
    if message.document:
        file = message.document
        filename = file.file_name or "file"
    elif message.photo:
        file = message.photo[-1]  # بهترین کیفیت
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
    elif message.video_note:
        file = message.video_note
        filename = "video_note.mp4"
    elif message.sticker:
        file = message.sticker
        filename = "sticker.webp"
    else:
        await message.reply_text("❌ این نوع فایل پشتیبانی نمیشه.")
        return

    # بررسی حجم (200MB)
    if hasattr(file, 'file_size') and file.file_size and file.file_size > 200 * 1024 * 1024:
        await message.reply_text("❌ حجم فایل بیشتر از 200MB هست!")
        return

    status_msg = await message.reply_text("⏳ در حال آپلود...")

    try:
        # دانلود فایل از تلگرام
        tg_file = await file.get_file()
        file_bytes = await tg_file.download_as_bytearray()

        # آپلود به Catbox
        link = upload_to_catbox(bytes(file_bytes), filename)

        await status_msg.edit_text(
            f"✅ آپلود شد!\n\n"
            f"🔗 لینک دانلود:\n`{link}`\n\n"
            f"📁 نام فایل: `{filename}`",
            parse_mode="Markdown"
        )

    except requests.RequestException as e:
        logger.error(f"خطا در آپلود: {e}")
        await status_msg.edit_text("❌ خطا در آپلود به Catbox. دوباره امتحان کن.")
    except Exception as e:
        logger.error(f"خطای کلی: {e}")
        await status_msg.edit_text("❌ یه خطایی پیش اومد. دوباره امتحان کن.")


# --- هندلر /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 راهنما:\n\n"
        "1️⃣ فایلت رو بفرست\n"
        "2️⃣ ربات آپلودش میکنه به Catbox.moe\n"
        "3️⃣ لینک مستقیم دانلود میگیری\n\n"
        "⚠️ فایل‌های آپلودشده روی Catbox تا وقتی که دسترسی داشته باشن نگه داشته میشن."
    )


# --- main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(
        filters.Document.ALL
        | filters.PHOTO
        | filters.VIDEO
        | filters.AUDIO
        | filters.VOICE
        | filters.VIDEO_NOTE
        | filters.Sticker.ALL,
        handle_file
    ))

    print("✅ ربات شروع به کار کرد...")
    app.run_polling()


if __name__ == "__main__":
    main()
