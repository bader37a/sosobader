import os
import logging
import yt_dlp
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد سجل الأخطاء لتتبع المشاكل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# توكن البوت
TOKEN = '7366837653:AAF2mYk0w_6whKkC_ReqPZDkn_XB8m-OEEA'

# تنظيف اسم الملف وإنشاء اسم فريد
def sanitize_filename():
    return str(uuid.uuid4())

# وظيفة لتنزيل الفيديو باستخدام yt-dlp
def download_video(url, platform):
    directory = f"{platform}_downloads"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # إعدادات yt-dlp
    options = {
        'outtmpl': f'{directory}/{sanitize_filename()}.%(ext)s',
        'format': 'best',
        'quiet': True,
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    # تخصيص إعدادات لمنصة X (Twitter)
    if platform == 'twitter':
        options['format'] = 'best'

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# وظيفة لحذف الفيديو
async def delete_file(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    file_path = job.data
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"تم حذف الملف: {file_path}")

# وظيفة لمعالجة الروابط
async def handle_message(update: Update, context):
    user_message = update.message.text
    try:
        platform = ''
        if "youtube.com" in user_message or "youtu.be" in user_message:
            platform = 'youtube'
        elif "instagram.com" in user_message:
            platform = 'instagram'
        elif "tiktok.com" in user_message:
            platform = 'tiktok'
        elif "twitter.com" in user_message or "x.com" in user_message:
            platform = 'twitter'
        else:
            await update.message.reply_text("المنصة غير مدعومة حاليًا.")
            return

        video_path = download_video(user_message, platform)
        await update.message.reply_text("تم التحميل بنجاح! لبى كبدتش و كبد أبيش...")

        # إرسال الفيديو
        with open(video_path, 'rb') as video:
            await update.message.reply_video(video)

        # جدولة حذف الملف بعد 10 دقائق
        context.job_queue.run_once(delete_file, 600, data=video_path)
    except yt_dlp.DownloadError:
        await update.message.reply_text("تعذر تحميل الفيديو. تأكد من صحة الرابط وحاول مرة أخرى.")
    except Exception as e:
        logger.error(f"حدث خطأ: {e}")
        await update.message.reply_text(f"حدث خطأ غير متوقع: {e}")

# وظيفة لعرض رسالة ترحيب عند بدء البوت
async def start(update: Update, context):
    await update.message.reply_text(
        "ارسلي الرابط لبى كبدتش و كبد أبيش و ثواني يكون عندك .ابي جاء ابي جاء"
    )

# معالج الأخطاء لتسجيل المشاكل
async def handle_error(update, context):
    logger.error(msg="Exception occurred:", exc_info=context.error)

# الوظيفة الرئيسية لتشغيل البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(handle_error)

    # تشغيل JobQueue
    app.job_queue.start()

    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
