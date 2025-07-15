import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import Message, WebAppInfo, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.keyboard as kb
import random
from config import TOKEN

admin_handlers = Router()
bot = Bot(token=TOKEN)

class adminStates(StatesGroup):
    enter_password = State()

@admin_handlers.message(F.text == '/admin')
async def cmd_admin(message: Message, state: FSMContext):
    await message.answer("🔐 Please enter the admin panel password to proceed:", parse_mode='Markdown')
    await state.set_state(adminStates.enter_password)

@admin_handlers.message(adminStates.enter_password)
async def state_enter_password(message: Message, state: FSMContext):
    password = message.text
    user_id = message.from_user.id
    username = message.from_user.id

    if password == 'douglasmcrae':
        await message.answer(f"👋🏻 Welcome to the admin panel, *{username}*!", parse_mode='Markdown')
    else:
        await message.answer("🚫 Incorrect password. Please try again.", parse_mode='Markdown')
        return

