from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

BOT_TOKEN = "YOUR_BOT_TOKEN"

# Главное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎬 Рекомендовать фильм", callback_data="recommend")],
        [InlineKeyboardButton("📚 Мои фильмы", callback_data="my_movies")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Привет! Я бот для рекомендации фильмов 🎬",
        reply_markup=main_menu()
    )

# Обработка кнопок
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "recommend":
        await query.edit_message_text("Скоро здесь будут рекомендации! 🎯")
    elif query.data == "my_movies":
        await query.edit_message_text("Здесь будет ваш список фильмов 📚")
    elif query.data == "help":
        await query.edit_message_text("Помощь по боту ℹ️")

# Обработка текстовых сообщений
async def text_handler(update: Update, context):
    await update.message.reply_text(
        "Используйте кнопки меню для навигации",
        reply_markup=main_menu()
    )

# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))
    
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()