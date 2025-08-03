import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes
)
from gspread import service_account

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
if not TELEGRAM_TOKEN or not SPREADSHEET_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or SPREADSHEET_ID environment variables")

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = service_account.from_service_account_info(os.getenv("GOOGLE_CREDENTIALS", "{}"))
client = creds.with_scopes(SCOPE)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен. Отправьте заявку в формате JSON (name, email, guests).")

async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text
    try:
        parsed = json.loads(data)
        if not all(k in parsed for k in ["name", "email", "guests"]):
            await update.message.reply_text("Ошибка: нужны поля name, email, guests.")
            return
        name, email, guests = parsed["name"], parsed["email"], parsed["guests"]
        context.user_data["current"] = {"name": name, "email": email, "guests": guests}
        keyboard = [[InlineKeyboardButton("✅ Принять", callback_data="accept"),
                     InlineKeyboardButton("❌ Отклонить", callback_data="decline")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🍽 Новая заявка:\nИмя: {name}\nEmail: {email}\nГостей: {guests}",
            reply_markup=reply_markup
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        await update.message.reply_text("Ошибка: неверный JSON формат.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("Ошибка обработки.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    data = context.user_data.get("current", {})

    if action == "accept":
        await query.edit_message_text("Введите номер стола:")
        context.user_data["status"] = "accepted"
        context.user_data["timeout"] = 300  # 5-minute timeout

    elif action == "decline":
        await query.edit_message_text("❌ Заявка отклонена.")
        await query.message.reply_text("Заявка записана.")
        sheet.append_row([data.get("name"), data.get("email"), data.get("guests"), "Отклонено", "-"])

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("status") == "accepted":
        table = update.message.text
        data = context.user_data.get("current", {})
        sheet.append_row([data.get("name"), data.get("email"), data.get("guests"), "Принято", table])
        await update.message.reply_text(f"✅ Заявка принята. Стол: {table}")
        context.user_data.clear()  # Reset user data
    else:
        await update.message.reply_text("Сначала примите заявку через кнопку.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.Regex(r'^{.*}$'), handle_webhook))
    app.add_error_handler(lambda update, context: logger.error(f"Error: {context.error}"))

    # For Render, use polling (webhook setup requires additional config)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
