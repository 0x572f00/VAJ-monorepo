from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)

home = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🏘 Home', callback_data='home')]
])