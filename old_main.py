from collections import defaultdict
import telebot
from telebot import types
import webbrowser
import sqlite3
import requests
import json
from currency_converter import CurrencyConverter

bot = telebot.TeleBot("7747217090:AAGrLncvc0J_cDh3Z2RHZl8LrPQ7terbUMo")
currency = CurrencyConverter()
user_amounts = defaultdict(int)
API_WEATHER = '2820363b2f71d0dfa9f3a29bf6f6fb05'


@bot.message_handler(commands=['site'])
def site(message):
    bot.send_message(message.chat.id, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUIcmlja3JvbGw%3D')


@bot.message_handler(commands=['start'])
def main(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    site_btn = types.KeyboardButton('Перейти на сайт')
    markup.row(site_btn)

    with open('./crop.png', 'rb') as file:
        bot.send_photo(message.chat.id, file, reply_markup=markup)

    welcome_message = (f'Здарова, <b>{message.from_user.first_name}</b> <em><u>легенда</u></em>!\n'
                     f'Если хочешь увидеть приколюшку, выбери команду /site')
    bot.send_message(message.chat.id, welcome_message, parse_mode='html', reply_markup=markup)
    #bot.register_next_step_handler(message, on_click)


def on_click(message):
    print(message.text)
    if message.text == 'Перейти на сайт':
        bot.send_message(message.chat.id, 'https://www.youtube.com', reply_markup=types.ReplyKeyboardRemove())


#-------------- add user --------------
@bot.message_handler(commands=['adduser'])
def add_user_command(message):
    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()

        cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), password varchar(50))')
        conn.commit()

    cur.close()
    conn.close()

    bot.send_message(message.chat.id, 'Ща тебя зарегаем. Введи имя')
    bot.register_next_step_handler(message, user_name)


def user_name(message):
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(message, user_pass, name)


def user_pass(message, name):
    password = message.text.strip()
    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, password))
        conn.commit()

    cur.close()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('Список пользователей', callback_data='users'))

    bot.send_message(message.chat.id, 'Пользовать зарегистрирован', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    callback_data = call.data
    if callback_data == 'delete':
        handle_delete(call)
    elif callback_data == 'edit':
        handle_edit(call)
    elif callback_data == 'users':
        handle_users(call)
    elif callback_data in ['usd/eur', 'eur/usd', 'rub/usd', 'usd/rub', 'else']:
        handle_currency_conversion(call)


def handle_users(call):
    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

    info = ''
    for el in users:
        info += f'Имя: {el[1]}, пароль: {el[2]}\n'

    cur.close()
    conn.close()

    bot.send_message(call.message.chat.id, info)

#-------------- photo message --------------
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    markup = telebot.types.InlineKeyboardMarkup()
    site_btn = telebot.types.InlineKeyboardButton('Перейти на сайт', url='https://www.youtube.com')
    markup.row(site_btn)
    delete_btn = telebot.types.InlineKeyboardButton('Удалить фото', callback_data='delete')
    edit_btn = telebot.types.InlineKeyboardButton('Изменить текст', callback_data='edit')
    markup.row(delete_btn, edit_btn)

    bot.reply_to(message, 'Ну и стрёмное же фото', reply_markup=markup)


def handle_delete(call):
    bot.delete_message(call.message.chat.id, call.message.message_id - 1)
    print('deleted')
    types.ReplyKeyboardRemove()


def handle_edit(call):
    bot.edit_message_text('Edit text', call.message.chat.id, call.message.message_id)
    types.ReplyKeyboardRemove()


#-------------- help --------------
@bot.message_handler(commands=['help'])
def get_photo(message):
    bot.send_message(message.chat.id, 'Пока что бот в разработке')


#-------------- weather --------------
@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'Напиши название города')
    bot.register_next_step_handler(message, get_weather)


#@bot.message_handler(content_types=['text'])
def get_weather(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_WEATHER}&units=metric')
    if res.status_code == 200:
        data = json.loads(res.text)
        print(data["main"]["temp"])
        bot.reply_to(message, f'Сейчас в городе {city}: {round(data["main"]["temp"])} градусов')
    else:
        bot.reply_to(message, 'Такой город не найден или указан неверно')


#-------------- currency --------------
@bot.message_handler(commands=['currency'])
def converter(message):
    bot.send_message(message.chat.id, 'Введите сумму...')
    bot.register_next_step_handler(message, summ)


def summ(message):
    try:
        amount = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректную сумму')
        bot.register_next_step_handler(message, summ)
        return

    if amount > 0:
        user_amounts[message.chat.id] = amount

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('USD/EUR', callback_data='usd/eur')
        btn2 = types.InlineKeyboardButton('EUR/USD', callback_data='eur/usd')
        btn3 = types.InlineKeyboardButton('Другое значение', callback_data='else')
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.chat.id, 'Выберите конвертацию валют', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Сумма должна быть больше нуля. Попробуйте снова')
        bot.register_next_step_handler(message, summ)
        return


def handle_currency_conversion(call):
    if call.data != 'else':
        values = call.data.upper().split('/')
        amount = user_amounts[call.message.chat.id]
        res = currency.convert(amount, values[0], values[1])
        bot.send_message(call.message.chat.id, f'Итог: {round(res, 2)}.')
        #bot.register_next_step_handler(call.message, summ)
    else:
        bot.send_message(call.message.chat.id, "Введите пару значений названия валют через '/'")
        bot.register_next_step_handler(call.message, my_currency)


def my_currency(message):
    try:
        values = message.text.upper().split('/')
        amount = user_amounts[message.chat.id]
        res = currency.convert(amount, values[0], values[1])
        bot.send_message(message.chat.id, f'Итог: {round(res, 2)}.')
    except Exception:
        bot.send_message(message.chat.id, 'Возможно введено некорректное значение. Попробуйте снова')
        bot.register_next_step_handler(message, summ)


#-------------- other messages --------------
@bot.message_handler()
def info(message):
    if message.text.lower() == 'здарова':
        bot.send_message(message.chat.id, f'Здарова, {message.from_user.first_name}!🙂')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'Твой ID: {message.from_user.id}')
    else:
        bot.reply_to(message, f'{message.text} это бабка твоя')


bot.polling(non_stop=True)
