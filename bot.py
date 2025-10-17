import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
import os
import httpx
from typing import AsyncIterator
import requests

# ==================== КОНФИГУРАЦИЯ ====================
# TODO: Замените на ваши реальные данные API
BOT_TOKEN = "8220896552:AAFqZ28ylYmItLQLmQHOqTGWDCRtbSLwD5U"

# Конфигурация Flexar API
FLEXAR_BASE_URL = "https://app.flexar.al"  # TODO: Замените на ваш URL
FLEXAR_API_KEY = "your_flexar_api_key_here"  # TODO: Замените на ваш API ключ
FLEXAR_CHAT_NAME = "MovieRecommendationBot"  # TODO: Замените на имя вашего чата в Flexar
FLEXAR_AGENT_ID = "your_agent_id_here"  # TODO: Замените на ID агента если используете агентов

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== КЛАССЫ ДЛЯ РАБОТЫ С API ====================

class FlexarAPIClient:
    """Клиент для работы с API Flexar"""
    
    def __init__(self):
        self.base_url = f"{FLEXAR_BASE_URL.rstrip('/')}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {FLEXAR_API_KEY}",
            "Content-Type": "application/json"
        }
    
    async def get_chat_id(self) -> str:
        """Получает ID чата по имени"""
        # TODO: Реализовать по гайду - шаг 1 для чатов
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/chats",
                    params={"name": FLEXAR_CHAT_NAME},
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 0 and data.get("data"):
                    return data["data"][0]["id"]
                else:
                    raise Exception("Чат не найден")
        except Exception as e:
            print(f"Ошибка получения chat_id: {e}")
            return ""
    
    async def create_session(self, chat_id: str, session_name: str = "Telegram Session") -> str:
        """Создает новую сессию"""
        # TODO: Реализовать по гайду - шаг 2 для чатов
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chats/{chat_id}/sessions",
                    json={"name": session_name},
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == 0 and data.get("data"):
                    return data["data"]["id"]
                else:
                    raise Exception("Ошибка создания сессии")
        except Exception as e:
            print(f"Ошибка создания сессии: {e}")
            return ""
    
    async def ask_question_stream(self, chat_id: str, session_id: str, question: str) -> str:
        """Задает вопрос и получает ответ в потоковом режиме"""
        # TODO: Реализовать по гайду - шаг 3 для чатов (потоковый режим)
        try:
            payload = {
                "question": question,
                "session_id": session_id,
                "stream": True
            }
            
            full_answer = ""
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chats/{chat_id}/completions",
                    json=payload,
                    headers={**self.headers, "Accept": "text/event-stream"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith('data:'):
                            data_str = line[5:].strip()
                            if data_str in ['true', '[DONE]']:
                                break
                            try:
                                event_data = json.loads(data_str)
                                if event_data.get("code") == 0:
                                    answer_data = event_data.get("data", {})
                                    if isinstance(answer_data, dict):
                                        answer = answer_data.get("answer", "")
                                        if answer:
                                            full_answer += answer
                            except json.JSONDecodeError:
                                continue
            
            return full_answer if full_answer else "Не удалось получить ответ"
            
        except Exception as e:
            print(f"Ошибка при запросе к API: {e}")
            return "Извините, произошла ошибка при обработке запроса"
    
    async def ask_question_direct(self, question: str) -> str:
        """Упрощенный метод для запроса к API"""
        # TODO: Можно реализовать через агентов если предпочтительнее
        try:
            chat_id = await self.get_chat_id()
            if not chat_id:
                return "Ошибка: не удалось найти чат"
            
            session_id = await self.create_session(chat_id)
            if not session_id:
                return "Ошибка: не удалось создать сессию"
            
            return await self.ask_question_stream(chat_id, session_id, question)
            
        except Exception as e:
            print(f"Общая ошибка API: {e}")
            return "Извините, сервис временно недоступен"

# ==================== ИНИЦИАЛИЗАЦИЯ КЛИЕНТА ====================
api_client = FlexarAPIClient()

# ==================== ФУНКЦИИ МЕНЮ ====================

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🎬 Рекомендовать фильм", callback_data="recommend"),
        InlineKeyboardButton("🎭 Выбрать жанр", callback_data="choose_genre"),
        InlineKeyboardButton("⭐ Рекомендация по настроению", callback_data="mood_recommend"),
        InlineKeyboardButton("📚 Мои рекомендации", callback_data="my_movies"), 
        InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
    )
    return markup

def genre_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🔫 Боевик", callback_data="genre_action"),
        InlineKeyboardButton("😂 Комедия", callback_data="genre_comedy"),
        InlineKeyboardButton("💖 Драма", callback_data="genre_drama"),
        InlineKeyboardButton("🚀 Фантастика", callback_data="genre_scifi"),
        InlineKeyboardButton("👻 Ужасы", callback_data="genre_horror"),
        InlineKeyboardButton("🔍 Детектив", callback_data="genre_mystery"),
        InlineKeyboardButton("↩️ Назад", callback_data="back_main")
    )
    return markup

def mood_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("😊 Веселое", callback_data="mood_happy"),
        InlineKeyboardButton("😢 Грустное", callback_data="mood_sad"),
        InlineKeyboardButton("🤔 Задумчивое", callback_data="mood_thoughtful"),
        InlineKeyboardButton("🎉 Праздничное", callback_data="mood_celebratory"),
        InlineKeyboardButton("🔮 Таинственное", callback_data="mood_mysterious"),
        InlineKeyboardButton("↩️ Назад", callback_data="back_main")
    )
    return markup

# ==================== ОБРАБОТЧИКИ СООБЩЕНИЙ ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для рекомендации фильмов 🎬\n\n"
        "Я использую AI чтобы подобрать идеальный фильм под ваше настроение и предпочтения!",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "recommend":
        bot.edit_message_text(
            "🎬 Отлично! Давайте подберем фильм.\n\n"
            "Опишите, какой фильм вы хотите посмотреть?\n"
            "Например:\n"
            "• 'Комедия про дружбу'\n" 
            "• 'Научная фантастика с пришельцами'\n"
            "• 'Что-то романтическое для вечера'",
            chat_id, message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("↩️ Назад", callback_data="back_main")
            )
        )
    
    elif call.data == "choose_genre":
        bot.edit_message_text(
            "🎭 Выберите жанр:",
            chat_id, message_id,
            reply_markup=genre_menu()
        )
    
    elif call.data == "mood_recommend":
        bot.edit_message_text(
            "⭐ Какое у вас сегодня настроение?",
            chat_id, message_id,
            reply_markup=mood_menu()
        )
    
    elif call.data == "my_movies":
        bot.edit_message_text(
            "📚 Здесь будут сохраненные ваши рекомендации\n\n"
            "⚙️ Функция в разработке...",
            chat_id, message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("↩️ Назад", callback_data="back_main")
            )
        )
    
    elif call.data == "help":
        bot.edit_message_text(
            "ℹ️ Помощь по боту:\n\n"
            "• 🎬 Рекомендовать фильм - AI подберет фильм по вашему описанию\n"
            "• 🎭 Выбрать жанр - фильмы по конкретному жанру\n"
            "• ⭐ Рекомендация по настроению - фильмы под ваше настроение\n"
            "• 📚 Мои рекомендации - история ваших запросов\n\n"
            "Просто напишите что вы хотите посмотреть!",
            chat_id, message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("↩️ Назад", callback_data="back_main")
            )
        )
    
    elif call.data == "back_main":
        bot.edit_message_text(
            "Главное меню:",
            chat_id, message_id,
            reply_markup=main_menu()
        )
    
    elif call.data.startswith("genre_"):
        genre = call.data.replace("genre_", "")
        genre_names = {
            "action": "боевик",
            "comedy": "комедия", 
            "drama": "драма",
            "scifi": "научная фантастика",
            "horror": "ужасы",
            "mystery": "детектив"
        }
        
        bot.edit_message_text(
            f"🔍 Ищу {genre_names.get(genre, 'фильмы')}...",
            chat_id, message_id
        )
        
        # Асинхронный запрос к API
        asyncio.run(send_genre_recommendation(chat_id, genre_names.get(genre, "фильм")))
    
    elif call.data.startswith("mood_"):
        mood = call.data.replace("mood_", "")
        mood_names = {
            "happy": "веселое",
            "sad": "грустное", 
            "thoughtful": "задумчивое",
            "celebratory": "праздничное",
            "mysterious": "таинственное"
        }
        
        bot.edit_message_text(
            f"🔍 Подбираю фильм под {mood_names.get(mood, 'ваше')} настроение...",
            chat_id, message_id
        )
        
        # Асинхронный запрос к API
        asyncio.run(send_mood_recommendation(chat_id, mood_names.get(mood, "настроение")))

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С API ====================

async def send_genre_recommendation(chat_id: int, genre: str):
    """Отправляет рекомендацию по жанру"""
    question = f"Порекомендуй 3 популярных фильма в жанре {genre}. Для каждого укажи год выпуска и краткое описание сюжета."
    
    bot.send_chat_action(chat_id, "typing")
    
    try:
        answer = await api_client.ask_question_direct(question)
        
        # Форматируем ответ
        formatted_answer = f"🎬 Рекомендации по жанру {genre}:\n\n{answer}\n\nЧто еще вас интересует?"
        
        bot.send_message(
            chat_id,
            formatted_answer,
            reply_markup=main_menu()
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            "Извините, произошла ошибка при поиске рекомендаций 😔",
            reply_markup=main_menu()
        )

async def send_mood_recommendation(chat_id: int, mood: str):
    """Отправляет рекомендацию по настроению"""
    question = f"Порекомендуй 3 фильма которые подходят для {mood} настроения. Для каждого укажи жанр, год выпуска и почему он подходит для этого настроения."
    
    bot.send_chat_action(chat_id, "typing")
    
    try:
        answer = await api_client.ask_question_direct(question)
        
        # Форматируем ответ
        formatted_answer = f"⭐ Фильмы для {mood} настроения:\n\n{answer}\n\nНайдем что-то еще?"
        
        bot.send_message(
            chat_id,
            formatted_answer,
            reply_markup=main_menu()
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            "Извините, произошла ошибка при поиске рекомендаций 😔",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Обрабатывает текстовые сообщения с запросами фильмов"""
    user_input = message.text.strip()
    chat_id = message.chat.id
    
    if len(user_input) < 3:
        bot.send_message(
            chat_id,
            "Пожалуйста, опишите подробнее, какой фильм вы ищете 🎬",
            reply_markup=main_menu()
        )
        return
    
    bot.send_chat_action(chat_id, "typing")
    
    # Отправляем сообщение о поиске
    search_msg = bot.send_message(
        chat_id,
        f"🔍 Ищу фильмы по запросу: '{user_input}'..."
    )
    
    # Асинхронный запрос к API
    async def process_request():
        try:
            question = f"Порекомендуй 3 фильма по запросу: '{user_input}'. Для каждого укажи год выпуска, жанр и краткое описание сюжета. Ответ должен быть структурированным и информативным."
            
            answer = await api_client.ask_question_direct(question)
            
            formatted_answer = f"🎯 Вот что я нашел по запросу '{user_input}':\n\n{answer}\n\nПонравились рекомендации?"
            
            bot.edit_message_text(
                formatted_answer,
                chat_id,
                search_msg.message_id,
                reply_markup=main_menu()
            )
            
        except Exception as e:
            bot.edit_message_text(
                "Извините, произошла ошибка при поиске фильмов 😔\nПопробуйте еще раз или выберите из меню.",
                chat_id,
                search_msg.message_id,
                reply_markup=main_menu()
            )
    
    asyncio.run(process_request())

# ==================== ЗАПУСК БОТА ====================

if __name__ == "__main__":
    print("🎬 Бот рекомендаций фильмов запущен! 🚀")
    print("⚠️  Не забудьте настроить API данные в конфигурации")
    bot.infinity_polling()