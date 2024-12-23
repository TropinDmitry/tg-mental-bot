from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from database.requests import get_categories, get_category_item
from aiogram.utils.keyboard import InlineKeyboardBuilder


users_btn = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='Список пользователей', callback_data='users')]])

photo_buttons = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='Перейти на сайт', url='https://www.youtube.com'),
                      InlineKeyboardButton(text='Удалить фото', callback_data='delete'),
                      InlineKeyboardButton(text='Изменить текст', callback_data='edit')]])

open_app = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Открыть приложение',
                                                         web_app=WebAppInfo(url='https://tropindmitry.github.io/simple-tg-app/index.html'))]],
                               resize_keyboard=True)

catalog_btn = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Каталог')]],
                                  resize_keyboard=True)


async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    print('categories: ', all_categories)
    for category in all_categories:
        print('cat')
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'category_{category.id}'))

    keyboard.add(InlineKeyboardButton(text='На главную', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()


async def items(category_id):
    category_id = int(category_id)
    all_items = await get_category_item(category_id)
    keyboard = InlineKeyboardBuilder()
    for item in all_items:
        keyboard.add(InlineKeyboardButton(text=item.name, callback_data=f'item_{item.id}'))

    keyboard.add(InlineKeyboardButton(text='На главную', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()