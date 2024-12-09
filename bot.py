from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import asyncio

TOKEN = "7943976877:AAFTnXwKbrxgJdi3mhv5xe2N5zK52CKgZ7o"

# Функція для обробки команди /start
async def start(update: Update, context):
    # Створення кнопки "Subscribe"
    keyboard = [
        [InlineKeyboardButton("Subscribe to Alerts", callback_data="subscribe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Надсилання повідомлення з кнопкою
    await update.message.reply_text(
        "Hello! This is Crypto Bot. Click below to subscribe to high transaction alerts.",
        reply_markup=reply_markup
    )

# Обробка кліку на кнопку "Subscribe"
async def button_click(update: Update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    # Додавання підписника
    context.application.bot_data.setdefault("subscribers", set()).add(chat_id)

    # Підтвердження дії користувача
    await query.answer("You have subscribed to alerts!")
    await query.edit_message_text("You are now subscribed to high transaction alerts.")

# Відправка повідомлень із черги
async def send_notifications(queue, application):
    while True:
        if not queue.empty():
            message = queue.get()
            for chat_id in application.bot_data["subscribers"]:
                await application.bot.send_message(chat_id=chat_id, text=message)
        await asyncio.sleep(1)

# Основна функція запуску бота
def run_bot(queue):
    # Створення застосунку бота
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data["subscribers"] = set()

    # Додавання обробників
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click, pattern="^subscribe$"))

    # Отримання існуючого event loop
    loop = asyncio.get_event_loop()

    # Додавання задачі для обробки черги
    loop.create_task(send_notifications(queue, app))

    # Запуск бота
    print("Бот працює...")
    loop.run_until_complete(app.run_polling())

