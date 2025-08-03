import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from google_api import append_to_sheet

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен и готов принимать заявки.")

# Обработка входящих JSON-заявок
async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text
    try:
        parsed = json.loads(data)
        name = parsed.get("name")
        email = parsed.get("email")
        guests = parsed.get("guests")

        context.user_data["current"] = {"name": name, "email": email, "guests": guests}
        keyboard = [[
            InlineKeyboardButton("✅ Принять", callback_data="accept"),
            InlineKeyboardButton("❌ Отклонить", callback_data="decline")
        ]]
        await update.message.reply_text(
            f"🍽 Новая заявка:\nИмя: {name}\nEmail: {email}\nГостей: {guests}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text("Ошибка обработки данных: " + str(e))

# Кнопки Принять/Отклонить
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

# Обработка номера стола после "Принято"
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("status") == "accepted":
        table = update.message.text
        data = context.user_data.get("current", {})
        append_to_sheet(SPREADSHEET_ID, [
            data.get("name"), data.get("email"), data.get("guests"), "Принято", table
        ])
        await update.message.reply_text(f"✅ Заявка принята. Стол: {table}")
        context.user_data["status"] = None

# Запуск приложения
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_webhook))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
