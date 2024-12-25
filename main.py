from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler


TOKEN = "7943976877:AAFTnXwKbrxgJdi3mhv5xe2N5zK52CKgZ7o"

# Функція для обробки команди /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Hello! This is Crypto Bot. Welcome to the bot."
    )

# Основна функція запуску бота
if __name__ == "__main__":
    # Створення застосунку бота
    app = ApplicationBuilder().token(TOKEN).build()
    # Додавання обробників
    app.add_handler(CommandHandler("start", start))
    # Запуск бота
    print("Бот працює...")
    app.run_polling()
