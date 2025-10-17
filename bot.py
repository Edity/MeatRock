import telebot, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🎬 Рекомендовать фильм", callback_data="recommend"),
        InlineKeyboardButton("📚 Мои фильмы", callback_data="my_movies"), 
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для рекомендации фильмов 🎬",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "recommend":
        bot.edit_message_text(
            "Скоро здесь будут рекомендации! 🎯",
            call.message.chat.id,
            call.message.message_id
        )
    elif call.data == "my_movies":
        bot.edit_message_text(
            "Здесь будет ваш список фильмов 📚",
            call.message.chat.id,
            call.message.message_id
        )
    elif call.data == "help":
        bot.edit_message_text(
            "Помощь по боту ℹ️",
            call.message.chat.id,
            call.message.message_id
        )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_message(
        message.chat.id,
        "Используйте кнопки меню для навигации 📱",
        reply_markup=main_menu()
    )

if __name__ == "__main__":
    print("Бот запущен! 🚀")
    bot.infinity_polling()