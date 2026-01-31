from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
import requests
import json

TOKEN_BOT = '7287099082:AAG59yMYRRqLFIKwmpIGaA3iWuJBYGIYI1A'
bot = TeleBot(TOKEN_BOT)

favs = {}

def create_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Искать фильм"))
    keyboard.add(KeyboardButton("Избранное"))
    return keyboard

def create_search_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Вернуться в главное меню"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in favs:
        favs[chat_id] = []
    bot.send_message(
        chat_id,
        "Здравствуйте!Нажмите «Искать фильм», чтобы найти фильм по названию.Нажмите «Избранное», чтобы посмотреть сохранённые фильмы.",
        reply_markup=create_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "Искать фильм")
def search_movie(message):
    chat_id = message.chat.id
    msg = bot.send_message(
        chat_id,
        "Введите название фильма:",
        reply_markup=create_search_keyboard()
    )
    bot.register_next_step_handler(msg, process_movie_search)

@bot.message_handler(func=lambda message: message.text == "Избранное")
def show_favorites(message):
    chat_id = message.chat.id
    if not favs[chat_id]:
        bot.send_message(chat_id, "У вас пока нет избранных фильмов.", reply_markup=create_main_keyboard())
        return

    for movie in favs[chat_id]:
        bot.send_photo(
            chat_id,
            movie['poster'],
            caption=f"<b>{movie['title']}</b> ({movie['year']})\n"
                    f"Рейтинг: {movie['rating']}\n"
                    f"{movie['plot']}",
            parse_mode='HTML'
        )
    bot.send_message(chat_id, "Вот ваши избранные фильмы.", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "Вернуться в главное меню")
def return_to_main(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Главное меню:", reply_markup=create_main_keyboard())

def process_movie_search(message):
    chat_id = message.chat.id
    title = message.text.strip()

    if title.lower() == "вернуть в главное меню":
        return_to_main(message)
        return

    movie_data = get_movie_info(title)

    if movie_data:
        bot.send_photo(
            chat_id,
            movie_data['poster'],
            caption=f"<b>{movie_data['title']}</b> ({movie_data['year']})\n"
                    f"Рейтинг: {movie_data['rating']}\n"
                    f"{movie_data['plot']}",
            parse_mode='HTML'
        )

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton(f"Добавить '{movie_data['title']}' в избранное"))
        keyboard.add(KeyboardButton("Искать другой фильм"))
        keyboard.add(KeyboardButton("Вернуться в главное меню"))
        bot.send_message(chat_id, "Что хотите сделать?", reply_markup=keyboard)

        bot.register_next_step_handler(message, lambda m: handle_favorite_choice(m, movie_data))
    else:
        bot.send_message(
            chat_id,
            "Фильм не найден. Попробуйте другое название.",
            reply_markup=create_search_keyboard()
        )
        bot.register_next_step_handler(message, process_movie_search)

def handle_favorite_choice(message, movie_data):
    chat_id = message.chat.id
    text = message.text

    if text.startswith("Добавить '") and text.endswith("' в избранное"):
        if movie_data not in favs[chat_id]:
            favs[chat_id].append(movie_data)
            bot.send_message(chat_id, "Фильм добавлен в избранное!", reply_markup=create_main_keyboard())
        else:
            bot.send_message(chat_id, "Этот фильм уже в избранном.", reply_markup=create_main_keyboard())
    elif text == "Искать другой фильм":
        search_movie(message)
    elif text == "Вернуться в главное меню":
        return_to_main(message)
    else:
        bot.send_message(chat_id, "Неизвестная команда.", reply_markup=create_main_keyboard())

def get_movie_info(title):
    api_key = '3112916e'  
    base_url = 'http://www.omdbapi.com/'
    params = {'t': title, 'apikey': api_key, 'plot': 'short', 'r': 'json'}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['Response'] == 'True':
            return {
                'title': data['Title'],
                'year': data['Year'],
                'rating': data.get('imdbRating', 'N/A'),
                'plot': data['Plot'],
                'poster': data['Poster'] if data['Poster'] != 'N/A' else 'https://via.placeholder.com/300x450?text=No+Poster'
            }
    except requests.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")

    return None

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)
