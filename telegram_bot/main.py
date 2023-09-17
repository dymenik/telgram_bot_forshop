import telebot
from telebot import types

bot = telebot.TeleBot("Ваш токен")

@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет {message.from_user.first_name}, данный бот предназначен для добавления и удаления товаров в группе!'
    bot.send_message(message.chat.id, mess)

    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    add_product_button = types.KeyboardButton('Добавить товар')
    delete_product_button = types.KeyboardButton('Удалить товар')
    view_products_button = types.KeyboardButton('Просмотреть товары')
    info_button = types.KeyboardButton('Информация')
    clear_posts_button = types.KeyboardButton('Очистить посты')
    keyboard.add(add_product_button, delete_product_button, view_products_button, info_button, clear_posts_button)

    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=keyboard)

posts = {}
users = {}
user_state = {}

@bot.message_handler(func=lambda message: message.text == 'Добавить товар')
def add_product(message):
    chat_id = message.chat.id
    user_state[chat_id] = 'waiting_for_info'
    bot.send_message(chat_id, 'Введите текстовую информацию о товаре:', reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_info')
def handle_product_info(message):
    chat_id = message.chat.id
    user_state[chat_id] = 'waiting_for_photo'
    users[chat_id] = {'product_info': message.text, 'photo_id': None}
    bot.send_message(chat_id,
                     'Теперь отправьте фотографию товара!',
                     reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_photo',
                     content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user = users.get(chat_id)

    if user:
        photo_id = message.photo[-1].file_id
        user['photo_id'] = photo_id

        # Add "Изменить" (Edit) and "Отправить" (Send) buttons
        markup = types.ReplyKeyboardMarkup(row_width=2)
        edit_button = types.KeyboardButton('Изменить')
        send_button = types.KeyboardButton('Отправить')
        markup.add(edit_button, send_button)

        bot.send_message(chat_id, 'Товар успешно добавлен!', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Пожалуйста, выберите действие из предложенных вариантов.')

@bot.message_handler(func=lambda message: message.text == 'Изменить' and user_state.get(message.chat.id) == 'waiting_for_photo')
def edit_product_info(message):
    chat_id = message.chat.id
    user_state[chat_id] = 'editing_info'
    bot.send_message(chat_id, 'Введите новую текстовую информацию о товаре:', reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'editing_info')
def handle_edit_product_info(message):
    chat_id = message.chat.id
    user = users.get(chat_id)

    if user:
        user['product_info'] = message.text
        user_state[chat_id] = 'waiting_for_photo'

        # Add "Изменить" (Edit) and "Отправить" (Send) buttons again
        markup = types.ReplyKeyboardMarkup(row_width=2)
        edit_button = types.KeyboardButton('Изменить')
        send_button = types.KeyboardButton('Отправить')
        markup.add(edit_button, send_button)

        bot.send_message(chat_id, 'Текстовая информация о товаре изменена.', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'Пожалуйста, выберите действие из предложенных вариантов.')

@bot.message_handler(func=lambda message: message.text == 'Отправить' and user_state.get(message.chat.id) == 'waiting_for_photo')
def send_product_info(message):
    chat_id = message.chat.id
    user = users.get(chat_id)

    if user:
        photo_id = user['photo_id']
        caption = user['product_info']

        if chat_id not in posts:
            posts[chat_id] = []
        sent_message = bot.send_photo("-1001979018110", photo_id, caption=caption)
        posts[chat_id].append({
            'message_id': sent_message.message_id,
            'photo_id': photo_id,
            'text': caption
        })

        send_main_menu(chat_id)
    else:
        bot.send_message(chat_id, 'Пожалуйста, выберите действие из предложенных вариантов.')

def send_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    add_product_button = types.KeyboardButton('Добавить товар')
    delete_product_button = types.KeyboardButton('Удалить товар')
    view_products_button = types.KeyboardButton('Просмотреть товары')
    info_button = types.KeyboardButton('Информация')
    clear_posts_button = types.KeyboardButton('Очистить посты')
    keyboard.add(add_product_button, delete_product_button, view_products_button, info_button, clear_posts_button)

    bot.send_message(chat_id, 'Выберите действие:', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Удалить товар')
def delete_product(message):
    chat_id = message.chat.id
    if chat_id in posts and len(posts[chat_id]) > 0:
        delete_keyboard = types.ReplyKeyboardMarkup(row_width=2)
        delete_buttons = []
        for i, post in enumerate(posts[chat_id]):
            delete_buttons.append(types.KeyboardButton(str(i + 1)))
        delete_keyboard.add(*delete_buttons)
        bot.send_message(chat_id, 'Выберите номер товара для удаления:', reply_markup=delete_keyboard)
    else:
        bot.send_message(chat_id, 'Нет сохраненных постов для удаления.')

@bot.message_handler(func=lambda message: message.text.isdigit() and int(message.text) > 0)
def confirm_delete(message):
    chat_id = message.chat.id
    post_number = int(message.text) - 1
    if chat_id in posts and len(posts[chat_id]) > post_number:
        post = posts[chat_id][post_number]
        bot.send_message(chat_id, f'Удален товар {post_number + 1} из группы.')
        bot.delete_message("-1001979018110", post['message_id'])
        del posts[chat_id][post_number]

        send_main_menu(chat_id)
    else:
        bot.send_message(chat_id, 'Неверный номер товара для удаления.')

@bot.message_handler(func=lambda message: message.text == 'Просмотреть товары')
def view_products(message):
    chat_id = message.chat.id
    user = users.get(chat_id)

    if chat_id in posts and len(posts[chat_id]) > 0:
        product_list = "Список добавленных товаров:\n"
        for i, post in enumerate(posts[chat_id]):
            product_list += f"{i + 1}. {post['text']}\n"

        bot.send_message(chat_id, product_list)
    else:
        bot.send_message(chat_id, 'Нет добавленных товаров.')

@bot.message_handler(func=lambda message: message.text == 'Очистить посты')
def clear_posts(message):
    chat_id = message.chat.id
    if chat_id in posts:
        posts[chat_id] = []
        bot.send_message(chat_id, "Сохраненные посты очищены.")
        send_main_menu(chat_id)

@bot.message_handler(func=lambda message: message.text == 'Информация')
def show_info(message):
    photo = open('img/info.png', 'rb')
    bot.send_photo(message.chat.id, photo)

@bot.message_handler(func=lambda message: True)
def handle_invalid_input(message):
    bot.send_message(message.chat.id, 'Пожалуйста, следуйте инструкциям и используйте предоставленные кнопки.')

bot.polling(none_stop=True)
