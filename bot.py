import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import time

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8220896552:AAFqZ28ylYmItLQLmQHOqTGWDCRtbSLwD5U"

# Конфигурация Flexar API
FLEXAR_BASE_URL = "https://vibeathon.flexar.ai"
FLEXAR_API_KEY = "flexar-ExNzcwMDA2YWI0NzExZjA5NzBlMGViYj"
FLEXAR_CHAT_ID = "15660a30ab4811f094ae0ebb9de0575e"

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== ПРОСТОЙ КЛИЕНТ API ====================

class SimpleFlexarClient:
    def __init__(self):
        self.base_url = FLEXAR_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {FLEXAR_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def ask_question(self, question: str, max_retries: int = 3) -> str:
        """Простой синхронный запрос к API с повторными попытками"""
        
        for attempt in range(max_retries):
            try:
                # Создаем сессию
                session_response = requests.post(
                    f"{self.base_url}/api/v1/chats/{FLEXAR_CHAT_ID}/sessions",
                    headers=self.headers,
                    json={"name": f"Telegram_{int(time.time())}"},
                    timeout=30
                )
                
                if session_response.status_code != 200:
                    print(f"Ошибка создания сессии: {session_response.status_code}")
                    continue
                    
                session_data = session_response.json()
                if session_data.get("code") != 0:
                    print(f"Ошибка в данных сессии: {session_data}")
                    continue
                    
                session_id = session_data["data"]["id"]
                
                # Задаем вопрос
                payload = {
                    "question": question,
                    "session_id": session_id,
                    "stream": False
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/chats/{FLEXAR_CHAT_ID}/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 503:
                    print(f"Сервер недоступен (503), попытка {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue
                    
                if response.status_code != 200:
                    print(f"Ошибка API: {response.status_code}")
                    continue
                    
                data = response.json()
                if data.get("code") == 0:
                    answer_data = data.get("data", {})
                    if isinstance(answer_data, dict):
                        return answer_data.get("answer", "Не удалось получить ответ")
                
            except requests.exceptions.Timeout:
                print(f"Таймаут запроса, попытка {attempt + 1}/{max_retries}")
                time.sleep(2)
            except requests.exceptions.ConnectionError:
                print(f"Ошибка соединения, попытка {attempt + 1}/{max_retries}")
                time.sleep(2)
            except Exception as e:
                print(f"Неизвестная ошибка: {e}, попытка {attempt + 1}/{max_retries}")
                time.sleep(2)
        
        return "Извините, сервис временно недоступен. Попробуйте позже."

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
api_client = SimpleFlexarClient()

# ==================== ИГРА "УГАДАЙ ФИЛЬМ" ====================

# Храним историю диалогов для каждого пользователя
user_conversations = {}

def get_answer_keyboard():
    """Клавиатура с кнопками ответов"""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✅ Да", callback_data="answer_yes"),
        InlineKeyboardButton("🟡 Скорее да", callback_data="answer_probably_yes"),
        InlineKeyboardButton("⚪️ Не уверен", callback_data="answer_not_sure"),
        InlineKeyboardButton("🟠 Скорее нет", callback_data="answer_probably_no"),
        InlineKeyboardButton("❌ Нет", callback_data="answer_no"),
        InlineKeyboardButton("🔄 Новая игра", callback_data="new_game")
    )
    return markup

def get_start_keyboard():
    """Клавиатура для начала игры"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎮 Начать угадывать!", callback_data="start_game")
    )
    return markup

# ==================== ОБРАБОТЧИКИ ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команды start"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Очищаем предыдущую историю
    if user_id in user_conversations:
        del user_conversations[user_id]
    
    welcome_text = (
        "🎬 Привет! Я Кинатор - волшебный угадыватель фильмов! 🧙‍♂️\n\n"
        "**Правила игры:**\n"
        "1. Загадай ЛЮБОЙ фильм\n"
        "2. Отвечай на мои вопросы кнопками\n"
        "3. Я попробую угадать твой фильм!\n\n"
        "Готов начать магический сеанс?"
    )
    
    bot.send_message(chat_id, welcome_text, reply_markup=get_start_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработчик нажатий на кнопки"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "start_game":
        # Начинаем новую игру
        start_game(chat_id, user_id)
    
    elif call.data == "new_game":
        # Начинаем новую игру
        start_game(chat_id, user_id)
    
    elif call.data.startswith("answer_"):
        # Обрабатываем ответ пользователя
        answer_type = call.data.replace("answer_", "")
        answer_map = {
            "yes": "Да",
            "probably_yes": "Скорее да", 
            "not_sure": "Не уверен",
            "probably_no": "Скорее нет",
            "no": "Нет"
        }
        
        answer_text = answer_map.get(answer_type, answer_type)
        
        # Отправляем ответ как сообщение
        bot.send_message(chat_id, f"➡️ Твой ответ: {answer_text}")
        
        # Продолжаем диалог
        continue_game(chat_id, user_id, answer_text)

def start_game(chat_id, user_id):
    """Начинает новую игру"""
    # Инициализируем историю диалога
    user_conversations[user_id] = []
    
    # Первое сообщение от бота
    first_message = (
        "Отлично! 🧙‍♂️ Загадай любой фильм и приготовься к магии...\n\n"
        "Начинаю задавать вопросы! Используй кнопки для ответов:"
    )
    
    bot.send_message(chat_id, first_message)
    
    # Запускаем первый вопрос
    ask_next_question(chat_id, user_id)

def ask_next_question(chat_id, user_id):
    """Задает следующий вопрос пользователю"""
    bot.send_chat_action(chat_id, "typing")
    
    try:
        # Получаем историю диалога
        history = user_conversations.get(user_id, [])
        
        # Создаем промпт для нейросети
        if not history:
            prompt = "Ты - Кинатор, который угадывает фильмы (пользователь не загадал ничего, ты пытаешься выбрать для него фильм по наводящим вопросам). Начни задавать первый вопрос о загаданном фильме. Задавай вопрос, на который можно ответить ТОЛЬКО Да/Нет/Скорее да/Скорее нет/Не уверен."
        else:
            # Формируем историю диалога для контекста
            conversation_text = "\n".join(history)
            prompt = f"Продолжи угадывать фильм (пользователь не загадал ничего, ты пытаешься выбрать для него фильм по наводящим вопросам) на основе этой истории:\n{conversation_text}\n\nЗадай следующий вопрос, на который можно ответить (только Да/Скорее да/ Не уверен/ Скорее нет/ нет) о фильме, если пользователь сказал что ты угадал предложи закончить игру:"
        
        # Получаем вопрос от нейросети
        question = api_client.ask_question(prompt)
        
        # Добавляем вопрос в историю
        user_conversations[user_id].append(f"Кинатор: {question}")
        
        # Отправляем вопрос с кнопками
        bot.send_message(chat_id, question, reply_markup=get_answer_keyboard())
        
    except Exception as e:
        print(f"Ошибка: {e}")
        # Запасной вопрос если API не работает
        fallback_questions = [
            "Этот фильм вышел после 2010 года?",
            "Это американский фильм?",
            "Жанр фильма - комедия?",
            "В главной роли известный актер?",
            "Фильм получил какие-то награды?",
            "Это экранизация книги?",
            "У фильма есть продолжения?"
        ]
        import random
        question = random.choice(fallback_questions)
        user_conversations[user_id].append(f"Кинатор: {question}")
        bot.send_message(chat_id, question, reply_markup=get_answer_keyboard())

def continue_game(chat_id, user_id, user_answer):
    """Продолжает игру после ответа пользователя"""
    # Добавляем ответ пользователя в историю
    user_conversations[user_id].append(f"Пользователь: {user_answer}")
    
    # Проверяем, не пора ли угадывать фильм
    history = user_conversations.get(user_id, [])
    if len(history) >= 6:  # После 3 вопросов можно попробовать угадать
        # Случайно решаем, пытаться ли угадать
        import random
        if random.random() < 0.3:  # 30% шанс попытаться угадать
            try_to_guess(chat_id, user_id)
            return
    
    # Задаем следующий вопрос
    ask_next_question(chat_id, user_id)

def try_to_guess(chat_id, user_id):
    """Пытается угадать фильм"""
    bot.send_chat_action(chat_id, "typing")
    
    try:
        # Получаем историю диалога
        history = user_conversations.get(user_id, [])
        conversation_text = "\n".join(history)
        
        # Запрашиваем угадывание у нейросети
        prompt = f"На основе этой истории диалога угадай, какой фильм загадал пользователь:\n{conversation_text}\n\nНазови фильм и объясни, почему ты так решил:"
        
        guess = api_client.ask_question(prompt)
        
        # Отправляем предположение
        bot.send_message(chat_id, f"🎯 Думаю, я знаю!\n\n{guess}\n\nЯ угадал?", reply_markup=get_answer_keyboard())
        
        # Добавляем предположение в историю
        user_conversations[user_id].append(f"Кинатор: {guess}")
        
    except Exception as e:
        print(f"Ошибка угадывания: {e}")
        # Запасное угадывание
        fallback_guesses = [
            "Думаю, ты загадал 'Интерстеллар' - фантастика про космос и время!",
            "Мне кажется, это 'Форрест Гамп' - трогательная история о жизни!",
            "Наверное, ты загадал 'Матрицу' - культовая фантастика про реальность!",
            "Возможно, это 'Побег из Шоушенка' - драма о надежде и свободе!"
        ]
        import random
        guess = random.choice(fallback_guesses)
        bot.send_message(chat_id, f"🎯 Думаю, я знаю!\n\n{guess}\n\nЯ угадал?", reply_markup=get_answer_keyboard())
        user_conversations[user_id].append(f"Кинатор: {guess}")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Обработчик текстовых сообщений (если пользователь пишет текст вместо кнопок)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Предлагаем использовать кнопки
    bot.send_message(
        chat_id, 
        "Для игры используй кнопки ответов! 🎮\n\nХочешь начать новую игру?", 
        reply_markup=get_start_keyboard()
    )

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("🎬 Кинатор запущен! 🧙‍♂️")
    print("Бот готов играть в угадайку фильмов...")
    
    # Тестовый запрос к API
    try:
        test_result = api_client.ask_question("Тестовое сообщение")
        print(f"✅ API статус: Работает")
    except Exception as e:
        print(f"⚠️ API временно недоступен, но бот будет работать с запасными ответами")
    
    print("🚀 Бот готов к игре!")
    bot.infinity_polling()