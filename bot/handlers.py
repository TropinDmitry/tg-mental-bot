from collections import defaultdict
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ContentType, FSInputFile, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters.command import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

import sqlite3
import requests
import json
import database.requests as req

from currency_converter import CurrencyConverter
from bot.keyboards import photo_buttons, open_app, categories, get_categories, items, catalog_btn
from bot.api_bot import bot

currency = CurrencyConverter()
user_amounts = defaultdict(int)

API_WEATHER = '2820363b2f71d0dfa9f3a29bf6f6fb05'

router = Router()


class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_password = State()
    waiting_for_weather = State()
    waiting_for_summ = State()
    another_currency = State()


@router.message(Command('site'))
async def site(message: Message):
    await message.answer('https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUIcmlja3JvbGw%3D')


@router.message(CommandStart())
async def start_bot(message: Message):
    with open('./crop.png', 'rb') as file:
        # input_file = InputFile(filename='crop.png')
        await message.answer_photo(photo=FSInputFile('./crop.png', filename='avatar'))

    welcome_message = (f'Здарова, <b>{message.from_user.first_name}</b> <em><u>легенда</u></em>!\n'
                       f'Если хочешь увидеть приколюшку, выбери команду /site')

    await req.set_user(message.from_user.id)
    await message.answer(welcome_message, parse_mode='html', reply_markup=open_app)


@router.message(F.content_type == ContentType.WEB_APP_DATA)
async def web_app(message: Message):
    res = json.loads(message.web_app_data.data)
    await message.answer(f"Entered name: {res['name']}, email: {res['email']}, phone: {res['phone']}")


# -------------- add user --------------
@router.message(Command('adduser'))
async def add_user_command(message: Message, state: FSMContext):
    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()

        cur.execute(
            'CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), password varchar(50))')
        conn.commit()

    #cur.close()
    #conn.close()

    await message.answer('Ща тебя зарегаем. Введи имя')
    await state.set_state(UserStates.waiting_for_name)
    #await dp.current_state().set_state(user_name)


@router.message(UserStates.waiting_for_name)
async def user_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)

    await message.answer('Введите пароль')
    await state.set_state(UserStates.waiting_for_password)
    #await dp.current_state().set_state(user_pass.set(name))


@router.message(UserStates.waiting_for_password)
async def user_pass(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    name = data.get('name')

    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, password))
        conn.commit()

    #cur.close()
    #conn.close()

    markup = InlineKeyboardBuilder()
    markup.add(InlineKeyboardButton(text='Список пользователей', callback_data='users'))
    markup = markup.as_markup()

    await message.answer('Пользовать зарегистрирован', reply_markup=markup)
    await state.clear()


@router.callback_query()
async def handle_callback(call: CallbackQuery, state: FSMContext):
    callback_data = call.data
    print(callback_data)
    match callback_data:
        case 'delete':
            await handle_delete(call)
        case 'edit':
            await handle_edit(call)
        case 'users':
            await handle_users(call)
        case 'usd/eur' | 'eur/usd' | 'rub/usd' | 'usd/rub' | 'else':
            await handle_currency_conversion(call, state)
        case str(value) if value.startswith('category_'):
            await handle_category(call)
        case str(value) if value.startswith('item_'):
            await handle_items(call)
        case 'to_main':
            await back_categories(call)


@router.callback_query()
async def handle_users(call: CallbackQuery):
    with sqlite3.connect('mentalbot.sql') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

    info = ''
    for el in users:
        info += f'Имя: {el[1]}, пароль: {el[2]}\n'

    cur.close()
    conn.close()

    await call.message.answer(info)


# -------------- photo message --------------
@router.message(F.content_type == ContentType.PHOTO)
async def get_photo(message: types.Message):
    await message.reply('Прикольная фотка)', reply_markup=photo_buttons)


@router.callback_query()
async def handle_delete(call: CallbackQuery):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id - 1)
    print('deleted')
    await call.answer()


@router.callback_query()
async def handle_edit(call: CallbackQuery):
    #await bot.edit_message_text('Edit text', call.message.chat.id, call.message.message_id)
    await call.message.edit_text('Edit text')
    print('edited')
    await call.answer()


# -------------- help --------------
@router.message(Command('help'))
async def help_info(message: types.Message):
    await message.answer('Пока что бот в разработке')


# -------------- weather --------------
@router.message(Command('weather'))
async def weather(message: Message, state: FSMContext):
    await message.answer('Напиши название города')
    await state.set_state(UserStates.waiting_for_weather)


@router.message(F.content_type == ContentType.TEXT, UserStates.waiting_for_weather)
async def get_weather(message: Message, state: FSMContext):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_WEATHER}&units=metric')
    if res.status_code == 200:
        data = json.loads(res.text)
        print(data["main"]["temp"])
        await message.reply(f'Сейчас в городе {city}: {round(data["main"]["temp"])} градусов')
    else:
        await message.reply('Такой город не найден или указан неверно')
    await state.clear()


# -------------- currency --------------
@router.message(Command('currency'))
async def converter(message: Message, state: FSMContext):
    await message.answer('Введите сумму...')
    await state.set_state(UserStates.waiting_for_summ)


@router.message(UserStates.waiting_for_summ)
async def summ(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer('Введите корректную сумму')
        await state.set_state(UserStates.waiting_for_summ)
        return

    if amount > 0:
        user_amounts[message.chat.id] = amount

        markup = InlineKeyboardBuilder()
        btn1 = InlineKeyboardButton(text='USD/EUR', callback_data='usd/eur')
        btn2 = InlineKeyboardButton(text='EUR/USD', callback_data='eur/usd')
        btn3 = InlineKeyboardButton(text='Другое значение', callback_data='else')
        markup.add(btn1, btn2, btn3)
        markup = markup.as_markup()

        await message.answer('Выберите конвертацию валют', reply_markup=markup)
    else:
        await message.answer('Сумма должна быть больше нуля. Попробуйте снова')
        await state.set_state(UserStates.waiting_for_summ)
        return


# -------------- add user --------------
@router.message(Command('catalog'))
async def category_command(message: Message):
    await message.answer('Тут можно узнать про видюхи', reply_markup=catalog_btn)


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберите категорию товара', reply_markup=await categories())


@router.callback_query()
async def handle_category(call: CallbackQuery):
    await call.answer('Вы выбрали категорию')
    await call.message.answer('Выберите товар по категории', reply_markup=await items(call.data.split('_')[1]))


@router.callback_query()
async def handle_items(call: CallbackQuery):
    item_data = await req.get_item(int(call.data.split('_')[1]))
    await call.answer('Вы выбрали товар')
    await call.message.answer(f'Название: {item_data.name}\nОписание: {item_data.description}\nЦена: {item_data.price}')


@router.callback_query()
async def back_categories(call: CallbackQuery):
    await call.message.answer('Выберите категорию товара', reply_markup=await categories())


@router.callback_query()
async def handle_currency_conversion(call: CallbackQuery, state: FSMContext):
    if call.data != 'else':
        values = call.data.upper().split('/')
        amount = user_amounts[call.message.chat.id]
        res = currency.convert(amount, values[0], values[1])
        await call.message.answer(f'Итог: {round(res, 2)}')
        # bot.register_next_step_handler(call.message, summ)
    else:
        await call.message.answer("Введите пару значений названия валют через '/'")
        await state.set_state(UserStates.another_currency)
    await call.answer()


@router.message(UserStates.another_currency)
async def my_currency(message: Message, state: FSMContext):
    try:
        values = message.text.upper().split('/')
        amount = user_amounts[message.chat.id]
        res = currency.convert(amount, values[0], values[1])
        await message.answer(f'Итог: {round(res, 2)}')
    except Exception:
        await message.answer('Возможно введено некорректное значение. Попробуйте снова')
        await state.set_state(UserStates.waiting_for_summ)


# -------------- other messages --------------
@router.message()
async def info(message: Message):
    if message.text:
        if message.text.lower() == 'здарова':
            await message.answer(f'Здарова, {message.from_user.first_name}!🙂')
        elif message.text.lower() == 'id':
            await message.reply(f'Твой ID: {message.from_user.id}')
        else:
            await message.reply(f'{message.text} - это что?')
