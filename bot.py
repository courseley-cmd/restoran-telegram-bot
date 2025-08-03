import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes
)
from google_api import append_to_sheet

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен и готов принимать заявки.")

async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text
    try:
        parsed = json.loads(data)
        name = parsed.get("name")
        email = parsed.get("email")
        guests = parsed.get("guests")

        context.user_data["current"] = {"name": name, "email": email, "guests": guests}
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data="accept"),
                InlineKeyboardButton("❌ Отклонить", callback_data="decline")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"""🍽 Новая заявка:
Имя: {name}
Email: {email}
Гостей: {guests}""",
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text("Ошибка обработки данных: " + str(e))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "accept":
        await query.edit_message_text("Введите номер стола:")
        context.user_data["status"] = "accepted"

    elif action == "decline":
        await query.edit_message_text("❌ Заявка отклонена.")
        data = context.user_data.get("current", {})
        append_to_sheet(SPREADSHEET_ID, [
            data.get("name"), data.get("email"), data.get("guests"), "Отклонено", "-"
        ])

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("status") == "accepted":
        table = update.message.text
        data = context.user_data.get("current", {})
        append_to_sheet(SPREADSHEET_ID, [
            data.get("name"), data.get("email"), data.get("guests"), "Принято", table
        ])
        await update.message.reply_text(f"✅ Заявка принята. Стол: {table}")
        context.user_data["status"] = None

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_webhook))

    app.run_polling()

if __name__ == "__main__":
    main()
